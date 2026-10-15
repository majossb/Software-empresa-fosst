"""
Signals para Formación y Desarrollo (§9).

- EvaluacionCompetencia post_save:
  1. Si existe brecha de competencia (brecha_calculada > 0), registra o vincula
     automáticamente la brecha en HBSEO.
  2. Dispara el recálculo asíncrono de MICHC para reflejar la competencia evaluada.
"""
import logging
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.hbseo.services import registrar_o_vincular_brecha
from .models import EvaluacionCompetencia

logger = logging.getLogger(__name__)


@receiver(post_save, sender=EvaluacionCompetencia)
def on_evaluacion_competencia_saved(sender, instance, created, **kwargs):
    """Procesa la evaluación de competencia para HBSEO y MICHC."""
    trabajador = instance.trabajador
    competencia = instance.cargo_competencia
    req = competencia.nivel_requerido or competencia.nivel or 1

    def _procesar():
        # 1. Registro en HBSEO si hay brecha
        if instance.brecha_calculada > 0:
            clasificacion = "oportunidad_mejora" if instance.brecha_calculada == 1 else "incumplimiento"
            desc_base = (
                f"Brecha de competencia detectada en '{competencia.nombre}': "
                f"Nivel Requerido L{req} vs Nivel Alcanzado L{instance.nivel_alcanzado} "
                f"(Brecha: -{instance.brecha_calculada}). Método: {instance.get_metodo_display()}."
            )
            try:
                registrar_o_vincular_brecha(
                    empresa=trabajador.empresa,
                    modulo_origen="formacion",
                    clasificacion=clasificacion,
                    referencia_obj=instance,
                    descripcion_base=desc_base,
                    trabajador=trabajador,
                    detectado_por="Sistema (Formación/MCC)"
                )
                logger.info(
                    "Formación: Brecha registrada en HBSEO para trabajador %s en competencia %s",
                    trabajador.nombre, competencia.nombre
                )
            except Exception as e:
                logger.error("Error registrando brecha HBSEO desde Formación: %s", e)

        # 2. Recálculo en MICHC
        try:
            from apps.michc.tasks import recalcular_michc_task
            recalcular_michc_task.delay(str(trabajador.id))
        except Exception:
            try:
                from apps.michc.engine import recalcular_habilitacion
                recalcular_habilitacion(trabajador.id)
            except Exception as e:
                logger.warning("No fue posible recalcular MICHC tras evaluación de competencia: %s", e)

    transaction.on_commit(_procesar)
