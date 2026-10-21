from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.common.mixins import EmpresaScopedViewSet
from apps.common.permissions import IsRolParaEscritura
from apps.auditoria.helpers import registrar_audit_log
from apps.common.competencias import parse_nivel
from apps.hbseo.models import Brecha, BrechaEvento, BrechaAccion
from apps.formacion.models import (
    CursoFormacion,
    CargoRequisitoFormacion,
    RegistroFormacion,
    EvaluacionCompetencia,
)
from apps.perfilcargo.models import CargoCompetencia
from apps.michc.engine import recalcular_habilitacion

from .models import (
    AfiliacionTrabajador,
    Capacitacion,
    ParticipanteCapacitacion,
    PlanillaSeguridad,
    Trabajador,
)
from .serializers import (
    AfiliacionTrabajadorSerializer,
    CapacitacionSerializer,
    ParticipanteCapacitacionSerializer,
    PlanillaSeguridadSerializer,
    TrabajadorSerializer,
)


class TrabajadorViewSet(EmpresaScopedViewSet):
    queryset = Trabajador.objects.select_related("sede", "perfil_cargo")
    serializer_class = TrabajadorSerializer
    filterset_fields = ["activo", "tipo_vinculacion", "sede"]


class AfiliacionTrabajadorViewSet(viewsets.ModelViewSet):
    """Se filtra por empresa a través del trabajador."""
    serializer_class = AfiliacionTrabajadorSerializer

    def get_queryset(self):
        user = self.request.user
        qs = AfiliacionTrabajador.objects.select_related("trabajador")
        return qs if user.rol == "ADMIN" else qs.filter(trabajador__empresa=user.empresa)


class PlanillaSeguridadViewSet(EmpresaScopedViewSet):
    queryset = PlanillaSeguridad.objects.all()
    serializer_class = PlanillaSeguridadSerializer
    filterset_fields = ["periodo", "estado_pago"]


