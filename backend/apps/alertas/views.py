from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from apps.common.mixins import EmpresaScopedViewSet
from apps.planes.mixins import PlanGatingMixin
from apps.accounts.models import UserRole
from .models import ReglaAlerta
from .serializers import ReglaAlertaSerializer
from .services import evaluar_reglas_alertas


class ReglaAlertaViewSet(PlanGatingMixin, EmpresaScopedViewSet):
    """
    Gestión de reglas de alerta por empresa (o consulta de reglas globales).
    """
    queryset = ReglaAlerta.objects.all()
    serializer_class = ReglaAlertaSerializer
    filterset_fields = ["modelo_origen", "activa", "nivel_criticidad"]
    required_feature = "tiene_alertas_email"

    def get_queryset(self):
        user = self.request.user
        if user.rol == UserRole.ADMIN:
            return ReglaAlerta.objects.all()
        # Ver reglas globales + reglas específicas de la empresa
        return ReglaAlerta.objects.filter(Q(empresa=user.empresa) | Q(empresa__isnull=True))

    @action(detail=False, methods=["post"], url_path="ejecutar-revision")
    def ejecutar_revision(self, request):
        """Dispara manualmente la revisión de vencimientos para la empresa."""
        empresa = request.user.empresa
        total = evaluar_reglas_alertas(empresa=empresa)
        return Response({
            "mensaje": f"Revisión completada exitosamente. Se generaron {total} alerta(s).",
            "alertas_generadas": total,
        }, status=status.HTTP_200_OK)
