from rest_framework.routers import DefaultRouter
from .views import PlanViewSet, SuscripcionViewSet

router = DefaultRouter(trailing_slash=False)
router.register("suscripciones", SuscripcionViewSet, basename="suscripcion")
router.register("", PlanViewSet, basename="plan")

urlpatterns = router.urls
