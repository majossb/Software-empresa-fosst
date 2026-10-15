from rest_framework import viewsets

from apps.accounts.permissions import EsAdmin
from apps.common.mixins import EmpresaScopedViewSet
from .models import Plan, Suscripcion
from .serializers import PlanSerializer, SuscripcionSerializer


class PlanViewSet(viewsets.ModelViewSet):
    """Catálogo de planes (global, no por empresa). Solo el ADMIN los edita;
    cualquier usuario autenticado puede listarlos (para elegir/ver el suyo)."""
    queryset = Plan.objects.filter(activo=True)
    serializer_class = PlanSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return []
        return [EsAdmin()]


class SuscripcionViewSet(EmpresaScopedViewSet):
    queryset = Suscripcion.objects.select_related("plan", "empresa")
    serializer_class = SuscripcionSerializer
