"""
Signals para Formación y Desarrollo (§9).

- EvaluacionCompetencia post_save / post_delete:
  1. Si existe brecha de competencia (brecha_calculada > 0), registra o vincula
     automáticamente la brecha en HBSEO.
  2. Dispara el recálculo de MICHC para reflejar la competencia evaluada.
- RegistroFormacion post_save / post_delete:
  Dispara el recálculo automático de MICHC para el trabajador ante la realización,
  vencimiento o renovación de cursos obligatorios.
- CargoRequisitoFormacion post_save / post_delete:
  Dispara el recálculo en cascada de MICHC para todos los trabajadores que ocupen
  el cargo cuando cambian sus requisitos de formación.
"""
import logging
from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.hbseo.services import registrar_o_vincular_brecha
from apps.common.competencias import parse_nivel
from .models import EvaluacionCompetencia, RegistroFormacion, CargoRequisitoFormacion

logger = logging.getLogger(__name__)


def _despachar_recalculo_michc_trabajador(trabajador_id):
    """Ejecuta el recálculo de habilitación para un trabajador al completar la transacción."""
    def _ejecutar():
        try:
            from apps.michc.tasks import recalcular_michc_task
            from django.conf import settings
            if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
                recalcular_michc_task.delay(str(trabajador_id))
            else:
                from apps.michc.engine import recalcular_habilitacion
                recalcular_habilitacion(trabajador_id)
        except Exception:
            try:
                from apps.michc.engine import recalcular_habilitacion
                recalcular_habilitacion(trabajador_id)
            except Exception as e:
                logger.warning("No fue posible recalcular MICHC para trabajador %s: %s", trabajador_id, e)

    transaction.on_commit(_ejecutar)


@receiver(post_save, sender=EvaluacionCompetencia)
def on_evaluacion_competencia_saved(sender, instance, created, **kwargs):
    """Procesa la evaluación de competencia para HBSEO y MICHC."""
    trabajador = instance.trabajador
    competencia = instance.cargo_competencia
    req = parse_nivel(competencia.nivel_requerido or competencia.nivel, default=3)

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
        _despachar_recalculo_michc_trabajador(trabajador.id)

    transaction.on_commit(_procesar)


@receiver(post_delete, sender=EvaluacionCompetencia)
def on_evaluacion_competencia_deleted(sender, instance, **kwargs):
    """Recalcular MICHC al eliminar una evaluación de competencia."""
    _despachar_recalculo_michc_trabajador(instance.trabajador_id)


@receiver(post_save, sender=RegistroFormacion)
@receiver(post_delete, sender=RegistroFormacion)
def on_registro_formacion_changed(sender, instance, **kwargs):
    """
    Cualquier cambio o registro de formación dispara el recálculo de MICHC para el trabajador
    (on_commit pattern).
    """
    _despachar_recalculo_michc_trabajador(instance.trabajador_id)


@receiver(post_save, sender=CargoRequisitoFormacion)
@receiver(post_delete, sender=CargoRequisitoFormacion)
def on_cargo_requisito_formacion_changed(sender, instance, **kwargs):
    """
    Cuando se modifica o elimina un requisito de formación de un perfil de cargo,
    recalcula la habilitación de todos los trabajadores que ocupan dicho cargo.
    """
    if instance.perfil_cargo_id:
        from apps.capacitaciones.models import Trabajador
        trabajadores_ids = list(
            Trabajador.objects.filter(
                perfil_cargo_id=instance.perfil_cargo_id,
                activo=True
            ).values_list("id", flat=True)
        )
        for tid in trabajadores_ids:
            _despachar_recalculo_michc_trabajador(tid)
        logger.info(
            "Formación: Disparado recálculo de MICHC para %d trabajadores por cambio en requisito de cargo",
            len(trabajadores_ids)
        )
