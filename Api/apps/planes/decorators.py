"""
Criterio de negocio adoptado para Gating por Plan (RF-USR-08):
- Al acceder a una funcionalidad (ej. tiene_auditoria, tiene_informes, tiene_calendario, tiene_alertas_email, tiene_historico)
  o al intentar superar un límite cuantitativo (max_usuarios, max_evidencias_mb), el sistema verifica la suscripción activa
  de la empresa del usuario.
- Si no existe una suscripción activa o el plan contratado no incluye la funcionalidad solicitada,
  el endpoint responde HTTP 403 Forbidden con un mensaje claro en español especificando la característica requerida.
- Los usuarios con rol ADMIN (Superadministrador) están exentos de la restricción de plan para fines de auditoría/soporte.
"""

from functools import wraps
from typing import Tuple
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from apps.accounts.models import UserRole
from apps.planes.models import Suscripcion


def verificar_acceso_plan(user, feature_flag: str) -> Tuple[bool, str]:
    if not user or not user.is_authenticated:
        return False, "Usuario no autenticado."

    if getattr(user, "rol", None) in [UserRole.ADMIN, UserRole.AUDITOR]:
        return True, ""

    empresa = getattr(user, "empresa", None)
    if not empresa:
        return False, "No tiene una empresa asociada."

    suscripcion = Suscripcion.objects.filter(
        empresa=empresa,
        estado=Suscripcion.Estado.ACTIVA
    ).select_related("plan").order_by("-created_at").first()

    if not suscripcion or not suscripcion.plan or not suscripcion.plan.activo:
        return False, "La empresa no cuenta con una suscripción activa."

    if suscripcion.fecha_fin and suscripcion.fecha_fin < timezone.now():
        return False, "La suscripción de la empresa ha vencido."

    plan = suscripcion.plan

    if feature_flag:
        if hasattr(plan, feature_flag):
            if not getattr(plan, feature_flag, False):
                nombre_feature = feature_flag.replace("tiene_", "").replace("_", " ").title()
                return False, f"Su plan '{plan.nombre}' no incluye la funcionalidad de {nombre_feature}. Requiere upgrade de plan."
        elif feature_flag == "limite_usuarios":
            cant_usuarios = user.empresa.usuarios.filter(is_active=True).count()
            if cant_usuarios >= plan.max_usuarios:
                return False, f"Ha alcanzado el límite máximo de usuarios ({plan.max_usuarios}) permitido por su plan '{plan.nombre}'."

    return True, ""


def requiere_plan(feature_flag: str):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request_or_self, *args, **kwargs):
            request = request_or_self if hasattr(request_or_self, "user") else (args[0] if args and hasattr(args[0], "user") else getattr(request_or_self, "request", None))
            permitido, mensaje = verificar_acceso_plan(request.user, feature_flag)
            if not permitido:
                return Response(
                    {
                        "error": "Acceso Restringido por Plan",
                        "detail": mensaje,
                        "feature_required": feature_flag,
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
            return view_func(request_or_self, *args, **kwargs)

        return _wrapped_view

    return decorator
