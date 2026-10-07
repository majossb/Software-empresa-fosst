"""
HBSEO — Servicio central de registro y vinculación de brechas.

Este es EL punto de entrada único para que cualquier módulo registre una brecha.
Garantiza:
  - RN-16: toda brecha tiene al menos un BrechaOrigen con referencia trazable
  - Deduplicación: mismo trabajador + misma condición activa → vincula, no duplica
  - Generación automática de descripción/interpretación via IA (apps.ia.service)
  - Creación automática de BrechaEvento de detección

Uso desde otro módulo:
    from apps.hbseo.services import registrar_o_vincular_brecha

    brecha = registrar_o_vincular_brecha(
        empresa=empresa,
        modulo_origen="michc",
        clasificacion="restriccion",
        referencia_obj=evaluacion_habilitacion,  # cualquier modelo Django
        descripcion_base="Trabajador no habilitado: falta examen médico vigente",
        trabajador=trabajador,  # opcional
        detectado_por="Sistema (MICHC)",
    )
"""
import logging

from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from .models import Brecha, BrechaOrigen, BrechaEvento

logger = logging.getLogger(__name__)


def registrar_o_vincular_brecha(
    empresa,
    modulo_origen: str,
    clasificacion: str,
    referencia_obj,
    descripcion_base: str,
    trabajador=None,
    detectado_por: str = "sistema",
    sede=None,
    proceso=None,
    area: str = "",
) -> Brecha:
    """
    Registra una brecha nueva o vincula un origen adicional a una brecha existente.

    Lógica de deduplicación (§7.2):
      - Si existe una brecha ABIERTA (estado != cerrada/subsanada) para el mismo
        trabajador + misma clasificación + mismo módulo de origen → vincula origen adicional
      - Si no existe → crea brecha nueva con primer BrechaOrigen

    Args:
        empresa: instancia de Empresa
        modulo_origen: uno de BrechaOrigen.ModuloOrigen choices
        clasificacion: uno de Brecha.Clasificacion choices
        referencia_obj: modelo Django que origina la brecha (para GenericFK)
        descripcion_base: descripción textual de la condición detectada
        trabajador: instancia de Trabajador (opcional, para deduplicación y filtrado)
        detectado_por: texto identificando quién/qué detectó la brecha
        sede: instancia de Sede (opcional)
        proceso: instancia de Proceso (opcional)
        area: nombre del área (opcional)

    Returns:
        Brecha creada o existente a la que se vinculó el nuevo origen

    Raises:
        ValueError: si referencia_obj es None (RN-16)
    """
    # RN-16: no se permite crear brechas sin referencia trazable
    if referencia_obj is None:
        raise ValueError(
            "RN-16: Toda brecha requiere una referencia trazable (referencia_obj). "
            "No se permiten brechas sin origen."
        )

    ct = ContentType.objects.get_for_model(referencia_obj)
    obj_id = str(referencia_obj.pk)

    with transaction.atomic():
        # Verificar si ya existe un BrechaOrigen con exactamente la misma referencia
        origen_existente = BrechaOrigen.objects.filter(
            content_type=ct,
            object_id=obj_id,
        ).select_related("brecha").first()

        if origen_existente:
            # Ya existe un origen para este registro exacto — no duplicar
            logger.info(
                "HBSEO: referencia %s.%s ya vinculada a brecha %s, no se duplica",
                ct.model, obj_id, origen_existente.brecha.codigo,
            )
            return origen_existente.brecha

        # Buscar brecha abierta existente para deduplicación
        brecha_existente = _buscar_brecha_abierta(
            empresa, trabajador, clasificacion, modulo_origen,
        )

        if brecha_existente:
            # Vincular nuevo origen a brecha existente
            return _vincular_origen(
                brecha_existente, modulo_origen, ct, obj_id,
                descripcion_base, es_principal=False,
            )
        else:
            # Crear brecha nueva
            return _crear_brecha(
                empresa=empresa,
                modulo_origen=modulo_origen,
                clasificacion=clasificacion,
                ct=ct,
                obj_id=obj_id,
                descripcion_base=descripcion_base,
                trabajador=trabajador,
                detectado_por=detectado_por,
                sede=sede,
                proceso=proceso,
                area=area,
            )


def _buscar_brecha_abierta(empresa, trabajador, clasificacion, modulo_origen):
    """
    Busca una brecha abierta que coincida con la condición actual.

    Criterios de coincidencia:
      - Misma empresa
      - Mismo trabajador (si aplica)
      - Misma clasificación
      - Estado abierto (no cerrada ni subsanada)
      - Ya tiene al menos un origen del mismo módulo
    """
    estados_abiertos = [
        Brecha.Estado.DETECTADA,
        Brecha.Estado.EN_TRATAMIENTO,
        Brecha.Estado.CONTROLADA,
    ]

    qs = Brecha.objects.filter(
        empresa=empresa,
        clasificacion=clasificacion,
        estado__in=estados_abiertos,
    )

    if trabajador:
        qs = qs.filter(trabajador=trabajador)
    else:
        qs = qs.filter(trabajador__isnull=True)

    # Filtrar por módulo de origen existente
    qs = qs.filter(origenes__modulo_origen=modulo_origen)

    return qs.order_by("-fecha_deteccion").first()


