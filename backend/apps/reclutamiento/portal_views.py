"""
Vistas para el Portal Público del Candidato — FOSST V.I.D.A.
Fase E: Ofertas de empleo abiertas, postulación pública con Habeas Data,
autenticación passwordless OTP y consulta de postulaciones.
"""
from django.db.models import Q
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from apps.reclutamiento.models import Vacante, Postulacion, Candidato
from apps.reclutamiento.portal_auth import (
    CandidateTokenAuthentication,
    IsAuthenticatedCandidate,
)
from apps.reclutamiento.portal_serializers import (
    VacantePublicaListSerializer,
    VacantePublicaDetailSerializer,
    PostulacionPublicaCreateSerializer,
    SolicitarAccesoOTPSerializer,
    VerificarOTPSerializer,
    PostulacionCandidatoConsultaSerializer,
    CandidatoPerfilConsultaSerializer,
    RetirarCandidaturaSerializer,
)
from apps.reclutamiento.services.portal import (
    generar_token_acceso_candidato,
    verificar_otp_candidato,
    verificar_magic_token_candidato,
    postular_publicamente_candidato,
    postular_rapido_candidato,
    retirar_postulacion_candidato,
)


class VacantesPublicasListView(APIView):
    """
    GET /api/reclutamiento/portal/vacantes/
    Listado público de vacantes abiertas y autorizadas para publicación en portal.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Vacante.objects.filter(
            estado=Vacante.Estado.ABIERTA,
            publicada_en_portal=True,
            deleted_at__isnull=True,
        ).select_related("empresa", "sede")

        search = request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(titulo__icontains=search)
                | Q(descripcion_publica__icontains=search)
                | Q(sede__ciudad__icontains=search)
            )

        modalidad = request.query_params.get("modalidad")
        if modalidad:
            qs = qs.filter(modalidad=modalidad)

        empresa_id = request.query_params.get("empresa_id")
        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)

        serializer = VacantePublicaListSerializer(qs, many=True)
        return Response(serializer.data)


class VacantePublicaDetailView(APIView):
    """
    GET /api/reclutamiento/portal/vacantes/{slug_or_id}/
    Detalle público de una vacante por ID o Slug.
    """
    permission_classes = [AllowAny]

    def get(self, request, slug_or_id):
        qs = Vacante.objects.filter(
            estado=Vacante.Estado.ABIERTA,
            publicada_en_portal=True,
            deleted_at__isnull=True,
        ).select_related("empresa", "sede", "proceso_seleccion")

        try:
            import uuid
            uuid_val = uuid.UUID(slug_or_id)
            vacante = qs.filter(id=uuid_val).first()
        except (ValueError, TypeError):
            vacante = qs.filter(slug=slug_or_id).first()

        if not vacante:
            return Response(
                {"detail": "La vacante solicitada no existe o ya no está disponible."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = VacantePublicaDetailSerializer(vacante)
        return Response(serializer.data)


class PostularPublicamenteView(APIView):
    """
    POST /api/reclutamiento/portal/vacantes/{slug_or_id}/postular/
    Registro anónimo / público de un candidato a una vacante con consentimiento de Habeas Data
    y soporte para subida directa de Hoja de Vida (PDF, DOC, DOCX).
    """
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, slug_or_id):
        qs = Vacante.objects.filter(
            estado=Vacante.Estado.ABIERTA,
            publicada_en_portal=True,
            deleted_at__isnull=True,
        ).select_related("empresa", "proceso_seleccion")

        try:
            import uuid
            uuid_val = uuid.UUID(slug_or_id)
            vacante = qs.filter(id=uuid_val).first()
        except (ValueError, TypeError):
            vacante = qs.filter(slug=slug_or_id).first()

        if not vacante:
            return Response(
                {"detail": "La vacante solicitada no existe o no admite postulaciones."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PostulacionPublicaCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        archivo_cv_file = request.FILES.get("archivo_cv")

        datos_candidato = {
            "tipo_documento": data["tipo_documento"],
            "documento": data["documento"],
            "nombres": data["nombres"],
            "apellidos": data["apellidos"],
            "email": data["email"],
            "telefono": data.get("telefono", ""),
            "ciudad": data.get("ciudad", ""),
            "direccion": data.get("direccion", ""),
            "autoriza_tratamiento_datos": data["autoriza_tratamiento_datos"],
            "fuente_reclutamiento_id": data.get("fuente_reclutamiento_id"),
            "fuente_detalle": data.get("fuente_detalle", "Portal Web"),
            "archivo_cv_file": archivo_cv_file,
        }

        datos_perfil = {
            "titulo_profesional": data.get("titulo_profesional", ""),
            "nivel_educativo": data.get("nivel_educativo"),
            "resumen_profesional": data.get("resumen_profesional", ""),
            "anios_experiencia": data.get("anios_experiencia", 0.0),
            "aspiracion_salarial": data.get("aspiracion_salarial"),
        }

        ip_solicitud = request.META.get("REMOTE_ADDR")

        try:
            postulacion, token_acceso = postular_publicamente_candidato(
                vacante=vacante,
                datos_candidato=datos_candidato,
                datos_perfil=datos_perfil,
                archivo_cv_id=data.get("archivo_cv_id"),
                ip_solicitud=ip_solicitud,
            )
            return Response(
                {
                    "detail": "¡Postulación registrada con éxito!",
                    "postulacion_id": str(postulacion.id),
                    "token_acceso": token_acceso.token,
                    "codigo_otp": token_acceso.codigo_otp,
                    "expira_en": token_acceso.expira_en,
                },
                status=status.HTTP_201_CREATED,
            )
        except DjangoValidationError as e:
            return Response({"detail": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)


class SolicitarAccesoOTPView(APIView):
    """
    POST /api/reclutamiento/portal/auth/solicitar-acceso/
    Solicita un código OTP al correo electrónico para consultar estado de postulaciones.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SolicitarAccesoOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()

        candidatos = Candidato.objects.filter(email__iexact=email, deleted_at__isnull=True)
        if not candidatos.exists():
            return Response(
                {"detail": "No se encontraron postulaciones asociadas a este correo electrónico."},
                status=status.HTTP_404_NOT_FOUND,
            )

        candidato = candidatos.first()
        ip_solicitud = request.META.get("REMOTE_ADDR")
        token_obj = generar_token_acceso_candidato(candidato=candidato, ip_solicitud=ip_solicitud)

        return Response(
            {
                "detail": f"Se ha enviado un código de acceso a {email}.",
                "codigo_otp": token_obj.codigo_otp,  # Visible en respuesta para testing / offline
                "expira_en": token_obj.expira_en,
            },
            status=status.HTTP_200_OK,
        )


