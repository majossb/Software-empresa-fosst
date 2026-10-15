from rest_framework.permissions import BasePermission

from .models import UserRole


class BaseRolePermission(BasePermission):
    """
    Permiso base para validar el rol del usuario autenticado.
    """

    allowed_roles = ()

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol in self.allowed_roles
        )


class EsAdmin(BaseRolePermission):
    """Solo administradores."""
    allowed_roles = (UserRole.ADMIN,)


class EsAuditor(BaseRolePermission):
    """Solo auditores."""
    allowed_roles = (UserRole.AUDITOR,)


class EsResponsableSST(BaseRolePermission):
    """Solo responsables SST."""
    allowed_roles = (UserRole.RESPONSABLE,)


class EsAltaDireccion(BaseRolePermission):
    """Solo alta dirección."""
    allowed_roles = (UserRole.ALTA_DIRECCION,)

class PerteneceAMismaEmpresa(BasePermission):
    """
    Garantiza el aislamiento entre empresas.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.rol == UserRole.ADMIN:
            return True

        empresa_obj = getattr(obj, "empresa", None)

        if empresa_obj is None:
            return False

        return empresa_obj == request.user.empresa