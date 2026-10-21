from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ReglaAlertaViewSet, NotificacionViewSet

router = DefaultRouter()
router.register("reglas", ReglaAlertaViewSet, basename="regla-alerta")
router.register("notificaciones", NotificacionViewSet, basename="notificacion")

urlpatterns = [
    path("", include(router.urls)),
]
