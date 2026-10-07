from rest_framework.permissions import BasePermission
from apps.accounts.models import UserRole


class IsRol(BasePermission):
    """
    Permission que verifica si el usuario tiene uno de los roles permitidos.
    Soporta roles en minúscula o mayúscula ('alta_direccion' o 'ALTA_DIRECCION').

    Uso:
        permission_classes = [IsAuthenticated, IsRol.de('alta_direccion')]
    """
    roles_permitidos = set()

    @classmethod
    def de(cls, *roles):
        roles_set = {r.upper() for r in roles}
        return type(
            f"IsRol_{'_'.join(roles)}",
            (cls,),
            {"roles_permitidos": roles_set},
        )

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        user_rol = getattr(request.user, "rol", "")
        if user_rol == UserRole.ADMIN or user_rol == "ADMIN":
            return True
        return user_rol.upper() in self.roles_permitidos


class IsRolParaEscritura(BasePermission):
    """
    Permite lectura (GET, HEAD, OPTIONS) a cualquier usuario autenticado,
    pero restringe escritura (POST, PUT, PATCH, DELETE) a los roles indicados.

    Uso:
        permission_classes = [IsAuthenticated, IsRolParaEscritura.de('responsable')]
    """
    roles_permitidos = set()

    @classmethod
    def de(cls, *roles):
        roles_set = {r.upper() for r in roles}
        return type(
            f"IsRolEscritura_{'_'.join(roles)}",
            (cls,),
            {"roles_permitidos": roles_set},
        )

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        user_rol = getattr(request.user, "rol", "")
        if user_rol == UserRole.ADMIN or user_rol == "ADMIN":
            return True
        return user_rol.upper() in self.roles_permitidos
