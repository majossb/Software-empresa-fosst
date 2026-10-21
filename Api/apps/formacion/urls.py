from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    EvaluacionCompetenciaViewSet,
    CursoFormacionViewSet,
    CargoRequisitoFormacionViewSet,
    RegistroFormacionViewSet,
)

router = DefaultRouter()
router.register("evaluaciones", EvaluacionCompetenciaViewSet, basename="formacion-evaluacion")
router.register("cursos", CursoFormacionViewSet, basename="formacion-curso")
router.register("requisitos-cargo", CargoRequisitoFormacionViewSet, basename="formacion-requisito-cargo")
router.register("registros", RegistroFormacionViewSet, basename="formacion-registro")

urlpatterns = [
    path("", include(router.urls)),
]
