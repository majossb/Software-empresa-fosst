from rest_framework import exceptions
from .decorators import verificar_acceso_plan


class PlanGatingMixin:
    """
    Mixin para ViewSets o APIViews de DRF.
    Define `required_feature = "tiene_auditoria"` en la clase para forzar gating por plan.
    """
    required_feature: str = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if self.required_feature:
            permitido, mensaje = verificar_acceso_plan(request.user, self.required_feature)
            if not permitido:
                raise exceptions.PermissionDenied(
                    detail=f"Acceso Restringido por Plan: {mensaje}"
                )
