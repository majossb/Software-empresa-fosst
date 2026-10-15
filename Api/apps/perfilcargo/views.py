import json
import uuid
import datetime
import anthropic

from django.db import transaction
from django.db.models import Count, Q
from django.http import StreamingHttpResponse
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.capacitaciones.models import Trabajador
from .models import (
    CatalogoEPP, CatalogoPeligro, PerfilCargo, CargoVersion,
    CargoFuncion, CargoResponsabilidad, CargoCompetencia,
    CargoIndicador, CargoPeligro, CargoEPP,
    CargoAptitud, CargoInteraccion, CargoRestriccion, CargoSuplente
)
from .serializers import (
    CatalogoEPPSerializer, CatalogoPeligroSerializer,
    PerfilCargoSerializer, CargoVersionSerializer
)


from apps.common.permissions import IsRol, IsRolParaEscritura


class PerfilCargoListView(APIView):
    permission_classes = [IsAuthenticated, IsRolParaEscritura.de("responsable", "alta_direccion")]

    def get(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        area = request.query_params.get('area')
        sede_id = request.query_params.get('sede_id')

        queryset = PerfilCargo.objects.filter(empresa=empresa, activo=True)
        if area:
            queryset = queryset.filter(area=area)
        if sede_id:
            queryset = queryset.filter(sede_id=sede_id)

        # Annotate worker count using the correct 'trabajadores' related name
        queryset = queryset.annotate(
            trabajadores_count=Count(
                'trabajadores',
                filter=Q(trabajadores__activo=True, trabajadores__deleted_at__isnull=True)
            )
        )

        queryset = queryset.order_by('codigo')
        serializer = PerfilCargoSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        data = request.data.copy()
        data['empresa'] = str(empresa.id)
        codigo = data.get('codigo')
        
        if not codigo:
            year = datetime.datetime.now().year
            prefix = f"PC-{year}-"
            ultimo = PerfilCargo.objects.filter(
                empresa=empresa, codigo__startswith=prefix
            ).order_by("-codigo").first()
            next_seq = 1
            if ultimo:
                parts = ultimo.codigo.split("-")
                if len(parts) == 3:
                    try:
                        next_seq = int(parts[2]) + 1
                    except ValueError:
                        pass
            codigo = f"{prefix}{next_seq:04d}"
            data['codigo'] = codigo

        if PerfilCargo.objects.filter(empresa=empresa, codigo=codigo).exists():
            return Response({"error": f"El código de perfil de cargo \"{codigo}\" ya se encuentra registrado."}, status=status.HTTP_400_BAD_REQUEST)

        # Sanitizar sede / sede_id
        sede_val = data.get('sede') or data.get('sede_id')
        if sede_val and str(sede_val).strip():
            data['sede'] = str(sede_val).strip()
        else:
            data['sede'] = None

        # Sanitizar campos vacíos
        for field in ['area', 'nodo_organigrama_id', 'proceso_id', 'proposito', 'educacion', 'experiencia', 'formacion', 'habilidades', 'impacto_descripcion', 'naturaleza_descripcion']:
            if field in data and (data[field] == "" or data[field] is None):
                data[field] = None

        serializer = PerfilCargoSerializer(data=data)
        if serializer.is_valid():
            with transaction.atomic():
                perfil = serializer.save()
                
                # Relations creation
                self._create_relations(perfil, data)
                
                # Snapshot
                raw_snapshot = PerfilCargoSerializer(perfil).data
                snapshot_data = json.loads(json.dumps(raw_snapshot, cls=DjangoJSONEncoder))
                CargoVersion.objects.create(
                    perfil_cargo=perfil,
                    numero_version=1,
                    snapshot=snapshot_data,
                    motivo_cambio=data.get('motivo_cambio', "Creación inicial del perfil de cargo"),
                    creado_por=request.user.username if request.user else "Sistema"
                )

                from apps.auditoria.helpers import registrar_audit_log
                registrar_audit_log(
                    request,
                    "CREAR_PERFIL_CARGO",
                    tabla_afectada="perfiles_cargo",
                    registro_id=perfil.id,
                    valores_nuevos=snapshot_data
                )

            return Response(PerfilCargoSerializer(perfil).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _create_relations(self, perfil, data):
        for idx, f in enumerate(data.get('funciones', [])):
            if isinstance(f, dict):
                desc = f.get('descripcion')
                ord_val = f.get('orden', idx)
            else:
                desc = str(f)
                ord_val = idx
            if desc and str(desc).strip():
                CargoFuncion.objects.create(perfil_cargo=perfil, descripcion=str(desc).strip(), orden=ord_val)

        for idx, r in enumerate(data.get('responsabilidades', [])):
            if isinstance(r, dict):
                desc = r.get('descripcion')
                ord_val = r.get('orden', idx)
            else:
                desc = str(r)
                ord_val = idx
            if desc and str(desc).strip():
                CargoResponsabilidad.objects.create(perfil_cargo=perfil, descripcion=str(desc).strip(), orden=ord_val)

        for c in data.get('competencias', []):
            if not isinstance(c, dict):
                continue
            nombre = c.get('nombre')
            if not nombre or not str(nombre).strip():
                continue
            nivel_str = c.get('nivel') or 'Intermedio'
            nivel_req = c.get('nivel_requerido')
            if not nivel_req:
                map_niveles = {"Básico": 1, "Intermedio": 2, "Avanzado": 3, "Experto": 4, "1": 1, "2": 2, "3": 3, "4": 4}
                nivel_req = map_niveles.get(str(nivel_str).strip(), 2)
            CargoCompetencia.objects.create(
                perfil_cargo=perfil,
                nombre=str(nombre).strip(),
                nivel=str(nivel_str).strip(),
                tipo=c.get('tipo') or 'tecnica',
                nivel_requerido=nivel_req,
            )

        for i in data.get('indicadores', []):
            if isinstance(i, dict) and i.get('descripcion'):
                CargoIndicador.objects.create(
                    perfil_cargo=perfil,
                    descripcion=str(i.get('descripcion')).strip(),
                    meta=str(i.get('meta', '')).strip() or None
                )

        for p in data.get('peligros', []):
            if isinstance(p, dict):
                cat_pel_id = p.get('catalogo_peligro_id')
                if cat_pel_id and not CatalogoPeligro.objects.filter(id=cat_pel_id).exists():
                    cat_pel_id = None
                CargoPeligro.objects.create(
                    perfil_cargo=perfil, 
                    catalogo_peligro_id=cat_pel_id,
                    tipo_personalizado=p.get('tipo_personalizado') or '',
                    clasificacion_personalizada=p.get('clasificacion_personalizada') or ''
                )

        for e in data.get('epps', []):
            if isinstance(e, dict):
                cat_epp_id = e.get('catalogo_epp_id')
                if cat_epp_id and not CatalogoEPP.objects.filter(id=cat_epp_id).exists():
                    cat_epp_id = None
                CargoEPP.objects.create(
                    perfil_cargo=perfil,
                    catalogo_epp_id=cat_epp_id,
                    nombre_personalizado=e.get('nombre_personalizado') or ''
                )

        for a in data.get('aptitudes', []):
            CargoAptitud.objects.create(
                perfil_cargo=perfil,
                tipo=a.get('tipo'),
                nombre=a.get('nombre'),
                requerida=a.get('requerida', True),
                observacion=a.get('observacion'),
            )

        for i in data.get('interacciones', []):
            CargoInteraccion.objects.create(
                perfil_cargo=perfil,
                parte_interesada=i.get('parte_interesada'),
                proceso_id=i.get('proceso_id'),
                tipo=i.get('tipo'),
                descripcion=i.get('descripcion'),
            )

        for r in data.get('restricciones', []):
            CargoRestriccion.objects.create(
                perfil_cargo=perfil,
                descripcion=r.get('descripcion'),
                activa=r.get('activa', True),
            )

        for s in data.get('suplentes', []):
            cargo_suplente_id = s.get('cargo_suplente_id')
            if not cargo_suplente_id:
                continue
            CargoSuplente.objects.create(
                perfil_cargo=perfil,
                cargo_suplente_id=cargo_suplente_id,
                orden_prioridad=s.get('orden_prioridad', 1),
            )


class PerfilCargoDetailView(APIView):
    permission_classes = [IsAuthenticated, IsRolParaEscritura.de("responsable", "alta_direccion")]

    def get(self, request, pk):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        try:
            perfil = PerfilCargo.objects.get(pk=pk, empresa=empresa, activo=True)
            serializer = PerfilCargoSerializer(perfil)
            return Response(serializer.data)
        except PerfilCargo.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        try:
            perfil = PerfilCargo.objects.get(pk=pk, empresa=empresa, activo=True)
        except PerfilCargo.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if 'codigo' in data and data['codigo'] != perfil.codigo:
            if PerfilCargo.objects.filter(empresa=empresa, codigo=data['codigo']).exclude(pk=pk).exists():
                return Response({"error": "Código ya existe para esta empresa."}, status=status.HTTP_400_BAD_REQUEST)

        # Sanitizar sede / sede_id
        if 'sede_id' in data or 'sede' in data:
            sede_val = data.get('sede') or data.get('sede_id')
            if sede_val and str(sede_val).strip():
                data['sede'] = str(sede_val).strip()
            else:
                data['sede'] = None

        # Sanitizar campos vacíos
        for field in ['area', 'nodo_organigrama_id', 'proceso_id', 'proposito', 'educacion', 'experiencia', 'formacion', 'habilidades', 'impacto_descripcion', 'naturaleza_descripcion']:
            if field in data and (data[field] == "" or data[field] is None):
                data[field] = None

        # Comparación profunda para detectar cambios sustanciales (como Express original)
        is_substantial = self._detect_substantial_changes(perfil, data)

        serializer = PerfilCargoSerializer(perfil, data=data, partial=True)
        if serializer.is_valid():
            with transaction.atomic():
                perfil = serializer.save()

                # Solo borrar/recrear relaciones que están presentes en request.data
                relation_map = {
                    'funciones': perfil.funciones,
                    'responsabilidades': perfil.responsabilidades,
                    'competencias': perfil.competencias,
                    'indicadores': perfil.indicadores,
                    'peligros': perfil.peligros,
                    'epps': perfil.epps,
                    'aptitudes': perfil.aptitudes,
                    'interacciones': perfil.interacciones,
                    'restricciones': perfil.restricciones,
                    'suplentes': perfil.suplentes,
                }
                for key, manager in relation_map.items():
                    if key in data:
                        manager.all().delete()

                PerfilCargoListView()._create_relations(perfil, data)

                if is_substantial:
                    perfil.version_actual += 1
                    perfil.save(update_fields=['version_actual'])
                    raw_snapshot = PerfilCargoSerializer(perfil).data
                    snapshot_data = json.loads(json.dumps(raw_snapshot, cls=DjangoJSONEncoder))
                    CargoVersion.objects.create(
                        perfil_cargo=perfil,
                        numero_version=perfil.version_actual,
                        snapshot=snapshot_data,
                        motivo_cambio=data.get('motivo_cambio', 'Actualización automática por cambios sustanciales'),
                        creado_por=request.user.username if request.user else "Sistema",
                    )

                from apps.auditoria.helpers import registrar_audit_log
                registrar_audit_log(
                    request,
                    "ACTUALIZAR_PERFIL_CARGO_VERSION" if is_substantial else "ACTUALIZAR_PERFIL_CARGO",
                    tabla_afectada="perfiles_cargo",
                    registro_id=perfil.id,
                    valores_nuevos=data
                )

            return Response(PerfilCargoSerializer(perfil).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _detect_substantial_changes(perfil, data):
        """Compara contenido real de funciones/peligros/epps como el Express original."""
        if 'funciones' in data:
            old = list(perfil.funciones.order_by('orden').values_list('descripcion', flat=True))
            new = [f.get('descripcion') if isinstance(f, dict) else str(f) for f in data['funciones']]
            if old != new:
                return True

        if 'peligros' in data:
            old_ids = set(perfil.peligros.values_list('catalogo_peligro_id', flat=True))
            new_ids = {p.get('catalogo_peligro_id') for p in data['peligros']}
            if old_ids != new_ids:
                return True

        if 'epps' in data:
            old_ids = set(perfil.epps.values_list('catalogo_epp_id', flat=True))
            new_ids = {e.get('catalogo_epp_id') for e in data['epps']}
            if old_ids != new_ids:
                return True

        # Criticidad, aptitudes y restricciones alimentan directamente a MICHC (Fase 4):
        # un cambio aquí también es "sustancial" y debe re-versionar el perfil.
        campos_criticidad = [
            'criticidad_sst', 'criticidad_operacional', 'criticidad_vial',
            'criticidad_ambiental', 'criticidad_estrategica',
        ]
        for campo in campos_criticidad:
            if campo in data and str(data[campo]) != str(getattr(perfil, campo)):
                return True

        if 'aptitudes' in data:
            old = set(perfil.aptitudes.values_list('tipo', 'nombre', 'requerida'))
            new = {(a.get('tipo'), a.get('nombre'), a.get('requerida', True)) for a in data['aptitudes']}
            if old != new:
                return True

        if 'restricciones' in data:
            old = set(perfil.restricciones.values_list('descripcion', 'activa'))
            new = {(r.get('descripcion'), r.get('activa', True)) for r in data['restricciones']}
            if old != new:
                return True

        return False

    def delete(self, request, pk):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        try:
            perfil = PerfilCargo.objects.get(pk=pk, empresa=empresa, activo=True)
            
            # Check for linked workers
            active_workers = Trabajador.objects.filter(perfil_cargo=perfil, activo=True, deleted_at__isnull=True).count()
            if active_workers > 0:
                return Response(
                    {"error": f"No se puede eliminar el perfil porque hay {active_workers} trabajador(es) activo(s) vinculado(s) al mismo."},
                    status=status.HTTP_409_CONFLICT
                )
                
            perfil.activo = False
            perfil.save()

            from apps.auditoria.helpers import registrar_audit_log
            registrar_audit_log(
                request,
                "ELIMINAR_PERFIL_CARGO",
                tabla_afectada="perfiles_cargo",
                registro_id=perfil.id
            )

            return Response({"message": "Perfil de cargo inhabilitado correctamente."})
        except PerfilCargo.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class PerfilCargoVersionesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        try:
            perfil = PerfilCargo.objects.get(pk=pk, empresa=empresa, activo=True)
        except PerfilCargo.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        versiones = CargoVersion.objects.filter(perfil_cargo=perfil).order_by('-numero_version')
        serializer = CargoVersionSerializer(versiones, many=True)
        return Response(serializer.data)


class SuggestedEPPsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            peligro = CatalogoPeligro.objects.get(pk=pk)
            epps = peligro.epps_sugeridos.filter(activo=True)
            serializer = CatalogoEPPSerializer(epps, many=True)
            return Response(serializer.data)
        except CatalogoPeligro.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class GenerateIAFieldView(APIView):
    permission_classes = [IsAuthenticated, IsRol.de("responsable", "alta_direccion")]

    def post(self, request):
        data = request.data
        campo = data.get('campo')
        nombre_cargo = data.get('nombre_cargo')
        area = data.get('area')
        contexto = data.get('contexto_adicional', '')

        if campo == 'proposito':
            prompt = f'Redacta el PROPÓSITO DEL CARGO para el puesto "{nombre_cargo}" en el área "{area}". Contexto adicional: {contexto}. Máximo 3 oraciones en lenguaje formal colombiano. Solo el texto, sin encabezado.'
        elif campo == 'funciones':
            prompt = f'Lista las FUNCIONES ESENCIALES del cargo "{nombre_cargo}" en el área "{area}". Contexto: {contexto}. Devuelve entre 5 y 8 funciones en formato de lista numerada. Cada función inicia con verbo infinitivo. Solo la lista, sin encabezado.'
        elif campo == 'responsabilidades':
            prompt = f'Lista las RESPONSABILIDADES del cargo "{nombre_cargo}" en el área "{area}". Contexto: {contexto}. Devuelve entre 3 y 6 responsabilidades en formato de lista numerada. Solo la lista, sin encabezado.'
        else:
            return Response({"error": "Campo no soportado"}, status=status.HTTP_400_BAD_REQUEST)

        # Usar API Key de Anthropic
        api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        
        def event_stream():
            try:
                with client.messages.stream(
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                    model="claude-3-5-sonnet-20241022",
                ) as stream:
                    for text in stream.text_stream:
                        yield f"data: {text}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"

        return StreamingHttpResponse(event_stream(), content_type='text/event-stream')


def generar_archivo_pdf_perfil_cargo(perfil, empresa):
    """
    Genera el archivo PDF físico de la ficha técnica del perfil de cargo usando ReportLab.
    """
    import os
    from django.conf import settings
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch

    output_dir = os.path.join(settings.BASE_DIR, "uploads", "pdfs", "perfiles", str(empresa.id))
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"{perfil.id}.pdf")

    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#0F172A'),
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#059669'),
    )
    header_meta_style = ParagraphStyle(
        'HeaderMeta',
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#475569'),
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        textColor=colors.HexColor('#0F172A'),
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#334155'),
    )
    body_bold = ParagraphStyle(
        'BodyBoldCustom',
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#0F172A'),
    )

    elements = []

    # ── 1. Encabezado Oficial FOSST V.I.D.A. ──────────────────────
    header_data = [
        [
            Paragraph("<b>FOSST V.I.D.A.</b><br/><font size=6.5 color='#64748B'>Gestión Integral • Seguridad • Desempeño</font>", title_style),
            Paragraph(f"<b>PERFIL DEL CARGO</b><br/><font color='#059669'>{perfil.nombre_cargo.upper()}</font>", subtitle_style),
            Paragraph(f"<b>Código:</b> {perfil.codigo}<br/><b>Versión:</b> {perfil.version_actual}.0<br/><b>Fecha:</b> {perfil.updated_at.strftime('%d/%m/%Y')}<br/><b>Página:</b> 1 de 1", header_meta_style)
        ]
    ]
    t_header = Table(header_data, colWidths=[150, 240, 150])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -1), 1.5, colors.HexColor('#059669')),
    ]))
    elements.append(t_header)
    elements.append(Spacer(1, 10))

    # ── 2. Identificación del Cargo & Propósito ────────────────────
    ident_data = [
        [Paragraph("<b>1. IDENTIFICACIÓN DEL CARGO</b>", section_heading), Paragraph("<b>2. PROPÓSITO DEL CARGO</b>", section_heading)],
        [
            Paragraph(
                f"<b>Nombre:</b> {perfil.nombre_cargo}<br/>"
                f"<b>Área / Proceso:</b> {perfil.area or 'Operaciones'}<br/>"
                f"<b>Nivel Riesgo:</b> {perfil.nivel_riesgo or 'II'}<br/>"
                f"<b>Criticidad SST:</b> {perfil.criticidad_sst.upper()}<br/>"
                f"<b>Sede:</b> {perfil.sede.nombre if perfil.sede else 'Principal'}",
                body_style
            ),
            Paragraph(perfil.proposito or "Garantizar la ejecución eficiente, segura y conforme a la normatividad de las actividades asignadas al cargo.", body_style)
        ]
    ]
    t_ident = Table(ident_data, colWidths=[265, 275])
    t_ident.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_ident)
    elements.append(Spacer(1, 8))

    # ── 3. Funciones Principales ──────────────────────────────────
    funciones = list(perfil.funciones.all().order_by('orden'))
    func_rows = [[Paragraph("<b>#</b>", body_bold), Paragraph("<b>3. FUNCIONES PRINCIPALES DEL CARGO</b>", section_heading)]]
    if funciones:
        for idx, f in enumerate(funciones, start=1):
            func_rows.append([Paragraph(str(idx), body_bold), Paragraph(f.descripcion, body_style)])
    else:
        func_rows.append([Paragraph("1", body_bold), Paragraph("Ejecutar las labores operativas y técnicas asignadas conforme al SG-SST.", body_style)])

    t_func = Table(func_rows, colWidths=[25, 515])
    t_func.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_func)
    elements.append(Spacer(1, 8))

    # ── 4. Requisitos y Responsabilidades ─────────────────────────
    req_data = [
        [Paragraph("<b>4. RESPONSABILIDADES CLAVE</b>", section_heading), Paragraph("<b>5. REQUISITOS DEL CARGO</b>", section_heading)],
        [
            Paragraph(
                "<br/>".join([f"• {r.descripcion}" for r in perfil.responsabilidades.all()])
                if perfil.responsabilidades.exists()
                else "• Cumplir con los estándares del SG-SST y políticas corporativas.<br/>• Reportar actos y condiciones inseguras de inmediato.",
                body_style
            ),
            Paragraph(
                f"<b>Educación:</b> {perfil.educacion or 'Bachiller / Técnico'}<br/>"
                f"<b>Experiencia:</b> {perfil.experiencia or 'Mínimo 1 año'}<br/>"
                f"<b>Formación:</b> {perfil.formacion or 'Capacitación en SST'}<br/>"
                f"<b>Habilidades:</b> {perfil.habilidades or 'Trabajo en equipo, comunicación'}",
                body_style
            )
        ]
    ]
    t_req = Table(req_data, colWidths=[265, 275])
    t_req.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_req)
    elements.append(Spacer(1, 8))

    # ── 5. Peligros GTC 45 y EPPs ─────────────────────────────────
    peligros = list(perfil.peligros.all().select_related('catalogo_peligro'))
    epps = list(perfil.epps.all().select_related('catalogo_epp'))

    peligros_txt = ", ".join([p.catalogo_peligro.clasificacion if p.catalogo_peligro else (p.clasificacion_personalizada or 'General') for p in peligros]) or "Iluminación, Postura prolongada, Riesgo biomecánico"
    epps_txt = ", ".join([e.catalogo_epp.nombre if e.catalogo_epp else (e.nombre_personalizado or 'EPP') for e in epps]) or "Dotación estándar según área"

    riesgo_data = [
        [Paragraph("<b>6. PELIGROS Y RIESGOS ASOCIADOS (GTC 45)</b>", section_heading), Paragraph("<b>7. ELEMENTOS DE PROTECCIÓN (EPP)</b>", section_heading)],
        [Paragraph(peligros_txt, body_style), Paragraph(epps_txt, body_style)]
    ]
    t_riesgo = Table(riesgo_data, colWidths=[265, 275])
    t_riesgo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_riesgo)
    elements.append(Spacer(1, 14))

    # ── 6. Control de Cambios y Aprobaciones (Footer) ──────────────
    footer_data = [
        [
            Paragraph("<b>DOCUMENTO CONTROLADO — FOSST V.I.D.A.</b><br/><font size=6 color='#64748B'>Prohibida su reproducción sin autorización</font>", header_meta_style),
            Paragraph("<b>Elaboró:</b><br/>Talento Humano", header_meta_style),
            Paragraph("<b>Revisó:</b><br/>Coordinación SST", header_meta_style),
            Paragraph("<b>Aprobó:</b><br/>Gerencia General", header_meta_style),
        ]
    ]
    t_footer = Table(footer_data, colWidths=[200, 110, 110, 120])
    t_footer.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#059669')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_footer)

    doc.build(elements)
    return filepath


