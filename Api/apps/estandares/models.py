import uuid
from django.db import models


class Estandar(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    capitulo = models.CharField(max_length=10)  # I, II, III
    ciclo_phva = models.CharField(max_length=20)  # Planear, Hacer, Verificar, Actuar
    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    puntaje_maximo = models.DecimalField(max_digits=5, decimal_places=2)
    obligatorio = models.BooleanField(default=True)

    class Meta:
        db_table = "estandares"


class Evaluacion(models.Model):
    class Estado(models.TextChoices):
        EN_PROGRESO = "en_progreso", "En progreso"
        COMPLETADA = "completada", "Completada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey("empresas.Empresa", on_delete=models.CASCADE, related_name="evaluaciones")
    anio = models.IntegerField()
    capitulo = models.CharField(max_length=10)
    puntaje_total = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.EN_PROGRESO)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "evaluaciones"
        constraints = [
            models.UniqueConstraint(fields=["empresa", "anio"], name="uq_evaluacion_empresa_anio")
        ]


class Respuesta(models.Model):
    class Estado(models.TextChoices):
        CUMPLE = "cumple", "Cumple"
        NO_CUMPLE = "no_cumple", "No cumple"
        PARCIAL = "parcial", "Parcial"
        NO_APLICA = "no_aplica", "No aplica"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE, related_name="respuestas")
    estandar = models.ForeignKey(Estandar, on_delete=models.PROTECT, related_name="respuestas")
    estado = models.CharField(max_length=20, choices=Estado.choices)
    puntaje = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    observacion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "respuestas"
        constraints = [
            models.UniqueConstraint(fields=["evaluacion", "estandar"], name="uq_respuesta_evaluacion_estandar")
        ]


class Apelacion(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        RESUELTA = "resuelta", "Resuelta"
        ACEPTADA = "aceptada", "Aceptada"
        RECHAZADA = "rechazada", "Rechazada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    respuesta = models.ForeignKey(Respuesta, on_delete=models.CASCADE, related_name="apelaciones")
    solicitante = models.ForeignKey("accounts.Usuario", on_delete=models.PROTECT, related_name="apelaciones")
    motivo = models.TextField()
    respuesta_auditor = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "apelaciones"

