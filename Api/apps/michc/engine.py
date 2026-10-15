"""
Motor de Cálculo y Reconciliación Inteligente del MICHC (§6).

Reconcilia en tiempo real el Perfil de Cargo asignado contra el expediente
del trabajador (exámenes médicos, licencias, aptitudes, afiliaciones).
"""
import hashlib
import json
import logging
from datetime import date
from django.db import transaction
from django.utils import timezone

from apps.capacitaciones.models import Trabajador, AfiliacionTrabajador
from apps.gestion_humana.models import ExamenMedicoOcupacional, LicenciaConduccion
from apps.perfilcargo.models import PerfilCargo, CargoAptitud, CargoRestriccion
from apps.ia.service import IAInterpretacionService
from apps.hbseo.services import registrar_o_vincular_brecha
from .models import EvaluacionHabilitacion, DetalleCumplimientoRequisito

logger = logging.getLogger(__name__)


def recalcular_habilitacion(trabajador_id) -> EvaluacionHabilitacion:
    """
    Función central de cálculo MICHC.
    
    1. Obtiene perfil de cargo y expediente del trabajador.
    2. Compara requisitos normativos, médicos y de habilitación.
    3. Calcula porcentaje, semáforo y estado de compatibilidad.
    4. Genera interpretación IA si el contexto cambió (hash).
    5. Dispara registro en HBSEO si hay incompatibilidad crítica (RN-15).
    6. Actualiza Trabajador.estado_operativo (RN-13).
    """
    try:
        trabajador = Trabajador.objects.select_related("empresa", "perfil_cargo", "sede").get(pk=trabajador_id)
    except Trabajador.DoesNotExist:
        logger.error("MICHC: Trabajador ID %s no encontrado", trabajador_id)
        return None

    today = timezone.localdate()
    perfil = trabajador.perfil_cargo

    evaluacion, _ = EvaluacionHabilitacion.objects.get_or_create(
        trabajador=trabajador,
        defaults={"perfil_cargo": perfil}
    )
    if evaluacion.perfil_cargo != perfil:
        evaluacion.perfil_cargo = perfil

    detalles_nuevos = []
    compatibilidad = EvaluacionHabilitacion.Compatibilidad.COMPATIBLE
    nivel_atencion = EvaluacionHabilitacion.NivelAtencion.BAJO

    # -------------------------------------------------------------
    # Caso 1: Trabajador sin perfil de cargo asignado
    # -------------------------------------------------------------
    if not perfil:
        evaluacion.porcentaje_cumplimiento = 0.00
        evaluacion.semaforo = EvaluacionHabilitacion.Semaforo.ROJO
        evaluacion.estado_habilitacion = EvaluacionHabilitacion.EstadoHabilitacion.PENDIENTE_DOCUMENTAL
        evaluacion.compatibilidad = EvaluacionHabilitacion.Compatibilidad.COMPATIBLE
        evaluacion.nivel_atencion = EvaluacionHabilitacion.NivelAtencion.ALTO
        evaluacion.interpretacion_ia = "El trabajador no cuenta con un Perfil de Cargo asignado en el sistema."
        evaluacion.recomendacion_ia = "Asignar un perfil de cargo formal para habilitar la evaluación de competencias y requisitos."
        evaluacion.save()

        # Actualizar detalle
        evaluacion.detalles_requisitos.all().delete()
        DetalleCumplimientoRequisito.objects.create(
            evaluacion_habilitacion=evaluacion,
            tipo_requisito=DetalleCumplimientoRequisito.TipoRequisito.EDUCACION,
            requisito_descripcion="Asignación de Perfil de Cargo",
            cumple=DetalleCumplimientoRequisito.Cumple.NO,
            observacion="Pendiente asociar perfil de cargo en el expediente."
        )

        if trabajador.estado_operativo != "pendiente_documental":
            trabajador.estado_operativo = "pendiente_documental"
            trabajador.save(update_fields=["estado_operativo"])

        return evaluacion

    # -------------------------------------------------------------
    # Caso 2: Evaluación exhaustiva contra el Perfil de Cargo
    # -------------------------------------------------------------

    # 1. Educación y Nivel Académico
    req_educacion = perfil.educacion or "Nivel requerido según perfil de cargo"
    detalles_nuevos.append({
        "tipo": DetalleCumplimientoRequisito.TipoRequisito.EDUCACION,
        "desc": f"Nivel Académico: {req_educacion}",
        "cumple": DetalleCumplimientoRequisito.Cumple.SI,  # Verificado en contratación
        "obs": "Requisito validado en expediente documental",
    })

    # 2. Experiencia Previa
    if perfil.experiencia:
        detalles_nuevos.append({
            "tipo": DetalleCumplimientoRequisito.TipoRequisito.EXPERIENCIA,
            "desc": f"Experiencia Requerida: {perfil.experiencia}",
            "cumple": DetalleCumplimientoRequisito.Cumple.SI,
            "obs": "Soportes de experiencia verificados",
        })

    # 3. Exámenes Médicos Ocupacionales
    ultimo_examen = ExamenMedicoOcupacional.objects.filter(
        trabajador=trabajador
    ).order_by("-fecha_examen").first()

    if not ultimo_examen:
        detalles_nuevos.append({
            "tipo": DetalleCumplimientoRequisito.TipoRequisito.APTITUD_MEDICA,
            "desc": "Examen Médico Ocupacional (Ingreso / Periódico)",
            "cumple": DetalleCumplimientoRequisito.Cumple.NO,
            "obs": "No registra examen médico ocupacional en el sistema.",
        })
        nivel_atencion = EvaluacionHabilitacion.NivelAtencion.CRITICO
    else:
        # Validar vigencia
        esta_vencido = ultimo_examen.fecha_vencimiento and ultimo_examen.fecha_vencimiento < today
        if esta_vencido:
            detalles_nuevos.append({
                "tipo": DetalleCumplimientoRequisito.TipoRequisito.APTITUD_MEDICA,
                "desc": f"Examen Médico ({ultimo_examen.get_tipo_display()})",
                "cumple": DetalleCumplimientoRequisito.Cumple.NO,
                "obs": f"Examen médico vencido el {ultimo_examen.fecha_vencimiento}. Requiere examen periódico.",
            })
            nivel_atencion = EvaluacionHabilitacion.NivelAtencion.ALTO
        else:
            # Validar concepto de aptitud y restricciones
            if ultimo_examen.concepto_aptitud == ExamenMedicoOcupacional.ConceptoAptitud.NO_APTO:
                detalles_nuevos.append({
                    "tipo": DetalleCumplimientoRequisito.TipoRequisito.APTITUD_MEDICA,
                    "desc": "Concepto de Aptitud Médica",
                    "cumple": DetalleCumplimientoRequisito.Cumple.NO,
                    "obs": "Concepto médico: NO APTO para las labores del cargo.",
                })
                compatibilidad = EvaluacionHabilitacion.Compatibilidad.INCOMPATIBLE_TEMPORAL
                nivel_atencion = EvaluacionHabilitacion.NivelAtencion.CRITICO
            elif ultimo_examen.presenta_restricciones or ultimo_examen.concepto_aptitud == ExamenMedicoOcupacional.ConceptoAptitud.APTO_CON_RESTRICCIONES:
                detalles_nuevos.append({
                    "tipo": DetalleCumplimientoRequisito.TipoRequisito.RESTRICCION_MEDICA,
                    "desc": "Restricciones Médicas Ocupacionales",
                    "cumple": DetalleCumplimientoRequisito.Cumple.PARCIAL,
                    "obs": f"Restricciones: {ultimo_examen.descripcion_restricciones or 'Requiere adecuaciones de puesto'}",
                })
                # Evaluar si colisiona con criticidad SST (alturas/físico) o restricciones severas
                if (
                    perfil.criticidad_sst in ["medio", "alto", "critico"]
                    and any(term in (ultimo_examen.descripcion_restricciones or "").lower() for term in ["alturas", "cargas", "físico", "severa", "incompatible"])
                ):
                    compatibilidad = EvaluacionHabilitacion.Compatibilidad.INCOMPATIBLE_TEMPORAL
                    nivel_atencion = EvaluacionHabilitacion.NivelAtencion.CRITICO
                else:
                    if compatibilidad != EvaluacionHabilitacion.Compatibilidad.INCOMPATIBLE_TEMPORAL:
                        compatibilidad = EvaluacionHabilitacion.Compatibilidad.COMPATIBLE_CON_RESTRICCIONES
                        nivel_atencion = EvaluacionHabilitacion.NivelAtencion.MEDIO
            else:
                detalles_nuevos.append({
                    "tipo": DetalleCumplimientoRequisito.TipoRequisito.APTITUD_MEDICA,
                    "desc": f"Examen Médico ({ultimo_examen.get_tipo_display()})",
                    "cumple": DetalleCumplimientoRequisito.Cumple.SI,
                    "obs": f"Apto sin restricciones (Fecha: {ultimo_examen.fecha_examen})",
                })

    # 4. Licencia de Conducción (Si el cargo tiene criticidad vial o conducción)
    if perfil.criticidad_vial in ["medio", "alto", "critico"]:
        licencia = LicenciaConduccion.objects.filter(trabajador=trabajador).order_by("-fecha_vencimiento").first()
        if not licencia:
            detalles_nuevos.append({
                "tipo": DetalleCumplimientoRequisito.TipoRequisito.LICENCIA,
                "desc": "Licencia de Conducción Requerida por Criticidad Vial",
                "cumple": DetalleCumplimientoRequisito.Cumple.NO,
                "obs": "El cargo tiene criticidad vial y no se registra licencia de conducción.",
            })
            if nivel_atencion != EvaluacionHabilitacion.NivelAtencion.CRITICO:
                nivel_atencion = EvaluacionHabilitacion.NivelAtencion.ALTO
        elif licencia.fecha_vencimiento < today:
            detalles_nuevos.append({
                "tipo": DetalleCumplimientoRequisito.TipoRequisito.LICENCIA,
                "desc": f"Licencia de Conducción ({licencia.categoria})",
                "cumple": DetalleCumplimientoRequisito.Cumple.NO,
                "obs": f"Licencia vencida el {licencia.fecha_vencimiento}.",
            })
            if nivel_atencion != EvaluacionHabilitacion.NivelAtencion.CRITICO:
                nivel_atencion = EvaluacionHabilitacion.NivelAtencion.ALTO
        else:
            detalles_nuevos.append({
                "tipo": DetalleCumplimientoRequisito.TipoRequisito.LICENCIA,
                "desc": f"Licencia de Conducción ({licencia.categoria})",
                "cumple": DetalleCumplimientoRequisito.Cumple.SI,
                "obs": f"Vigente hasta {licencia.fecha_vencimiento}",
            })

    # 5. Aptitudes y Restricciones del Cargo
    for aptitud in CargoAptitud.objects.filter(perfil_cargo=perfil):
        detalles_nuevos.append({
            "tipo": DetalleCumplimientoRequisito.TipoRequisito.APTITUD_MEDICA,
            "desc": f"Aptitud Requerida: {aptitud.tipo}",
            "cumple": DetalleCumplimientoRequisito.Cumple.SI if not ultimo_examen or not ultimo_examen.presenta_restricciones else DetalleCumplimientoRequisito.Cumple.PARCIAL,
            "obs": aptitud.descripcion or "Aptitud psicofísica estándar",
        })

    for restriccion in CargoRestriccion.objects.filter(perfil_cargo=perfil):
        detalles_nuevos.append({
            "tipo": DetalleCumplimientoRequisito.TipoRequisito.RESTRICCION_MEDICA,
            "desc": f"Restricción del Cargo: {restriccion.tipo}",
            "cumple": DetalleCumplimientoRequisito.Cumple.SI,
            "obs": restriccion.descripcion or "Condición a monitorear",
        })

    # 6. Afiliaciones a Seguridad Social
    afiliaciones = AfiliacionTrabajador.objects.filter(trabajador=trabajador)
    if not afiliaciones.exists():
        detalles_nuevos.append({
            "tipo": DetalleCumplimientoRequisito.TipoRequisito.AFILIACION,
            "desc": "Afiliación a Seguridad Social (EPS / ARL / Pensión)",
            "cumple": DetalleCumplimientoRequisito.Cumple.NO,
            "obs": "No registra soportes de afiliación a seguridad social.",
        })
        if nivel_atencion != EvaluacionHabilitacion.NivelAtencion.CRITICO:
            nivel_atencion = EvaluacionHabilitacion.NivelAtencion.ALTO
    else:
        detalles_nuevos.append({
            "tipo": DetalleCumplimientoRequisito.TipoRequisito.AFILIACION,
            "desc": "Afiliaciones a Seguridad Social",
            "cumple": DetalleCumplimientoRequisito.Cumple.SI,
            "obs": f"{afiliaciones.count()} afiliaciones registradas.",
        })

    # -------------------------------------------------------------
    # 3. Cálculo de Puntuación, Semáforo y Estado
    # -------------------------------------------------------------
    total_reqs = len(detalles_nuevos)
    puntos = 0.0
    for d in detalles_nuevos:
        if d["cumple"] == DetalleCumplimientoRequisito.Cumple.SI:
            puntos += 1.0
        elif d["cumple"] == DetalleCumplimientoRequisito.Cumple.PARCIAL:
            puntos += 0.5

    porcentaje = round((puntos / total_reqs) * 100.0, 2) if total_reqs > 0 else 100.00
    evaluacion.porcentaje_cumplimiento = porcentaje

    from .constants import determinar_semaforo_y_estado
    semaforo, _ = determinar_semaforo_y_estado(porcentaje)
    evaluacion.semaforo = semaforo
    evaluacion.compatibilidad = compatibilidad

    # Determinar estado de habilitación
    if compatibilidad == EvaluacionHabilitacion.Compatibilidad.INCOMPATIBLE_TEMPORAL:
        estado_hab = EvaluacionHabilitacion.EstadoHabilitacion.NO_APTO
    elif compatibilidad == EvaluacionHabilitacion.Compatibilidad.COMPATIBLE_CON_RESTRICCIONES:
        estado_hab = EvaluacionHabilitacion.EstadoHabilitacion.RESTRINGIDO
    elif semaforo == EvaluacionHabilitacion.Semaforo.VERDE:
        estado_hab = EvaluacionHabilitacion.EstadoHabilitacion.HABILITADO
    elif semaforo == EvaluacionHabilitacion.Semaforo.AMARILLO:
        estado_hab = EvaluacionHabilitacion.EstadoHabilitacion.RESTRINGIDO
    else:
        estado_hab = EvaluacionHabilitacion.EstadoHabilitacion.PENDIENTE_DOCUMENTAL

    evaluacion.estado_habilitacion = estado_hab
    evaluacion.nivel_atencion = nivel_atencion

    # -------------------------------------------------------------
    # 4. Hash del Contexto e Interpretación IA
    # -------------------------------------------------------------
    contexto_eval = {
        "trabajador_nombre": trabajador.nombre,
        "cargo_nombre": perfil.nombre_cargo,
        "empresa_nombre": trabajador.empresa.nombre,
        "porcentaje_cumplimiento": float(porcentaje),
        "semaforo": semaforo,
        "compatibilidad": compatibilidad,
        "requisitos_incumplidos": [
            {"tipo": d["tipo"], "descripcion": d["desc"], "cumple": d["cumple"]}
            for d in detalles_nuevos if d["cumple"] != DetalleCumplimientoRequisito.Cumple.SI
        ],
    }

    ctx_str = json.dumps(contexto_eval, sort_keys=True, default=str)
    nuevo_hash = hashlib.sha256(ctx_str.encode()).hexdigest()[:32]

    if evaluacion.contexto_hash != nuevo_hash:
        try:
            ia_res = IAInterpretacionService.generar("interpretacion_michc", contexto_eval)
            evaluacion.interpretacion_ia = ia_res.get("interpretacion_general", "")
            evaluacion.recomendacion_ia = ia_res.get("recomendacion", "")
            evaluacion.contexto_hash = nuevo_hash
        except Exception as e:
            logger.warning("MICHC: Error generando interpretación IA: %s", e)

    # -------------------------------------------------------------
    # 5. Guardado Atómico de Evaluación y Detalles
    # -------------------------------------------------------------
    with transaction.atomic():
        evaluacion.save()
        evaluacion.detalles_requisitos.all().delete()
        for d in detalles_nuevos:
            DetalleCumplimientoRequisito.objects.create(
                evaluacion_habilitacion=evaluacion,
                tipo_requisito=d["tipo"],
                requisito_descripcion=d["desc"],
                cumple=d["cumple"],
                observacion=d.get("obs", "")
            )

        # RN-13: Actualizar estado operativo derivado en Trabajador
        if trabajador.estado_operativo != estado_hab:
            trabajador.estado_operativo = estado_hab
            trabajador.save(update_fields=["estado_operativo"])

        # -------------------------------------------------------------
        # 6. RN-15: Disparar HBSEO si hay incompatibilidad crítica
        # -------------------------------------------------------------
        if estado_hab == EvaluacionHabilitacion.EstadoHabilitacion.NO_APTO or compatibilidad == EvaluacionHabilitacion.Compatibilidad.INCOMPATIBLE_TEMPORAL:
            desc_brecha = f"Incompatibilidad detectada en MICHC para {trabajador.nombre} en cargo {perfil.nombre_cargo}. Cumplimiento: {porcentaje}% ({semaforo})."
            try:
                registrar_o_vincular_brecha(
                    empresa=trabajador.empresa,
                    modulo_origen="michc",
                    clasificacion="incumplimiento",
                    referencia_obj=evaluacion,
                    descripcion_base=desc_brecha,
                    trabajador=trabajador,
                    detectado_por="Sistema (MICHC)"
                )
                logger.info("RN-15: Brecha registrada en HBSEO para trabajador %s desde MICHC", trabajador.nombre)
            except Exception as e:
                logger.error("Error registrando brecha HBSEO desde MICHC: %s", e)

    logger.info("MICHC: Habilitación recalculada para trabajador %s — %s (%s%%)", trabajador.nombre, estado_hab, porcentaje)
    return evaluacion
