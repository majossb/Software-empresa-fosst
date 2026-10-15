from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Count

from apps.common.mixins import EmpresaScopedViewSet
from .models import EvaluacionHabilitacion
from .serializers import (
    EvaluacionHabilitacionListSerializer,
    EvaluacionHabilitacionDetailSerializer,
)
from .engine import recalcular_habilitacion


class EvaluacionHabilitacionViewSet(EmpresaScopedViewSet):
    """
    ViewSet para la Matriz Inteligente de Cumplimiento y Habilitación del Cargo (MICHC).
    
    GET /api/michc/matriz/              -> Listado de habilitación de todos los trabajadores
    GET /api/michc/matriz/{id}/         -> Detalle con desglose de requisitos e interpretación IA
    POST /api/michc/matriz/{id}/recalcular/ -> Fuerza recálculo manual en tiempo real
    GET /api/michc/matriz/resumen/      -> Métricas agregadas y estadísticas de cumplimiento
    """
    queryset = EvaluacionHabilitacion.objects.all()
    serializer_class = EvaluacionHabilitacionListSerializer
    empresa_field = "trabajador__empresa"
    filterset_fields = ["semaforo", "estado_habilitacion", "compatibilidad", "nivel_atencion", "perfil_cargo"]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            "trabajador", "perfil_cargo", "trabajador__sede", "trabajador__empresa"
        )
        
        sede_id = self.request.query_params.get("sede_id")
        if sede_id:
            qs = qs.filter(trabajador__sede_id=sede_id)
            
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return EvaluacionHabilitacionDetailSerializer
        return EvaluacionHabilitacionListSerializer

    @action(detail=True, methods=["post"], url_path="recalcular")
    def recalcular(self, request, pk=None):
        """Fuerza recálculo manual del trabajador."""
        evaluacion = self.get_object()
        eval_actualizada = recalcular_habilitacion(evaluacion.trabajador_id)
        serializer = EvaluacionHabilitacionDetailSerializer(eval_actualizada)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="resumen")
    def resumen(self, request):
        """Métricas agregadas del estado de cumplimiento de la empresa."""
        qs = self.get_queryset()
        total = qs.count()

        por_semaforo = {
            "verde": qs.filter(semaforo="verde").count(),
            "amarillo": qs.filter(semaforo="amarillo").count(),
            "rojo": qs.filter(semaforo="rojo").count(),
        }

        por_estado = {}
        for estado_val, _ in EvaluacionHabilitacion.EstadoHabilitacion.choices:
            por_estado[estado_val] = qs.filter(estado_habilitacion=estado_val).count()

        por_compatibilidad = {}
        for comp_val, _ in EvaluacionHabilitacion.Compatibilidad.choices:
            por_compatibilidad[comp_val] = qs.filter(compatibilidad=comp_val).count()

        promedio_cumplimiento = qs.aggregate(avg=Avg("porcentaje_cumplimiento"))["avg"] or 0.0

        return Response({
            "total_evaluaciones": total,
            "promedio_cumplimiento": round(promedio_cumplimiento, 2),
            "por_semaforo": por_semaforo,
            "por_estado_habilitacion": por_estado,
            "por_compatibilidad": por_compatibilidad,
        })
