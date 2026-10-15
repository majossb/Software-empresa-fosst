import hmac
import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    RESPONSABLE = "RESPONSABLE", "Responsable SST"
    AUDITOR = "AUDITOR", "Auditor"
    ALTA_DIRECCION = "ALTA_DIRECCION", "Alta Dirección"
    ADMIN = "ADMIN", "Administrador"


class TipoDocumento(models.TextChoices):
    CC = "CC", "Cédula de ciudadanía"
    CE = "CE", "Cédula de extranjería"
    TI = "TI", "Tarjeta de identidad"
    PASAPORTE = "PASAPORTE", "Pasaporte"
    NIT = "NIT", "NIT"


class Usuario(AbstractUser):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    tipo_documento = models.CharField(
        max_length=20,
        choices=TipoDocumento.choices,
        default=TipoDocumento.CC,
    )

    documento = models.CharField(
        max_length=30,
        db_index=True,
    )

    rol = models.CharField(
        max_length=20,
        choices=UserRole.choices,
    )

    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.PROTECT,
        related_name="usuarios",
        null=True,
        blank=True,
    )

    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    email = models.EmailField()

    activo = models.BooleanField(default=True)
    email_verificado = models.BooleanField(default=False)
    otp_habilitado = models.BooleanField(default=True)

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "usuarios"
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "documento", "rol"],
                name="uq_usuario_empresa_documento_rol",
            )
        ]

    def __str__(self):
        nombre = self.get_full_name() or self.username
        return f"{nombre} ({self.get_rol_display()})"
    
class TokenActivacion(models.Model):
    """Token de un solo uso para activar la cuenta vía correo electrónico."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="tokens_activacion")
    token = models.CharField(max_length=64, unique=True)
    usado = models.BooleanField(default=False)
    expira_en = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tokens_activacion"

    def esta_vigente(self):
        return not self.usado and timezone.now() < self.expira_en


class CodigoOTP(models.Model):
    """Código de un solo uso (6 dígitos) enviado por correo para el segundo factor de login."""
    class Proposito(models.TextChoices):
        LOGIN = "LOGIN", "Verificación de inicio de sesión"
        RESET_PASSWORD = "RESET_PASSWORD", "Recuperación de contraseña"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="codigos_otp")
    codigo = models.CharField(max_length=6)
    proposito = models.CharField(max_length=20, choices=Proposito.choices)
    intentos = models.PositiveSmallIntegerField(default=0)
    usado = models.BooleanField(default=False)
    expira_en = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "codigos_otp"

    MAX_INTENTOS = 5

    def esta_vigente(self):
        return (
            not self.usado
            and self.intentos < self.MAX_INTENTOS
            and timezone.now() < self.expira_en
        )

    def verificar_codigo(self, codigo_ingresado: str) -> bool:
        """Comparación de tiempo constante para evitar timing attacks."""
        return hmac.compare_digest(self.codigo, codigo_ingresado)

    @classmethod
    def crear_para(cls, usuario, proposito):
        # Invalidar todos los OTP anteriores pendientes del mismo usuario y propósito
        cls.objects.filter(
            usuario=usuario,
            proposito=proposito,
            usado=False,
        ).update(usado=True)

        # Generar código criptográficamente seguro
        codigo = f"{secrets.randbelow(1_000_000):06d}"

        return cls.objects.create(
            usuario=usuario,
            codigo=codigo,
            proposito=proposito,
            expira_en=timezone.now() + timedelta(minutes=settings.OTP_EXPIRATION_MINUTES),
        )


class TokenRecuperacion(models.Model):
    """Token de un solo uso para el enlace de recuperación de contraseña."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="tokens_recuperacion")
    token = models.CharField(max_length=64, unique=True)
    usado = models.BooleanField(default=False)
    expira_en = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tokens_recuperacion"

    def esta_vigente(self):
        return not self.usado and timezone.now() < self.expira_en
