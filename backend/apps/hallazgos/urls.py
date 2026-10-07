from rest_framework.routers import DefaultRouter
from .views import HallazgoViewSet, PlanMejoraViewSet

router = DefaultRouter(trailing_slash=False)
router.register("hallazgos", HallazgoViewSet, basename="hallazgo")
router.register("plan-mejora", PlanMejoraViewSet, basename="plan-mejora")

urlpatterns = router.urls
