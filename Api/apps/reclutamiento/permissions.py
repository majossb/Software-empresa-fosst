from rest_framework import permissions
from apps.accounts.models import UserRole
from apps.reclutamiento.models import AsignacionRolProceso


def verificar_rol_reclutamiento(user, proceso_seleccion, roles_permitidos: list[str]) -> bool:
    """
    Verifica si un usuario tiene permiso para ejecutar una acción sobre un proceso de selección
    según la matriz de permisos de Reclutamiento (MODULOS v02 §2.1):
    - ADMIN: acceso total.
    - RESPONSABLE / RH: si es el responsable del proceso o tiene asignación SELECCIONADOR / ADMIN.
    - ENTREVISTADOR: si tiene asignación ENTREVISTADOR en el proceso y la acción es de entrevistas.
    - EVALUADOR: si tiene asignación EVALUADOR en el proceso y la acción es de evaluaciones.
    """
    if not user or not user.is_authenticated:
        return False

    if getattr(user, "rol", None) == UserRole.ADMIN or getattr(user, "is_superuser", False):
        return True

    if not proceso_seleccion:
        return getattr(user, "rol", None) in [UserRole.RESPONSABLE, UserRole.ADMIN]

    # Verificar si el usuario es responsable directo del proceso
    if getattr(proceso_seleccion, "responsable_rh_id", None) == user.id:
        return True

    # Buscar asignación explícita de rol por proceso
    asignaciones = AsignacionRolProceso.objects.filter(
        proceso_seleccion=proceso_seleccion,
        usuario=user
    ).values_list("rol", flat=True)

    if not asignaciones.exists():
        # Fallback de compatibilidad: si no hay roles asignados explícitamente en esta convocatoria,
        # el usuario RESPONSABLE de la empresa mantiene permisos de RH
        return getattr(user, "rol", None) == UserRole.RESPONSABLE

    # Validar si alguno de los roles asignados coincide con los roles permitidos para la acción
    for rol_asignado in asignaciones:
        if rol_asignado in roles_permitidos or rol_asignado == AsignacionRolProceso.RolReclutamiento.ADMIN:
            return True

    return False


class IsRolReclutamientoPermitido(permissions.BasePermission):
    """
    Permiso DRF configurable por acción.
    Uso en vista: permission_classes = [IsRolReclutamientoPermitido.para("seleccionador", "admin")]
    """
    def __init__(self, roles_permitidos: list[str] = None):
        self.roles_permitidos = roles_permitidos or [
            AsignacionRolProceso.RolReclutamiento.SELECCIONADOR,
            AsignacionRolProceso.RolReclutamiento.ADMIN,
        ]

    @classmethod
    def para(cls, *roles):
        return cls(roles_permitidos=list(roles))

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        proceso = getattr(obj, "proceso_seleccion", None) or getattr(obj, "proceso", None)
        if not proceso and hasattr(obj, "postulacion"):
            proceso = getattr(obj.postulacion, "proceso_seleccion", None)
        return verificar_rol_reclutamiento(request.user, proceso, self.roles_permitidos)
