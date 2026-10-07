import uuid
from django.db import models


class Hallazgo(models.Model):
    class Tipo(models.TextChoices):
        NO_CONFORMIDAD = "no_conformidad", "No conformidad"
        OBSERVACION = "observacion", "Observación"
        OPORTUNIDAD_MEJORA = "oportunidad_mejora", "Oportunidad de mejora"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evaluacion = models.ForeignKey("estandares.Evaluacion", on_delete=models.CASCADE, related_name="hallazgos")
    auditor = models.ForeignKey("accounts.Usuario", on_delete=models.PROTECT, related_name="hallazgos")
    estandar = models.ForeignKey("estandares.Estandar", on_delete=models.SET_NULL, null=True, blank=True, related_name="hallazgos")
    respuesta = models.ForeignKey("estandares.Respuesta", on_delete=models.SET_NULL, null=True, blank=True, related_name="hallazgos")
    descripcion = models.TextField()
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "hallazgos"


class PlanMejora(models.Model):
    class Prioridad(models.TextChoices):
        URGENTE = "urgente", "Urgente (3 meses)"
        IMPORTANTE = "importante", "Importante (6 meses)"
        ACEPTABLE = "aceptable", "Aceptable (1 año)"

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        EN_PROGRESO = "en_progreso", "En progreso"
        COMPLETADO = "completado", "Completado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey("empresas.Empresa", on_delete=models.CASCADE, related_name="planes_mejora")
    evaluacion = models.ForeignKey(
        "estandares.Evaluacion", on_delete=models.SET_NULL, null=True, blank=True, related_name="planes_mejora"
    )
    accion = models.TextField()
    responsable = models.CharField(max_length=150)
    prioridad = models.CharField(max_length=20, choices=Prioridad.choices)
    fecha_limite = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "plan_mejora"
