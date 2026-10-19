"""
Servicios de registro y calificación de etapas de selección (Fase C) — FOSST V.I.D.A.
Orquesta Entrevistas, Evaluaciones y Validaciones Documentales vinculadas a Postulaciones.

Reglas:
- Entrevista desfavorable: cierra automáticamente como NO_SELECCIONADO y notifica.
- Evaluación: 0-60 crítico (cierra/no continúa), 61-80 alerta (continúa con refuerzo), 81-100 apto.
- Entrevista desfavorable bloquea cualquier avance posterior.
"""
from typing import Optional, Dict, Any
from django.db import transaction
from django.utils import timezone
from apps.reclutamiento.models import (
    Postulacion,
    PostulacionEvento,
    Entrevista,
    Evaluacion,
    ValidacionDocumental,
)
from apps.reclutamiento.services.postulacion import (
    transicionar_postulacion,
    cerrar_postulacion,
)
from apps.reclutamiento.services.transiciones import (
    EntrevistaDesfavorableError,
    ultima_entrevista_desfavorable,
)

# Umbrales de clasificación de evaluación
UMBRAL_CRITICO = 60.0
UMBRAL_APTO = 81.0


def clasificar_evaluacion(porcentaje: Optional[float]) -> str:
    """Clasifica el resultado de una evaluación: critico | alerta | apto."""
    pct = float(porcentaje or 0)
    if pct <= UMBRAL_CRITICO:
        return "critico"
    if pct < UMBRAL_APTO:
        return "alerta"
    return "apto"


def etiqueta_clasificacion(clasificacion: str) -> str:
    return {
        "critico": "No continúa en el proceso",
        "alerta": "Puede continuar (requiere refuerzo de competencia)",
        "apto": "Apto para el cargo",
    }.get(clasificacion, "Sin clasificar")


@transaction.atomic
def registrar_y_completar_entrevista(
    postulacion: Postulacion,
    tipo_entrevista: str,
    modalidad: str,
    fecha_programada,
    entrevistador=None,
    calificacion: Optional[float] = None,
    concepto: str = Entrevista.Concepto.FAVORABLE,
    observaciones: str = "",
    aspectos_evaluados: Optional[Dict[str, Any]] = None,
    enlace_reunion: str = "",
    lugar: str = "",
    usuario=None,
) -> Entrevista:
    """
    Registra una entrevista. Si el concepto es desfavorable, cierra la postulación
    como NO_SELECCIONADO (notificación automática) y bloquea el avance.
    """
    entrevista = Entrevista.objects.create(
        empresa=postulacion.empresa,
        postulacion=postulacion,
        tipo_entrevista=tipo_entrevista,
        modalidad=modalidad,
        fecha_programada=fecha_programada,
        entrevistador=entrevistador or usuario,
        estado=Entrevista.Estado.REALIZADA,
        calificacion=calificacion,
        concepto=concepto,
        observaciones=observaciones,
        aspectos_evaluados=aspectos_evaluados or {},
        enlace_reunion=enlace_reunion,
        lugar=lugar,
    )

    # El puntaje de la entrevista se refleja en la postulación
    if calificacion is not None:
        postulacion.puntuacion_general = calificacion

    es_favorable = concepto in [Entrevista.Concepto.FAVORABLE, Entrevista.Concepto.CON_RESERVAS]

    if not es_favorable:
        motivo = "Entrevista no aprobada: concepto desfavorable"
        if postulacion.es_activa:
            cerrar_postulacion(
                postulacion=postulacion,
                nuevo_estado=Postulacion.Estado.NO_SELECCIONADO,
                motivo=motivo,
                usuario=usuario,
                datos_adicionales={
                    "entrevista_id": str(entrevista.id),
                    "concepto": concepto,
                    "calificacion": float(calificacion) if calificacion is not None else None,
                },
            )
        elif calificacion is not None:
            postulacion.save(update_fields=["puntuacion_general"])
        return entrevista

    etapas = set(postulacion.etapas_completadas or [])
    etapas.add("entrevista")
    postulacion.etapas_completadas = list(etapas)

    if postulacion.estado == Postulacion.Estado.PRESELECCIONADO:
        transicionar_postulacion(
            postulacion=postulacion,
            nuevo_estado=Postulacion.Estado.EN_ENTREVISTA,
            usuario=usuario,
            motivo=f"Entrevista {entrevista.get_tipo_entrevista_display()} completada ({entrevista.get_concepto_display()})",
            contexto={
                "entrevista_id": str(entrevista.id),
                "calificacion": float(calificacion) if calificacion is not None else None,
            },
        )
    else:
        update_fields = ["etapas_completadas"]
        if calificacion is not None:
            update_fields.append("puntuacion_general")
        postulacion.save(update_fields=update_fields)
        PostulacionEvento.objects.create(
            postulacion=postulacion,
            tipo_evento=PostulacionEvento.TipoEvento.ENTREVISTA_REGISTRADA,
            estado_anterior=postulacion.estado,
            estado_nuevo=postulacion.estado,
            descripcion=f"Entrevista {entrevista.get_tipo_entrevista_display()} registrada ({entrevista.get_concepto_display()})",
            motivo=observaciones or "Entrevista completada",
            datos_capturados={
                "entrevista_id": str(entrevista.id),
                "calificacion": float(calificacion) if calificacion is not None else None,
            },
            usuario=usuario,
        )

    return entrevista


