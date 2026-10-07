import uuid
from django.conf import settings
from django.db import models


class DispositivoConocido(models.Model):
    """
    Historial de dispositivos/IP desde los que un usuario ha iniciado sesión.
    Permite detectar accesos desde un dispositivo o ubicación nuevos.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dispositivos"
    )
    fingerprint = models.CharField(max_length=64, db_index=True)  # hash(user_agent + ip range)
    user_agent = models.TextField(blank=True)
    navegador = models.CharField(max_length=100, blank=True)
    sistema_operativo = models.CharField(max_length=100, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    primera_vez = models.DateTimeField(auto_now_add=True)
    ultima_vez = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "dispositivos_conocidos"
        unique_together = ("usuario", "fingerprint")


class EventoRiesgo(models.Model):
    """Registro de eventos de seguridad para el panel de métricas."""
    class Tipo(models.TextChoices):
        LOGIN_NUEVO_DISPOSITIVO = "LOGIN_NUEVO_DISPOSITIVO", "Login desde dispositivo nuevo"
        MULTIPLES_FALLOS = "MULTIPLES_FALLOS", "Múltiples intentos fallidos"
        CUENTA_BLOQUEADA = "CUENTA_BLOQUEADA", "Cuenta bloqueada temporalmente"
        IP_BLOQUEADA = "IP_BLOQUEADA", "IP bloqueada temporalmente"
        RATE_LIMIT_EXCEDIDO = "RATE_LIMIT_EXCEDIDO", "Límite de peticiones excedido"
        OTP_FALLIDO_REPETIDO = "OTP_FALLIDO_REPETIDO", "Múltiples códigos OTP incorrectos"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="eventos_riesgo",
    )
    tipo = models.CharField(max_length=40, choices=Tipo.choices)
    ip = models.GenericIPAddressField(null=True, blank=True)
    detalle = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "eventos_riesgo"
        ordering = ["-created_at"]
