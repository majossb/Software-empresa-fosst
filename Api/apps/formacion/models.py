"""
Modelos de Formación y Desarrollo — Matriz de Competencias del Cargo (MCC) — §9.

- EvaluacionCompetencia: registro de evaluación periódica del nivel alcanzado
  por un trabajador en una competencia específica del cargo (Nivel 1 a 4).
  Calcula automáticamente la brecha respecto al nivel requerido.
"""
import uuid
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class EvaluacionCompetencia(models.Model):
    class MetodoEvaluacion(models.TextChoices):
        OBSERVACION = "observacion_directa", "Observación Directa en Puesto"
        PRUEBA_TECNICA = "prueba_tecnica", "Prueba Técnica / Conocimiento"
        EVALUACION_360 = "evaluacion_360", "Evaluación 360° / Jefe Directo"
        CERTIFICACION = "certificacion", "Certificación / Título Acreditado"
        ENTREVISTA = "entrevista", "Entrevista por Competencias"
        AUTOEVALUACION = "autoevaluacion", "Autoevaluación"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trabajador = models.ForeignKey(
        "capacitaciones.Trabajador",
        on_delete=models.CASCADE,
        related_name="evaluaciones_competencias"
    )
    cargo_competencia = models.ForeignKey(
        "perfilcargo.CargoCompetencia",
        on_delete=models.CASCADE,
        related_name="evaluaciones"
    )
    nivel_alcanzado = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        help_text="Nivel alcanzado (1: Básico, 2: Intermedio, 3: Avanzado, 4: Experto)"
    )
    brecha_calculada = models.IntegerField(
        default=0,
        help_text="Brecha negativa (Nivel Requerido - Nivel Alcanzado). 0 si cumple o supera."
    )
    evaluado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="competencias_evaluadas"
    )
    fecha_evaluacion = models.DateField()
    metodo = models.CharField(
        max_length=40,
        choices=MetodoEvaluacion.choices,
        default=MetodoEvaluacion.EVALUACION_360
    )
    observacion = models.TextField(blank=True, null=True)
    soporte_archivo = models.ForeignKey(
        "evidencias.Archivo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evaluaciones_competencias"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "evaluaciones_competencias_mcc"
        ordering = ["-fecha_evaluacion", "-created_at"]
        indexes = [
            models.Index(fields=["trabajador", "fecha_evaluacion"]),
            models.Index(fields=["cargo_competencia", "nivel_alcanzado"]),
        ]

    def __str__(self):
        req = self.cargo_competencia.nivel_requerido or self.cargo_competencia.nivel or 1
        return f"{self.trabajador.nombre} — {self.cargo_competencia.nombre} (Req: L{req} / Alc: L{self.nivel_alcanzado})"

    def save(self, *args, **kwargs):
        # Calcular brecha automáticamente
        req = self.cargo_competencia.nivel_requerido or self.cargo_competencia.nivel or 1
        self.brecha_calculada = max(0, req - self.nivel_alcanzado)
        super().save(*args, **kwargs)
