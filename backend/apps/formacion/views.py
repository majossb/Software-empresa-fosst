from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Count, Max

from apps.common.mixins import EmpresaScopedViewSet
from apps.capacitaciones.models import Trabajador
from apps.perfilcargo.models import PerfilCargo, CargoCompetencia
from .models import EvaluacionCompetencia
from .serializers import EvaluacionCompetenciaSerializer


class EvaluacionCompetenciaViewSet(EmpresaScopedViewSet):
    """
    ViewSet para la gestión de evaluaciones de competencias del cargo (MCC).
    """
    queryset = EvaluacionCompetencia.objects.all()
    serializer_class = EvaluacionCompetenciaSerializer
    empresa_field = "trabajador__empresa"
    filterset_fields = ["trabajador", "cargo_competencia", "metodo"]

    def get_queryset(self):
        return super().get_queryset().select_related(
            "trabajador", "cargo_competencia", "evaluado_por", "trabajador__empresa"
        )

    def perform_create(self, serializer):
        if not serializer.validated_data.get("evaluado_por"):
            serializer.save(evaluado_por=self.request.user)
        else:
            serializer.save()

    @action(detail=False, methods=["get"], url_path="matriz-trabajador/(?P<trabajador_id>[^/.]+)")
    def matriz_trabajador(self, request, trabajador_id=None):
        """
        Devuelve la matriz de competencias del trabajador con todas las competencias
        de su cargo actual, nivel requerido, última evaluación, nivel alcanzado y brecha.
        """
        empresa = request.user.empresa
        try:
            trabajador = Trabajador.objects.select_related("perfil_cargo").get(pk=trabajador_id, empresa=empresa)
        except Trabajador.DoesNotExist:
            return Response({"error": "Trabajador no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        if not trabajador.perfil_cargo:
            return Response({"error": "El trabajador no tiene perfil de cargo asignado"}, status=status.HTTP_400_BAD_REQUEST)

        competencias = CargoCompetencia.objects.filter(perfil_cargo=trabajador.perfil_cargo)
        matriz = []

        for comp in competencias:
            req = comp.nivel_requerido or comp.nivel or 1
            ultima_eval = EvaluacionCompetencia.objects.filter(
                trabajador=trabajador, cargo_competencia=comp
            ).order_by("-fecha_evaluacion").first()

            alcanzado = ultima_eval.nivel_alcanzado if ultima_eval else 0
            brecha = max(0, req - alcanzado) if ultima_eval else req

            matriz.append({
                "competencia_id": comp.id,
                "nombre": comp.nombre,
                "tipo": comp.tipo or "general",
                "nivel_requerido": req,
                "nivel_alcanzado": alcanzado,
                "brecha": brecha,
                "cumple": alcanzado >= req if ultima_eval else False,
                "ultima_evaluacion": EvaluacionCompetenciaSerializer(ultima_eval).data if ultima_eval else None,
            })

        return Response({
            "trabajador": {
                "id": str(trabajador.id),
                "nombre": trabajador.nombre,
                "documento": trabajador.documento,
                "cargo": trabajador.perfil_cargo.nombre_cargo,
            },
            "competencias": matriz,
        })

    @action(detail=False, methods=["get"], url_path="resumen")
    def resumen(self, request):
        """Resumen consolidado de competencias de la empresa."""
        qs = self.get_queryset()
        total_evaluaciones = qs.count()
        con_brecha = qs.filter(brecha_calculada__gt=0).count()
        promedio_brecha = qs.aggregate(avg=Avg("brecha_calculada"))["avg"] or 0.0

        return Response({
            "total_evaluaciones": total_evaluaciones,
            "evaluaciones_con_brecha": con_brecha,
            "evaluaciones_optimas": total_evaluaciones - con_brecha,
            "promedio_brecha": round(promedio_brecha, 2),
        })