def _crear_brecha(
    empresa, modulo_origen, clasificacion, ct, obj_id,
    descripcion_base, trabajador, detectado_por, sede, proceso, area,
):
    """Crea una brecha nueva con su primer BrechaOrigen y evento de detección."""
    brecha = Brecha.objects.create(
        empresa=empresa,
        sede=sede,
        proceso=proceso,
        area=area,
        trabajador=trabajador,
        clasificacion=clasificacion,
        estado=Brecha.Estado.DETECTADA,
        detectado_por=detectado_por,
    )

    # Primer origen (principal)
    BrechaOrigen.objects.create(
        brecha=brecha,
        modulo_origen=modulo_origen,
        content_type=ct,
        object_id=obj_id,
        es_origen_principal=True,
        descripcion=descripcion_base,
    )

    # Evento de detección
    BrechaEvento.objects.create(
        brecha=brecha,
        tipo_evento=BrechaEvento.TipoEvento.DETECCION,
        descripcion=(
            f"Brecha detectada automáticamente por {detectado_por} "
            f"desde el módulo de {modulo_origen}: {descripcion_base}"
        ),
    )

    # Generar descripción e interpretación via IA (asíncrono-conceptual:
    # se ejecuta en el mismo request porque el servicio IA tiene cache/mock rápido,
    # y los textos generados se necesitan inmediatamente para la respuesta).
    _generar_textos_ia(brecha, descripcion_base, modulo_origen, clasificacion, trabajador)

    logger.info(
        "HBSEO: Brecha %s creada — módulo=%s, clasificación=%s, trabajador=%s",
        brecha.codigo, modulo_origen, clasificacion,
        trabajador.nombre if trabajador else "N/A",
    )

    return brecha


def _vincular_origen(brecha, modulo_origen, ct, obj_id, descripcion, es_principal=False):
    """Vincula un BrechaOrigen adicional a una brecha existente."""
    BrechaOrigen.objects.create(
        brecha=brecha,
        modulo_origen=modulo_origen,
        content_type=ct,
        object_id=obj_id,
        es_origen_principal=es_principal,
        descripcion=descripcion,
    )

    # Evento de vinculación
    BrechaEvento.objects.create(
        brecha=brecha,
        tipo_evento=BrechaEvento.TipoEvento.ORIGEN_VINCULADO,
        descripcion=(
            f"Nuevo origen vinculado desde el módulo de {modulo_origen}: {descripcion}"
        ),
    )

    # Regenerar interpretación IA con contexto combinado de todos los orígenes
    _regenerar_interpretacion_combinada(brecha)

    logger.info(
        "HBSEO: Origen adicional vinculado a brecha %s — módulo=%s",
        brecha.codigo, modulo_origen,
    )

    return brecha


def _generar_textos_ia(brecha, descripcion_base, modulo_origen, clasificacion, trabajador):
    """Genera textos descriptivos via el servicio de IA."""
    try:
        from apps.ia.service import IAInterpretacionService

        contexto = {
            "modulo_origen": modulo_origen,
            "clasificacion": clasificacion,
            "descripcion_base": descripcion_base,
            "empresa_nombre": brecha.empresa.nombre,
        }
        if trabajador:
            contexto["trabajador_nombre"] = trabajador.nombre
            if hasattr(trabajador, "perfil_cargo") and trabajador.perfil_cargo:
                contexto["cargo_nombre"] = trabajador.perfil_cargo.nombre_cargo

        resultado = IAInterpretacionService.generar("descripcion_brecha", contexto)

        brecha.descripcion_automatica = resultado.get("descripcion_automatica", "")
        brecha.interpretacion_ia = resultado.get("interpretacion_ia", "")
        brecha.recomendacion_automatica = resultado.get("recomendacion_automatica", "")

        nivel = resultado.get("nivel_atencion", "")
        if nivel in dict(Brecha.NivelAtencion.choices):
            brecha.nivel_atencion = nivel

        brecha.save(update_fields=[
            "descripcion_automatica", "interpretacion_ia",
            "recomendacion_automatica", "nivel_atencion",
        ])

    except Exception as e:
        logger.error(
            "HBSEO: Error generando textos IA para brecha %s: %s",
            brecha.codigo, e,
        )
        # No falla la creación de la brecha si la IA falla — los textos quedan vacíos
        # y pueden regenerarse después.


def _regenerar_interpretacion_combinada(brecha):
    """Regenera la interpretación IA considerando todos los orígenes vinculados."""
    try:
        from apps.ia.service import IAInterpretacionService

        origenes = list(brecha.origenes.values("modulo_origen", "descripcion"))
        acciones = list(brecha.acciones.values_list("descripcion", flat=True))

        contexto = {
            "empresa_nombre": brecha.empresa.nombre,
            "brecha_codigo": brecha.codigo,
            "clasificacion": brecha.clasificacion,
            "estado_actual": brecha.estado,
            "origenes": origenes,
            "acciones_existentes": list(acciones),
        }

        resultado = IAInterpretacionService.generar(
            "recomendacion_brecha", contexto, forzar=True,
        )

        brecha.interpretacion_ia = resultado.get("interpretacion_ia", brecha.interpretacion_ia)
        brecha.recomendacion_automatica = resultado.get(
            "recomendacion_automatica", brecha.recomendacion_automatica,
        )

        nivel = resultado.get("nivel_atencion", "")
        if nivel in dict(Brecha.NivelAtencion.choices):
            brecha.nivel_atencion = nivel

        brecha.save(update_fields=[
            "interpretacion_ia", "recomendacion_automatica", "nivel_atencion",
        ])

    except Exception as e:
        logger.error(
            "HBSEO: Error regenerando interpretación combinada para brecha %s: %s",
            brecha.codigo, e,
        )
