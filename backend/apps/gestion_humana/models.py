"""
Modelos de Gestión Humana y Administración Laboral (§5).

- NovedadLaboral: registro de novedades (vacaciones, incapacidades, licencias, etc.)
  con recálculo determinista de estado contractual.
- ExamenMedicoOcupacional: historial de exámenes médicos ocupacionales y restricciones.
  (Nota de arquitectura: las restricciones se reconcilian con el cargo en MICHC - Fase 4,
  no generan brecha HBSEO directa sin validación de cargo).
- LicenciaConduccion: registro de licencias de conducción requeridas para el cargo.
"""
import uuid
from django.conf import settings
from django.db import models


class NovedadLaboral(models.Model):
    class Tipo(models.TextChoices):
        VACACIONES = "vacaciones", "Vacaciones"
        LICENCIA = "licencia", "Licencia"
        INCAPACIDAD = "incapacidad", "Incapacidad médica"
        SUSPENSION = "suspension", "Suspensión"
        PERIODO_PRUEBA = "periodo_prueba", "Periodo de prueba"
        REINTEGRO = "reintegro", "Reintegro"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trabajador = models.ForeignKey(
        "capacitaciones.Trabajador", on_delete=models.CASCADE, related_name="novedades_laborales"
    )
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    dias = models.PositiveIntegerField(null=True, blank=True, help_text="Duración en días calendario")
    observaciones = models.TextField(blank=True, null=True)
    archivo_soporte = models.ForeignKey(
        "evidencias.Archivo", on_delete=models.SET_NULL, null=True, blank=True, related_name="novedades_laborales"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="novedades_creadas"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "novedades_laborales"
        ordering = ["-fecha_inicio", "-created_at"]
        indexes = [
            models.Index(fields=["trabajador", "fecha_inicio", "fecha_fin"]),
            models.Index(fields=["tipo", "fecha_inicio"]),
        ]

    def __str__(self):
        return f"{self.trabajador.nombre} — {self.get_tipo_display()} ({self.fecha_inicio} a {self.fecha_fin or 'Indefinido'})"


class ExamenMedicoOcupacional(models.Model):
    class Tipo(models.TextChoices):
        INGRESO = "ingreso", "Ingreso (Pre-empleo)"
        PERIODICO = "periodico", "Periódico"
        EGRESO = "egreso", "Egreso (Retiro)"
        POST_INCAPACIDAD = "post_incapacidad", "Post-incapacidad / Reintegro"
        CAMBIO_CARGO = "cambio_cargo", "Cambio de cargo"

    class ConceptoAptitud(models.TextChoices):
        APTO = "apto", "Apto para el cargo"
        APTO_CON_RESTRICCIONES = "apto_con_restricciones", "Apto con restricciones"
        NO_APTO = "no_apto", "No apto para el cargo"
        APLAZADO = "aplazado", "Evaluación aplazada / Pendiente paraclínicos"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trabajador = models.ForeignKey(
        "capacitaciones.Trabajador", on_delete=models.CASCADE, related_name="examenes_medicos"
    )
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    fecha_examen = models.DateField()
    fecha_vencimiento = models.DateField(null=True, blank=True)
    concepto_aptitud = models.CharField(
        max_length=30, choices=ConceptoAptitud.choices, default=ConceptoAptitud.APTO
    )
    presenta_restricciones = models.BooleanField(default=False)
    descripcion_restricciones = models.TextField(blank=True, null=True)
    medico_evaluador = models.CharField(max_length=200, blank=True, null=True)
    licencia_so_medico = models.CharField(max_length=100, blank=True, null=True, help_text="Licencia en Salud Ocupacional del médico")
    archivo = models.ForeignKey(
        "evidencias.Archivo", on_delete=models.SET_NULL, null=True, blank=True, related_name="examenes_medicos"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "examenes_medicos_ocupacionales"
        ordering = ["-fecha_examen"]
        indexes = [
            models.Index(fields=["trabajador", "fecha_examen"]),
            models.Index(fields=["fecha_vencimiento"]),
        ]

    def __str__(self):
        return f"{self.trabajador.nombre} — Examen {self.get_tipo_display()} ({self.fecha_examen})"


class LicenciaConduccion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trabajador = models.ForeignKey(
        "capacitaciones.Trabajador", on_delete=models.CASCADE, related_name="licencias_conduccion"
    )
    categoria = models.CharField(max_length=10, help_text="Ej: A1, A2, B1, B2, C1, C2, C3")
    fecha_expedicion = models.DateField(null=True, blank=True)
    fecha_vencimiento = models.DateField()
    presenta_restricciones = models.BooleanField(default=False)
    descripcion_restricciones = models.TextField(blank=True, null=True, help_text="Ej: Uso de lentes, vehículo adaptado")
    archivo = models.ForeignKey(
        "evidencias.Archivo", on_delete=models.SET_NULL, null=True, blank=True, related_name="licencias_conduccion"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "licencias_conduccion"
        ordering = ["-fecha_vencimiento"]
        indexes = [
            models.Index(fields=["trabajador", "fecha_vencimiento"]),
        ]

    def __str__(self):
        return f"{self.trabajador.nombre} — Licencia {self.categoria} (Vence: {self.fecha_vencimiento})"
