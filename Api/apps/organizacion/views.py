from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.mixins import EmpresaScopedViewSet
from .models import NodoOrganigrama, Proceso, Sede
from .serializers import NodoOrganigramaSerializer, ProcesoSerializer, SedeSerializer


class SedeViewSet(EmpresaScopedViewSet):
    queryset = Sede.objects.all()
    serializer_class = SedeSerializer
    filterset_fields = ["activa", "ciudad"]


def es_descendiente(nodo_evaluado, ancestro_id):
    """Verifica si ancestro_id es igual a nodo_evaluado o se encuentra en sus subordinados."""
    if str(nodo_evaluado.id) == str(ancestro_id):
        return True
    for hijo in nodo_evaluado.hijos.filter(activo=True):
        if es_descendiente(hijo, ancestro_id):
            return True
    return False


def recalcular_subarbol_nivel(nodo):
    """Recalcula recursivamente el campo 'nivel' para todos los subordinados de un nodo."""
    for hijo in nodo.hijos.filter(activo=True):
        nuevo_nivel = nodo.nivel + 1
        if hijo.nivel != nuevo_nivel:
            hijo.nivel = nuevo_nivel
            hijo.save(update_fields=["nivel", "updated_at"])
        recalcular_subarbol_nivel(hijo)


class NodoOrganigramaViewSet(EmpresaScopedViewSet):
    """
    Soporta ?padre_id=<uuid> para traer solo los hijos directos de un nodo
    (útil para renderizar el árbol de forma perezosa en el frontend) y
    ?padre_id=null para traer la raíz.
    """
    queryset = NodoOrganigrama.objects.all()
    serializer_class = NodoOrganigramaSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        padre_id = self.request.query_params.get("padre_id")
        if padre_id == "null":
            return qs.filter(padre__isnull=True)
        if padre_id:
            return qs.filter(padre_id=padre_id)
        return qs

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if 'padre_id' in data and (data['padre_id'] == "" or data['padre_id'] is None):
            data['padre_id'] = None
        if 'padre' in data and (data['padre'] == "" or data['padre'] is None):
            data['padre'] = None
        if 'area' in data and data['area'] == "":
            data['area'] = None
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if 'padre_id' in data and (data['padre_id'] == "" or data['padre_id'] is None):
            data['padre_id'] = None
        if 'padre' in data and (data['padre'] == "" or data['padre'] is None):
            data['padre'] = None
        if 'area' in data and data['area'] == "":
            data['area'] = None

        nuevo_padre_id = data.get('padre_id') if 'padre_id' in data else (data.get('padre') if 'padre' in data else None)

        # Validación de ciclos si cambia el padre
        if nuevo_padre_id is not None and str(nuevo_padre_id) != str(instance.padre_id if instance.padre else ''):
            if es_descendiente(instance, nuevo_padre_id):
                return Response(
                    {
                        "message": "No se puede asignar un cargo subordinado como padre (ciclo detectado).",
                        "code": "CYCLE_DETECTED"
                    },
                    status=400
                )

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)

        padre_cambio = False
        if 'padre' in serializer.validated_data or 'padre_id' in data:
            nuevo_padre = serializer.validated_data.get('padre')
            if nuevo_padre != instance.padre:
                padre_cambio = True
                instance.padre = nuevo_padre
                instance.nivel = (nuevo_padre.nivel + 1) if nuevo_padre else 1

        self.perform_update(serializer)

        if padre_cambio:
            recalcular_subarbol_nivel(instance)
            # Refrescar instancia serializada con nivel actualizado
            instance.refresh_from_db()
            serializer = self.get_serializer(instance)

        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="auto-organizar")
    def auto_organizar(self, request):
        """Restablece pos_x y pos_y a null para todos los nodos activos de la empresa."""
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        NodoOrganigrama.objects.filter(empresa=empresa, activo=True).update(pos_x=None, pos_y=None)
        return Response({"message": "Posiciones manuales eliminadas. El organigrama utilizará el trazado automático."})


