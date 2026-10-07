from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from apps.accounts.models import UserRole
from apps.capacitaciones.models import Trabajador
from apps.capacitaciones.serializers import TrabajadorSerializer
from .models import NovedadLaboral, ExamenMedicoOcupacional, LicenciaConduccion
from .serializers import (
    NovedadLaboralSerializer,
    ExamenMedicoOcupacionalSerializer,
    LicenciaConduccionSerializer,
)


class BaseTrabajadorScopedViewSet(viewsets.ModelViewSet):
    """
    Base para recursos vinculados a Trabajador, con filtrado multi-tenant estricto.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset().select_related("trabajador")
        user = self.request.user
        if user.rol == UserRole.ADMIN:
            empresa_id = self.request.query_params.get("empresa_id")
            if empresa_id:
                return qs.filter(trabajador__empresa_id=empresa_id)
            return qs
        return qs.filter(trabajador__empresa=user.empresa)

    def perform_create(self, serializer):
        user = self.request.user
        trabajador = serializer.validated_data.get("trabajador")
        if user.rol != UserRole.ADMIN and trabajador and trabajador.empresa_id != user.empresa_id:
            raise serializers.ValidationError({"trabajador": "El trabajador no pertenece a su empresa."})
        
        # Asignar created_by si el modelo lo tiene
        if "created_by" in [f.name for f in serializer.Meta.model._meta.fields]:
            serializer.save(created_by=user)
        else:
            serializer.save()


class NovedadLaboralViewSet(BaseTrabajadorScopedViewSet):
    queryset = NovedadLaboral.objects.all()
    serializer_class = NovedadLaboralSerializer
    filterset_fields = ["tipo", "trabajador"]


class ExamenMedicoOcupacionalViewSet(BaseTrabajadorScopedViewSet):
    queryset = ExamenMedicoOcupacional.objects.all()
    serializer_class = ExamenMedicoOcupacionalSerializer
    filterset_fields = ["tipo", "concepto_aptitud", "presenta_restricciones", "trabajador"]


class LicenciaConduccionViewSet(BaseTrabajadorScopedViewSet):
    queryset = LicenciaConduccion.objects.all()
    serializer_class = LicenciaConduccionSerializer
    filterset_fields = ["categoria", "presenta_restricciones", "trabajador"]


class ExpedienteTrabajadorViewSet(viewsets.ViewSet):
    """
    Endpoint para consultar el expediente laboral consolidado de un trabajador.
    GET /api/gestion-humana/expediente/{trabajador_id}/
    """
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk=None):
        user = request.user
        try:
            if user.rol == UserRole.ADMIN:
                trabajador = Trabajador.objects.select_related("sede", "perfil_cargo", "empresa").get(pk=pk)
            else:
                trabajador = Trabajador.objects.select_related("sede", "perfil_cargo", "empresa").get(pk=pk, empresa=user.empresa)
        except Trabajador.DoesNotExist:
            return Response({"error": "Trabajador no encontrado o sin permisos"}, status=status.HTTP_404_NOT_FOUND)

        novedades = NovedadLaboral.objects.filter(trabajador=trabajador).order_by("-fecha_inicio")
        examenes = ExamenMedicoOcupacional.objects.filter(trabajador=trabajador).order_by("-fecha_examen")
        licencias = LicenciaConduccion.objects.filter(trabajador=trabajador).order_by("-fecha_vencimiento")

        return Response({
            "trabajador": TrabajadorSerializer(trabajador).data,
            "novedades": NovedadLaboralSerializer(novedades, many=True).data,
            "examenes_medicos": ExamenMedicoOcupacionalSerializer(examenes, many=True).data,
            "licencias_conduccion": LicenciaConduccionSerializer(licencias, many=True).data,
        })


class ImportarTrabajadoresMasivoView(APIView):
    """
    POST /api/gestion-humana/importar-masivo/
    Procesa la carga masiva de trabajadores desde Excel (.xlsx) o CSV (.csv).
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response({"error": "Sin empresa asociada."}, status=status.HTTP_400_BAD_REQUEST)

        file_obj = request.FILES.get("archivo")
        if not file_obj:
            return Response({"error": "Debe adjuntar un archivo (.xlsx o .csv)."}, status=status.HTTP_400_BAD_REQUEST)

        from .importador import procesar_importacion_trabajadores
        resultado = procesar_importacion_trabajadores(file_obj, empresa, request.user)

        return Response(resultado, status=status.HTTP_200_OK)


class DescargarPlantillaImportacionView(APIView):
    """
    GET /api/gestion-humana/plantilla-importacion/
    Descarga la plantilla oficial en formato Excel (.xlsx) para importación de trabajadores.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.http import HttpResponse
        from .importador import generar_plantilla_excel

        excel_bytes = generar_plantilla_excel()
        response = HttpResponse(
            excel_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="plantilla_importacion_trabajadores.xlsx"'
        return response
