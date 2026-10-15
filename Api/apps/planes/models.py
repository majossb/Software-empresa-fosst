import uuid
from django.db import models


class Plan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    precio_mensual = models.DecimalField(max_digits=10, decimal_places=2)
    precio_anual = models.DecimalField(max_digits=10, decimal_places=2)
    max_usuarios = models.IntegerField()
    max_evidencias_mb = models.IntegerField()
    tiene_auditoria = models.BooleanField(default=False)
    tiene_informes = models.BooleanField(default=False)
    tiene_calendario = models.BooleanField(default=False)
    tiene_alertas_email = models.BooleanField(default=False)
    tiene_historico = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "planes"

    def __str__(self):
        return self.nombre


class Suscripcion(models.Model):
    class Estado(models.TextChoices):
        ACTIVA = "activa", "Activa"
        SUSPENDIDA = "suspendida", "Suspendida"
        CANCELADA = "cancelada", "Cancelada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey("empresas.Empresa", on_delete=models.CASCADE, related_name="suscripciones")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="suscripciones")
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVA)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(null=True, blank=True)
    forma_pago = models.CharField(max_length=50, blank=True, null=True)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "suscripciones"
