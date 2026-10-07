import os
import time
import secrets
from datetime import timedelta
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from apps.accounts.permissions import EsAdmin
from apps.accounts.models import Usuario, UserRole, TokenActivacion
from apps.accounts.tasks import enviar_email_task
from apps.auditoria.models import AuditLog
from .models import Empresa, TransicionCapitulo

from .serializers import EmpresaSerializer, RegistroEmpresaSerializer
from .permissions import EsCorporativo, PerteneceAMismaEmpresaOAdmin
from .utils_ciiu import filtrar_candidatos, buscar_por_codigo_768, buscar_multiples_por_codigo_768
from .services_ia import IAContextoService


def get_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    return xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")


def clasificar_capitulo(num_trabajadores, nivel_riesgo):
    if nivel_riesgo >= 4:
        return "III"
    if num_trabajadores > 50:
        return "III"
    if num_trabajadores >= 11:
        return "II"
    return "I"


class EmpresaViewSet(viewsets.ModelViewSet):
    """CRUD completo de empresas — restringido a rol ADMIN."""
    queryset = Empresa.objects.filter(deleted_at__isnull=True)
    serializer_class = EmpresaSerializer
    permission_classes = [EsAdmin]

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.estado = Empresa.Estado.SUSPENDIDA
        instance.save(update_fields=["deleted_at", "estado"])


# ── GET /api/empresa/ciiu/buscar ──────────────────────────────────
class BuscarCiiuPublicoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query or len(query) < 2:
            return Response([])
        candidatos = filtrar_candidatos(descripcion_libre=query, max_resultados=15)
        return Response(candidatos)


# ── POST /api/empresa/registro ────────────────────────────────────
class RegistroEmpresaView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistroEmpresaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        nombre = data["nombre"]
        nit = data["nit"]
        num_trabajadores = data["num_trabajadores"]
        nivel_riesgo = data["nivel_riesgo"]
        representante_legal = data.get("representante_legal", "")
        arl = data.get("arl", "")
        sector_economico = data.get("sector_economico", "")
        ciudad = data.get("ciudad", "")

        responsable_nombre = data["responsable_nombre"]
        responsable_documento = data["responsable_documento"]
        responsable_email = data["responsable_email"]
        responsable_password = data["responsable_password"]

        capitulo = clasificar_capitulo(num_trabajadores, nivel_riesgo)

        ciiu_768_principal = data.get("ciiu_768_principal", "") or ""
        ciiu_codigo = data.get("ciiu_codigo", "") or ""
        ciiu_descripcion = data.get("ciiu_descripcion", "") or ""

        # Normalización de códigos Dec 768 (7 dígitos) y CIIU Rev. 4 (4 dígitos)
        if ciiu_768_principal and len(ciiu_768_principal) == 7 and not ciiu_codigo:
            found = buscar_por_codigo_768(ciiu_768_principal)
            if found:
                ciiu_codigo = found.get("ciiu_rev4", "")
        elif ciiu_codigo and len(ciiu_codigo) == 7:
            if not ciiu_768_principal:
                ciiu_768_principal = ciiu_codigo
            found = buscar_por_codigo_768(ciiu_768_principal)
            if found:
                ciiu_codigo = found.get("ciiu_rev4", "")

        with transaction.atomic():
            empresa = Empresa.objects.create(
                nombre=nombre,
                nit=nit,
                num_trabajadores=num_trabajadores,
                nivel_riesgo=nivel_riesgo,
                capitulo_vigente=capitulo,
                estado=Empresa.Estado.ACTIVA,
                representante_legal=representante_legal,
                arl=arl,
                sector_economico=sector_economico,
                ciudad=ciudad,
                ciiu_codigo=ciiu_codigo,
                ciiu_768_principal=ciiu_768_principal,
                ciiu_descripcion=ciiu_descripcion,
            )

            # Dividir responsable_nombre en first_name y last_name
            name_parts = responsable_nombre.split(" ", 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            username = f"{responsable_documento}_{nit}"

            usuario = Usuario.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                documento=responsable_documento,
                email=responsable_email,
                rol=UserRole.RESPONSABLE,
                empresa=empresa,
                activo=False,
                is_active=False,
                email_verificado=False,
            )
            usuario.set_password(responsable_password)
            usuario.save()

            token = TokenActivacion.objects.create(
                usuario=usuario,
                token=secrets.token_urlsafe(32),
                expira_en=timezone.now()
                + timedelta(hours=settings.ACTIVATION_TOKEN_EXPIRATION_HOURS),
            )

            AuditLog.objects.create(
                usuario=usuario,
                empresa=empresa,
                accion="REGISTRO_EMPRESA",
                tabla_afectada="empresas",
                registro_id=str(empresa.id),
                ip=get_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                ruta=request.path,
                metodo_http=request.method,
            )

        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173").rstrip("/")
        enlace = f"{frontend_url}/activar-cuenta?token={token.token}"

        cuerpo = render_to_string(
            "emails/activacion_cuenta.txt",
            {
                "usuario": usuario,
                "enlace": enlace,
            },
        )

        enviar_email_task.delay(
            "Activa tu cuenta en DiagnostISST",
            cuerpo,
            usuario.email,
        )

        usuario_data = {
            "id": str(usuario.id),
            "nombre": responsable_nombre,
            "documento": responsable_documento,
            "email": responsable_email,
            "rol": usuario.rol,
        }

        empresa_serializer = EmpresaSerializer(empresa)

        return Response(
            {
                "message": f"Empresa registrada exitosamente en Capítulo {capitulo}. Revisa tu correo electrónico para activar la cuenta.",
                "empresa": empresa_serializer.data,
                "usuario": usuario_data,
            },
            status=status.HTTP_201_CREATED,
        )