@transaction.atomic
def registrar_y_completar_evaluacion(
    postulacion: Postulacion,
    tipo_evaluacion: str,
    nombre_prueba: str,
    puntaje_obtenido: float,
    puntaje_maximo: float = 100.0,
    porcentaje_aprobacion: float = 70.0,
    concepto: str = "",
    evaluador=None,
    archivo_informe=None,
    usuario=None,
) -> Evaluacion:
    """
    Registra una prueba técnica/psicotécnica.
    - 0-60: crítico -> NO_APROBADA y cierre automático (NO_SELECCIONADO, notifica).
    - 61-80: alerta -> APROBADA, continúa requiriendo refuerzo.
    - 81-100: apto -> APROBADA.
    """
    if ultima_entrevista_desfavorable(postulacion):
        raise EntrevistaDesfavorableError(
            "No puede continuar: la entrevista fue desfavorable."
        )

    porcentaje = round((puntaje_obtenido / puntaje_maximo) * 100, 2) if puntaje_maximo > 0 else 0
    clasificacion = clasificar_evaluacion(porcentaje)
    aprobada = clasificacion in ("apto", "alerta")
    estado_eval = Evaluacion.Estado.APROBADA if aprobada else Evaluacion.Estado.NO_APROBADA

    concepto_base = concepto or (
        f"Puntaje obtenido: {puntaje_obtenido}/{puntaje_maximo} ({porcentaje}%). "
        f"Clasificación: {etiqueta_clasificacion(clasificacion)}."
    )

    evaluacion = Evaluacion.objects.create(
        empresa=postulacion.empresa,
        postulacion=postulacion,
        tipo_evaluacion=tipo_evaluacion,
        nombre_prueba=nombre_prueba,
        fecha_realizacion=timezone.now(),
        evaluador=evaluador or usuario,
        puntaje_obtenido=puntaje_obtenido,
        puntaje_maximo=puntaje_maximo,
        porcentaje_aprobacion=porcentaje_aprobacion,
        estado=estado_eval,
        concepto=concepto_base,
        archivo_informe=archivo_informe,
    )

    # Reflejar el puntaje de la evaluación en la postulación
    postulacion.puntuacion_general = porcentaje

    if not aprobada:
        motivo = f"Evaluación crítica ({porcentaje}%): no continúa en el proceso"
        if postulacion.es_activa:
            cerrar_postulacion(
                postulacion=postulacion,
                nuevo_estado=Postulacion.Estado.NO_SELECCIONADO,
                motivo=motivo,
                usuario=usuario,
                datos_adicionales={
                    "evaluacion_id": str(evaluacion.id),
                    "puntaje": float(puntaje_obtenido),
                    "porcentaje": porcentaje,
                    "clasificacion": clasificacion,
                },
            )
        elif porcentaje is not None:
            postulacion.save(update_fields=["puntuacion_general"])
        return evaluacion

    etapas = set(postulacion.etapas_completadas or [])
    etapas.add("evaluacion")
    postulacion.etapas_completadas = list(etapas)

    sufijo = " (requiere refuerzo de competencia)" if clasificacion == "alerta" else ""
    motivo_evento = f"Evaluación '{nombre_prueba}' aprobada con {porcentaje}%{sufijo}"

    if postulacion.estado in [Postulacion.Estado.PRESELECCIONADO, Postulacion.Estado.EN_ENTREVISTA]:
        transicionar_postulacion(
            postulacion=postulacion,
            nuevo_estado=Postulacion.Estado.EN_EVALUACION,
            usuario=usuario,
            motivo=motivo_evento,
            contexto={
                "evaluacion_id": str(evaluacion.id),
                "puntaje": float(puntaje_obtenido),
                "clasificacion": clasificacion,
            },
        )
    else:
        postulacion.save(update_fields=["etapas_completadas", "puntuacion_general"])
        PostulacionEvento.objects.create(
            postulacion=postulacion,
            tipo_evento=PostulacionEvento.TipoEvento.PRUEBA_REGISTRADA,
            estado_anterior=postulacion.estado,
            estado_nuevo=postulacion.estado,
            descripcion=motivo_evento,
            motivo=f"Puntaje {puntaje_obtenido}/{puntaje_maximo}",
            datos_capturados={
                "evaluacion_id": str(evaluacion.id),
                "puntaje": float(puntaje_obtenido),
                "clasificacion": clasificacion,
            },
            usuario=usuario,
        )

    return evaluacion


