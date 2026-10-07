from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import EvaluacionCompetenciaViewSet

router = DefaultRouter()
router.register("evaluaciones", EvaluacionCompetenciaViewSet, basename="formacion-evaluacion")

urlpatterns = [
    path("", include(router.urls)),
]
