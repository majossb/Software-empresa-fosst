from datetime import datetime
from decimal import Decimal

from django.db.models import Sum
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.mixins import EmpresaScopedViewSet
from .models import Estandar, Evaluacion, Respuesta, Apelacion
from .serializers import (
    EstandarSerializer,
    EvaluacionSerializer,
    RespuestaSerializer,
    ApelacionSerializer,
)


def obtener_capitulo_empresa(empresa):
    if empresa.capitulo_vigente in ("I", "II", "III"):
        return empresa.capitulo_vigente
    from apps.empresas.views import clasificar_capitulo
    cap = clasificar_capitulo(empresa.num_trabajadores, empresa.nivel_riesgo)
    empresa.capitulo_vigente = cap
    empresa.save(update_fields=["capitulo_vigente"])
    return cap


# ── GET /api/estandares/ ──────────────────────────────────────────
class EstandarListView(APIView):
    """Lista estándares del capítulo vigente de la empresa."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        capitulo = obtener_capitulo_empresa(empresa)
        estandares = Estandar.objects.filter(capitulo=capitulo).order_by("ciclo_phva", "codigo")
        serializer = EstandarSerializer(estandares, many=True)
        return Response(serializer.data)


# ── GET /api/estandares/respuestas ────────────────────────────────
class EstandaresConRespuestasView(APIView):
    """Estándares + respuestas de la evaluación del año actual."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        anio_actual = datetime.now().year
        capitulo = obtener_capitulo_empresa(empresa)

        # Obtener o crear evaluación del año actual
        evaluacion, _ = Evaluacion.objects.get_or_create(
            empresa=empresa,
            anio=anio_actual,
            defaults={"capitulo": capitulo},
        )

        estandares = Estandar.objects.filter(capitulo=capitulo).order_by("ciclo_phva", "codigo")
        respuestas = (
            Respuesta.objects.filter(evaluacion=evaluacion)
            .select_related("estandar")
            .prefetch_related("evidencias")
        )

        # Indexar respuestas por estandar_id para O(1) lookup
        resp_map = {str(r.estandar_id): r for r in respuestas}

        resultado = []
        for est in estandares:
            resp = resp_map.get(str(est.id))
            evidencias_count = 0
            if resp and hasattr(resp, "evidencias"):
                evidencias_count = resp.evidencias.count()

            puntaje_est = float(resp.puntaje or 0) if (resp and resp.puntaje) else 0.0
            max_est = float(est.puntaje_maximo)
            porcentaje = round((puntaje_est / max_est) * 100) if max_est > 0 else 0

            resultado.append({
                "estandar_id": str(est.id),
                "codigo": est.codigo,
                "nombre": est.nombre,
                "descripcion": est.descripcion,
                "ciclo_phva": est.ciclo_phva,
                "puntaje_maximo": max_est,
                "obligatorio": est.obligatorio,
                "respuesta_id": str(resp.id) if resp else None,
                "estado": resp.estado if resp else "sin_respuesta",
                "puntaje": puntaje_est,
                "observacion": resp.observacion if resp else "",
                "evidencias": evidencias_count,
                "porcentaje": porcentaje,
            })

        return Response({
            "evaluacion_id": str(evaluacion.id),
            "capitulo": capitulo,
            "estandares": resultado,
        })


# ── PUT /api/estandares/respuesta/<estandar_id> ──────────────────
class ActualizarRespuestaView(APIView):
    """Crear o actualizar la respuesta de un estándar."""
    permission_classes = [IsAuthenticated]

    def put(self, request, estandar_id):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        estado = request.data.get("estado")
        observacion = request.data.get("observacion", "")
        puntaje = request.data.get("puntaje")

        # Verificar que el estándar existe
        try:
            estandar = Estandar.objects.get(id=estandar_id)
        except Estandar.DoesNotExist:
            return Response({"message": "Estándar no encontrado."}, status=404)

        anio_actual = datetime.now().year
        capitulo = empresa.capitulo_vigente or "II"

        # Obtener o crear evaluación
        evaluacion, _ = Evaluacion.objects.get_or_create(
            empresa=empresa,
            anio=anio_actual,
            defaults={"capitulo": capitulo},
        )

        # Calcular puntaje automático si no se envía
        if puntaje is None:
            max_pts = float(estandar.puntaje_maximo)
            puntaje_map = {
                "cumple": max_pts,
                "parcial": max_pts * 0.5,
                "no_aplica": max_pts,
            }
            puntaje_final = Decimal(str(puntaje_map.get(estado, 0)))
        else:
            puntaje_final = Decimal(str(puntaje))

        # Upsert de respuesta
        respuesta, created = Respuesta.objects.update_or_create(
            evaluacion=evaluacion,
            estandar=estandar,
            defaults={
                "estado": estado,
                "observacion": observacion,
                "puntaje": puntaje_final,
            },
        )

        # Recalcular puntaje total — SOLO respuestas del capítulo vigente de la empresa.
        # Esto garantiza que tras una transición de capítulo el puntaje sea coherente
        # y no mezcle respuestas de capítulos anteriores con las del capítulo actual.
        capitulo_activo = empresa.capitulo_vigente or evaluacion.capitulo
        puntaje_total = (
            Respuesta.objects.filter(
                evaluacion=evaluacion,
                estandar__capitulo=capitulo_activo,
            )
            .aggregate(total=Sum("puntaje"))["total"]
            or 0
        )
        evaluacion.puntaje_total = puntaje_total
        evaluacion.save(update_fields=["puntaje_total"])

        serializer = RespuestaSerializer(respuesta)
        return Response({
            "respuesta": serializer.data,
            "puntaje_total_evaluacion": float(puntaje_total),
        })


