from rest_framework import viewsets
from rest_framework.response import Response

from apps.common.mixins import EmpresaScopedViewSet
from .models import (
    AfiliacionTrabajador,
    Capacitacion,
    ParticipanteCapacitacion,
    PlanillaSeguridad,
    Trabajador,
)
from .serializers import (
    AfiliacionTrabajadorSerializer,
    CapacitacionSerializer,
    ParticipanteCapacitacionSerializer,
    PlanillaSeguridadSerializer,
    TrabajadorSerializer,
)


class TrabajadorViewSet(EmpresaScopedViewSet):
    queryset = Trabajador.objects.select_related("sede", "perfil_cargo")
    serializer_class = TrabajadorSerializer
    filterset_fields = ["activo", "tipo_vinculacion", "sede"]


class AfiliacionTrabajadorViewSet(viewsets.ModelViewSet):
    """Se filtra por empresa a través del trabajador."""
    serializer_class = AfiliacionTrabajadorSerializer

    def get_queryset(self):
        user = self.request.user
        qs = AfiliacionTrabajador.objects.select_related("trabajador")
        return qs if user.rol == "ADMIN" else qs.filter(trabajador__empresa=user.empresa)


class PlanillaSeguridadViewSet(EmpresaScopedViewSet):
    queryset = PlanillaSeguridad.objects.all()
    serializer_class = PlanillaSeguridadSerializer
    filterset_fields = ["periodo", "estado_pago"]


from apps.common.permissions import IsRolParaEscritura
from rest_framework.permissions import IsAuthenticated


class CapacitacionViewSet(EmpresaScopedViewSet):
    queryset = Capacitacion.objects.prefetch_related("participantes")
    serializer_class = CapacitacionSerializer
    filterset_fields = ["estado"]
    permission_classes = [IsAuthenticated, IsRolParaEscritura.de("responsable")]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        capacitaciones = serializer.data
        resumen = {
            "total": len(capacitaciones),
            "programadas": sum(1 for c in capacitaciones if c.get("estado") == "programada"),
            "realizadas": sum(1 for c in capacitaciones if c.get("estado") == "realizada"),
            "canceladas": sum(1 for c in capacitaciones if c.get("estado") == "cancelada"),
        }
        return Response({"capacitaciones": capacitaciones, "resumen": resumen})

    def perform_create(self, serializer):
        super().perform_create(serializer)
        instance = serializer.instance
        from apps.auditoria.helpers import registrar_audit_log
        registrar_audit_log(
            self.request,
            "CREAR_CAPACITACION",
            tabla_afectada="capacitaciones",
            registro_id=instance.id,
            valores_nuevos={"tema": instance.tema},
        )

    def perform_update(self, serializer):
        old_data = {"estado": serializer.instance.estado, "tema": serializer.instance.tema}
        super().perform_update(serializer)
        instance = serializer.instance
        from apps.auditoria.helpers import registrar_audit_log
        registrar_audit_log(
            self.request,
            "ACTUALIZAR_CAPACITACION",
            tabla_afectada="capacitaciones",
            registro_id=instance.id,
            valores_anteriores=old_data,
            valores_nuevos=serializer.validated_data,
        )


class ParticipanteCapacitacionViewSet(viewsets.ModelViewSet):
    serializer_class = ParticipanteCapacitacionSerializer

    def get_queryset(self):
        user = self.request.user
        qs = ParticipanteCapacitacion.objects.select_related("capacitacion", "trabajador")
        return qs if user.rol == "ADMIN" else qs.filter(capacitacion__empresa=user.empresa)
