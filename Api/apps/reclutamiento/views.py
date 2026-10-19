"""
Vistas y ViewSets REST para Reclutamiento y Selección — FOSST V.I.D.A.
Fase D: Endpoints para Banco de Talento, Vacantes, Procesos de Selección,
Postulaciones (Máquina de Estados y Trazabilidad) y Etapas (Entrevista, Evaluación, Validación).

Convenciones respetadas:
- Herencia de `EmpresaScopedViewSet` (aislamiento multi-tenant estricto y soft-delete).
- Los ViewSets NO contienen lógica de negocio; delegan exclusivamente en `services.postulacion` y `services.etapas`.
- Manejo determinista de excepciones de dominio con HTTP 400.
"""
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q, Count
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from apps.common.mixins import EmpresaScopedViewSet
from apps.common.permissions import IsRol, IsRolParaEscritura
from apps.evidencias.models import Archivo

Usuario = get_user_model()
from apps.reclutamiento.models import (
    FuenteReclutamiento,
    Candidato,
    PerfilCandidato,
    CandidatoDocumento,
    Vacante,
    ProcesoSeleccion,
    Postulacion,
    PostulacionEvento,
    Entrevista,
    Evaluacion,
    ValidacionDocumental,
)
from apps.reclutamiento.serializers import (
    FuenteReclutamientoSerializer,
    CandidatoListSerializer,
    CandidatoDetailSerializer,
    CandidatoCreateUpdateSerializer,
    CandidatoDocumentoSerializer,
    PerfilCandidatoSerializer,
    VacanteListSerializer,
    VacanteDetailSerializer,
    VacanteCreateUpdateSerializer,
    ProcesoSeleccionDetailSerializer,
    ProcesoSeleccionUpdateSerializer,
    PostulacionListSerializer,
    PostulacionDetailSerializer,
    EntrevistaSerializer,
    EvaluacionSerializer,
    ValidacionDocumentalSerializer,
    PostulacionEventoSerializer,
    PostularCandidatoSerializer,
    PreseleccionarActionSerializer,
    RegistrarEntrevistaActionSerializer,
    RegistrarEvaluacionActionSerializer,
    RegistrarValidacionActionSerializer,
    SeleccionarActionSerializer,
    CerrarPostulacionActionSerializer,
    ReabrirPostulacionActionSerializer,
)
from apps.reclutamiento.services.transiciones import (
    TransicionInvalidaError,
    RequisitoIncumplidoError,
    EtapaObligatoriaFaltanteError,
    MotivoRequeridoError,
    CuposAgotadosError,
    ExcepcionNoAutorizadaError,
    EntrevistaDesfavorableError,
)
from apps.reclutamiento.services.postulacion import (
    transicionar_postulacion,
    registrar_postulacion,
    preseleccionar_candidato,
    seleccionar_candidato,
    cerrar_postulacion,
    reabrir_postulacion_excepcional,
)
from apps.reclutamiento.services.etapas import (
    registrar_y_completar_entrevista,
    registrar_y_completar_evaluacion,
    registrar_y_completar_validacion,
)


