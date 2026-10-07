"""
Servicios de dominio para Postulaciones y Máquina de Estados — FOSST V.I.D.A.
Implementa RN-R01 a RN-R09 con transacciones atómicas y trazabilidad inmutable.
"""
from typing import Optional, Dict, Any, List
from django.db import transaction
from django.utils import timezone
from apps.reclutamiento.models import Postulacion, PostulacionEvento, Vacante
from apps.reclutamiento.services.transiciones import (
    ESTADO_TRANSICIONES,
    VALIDADORES_DESTINO,
    TransicionInvalidaError,
    ExcepcionNoAutorizadaError,
)


@transaction.atomic
def transicionar_postulacion(
    postulacion: Postulacion,
    nuevo_estado: str,
    usuario=None,
    motivo: str = "",
    contexto: Optional[Dict[str, Any]] = None,
    es_excepcion: bool = False,
    justificacion_excepcion: str = "",
) -> Postulacion:
    """
    RN-R01: Ejecuta la transición de estado de una postulación de forma determinista.
    RN-R08: Genera un PostulacionEvento inmutable con la trazabilidad completa.
    RN-R09: Si la transición es una excepción autorizada, exige justificación explícita.
    """
    contexto = contexto or {}
    estado_anterior = postulacion.estado

    # 1. Validar si la transición está permitida en la tabla declarativa
    estados_permitidos = ESTADO_TRANSICIONES.get(estado_anterior, [])
    if nuevo_estado not in estados_permitidos:
        raise TransicionInvalidaError(
            f"Transición inválida: No se puede pasar de '{postulacion.get_estado_display()}' a '{nuevo_estado}'."
        )

    # 2. Manejo de excepciones
    if es_excepcion:
        if not justificacion_excepcion.strip():
            raise ExcepcionNoAutorizadaError(
                "RN-R09: Las transiciones por excepción exigen una justificación obligatoria."
            )
        contexto["es_excepcion"] = True
        contexto["justificacion_excepcion"] = justificacion_excepcion

    contexto["motivo"] = motivo

    # 3. Ejecutar validador de condiciones de entrada si existe
    validador = VALIDADORES_DESTINO.get(nuevo_estado)
    if validador:
        validador(postulacion, contexto)

    # 4. Actualizar estado y campos de contexto en la Postulación
    postulacion.estado = nuevo_estado
    if "calificacion_requisitos" in contexto:
        postulacion.calificacion_requisitos = contexto["calificacion_requisitos"]
    if "puntuacion_general" in contexto:
        postulacion.puntuacion_general = contexto["puntuacion_general"]
    if "etapas_completadas" in contexto:
        etapas_actuales = set(postulacion.etapas_completadas or [])
        etapas_actuales.update(contexto["etapas_completadas"])
        postulacion.etapas_completadas = list(etapas_actuales)

    if nuevo_estado in [
        Postulacion.Estado.NO_SELECCIONADO,
        Postulacion.Estado.RETIRO_CANDIDATURA,
        Postulacion.Estado.NO_CONTINUO,
    ]:
        postulacion.motivo_cierre = motivo

    if es_excepcion:
        postulacion.es_excepcion = True
        postulacion.justificacion_excepcion = justificacion_excepcion
        postulacion.autorizado_por = usuario

    postulacion.save()

    # 5. Registrar el Evento Inmutable de Trazabilidad (RN-R08)
    tipo_evento = PostulacionEvento.TipoEvento.CAMBIO_ESTADO
    if nuevo_estado == Postulacion.Estado.SELECCIONADO:
        tipo_evento = PostulacionEvento.TipoEvento.DECISION_SELECCION
    elif nuevo_estado in [Postulacion.Estado.NO_SELECCIONADO, Postulacion.Estado.RETIRO_CANDIDATURA, Postulacion.Estado.NO_CONTINUO]:
        tipo_evento = PostulacionEvento.TipoEvento.CIERRE_POSTULACION

    PostulacionEvento.objects.create(
        postulacion=postulacion,
        tipo_evento=tipo_evento,
        estado_anterior=estado_anterior,
        estado_nuevo=nuevo_estado,
        descripcion=f"Transición a {postulacion.get_estado_display()}",
        motivo=motivo,
        es_excepcion=es_excepcion,
        justificacion_excepcion=justificacion_excepcion,
        datos_capturados=contexto,
        usuario=usuario,
    )

    return postulacion


@transaction.atomic
def registrar_postulacion(
    candidato,
    proceso_seleccion,
    usuario=None,
    fuente=None,
) -> Postulacion:
    """
    Crea una nueva postulación en estado inicial POSTULADO con su evento de auditoría.
    """
    postulacion = Postulacion.objects.create(
        empresa=proceso_seleccion.empresa,
        candidato=candidato,
        proceso_seleccion=proceso_seleccion,
        estado=Postulacion.Estado.POSTULADO,
    )

    PostulacionEvento.objects.create(
        postulacion=postulacion,
        tipo_evento=PostulacionEvento.TipoEvento.POSTULACION_REGISTRADA,
        estado_anterior="",
        estado_nuevo=Postulacion.Estado.POSTULADO,
        descripcion=f"Postulación registrada en {proceso_seleccion.vacante.titulo}",
        motivo="Registro inicial de postulación",
        usuario=usuario,
    )

    return postulacion


