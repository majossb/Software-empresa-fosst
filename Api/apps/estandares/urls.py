from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EstandarListView,
    EstandaresConRespuestasView,
    ActualizarRespuestaView,
    EvaluacionActualView,
    HistorialEvaluacionesView,
    ResumenEvaluacionView,
    ApelacionViewSet,
    RespuestasHistoricasEvaluacionView,
)

router = DefaultRouter()
router.register("apelaciones", ApelacionViewSet, basename="apelacion")

urlpatterns = [
    # Estándares
    path("estandares/", EstandarListView.as_view(), name="estandar-list"),
    path("estandares/respuestas", EstandaresConRespuestasView.as_view(), name="estandar-respuestas"),
    path("estandares/respuesta/<uuid:estandar_id>", ActualizarRespuestaView.as_view(), name="estandar-respuesta-update"),
    # Evaluaciones
    path("evaluaciones/actual", EvaluacionActualView.as_view(), name="evaluacion-actual"),
    path("evaluaciones/actual/respuestas-historicas", RespuestasHistoricasEvaluacionView.as_view(), name="evaluacion-respuestas-historicas"),
    path("evaluaciones/historial", HistorialEvaluacionesView.as_view(), name="evaluacion-historial"),
    path("evaluaciones/<uuid:evaluacion_id>/resumen", ResumenEvaluacionView.as_view(), name="evaluacion-resumen"),
    # Router-based
    path("", include(router.urls)),
]
