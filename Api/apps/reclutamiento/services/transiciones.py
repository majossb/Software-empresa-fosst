"""
Tabla de Transiciones Declarativa y Validadores de Reglas de Negocio (RN-R01 a RN-R09).
Aplica Open/Closed: Agregar un estado nuevo o regla se realiza mediante configuración.
"""
from typing import Dict, List, Callable, Any, Optional
from apps.reclutamiento.models import Postulacion, ProcesoSeleccion


class ReclutamientoDomainError(Exception):
    """Excepción base para errores de reglas de negocio en Reclutamiento."""
    pass


class TransicionInvalidaError(ReclutamientoDomainError):
    """RN-R01: La transición solicitada no está permitida por la máquina de estados."""
    pass


class RequisitoIncumplidoError(ReclutamientoDomainError):
    """RN-R02: No se cumplen los requisitos obligatorios del perfil de cargo o proceso."""
    pass


class EtapaObligatoriaFaltanteError(ReclutamientoDomainError):
    """RN-R02/RN-R03: Falta superar una etapa obligatoria configurada para el proceso."""
    pass


class MotivoRequeridoError(ReclutamientoDomainError):
    """RN-R04: Todo cierre de postulación exige un motivo explícito."""
    pass


class CuposAgotadosError(ReclutamientoDomainError):
    """RN-R06: La vacante ya no cuenta con cupos disponibles para selección."""
    pass


class ExcepcionNoAutorizadaError(ReclutamientoDomainError):
    """RN-R09: Una transición por excepción requiere justificación y usuario autorizador."""
    pass


# ── TABLA DE TRANSICIONES DECLARATIVA (Open/Closed) ───────────────────────────
ESTADO_TRANSICIONES: Dict[str, List[str]] = {
    Postulacion.Estado.POSTULADO: [
        Postulacion.Estado.EN_REVISION,
        Postulacion.Estado.NO_SELECCIONADO,
        Postulacion.Estado.RETIRO_CANDIDATURA,
    ],
    Postulacion.Estado.EN_REVISION: [
        Postulacion.Estado.PRESELECCIONADO,
        Postulacion.Estado.NO_SELECCIONADO,
        Postulacion.Estado.RETIRO_CANDIDATURA,
        Postulacion.Estado.NO_CONTINUO,
    ],
    Postulacion.Estado.PRESELECCIONADO: [
        Postulacion.Estado.EN_ENTREVISTA,
        Postulacion.Estado.EN_EVALUACION,
        Postulacion.Estado.EN_VALIDACION,
        Postulacion.Estado.SELECCIONADO,
        Postulacion.Estado.NO_SELECCIONADO,
        Postulacion.Estado.RETIRO_CANDIDATURA,
        Postulacion.Estado.NO_CONTINUO,
    ],
    Postulacion.Estado.EN_ENTREVISTA: [
        Postulacion.Estado.EN_EVALUACION,
        Postulacion.Estado.EN_VALIDACION,
        Postulacion.Estado.SELECCIONADO,
        Postulacion.Estado.NO_SELECCIONADO,
        Postulacion.Estado.RETIRO_CANDIDATURA,
        Postulacion.Estado.NO_CONTINUO,
    ],
    Postulacion.Estado.EN_EVALUACION: [
        Postulacion.Estado.EN_ENTREVISTA,
        Postulacion.Estado.EN_VALIDACION,
        Postulacion.Estado.SELECCIONADO,
        Postulacion.Estado.NO_SELECCIONADO,
        Postulacion.Estado.RETIRO_CANDIDATURA,
        Postulacion.Estado.NO_CONTINUO,
    ],
    Postulacion.Estado.EN_VALIDACION: [
        Postulacion.Estado.SELECCIONADO,
        Postulacion.Estado.NO_SELECCIONADO,
        Postulacion.Estado.RETIRO_CANDIDATURA,
        Postulacion.Estado.NO_CONTINUO,
    ],
    Postulacion.Estado.SELECCIONADO: [],  # Estado final de éxito
    Postulacion.Estado.NO_SELECCIONADO: [
        Postulacion.Estado.EN_REVISION,  # RN-R07: Reapertura excepcional
    ],
    Postulacion.Estado.RETIRO_CANDIDATURA: [],
    Postulacion.Estado.NO_CONTINUO: [],
}


