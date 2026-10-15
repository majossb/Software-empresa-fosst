from rest_framework.permissions import BasePermission
from apps.accounts.models import UserRole
from apps.accounts.permissions import BaseRolePermission


class EsCorporativo(BaseRolePermission):
    """
    Permiso para roles corporativos autorizados en Módulo 0:
    ADMIN, RESPONSABLE (Responsable SST), ALTA_DIRECCION.
    """
    allowed_roles = (UserRole.ADMIN, UserRole.RESPONSABLE, UserRole.ALTA_DIRECCION)


class PerteneceAMismaEmpresaOAdmin(BasePermission):
    """
    Garantiza el aislamiento entre empresas: el usuario debe pertenecer
    a la misma empresa que se está consultando, o ser ADMIN.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.rol == UserRole.ADMIN:
            return True
        
        # Si el objeto es una Empresa
        if hasattr(obj, "nit") and hasattr(obj, "usuarios"):
            return obj == request.user.empresa
            
        # Si el objeto tiene FK a Empresa
        empresa_obj = getattr(obj, "empresa", None)
        if empresa_obj is None:
            return False
            
        return empresa_obj == request.user.empresa