@transaction.atomic
def registrar_y_completar_validacion(
    postulacion: Postulacion,
    tipo_verificacion: str,
    entidad_o_contacto: str,
    estado: str = ValidacionDocumental.Estado.VERIFICADO_CONFORME,
    telefono_contacto: str = "",
    detalles_verificacion: str = "",
    soporte_archivo=None,
    usuario=None,
) -> ValidacionDocumental:
    """
    Registra la validación documental / antecedentes y habilita la etapa en la postulación.
    """
    if ultima_entrevista_desfavorable(postulacion):
        raise EntrevistaDesfavorableError(
            "No puede continuar: la entrevista fue desfavorable."
        )

    validacion = ValidacionDocumental.objects.create(
        empresa=postulacion.empresa,
        postulacion=postulacion,
        tipo_verificacion=tipo_verificacion,
        entidad_o_contacto=entidad_o_contacto,
        telefono_contacto=telefono_contacto,
        verificado_por=usuario,
        fecha_verificacion=timezone.now(),
        estado=estado,
        detalles_verificacion=detalles_verificacion,
        soporte_archivo=soporte_archivo,
    )

    if estado == ValidacionDocumental.Estado.VERIFICADO_CONFORME:
        etapas = set(postulacion.etapas_completadas or [])
        etapas.add("validacion_documental")
        postulacion.etapas_completadas = list(etapas)

        if postulacion.estado in [
            Postulacion.Estado.PRESELECCIONADO,
            Postulacion.Estado.EN_ENTREVISTA,
            Postulacion.Estado.EN_EVALUACION,
        ]:
            transicionar_postulacion(
                postulacion=postulacion,
                nuevo_estado=Postulacion.Estado.EN_VALIDACION,
                usuario=usuario,
                motivo=f"Validación documental conforme: {validacion.get_tipo_verificacion_display()} ({entidad_o_contacto})",
                contexto={"validacion_id": str(validacion.id)},
            )
        else:
            postulacion.save(update_fields=["etapas_completadas"])
            PostulacionEvento.objects.create(
                postulacion=postulacion,
                tipo_evento=PostulacionEvento.TipoEvento.VALIDACION_REGISTRADA,
                estado_anterior=postulacion.estado,
                estado_nuevo=postulacion.estado,
                descripcion=f"Validación documental {validacion.get_tipo_verificacion_display()} verificada conforme",
                motivo=detalles_verificacion or "Validación conforme",
                datos_capturados={"validacion_id": str(validacion.id)},
                usuario=usuario,
            )

    return validacion