class ProcesoViewSet(EmpresaScopedViewSet):
    queryset = Proceso.objects.all()
    serializer_class = ProcesoSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        padre_id = self.request.query_params.get("padre_id")
        if padre_id == "null":
            return qs.filter(padre__isnull=True)
        if padre_id:
            return qs.filter(padre_id=padre_id)
        return qs

    def list(self, request, *args, **kwargs):
        padre_id = request.query_params.get("padre_id")
        if padre_id is not None:
            return super().list(request, *args, **kwargs)

        empresa = request.user.empresa
        if not empresa and request.user.rol != "ADMIN":
            return Response({"estrategico": [], "misional": [], "apoyo": []})

        qs = self.get_queryset().filter(padre__isnull=True, activo=True).prefetch_related("subprocesos")
        serializer = self.get_serializer(qs, many=True)

        data = {
            "estrategico": [],
            "misional": [],
            "apoyo": [],
        }
        for item in serializer.data:
            tipo = item.get("tipo", "estrategico")
            if tipo in data:
                data[tipo].append(item)
            else:
                data["estrategico"].append(item)
        return Response(data)

    @action(detail=False, methods=["post"], url_path="sugerir-ia")
    def sugerir_ia(self, request):
        from rest_framework.response import Response
        from apps.empresas.services_ia import IAContextoService
        
        empresa = request.user.empresa
        if not empresa:
            return Response(
                {"message": "Identificador de empresa no provisto."},
                status=400
            )

        result = IAContextoService.sugerir_procesos(
            nombre=empresa.nombre,
            sector=empresa.sector_economico or "",
            ciiu_codigo=empresa.ciiu_codigo or "",
            ciiu_desc=empresa.ciiu_descripcion or "",
        )
        return Response(result)

    @action(detail=False, methods=["post"], url_path="importar-plantilla")
    def importar_plantilla(self, request):
        """
        POST /api/organizacion/procesos/importar-plantilla/
        Importa de forma atómica e idempotente los procesos de una plantilla normativa.
        Usa get_or_create por (empresa, tipo, padre, nombre_normalizado).
        """
        from django.db import transaction
        from .plantillas import PLANTILLAS_SGSST
        from .models import normalizar_texto

        empresa = request.user.empresa
        if not empresa and getattr(request.user, "rol", None) == "ADMIN":
            empresa_id = request.query_params.get("empresa_id") or request.data.get("empresa_id")
            if empresa_id:
                from apps.empresas.models import Empresa
                empresa = Empresa.objects.filter(id=empresa_id).first()

        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        plantilla_id = request.data.get("plantilla_id") or request.data.get("id") or request.data.get("clave")
        procesos_data = None
        plantilla_nombre = ""

        if plantilla_id and plantilla_id in PLANTILLAS_SGSST:
            plantilla = PLANTILLAS_SGSST[plantilla_id]
            procesos_data = plantilla["procesos"]
            plantilla_nombre = plantilla["nombre"]
        elif "procesos" in request.data and isinstance(request.data["procesos"], list):
            procesos_data = request.data["procesos"]
            plantilla_nombre = request.data.get("nombre", "Personalizada")
        else:
            return Response(
                {
                    "message": f"Plantilla '{plantilla_id}' no encontrada. Opciones válidas: {list(PLANTILLAS_SGSST.keys())}."
                },
                status=400
            )

        creados = 0
        existentes = 0

        with transaction.atomic():
            for p_item in procesos_data:
                p_nombre = p_item["nombre"].strip()
                p_tipo = p_item["tipo"]
                p_norm = normalizar_texto(p_nombre)

                proceso_raiz, created = Proceso.objects.get_or_create(
                    empresa=empresa,
                    tipo=p_tipo,
                    padre=None,
                    nombre_normalizado=p_norm,
                    defaults={
                        "nombre": p_nombre,
                        "descripcion": p_item.get("descripcion", ""),
                        "activo": True,
                    }
                )
                if not proceso_raiz.activo:
                    proceso_raiz.activo = True
                    proceso_raiz.save(update_fields=["activo"])

                if created:
                    creados += 1
                else:
                    existentes += 1

                subprocesos = p_item.get("subprocesos", [])
                for sub_item in subprocesos:
                    sub_nombre = (sub_item["nombre"] if isinstance(sub_item, dict) else str(sub_item)).strip()
                    sub_desc = sub_item.get("descripcion") if isinstance(sub_item, dict) else f"Subproceso de {proceso_raiz.nombre}"
                    sub_norm = normalizar_texto(sub_nombre)

                    sub_proceso, sub_created = Proceso.objects.get_or_create(
                        empresa=empresa,
                        tipo=p_tipo,
                        padre=proceso_raiz,
                        nombre_normalizado=sub_norm,
                        defaults={
                            "nombre": sub_nombre,
                            "descripcion": sub_desc,
                            "activo": True,
                        }
                    )
                    if not sub_proceso.activo:
                        sub_proceso.activo = True
                        sub_proceso.save(update_fields=["activo"])

                    if sub_created:
                        creados += 1
                    else:
                        existentes += 1

        return Response({
            "message": f"Plantilla '{plantilla_nombre}' procesada exitosamente.",
            "creados": creados,
            "existentes": existentes,
        })

    @action(detail=False, methods=["get"], url_path="exportar-mapa-pdf")
    def exportar_mapa_pdf(self, request):
        """
        GET /api/organizacion/procesos/exportar-mapa-pdf/
        Genera PDF del Mapa de Procesos incorporando el logo real de la empresa y los colores de la marca (§Módulo 0).
        """
        import io
        import os
        from django.conf import settings
        from django.http import HttpResponse
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors

        empresa = request.user.empresa
        if not empresa:
            return Response({"error": "Sin empresa asociada."}, status=400)

        branding = empresa.branding or {}
        primary_hex = branding.get("primario", "#002D62")
        secondary_hex = branding.get("secundario", "#0284C7")
        mapa_branding = branding.get("mapa_procesos", {})
        
        est_hex = mapa_branding.get("estrategico", primary_hex)
        mis_hex = mapa_branding.get("misional", secondary_hex)
        apo_hex = mapa_branding.get("apoyo", "#64748B")

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=landscape(letter))
        width, height = landscape(letter)

        # Background color
        p.setFillColor(colors.HexColor("#F8FAFC"))
        p.rect(0, 0, width, height, fill=True, stroke=False)

        # Header bar
        p.setFillColor(colors.HexColor(primary_hex))
        p.rect(0, height - 70, width, 70, fill=True, stroke=False)

        # Intentar dibujar el logo real si existe en el disco
        logo_drawn = False
        if empresa.logo_url:
            try:
                # Si logo_url es una ruta relativa de media
                rel_path = empresa.logo_url.lstrip('/')
                if rel_path.startswith('media/'):
                    rel_path = rel_path[6:]
                full_logo_path = os.path.join(settings.MEDIA_ROOT, rel_path)
                if os.path.exists(full_logo_path):
                    # Placa blanca redonda para el logo
                    p.setFillColor(colors.white)
                    p.roundRect(30, height - 60, 50, 50, 8, fill=True, stroke=False)
                    p.drawImage(full_logo_path, 35, height - 55, width=40, height=40, preserveAspectRatio=True, mask='auto')
                    logo_drawn = True
            except Exception:
                logo_drawn = False

        # Texto del Encabezado
        text_x = 95 if logo_drawn else 35
        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold", 16)
        p.drawString(text_x, height - 35, f"MAPA DE PROCESOS ORGANIZACIONAL — {empresa.nombre.upper()}")

        p.setFont("Helvetica", 9)
        p.drawString(text_x, height - 52, f"NIT: {empresa.nit} • Sector: {empresa.sector_economico or 'General'} • Código CIIU: {empresa.ciiu_codigo or 'N/A'}")

        # Pie de página
        p.setFillColor(colors.HexColor("#64748B"))
        p.setFont("Helvetica-Bold", 8)
        p.drawString(35, 20, "FOSST V.I.D.A. — Sistema Integrado de Gestión de Seguridad y Salud en el Trabajo (ISO 45001 / Dec. 1072)")

        # Render de Secciones
        y = height - 100
        procesos = Proceso.objects.filter(empresa=empresa, padre__isnull=True, activo=True).prefetch_related("subprocesos")

        for tipo, titulo, col_hex in [
            ("estrategico", "PROCESOS ESTRATÉGICOS Y DIRECCIONAMIENTO", est_hex),
            ("misional", "PROCESOS MISIONALES Y CONTROL OPERACIONAL", mis_hex),
            ("apoyo", "PROCESOS DE APOYO Y SOPORTE", apo_hex)
        ]:
            # Franja de encabezado de categoría
            p.setFillColor(colors.HexColor(col_hex))
            p.roundRect(35, y - 22, width - 70, 24, 4, fill=True, stroke=False)
            p.setFillColor(colors.white)
            p.setFont("Helvetica-Bold", 10)
            p.drawString(45, y - 15, titulo)

            y -= 38
            procs = [pr for pr in procesos if pr.tipo == tipo]

            if not procs:
                p.setFillColor(colors.HexColor("#94A3B8"))
                p.setFont("Helvetica-Oblique", 9)
                p.drawString(55, y, "(Sin procesos registrados en esta categoría)")
                y -= 25
            else:
                x_pos = 45
                for pr in procs:
                    # Tarjeta de proceso
                    p.setFillColor(colors.white)
                    p.setStrokeColor(colors.HexColor("#CBD5E1"))
                    p.setLineWidth(1)
                    p.roundRect(x_pos, y - 35, 220, 42, 6, fill=True, stroke=True)

                    # Borde acentuado superior
                    p.setFillColor(colors.HexColor(col_hex))
                    p.roundRect(x_pos, y + 3, 220, 4, 2, fill=True, stroke=False)

                    p.setFillColor(colors.HexColor("#0F172A"))
                    p.setFont("Helvetica-Bold", 9)
                    p.drawString(x_pos + 10, y - 12, pr.nombre[:32])

                    subs = pr.subprocesos.filter(activo=True)
                    if subs:
                        sub_text = f"Subprocesos: {', '.join([s.nombre for s in subs[:2]])}"
                        p.setFillColor(colors.HexColor("#64748B"))
                        p.setFont("Helvetica", 8)
                        p.drawString(x_pos + 10, y - 27, sub_text[:38])

                    x_pos += 235
                    if x_pos + 220 > width - 40:
                        x_pos = 45
                        y -= 50

                y -= 55

        p.showPage()
        p.save()

        pdf_bytes = buffer.getvalue()
        buffer.close()

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="mapa_procesos_{empresa.nit}.pdf"'
        return response