# ── GET /api/empresa/:id ──────────────────────────────────────────
class ObtenerEmpresaView(APIView):
    permission_classes = [IsAuthenticated, PerteneceAMismaEmpresaOAdmin]

    def get(self, request, id):
        empresa = get_object_or_404(Empresa, id=id, deleted_at__isnull=True)
        self.check_object_permissions(request, empresa)
        serializer = EmpresaSerializer(empresa)
        return Response(serializer.data)


# ── GET/PUT /api/modulo0/contexto ─────────────────────────────────
class ContextoEmpresaView(APIView):
    permission_classes = [IsAuthenticated, EsCorporativo]

    def get(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response(
                {"message": "Identificador de empresa no provisto en la solicitud."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = EmpresaSerializer(empresa)
        return Response(serializer.data)

    def put(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response(
                {"message": "Identificador de empresa no provisto."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        fields = [
            "ciiu_codigo",
            "ciiu_descripcion",
            "representante_legal",
            "arl",
            "sector_economico",
            "ciudad",
            "num_trabajadores",
            "nivel_riesgo",
            "ciiu_768_principal",
            "ciiu_768_secundarios",
            "ciiu_768_metadata",
        ]

        old_data = {}
        for f in fields:
            old_data[f] = getattr(empresa, f)

        # Crear dict con nuevos datos
        datos_nuevos = {}
        for f in fields:
            if f in request.data:
                val = request.data[f]
                if f in ["num_trabajadores", "nivel_riesgo"] and val is not None:
                    datos_nuevos[f] = int(val)
                else:
                    datos_nuevos[f] = val

        if not datos_nuevos:
            serializer = EmpresaSerializer(empresa)
            return Response(
                {
                    "message": "Datos de la organización actualizados con éxito.",
                    "empresa": serializer.data,
                }
            )

        # ── Detección de cambio de capítulo ──────────────────────────
        target_trabajadores = datos_nuevos.get("num_trabajadores", empresa.num_trabajadores)
        target_riesgo = datos_nuevos.get("nivel_riesgo", empresa.nivel_riesgo)
        capitulo_calculado = clasificar_capitulo(target_trabajadores, target_riesgo)
        confirmar = request.data.get("confirmar_transicion") is True

        # Si el nuevo contexto implica un cambio de capítulo y NO ha sido confirmado:
        # NO PERSISTIR el nuevo contexto aún y devolver la respuesta estructurada de confirmación.
        if capitulo_calculado != empresa.capitulo_vigente and not confirmar:
            return Response(
                {
                    "success": False,
                    "code": "CHAPTER_CHANGE_REQUIRES_CONFIRMATION",
                    "message": "Las condiciones actuales de la empresa corresponden a un capítulo normativo diferente.",
                    "data": {
                        "capitulo_anterior": empresa.capitulo_vigente,
                        "capitulo_nuevo": capitulo_calculado,
                        "num_trabajadores": target_trabajadores,
                        "nivel_riesgo": target_riesgo,
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            for key, val in datos_nuevos.items():
                setattr(empresa, key, val)
            empresa.save()

            # Guardar en log de auditoría
            new_data_logged = {f: getattr(empresa, f) for f in fields}
            AuditLog.objects.create(
                usuario=request.user,
                empresa=empresa,
                accion="ACTUALIZAR_CONTEXTO_EMPRESA",
                tabla_afectada="empresas",
                registro_id=str(empresa.id),
                valores_anteriores=old_data,
                valores_nuevos=new_data_logged,
                ip=get_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                ruta=request.path,
                metodo_http=request.method,
            )

        serializer = EmpresaSerializer(empresa)
        return Response(
            {
                "message": "Datos de la organización actualizados con éxito.",
                "empresa": serializer.data,
            }
        )


# ── POST /api/modulo0/transicion-capitulo ─────────────────────────
class TransicionCapituloView(APIView):
    """Confirmación e instrumentación de transición atómica de capítulo."""
    permission_classes = [IsAuthenticated, EsCorporativo]

    def post(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response({"success": False, "code": "RESOURCE_NOT_FOUND", "message": "Sin empresa asociada."}, status=400)

        num_trabajadores = int(request.data.get("num_trabajadores", empresa.num_trabajadores))
        nivel_riesgo = int(request.data.get("nivel_riesgo", empresa.nivel_riesgo))
        motivo = str(request.data.get("motivo", "")).strip()

        capitulo_calculado = clasificar_capitulo(num_trabajadores, nivel_riesgo)
        capitulo_anterior = empresa.capitulo_vigente

        if capitulo_calculado == capitulo_anterior:
            return Response(
                {
                    "success": False,
                    "code": "SAME_CHAPTER_TRANSITION_INVALID",
                    "message": "No fue posible realizar el cambio de capítulo porque las condiciones actuales de la empresa no corresponden a la transición solicitada.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.estandares.models import Evaluacion, Respuesta
        from django.db.models import Sum
        from datetime import datetime

        contexto_anterior = {
            "num_trabajadores": empresa.num_trabajadores,
            "nivel_riesgo": empresa.nivel_riesgo,
        }
        contexto_nuevo = {
            "num_trabajadores": num_trabajadores,
            "nivel_riesgo": nivel_riesgo,
        }

        anio_actual = datetime.now().year

        with transaction.atomic():
            # 1. Actualizar contexto y capítulo de la empresa conjuntamente
            empresa.num_trabajadores = num_trabajadores
            empresa.nivel_riesgo = nivel_riesgo
            empresa.capitulo_vigente = capitulo_calculado
            empresa.save(update_fields=["num_trabajadores", "nivel_riesgo", "capitulo_vigente", "updated_at"])

            # 2. Actualizar capítulo de la Evaluación activa MANTENIENDO la misma Evaluacion.id = X
            evaluacion, _ = Evaluacion.objects.get_or_create(
                empresa=empresa,
                anio=anio_actual,
                defaults={"capitulo": capitulo_calculado},
            )
            evaluacion.capitulo = capitulo_calculado
            # Recalcular puntaje total sumando SOLO respuestas pertenecientes al nuevo capítulo
            puntaje_total = (
                Respuesta.objects.filter(evaluacion=evaluacion, estandar__capitulo=capitulo_calculado)
                .aggregate(total=Sum("puntaje"))["total"]
                or 0
            )
            evaluacion.puntaje_total = puntaje_total
            evaluacion.save(update_fields=["capitulo", "puntaje_total", "updated_at"])

            # 3. Registrar historial inmutable TransicionCapitulo
            transicion = TransicionCapitulo.objects.create(
                empresa=empresa,
                evaluacion=evaluacion,
                capitulo_anterior=capitulo_anterior,
                capitulo_nuevo=capitulo_calculado,
                usuario=request.user,
                motivo=motivo or "Actualización de contexto organizacional",
                contexto_anterior=contexto_anterior,
                contexto_nuevo=contexto_nuevo,
            )

            # 4. Registrar AuditLog
            AuditLog.objects.create(
                usuario=request.user,
                empresa=empresa,
                accion="TRANSICION_CAPITULO",
                tabla_afectada="empresas",
                registro_id=str(empresa.id),
                valores_anteriores={"capitulo_vigente": capitulo_anterior, **contexto_anterior},
                valores_nuevos={"capitulo_vigente": capitulo_calculado, **contexto_nuevo},
                ip=get_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                ruta=request.path,
                metodo_http=request.method,
            )

        serializer = EmpresaSerializer(empresa)
        return Response(
            {
                "success": True,
                "message": f"Transición de capítulo realizada con éxito: Capítulo {capitulo_anterior} -> Capítulo {capitulo_calculado}.",
                "empresa": serializer.data,
                "transicion": {
                    "id": str(transicion.id),
                    "capitulo_anterior": capitulo_anterior,
                    "capitulo_nuevo": capitulo_calculado,
                    "created_at": transicion.created_at.isoformat(),
                    "evaluacion_id": str(evaluacion.id),
                },
            }
        )


# ── GET /api/modulo0/historial-transiciones ───────────────────────
class HistorialTransicionesCapituloView(APIView):
    """Consulta el historial inmutable de transiciones de capítulo de la empresa."""
    permission_classes = [IsAuthenticated, PerteneceAMismaEmpresaOAdmin]

    def get(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response({"success": False, "code": "RESOURCE_NOT_FOUND", "message": "Sin empresa asociada."}, status=400)

        transiciones = TransicionCapitulo.objects.filter(empresa=empresa).select_related("usuario").order_by("-created_at")
        data = []
        for t in transiciones:
            data.append({
                "id": str(t.id),
                "capitulo_anterior": t.capitulo_anterior,
                "capitulo_nuevo": t.capitulo_nuevo,
                "usuario_nombre": t.usuario.get_full_name() or t.usuario.username,
                "usuario_email": t.usuario.email,
                "motivo": t.motivo,
                "contexto_anterior": t.contexto_anterior,
                "contexto_nuevo": t.contexto_nuevo,
                "created_at": t.created_at.isoformat(),
            })
        return Response(data)



# ── POST /api/modulo0/contexto/logo ───────────────────────────────
class UploadLogoEmpresaView(APIView):
    permission_classes = [IsAuthenticated, EsCorporativo]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response(
                {"message": "Identificador de empresa no provisto."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logo_file = request.FILES.get("logo")
        if not logo_file:
            return Response(
                {"message": "Archivo de logotipo requerido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validar tipo de archivo
        valid_extensions = [".png", ".jpg", ".jpeg", ".webp"]
        ext = os.path.splitext(logo_file.name)[1].lower()
        if ext not in valid_extensions:
            return Response(
                {
                    "message": "Formato de imagen inválido. Solo se admiten extensiones PNG, JPG, JPEG y WebP."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validar tamaño máximo: 2MB
        max_size = 2 * 1024 * 1024
        if logo_file.size > max_size:
            return Response(
                {"message": "La imagen excede el límite de 2MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Crear directorio
        logos_dir = os.path.join(settings.BASE_DIR, "uploads", "logos")
        os.makedirs(logos_dir, exist_ok=True)

        unique_name = f"logo_{empresa.id}_{int(time.time())}{ext}"
        final_path = os.path.join(logos_dir, unique_name)

        # Guardar archivo
        with open(final_path, "wb+") as destination:
            for chunk in logo_file.chunks():
                destination.write(chunk)

        url = f"/uploads/logos/{unique_name}"

        # Actualizar base de datos
        empresa.logo_url = url
        empresa.save(update_fields=["logo_url"])

        return Response(
            {
                "message": "Logotipo subido correctamente.",
                "logo_url": url,
            }
        )


# ── GET /api/modulo0/completitud ──────────────────────────────────
class ResumenCompletitudView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response(
                {"message": "Identificador de empresa no provisto."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        campos_faltantes = []

        # Hito 1: Datos Base (20%)
        c_base = [
            ("ciiu_codigo", "Código CIIU"),
            ("ciiu_descripcion", "Descripción CIIU"),
            ("representante_legal", "Representante Legal"),
            ("arl", "ARL asignada"),
            ("sector_economico", "Sector Económico"),
            ("ciudad", "Ciudad principal"),
        ]
        base_completado = True
        for campo, label in c_base:
            val = getattr(empresa, campo)
            if val is None or str(val).strip() == "":
                base_completado = False
                campos_faltantes.append(label)

        # Hito 2: Identidad Corporativa (20%)
        identidad_completado = True
        valores_array = empresa.valores if empresa.valores else []
        if not empresa.mision or str(empresa.mision).strip() == "":
            identidad_completado = False
            campos_faltantes.append("Misión de la empresa")
        if not empresa.vision or str(empresa.vision).strip() == "":
            identidad_completado = False
            campos_faltantes.append("Visión de la empresa")
        if not valores_array or len(valores_array) == 0:
            identidad_completado = False
            campos_faltantes.append("Valores corporativos")

        # Hito 3: Sede Principal (20%)
        sedes_count = empresa.sedes.filter(activa=True).count()
        sedes_completado = sedes_count > 0
        if not sedes_completado:
            campos_faltantes.append("Registrar al menos una sede")

        # Hito 4: Procesos Organizacionales (20%)
        procesos_count = empresa.procesos.filter(activo=True).count()
        procesos_completado = procesos_count > 0
        if not procesos_completado:
            campos_faltantes.append("Registrar al menos un proceso")

        # Hito 5: Organigrama / Cargos (20%)
        organigrama_count = empresa.organigrama.filter(activo=True).count()
        organigrama_completado = organigrama_count > 0
        if not organigrama_completado:
            campos_faltantes.append("Registrar al menos un cargo en el organigrama")

        hitos = [
            {"nombre": "Datos Generales", "completado": base_completado},
            {"nombre": "Identidad Estratégica", "completado": identidad_completado},
            {"nombre": "Sedes Operativas", "completado": sedes_completado},
            {"nombre": "Estructura de Procesos", "completado": procesos_completado},
            {"nombre": "Organigrama Funcional", "completado": organigrama_completado},
        ]

        completados_count = sum(1 for h in hitos if h["completado"])
        porcentaje = completados_count * 20

        return Response(
            {
                "porcentaje": porcentaje,
                "hitos": hitos,
                "campos_faltantes": campos_faltantes,
            }
        )


# ── POST /api/modulo0/contexto/ciiu/sugerir ───────────────────────
class SugerirCiiuIAView(APIView):
    permission_classes = [IsAuthenticated, EsCorporativo]

    def post(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response(
                {"message": "Identificador de empresa no provisto."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        descripcion_actividad = request.data.get("descripcion_actividad")
        sector = request.data.get("sector")
        clase_riesgo = request.data.get("clase_riesgo")

        is_auto = not descripcion_actividad
        desc_libre = descripcion_actividad or ""
        falta_contexto = False

        procesos = empresa.procesos.filter(activo=True)

        if is_auto:
            parts = [
                f"Empresa: {empresa.nombre}",
                f"Sector: {sector}" if sector else (f"Sector: {empresa.sector_economico}" if empresa.sector_economico else ""),
                f"Misión: {empresa.mision}" if empresa.mision else "",
                f"Visión: {empresa.vision}" if empresa.vision else "",
                f"Procesos: {', '.join([p.nombre for p in procesos])}" if procesos.exists() else "",
            ]
            desc_libre = ". ".join([p for p in parts if p])

            if (
                not empresa.mision
                or not empresa.vision
                or not (sector or empresa.sector_economico)
                or not (clase_riesgo or empresa.nivel_riesgo)
                or not procesos.exists()
            ):
                falta_contexto = True

        sector_para_candidatos = sector or (empresa.sector_economico if is_auto else None)
        clase_riesgo_para_candidatos = int(clase_riesgo) if clase_riesgo else (empresa.nivel_riesgo if is_auto else None)

        texto_filtrado_candidatos = (
            " ".join([empresa.nombre, sector_para_candidatos or "", " ".join([p.nombre for p in procesos])])
            if is_auto
            else desc_libre
        )

        candidatos = filtrar_candidatos(
            sector=sector_para_candidatos,
            descripcion_libre=texto_filtrado_candidatos,
            clase_riesgo=clase_riesgo_para_candidatos,
            max_resultados=12,
        )

        result = IAContextoService.sugerir_codigo_ciiu(
            nombre=empresa.nombre,
            sector=sector_para_candidatos or "General",
            descripcion_actividad=desc_libre,
            candidatos=candidatos,
        )

        return Response(
            {
                "resultado": result["sugerencia"],
                "fuente": result["fuente"],
                "candidatos_evaluados": candidatos,
                "falta_contexto": falta_contexto,
            }
        )


# ── POST /api/modulo0/contexto/ciiu/describir ──────────────────────
class DescribirCiiuIAView(APIView):
    permission_classes = [IsAuthenticated, EsCorporativo]

    def post(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response(
                {"message": "Identificador de empresa no provisto."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        codigo_principal = request.data.get("codigo_principal")
        codigos_secundarios = request.data.get("codigos_secundarios")

        if not codigo_principal:
            return Response(
                {"message": "Código principal CIIU 768 requerido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        registro_principal = buscar_por_codigo_768(codigo_principal)
        if not registro_principal:
            return Response(
                {"message": f"El código principal {codigo_principal} no existe en el catálogo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        registros_secundarios = (
            buscar_multiples_por_codigo_768(codigos_secundarios)
            if codigos_secundarios and isinstance(codigos_secundarios, list)
            else []
        )

        result = IAContextoService.describir_codigo_ciiu(
            nombre=empresa.nombre,
            sector=empresa.sector_economico or "General",
            registro_principal=registro_principal,
            registros_secundarios=registros_secundarios,
        )

        return Response(
            {
                "resultado": result["descripcion"],
                "fuente": result["fuente"],
            }
        )


# ── PUT /api/modulo0/identidad ────────────────────────────────────
class UpdateIdentidadView(APIView):
    permission_classes = [IsAuthenticated, EsCorporativo]

    def put(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response(
                {"message": "Identificador de empresa no provisto."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        mision = request.data.get("mision")
        vision = request.data.get("vision")
        valores = request.data.get("valores")

        old_data = {
            "mision": empresa.mision,
            "vision": empresa.vision,
            "valores": empresa.valores,
        }

        data_updated = {}
        if mision is not None:
            empresa.mision = mision
            data_updated["mision"] = mision
        if vision is not None:
            empresa.vision = vision
            data_updated["vision"] = vision
        if valores is not None:
            empresa.valores = valores
            data_updated["valores"] = valores

        with transaction.atomic():
            empresa.save()

            AuditLog.objects.create(
                usuario=request.user,
                empresa=empresa,
                accion="ACTUALIZAR_IDENTIDAD_EMPRESA",
                tabla_afectada="empresas",
                registro_id=str(empresa.id),
                valores_anteriores=old_data,
                valores_nuevos=data_updated,
                ip=get_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                ruta=request.path,
                metodo_http=request.method,
            )

        serializer = EmpresaSerializer(empresa)
        return Response(
            {
                "message": "Identidad estratégica corporativa actualizada con éxito.",
                "empresa": serializer.data,
            }
        )


# ── POST /api/modulo0/identidad/sugerir-ia ────────────────────────
class SugerirIdentidadIAView(APIView):
    permission_classes = [IsAuthenticated, EsCorporativo]

    def post(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response(
                {"message": "Identificador de empresa no provisto."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = IAContextoService.sugerir_identidad(
            nombre=empresa.nombre,
            sector=empresa.sector_economico or "",
            ciiu_desc=empresa.ciiu_descripcion or "",
        )

        return Response(result)
