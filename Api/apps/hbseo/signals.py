"""
HBSEO — Signals.

RN-17: Todo cambio de estado de una Brecha genera automáticamente un BrechaEvento.
El estado nunca se actualiza sin dejar rastro.

Patrón de referencia: apps/perfilcargo/signals.py (primer signal del repo, §0).
"""
import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Brecha, BrechaEvento

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Brecha)
def on_brecha_estado_changed(sender, instance, **kwargs):
    """
    RN-17: Detecta cambios de estado en Brecha y crea un BrechaEvento.

    Usa pre_save para comparar el estado actual con el de la BD antes de guardar.
    El evento se crea después del save (no aquí) — se marca con un flag en la
    instancia para que post_save lo recoja, pero dado que el patrón de
    perfilcargo/signals.py usa on_commit solo cuando hay tasks async, y aquí
    el evento es un simple INSERT síncrono, lo hacemos directo en pre_save
    guardando el estado anterior para crear el evento en post_save.

    Nota: se usa pre_save en vez de un campo _estado_previo porque es más
    robusto contra cambios de save() que no pasen por el signal.
    """
    if not instance.pk:
        # Brecha nueva — el evento de detección lo crea el servicio, no el signal
        return

    try:
        anterior = Brecha.objects.get(pk=instance.pk)
    except Brecha.DoesNotExist:
        return

    if anterior.estado != instance.estado:
        # Guardar referencia para crear evento después del save
        instance._estado_anterior = anterior.estado
        instance._estado_nuevo = instance.estado
    else:
        instance._estado_anterior = None


# Importar post_save para crear el evento después de que el save sea exitoso
from django.db.models.signals import post_save  # noqa: E402


@receiver(post_save, sender=Brecha)
def on_brecha_saved_create_evento(sender, instance, created, **kwargs):
    """Crea BrechaEvento de cambio de estado si se detectó un cambio en pre_save."""
    if created:
        # Brecha nueva — no crear evento duplicado (el servicio ya crea uno de detección)
        return

    estado_anterior = getattr(instance, "_estado_anterior", None)
    if estado_anterior is None:
        return

    estado_nuevo = getattr(instance, "_estado_nuevo", instance.estado)

    BrechaEvento.objects.create(
        brecha=instance,
        tipo_evento=BrechaEvento.TipoEvento.CAMBIO_ESTADO,
        descripcion=(
            f"Estado cambiado de '{estado_anterior}' a '{estado_nuevo}'"
        ),
    )

    logger.info(
        "RN-17: Brecha %s — estado cambiado de '%s' a '%s', evento registrado",
        instance.codigo, estado_anterior, estado_nuevo,
    )

    # Limpiar flags temporales
    instance._estado_anterior = None
    instance._estado_nuevo = None