class CapacitacionViewSet(EmpresaScopedViewSet):
    queryset = Capacitacion.objects.select_related("curso", "competencia").prefetch_related("participantes__trabajador", "brechas")
    serializer_class = CapacitacionSerializer
    filterset_fields = ["estado", "curso", "competencia"]
    permission_classes = [IsAuthenticated, IsRolParaEscritura.de("responsable")]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        capacitaciones = serializer.data
        resumen = {
            "total": len(capacitaciones),
            "programadas": sum(1 for c in capacitaciones if c.get("estado") == "programada"),
            "realizadas": sum(1 for c in capacitaciones if c.get("estado") == "realizada"),
            "canceladas": sum(1 for c in capacitaciones if c.get("estado") == "cancelada"),
        }
        return Response({"capacitaciones": capacitaciones, "resumen": resumen})

    def perform_create(self, serializer):
        super().perform_create(serializer)
        instance = serializer.instance
        registrar_audit_log(
            self.request,
            "CREAR_CAPACITACION",
            tabla_afectada="capacitaciones",
            registro_id=instance.id,
            valores_nuevos={"tema": instance.tema, "objetivo": instance.objetivo},
        )

    def perform_update(self, serializer):
        old_data = {"estado": serializer.instance.estado, "tema": serializer.instance.tema}
        nuevo_estado = serializer.validated_data.get("estado")
        super().perform_update(serializer)
        instance = serializer.instance
        registrar_audit_log(
            self.request,
            "ACTUALIZAR_CAPACITACION",
            tabla_afectada="capacitaciones",
            registro_id=instance.id,
            valores_anteriores=old_data,
            valores_nuevos=serializer.validated_data,
        )
        # Si se transicionó a realizada via PATCH/PUT, disparar procesamiento de cierre
        if old_data["estado"] != Capacitacion.Estado.REALIZADA and nuevo_estado == Capacitacion.Estado.REALIZADA:
            self._procesar_finalizacion_capacitacion(instance, self.request.user)

    @action(detail=False, methods=["get"], url_path="sugerir-participantes")
    def sugerir_participantes(self, request):
        """
        Sugiere participantes automáticamente según:
        - Trabajadores con el curso requerido vencido o faltante.
        - Trabajadores con brechas abiertas asociadas.
        - Trabajadores con competencias pendientes de evaluar o con brecha.
        """
        empresa = request.user.empresa
        curso_id = request.query_params.get("curso_id")
        competencia_id = request.query_params.get("competencia_id")
        brecha_ids_param = request.query_params.get("brecha_ids")

        brecha_ids = [b.strip() for b in brecha_ids_param.split(",") if b.strip()] if brecha_ids_param else []

        today = timezone.localdate()
        sugerencias_map = {}  # {trabajador_id: {trabajador, motivos: []}}

        trabajadores_activos = list(
            Trabajador.objects.filter(empresa=empresa, activo=True)
            .select_related("perfil_cargo")
        )

        # 1. Sugerencia por Brechas específicas seleccionadas
        if brecha_ids:
            brechas_qs = Brecha.objects.filter(
                id__in=brecha_ids,
                empresa=empresa,
                trabajador__isnull=False
            ).select_related("trabajador")
            for b in brechas_qs:
                tid = str(b.trabajador_id)
                if tid not in sugerencias_map:
                    sugerencias_map[tid] = {
                        "trabajador": b.trabajador,
                        "motivos": [],
                    }
                sugerencias_map[tid]["motivos"].append(f"Brecha abierta {b.codigo}: {b.get_clasificacion_display()}")

        # 2. Sugerencia por Curso del Catálogo
        if curso_id:
            try:
                curso = CursoFormacion.objects.get(id=curso_id, empresa=empresa)
                # Cargos que exigen este curso
                perfiles_exigen = set(
                    CargoRequisitoFormacion.objects.filter(
                        curso=curso,
                        obligatorio=True
                    ).values_list("perfil_cargo_id", flat=True)
                )

                for t in trabajadores_activos:
                    if t.perfil_cargo_id in perfiles_exigen:
                        tid = str(t.id)
                        # Verificar registro de formación
                        ultimo_reg = (
                            RegistroFormacion.objects.filter(trabajador=t, curso=curso)
                            .order_by("-fecha_realizacion", "-created_at")
                            .first()
                        )
                        motivo = None
                        if not ultimo_reg:
                            motivo = f"Curso obligatorio '{curso.nombre}' faltante"
                        elif ultimo_reg.fecha_vencimiento and ultimo_reg.fecha_vencimiento < today:
                            motivo = f"Curso obligatorio '{curso.nombre}' vencido el {ultimo_reg.fecha_vencimiento}"
                        elif ultimo_reg.fecha_vencimiento and ultimo_reg.fecha_vencimiento <= today + timedelta(days=30):
                            motivo = f"Curso obligatorio '{curso.nombre}' por vencer el {ultimo_reg.fecha_vencimiento}"

                        if motivo:
                            if tid not in sugerencias_map:
                                sugerencias_map[tid] = {"trabajador": t, "motivos": []}
                            sugerencias_map[tid]["motivos"].append(motivo)
            except CursoFormacion.DoesNotExist:
                pass

        # 3. Sugerencia por Competencia
        if competencia_id:
            try:
                comp = CargoCompetencia.objects.get(id=competencia_id)
                perfil_comp_id = comp.perfil_cargo_id
                req_nivel = parse_nivel(comp.nivel_requerido or comp.nivel, default=3)

                for t in trabajadores_activos:
                    if t.perfil_cargo_id == perfil_comp_id:
                        tid = str(t.id)
                        ultima_eval = (
                            EvaluacionCompetencia.objects.filter(trabajador=t, cargo_competencia=comp)
                            .order_by("-fecha_evaluacion", "-created_at")
                            .first()
                        )
                        motivo = None
                        if not ultima_eval:
                            motivo = f"Competencia '{comp.nombre}' sin evaluar (requiere nivel {req_nivel})"
                        elif ultima_eval.nivel_alcanzado < req_nivel:
                            motivo = f"Brecha en competencia '{comp.nombre}': nivel {ultima_eval.nivel_alcanzado} vs {req_nivel} requerido"

                        if motivo:
                            if tid not in sugerencias_map:
                                sugerencias_map[tid] = {"trabajador": t, "motivos": []}
                            sugerencias_map[tid]["motivos"].append(motivo)
            except CargoCompetencia.DoesNotExist:
                pass

        resultado = [
            {
                "trabajador_id": tid,
                "nombre": data["trabajador"].nombre,
                "documento": data["trabajador"].documento,
                "cargo": data["trabajador"].cargo or (data["trabajador"].perfil_cargo.nombre_cargo if data["trabajador"].perfil_cargo else "Sin cargo"),
                "motivos": data["motivos"],
                "motivo_principal": data["motivos"][0] if data["motivos"] else "Requerido por perfil",
            }
            for tid, data in sugerencias_map.items()
        ]

        return Response(resultado)

    @action(detail=True, methods=["post"], url_path="inscribir-participantes")
    def inscribir_participantes(self, request, pk=None):
        """Inscribe uno o más trabajadores en la capacitación."""
        capacitacion = self.get_object()
        trabajadores_ids = request.data.get("trabajadores_ids", [])
        if not trabajadores_ids:
            return Response({"error": "Debe proporcionar una lista de IDs de trabajadores"}, status=status.HTTP_400_BAD_REQUEST)

        creados = 0
        with transaction.atomic():
            for tid in trabajadores_ids:
                trabajador = Trabajador.objects.filter(id=tid, empresa=capacitacion.empresa).first()
                if trabajador:
                    _, created = ParticipanteCapacitacion.objects.get_or_create(
                        capacitacion=capacitacion,
                        trabajador=trabajador,
                    )
                    if created:
                        creados += 1

            capacitacion.num_asistentes = capacitacion.participantes.count()
            capacitacion.save(update_fields=["num_asistentes"])

        registrar_audit_log(
            request,
            "INSCRIBIR_PARTICIPANTES_CAPACITACION",
            tabla_afectada="participantes_capacitacion",
            registro_id=capacitacion.id,
            valores_nuevos={"total_inscritos": capacitacion.participantes.count(), "nuevos": creados},
        )

        capacitacion = self.get_queryset().get(id=capacitacion.id)
        serializer = self.get_serializer(capacitacion)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="registrar-asistencia")
    def registrar_asistencia(self, request, pk=None):
        """
        Registra la asistencia individual de los participantes, soporte y evaluación.
        Payload esperado:
        {
          "participantes": [
            {
              "trabajador_id": "uuid",
              "asistio": true,
              "certificado_url": "https://...",
              "soporte_id": "uuid",
              "nota_evaluacion": 4.5,
              "nivel_alcanzado": 4,
              "observaciones": "..."
            }
          ]
        }
        """
        capacitacion = self.get_object()
        participantes_data = request.data.get("participantes", [])
        if not isinstance(participantes_data, list):
            return Response({"error": "Formato de participantes inválido"}, status=status.HTTP_400_BAD_REQUEST)

        actualizados = 0
        with transaction.atomic():
            for item in participantes_data:
                tid = item.get("trabajador_id")
                part = ParticipanteCapacitacion.objects.filter(capacitacion=capacitacion, trabajador_id=tid).first()
                if not part:
                    # Si no estaba inscrito previamente, inscribirlo
                    trabajador = Trabajador.objects.filter(id=tid, empresa=capacitacion.empresa).first()
                    if trabajador:
                        part = ParticipanteCapacitacion.objects.create(capacitacion=capacitacion, trabajador=trabajador)

                if part:
                    if "asistio" in item:
                        part.asistio = bool(item["asistio"])
                    if "certificado_url" in item:
                        part.certificado_url = item["certificado_url"]
                    if "soporte_id" in item:
                        part.soporte_id = item["soporte_id"]
                    if "nota_evaluacion" in item and item["nota_evaluacion"] is not None:
                        part.nota_evaluacion = item["nota_evaluacion"]
                    if "nivel_alcanzado" in item and item["nivel_alcanzado"] is not None:
                        part.nivel_alcanzado = item["nivel_alcanzado"]
                    if "observaciones" in item:
                        part.observaciones = item["observaciones"]
                    part.save()
                    actualizados += 1

            total_asistentes = capacitacion.participantes.filter(asistio=True).count()
            capacitacion.num_asistentes = total_asistentes
            capacitacion.save(update_fields=["num_asistentes"])

        registrar_audit_log(
            request,
            "REGISTRAR_ASISTENCIA_CAPACITACION",
            tabla_afectada="participantes_capacitacion",
            registro_id=capacitacion.id,
            valores_nuevos={"actualizados": actualizados, "asistentes": total_asistentes},
        )

        capacitacion = self.get_queryset().get(id=capacitacion.id)
        serializer = self.get_serializer(capacitacion)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="finalizar")
    def finalizar_capacitacion(self, request, pk=None):
        """
        Marca la capacitación como REALIZADA y ejecuta el cierre de brechas:
        1. Para cada asistente, crea o actualiza su RegistroFormacion.
        2. Si cubre competencia, registra la EvaluacionCompetencia.
        3. Verifica y subsana brechas abiertas de HBSEO ligadas.
        4. Dispara recálculo de MICHC para todos los participantes.
        """
        capacitacion = self.get_object()
        capacitacion.estado = Capacitacion.Estado.REALIZADA
        capacitacion.save(update_fields=["estado"])

        self._procesar_finalizacion_capacitacion(capacitacion, request.user)

        capacitacion = self.get_queryset().get(id=capacitacion.id)
        serializer = self.get_serializer(capacitacion)
        return Response(serializer.data)

    def _procesar_finalizacion_capacitacion(self, capacitacion, usuario):
        """Lógica central de impacto en expediente, MICHC y HBSEO al realizarse una capacitación."""
        participantes_asistentes = list(
            capacitacion.participantes.filter(asistio=True)
            .select_related("trabajador", "soporte")
        )

        fecha_realizacion = capacitacion.fecha.date() if hasattr(capacitacion.fecha, 'date') else capacitacion.fecha
        today = timezone.localdate()

        with transaction.atomic():
            for part in participantes_asistentes:
                trabajador = part.trabajador

                # 1. Crear o actualizar RegistroFormacion si cubre curso
                if capacitacion.curso:
                    origen = (
                        RegistroFormacion.Origen.PROVEEDOR_EXTERNO
                        if capacitacion.proveedor
                        else RegistroFormacion.Origen.CAPACITACION_INTERNA
                    )
                    reg, created = RegistroFormacion.objects.get_or_create(
                        trabajador=trabajador,
                        curso=capacitacion.curso,
                        fecha_realizacion=fecha_realizacion,
                        defaults={
                            "soporte": part.soporte,
                            "origen": origen,
                            "entidad_emisora": capacitacion.proveedor or capacitacion.empresa.nombre,
                            "horas_duracion": capacitacion.horas_duracion,
                            "observaciones": f"Generado automáticamente tras capacitación: {capacitacion.tema}",
                        }
                    )
                    if not created:
                        reg.soporte = part.soporte or reg.soporte
                        reg.horas_duracion = capacitacion.horas_duracion or reg.horas_duracion
                        reg.save()

                # 2. Reevaluación de Competencia si aplica
                if capacitacion.competencia and part.nivel_alcanzado:
                    EvaluacionCompetencia.objects.create(
                        trabajador=trabajador,
                        cargo_competencia=capacitacion.competencia,
                        nivel_alcanzado=part.nivel_alcanzado,
                        fecha_evaluacion=fecha_realizacion,
                        evaluado_por=usuario if getattr(usuario, "is_authenticated", False) else None,
                        rol_evaluador=EvaluacionCompetencia.RolEvaluador.GESTION_HUMANA,
                        metodo=(
                            EvaluacionCompetencia.MetodoEvaluacion.CERTIFICACION
                            if capacitacion.proveedor
                            else EvaluacionCompetencia.MetodoEvaluacion.PRUEBA_TECNICA
                        ),
                        soporte_archivo=part.soporte,
                        observacion=f"Reevaluación de competencia tras capacitación '{capacitacion.tema}'",
                    )

                # 3. Recalcular habilitación en MICHC para el trabajador
                recalcular_habilitacion(trabajador.id)

            # 4. Procesar Brechas ligadas a la capacitación
            brechas_ligadas = list(capacitacion.brechas.filter(
                estado__in=[Brecha.Estado.DETECTADA, Brecha.Estado.EN_TRATAMIENTO, Brecha.Estado.CONTROLADA]
            ))

            for brecha in brechas_ligadas:
                brecha_subsanada = False
                motivo_cierre = ""

                if capacitacion.curso:
                    # Si el trabajador de la brecha asistió y tiene curso vigente
                    if not brecha.trabajador or any(p.trabajador_id == brecha.trabajador_id for p in participantes_asistentes):
                        brecha_subsanada = True
                        motivo_cierre = f"Curso obligatorio '{capacitacion.curso.nombre}' completado y vigente mediante capacitación '{capacitacion.tema}'."

                elif capacitacion.competencia:
                    # Verificar si la reevaluación alcanzó el nivel requerido
                    part = next((p for p in participantes_asistentes if p.trabajador_id == brecha.trabajador_id), None)
                    nivel_req = parse_nivel(capacitacion.competencia.nivel_requerido or capacitacion.competencia.nivel, default=3)
                    if part and part.nivel_alcanzado and part.nivel_alcanzado >= nivel_req:
                        brecha_subsanada = True
                        motivo_cierre = f"Competencia '{capacitacion.competencia.nombre}' superó el nivel requerido L{nivel_req} (alcanzado: L{part.nivel_alcanzado})."
                    else:
                        # No alcanzó el nivel esperado -> Sugerir nueva acción
                        nivel_alc = part.nivel_alcanzado if part else "no registrado"
                        BrechaAccion.objects.create(
                            brecha=brecha,
                            descripcion=f"Programar refuerzo o re-evaluación para '{capacitacion.tema}'. Nivel L{nivel_alc} inferior a L{nivel_req}.",
                            fecha_programada=today + timedelta(days=30),
                        )
                        BrechaEvento.objects.create(
                            brecha=brecha,
                            tipo_evento=BrechaEvento.TipoEvento.PROXIMA_ACCION,
                            descripcion=f"Capacitación realizada pero no subsanó la brecha de competencia (nivel alcanzado: L{nivel_alc} vs L{nivel_req} requerido). Nueva acción programada.",
                            usuario=usuario if getattr(usuario, "is_authenticated", False) else None,
                        )

                else:
                    # Capacitación general que cierra la brecha
                    brecha_subsanada = True
                    motivo_cierre = f"Capacitación realizada satisfactoriamente: '{capacitacion.tema}'."

                if brecha_subsanada:
                    brecha.estado = Brecha.Estado.SUBSANADA
                    brecha.save(update_fields=["estado"])
                    BrechaEvento.objects.create(
                        brecha=brecha,
                        tipo_evento=BrechaEvento.TipoEvento.CAMBIO_ESTADO,
                        descripcion=f"Brecha subsanada tras realización de capacitación: {motivo_cierre}",
                        usuario=usuario if getattr(usuario, "is_authenticated", False) else None,
                    )


class ParticipanteCapacitacionViewSet(viewsets.ModelViewSet):
    serializer_class = ParticipanteCapacitacionSerializer

    def get_queryset(self):
        user = self.request.user
        qs = ParticipanteCapacitacion.objects.select_related("capacitacion", "trabajador", "soporte")
        return qs if user.rol == "ADMIN" else qs.filter(capacitacion__empresa=user.empresa)