# ── GET /api/evaluaciones/actual ──────────────────────────────────
class EvaluacionActualView(APIView):
    """Obtiene la evaluación del año actual (la crea si no existe)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        anio_actual = datetime.now().year
        capitulo = empresa.capitulo_vigente or "II"

        evaluacion, _ = Evaluacion.objects.get_or_create(
            empresa=empresa,
            anio=anio_actual,
            defaults={"capitulo": capitulo},
        )

        serializer = EvaluacionSerializer(evaluacion)
        return Response(serializer.data)


# ── GET /api/evaluaciones/historial ───────────────────────────────
class HistorialEvaluacionesView(APIView):
    """Historial de evaluaciones de la empresa."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        evaluaciones = Evaluacion.objects.filter(empresa=empresa).order_by("-anio")
        data = []
        for ev in evaluaciones:
            data.append({
                "id": str(ev.id),
                "anio": ev.anio,
                "capitulo": ev.capitulo,
                "puntaje_total": float(ev.puntaje_total) if ev.puntaje_total else None,
                "estado": ev.estado,
                "fecha_completado": ev.fecha_completado.isoformat() if ev.fecha_completado else None,
                "created_at": ev.created_at.isoformat() if ev.created_at else None,
                "respuestas_count": ev.respuestas.count(),
                "hallazgos_count": ev.hallazgos.count() if hasattr(ev, "hallazgos") else 0,
            })
        return Response(data)


# ── GET /api/evaluaciones/<id>/resumen ────────────────────────────
class ResumenEvaluacionView(APIView):
    """Resumen de una evaluación específica."""
    permission_classes = [IsAuthenticated]

    def get(self, request, evaluacion_id):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        try:
            evaluacion = Evaluacion.objects.prefetch_related(
                "respuestas__estandar"
            ).get(id=evaluacion_id, empresa=empresa)
        except Evaluacion.DoesNotExist:
            return Response({"message": "Evaluación no encontrada."}, status=404)

        respuestas = evaluacion.respuestas.all()
        puntaje_maximo = sum(float(r.estandar.puntaje_maximo) for r in respuestas)
        puntaje_obtenido = sum(float(r.puntaje or 0) for r in respuestas)

        serializer = EvaluacionSerializer(evaluacion)
        return Response({
            **serializer.data,
            "resumen": {
                "puntaje_maximo": puntaje_maximo,
                "puntaje_obtenido": puntaje_obtenido,
                "porcentaje": round((puntaje_obtenido / puntaje_maximo) * 100) if puntaje_maximo > 0 else 0,
                "total_respuestas": len(respuestas),
                "cumple": sum(1 for r in respuestas if r.estado == "cumple"),
                "no_cumple": sum(1 for r in respuestas if r.estado == "no_cumple"),
                "parcial": sum(1 for r in respuestas if r.estado == "parcial"),
            },
        })


