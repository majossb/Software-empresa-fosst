"""
Modelos del Motor de Alertas (§5.2).

Una sola entidad de configuración `ReglaAlerta` parametrizada
que permite definir cualquier alerta de vencimiento sin duplicar tareas Celery.
"""
import uuid
from django.db import models
from apps.calendario.models import Notificacion


class ReglaAlerta(models.Model):
    class ModeloOrigen(models.TextChoices):
        TRABAJADOR = "Trabajador", "Trabajador (Contratos / Periodo de prueba)"
        EXAMEN_MEDICO = "ExamenMedicoOcupacional", "Examen Médico Ocupacional"
        LICENCIA_CONDUCCION = "LicenciaConduccion", "Licencia de Conducción"
        AFILIACION = "AfiliacionTrabajador", "Afiliación a Seguridad Social"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        "empresas.Empresa", on_delete=models.CASCADE, null=True, blank=True,
        related_name="reglas_alerta", help_text="Null para regla global del sistema"
    )
    codigo = models.CharField(max_length=60, help_text="Código único de la regla, ej. VENC_CONTRATO_60D")
    nombre = models.CharField(max_length=200)
    modelo_origen = models.CharField(max_length=50, choices=ModeloOrigen.choices)
    campo_fecha = models.CharField(max_length=100, help_text="Nombre del campo de fecha en el modelo, ej: fecha_fin_contrato")
    dias_anticipacion = models.IntegerField(help_text="Días de anticipación antes de la fecha (0 = vence hoy / vencido)")
    nivel_criticidad = models.CharField(
        max_length=20, choices=Notificacion.Nivel.choices, default=Notificacion.Nivel.NORMAL
    )
    mensaje_template = models.TextField(
        help_text="Plantilla de mensaje. Placeholders: {trabajador}, {documento}, {fecha}, {dias}, {cargo}, {tipo}"
    )
    roles_destinatarios = models.JSONField(
        default=list, help_text="Lista de roles a notificar, ej: ['RESPONSABLE', 'ALTA_DIRECCION']"
    )
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reglas_alerta"
        ordering = ["modelo_origen", "dias_anticipacion"]

    def __str__(self):
        emp_str = self.empresa.nombre if self.empresa else "Global"
        return f"{self.nombre} ({self.dias_anticipacion}d) — {emp_str}"
