"""
Servicios de Gestión Humana.

Motor determinista de cálculo de estado contractual con jerarquía de precedencia
cuando existen novedades laborales simultáneas o solapadas.
"""
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

# Jerarquía estricta de precedencia para novedades activas simultáneas (§5)
# En caso de solapamiento (ej. incapacidad durante vacaciones), la incapacidad prevalece.
JERARQUIA_PRECEDENCIA_NOVEDADES = [
    ("incapacidad", "incapacidad"),       # Prioridad 1: Incapacidad médica (suspende vacaciones/contrato)
    ("suspension", "suspendido"),         # Prioridad 2: Suspensión disciplinaria/contractual
    ("licencia", "licencia"),             # Prioridad 3: Licencias (remuneradas, no remuneradas, maternidad)
    ("vacaciones", "vacaciones"),         # Prioridad 4: Vacaciones
    ("periodo_prueba", "periodo_prueba"), # Prioridad 5: Novedad de periodo de prueba
]


def recalcular_estado_contractual(trabajador, fecha_referencia=None) -> str:
    """
    Recalcula determinísticamente el estado contractual de un trabajador
    evaluando novedades laborales vigentes en la fecha de referencia.

    RN-13: `estado_contractual` es un campo derivado, nunca editable a mano.

    Args:
        trabajador: instancia de capacitaciones.Trabajador
        fecha_referencia: date (por defecto hoy en zona horaria local)

    Returns:
        nuevo_estado (str): el estado contractual resultante asignado y guardado
    """
    if fecha_referencia is None:
        fecha_referencia = timezone.localdate()

    from .models import NovedadLaboral

    # 1. Validación de retiro definitivo
    if not trabajador.activo or (trabajador.fecha_retiro and trabajador.fecha_retiro <= fecha_referencia):
        nuevo_estado = "retirado"
        if trabajador.estado_contractual != nuevo_estado:
            trabajador.estado_contractual = nuevo_estado
            trabajador.save(update_fields=["estado_contractual"])
            logger.info("Trabajador %s (%s) estado_contractual recalculado a 'retirado'", trabajador.id, trabajador.nombre)
        return nuevo_estado

    # 2. Consultar todas las novedades vigentes para la fecha
    novedades_vigentes = NovedadLaboral.objects.filter(
        trabajador=trabajador,
        fecha_inicio__lte=fecha_referencia,
    ).exclude(
        fecha_fin__lt=fecha_referencia
    )

    tipos_activos = set(novedades_vigentes.values_list("tipo", flat=True))

    # 3. Aplicar jerarquía de precedencia
    nuevo_estado = None
    for tipo_novedad, estado_target in JERARQUIA_PRECEDENCIA_NOVEDADES:
        if tipo_novedad in tipos_activos:
            nuevo_estado = estado_target
            break

    # 4. Si no hay novedades vigentes, evaluar periodo de prueba del contrato o estado activo
    if nuevo_estado is None:
        if (
            trabajador.fecha_inicio_periodo_prueba
            and trabajador.fecha_fin_periodo_prueba
            and trabajador.fecha_inicio_periodo_prueba <= fecha_referencia <= trabajador.fecha_fin_periodo_prueba
        ):
            nuevo_estado = "periodo_prueba"
        else:
            nuevo_estado = "activo"

    if trabajador.estado_contractual != nuevo_estado:
        anterior = trabajador.estado_contractual
        trabajador.estado_contractual = nuevo_estado
        trabajador.save(update_fields=["estado_contractual"])
        logger.info(
            "Trabajador %s (%s) estado_contractual cambió de '%s' a '%s' (novedades activas: %s)",
            trabajador.id, trabajador.nombre, anterior, nuevo_estado, list(tipos_activos)
        )

    return nuevo_estado
