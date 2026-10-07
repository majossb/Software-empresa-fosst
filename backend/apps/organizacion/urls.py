from rest_framework.routers import DefaultRouter
from .views import NodoOrganigramaViewSet, ProcesoViewSet, SedeViewSet

router = DefaultRouter(trailing_slash=False)
router.register("sedes", SedeViewSet, basename="sede")
router.register("organigrama", NodoOrganigramaViewSet, basename="nodo-organigrama")
router.register("procesos", ProcesoViewSet, basename="proceso")

urlpatterns = router.urls
