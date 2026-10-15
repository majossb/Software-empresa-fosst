from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.mixins import EmpresaScopedViewSet
from apps.planes.mixins import PlanGatingMixin
from .models import CalendarioActividad, Incidente, Notificacion
from .serializers import CalendarioActividadSerializer, IncidenteSerializer, NotificacionSerializer


class IncidenteViewSet(EmpresaScopedViewSet):
    queryset = Incidente.objects.all()
    serializer_class = IncidenteSerializer
    filterset_fields = ["tipo", "estado_investigacion"]

    @action(detail=True, methods=["get"], url_path="furat-pdf")
    def generar_furat_pdf(self, request, pk=None):
        """GET /api/calendario/incidentes/{id}/furat-pdf → genera la plantilla oficial FURAT en PDF."""
        from django.http import HttpResponse
        from apps.capacitaciones.services import generar_plantilla_furat_pdf

        incidente = self.get_object()
        pdf_bytes = generar_plantilla_furat_pdf(incidente)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="FURAT_{incidente.id}.pdf"'
        return response

    @action(detail=False, methods=["get"], url_path="indicadores-accidentalidad")
    def indicadores_accidentalidad(self, request):
        """GET /api/calendario/incidentes/indicadores-accidentalidad → calcula IFA, ISA, ILI y tasa de accidentalidad."""
        from apps.capacitaciones.services import calcular_indicadores_accidentalidad

        empresa = request.user.empresa
        if not empresa:
            return Response({"error": "Sin empresa asociada."}, status=400)

        anio_param = request.query_params.get("anio")
        anio = int(anio_param) if anio_param and anio_param.isdigit() else None

        indicadores = calcular_indicadores_accidentalidad(empresa, anio=anio)
        return Response(indicadores)


class CalendarioActividadViewSet(PlanGatingMixin, EmpresaScopedViewSet):
    queryset = CalendarioActividad.objects.all()
    serializer_class = CalendarioActividadSerializer
    filterset_fields = ["tipo", "completada"]
    required_feature = "tiene_calendario"


class NotificacionViewSet(EmpresaScopedViewSet):
    """Además del CRUD normal, cada usuario solo ve SUS notificaciones
    (o las generales de su empresa con usuario=null)."""
    queryset = Notificacion.objects.all()
    serializer_class = NotificacionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.rol != "ADMIN":
            from django.db.models import Q
            qs = qs.filter(Q(usuario=user) | Q(usuario__isnull=True))
        return qs

    @action(detail=True, methods=["post"])
    def marcar_leida(self, request, pk=None):
        notificacion = self.get_object()
        notificacion.leida = True
        notificacion.save(update_fields=["leida"])
        return Response(NotificacionSerializer(notificacion).data)
