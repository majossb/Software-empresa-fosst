from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ReglaAlertaViewSet

router = DefaultRouter()
router.register("reglas", ReglaAlertaViewSet, basename="regla-alerta")

urlpatterns = [
    path("", include(router.urls)),
]
