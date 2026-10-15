"""
RN-11 — Re-versionado en cascada del perfil del cargo.

Si se modifica CatalogoPeligro, CatalogoEPP, o la relación M2M entre ellos
(epps_sugeridos), todo PerfilCargo que referencie esos catálogos debe:
  (a) recalcular su lista efectiva de peligros/EPP (ya es una relación viva,
      no requiere recálculo de datos, solo re-snapshot),
  (b) generar una nueva fila en CargoVersion con snapshot completo,
  (c) registrar en motivo_cambio que el origen fue una actualización de
      catálogo, no una edición manual del usuario.

Este signal es disparado por el catálogo, nunca por un endpoint que dependa
de que el usuario lo active — es el mismo patrón de "versionado disparado
por evento" que se reutiliza en Fase 2 para HBSEO (§4.2 de la especificación).
"""
import logging

from django.db import transaction
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from .models import CatalogoPeligro, CatalogoEPP, PerfilCargo

logger = logging.getLogger(__name__)


def _reversionar_perfiles(perfiles_qs, motivo_cambio):
    """Crea una nueva CargoVersion para cada perfil de la queryset, con snapshot completo."""
    # Import diferido: evita import circular (serializers.py importa de models.py).
    from .serializers import PerfilCargoSerializer
    from .models import CargoVersion

    import json
    from django.core.serializers.json import DjangoJSONEncoder

    for perfil in perfiles_qs.distinct():
        perfil.version_actual += 1
        perfil.save(update_fields=['version_actual'])
        raw_snapshot = PerfilCargoSerializer(perfil).data
        snapshot_data = json.loads(json.dumps(raw_snapshot, cls=DjangoJSONEncoder))
        CargoVersion.objects.create(
            perfil_cargo=perfil,
            numero_version=perfil.version_actual,
            snapshot=snapshot_data,
            motivo_cambio=motivo_cambio,
            creado_por="Sistema (actualización de catálogo)",
        )
        logger.info(
            "RN-11: perfil %s re-versionado a v%s por %s",
            perfil.id, perfil.version_actual, motivo_cambio,
        )


@receiver(post_save, sender=CatalogoPeligro)
def on_catalogo_peligro_saved(sender, instance, created, **kwargs):
    if created:
        return  # solo re-versiona por EDICIÓN de un catálogo ya en uso, no por su creación
    perfiles = PerfilCargo.objects.filter(peligros__catalogo_peligro=instance, activo=True)
    if not perfiles.exists():
        return
    transaction.on_commit(
        lambda: _reversionar_perfiles(
            perfiles,
            f"Actualización automática por cambio en catálogo de peligro '{instance.tipo}'",
        )
    )


@receiver(post_save, sender=CatalogoEPP)
def on_catalogo_epp_saved(sender, instance, created, **kwargs):
    if created:
        return
    perfiles = PerfilCargo.objects.filter(epps__catalogo_epp=instance, activo=True)
    if not perfiles.exists():
        return
    transaction.on_commit(
        lambda: _reversionar_perfiles(
            perfiles,
            f"Actualización automática por cambio en catálogo de EPP '{instance.nombre}'",
        )
    )


@receiver(m2m_changed, sender=CatalogoPeligro.epps_sugeridos.through)
def on_catalogo_peligro_epps_changed(sender, instance, action, **kwargs):
    """
    `instance` aquí es siempre un CatalogoPeligro (lado por el que se dispara
    la relación M2M en el proyecto). Cambiar sus EPP sugeridos altera la lista
    efectiva de EPP de cualquier PerfilCargo que use ese peligro.
    """
    if action not in ("post_add", "post_remove", "post_clear"):
        return
    perfiles = PerfilCargo.objects.filter(peligros__catalogo_peligro=instance, activo=True)
    if not perfiles.exists():
        return
    transaction.on_commit(
        lambda: _reversionar_perfiles(
            perfiles,
            f"Actualización automática por cambio en EPP sugeridos del peligro '{instance.tipo}'",
        )
    )
