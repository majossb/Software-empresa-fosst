import uuid
from django.db import models


class Incidente(models.Model):
    class Tipo(models.TextChoices):
        ACCIDENTE = "accidente", "Accidente"
        INCIDENTE = "incidente", "Incidente"
        ENFERMEDAD_LABORAL = "enfermedad_laboral", "Enfermedad laboral"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey("empresas.Empresa", on_delete=models.CASCADE, related_name="incidentes")
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    fecha = models.DateTimeField()
    descripcion = models.TextField()
    estado_investigacion = models.CharField(max_length=30, default="pendiente")
    dias_incapacidad = models.IntegerField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "incidentes"


class CalendarioActividad(models.Model):
    class Tipo(models.TextChoices):
        CAPACITACION = "capacitacion", "Capacitación"
        AUDITORIA = "auditoria", "Auditoría"
        VENCIMIENTO = "vencimiento", "Vencimiento"
        OTRO = "otro", "Otro"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey("empresas.Empresa", on_delete=models.CASCADE, related_name="calendario")
    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    fecha = models.DateTimeField()
    descripcion = models.TextField(blank=True, null=True)
    completada = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "calendario_actividades"


class Notificacion(models.Model):
    class Tipo(models.TextChoices):
        ALERTA = "alerta", "Alerta"
        RECORDATORIO = "recordatorio", "Recordatorio"
        INFORMATIVA = "informativa", "Informativa"

    class Nivel(models.TextChoices):
        NORMAL = "normal", "Normal"
        IMPORTANTE = "importante", "Importante"
        CRITICO = "critico", "Crítico"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey("empresas.Empresa", on_delete=models.CASCADE, related_name="notificaciones")
    usuario = models.ForeignKey(
        "accounts.Usuario", on_delete=models.CASCADE, null=True, blank=True, related_name="notificaciones"
    )
    actividad = models.ForeignKey(
        CalendarioActividad, on_delete=models.SET_NULL, null=True, blank=True, related_name="notificaciones"
    )
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    nivel = models.CharField(max_length=20, choices=Nivel.choices, default=Nivel.NORMAL)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    enviado_email = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notificaciones"
        ordering = ["-created_at"]
