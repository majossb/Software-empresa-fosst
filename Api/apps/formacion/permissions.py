from rest_framework.exceptions import PermissionDenied, ValidationError
from apps.accounts.models import UserRole
from apps.capacitaciones.models import Trabajador
from apps.perfilcargo.models import PerfilCargo


def es_jefe_inmediato(usuario, trabajador) -> bool:
    """
    Determina si `usuario` es el jefe inmediato de `trabajador`.
    Resuelve: cargo del trabajador -> cargo del jefe -> persona que ocupa ese cargo -> su usuario.
    """
    if not usuario or not trabajador:
        return False

    if not trabajador.perfil_cargo or not trabajador.perfil_cargo.jefe_inmediato:
        return False

    cargo_jefe = trabajador.perfil_cargo.jefe_inmediato

    # Buscar trabajadores que ocupen el cargo de jefe en la misma empresa
    posibles_jefes = Trabajador.objects.filter(
        empresa=trabajador.empresa,
        perfil_cargo=cargo_jefe,
        activo=True
    ).exclude(deleted_at__isnull=False)

    for jefe in posibles_jefes:
        u = jefe.resolver_usuario()
        if u and u.id == usuario.id:
            return True

    return False


def obtener_subordinados_de_usuario(usuario):
    """
    Retorna el QuerySet de trabajadores subordinados directamente del usuario.
    """
    if not usuario or not getattr(usuario, "empresa", None):
        return Trabajador.objects.none()

    # Identificar trabajadores vinculados a este usuario
    trabajadores_usuario = Trabajador.objects.filter(
        empresa=usuario.empresa,
        activo=True
    ).filter(
        usuario=usuario
    ) | Trabajador.objects.filter(
        empresa=usuario.empresa,
        documento=usuario.documento,
        activo=True
    )

    cargos_usuario = PerfilCargo.objects.filter(
        trabajadores__in=trabajadores_usuario,
        empresa=usuario.empresa,
        activo=True
    ).distinct()

    if not cargos_usuario.exists():
        return Trabajador.objects.none()

    cargos_subordinados = PerfilCargo.objects.filter(
        jefe_inmediato__in=cargos_usuario,
        empresa=usuario.empresa,
        activo=True
    )

    return Trabajador.objects.filter(
        empresa=usuario.empresa,
        perfil_cargo__in=cargos_subordinados,
        activo=True
    ).exclude(deleted_at__isnull=False)


def verificar_permiso_evaluar(usuario, trabajador, metodo="evaluacion_360"):
    """
    Valida si `usuario` tiene autorización para evaluar a `trabajador`.
    Retorna el rol con el que evalúa ('gestion_humana', 'jefe_inmediato', 'autoevaluacion')
    o lanza PermissionDenied / ValidationError.
    """
    if not usuario or not usuario.is_authenticated:
        raise PermissionDenied("Usuario no autenticado.")

    if not trabajador:
        raise ValidationError("Trabajador no especificado.")

    if usuario.empresa_id != trabajador.empresa_id:
        raise PermissionDenied("No puede evaluar a un trabajador de otra empresa.")

    # Verificar si es autoevaluación
    usuario_trabajador = trabajador.resolver_usuario()
    es_mismo_usuario = (usuario_trabajador and usuario_trabajador.id == usuario.id) or (trabajador.documento == usuario.documento)

    if es_mismo_usuario:
        if metodo == "autoevaluacion":
            return "autoevaluacion"
        raise ValidationError("Nadie se evalúa a sí mismo salvo mediante el método 'autoevaluación'.")

    # Si es Gestión Humana o Administrador
    if getattr(usuario, "rol", None) in [UserRole.RESPONSABLE, UserRole.ADMIN] or usuario.is_staff or usuario.is_superuser:
        return "gestion_humana"

    # Si es jefe inmediato
    if es_jefe_inmediato(usuario, trabajador):
        return "jefe_inmediato"

    raise PermissionDenied("No tiene permisos para evaluar a este trabajador. Solo Gestión Humana o el jefe inmediato pueden hacerlo.")