class FuenteReclutamientoViewSet(EmpresaScopedViewSet):
    """
    CRUD de catálogo de fuentes de atracción de talento por empresa y métricas de efectividad.
    """
    queryset = FuenteReclutamiento.objects.all()
    serializer_class = FuenteReclutamientoSerializer
    permission_classes = [IsAuthenticated, IsRolParaEscritura.de("responsable", "admin")]

    def list(self, request, *args, **kwargs):
        # Al abrir el catálogo se garantizan las fuentes semilla de la empresa
        empresa = getattr(request.user, "empresa", None)
        if empresa:
            from apps.reclutamiento.services.fuentes import asegurar_fuentes_sistema
            asegurar_fuentes_sistema(empresa)
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["get"], url_path="indicadores-efectividad")
    def indicadores_efectividad(self, request):
        """
        GET /api/reclutamiento/fuentes/indicadores-efectividad/
        Devuelve el embudo completo de conversión por fuente de reclutamiento (§2.1),
        incluyendo el bucket "Sin fuente".
        """
        empresa = request.user.empresa
        if not empresa and request.user.rol != "ADMIN":
            return Response({"error": "Sin empresa asociada."}, status=400)

        def metricas(postulaciones):
            candidatos_count = postulaciones.count()
            preseleccionados = postulaciones.filter(
                estado__in=[
                    Postulacion.Estado.PRESELECCIONADO,
                    Postulacion.Estado.EN_ENTREVISTA,
                    Postulacion.Estado.EN_EVALUACION,
                    Postulacion.Estado.EN_VALIDACION,
                    Postulacion.Estado.SELECCIONADO,
                ]
            ).count()
            entrevistados = postulaciones.filter(
                estado__in=[
                    Postulacion.Estado.EN_ENTREVISTA,
                    Postulacion.Estado.EN_EVALUACION,
                    Postulacion.Estado.EN_VALIDACION,
                    Postulacion.Estado.SELECCIONADO,
                ]
            ).count()
            contratados = postulaciones.filter(estado=Postulacion.Estado.SELECCIONADO).count()
            tasa = round((contratados / candidatos_count) * 100, 2) if candidatos_count > 0 else 0.0
            return {
                "candidatos": candidatos_count,
                "preseleccionados": preseleccionados,
                "entrevistados": entrevistados,
                "contratados": contratados,
                "tasa_conversion_porcentaje": tasa,
            }

        resultado = []
        for fuente in self.get_queryset():
            postulaciones = Postulacion.objects.filter(
                empresa=empresa,
                candidato__fuente_reclutamiento=fuente,
                deleted_at__isnull=True,
            )
            resultado.append({
                "fuente_id": str(fuente.id),
                "fuente_nombre": fuente.nombre,
                **metricas(postulaciones),
            })

        sin_fuente = Postulacion.objects.filter(
            empresa=empresa,
            candidato__fuente_reclutamiento__isnull=True,
            deleted_at__isnull=True,
        )
        resultado.append({
            "fuente_id": "",
            "fuente_nombre": "Sin fuente",
            **metricas(sin_fuente),
        })

        return Response(resultado)


