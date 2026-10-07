import uuid
from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    Registro transversal de auditoría. Sustituye y amplía el `auditLog`
    que ya existía en Prisma (usado solo para LOGIN). Ahora cubre:
    login/logout, actividad de módulos, historial de cambios y
    acciones administrativas.
    """
    class Accion(models.TextChoices):
        LOGIN = "LOGIN", "Inicio de sesión"
        LOGOUT = "LOGOUT", "Cierre de sesión"
        LOGIN_FALLIDO = "LOGIN_FALLIDO", "Intento de inicio de sesión fallido"
        REGISTRO = "REGISTRO", "Registro de usuario"
        ACTIVACION_CUENTA = "ACTIVACION_CUENTA", "Activación de cuenta"
        CAMBIO_PASSWORD = "CAMBIO_PASSWORD", "Cambio de contraseña"
        RESET_PASSWORD = "RESET_PASSWORD", "Recuperación de contraseña"
        CREACION = "CREACION", "Creación de registro"
        ACTUALIZACION = "ACTUALIZACION", "Actualización de registro"
        ELIMINACION = "ELIMINACION", "Eliminación de registro"
        ACCION_ADMIN = "ACCION_ADMIN", "Acción administrativa"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="audit_logs",
    )
    empresa = models.ForeignKey(
        "empresas.Empresa", on_delete=models.SET_NULL, null=True, blank=True,
    )
    accion = models.CharField(max_length=30, choices=Accion.choices)
    tabla_afectada = models.CharField(max_length=100, blank=True)
    registro_id = models.CharField(max_length=100, blank=True)
    valores_anteriores = models.JSONField(null=True, blank=True)
    valores_nuevos = models.JSONField(null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    ruta = models.CharField(max_length=255, blank=True)
    metodo_http = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        indexes = [
            models.Index(fields=["usuario", "created_at"]),
            models.Index(fields=["accion", "created_at"]),
        ]
        ordering = ["-created_at"]
