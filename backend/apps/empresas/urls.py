from rest_framework.routers import DefaultRouter
from .views import EmpresaViewSet

router = DefaultRouter(trailing_slash=False)
router.register("", EmpresaViewSet, basename="empresa")
urlpatterns = router.urls
