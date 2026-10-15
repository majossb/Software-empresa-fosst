from rest_framework.routers import DefaultRouter

from .views import (
    AfiliacionTrabajadorViewSet,
    CapacitacionViewSet,
    ParticipanteCapacitacionViewSet,
    PlanillaSeguridadViewSet,
    TrabajadorViewSet,
)

router = DefaultRouter(trailing_slash=False)
router.register("trabajadores", TrabajadorViewSet, basename="trabajador")
router.register("afiliaciones", AfiliacionTrabajadorViewSet, basename="afiliacion")
router.register("planillas", PlanillaSeguridadViewSet, basename="planilla")
router.register("capacitaciones", CapacitacionViewSet, basename="capacitacion")
router.register("participantes", ParticipanteCapacitacionViewSet, basename="participante")

urlpatterns = router.urls