# ── VALIDACIONES ESPECÍFICAS DE ENTRADA POR TRANSICIÓN ────────────────────────

def validar_preseleccion(postulacion: Postulacion, contexto: Optional[Dict[str, Any]] = None):
    """
    RN-R02: No se puede preseleccionar si existen requisitos obligatorios incumplidos.
    """
    contexto = contexto or {}
    calificacion_requisitos = contexto.get("calificacion_requisitos") or postulacion.calificacion_requisitos or {}
    requisitos_obligatorios = postulacion.proceso_seleccion.requisitos_obligatorios or []

    faltantes = []
    for req in requisitos_obligatorios:
        req_id = req.get("id") or req.get("nombre") or str(req)
        nombre_req = req.get("nombre") or str(req)
        cumplido = calificacion_requisitos.get(req_id, {}).get("cumple", False) if isinstance(calificacion_requisitos.get(req_id), dict) else calificacion_requisitos.get(req_id, False)
        if not cumplido:
            faltantes.append(nombre_req)

    if faltantes and not contexto.get("es_excepcion"):
        raise RequisitoIncumplidoError(
            f"No se puede preseleccionar al candidato: Incumple los siguientes requisitos obligatorios: {', '.join(faltantes)}."
        )


def validar_seleccion_final(postulacion: Postulacion, contexto: Optional[Dict[str, Any]] = None):
    """
    RN-R02/RN-R03/RN-R06: Valida etapas obligatorias configuradas en el proceso y cupos disponibles.
    """
    contexto = contexto or {}
    proceso = postulacion.proceso_seleccion
    vacante = proceso.vacante

    # 1. Verificar cupos disponibles
    if vacante.esta_cubierta and not contexto.get("es_excepcion"):
        raise CuposAgotadosError(
            f"La vacante '{vacante.titulo}' ya completó sus {vacante.numero_cupos} cupos disponibles."
        )

    # 2. Verificar etapas obligatorias configuradas para este proceso (RN-R03)
    etapas_superadas = list(postulacion.etapas_completadas or [])
    if contexto.get("etapas_completadas"):
        etapas_superadas.extend(contexto.get("etapas_completadas"))
    etapas_superadas = set(etapas_superadas)

    etapas_faltantes = []
    if proceso.requiere_entrevista and "entrevista" not in etapas_superadas:
        etapas_faltantes.append("Entrevista")
    if proceso.requiere_evaluacion and "evaluacion" not in etapas_superadas:
        etapas_faltantes.append("Evaluación Técnica / Psicotécnica")
    if proceso.requiere_validacion_documental and "validacion_documental" not in etapas_superadas:
        etapas_faltantes.append("Validación Documental")

    if etapas_faltantes and not contexto.get("es_excepcion"):
        raise EtapaObligatoriaFaltanteError(
            f"No se puede seleccionar al candidato: Faltan las siguientes etapas obligatorias del proceso: {', '.join(etapas_faltantes)}."
        )


def validar_cierre(postulacion: Postulacion, contexto: Optional[Dict[str, Any]] = None):
    """
    RN-R04/RN-R05: Todo cierre exige un motivo obligatorio y valida la naturaleza del retiro.
    """
    contexto = contexto or {}
    motivo = (contexto.get("motivo") or contexto.get("motivo_cierre") or "").strip()
    if not motivo:
        raise MotivoRequeridoError(
            "El motivo de cierre es obligatorio para registrar la no selección, retiro o abandono."
        )


VALIDADORES_DESTINO: Dict[str, Callable[[Postulacion, Optional[Dict[str, Any]]], None]] = {
    Postulacion.Estado.PRESELECCIONADO: validar_preseleccion,
    Postulacion.Estado.SELECCIONADO: validar_seleccion_final,
    Postulacion.Estado.NO_SELECCIONADO: validar_cierre,
    Postulacion.Estado.RETIRO_CANDIDATURA: validar_cierre,
    Postulacion.Estado.NO_CONTINUO: validar_cierre,
}
