"""
Motor de Cálculo y Reconciliación Inteligente del MICHC (§6).

Reconcilia en tiempo real el Perfil de Cargo asignado contra el expediente
del trabajador (exámenes médicos, licencias, aptitudes, afiliaciones,
formación obligatoria y competencias).
"""
import hashlib
import json
import logging
from datetime import date, timedelta
from django.db import transaction
from django.utils import timezone

from apps.capacitaciones.models import Trabajador, AfiliacionTrabajador
from apps.gestion_humana.models import ExamenMedicoOcupacional, LicenciaConduccion
from apps.perfilcargo.models import PerfilCargo, CargoAptitud, CargoRestriccion, CargoCompetencia
from apps.ia.service import IAInterpretacionService
from apps.hbseo.models import Brecha
from apps.hbseo.services import registrar_o_vincular_brecha
from apps.common.competencias import parse_nivel, obtener_nombre_nivel
from .models import EvaluacionHabilitacion, DetalleCumplimientoRequisito

logger = logging.getLogger(__name__)


def recalcular_habilitacion(trabajador_id) -> EvaluacionHabilitacion:
    """
    Función central de cálculo MICHC.
    
    1. Obtiene perfil de cargo y expediente del trabajador.
    2. Compara requisitos normativos, médicos y de habilitación.
    3. Evalúa formación obligatoria (cursos vigentes/vencidos/faltantes).
    4. Evalúa competencias (última evaluación vs nivel esperado).
    5. Calcula porcentaje, semáforo y estado de compatibilidad.
    6. Genera interpretación IA si el contexto cambió (hash).
    7. Dispara registro o subsanación en HBSEO (formación, competencias, incompatibilidad).
    8. Actualiza Trabajador.estado_operativo (RN-13).
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

    # 1. Educación y Nivel Académico — Pendiente de validar
    req_educacion = perfil.educacion or "Nivel requerido según perfil de cargo"
    detalles_nuevos.append({
        "tipo": DetalleCumplimientoRequisito.TipoRequisito.EDUCACION,
        "desc": f"Nivel Académico: {req_educacion}",
        "cumple": DetalleCumplimientoRequisito.Cumple.PENDIENTE,
        "obs": "Pendiente de validar documentalmente (soporte no verificado en el sistema).",
    })

    # 2. Experiencia Previa — Pendiente de validar
    if perfil.experiencia:
        detalles_nuevos.append({
            "tipo": DetalleCumplimientoRequisito.TipoRequisito.EXPERIENCIA,
            "desc": f"Experiencia Requerida: {perfil.experiencia}",
            "cumple": DetalleCumplimientoRequisito.Cumple.PENDIENTE,
            "obs": "Pendiente de validar documentalmente (certificaciones laborales no verificadas).",
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
    # 7. Formación Obligatoria del Cargo (Fase 3)
    # -------------------------------------------------------------
    detalles_formacion, brechas_formacion, cursos_cumplidos = _evaluar_formacion_obligatoria(trabajador, perfil, today)
    detalles_nuevos.extend(detalles_formacion)

    for d in detalles_formacion:
        if d["cumple"] == DetalleCumplimientoRequisito.Cumple.NO:
            if nivel_atencion not in [EvaluacionHabilitacion.NivelAtencion.CRITICO]:
                nivel_atencion = EvaluacionHabilitacion.NivelAtencion.ALTO

    # -------------------------------------------------------------
    # 8. Competencias del Cargo (Fase 3)
    # -------------------------------------------------------------
    detalles_competencia, brechas_competencia, comps_cumplidas = _evaluar_competencias(trabajador, perfil)
    detalles_nuevos.extend(detalles_competencia)

    for d in detalles_competencia:
        if d["cumple"] == DetalleCumplimientoRequisito.Cumple.NO:
            if nivel_atencion not in [EvaluacionHabilitacion.NivelAtencion.CRITICO]:
                nivel_atencion = EvaluacionHabilitacion.NivelAtencion.ALTO

    # -------------------------------------------------------------
    # 9. Cálculo de Puntuación, Semáforo y Estado
    # -------------------------------------------------------------
    # Solo los requisitos con mecanismo de evaluación operativo suman al porcentaje.
    # Los requisitos 'pendiente de validar' (educación y experiencia sin módulo de validación)
    # no penalizan la habilitación operativa para evitar bloqueos artificiales.
    reqs_evaluables = [
        d for d in detalles_nuevos 
        if d["cumple"] not in [DetalleCumplimientoRequisito.Cumple.PENDIENTE, DetalleCumplimientoRequisito.Cumple.NO_APLICA]
    ]
    total_reqs = len(reqs_evaluables)
    puntos = 0.0
    for d in reqs_evaluables:
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
    # 10. Hash del Contexto e Interpretación IA
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
    # 11. Guardado Atómico de Evaluación y Detalles
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
        # 12. RN-15: Disparar HBSEO si hay incompatibilidad crítica
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
        elif estado_hab == EvaluacionHabilitacion.EstadoHabilitacion.HABILITADO:
            # Revertir / subsanar brechas abiertas de incompatibilidad previa
            Brecha.objects.filter(
                empresa=trabajador.empresa,
                trabajador=trabajador,
                estado__in=[Brecha.Estado.DETECTADA, Brecha.Estado.EN_TRATAMIENTO, Brecha.Estado.CONTROLADA],
                origenes__modulo_origen="michc",
            ).update(estado=Brecha.Estado.SUBSANADA)

        # -------------------------------------------------------------
        # 13. Brechas HBSEO por formación obligatoria incumplida
        # -------------------------------------------------------------
        for brecha_info in brechas_formacion:
            try:
                registrar_o_vincular_brecha(
                    empresa=trabajador.empresa,
                    modulo_origen="formacion",
                    clasificacion=brecha_info["clasificacion"],
                    referencia_obj=brecha_info["referencia_obj"],
                    descripcion_base=brecha_info["descripcion"],
                    trabajador=trabajador,
                    detectado_por="Sistema (Formación/MICHC)"
                )
            except Exception as e:
                logger.error("Error registrando brecha HBSEO de formación: %s", e)

        # -------------------------------------------------------------
        # 14. Brechas HBSEO por competencias no cumplidas
        # -------------------------------------------------------------
        for brecha_info in brechas_competencia:
            try:
                registrar_o_vincular_brecha(
                    empresa=trabajador.empresa,
                    modulo_origen="formacion",
                    clasificacion=brecha_info["clasificacion"],
                    referencia_obj=brecha_info["referencia_obj"],
                    descripcion_base=brecha_info["descripcion"],
                    trabajador=trabajador,
                    detectado_por="Sistema (Formación/MICHC)"
                )
            except Exception as e:
                logger.error("Error registrando brecha HBSEO de competencia: %s", e)

        # -------------------------------------------------------------
        # 15. Subsanación automática de brechas previas al renovar/cumplir
        # -------------------------------------------------------------
        if cursos_cumplidos:
            brechas_formacion_abiertas = Brecha.objects.filter(
                empresa=trabajador.empresa,
                trabajador=trabajador,
                estado__in=[Brecha.Estado.DETECTADA, Brecha.Estado.EN_TRATAMIENTO, Brecha.Estado.CONTROLADA],
                origenes__modulo_origen="formacion",
            ).prefetch_related("origenes")

            for curso_info in cursos_cumplidos:
                cid = str(curso_info["curso_id"])
                cnombre = curso_info["curso_nombre"].lower()

                for b in brechas_formacion_abiertas:
                    coincide = False
                    for origen in b.origenes.all():
                        if str(origen.object_id) == cid:
                            coincide = True
                            break
                        if origen.referencia and hasattr(origen.referencia, 'curso_id') and str(origen.referencia.curso_id) == cid:
                            coincide = True
                            break
                    if not coincide and cnombre and (cnombre in (b.descripcion_automatica or "").lower() or b.origenes.filter(descripcion__icontains=cnombre).exists()):
                        coincide = True

                    if coincide and b.estado != Brecha.Estado.SUBSANADA:
                        b.estado = Brecha.Estado.SUBSANADA
                        b.save(update_fields=["estado"])
                        logger.info("HBSEO: Brecha %s subsanada automáticamente por renovación de curso %s", b.codigo, curso_info["curso_nombre"])

        if comps_cumplidas:
            brechas_formacion_abiertas = Brecha.objects.filter(
                empresa=trabajador.empresa,
                trabajador=trabajador,
                estado__in=[Brecha.Estado.DETECTADA, Brecha.Estado.EN_TRATAMIENTO, Brecha.Estado.CONTROLADA],
                origenes__modulo_origen="formacion",
            ).prefetch_related("origenes")

            for comp_info in comps_cumplidas:
                comp_nombre = comp_info["comp_nombre"].lower()
                for b in brechas_formacion_abiertas:
                    if comp_nombre and (comp_nombre in (b.descripcion_automatica or "").lower() or b.origenes.filter(descripcion__icontains=comp_nombre).exists()):
                        if b.estado != Brecha.Estado.SUBSANADA:
                            b.estado = Brecha.Estado.SUBSANADA
                            b.save(update_fields=["estado"])
                            logger.info("HBSEO: Brecha %s subsanada automáticamente por cumplimiento de competencia %s", b.codigo, comp_info["comp_nombre"])

    logger.info("MICHC: Habilitación recalculada para trabajador %s — %s (%s%%)", trabajador.nombre, estado_hab, porcentaje)
    return evaluacion


def _evaluar_formacion_obligatoria(trabajador, perfil, today):
    """
    Evalúa los requisitos de formación obligatoria del cargo contra los registros del trabajador.

    Retorna:
        (detalles, brechas, cursos_cumplidos) donde:
        - detalles: lista de dicts para DetalleCumplimientoRequisito
        - brechas: lista de dicts para registrar_o_vincular_brecha
        - cursos_cumplidos: lista de dicts {curso_id, curso_nombre}
    """
    from apps.formacion.models import CargoRequisitoFormacion, RegistroFormacion

    detalles = []
    brechas = []
    cursos_cumplidos = []

    requisitos = list(
        CargoRequisitoFormacion.objects.filter(
            perfil_cargo=perfil,
            obligatorio=True,
        ).select_related("curso")
    )

    if not requisitos:
        return detalles, brechas, cursos_cumplidos

    # Obtener todos los registros de formación del trabajador
    registros = list(
        RegistroFormacion.objects.filter(trabajador=trabajador)
        .select_related("curso")
        .order_by("-fecha_realizacion", "-created_at")
    )
    registros_por_curso = {}
    for reg in registros:
        cid = str(reg.curso_id)
        if cid not in registros_por_curso:
            registros_por_curso[cid] = reg

    # Detectar grupos alternativos satisfechos
    grupos_satisfechos = {}
    for req in requisitos:
        if req.grupo_alternativo:
            reg = registros_por_curso.get(str(req.curso_id))
            if reg:
                if not reg.fecha_vencimiento or reg.fecha_vencimiento >= today:
                    if req.grupo_alternativo not in grupos_satisfechos:
                        grupos_satisfechos[req.grupo_alternativo] = {
                            "curso_id": str(req.curso_id),
                            "curso_nombre": req.curso.nombre,
                        }

    # Procesar cada requisito
    grupos_procesados = set()

    for req in requisitos:
        curso = req.curso
        cid = str(curso.id)
        reg = registros_por_curso.get(cid)

        # Si es parte de un grupo alternativo, manejar como grupo
        if req.grupo_alternativo:
            if req.grupo_alternativo in grupos_procesados:
                continue  # Ya se procesó este grupo
            grupos_procesados.add(req.grupo_alternativo)

            cursos_grupo = [r for r in requisitos if r.grupo_alternativo == req.grupo_alternativo]
            nombres_grupo = " / ".join(r.curso.nombre for r in cursos_grupo)

            if req.grupo_alternativo in grupos_satisfechos:
                info_alt = grupos_satisfechos[req.grupo_alternativo]
                detalles.append({
                    "tipo": DetalleCumplimientoRequisito.TipoRequisito.FORMACION,
                    "desc": f"Formación obligatoria (alternativa): {nombres_grupo}",
                    "cumple": DetalleCumplimientoRequisito.Cumple.SI,
                    "obs": f"Cumple con '{info_alt['curso_nombre']}' (cualquiera del grupo es suficiente).",
                })
                cursos_cumplidos.append({
                    "curso_id": info_alt["curso_id"],
                    "curso_nombre": info_alt["curso_nombre"],
                })
            else:
                detalles.append({
                    "tipo": DetalleCumplimientoRequisito.TipoRequisito.FORMACION,
                    "desc": f"Formación obligatoria (alternativa): {nombres_grupo}",
                    "cumple": DetalleCumplimientoRequisito.Cumple.NO,
                    "obs": f"No se encontró registro vigente de ningún curso alternativo ({nombres_grupo}).",
                })
                brechas.append({
                    "clasificacion": "incumplimiento",
                    "referencia_obj": req,
                    "descripcion": (
                        f"Curso obligatorio faltante o vencido para {trabajador.nombre} "
                        f"en cargo {perfil.nombre_cargo}: {nombres_grupo} (grupo alternativo)."
                    ),
                })
            continue

        # Curso individual
        if reg:
            if not reg.fecha_vencimiento:
                detalles.append({
                    "tipo": DetalleCumplimientoRequisito.TipoRequisito.FORMACION,
                    "desc": f"Formación obligatoria: {curso.nombre}",
                    "cumple": DetalleCumplimientoRequisito.Cumple.SI,
                    "obs": f"Vigente (realizado el {reg.fecha_realizacion}, sin vencimiento).",
                })
                cursos_cumplidos.append({"curso_id": cid, "curso_nombre": curso.nombre})
            elif reg.fecha_vencimiento < today:
                detalles.append({
                    "tipo": DetalleCumplimientoRequisito.TipoRequisito.FORMACION,
                    "desc": f"Formación obligatoria: {curso.nombre}",
                    "cumple": DetalleCumplimientoRequisito.Cumple.NO,
                    "obs": f"Curso vencido el {reg.fecha_vencimiento}. Requiere renovación.",
                })
                brechas.append({
                    "clasificacion": "incumplimiento",
                    "referencia_obj": reg,
                    "descripcion": (
                        f"Curso obligatorio '{curso.nombre}' vencido el {reg.fecha_vencimiento} "
                        f"para {trabajador.nombre} en cargo {perfil.nombre_cargo}."
                    ),
                })
            elif reg.fecha_vencimiento <= today + timedelta(days=30):
                detalles.append({
                    "tipo": DetalleCumplimientoRequisito.TipoRequisito.FORMACION,
                    "desc": f"Formación obligatoria: {curso.nombre}",
                    "cumple": DetalleCumplimientoRequisito.Cumple.SI,
                    "obs": f"Vigente, vence el {reg.fecha_vencimiento} (próximo a vencer, renovar pronto).",
                })
                cursos_cumplidos.append({"curso_id": cid, "curso_nombre": curso.nombre})
            else:
                detalles.append({
                    "tipo": DetalleCumplimientoRequisito.TipoRequisito.FORMACION,
                    "desc": f"Formación obligatoria: {curso.nombre}",
                    "cumple": DetalleCumplimientoRequisito.Cumple.SI,
                    "obs": f"Vigente hasta {reg.fecha_vencimiento}.",
                })
                cursos_cumplidos.append({"curso_id": cid, "curso_nombre": curso.nombre})
        else:
            detalles.append({
                "tipo": DetalleCumplimientoRequisito.TipoRequisito.FORMACION,
                "desc": f"Formación obligatoria: {curso.nombre}",
                "cumple": DetalleCumplimientoRequisito.Cumple.NO,
                "obs": f"No registra formación en '{curso.nombre}'.",
            })
            brechas.append({
                "clasificacion": "oportunidad_mejora",
                "referencia_obj": req,
                "descripcion": (
                    f"Curso obligatorio '{curso.nombre}' faltante "
                    f"para {trabajador.nombre} en cargo {perfil.nombre_cargo}."
                ),
            })

    return detalles, brechas, cursos_cumplidos


def _evaluar_competencias(trabajador, perfil):
    """
    Evalúa las competencias del cargo contra las últimas evaluaciones del trabajador.

    Criterios:
    - Cumple: nivel_alcanzado >= nivel_requerido
    - Parcial: le falta 1 nivel
    - No cumple: le faltan 2 o más niveles, o no hay evaluación

    Retorna:
        (detalles, brechas, comps_cumplidas)
    """
    from apps.formacion.models import EvaluacionCompetencia

    detalles = []
    brechas = []
    comps_cumplidas = []

    competencias = list(
        CargoCompetencia.objects.filter(perfil_cargo=perfil)
    )

    if not competencias:
        return detalles, brechas, comps_cumplidas

    for comp in competencias:
        nivel_req = parse_nivel(comp.nivel_requerido or comp.nivel, default=3)
        nombre_nivel_req = obtener_nombre_nivel(nivel_req)
        tipo_display = comp.get_tipo_display() if comp.tipo else "General"

        ultima_eval = (
            EvaluacionCompetencia.objects
            .filter(trabajador=trabajador, cargo_competencia=comp)
            .order_by("-fecha_evaluacion", "-created_at")
            .first()
        )

        if not ultima_eval:
            detalles.append({
                "tipo": DetalleCumplimientoRequisito.TipoRequisito.COMPETENCIA,
                "desc": f"Competencia ({tipo_display}): {comp.nombre}",
                "cumple": DetalleCumplimientoRequisito.Cumple.NO,
                "obs": f"Se requiere nivel {nivel_req} ({nombre_nivel_req}). Sin evaluación registrada.",
            })
            # La brecha en HBSEO se genera cuando existe una evaluación no aprobada
        else:
            nivel_alc = ultima_eval.nivel_alcanzado
            nombre_nivel_alc = obtener_nombre_nivel(nivel_alc)
            diferencia = nivel_req - nivel_alc

            if diferencia <= 0:
                detalles.append({
                    "tipo": DetalleCumplimientoRequisito.TipoRequisito.COMPETENCIA,
                    "desc": f"Competencia ({tipo_display}): {comp.nombre}",
                    "cumple": DetalleCumplimientoRequisito.Cumple.SI,
                    "obs": (
                        f"Nivel alcanzado: {nivel_alc} ({nombre_nivel_alc}) — "
                        f"cumple o supera el requerido ({nivel_req})."
                    ),
                })
                comps_cumplidas.append({"comp_id": str(comp.id), "comp_nombre": comp.nombre})
            elif diferencia == 1:
                detalles.append({
                    "tipo": DetalleCumplimientoRequisito.TipoRequisito.COMPETENCIA,
                    "desc": f"Competencia ({tipo_display}): {comp.nombre}",
                    "cumple": DetalleCumplimientoRequisito.Cumple.PARCIAL,
                    "obs": (
                        f"Nivel alcanzado: {nivel_alc} ({nombre_nivel_alc}) — "
                        f"requiere {nivel_req} ({nombre_nivel_req}). Brecha de 1 nivel."
                    ),
                })
                brechas.append({
                    "clasificacion": "oportunidad_mejora",
                    "referencia_obj": ultima_eval,
                    "descripcion": (
                        f"Brecha de competencia en '{comp.nombre}' ({tipo_display}): "
                        f"Nivel alcanzado {nivel_alc} vs requerido {nivel_req} (brecha: -1) "
                        f"para {trabajador.nombre} en cargo {perfil.nombre_cargo}."
                    ),
                })
            else:
                detalles.append({
                    "tipo": DetalleCumplimientoRequisito.TipoRequisito.COMPETENCIA,
                    "desc": f"Competencia ({tipo_display}): {comp.nombre}",
                    "cumple": DetalleCumplimientoRequisito.Cumple.NO,
                    "obs": (
                        f"Nivel alcanzado: {nivel_alc} ({nombre_nivel_alc}) — "
                        f"requiere {nivel_req} ({nombre_nivel_req}). Brecha de {diferencia} niveles."
                    ),
                })
                brechas.append({
                    "clasificacion": "incumplimiento",
                    "referencia_obj": ultima_eval,
                    "descripcion": (
                        f"Brecha crítica de competencia en '{comp.nombre}' ({tipo_display}): "
                        f"Nivel alcanzado {nivel_alc} vs requerido {nivel_req} (brecha: -{diferencia}) "
                        f"para {trabajador.nombre} en cargo {perfil.nombre_cargo}."
                    ),
                })

    return detalles, brechas, comps_cumplidas
