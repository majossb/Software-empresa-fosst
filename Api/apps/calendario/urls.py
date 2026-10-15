from rest_framework.routers import DefaultRouter
from .views import CalendarioActividadViewSet, IncidenteViewSet, NotificacionViewSet

router = DefaultRouter(trailing_slash=False)
router.register("incidentes", IncidenteViewSet, basename="incidente")
router.register("actividades", CalendarioActividadViewSet, basename="actividad")
router.register("notificaciones", NotificacionViewSet, basename="notificacion")

urlpatterns = router.urls