class VerificarOTPView(APIView):
    """
    POST /api/reclutamiento/portal/auth/verificar-otp/
    Valida el código OTP y entrega el token de sesión Bearer para el candidato.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerificarOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
        codigo = serializer.validated_data["codigo_otp"].strip()

        try:
            candidato, token_sesion = verificar_otp_candidato(email=email, codigo_otp=codigo)
            return Response(
                {
                    "token": token_sesion.token,
                    "candidato": {
                        "id": str(candidato.id),
                        "nombre_completo": candidato.nombre_completo,
                        "email": candidato.email,
                    },
                    "expira_en": token_sesion.expira_en,
                },
                status=status.HTTP_200_OK,
            )
        except DjangoValidationError as e:
            return Response({"detail": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)


class MisPostulacionesView(APIView):
    """
    GET /api/reclutamiento/portal/mis-postulaciones/
    Consulta de postulaciones del candidato autenticado.
    """
    authentication_classes = [CandidateTokenAuthentication]
    permission_classes = [IsAuthenticatedCandidate]

    def get(self, request):
        candidato = getattr(request, "candidato", request.user)
        postulaciones = Postulacion.objects.filter(
            candidato=candidato,
            deleted_at__isnull=True,
        ).select_related("proceso_seleccion__vacante", "empresa").order_by("-fecha_postulacion")

        serializer = PostulacionCandidatoConsultaSerializer(postulaciones, many=True)
        return Response(serializer.data)


class RetirarPostulacionView(APIView):
    """
    POST /api/reclutamiento/portal/mis-postulaciones/{id}/retirar/
    Retiro voluntario de una postulación por parte del candidato.
    """
    authentication_classes = [CandidateTokenAuthentication]
    permission_classes = [IsAuthenticatedCandidate]

    def post(self, request, pk):
        candidato = getattr(request, "candidato", request.user)
        try:
            postulacion = Postulacion.objects.get(
                id=pk,
                candidato=candidato,
                deleted_at__isnull=True,
            )
        except Postulacion.DoesNotExist:
            return Response({"detail": "Postulación no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RetirarCandidaturaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        motivo = serializer.validated_data.get("motivo")

        try:
            postulacion_retirada = retirar_postulacion_candidato(
                postulacion=postulacion,
                candidato=candidato,
                motivo=motivo,
            )
            return Response(
                {
                    "detail": "Su candidatura ha sido retirada exitosamente.",
                    "postulacion": PostulacionCandidatoConsultaSerializer(postulacion_retirada).data,
                },
                status=status.HTTP_200_OK,
            )
        except DjangoValidationError as e:
            return Response({"detail": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)


class MiPerfilCandidatoView(APIView):
    """
    GET /api/reclutamiento/portal/mi-perfil/
    Obtiene los datos consolidados del candidato autenticado (datos personales, perfil y última HV).
    """
    authentication_classes = [CandidateTokenAuthentication]
    permission_classes = [IsAuthenticatedCandidate]

    def get(self, request):
        candidato = getattr(request, "candidato", request.user)
        serializer = CandidatoPerfilConsultaSerializer(candidato)
        return Response(serializer.data)


class PostularRapidoView(APIView):
    """
    POST /api/reclutamiento/portal/vacantes/{slug_or_id}/postular-rapido/
    Postulación en 1 Clic para un candidato ya autenticado, reutilizando su perfil y su última Hoja de Vida.
    """
    authentication_classes = [CandidateTokenAuthentication]
    permission_classes = [IsAuthenticatedCandidate]

    def post(self, request, slug_or_id):
        candidato = getattr(request, "candidato", request.user)
        qs = Vacante.objects.filter(
            estado=Vacante.Estado.ABIERTA,
            publicada_en_portal=True,
            deleted_at__isnull=True,
        ).select_related("empresa", "proceso_seleccion")

        try:
            import uuid
            uuid_val = uuid.UUID(slug_or_id)
            vacante = qs.filter(id=uuid_val).first()
        except (ValueError, TypeError):
            vacante = qs.filter(slug=slug_or_id).first()

        if not vacante:
            return Response(
                {"detail": "La vacante solicitada no existe o no admite postulaciones."},
                status=status.HTTP_404_NOT_FOUND,
            )

        ip_solicitud = request.META.get("REMOTE_ADDR")

        try:
            postulacion, token_acceso = postular_rapido_candidato(
                vacante=vacante,
                candidato=candidato,
                ip_solicitud=ip_solicitud,
            )
            return Response(
                {
                    "detail": f"¡Te has postulado exitosamente a {vacante.titulo}!",
                    "postulacion_id": str(postulacion.id),
                    "token_acceso": token_acceso.token,
                    "codigo_otp": token_acceso.codigo_otp,
                    "expira_en": token_acceso.expira_en,
                },
                status=status.HTTP_201_CREATED,
            )
        except DjangoValidationError as e:
            return Response({"detail": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)


class BuscarPerfilPrevioView(APIView):
    """
    POST /api/reclutamiento/portal/auth/buscar-perfil-previo/
    Permite autocompletar el formulario de postulación buscando por email y documento.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        documento = request.data.get("documento", "").strip()

        if not email and not documento:
            return Response({"encontrado": False, "datos": None})

        query = Q()
        if email:
            query |= Q(email__iexact=email)
        if documento:
            query |= Q(documento=documento)

        candidato = Candidato.objects.filter(query, deleted_at__isnull=True).first()
        if not candidato:
            return Response({"encontrado": False, "datos": None})

        serializer = CandidatoPerfilConsultaSerializer(candidato)
        return Response({"encontrado": True, "datos": serializer.data})

