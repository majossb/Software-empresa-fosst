"""
Servicio del Motor Genérico de Alertas (§5.2) — ampliado Fase 5.

Evalúa las reglas activas de vencimiento contra los modelos de datos,
formatea los mensajes y genera notificaciones con deduplicación diaria.

Handlers disponibles:
  exacta             — fecha == hoy + N días  (comportamiento original)
  vencido_rango      — fecha < hoy (certificados ya vencidos con curso obligatorio)
  sin_registrar      — trabajador sin ningún RegistroFormacion del curso obligatorio
  evaluacion_pendiente — trabajador con brecha de competencia o sin evaluación
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q

from apps.accounts.models import Usuario
from apps.calendario.models import Notificacion
from .models import ReglaAlerta

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _inicio_dia():
    return timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)


def _crear_notificacion(empresa_obj, trabajador, regla, mensaje, metadatos=None):
    """
    Crea una Notificacion para cada usuario destinatario con deduplicación diaria.
    Devuelve la cantidad de notificaciones nuevas creadas.
    """
    roles_upper = [r.upper() for r in (regla.roles_destinatarios or ["RESPONSABLE"])]
    destinatarios = Usuario.objects.filter(
        empresa=empresa_obj,
        rol__in=roles_upper,
        activo=True,
    )

    inicio = _inicio_dia()
    creadas = 0
    for usuario in destinatarios:
        ya_existe = Notificacion.objects.filter(
            empresa=empresa_obj,
            usuario=usuario,
            mensaje=mensaje,
            created_at__gte=inicio,
        ).exists()
        if not ya_existe:
            Notificacion.objects.create(
                empresa=empresa_obj,
                usuario=usuario,
                tipo=Notificacion.Tipo.ALERTA,
                nivel=regla.nivel_criticidad,
                mensaje=mensaje,
                metadatos=metadatos,
            )
            creadas += 1
    return creadas


def _render_mensaje(template, **kwargs):
    try:
        return template.format(**kwargs)
    except Exception:
        return template


# ---------------------------------------------------------------------------
# Handler: exacta  (comportamiento original + RegistroFormacion)
# ---------------------------------------------------------------------------

def _handler_exacta(regla, empresa, fecha_referencia, model_cls):
    """
    Dispara alertas cuando campo_fecha == fecha_referencia + dias_anticipacion.
    """
    target_date = fecha_referencia + timedelta(days=regla.dias_anticipacion)

    filter_kwargs = {regla.campo_fecha: target_date}

    if hasattr(model_cls, "activo"):
        filter_kwargs["activo"] = True
    if hasattr(model_cls, "deleted_at"):
        filter_kwargs["deleted_at__isnull"] = True

    tiene_trabajador_fk = regla.modelo_origen not in ("Trabajador",)
    if tiene_trabajador_fk:
        filter_kwargs["trabajador__activo"] = True
        filter_kwargs["trabajador__deleted_at__isnull"] = True

    if empresa:
        if hasattr(model_cls, "empresa"):
            filter_kwargs["empresa"] = empresa
        elif tiene_trabajador_fk:
            filter_kwargs["trabajador__empresa"] = empresa

    try:
        records = model_cls.objects.filter(**filter_kwargs).select_related(
            "trabajador__empresa" if tiene_trabajador_fk else "empresa"
        )
    except Exception as e:
        logger.error("exacta — error consultando regla %s: %s", regla.codigo, e)
        return 0

    total = 0
    for item in records:
        if tiene_trabajador_fk:
            trabajador = item.trabajador
            empresa_obj = item.trabajador.empresa
        else:
            trabajador = item
            empresa_obj = item.empresa

        # Contexto extra para placeholders {curso}, {competencia}, {tipo}
        curso_nombre = ""
        metadatos = {"tipo_alerta": regla.codigo, "trabajador_id": str(trabajador.id)}

        if regla.modelo_origen == "RegistroFormacion":
            curso_nombre = item.curso.nombre if hasattr(item, "curso") and item.curso else ""
            metadatos["curso_id"] = str(item.curso_id)
            metadatos["registro_id"] = str(item.id)
            metadatos["cargo"] = getattr(trabajador, "cargo", "") or ""

        mensaje = _render_mensaje(
            regla.mensaje_template,
            trabajador=trabajador.nombre,
            documento=getattr(trabajador, "documento", ""),
            fecha=target_date.strftime("%Y-%m-%d"),
            dias=regla.dias_anticipacion,
            cargo=getattr(trabajador, "cargo", "") or "No especificado",
            tipo=getattr(item, "tipo", getattr(item, "categoria", "")),
            curso=curso_nombre,
            competencia="",
        )
        total += _crear_notificacion(empresa_obj, trabajador, regla, mensaje, metadatos)
    return total


# ---------------------------------------------------------------------------
# Handler: vencido_rango  (cursos ya vencidos con curso obligatorio en cargo)
# ---------------------------------------------------------------------------

def _handler_vencido_rango(regla, empresa, fecha_referencia):
    """
    Alerta cuando fecha_vencimiento < hoy y el curso es obligatorio para el cargo.
    """
    from apps.formacion.models import RegistroFormacion, CargoRequisitoFormacion

    qs = RegistroFormacion.objects.filter(
        fecha_vencimiento__lt=fecha_referencia,
        fecha_vencimiento__isnull=False,
        trabajador__activo=True,
        trabajador__deleted_at__isnull=True,
    ).select_related("trabajador__empresa", "curso")

    if empresa:
        qs = qs.filter(trabajador__empresa=empresa)

    # Solo alertar cursos que son obligatorios en el cargo del trabajador
    total = 0
    for registro in qs:
        trabajador = registro.trabajador
        empresa_obj = trabajador.empresa

        # Verificar si este curso es obligatorio en el perfil del cargo actual
        if not trabajador.perfil_cargo_id:
            continue
        es_obligatorio = CargoRequisitoFormacion.objects.filter(
            perfil_cargo_id=trabajador.perfil_cargo_id,
            curso=registro.curso,
            obligatorio=True,
        ).exists()
        if not es_obligatorio:
            continue

        metadatos = {
            "tipo_alerta": regla.codigo,
            "trabajador_id": str(trabajador.id),
            "curso_id": str(registro.curso_id),
            "registro_id": str(registro.id),
            "cargo": getattr(trabajador, "cargo", "") or "",
        }
        mensaje = _render_mensaje(
            regla.mensaje_template,
            trabajador=trabajador.nombre,
            documento=getattr(trabajador, "documento", ""),
            fecha=registro.fecha_vencimiento.strftime("%Y-%m-%d"),
            dias=0,
            cargo=getattr(trabajador, "cargo", "") or "No especificado",
            tipo="",
            curso=registro.curso.nombre,
            competencia="",
        )
        total += _crear_notificacion(empresa_obj, trabajador, regla, mensaje, metadatos)
    return total


# ---------------------------------------------------------------------------
# Handler: sin_registrar  (trabajador sin RegistroFormacion de curso obligatorio)
# ---------------------------------------------------------------------------

def _handler_sin_registrar(regla, empresa, fecha_referencia):
    """
    Alerta cuando un trabajador activo no tiene ningún RegistroFormacion
    para un curso que su cargo marca como obligatorio.
    """
    from apps.formacion.models import RegistroFormacion, CargoRequisitoFormacion
    from apps.capacitaciones.models import Trabajador

    # Cargos-requisito obligatorios
    requisitos_qs = CargoRequisitoFormacion.objects.filter(
        obligatorio=True,
    ).select_related("perfil_cargo", "curso")

    if empresa:
        requisitos_qs = requisitos_qs.filter(perfil_cargo__empresa=empresa)

    total = 0
    for req in requisitos_qs:
        # Trabajadores activos con ese cargo que NO tienen el curso registrado
        trabajadores_con_cargo = Trabajador.objects.filter(
            perfil_cargo=req.perfil_cargo,
            activo=True,
            deleted_at__isnull=True,
        )
        if empresa:
            trabajadores_con_cargo = trabajadores_con_cargo.filter(empresa=empresa)

        for trabajador in trabajadores_con_cargo:
            # Tiene al menos un registro vigente o histórico del curso
            tiene_registro = RegistroFormacion.objects.filter(
                trabajador=trabajador,
                curso=req.curso,
            ).exists()
            if tiene_registro:
                continue

            empresa_obj = trabajador.empresa
            metadatos = {
                "tipo_alerta": regla.codigo,
                "trabajador_id": str(trabajador.id),
                "curso_id": str(req.curso_id),
                "cargo": getattr(trabajador, "cargo", "") or "",
            }
            mensaje = _render_mensaje(
                regla.mensaje_template,
                trabajador=trabajador.nombre,
                documento=getattr(trabajador, "documento", ""),
                fecha=fecha_referencia.strftime("%Y-%m-%d"),
                dias=0,
                cargo=getattr(trabajador, "cargo", "") or "No especificado",
                tipo="",
                curso=req.curso.nombre,
                competencia="",
            )
            total += _crear_notificacion(empresa_obj, trabajador, regla, mensaje, metadatos)
    return total


# ---------------------------------------------------------------------------
# Handler: evaluacion_pendiente  (competencia sin evaluación o con brecha)
# ---------------------------------------------------------------------------

def _handler_evaluacion_pendiente(regla, empresa, fecha_referencia):
    """
    Alerta cuando un trabajador tiene una competencia requerida por su cargo
    sin ninguna evaluación registrada, o la última evaluación muestra brecha.
    """
    from apps.perfilcargo.models import CargoCompetencia
    from apps.formacion.models import EvaluacionCompetencia
    from apps.capacitaciones.models import Trabajador

    cargos_competencia_qs = CargoCompetencia.objects.select_related("perfil_cargo")
    if empresa:
        cargos_competencia_qs = cargos_competencia_qs.filter(perfil_cargo__empresa=empresa)

    total = 0
    for cargo_comp in cargos_competencia_qs:
        trabajadores = Trabajador.objects.filter(
            perfil_cargo=cargo_comp.perfil_cargo,
            activo=True,
            deleted_at__isnull=True,
        )
        if empresa:
            trabajadores = trabajadores.filter(empresa=empresa)

        for trabajador in trabajadores:
            # Última evaluación para esta competencia
            ultima = (
                EvaluacionCompetencia.objects.filter(
                    trabajador=trabajador,
                    cargo_competencia=cargo_comp,
                )
                .order_by("-fecha_evaluacion", "-created_at")
                .first()
            )
            tiene_brecha = False
            if ultima is None:
                tiene_brecha = True
            elif ultima.brecha_calculada > 0:
                tiene_brecha = True

            if not tiene_brecha:
                continue

            empresa_obj = trabajador.empresa
            comp_nombre = getattr(cargo_comp, "nombre", str(cargo_comp))
            metadatos = {
                "tipo_alerta": regla.codigo,
                "trabajador_id": str(trabajador.id),
                "cargo": getattr(trabajador, "cargo", "") or "",
                "cargo_competencia_id": str(cargo_comp.id),
            }
            mensaje = _render_mensaje(
                regla.mensaje_template,
                trabajador=trabajador.nombre,
                documento=getattr(trabajador, "documento", ""),
                fecha=fecha_referencia.strftime("%Y-%m-%d"),
                dias=0,
                cargo=getattr(trabajador, "cargo", "") or "No especificado",
                tipo="",
                curso="",
                competencia=comp_nombre,
            )
            total += _crear_notificacion(empresa_obj, trabajador, regla, mensaje, metadatos)
    return total


# ---------------------------------------------------------------------------
# Función pública principal
# ---------------------------------------------------------------------------

def evaluar_reglas_alertas(empresa=None, fecha_referencia=None) -> int:
    """
    Recorre todas las ReglaAlerta activas y genera Notificaciones
    con deduplicación (no enviar la misma alerta el mismo día).

    RN-14: Las alertas quedan registradas en Notificacion (fuente única).

    Args:
        empresa: Empresa opcional para filtrar evaluación
        fecha_referencia: date opcional (por defecto hoy)

    Returns:
        total_notificaciones_creadas (int)
    """
    if fecha_referencia is None:
        fecha_referencia = timezone.localdate()

    from apps.capacitaciones.models import Trabajador, AfiliacionTrabajador
    from apps.gestion_humana.models import ExamenMedicoOcupacional, LicenciaConduccion
    from apps.formacion.models import RegistroFormacion

    MODEL_MAP = {
        "Trabajador": Trabajador,
        "ExamenMedicoOcupacional": ExamenMedicoOcupacional,
        "LicenciaConduccion": LicenciaConduccion,
        "AfiliacionTrabajador": AfiliacionTrabajador,
        "RegistroFormacion": RegistroFormacion,
    }

    reglas_qs = ReglaAlerta.objects.filter(activa=True)
    if empresa:
        reglas_qs = reglas_qs.filter(Q(empresa=empresa) | Q(empresa__isnull=True))

    notificaciones_creadas = 0

    for regla in reglas_qs:
        handler = regla.tipo_handler

        try:
            if handler == ReglaAlerta.TipoHandler.VENCIDO_RANGO:
                notificaciones_creadas += _handler_vencido_rango(regla, empresa, fecha_referencia)

            elif handler == ReglaAlerta.TipoHandler.SIN_REGISTRAR:
                notificaciones_creadas += _handler_sin_registrar(regla, empresa, fecha_referencia)

            elif handler == ReglaAlerta.TipoHandler.EVALUACION_PENDIENTE:
                notificaciones_creadas += _handler_evaluacion_pendiente(regla, empresa, fecha_referencia)

            else:
                # handler == "exacta" (por defecto)
                model_cls = MODEL_MAP.get(regla.modelo_origen)
                if not model_cls:
                    logger.warning(
                        "Modelo origen '%s' no encontrado en MODEL_MAP (regla %s)",
                        regla.modelo_origen, regla.codigo,
                    )
                    continue
                notificaciones_creadas += _handler_exacta(regla, empresa, fecha_referencia, model_cls)

        except Exception as e:
            logger.error("Error evaluando regla %s: %s", regla.codigo, e, exc_info=True)

    logger.info(
        "Motor de alertas: %d notificaciones generadas para fecha %s",
        notificaciones_creadas, fecha_referencia,
    )
    return notificaciones_creadas
