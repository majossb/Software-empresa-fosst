"""
Signals de integración de MICHC (§6).

Dispara el recálculo automático de la habilitación del trabajador ante
cualquier cambio en:
- Perfil de cargo o datos del trabajador
- Exámenes médicos ocupacionales
- Licencias de conducción
- Novedades laborales
- Afiliaciones a seguridad social
- Re-versionamiento en cascada del perfil de cargo (RN-11)
"""
import logging
from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.capacitaciones.models import Trabajador, AfiliacionTrabajador
from apps.gestion_humana.models import ExamenMedicoOcupacional, LicenciaConduccion, NovedadLaboral
from apps.perfilcargo.models import CargoVersion
from .engine import recalcular_habilitacion

logger = logging.getLogger(__name__)


def _despachar_recalculo(trabajador_id):
    """Ejecuta el recálculo al completar la transacción."""
    try:
        from .tasks import recalcular_michc_task
        # Si Celery está en eager o disponible
        transaction.on_commit(lambda: recalcular_michc_task.delay(str(trabajador_id)))
    except Exception:
        transaction.on_commit(lambda: recalcular_habilitacion(trabajador_id))


@receiver(post_save, sender=Trabajador)
def on_trabajador_saved_recalcular_michc(sender, instance, created, **kwargs):
    _despachar_recalculo(instance.id)


@receiver(post_save, sender=ExamenMedicoOcupacional)
@receiver(post_delete, sender=ExamenMedicoOcupacional)
def on_examen_medico_changed_recalcular_michc(sender, instance, **kwargs):
    _despachar_recalculo(instance.trabajador_id)


@receiver(post_save, sender=LicenciaConduccion)
@receiver(post_delete, sender=LicenciaConduccion)
def on_licencia_changed_recalcular_michc(sender, instance, **kwargs):
    _despachar_recalculo(instance.trabajador_id)


@receiver(post_save, sender=NovedadLaboral)
@receiver(post_delete, sender=NovedadLaboral)
def on_novedad_changed_recalcular_michc(sender, instance, **kwargs):
    _despachar_recalculo(instance.trabajador_id)


@receiver(post_save, sender=AfiliacionTrabajador)
@receiver(post_delete, sender=AfiliacionTrabajador)
def on_afiliacion_changed_recalcular_michc(sender, instance, **kwargs):
    _despachar_recalculo(instance.trabajador_id)


@receiver(post_save, sender=CargoVersion)
def on_cargo_version_created_recalcular_trabajadores(sender, instance, created, **kwargs):
    """
    RN-11 / §4.2: Cuando un perfil de cargo se re-versiona, se dispara el recálculo
    de habilitación para todos los trabajadores que ocupan dicho cargo.
    """
    if created and instance.perfil_cargo_id:
        trabajadores_ids = list(
            Trabajador.objects.filter(
                perfil_cargo_id=instance.perfil_cargo_id,
                activo=True
            ).values_list("id", flat=True)
        )
        for tid in trabajadores_ids:
            _despachar_recalculo(tid)
        logger.info("MICHC: Disparado recálculo para %d trabajadores por re-versionamiento de cargo", len(trabajadores_ids))
