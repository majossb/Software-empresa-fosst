"""
Servicios de registro y calificación de etapas de selección (Fase C) — FOSST V.I.D.A.
Orquesta Entrevistas, Evaluaciones y Validaciones Documentales vinculadas a Postulaciones.
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
from apps.reclutamiento.services.postulacion import transicionar_postulacion


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
    Registra una entrevista y actualiza las etapas completadas de la postulación si es favorable.
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

    es_favorable = concepto in [Entrevista.Concepto.FAVORABLE, Entrevista.Concepto.CON_RESERVAS]
    if es_favorable:
        etapas = set(postulacion.etapas_completadas or [])
        etapas.add("entrevista")
        postulacion.etapas_completadas = list(etapas)

        # Si estaba en preseleccionado, transiciona formalmente a EN_ENTREVISTA
        if postulacion.estado == Postulacion.Estado.PRESELECCIONADO:
            transicionar_postulacion(
                postulacion=postulacion,
                nuevo_estado=Postulacion.Estado.EN_ENTREVISTA,
                usuario=usuario,
                motivo=f"Entrevista {entrevista.get_tipo_entrevista_display()} completada ({entrevista.get_concepto_display()})",
                contexto={"entrevista_id": str(entrevista.id), "calificacion": float(calificacion) if calificacion is not None else None},
            )
        else:
            postulacion.save(update_fields=["etapas_completadas"])
            PostulacionEvento.objects.create(
                postulacion=postulacion,
                tipo_evento=PostulacionEvento.TipoEvento.ENTREVISTA_REGISTRADA,
                estado_anterior=postulacion.estado,
                estado_nuevo=postulacion.estado,
                descripcion=f"Entrevista {entrevista.get_tipo_entrevista_display()} registrada ({entrevista.get_concepto_display()})",
                motivo=observaciones or "Entrevista completada",
                datos_capturados={"entrevista_id": str(entrevista.id), "calificacion": float(calificacion) if calificacion is not None else None},
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
    Registra una prueba técnica o psicotécnica y marca la etapa de evaluación si supera el umbral.
    """
    porcentaje = round((puntaje_obtenido / puntaje_maximo) * 100, 2) if puntaje_maximo > 0 else 0
    aprobada = porcentaje >= porcentaje_aprobacion
    estado_eval = Evaluacion.Estado.APROBADA if aprobada else Evaluacion.Estado.NO_APROBADA

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
        concepto=concepto or f"Puntaje obtenido: {puntaje_obtenido}/{puntaje_maximo} ({porcentaje}%)",
        archivo_informe=archivo_informe,
    )

    if aprobada:
        etapas = set(postulacion.etapas_completadas or [])
        etapas.add("evaluacion")
        postulacion.etapas_completadas = list(etapas)

        if postulacion.estado in [Postulacion.Estado.PRESELECCIONADO, Postulacion.Estado.EN_ENTREVISTA]:
            transicionar_postulacion(
                postulacion=postulacion,
                nuevo_estado=Postulacion.Estado.EN_EVALUACION,
                usuario=usuario,
                motivo=f"Evaluación '{nombre_prueba}' aprobada con {porcentaje}%",
                contexto={"evaluacion_id": str(evaluacion.id), "puntaje": float(puntaje_obtenido)},
            )
        else:
            postulacion.save(update_fields=["etapas_completadas"])
            PostulacionEvento.objects.create(
                postulacion=postulacion,
                tipo_evento=PostulacionEvento.TipoEvento.PRUEBA_REGISTRADA,
                estado_anterior=postulacion.estado,
                estado_nuevo=postulacion.estado,
                descripcion=f"Evaluación '{nombre_prueba}' aprobada ({porcentaje}%)",
                motivo=f"Puntaje {puntaje_obtenido}/{puntaje_maximo}",
                datos_capturados={"evaluacion_id": str(evaluacion.id), "puntaje": float(puntaje_obtenido)},
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

        if postulacion.estado in [Postulacion.Estado.PRESELECCIONADO, Postulacion.Estado.EN_ENTREVISTA, Postulacion.Estado.EN_EVALUACION]:
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