class CandidatoViewSet(EmpresaScopedViewSet):
    """
    Banco de Talento (RN-R10): CRUD centralizado de candidatos independientes de postulaciones.
    Búsqueda por texto libre (nombre, documento, email, ciudad, habilidades) y filtros de competencias.
    """
    queryset = Candidato.objects.all()
    permission_classes = [IsAuthenticated, IsRolParaEscritura.de("responsable", "admin")]

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related("fuente_reclutamiento", "perfil").annotate(
            postulaciones_count=Count("postulaciones", filter=Q(postulaciones__deleted_at__isnull=True))
        )

        # Filtro de búsqueda por texto libre
        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(nombres__icontains=search)
                | Q(apellidos__icontains=search)
                | Q(documento__icontains=search)
                | Q(email__icontains=search)
                | Q(telefono__icontains=search)
                | Q(ciudad__icontains=search)
                | Q(perfil__titulo_profesional__icontains=search)
            )

        # Filtro por fuente
        fuente_id = self.request.query_params.get("fuente_id")
        if fuente_id:
            qs = qs.filter(fuente_reclutamiento_id=fuente_id)

        # Filtro por etiqueta / competencia
        etiqueta = self.request.query_params.get("etiqueta")
        if etiqueta:
            qs = qs.filter(etiquetas__contains=[etiqueta])

        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return CandidatoListSerializer
        if self.action in ["retrieve"]:
            return CandidatoDetailSerializer
        return CandidatoCreateUpdateSerializer

    @action(detail=True, methods=["post"], url_path="vincular-documento")
    def vincular_documento(self, request, pk=None):
        """Asocia un archivo existente al candidato."""
        candidato = self.get_object()
        archivo_id = request.data.get("archivo_id")
        tipo_doc = request.data.get("tipo_documento", CandidatoDocumento.TipoDocumento.HOJA_DE_VIDA)
        nombre_desc = request.data.get("nombre_descriptivo", "")

        if not archivo_id:
            return Response({"detail": "archivo_id es obligatorio"}, status=status.HTTP_400_BAD_REQUEST)

        doc = CandidatoDocumento.objects.create(
            candidato=candidato,
            archivo_id=archivo_id,
            tipo_documento=tipo_doc,
            nombre_descriptivo=nombre_desc,
        )
        return Response(CandidatoDocumentoSerializer(doc).data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["post"],
        url_path="subir-documento",
        parser_classes=[MultiPartParser, FormParser],
    )
    def subir_documento(self, request, pk=None):
        """
        Sube un documento del candidato (hoja de vida, certificación, licencia, etc.)
        al almacenamiento central (S3/MinIO) con validación de MIME/tamaño y hash SHA-256.
        multipart/form-data: archivo, tipo_documento, nombre_descriptivo.
        """
        from django.core.exceptions import ValidationError as DjangoValidationError
        from apps.common.storage import validate_and_process_file

        candidato = self.get_object()
        archivo_file = request.FILES.get("archivo")
        if not archivo_file:
            return Response(
                {"detail": "El archivo es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tipo_doc = request.data.get("tipo_documento", CandidatoDocumento.TipoDocumento.HOJA_DE_VIDA)
        if tipo_doc not in dict(CandidatoDocumento.TipoDocumento.choices):
            return Response(
                {"detail": "Tipo de documento inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            meta = validate_and_process_file(
                archivo_file, folder="candidatos", filename=archivo_file.name
            )
        except DjangoValidationError as exc:
            detail = getattr(exc, "message", None) or getattr(exc, "detail", None) or str(exc)
            return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        archivo = Archivo.objects.create(
            nombre=meta["original_name"],
            url=meta["url"] if isinstance(meta["url"], str) else "",
            tipo_mime=meta["mime_type"],
            tamanio_kb=round(meta["size_bytes"] / 1024),
            subido_por=getattr(request.user, "email", "") or getattr(request.user, "username", ""),
            sha256_hash=meta["sha256_hash"],
        )
        doc = CandidatoDocumento.objects.create(
            candidato=candidato,
            archivo=archivo,
            tipo_documento=tipo_doc,
            nombre_descriptivo=request.data.get("nombre_descriptivo") or meta["original_name"],
        )
        return Response(CandidatoDocumentoSerializer(doc).data, status=status.HTTP_201_CREATED)


class VacanteViewSet(EmpresaScopedViewSet):
    """
    CRUD de requerimientos / vacantes de personal vinculadas a PerfilCargo.
    """
    queryset = Vacante.objects.all()
    permission_classes = [IsAuthenticated, IsRolParaEscritura.de("responsable", "admin")]

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related("perfil_cargo", "sede", "proceso_seleccion").annotate(
            postulaciones_count=Count(
                "proceso_seleccion__postulaciones",
                filter=Q(proceso_seleccion__postulaciones__deleted_at__isnull=True),
            )
        )

        estado = self.request.query_params.get("estado")
        if estado:
            qs = qs.filter(estado=estado)

        modalidad = self.request.query_params.get("modalidad")
        if modalidad:
            qs = qs.filter(modalidad=modalidad)

        perfil_cargo_id = self.request.query_params.get("perfil_cargo_id")
        if perfil_cargo_id:
            qs = qs.filter(perfil_cargo_id=perfil_cargo_id)

        sede_id = self.request.query_params.get("sede_id")
        if sede_id:
            qs = qs.filter(sede_id=sede_id)

        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return VacanteListSerializer
        if self.action == "retrieve":
            return VacanteDetailSerializer
        return VacanteCreateUpdateSerializer

    @action(detail=True, methods=["post"], url_path="publicar")
    def publicar(self, request, pk=None):
        vacante = self.get_object()
        vacante.estado = Vacante.Estado.ABIERTA
        vacante.publicada_en_portal = True
        vacante.save()
        return Response(VacanteDetailSerializer(vacante).data)

    @action(detail=True, methods=["post"], url_path="pausar")
    def pausar(self, request, pk=None):
        vacante = self.get_object()
        vacante.estado = Vacante.Estado.PAUSADA
        vacante.publicada_en_portal = False
        vacante.save()
        return Response(VacanteDetailSerializer(vacante).data)

    @action(detail=True, methods=["post"], url_path="cerrar")
    def cerrar(self, request, pk=None):
        vacante = self.get_object()
        vacante.estado = Vacante.Estado.CERRADA
        vacante.publicada_en_portal = False
        vacante.save()
        return Response(VacanteDetailSerializer(vacante).data)

    @action(
        detail=True,
        methods=["get"],
        url_path="informe-gerencial",
        permission_classes=[IsAuthenticated, IsRol.de("responsable")],
    )
    def informe_gerencial(self, request, pk=None):
        """Informe gerencial agregado y anonimizado de la vacante, con análisis IA."""
        from apps.reclutamiento.services.informe_gerencial import generar_informe_gerencial

        vacante = self.get_object()
        forzar = request.query_params.get("forzar") in ("1", "true", "True")
        informe = generar_informe_gerencial(vacante.empresa, vacante, forzar=forzar)
        return Response(informe)

    @action(
        detail=True,
        methods=["get"],
        url_path="informe-gerencial/pdf",
        permission_classes=[IsAuthenticated, IsRol.de("responsable")],
    )
    def informe_gerencial_pdf(self, request, pk=None):
        """Descarga el informe gerencial en PDF."""
        from django.http import HttpResponse
        from apps.reclutamiento.services.informe_gerencial import (
            generar_informe_gerencial,
            render_pdf,
        )

        vacante = self.get_object()
        forzar = request.query_params.get("forzar") in ("1", "true", "True")
        informe = generar_informe_gerencial(vacante.empresa, vacante, forzar=forzar)
        pdf = render_pdf(informe)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="informe_gerencial_{vacante.codigo}.pdf"'
        )
        return response


class ProcesoSeleccionViewSet(EmpresaScopedViewSet):
    """
    Convocatoria de selección activa para una vacante. Detalle con postulaciones y semáforo de etapas.
    """
    queryset = ProcesoSeleccion.objects.all()
    permission_classes = [IsAuthenticated, IsRolParaEscritura.de("responsable", "admin")]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related(
            "vacante", "vacante__perfil_cargo", "vacante__sede", "responsable_rh"
        ).prefetch_related(
            "postulaciones__candidato",
            "postulaciones__candidato__documentos",
            "postulaciones__proceso_seleccion",
        )

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return ProcesoSeleccionDetailSerializer
        return ProcesoSeleccionUpdateSerializer

    @action(detail=True, methods=["post"], url_path="postular")
    def postular(self, request, pk=None):
        """
        Registra un candidato existente en el banco de talento al proceso de selección.
        """
        proceso = self.get_object()
        candidato_id = request.data.get("candidato_id")

        if not candidato_id:
            return Response({"detail": "candidato_id es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            candidato = Candidato.objects.get(
                id=candidato_id,
                empresa=proceso.empresa,
                deleted_at__isnull=True,
            )
        except Candidato.DoesNotExist:
            return Response({"detail": "Candidato no encontrado en su empresa."}, status=status.HTTP_404_NOT_FOUND)

        if Postulacion.objects.filter(
            proceso_seleccion=proceso, candidato=candidato, deleted_at__isnull=True
        ).exists():
            return Response(
                {"detail": "El candidato ya tiene una postulación activa en este proceso."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        postulacion = registrar_postulacion(
            candidato=candidato,
            proceso_seleccion=proceso,
            usuario=request.user,
        )

        return Response(
            PostulacionDetailSerializer(postulacion).data,
            status=status.HTTP_201_CREATED,
        )


class PostulacionViewSet(EmpresaScopedViewSet):
    """
    Controlador de la Máquina de Estados de Postulación.
    Todas las transiciones de estado ocurren a través de endpoints de acción dedicados (RN-R01).
    """
    queryset = Postulacion.objects.all()
    permission_classes = [IsAuthenticated, IsRolParaEscritura.de("responsable", "admin")]

    def get_queryset(self):
        qs = super().get_queryset()
        proceso_id = self.request.query_params.get("proceso_seleccion_id")
        if proceso_id:
            qs = qs.filter(proceso_seleccion_id=proceso_id)

        estado = self.request.query_params.get("estado")
        if estado:
            qs = qs.filter(estado=estado)

        candidato_id = self.request.query_params.get("candidato_id")
        if candidato_id:
            qs = qs.filter(candidato_id=candidato_id)

        return qs.select_related(
            "candidato",
            "candidato__perfil",
            "proceso_seleccion",
            "proceso_seleccion__vacante",
            "autorizado_por",
        ).prefetch_related(
            "eventos__usuario",
            "entrevistas__entrevistador",
            "evaluaciones__evaluador",
            "evaluaciones__archivo_informe",
            "validaciones_documentales__verificado_por",
            "validaciones_documentales__soporte_archivo",
            "candidato__documentos",
        )

    def get_serializer_class(self):
        if self.action == "list":
            return PostulacionListSerializer
        return PostulacionDetailSerializer

    @action(detail=True, methods=["post"], url_path="preseleccionar")
    def preseleccionar(self, request, pk=None):
        """
        RN-R02: Valida requisitos obligatorios y avanza a PRESELECCIONADO.
        """
        postulacion = self.get_object()
        serializer = PreseleccionarActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            postulacion_actualizada = preseleccionar_candidato(
                postulacion=postulacion,
                calificacion_requisitos=serializer.validated_data["calificacion_requisitos"],
                puntuacion=serializer.validated_data.get("puntuacion"),
                usuario=request.user,
                es_excepcion=serializer.validated_data.get("es_excepcion", False),
                justificacion_excepcion=serializer.validated_data.get("justificacion_excepcion", ""),
            )
            return Response(PostulacionDetailSerializer(postulacion_actualizada).data)
        except (TransicionInvalidaError, RequisitoIncumplidoError, ExcepcionNoAutorizadaError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="registrar-entrevista")
    def registrar_entrevista(self, request, pk=None):
        """
        Registra una entrevista y actualiza la máquina de estados.
        """
        postulacion = self.get_object()
        serializer = RegistrarEntrevistaActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        entrevistador = None
        if data.get("entrevistador_id"):
            entrevistador = Usuario.objects.filter(id=data["entrevistador_id"]).first()

        try:
            entrevista = registrar_y_completar_entrevista(
                postulacion=postulacion,
                tipo_entrevista=data["tipo_entrevista"],
                modalidad=data["modalidad"],
                fecha_programada=data["fecha_programada"],
                entrevistador=entrevistador,
                calificacion=data.get("calificacion"),
                concepto=data["concepto"],
                observaciones=data.get("observaciones", ""),
                aspectos_evaluados=data.get("aspectos_evaluados"),
                enlace_reunion=data.get("enlace_reunion", ""),
                lugar=data.get("lugar", ""),
                usuario=request.user,
            )
            postulacion.refresh_from_db()
            return Response(
                {
                    "entrevista": EntrevistaSerializer(entrevista).data,
                    "postulacion": PostulacionDetailSerializer(postulacion).data,
                },
                status=status.HTTP_201_CREATED,
            )
        except (TransicionInvalidaError, ExcepcionNoAutorizadaError, EntrevistaDesfavorableError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="registrar-evaluacion")
    def registrar_evaluacion(self, request, pk=None):
        """
        Registra una prueba/evaluación y actualiza la máquina de estados.
        """
        postulacion = self.get_object()
        serializer = RegistrarEvaluacionActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        evaluador = None
        if data.get("evaluador_id"):
            evaluador = Usuario.objects.filter(id=data["evaluador_id"]).first()

        archivo_informe = None
        if data.get("archivo_informe_id"):
            archivo_informe = Archivo.objects.filter(id=data["archivo_informe_id"]).first()

        try:
            evaluacion = registrar_y_completar_evaluacion(
                postulacion=postulacion,
                tipo_evaluacion=data["tipo_evaluacion"],
                nombre_prueba=data["nombre_prueba"],
                puntaje_obtenido=float(data["puntaje_obtenido"]),
                puntaje_maximo=float(data.get("puntaje_maximo", 100.0)),
                porcentaje_aprobacion=float(data.get("porcentaje_aprobacion", 70.0)),
                concepto=data.get("concepto", ""),
                evaluador=evaluador,
                archivo_informe=archivo_informe,
                usuario=request.user,
            )
            postulacion.refresh_from_db()
            return Response(
                {
                    "evaluacion": EvaluacionSerializer(evaluacion).data,
                    "postulacion": PostulacionDetailSerializer(postulacion).data,
                },
                status=status.HTTP_201_CREATED,
            )
        except (TransicionInvalidaError, ExcepcionNoAutorizadaError, EntrevistaDesfavorableError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="registrar-validacion")
    def registrar_validacion(self, request, pk=None):
        """
        Registra una validación documental/referencia y actualiza la máquina de estados.
        """
        postulacion = self.get_object()
        serializer = RegistrarValidacionActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        soporte_archivo = None
        if data.get("soporte_archivo_id"):
            soporte_archivo = Archivo.objects.filter(id=data["soporte_archivo_id"]).first()

        try:
            validacion = registrar_y_completar_validacion(
                postulacion=postulacion,
                tipo_verificacion=data["tipo_verificacion"],
                entidad_o_contacto=data["entidad_o_contacto"],
                estado=data["estado"],
                telefono_contacto=data.get("telefono_contacto", ""),
                detalles_verificacion=data.get("detalles_verificacion", ""),
                soporte_archivo=soporte_archivo,
                usuario=request.user,
            )
            postulacion.refresh_from_db()
            return Response(
                {
                    "validacion": ValidacionDocumentalSerializer(validacion).data,
                    "postulacion": PostulacionDetailSerializer(postulacion).data,
                },
                status=status.HTTP_201_CREATED,
            )
        except (TransicionInvalidaError, ExcepcionNoAutorizadaError, EntrevistaDesfavorableError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="seleccionar")
    def seleccionar(self, request, pk=None):
        """
        RN-R02 / RN-R03 / RN-R06: Selección final del candidato.
        Al completar cupos de la vacante, cierra automáticamente las demás candidaturas.
        """
        postulacion = self.get_object()
        serializer = SeleccionarActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            postulacion_seleccionada = seleccionar_candidato(
                postulacion=postulacion,
                usuario=request.user,
                notas_finales=data.get("notas_finales", ""),
                es_excepcion=data.get("es_excepcion", False),
                justificacion_excepcion=data.get("justificacion_excepcion", ""),
            )
            return Response(PostulacionDetailSerializer(postulacion_seleccionada).data)
        except (
            TransicionInvalidaError,
            RequisitoIncumplidoError,
            EtapaObligatoriaFaltanteError,
            CuposAgotadosError,
            ExcepcionNoAutorizadaError,
        ) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="cerrar")
    def cerrar(self, request, pk=None):
        """
        RN-R04 / RN-R05: Cierre de postulación por no selección, retiro o abandono con motivo obligatorio.
        """
        postulacion = self.get_object()
        serializer = CerrarPostulacionActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            postulacion_cerrada = cerrar_postulacion(
                postulacion=postulacion,
                nuevo_estado=data["nuevo_estado"],
                motivo=data["motivo"],
                usuario=request.user,
                datos_adicionales=data.get("datos_adicionales"),
            )
            return Response(PostulacionDetailSerializer(postulacion_cerrada).data)
        except (TransicionInvalidaError, MotivoRequeridoError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="seleccionar-masivo")
    def seleccionar_masivo(self, request):
        """
        Selecciona en lote candidatos de un mismo proceso hasta cubrir los cupos.
        Al cubrirse, RN-R06 cierra el resto y se notifica a todos.
        """
        ids = request.data.get("postulacion_ids") or []
        if not isinstance(ids, list) or not ids:
            return Response(
                {"detail": "Debe indicar 'postulacion_ids' como lista."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ids = list(dict.fromkeys([str(i) for i in ids]))

        postulaciones = list(self.get_queryset().filter(id__in=ids))
        if len(postulaciones) != len(ids):
            return Response(
                {"detail": "Alguna postulación no existe o no pertenece a su empresa."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        procesos = {str(p.proceso_seleccion_id) for p in postulaciones}
        if len(procesos) != 1:
            return Response(
                {"detail": "Todas las postulaciones deben pertenecer al mismo proceso."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        vacante = postulaciones[0].proceso_seleccion.vacante
        disponibles = vacante.cupos_disponibles
        if len(postulaciones) > disponibles:
            return Response(
                {"detail": f"Solo hay {disponibles} cupo(s) disponible(s) en la vacante."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                vacante_locked = Vacante.objects.select_for_update().get(pk=vacante.pk)
                for postulacion in postulaciones:
                    # Compartir la instancia bloqueada para que el conteo de cupos sea consistente
                    postulacion.proceso_seleccion.vacante = vacante_locked
                    seleccionar_candidato(postulacion=postulacion, usuario=request.user)
        except (
            TransicionInvalidaError,
            RequisitoIncumplidoError,
            EtapaObligatoriaFaltanteError,
            CuposAgotadosError,
            ExcepcionNoAutorizadaError,
            EntrevistaDesfavorableError,
        ) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        vacante.refresh_from_db()
        return Response({
            "seleccionados": len(postulaciones),
            "cupos_disponibles": vacante.cupos_disponibles,
            "vacante_estado": vacante.estado,
        })

    @action(detail=True, methods=["post"], url_path="cerrar-por-falta-documentos")
    def cerrar_por_falta_documentos(self, request, pk=None):
        """Cierra la postulación como NO_CONTINUO por no cargar la documentación y notifica."""
        postulacion = self.get_object()
        if not postulacion.es_activa:
            return Response(
                {"detail": "La postulación ya se encuentra finalizada."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            postulacion_cerrada = cerrar_postulacion(
                postulacion=postulacion,
                nuevo_estado=Postulacion.Estado.NO_CONTINUO,
                motivo="No cargó la documentación requerida para continuar el proceso de selección.",
                usuario=request.user,
                datos_adicionales={"causa": "falta_documentos"},
            )
            return Response(PostulacionDetailSerializer(postulacion_cerrada).data)
        except (TransicionInvalidaError, MotivoRequeridoError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], url_path="historico/exportar")
    def exportar_historico(self, request):
        """
        Exporta el histórico de postulaciones con observaciones por filtro.
        Formatos: csv (default), xlsx, pdf.
        """
        import csv
        import io as _io
        from datetime import datetime

        from django.http import HttpResponse

        formato = (request.query_params.get("formato") or "csv").lower()
        qs = self.get_queryset().select_related(
            "candidato", "proceso_seleccion__vacante"
        ).prefetch_related(
            "entrevistas", "evaluaciones", "validaciones_documentales"
        ).order_by("-fecha_postulacion")

        vacante_id = request.query_params.get("vacante_id")
        if vacante_id:
            qs = qs.filter(proceso_seleccion__vacante_id=vacante_id)
        proceso_id = request.query_params.get("proceso_seleccion_id")
        if proceso_id:
            qs = qs.filter(proceso_seleccion_id=proceso_id)
        estado = request.query_params.get("estado")
        if estado:
            qs = qs.filter(estado=estado)

        header = [
            "Vacante", "Candidato", "Documento", "Email", "Estado", "Motivo cierre",
            "Entrevista", "Evaluación", "Validación", "Puntaje entrevista", "Puntaje evaluación",
        ]

        def fila(p):
            ent = sorted(list(p.entrevistas.all()), key=lambda e: (e.fecha_programada, e.created_at), reverse=True)
            eva = sorted(list(p.evaluaciones.all()), key=lambda e: e.created_at, reverse=True)
            ent = ent[0] if ent else None
            eva = eva[0] if eva else None
            pct = eva.porcentaje_obtenido if eva else None
            clasif = None
            if pct is not None:
                clasif = "crítico" if pct <= 60 else ("alerta" if pct < 81 else "apto")
            ent_txt = (
                f"{ent.get_concepto_display()} ({ent.calificacion or 'N/A'}/100). {ent.observaciones or ''}".strip()
                if ent else ""
            )
            eva_txt = (
                f"{pct}% - {clasif}. {eva.concepto or ''}".strip() if eva else ""
            )
            val_txt = "; ".join(
                f"{v.get_tipo_verificacion_display()}: {v.get_estado_display()} ({v.detalles_verificacion or ''})"
                for v in p.validaciones_documentales.all()
            )
            return [
                f"{p.proceso_seleccion.vacante.codigo} - {p.proceso_seleccion.vacante.titulo}",
                f"{p.candidato.nombres} {p.candidato.apellidos}",
                p.candidato.documento,
                p.candidato.email,
                p.get_estado_display(),
                p.motivo_cierre or "",
                ent_txt,
                eva_txt,
                val_txt,
                ent.calificacion if ent and ent.calificacion is not None else "",
                pct if pct is not None else "",
            ]

        filas = [fila(p) for p in qs]
        fecha = datetime.now().strftime("%Y%m%d_%H%M")

        if formato == "xlsx":
            from openpyxl import Workbook

            wb = Workbook()
            ws = wb.active
            ws.title = "Histórico"
            ws.append(header)
            for r in filas:
                ws.append(r)
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = 24
            buf = _io.BytesIO()
            wb.save(buf)
            buf.seek(0)
            resp = HttpResponse(
                buf.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            resp["Content-Disposition"] = f'attachment; filename="historico_postulaciones_{fecha}.xlsx"'
            return resp

        if formato == "pdf":
            from reportlab.lib import colors as rl_colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, LongTable, TableStyle, Paragraph, Spacer
            from xml.sax.saxutils import escape as xml_escape

            buf = _io.BytesIO()
            docpdf = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=12, rightMargin=12, topMargin=12, bottomMargin=12)
            styles = getSampleStyleSheet()
            cell_style = ParagraphStyle("cell", parent=styles["Normal"], fontSize=6.5, leading=8)
            head_style = ParagraphStyle("head", parent=cell_style, textColor=rl_colors.white, fontName="Helvetica-Bold")

            data = [[Paragraph(xml_escape(str(h)), head_style) for h in header]]
            for r in filas:
                data.append([Paragraph(xml_escape(str(x)), cell_style) for x in r])
            t = LongTable(data, repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), rl_colors.HexColor("#002D62")),
                ("GRID", (0, 0), (-1, -1), 0.3, rl_colors.HexColor("#CCCCCC")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [rl_colors.white, rl_colors.HexColor("#F4F6F8")]),
            ]))
            docpdf.build([Paragraph("Histórico de Postulaciones — Reclutamiento y Selección", styles["Heading2"]), Spacer(1, 8), t])
            resp = HttpResponse(buf.getvalue(), content_type="application/pdf")
            resp["Content-Disposition"] = f'attachment; filename="historico_postulaciones_{fecha}.pdf"'
            return resp

        # CSV
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="historico_postulaciones_{fecha}.csv"'
        resp.write("\ufeff")  # BOM para Excel
        writer = csv.writer(resp)
        writer.writerow(header)
        for r in filas:
            writer.writerow(r)
        return resp

    @action(detail=True, methods=["post"], url_path="reabrir")
    def reabrir(self, request, pk=None):
        """
        RN-R07 / RN-R09: Reapertura excepcional con justificación obligatoria.
        """
        postulacion = self.get_object()
        serializer = ReabrirPostulacionActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            postulacion_reabierta = reabrir_postulacion_excepcional(
                postulacion=postulacion,
                justificacion=serializer.validated_data["justificacion"],
                usuario=request.user,
            )
            return Response(PostulacionDetailSerializer(postulacion_reabierta).data)
        except (TransicionInvalidaError, ExcepcionNoAutorizadaError, EntrevistaDesfavorableError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="iniciar-vinculacion")
    def iniciar_vinculacion(self, request, pk=None):
        """
        Fase G: Hand-off de candidato SELECCIONADO hacia Gestión Humana / Contratación.
        Genera el paquete estructurado de vinculación listo para consumo de módulos posteriores.
        """
        postulacion = self.get_object()
        if postulacion.estado != Postulacion.Estado.SELECCIONADO:
            return Response(
                {"detail": "Solo se puede iniciar vinculación para candidatos en estado 'Seleccionado'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        candidato = postulacion.candidato
        vacante = postulacion.proceso_seleccion.vacante
        perfil_cargo = vacante.perfil_cargo

        paquete_vinculacion = {
            "candidato": {
                "id": str(candidato.id),
                "tipo_documento": candidato.tipo_documento,
                "documento": candidato.documento,
                "nombres": candidato.nombres,
                "apellidos": candidato.apellidos,
                "email": candidato.email,
                "telefono": candidato.telefono,
                "ciudad": candidato.ciudad,
                "direccion": candidato.direccion,
            },
            "cargo_propuesto": {
                "id": str(perfil_cargo.id),
                "codigo": perfil_cargo.codigo,
                "nombre_cargo": perfil_cargo.nombre_cargo,
                "area": perfil_cargo.area,
            },
            "condiciones_laborales": {
                "sede_id": str(vacante.sede_id) if vacante.sede_id else None,
                "sede_nombre": vacante.sede.nombre if vacante.sede else "",
                "modalidad": vacante.modalidad,
                "tipo_contrato": vacante.tipo_contrato,
                "rango_salarial": f"{vacante.rango_salarial_min} - {vacante.rango_salarial_max}",
            },
            "checklist_ingreso": [
                {"item": "Examen médico de ingreso osteomuscular y audiometría", "completado": False},
                {"item": "Firma de contrato laboral y entrega de reglamento interno", "completado": False},
                {"item": "Afiliación a ARL, EPS, Fondo de Pensiones y Caja de Compensación", "completado": False},
                {"item": "Inducción general SST y entrega de Matriz de Peligros", "completado": False},
                {"item": "Entrega y firma de dotación y Elementos de Protección Personal (EPP)", "completado": False},
            ],
            "documentos_soporte": [
                {
                    "tipo": doc.get_tipo_documento_display(),
                    "nombre": doc.nombre_descriptivo or getattr(doc.archivo, "nombre_original", "Documento"),
                    "url": doc.archivo.archivo.url if hasattr(doc.archivo, "archivo") and doc.archivo.archivo else None,
                }
                for doc in candidato.documentos.all()
            ],
        }

        PostulacionEvento.objects.create(
            postulacion=postulacion,
            tipo_evento=PostulacionEvento.TipoEvento.CAMBIO_ESTADO,
            estado_anterior=postulacion.estado,
            estado_nuevo=postulacion.estado,
            descripcion="Paquete de vinculación laboral y hand-off generado hacia Gestión Humana",
            motivo="Inicio de proceso de contratación e inducción SST",
            usuario=request.user,
        )

        return Response(paquete_vinculacion, status=status.HTTP_200_OK)


class EntrevistaViewSet(EmpresaScopedViewSet):
    """
    ViewSet para consulta y gestión directa de entrevistas.
    """
    queryset = Entrevista.objects.all()
    serializer_class = EntrevistaSerializer
    permission_classes = [IsAuthenticated, IsRolParaEscritura.de("responsable", "admin")]


class EvaluacionViewSet(EmpresaScopedViewSet):
    """
    ViewSet para consulta y gestión directa de evaluaciones técnicas.
    """
    queryset = Evaluacion.objects.all()
    serializer_class = EvaluacionSerializer
    permission_classes = [IsAuthenticated, IsRolParaEscritura.de("responsable", "admin")]


class ValidacionDocumentalViewSet(EmpresaScopedViewSet):
    """
    ViewSet para consulta y gestión directa de validaciones documentales.
    """
    queryset = ValidacionDocumental.objects.all()
    serializer_class = ValidacionDocumentalSerializer
    permission_classes = [IsAuthenticated, IsRolParaEscritura.de("responsable", "admin")]
