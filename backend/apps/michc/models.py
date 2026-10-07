"""
Modelos de la Matriz Inteligente de Cumplimiento y Habilitación del Cargo (MICHC) — §6.

- EvaluacionHabilitacion: Matriz que cruza el PerfilCargo con el expediente real
  del Trabajador, calculando porcentaje de cumplimiento, semáforo, compatibilidad y estado.
- DetalleCumplimientoRequisito: Desglose punto por punto de cada requisito del cargo
  (educación, experiencia, formación, aptitudes médicas, licencias, etc.).
"""
import uuid
from django.db import models


class EvaluacionHabilitacion(models.Model):
    class Semaforo(models.TextChoices):
        VERDE = "verde", "Verde (Cumplimiento Total ≥100%)"
        AMARILLO = "amarillo", "Amarillo (Cumplimiento Parcial ≥80%)"
        ROJO = "rojo", "Rojo (Incumplimiento Crítico <80%)"

    class EstadoHabilitacion(models.TextChoices):
        HABILITADO = "habilitado", "Habilitado"
        RESTRINGIDO = "restringido", "Restringido (Con observaciones)"
        PENDIENTE_DOCUMENTAL = "pendiente_documental", "Pendiente Documental"
        NO_APTO = "no_apto", "No Apto"

    class Compatibilidad(models.TextChoices):
        COMPATIBLE = "compatible", "Compatible"
        COMPATIBLE_CON_RESTRICCIONES = "compatible_con_restricciones", "Compatible con Restricciones"
        INCOMPATIBLE_TEMPORAL = "incompatible_temporal", "Incompatible Temporal"

    class NivelAtencion(models.TextChoices):
        BAJO = "bajo", "Bajo"
        MEDIO = "medio", "Medio"
        ALTO = "alto", "Alto"
        CRITICO = "critico", "Crítico"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trabajador = models.OneToOneField(
        "capacitaciones.Trabajador",
        on_delete=models.CASCADE,
        related_name="evaluacion_habilitacion"
    )
    perfil_cargo = models.ForeignKey(
        "perfilcargo.PerfilCargo",
        on_delete=models.CASCADE,
        related_name="evaluaciones_habilitacion",
        null=True,
        blank=True
    )
    porcentaje_cumplimiento = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    semaforo = models.CharField(max_length=20, choices=Semaforo.choices, default=Semaforo.ROJO)
    estado_habilitacion = models.CharField(
        max_length=30, choices=EstadoHabilitacion.choices, default=EstadoHabilitacion.PENDIENTE_DOCUMENTAL
    )
    compatibilidad = models.CharField(
        max_length=40, choices=Compatibilidad.choices, default=Compatibilidad.COMPATIBLE
    )
    nivel_atencion = models.CharField(
        max_length=20, choices=NivelAtencion.choices, default=NivelAtencion.MEDIO
    )

    # Textos generados por IA con hash para deduplicación
    interpretacion_ia = models.TextField(blank=True, null=True)
    recomendacion_ia = models.TextField(blank=True, null=True)
    contexto_hash = models.CharField(max_length=64, blank=True, null=True)

    calculado_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "evaluaciones_habilitacion_michc"
        ordering = ["porcentaje_cumplimiento", "-calculado_at"]
        indexes = [
            models.Index(fields=["trabajador", "semaforo"]),
            models.Index(fields=["perfil_cargo", "estado_habilitacion"]),
        ]

    def __str__(self):
        cargo_str = self.perfil_cargo.nombre_cargo if self.perfil_cargo else "Sin Cargo"
        return f"{self.trabajador.nombre} — {cargo_str} ({self.porcentaje_cumplimiento}% - {self.semaforo})"


class DetalleCumplimientoRequisito(models.Model):
    class TipoRequisito(models.TextChoices):
        EDUCACION = "educacion", "Educación / Nivel Académico"
        EXPERIENCIA = "experiencia", "Experiencia Laboral"
        FORMACION = "formacion", "Formación / Cursos Obligatorios"
        CERTIFICACION = "certificacion", "Certificaciones Específicas"
        LICENCIA = "licencia", "Licencia de Conducción / Profesional"
        APTITUD_MEDICA = "aptitud_medica", "Aptitud Médica / Exámenes"
        RESTRICCION_MEDICA = "restriccion_medica", "Evaluación de Restricciones Médicas"
        COMPETENCIA = "competencia", "Competencias del Cargo"
        AFILIACION = "afiliacion", "Afiliaciones a Seguridad Social"

    class Cumple(models.TextChoices):
        SI = "si", "Cumple Totalmente"
        PARCIAL = "parcial", "Cumple Parcialmente"
        NO = "no", "No Cumple"
        NO_APLICA = "no_aplica", "No Aplica"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evaluacion_habilitacion = models.ForeignKey(
        EvaluacionHabilitacion,
        on_delete=models.CASCADE,
        related_name="detalles_requisitos"
    )
    tipo_requisito = models.CharField(max_length=30, choices=TipoRequisito.choices)
    requisito_descripcion = models.CharField(max_length=300)
    cumple = models.CharField(max_length=20, choices=Cumple.choices, default=Cumple.NO)
    observacion = models.TextField(blank=True, null=True)
    evidencia_id = models.CharField(max_length=100, blank=True, null=True, help_text="ID del archivo/registro que soporta el cumplimiento")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "detalles_cumplimiento_michc"
        ordering = ["tipo_requisito", "created_at"]

    def __str__(self):
        return f"[{self.get_tipo_requisito_display()}] {self.requisito_descripcion}: {self.get_cumple_display()}"