@transaction.atomic
def preseleccionar_candidato(
    postulacion: Postulacion,
    calificacion_requisitos: Dict[str, Any],
    usuario=None,
    puntuacion: Optional[float] = None,
    es_excepcion: bool = False,
    justificacion_excepcion: str = "",
) -> Postulacion:
    """
    RN-R02: Valida requisitos obligatorios antes de avanzar a PRESELECCIONADO.
    """
    # Si estaba en POSTULADO, pasa primero a EN_REVISION y luego a PRESELECCIONADO
    if postulacion.estado == Postulacion.Estado.POSTULADO:
        transicionar_postulacion(
            postulacion=postulacion,
            nuevo_estado=Postulacion.Estado.EN_REVISION,
            usuario=usuario,
            motivo="Inicio de revisión de requisitos",
        )

    contexto = {
        "calificacion_requisitos": calificacion_requisitos,
    }
    if puntuacion is not None:
        contexto["puntuacion_general"] = puntuacion

    return transicionar_postulacion(
        postulacion=postulacion,
        nuevo_estado=Postulacion.Estado.PRESELECCIONADO,
        usuario=usuario,
        motivo="Requisitos de perfil de cargo verificados satisfactoriamente",
        contexto=contexto,
        es_excepcion=es_excepcion,
        justificacion_excepcion=justificacion_excepcion,
    )


@transaction.atomic
def seleccionar_candidato(
    postulacion: Postulacion,
    usuario=None,
    notas_finales: str = "",
    es_excepcion: bool = False,
    justificacion_excepcion: str = "",
) -> Postulacion:
    """
    RN-R02 / RN-R03 / RN-R06: Decisión final de selección.
    Al completar los cupos de la vacante, cierra automáticamente las demás candidaturas activas.
    """
    proceso = postulacion.proceso_seleccion
    vacante = proceso.vacante

    # 1. Transicionar al candidato a SELECCIONADO
    transicionar_postulacion(
        postulacion=postulacion,
        nuevo_estado=Postulacion.Estado.SELECCIONADO,
        usuario=usuario,
        motivo=notas_finales or "Candidato seleccionado para el cargo",
        es_excepcion=es_excepcion,
        justificacion_excepcion=justificacion_excepcion,
    )

    # 2. Incrementar cupos cubiertos en la Vacante
    vacante.numero_seleccionados += 1
    if vacante.numero_seleccionados >= vacante.numero_cupos:
        vacante.estado = Vacante.Estado.CUBIERTA
        vacante.fecha_cierre_real = timezone.now().date()
    vacante.save()

    # 3. RN-R06: Si se cubrieron los cupos, cerrar las demás postulaciones activas
    if vacante.esta_cubierta:
        otras_activas = Postulacion.objects.filter(
            proceso_seleccion=proceso,
        ).exclude(id=postulacion.id).filter(
            estado__in=[
                Postulacion.Estado.POSTULADO,
                Postulacion.Estado.EN_REVISION,
                Postulacion.Estado.PRESELECCIONADO,
                Postulacion.Estado.EN_ENTREVISTA,
                Postulacion.Estado.EN_EVALUACION,
                Postulacion.Estado.EN_VALIDACION,
            ]
        )

        for otra in otras_activas:
            transicionar_postulacion(
                postulacion=otra,
                nuevo_estado=Postulacion.Estado.NO_SELECCIONADO,
                usuario=usuario,
                motivo=f"Vacante cubierta — Se completaron los {vacante.numero_cupos} cupo(s) disponibles para este proceso.",
                contexto={"cierre_automatico_por_cupos": True},
            )

    return postulacion


@transaction.atomic
def cerrar_postulacion(
    postulacion: Postulacion,
    nuevo_estado: str,
    motivo: str,
    usuario=None,
    datos_adicionales: Optional[Dict[str, Any]] = None,
) -> Postulacion:
    """
    RN-R04 / RN-R05: Cierra una postulación por no selección, retiro o abandono con motivo obligatorio.
    """
    if nuevo_estado not in [
        Postulacion.Estado.NO_SELECCIONADO,
        Postulacion.Estado.RETIRO_CANDIDATURA,
        Postulacion.Estado.NO_CONTINUO,
    ]:
        raise TransicionInvalidaError(
            f"'{nuevo_estado}' no es un estado válido de cierre."
        )

    return transicionar_postulacion(
        postulacion=postulacion,
        nuevo_estado=nuevo_estado,
        usuario=usuario,
        motivo=motivo,
        contexto=datos_adicionales or {},
    )


@transaction.atomic
def reabrir_postulacion_excepcional(
    postulacion: Postulacion,
    justificacion: str,
    usuario,
) -> Postulacion:
    """
    RN-R07 / RN-R09: Reapertura excepcional de una postulación cerrada.
    Se registra como un nuevo evento sobre el histórico existente, sin sobreescribir.
    """
    if not justificacion.strip():
        raise ExcepcionNoAutorizadaError(
            "La reapertura excepcional exige una justificación detallada."
        )

    return transicionar_postulacion(
        postulacion=postulacion,
        nuevo_estado=Postulacion.Estado.EN_REVISION,
        usuario=usuario,
        motivo=f"Reapertura excepcional: {justificacion}",
        es_excepcion=True,
        justificacion_excepcion=justificacion,
    )
