from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import BrechaViewSet, BrechaAccionViewSet

router = DefaultRouter()
router.register("brechas", BrechaViewSet, basename="brecha")

# Acciones anidadas bajo brechas
acciones_router = DefaultRouter()
acciones_router.register("acciones", BrechaAccionViewSet, basename="brecha-accion")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "brechas/<uuid:brecha_pk>/",
        include(acciones_router.urls),
    ),
]
