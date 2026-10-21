"""
Modelos del Motor de Alertas (§5.2).

Una sola entidad de configuración `ReglaAlerta` parametrizada
que permite definir cualquier alerta de vencimiento sin duplicar tareas Celery.

Fase 5: soporte para alertas de formación y competencias.
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
        # Fase 5 — Formación & Competencias
        REGISTRO_FORMACION = "RegistroFormacion", "Registro de Formación (Certificados)"
        EVALUACION_COMPETENCIA = "EvaluacionCompetencia", "Evaluación de Competencia"

    class TipoHandler(models.TextChoices):
        EXACTA = "exacta", "Exacta (fecha == hoy + N días)"
        VENCIDO_RANGO = "vencido_rango", "Rango vencido (fecha < hoy)"
        SIN_REGISTRAR = "sin_registrar", "Sin registrar (trabajador sin certificado obligatorio)"
        EVALUACION_PENDIENTE = "evaluacion_pendiente", "Evaluación de competencia pendiente o desactualizada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        "empresas.Empresa", on_delete=models.CASCADE, null=True, blank=True,
        related_name="reglas_alerta", help_text="Null para regla global del sistema"
    )
    codigo = models.CharField(max_length=60, help_text="Código único de la regla, ej. VENC_CONTRATO_60D")
    nombre = models.CharField(max_length=200)
    modelo_origen = models.CharField(max_length=50, choices=ModeloOrigen.choices)
    campo_fecha = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Nombre del campo de fecha en el modelo, ej: fecha_fin_contrato"
    )
    tipo_handler = models.CharField(
        max_length=30,
        choices=TipoHandler.choices,
        default=TipoHandler.EXACTA,
        help_text="Modo de evaluación de la regla"
    )
    dias_anticipacion = models.IntegerField(
        default=0,
        help_text="Días de anticipación antes de la fecha (0 = vence hoy / vencido)"
    )
    nivel_criticidad = models.CharField(
        max_length=20, choices=Notificacion.Nivel.choices, default=Notificacion.Nivel.NORMAL
    )
    mensaje_template = models.TextField(
        help_text=(
            "Plantilla de mensaje. Placeholders: "
            "{trabajador}, {documento}, {fecha}, {dias}, {cargo}, {tipo}, {curso}, {competencia}"
        )
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