# ── ViewSet de Apelaciones ────────────────────────────────────────
class ApelacionViewSet(EmpresaScopedViewSet):
    queryset = Apelacion.objects.select_related("respuesta__estandar", "respuesta__evaluacion", "solicitante")
    serializer_class = ApelacionSerializer
    empresa_field = "respuesta__evaluacion__empresa"

    def create(self, request, *args, **kwargs):
        empresa = request.user.empresa
        if not empresa:
            return Response(
                {"success": False, "code": "PERMISSION_DENIED", "message": "El usuario no tiene una empresa asociada."},
                status=status.HTTP_403_FORBIDDEN,
            )

        respuesta_id = request.data.get("respuesta")
        if not respuesta_id:
            return Response(
                {"success": False, "code": "VALIDATION_ERROR", "message": "Debe especificar la respuesta a apelar."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            respuesta = Respuesta.objects.select_related("evaluacion").get(id=respuesta_id)
        except (Respuesta.DoesNotExist, ValueError):
            return Response(
                {"success": False, "code": "RESOURCE_NOT_FOUND", "message": "La respuesta especificada no existe."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Multi-Tenant Isolation: Ensure respuesta belongs to user's company
        if respuesta.evaluacion.empresa_id != empresa.id:
            return Response(
                {"success": False, "code": "PERMISSION_DENIED", "message": "No tiene permiso para apelar observaciones de otra empresa."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Prevent duplicate active appeals for same response
        if Apelacion.objects.filter(respuesta=respuesta, estado=Apelacion.Estado.PENDIENTE).exists():
            return Response(
                {"success": False, "code": "APPEAL_ALREADY_PENDING", "message": "Ya existe una apelación pendiente para este estándar."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        apelacion = serializer.save(solicitante=request.user)

        # Notify Auditor(s) of company about new appeal
        from apps.accounts.models import Usuario, UserRole
        from apps.calendario.models import Notificacion
        auditores = Usuario.objects.filter(
            empresa=empresa,
            rol=UserRole.AUDITOR,
            is_active=True
        )
        for aud in auditores:
            Notificacion.objects.create(
                empresa=empresa,
                usuario=aud,
                tipo=Notificacion.Tipo.ALERTA,
                nivel=Notificacion.Nivel.IMPORTANTE,
                mensaje=f"🔔 Nueva apelación de Responsable SST sobre el estándar {respuesta.estandar.codigo} ({respuesta.estandar.nombre}): \"{apelacion.motivo}\"",
                leida=False
            )

        # Registro en AuditLog
        from apps.auditoria.models import AuditLog
        from apps.empresas.views import get_ip
        AuditLog.objects.create(
            usuario=request.user,
            empresa=empresa,
            accion="CREAR_APELACION",
            tabla_afectada="apelaciones",
            registro_id=str(apelacion.id),
            valores_nuevos={"motivo": apelacion.motivo, "respuesta_id": str(respuesta.id)},
            ip=get_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            ruta=request.path,
            metodo_http=request.method,
        )

        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "success": True,
                "message": "Apelación presentada exitosamente.",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @action(detail=True, methods=["post"], url_path="resolver")
    def resolver(self, request, pk=None):
        from apps.accounts.models import UserRole
        if getattr(request.user, "rol", None) not in [UserRole.AUDITOR, UserRole.ADMIN] and not getattr(request.user, "is_superuser", False):
            return Response(
                {"success": False, "code": "PERMISSION_DENIED", "message": "Solo auditores o administradores pueden resolver apelaciones."},
                status=status.HTTP_403_FORBIDDEN,
            )

        apelacion = self.get_object()
        empresa = request.user.empresa or apelacion.respuesta.evaluacion.empresa

        decision = str(request.data.get("decision") or request.data.get("estado") or "resuelta").lower()
        respuesta_auditor = str(request.data.get("respuesta_auditor", "")).strip()

        if decision not in ["resuelta", "aceptada", "rechazada"]:
            return Response(
                {"success": False, "code": "VALIDATION_ERROR", "message": "La decisión debe ser 'aceptada', 'rechazada' o 'resuelta'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        estado_previo = apelacion.estado
        apelacion.estado = decision
        if respuesta_auditor:
            apelacion.respuesta_auditor = respuesta_auditor
        apelacion.save(update_fields=["estado", "respuesta_auditor", "updated_at"])

        # Update standard response state if appeal is accepted
        respuesta = apelacion.respuesta
        evaluacion = respuesta.evaluacion
        nuevo_estado = request.data.get("nuevo_estado")

        if decision == "aceptada":
            if nuevo_estado in ["cumple", "no_cumple", "parcial", "no_aplica"]:
                respuesta.estado = nuevo_estado
            else:
                respuesta.estado = Respuesta.Estado.CUMPLE

            if respuesta.estado == Respuesta.Estado.CUMPLE:
                respuesta.puntaje = respuesta.estandar.puntaje_maximo
            elif respuesta.estado == Respuesta.Estado.PARCIAL:
                respuesta.puntaje = float(respuesta.estandar.puntaje_maximo) / 2
            elif respuesta.estado in [Respuesta.Estado.NO_CUMPLE, Respuesta.Estado.NO_APLICA]:
                respuesta.puntaje = 0

            respuesta.save()

            # Recalculate evaluation score
            capitulo_vigente = evaluacion.empresa.capitulo_vigente or evaluacion.capitulo or "II"
            respuestas_vigentes = Respuesta.objects.filter(
                evaluacion=evaluacion,
                estandar__capitulo=capitulo_vigente
            )
            total_puntaje = sum(float(r.puntaje or 0) for r in respuestas_vigentes)
            evaluacion.puntaje_total = total_puntaje
            evaluacion.save(update_fields=["puntaje_total", "updated_at"])

        # Notify Responsable SST of resolution
        from apps.accounts.models import Usuario, UserRole
        from apps.calendario.models import Notificacion
        destinatarios = list(Usuario.objects.filter(
            empresa=evaluacion.empresa,
            rol=UserRole.RESPONSABLE,
            is_active=True
        ))
        if apelacion.solicitante and apelacion.solicitante not in destinatarios:
            destinatarios.append(apelacion.solicitante)

        for dest in destinatarios:
            Notificacion.objects.create(
                empresa=evaluacion.empresa,
                usuario=dest,
                tipo=Notificacion.Tipo.INFORMATIVA,
                nivel=Notificacion.Nivel.IMPORTANTE,
                mensaje=f"🔔 Apelación resuelta ({decision.upper()}) sobre el estándar {respuesta.estandar.codigo} ({respuesta.estandar.nombre}). Respuesta Auditor: \"{respuesta_auditor or 'Sin comentarios adicionales.'}\"",
                leida=False
            )

        from apps.auditoria.models import AuditLog
        from apps.empresas.views import get_ip
        AuditLog.objects.create(
            usuario=request.user,
            empresa=empresa,
            accion="RESOLVER_APELACION",
            tabla_afectada="apelaciones",
            registro_id=str(apelacion.id),
            valores_anteriores={"estado": estado_previo},
            valores_nuevos={"estado": apelacion.estado, "respuesta_auditor": apelacion.respuesta_auditor},
            ip=get_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            ruta=request.path,
            metodo_http=request.method,
        )

        serializer = self.get_serializer(apelacion)
        return Response({
            "success": True,
            "message": f"Apelación {decision} exitosamente.",
            "data": serializer.data,
        })



# ── GET /api/evaluaciones/actual/respuestas-historicas ───────────
class RespuestasHistoricasEvaluacionView(APIView):
    """
    Devuelve TODAS las respuestas de la evaluación activa (sin filtrar por
    capítulo), etiquetando cada una con el capítulo al que pertenece su
    estándar.  Permite visualizar respuestas registradas bajo capítulos
    anteriores después de una transición RF-USR-03.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response(
                {"success": False, "code": "RESOURCE_NOT_FOUND", "message": "Sin empresa asociada."},
                status=400,
            )

        anio_actual = datetime.now().year
        capitulo_vigente = empresa.capitulo_vigente or "II"

        try:
            evaluacion = Evaluacion.objects.get(empresa=empresa, anio=anio_actual)
        except Evaluacion.DoesNotExist:
            return Response(
                {
                    "success": True,
                    "evaluacion_id": None,
                    "capitulo_vigente": capitulo_vigente,
                    "respuestas": [],
                    "total": 0,
                }
            )

        respuestas_qs = (
            Respuesta.objects.filter(evaluacion=evaluacion)
            .select_related("estandar")
            .order_by("estandar__capitulo", "estandar__ciclo_phva", "estandar__codigo")
        )

        data = []
        for r in respuestas_qs:
            es_capitulo_vigente = r.estandar.capitulo == capitulo_vigente
            data.append({
                "respuesta_id": str(r.id),
                "estandar_id": str(r.estandar.id),
                "codigo": r.estandar.codigo,
                "nombre": r.estandar.nombre,
                "ciclo_phva": r.estandar.ciclo_phva,
                "puntaje_maximo": float(r.estandar.puntaje_maximo),
                "estado": r.estado,
                "puntaje": float(r.puntaje or 0),
                "observacion": r.observacion or "",
                # Etiqueta explícita del capítulo al que pertenece el estándar
                "capitulo_estandar": r.estandar.capitulo,
                # Indica si esta respuesta cuenta para el capítulo actualmente vigente
                "es_capitulo_vigente": es_capitulo_vigente,
                "updated_at": r.updated_at.isoformat() if hasattr(r, "updated_at") and r.updated_at else None,
            })

        return Response({
            "success": True,
            "evaluacion_id": str(evaluacion.id),
            "capitulo_vigente": capitulo_vigente,
            "respuestas": data,
            "total": len(data),
        })