class GeneratePDFView(APIView):
    permission_classes = [IsAuthenticated, IsRol.de("responsable", "alta_direccion")]

    def post(self, request, pk):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        try:
            perfil = PerfilCargo.objects.get(pk=pk, empresa=empresa, activo=True)
        except PerfilCargo.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        job_id = f"job_{uuid.uuid4().hex[:12]}"
        cache_key = f"pdf:{empresa.id}:{pk}"
        
        # Generar el archivo PDF real en disco
        try:
            generar_archivo_pdf_perfil_cargo(perfil, empresa)
            relative_url = f"/uploads/pdfs/perfiles/{empresa.id}/{pk}.pdf"
            cache.set(cache_key, {"estado": "listo", "url": relative_url, "jobId": job_id}, timeout=300)
            return Response({
                "jobId": job_id,
                "estado": "listo",
                "url": relative_url,
                "mensaje": "Documento PDF generado exitosamente."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            cache.set(cache_key, {"estado": "error", "error": str(e), "jobId": job_id}, timeout=300)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PDFStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        cache_key = f"pdf:{empresa.id}:{pk}"
        status_data = cache.get(cache_key)
        
        if not status_data:
            # Si no está en cache, verificar si el archivo existe en disco o generarlo
            import os
            from django.conf import settings
            filepath = os.path.join(settings.BASE_DIR, "uploads", "pdfs", "perfiles", str(empresa.id), f"{pk}.pdf")
            if not os.path.exists(filepath):
                try:
                    perfil = PerfilCargo.objects.get(pk=pk, empresa=empresa, activo=True)
                    generar_archivo_pdf_perfil_cargo(perfil, empresa)
                except Exception:
                    pass
            relative_url = f"/uploads/pdfs/perfiles/{empresa.id}/{pk}.pdf"
            return Response({"estado": "listo", "url": relative_url})
            
        return Response(status_data)


class CatalogoPeligrosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Auto-seed si la tabla está vacía
        if CatalogoPeligro.objects.count() == 0:
            from .catalogo_seeder import seed_gtc45_and_epp_catalogs
            seed_gtc45_and_epp_catalogs()

        peligros = CatalogoPeligro.objects.filter(activo=True).prefetch_related('epps_sugeridos')
        
        # Agrupar por tipo para el formato esperado por el frontend
        grouped = {}
        for p in peligros:
            if p.tipo not in grouped:
                grouped[p.tipo] = []
            grouped[p.tipo].append({
                'id': str(p.id),
                'tipo': p.tipo,
                'clasificacion': p.clasificacion,
                'descripcion': p.descripcion or '',
                'epps_sugeridos': [
                    {'id': str(e.id), 'nombre': e.nombre, 'descripcion': e.descripcion or ''}
                    for e in p.epps_sugeridos.all()
                ]
            })
        return Response(grouped)


class CatalogoEPPsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Auto-seed si la tabla está vacía
        if CatalogoEPP.objects.count() == 0:
            from .catalogo_seeder import seed_gtc45_and_epp_catalogs
            seed_gtc45_and_epp_catalogs()

        epps = CatalogoEPP.objects.filter(activo=True).order_by('nombre')
        serializer = CatalogoEPPSerializer(epps, many=True)
        return Response(serializer.data)


class SugerirPeligrosEPPsCargoView(APIView):
    """
    Analiza el nombre del cargo, área y propósito para identificar de forma determinística
    e inteligente los peligros GTC 45 aplicables y los EPPs obligatorios según la normativa colombiana.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Auto-seed si no hay datos
        if CatalogoPeligro.objects.count() == 0:
            from .catalogo_seeder import seed_gtc45_and_epp_catalogs
            seed_gtc45_and_epp_catalogs()

        nombre_cargo = request.data.get('nombre_cargo', '').lower()
        area = request.data.get('area', '').lower()
        texto = f"{nombre_cargo} {area}"

        peligros_all = CatalogoPeligro.objects.filter(activo=True).prefetch_related('epps_sugeridos')
        epps_all = CatalogoEPP.objects.filter(activo=True)

        peligro_match_ids = set()
        epp_match_ids = set()

        def match_peligro(palabras_clave):
            for p in peligros_all:
                for kw in palabras_clave:
                    if kw.lower() in p.clasificacion.lower() or kw.lower() in p.tipo.lower():
                        peligro_match_ids.add(str(p.id))
                        for e in p.epps_sugeridos.all():
                            epp_match_ids.add(str(e.id))

        def match_epp(palabras_clave):
            for e in epps_all:
                for kw in palabras_clave:
                    if kw.lower() in e.nombre.lower():
                        epp_match_ids.add(str(e.id))

        # 1. Reglas específicas por perfiles ocupacionales SG-SST
        if any(w in texto for w in ['admin', 'geren', 'jefe', 'asistent', 'secretari', 'auxiliar contable', 'contador', 'analista', 'abogad', 'recepcion', 'financier', 'rrhh', 'talento humano']):
            match_peligro(['Iluminación', 'Postura', 'Movimiento Repetitivo', 'Gestión Organizacional', 'Características de la Organización', 'Condiciones de la Tarea', 'Sismo'])

        if any(w in texto for w in ['operari', 'planta', 'producc', 'fabric', 'ensamble', 'maquinist', 'operador', 'molienda']):
            match_peligro(['Ruido', 'Polvos', 'Material Particulado', 'Esfuerzo Físico', 'Movimiento Repetitivo', 'Manipulación Manual', 'Mecánico', 'Locativo', 'Iluminación'])
            match_epp(['Casco', 'Gafas de seguridad', 'Protector auditivo', 'Guantes de vaqueta', 'Botas de seguridad con puntera'])

        if any(w in texto for w in ['conduct', 'chofer', 'transport', 'mensajer', 'motoriz', 'repartid', 'pesv', 'flota']):
            match_peligro(['Accidentes de Tránsito', 'Postura', 'Vibración', 'Público', 'Condiciones de la Tarea', 'Precipitaciones'])
            match_epp(['Chaleco reflectivo', 'Botas de seguridad'])

        if any(w in texto for w in ['mantenimient', 'mecanic', 'tecnic', 'electromecanic', 'taller']):
            match_peligro(['Mecánico', 'Eléctrico', 'Trabajo en Alturas', 'Espacios Confinados', 'Ruido', 'Líquidos', 'Manipulación Manual', 'Locativo'])
            match_epp(['Casco', 'Barbuquejo', 'Gafas de seguridad', 'Guantes anticorte', 'Botas de seguridad', 'Protector auditivo', 'Arnés'])

        if any(w in texto for w in ['electri', 'linier', 'redes', 'alta tension', 'baja tension']):
            match_peligro(['Eléctrico', 'Trabajo en Alturas', 'Mecánico', 'Tecnológico', 'Locativo'])
            match_epp(['Casco de seguridad industrial dieléctrico', 'Barbuquejo', 'Guantes dieléctricos', 'Botas de seguridad dieléctricas', 'Gafas de seguridad', 'Ropa de trabajo ignífuga', 'Arnés'])

        if any(w in texto for w in ['soldad', 'oxicode', 'metalmecanic', 'pailer', 'herreri']):
            match_peligro(['Radiaciones No Ionizantes', 'Humos Metálicos', 'Temperaturas Extremas', 'Mecánico', 'Ruido', 'Tecnológico'])
            match_epp(['Careta para soldadura', 'Respirador con filtros para humos metálicos', 'Guantes de vaqueta', 'Botas de seguridad con puntera', 'Protector auditivo'])

        if any(w in texto for w in ['bodeg', 'almacen', 'logisti', 'despach', 'estibador', 'cargue', 'descargue']):
            match_peligro(['Manipulación Manual', 'Esfuerzo Físico', 'Locativo', 'Accidentes de Tránsito', 'Material Particulado'])
            match_epp(['Casco', 'Botas de seguridad con puntera', 'Guantes de vaqueta', 'Chaleco reflectivo'])

        if any(w in texto for w in ['salud', 'enfermer', 'medic', 'aseo', 'limpieza', 'servicios generales', 'desinfecc']):
            match_peligro(['Virus', 'Bacterias', 'Fluidos', 'Líquidos', 'Postura', 'Movimiento Repetitivo'])
            match_epp(['Respirador libre de mantenimiento N95', 'Guantes de nitrilo', 'Monogafas', 'Delantal de PVC', 'Botas de caucho'])

        if any(w in texto for w in ['construcc', 'obra', 'albanil', 'maestro de obra', 'fierrer']):
            match_peligro(['Trabajo en Alturas', 'Locativo', 'Material Particulado', 'Ruido', 'Manipulación Manual', 'Mecánico', 'Sismo'])
            match_epp(['Casco', 'Barbuquejo', 'Gafas de seguridad', 'Botas de seguridad con puntera', 'Arnés', 'Eslinga', 'Protector auditivo', 'Guantes de vaqueta', 'Respirador libre de mantenimiento N95'])

        if any(w in texto for w in ['sst', 'seguridad y salud', 'hseq', 'hsec', 'inspector', 'coordinador sst', 'prevencion']):
            match_peligro(['Condiciones de la Tarea', 'Locativo', 'Accidentes de Tránsito', 'Iluminación', 'Sismo'])
            match_epp(['Casco', 'Barbuquejo', 'Gafas de seguridad', 'Botas de seguridad dieléctricas', 'Chaleco reflectivo'])

        # Si no hubo coincidencia específica, colocar un set base general preventivo
        if not peligro_match_ids:
            match_peligro(['Iluminación', 'Postura', 'Gestión Organizacional', 'Locativo', 'Sismo'])

        return Response({
            'peligros_sugeridos': list(peligro_match_ids),
            'epps_sugeridos': list(epp_match_ids),
            'total_peligros': len(peligro_match_ids),
            'total_epps': len(epp_match_ids)
        })
