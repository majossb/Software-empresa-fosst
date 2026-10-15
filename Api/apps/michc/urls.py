from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import EvaluacionHabilitacionViewSet

router = DefaultRouter()
router.register("matriz", EvaluacionHabilitacionViewSet, basename="michc-matriz")

urlpatterns = [
    path("", include(router.urls)),
]
