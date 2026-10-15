from datetime import datetime, timedelta
from django.utils import timezone

from dateutil.relativedelta import relativedelta
from django.db import transaction as db_transaction
from django.db.models import Count
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.common.mixins import EmpresaScopedViewSet
from apps.estandares.models import Evaluacion, Estandar, Respuesta
from apps.accounts.models import Usuario, UserRole
from apps.calendario.models import Notificacion
from .models import Hallazgo, PlanMejora
from .serializers import HallazgoSerializer, PlanMejoraSerializer


def calcular_fecha_limite(prioridad: str) -> datetime:
    """RN-05: urgente=3 meses, importante=6 meses, aceptable=12 meses."""
    meses_map = {"urgente": 3, "importante": 6, "aceptable": 12}
    return datetime.now() + relativedelta(months=meses_map.get(prioridad, 6))


class HallazgoViewSet(EmpresaScopedViewSet):
    """Se filtra por empresa a través de la evaluación (no tiene FK directa a empresa)."""
    queryset = Hallazgo.objects.select_related("evaluacion", "auditor", "estandar", "respuesta")
    serializer_class = HallazgoSerializer
    empresa_field = "evaluacion__empresa"

    def list(self, request, *args, **kwargs):
        """Retorna hallazgos del año actual envueltos con metadata."""
        empresa = request.user.empresa
        if not empresa:
            return Response({"hallazgos": [], "total": 0, "evaluacion_id": None})

        anio_actual = datetime.now().year
        evaluacion = Evaluacion.objects.filter(
            empresa=empresa, anio=anio_actual
        ).first()

        if not evaluacion:
            return Response({"hallazgos": [], "total": 0, "evaluacion_id": None})

        hallazgos = Hallazgo.objects.filter(
            evaluacion=evaluacion
        ).select_related("auditor", "estandar", "respuesta").order_by("-created_at")

        serializer = self.get_serializer(hallazgos, many=True)
        return Response({
            "hallazgos": serializer.data,
            "total": len(serializer.data),
            "evaluacion_id": str(evaluacion.id),
        })

    def create(self, request, *args, **kwargs):
        user = request.user
        empresa_user = getattr(user, "empresa", None)

        eval_id = request.data.get("evaluacion") or request.data.get("evaluacion_id")
        if not eval_id:
            return Response(
                {"error": "La evaluación es obligatoria.", "detail": "Debe especificar una evaluación válida."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            evaluacion = Evaluacion.objects.select_related("empresa").get(id=eval_id)
        except (Evaluacion.DoesNotExist, ValueError):
            return Response(
                {"error": "Evaluación no encontrada.", "detail": "La evaluación especificada no existe."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Multi-Tenant Validation & Permission Check
        if user.rol != UserRole.ADMIN:
            if not empresa_user or evaluacion.empresa_id != empresa_user.id:
                return Response(
                    {"error": "No autorizado.", "detail": "No tiene permisos para registrar hallazgos en la empresa de esta evaluación."},
                    status=status.HTTP_403_FORBIDDEN
                )

        descripcion = (request.data.get("descripcion") or "").strip()
        if not descripcion:
            return Response(
                {"error": "La descripción es obligatoria.", "detail": "Debe ingresar una descripción del hallazgo."},
                status=status.HTTP_400_BAD_REQUEST
            )

        tipo = request.data.get("tipo") or "observacion"
        valid_tipos = [c[0] for c in Hallazgo.Tipo.choices]
        if tipo not in valid_tipos:
            return Response(
                {"error": "Tipo de hallazgo inválido.", "detail": f"Los tipos válidos son: {', '.join(valid_tipos)}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Resolve Estandar & Respuesta
        estandar_obj = None
        estandar_ref = request.data.get("estandar") or request.data.get("estandar_id") or request.data.get("estandar_codigo")
        if estandar_ref:
            try:
                estandar_obj = Estandar.objects.filter(id=estandar_ref).first()
                if not estandar_obj:
                    estandar_obj = Estandar.objects.filter(codigo=estandar_ref).first()
            except Exception:
                estandar_obj = Estandar.objects.filter(codigo=estandar_ref).first()

        respuesta_obj = None
        if estandar_obj:
            respuesta_obj = Respuesta.objects.filter(evaluacion=evaluacion, estandar=estandar_obj).first()

        # Idempotency / Double submit check (3 seconds window)
        three_sec_ago = timezone.now() - timedelta(seconds=3)
        recent_duplicate = Hallazgo.objects.filter(
            evaluacion=evaluacion,
            auditor=user,
            tipo=tipo,
            descripcion=descripcion,
            estandar=estandar_obj,
            created_at__gte=three_sec_ago
        ).first()

        if recent_duplicate:
            serializer = self.get_serializer(recent_duplicate)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # Transaction Atomic: Create Hallazgo + Notificacion
        with db_transaction.atomic():
            hallazgo = Hallazgo.objects.create(
                evaluacion=evaluacion,
                auditor=user,
                estandar=estandar_obj,
                respuesta=respuesta_obj,
                descripcion=descripcion,
                tipo=tipo
            )

            # Notify Responsable SST users of company
            responsables = Usuario.objects.filter(empresa=evaluacion.empresa, rol=UserRole.RESPONSABLE, is_active=True)
            for resp in responsables:
                tipo_display = dict(Hallazgo.Tipo.choices).get(tipo, tipo)
                if estandar_obj:
                    msg = f"El Auditor ha registrado una observación/hallazgo ({tipo_display}) sobre el estándar {estandar_obj.codigo} ({estandar_obj.nombre}): \"{descripcion}\""
                else:
                    msg = f"El Auditor ha registrado una observación/hallazgo ({tipo_display}) en la autoevaluación: \"{descripcion}\""

                Notificacion.objects.create(
                    empresa=evaluacion.empresa,
                    usuario=resp,
                    tipo=Notificacion.Tipo.ALERTA,
                    nivel=Notificacion.Nivel.CRITICO if tipo == "no_conformidad" else Notificacion.Nivel.IMPORTANTE,
                    mensaje=msg,
                    leida=False
                )

        serializer = self.get_serializer(hallazgo)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        """SEC-01: Solo el auditor que creó el hallazgo puede editarlo."""
        instance = self.get_object()
        if instance.auditor_id != self.request.user.id:
            raise PermissionDenied("Solo el auditor que registró el hallazgo puede editarlo.")
        serializer.save()

    def perform_destroy(self, instance):
        """SEC-01: Solo el auditor que creó el hallazgo puede eliminarlo."""
        if instance.auditor_id != self.request.user.id:
            raise PermissionDenied("Solo el auditor que registró el hallazgo puede eliminarlo.")
        super().perform_destroy(instance)


class PlanMejoraViewSet(EmpresaScopedViewSet):
    queryset = PlanMejora.objects.select_related("evaluacion", "empresa")
    serializer_class = PlanMejoraSerializer
    filterset_fields = ["estado", "prioridad"]

    def list(self, request, *args, **kwargs):
        """Retorna planes envueltos con resumen, replicando la forma del Express original."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        planes = serializer.data

        empresa = request.user.empresa
        por_estado = list(
            PlanMejora.objects.filter(empresa=empresa, deleted_at__isnull=True)
            .values("estado")
            .annotate(_count=Count("id"))
        )

        return Response({
            "planes": planes,
            "resumen": {"por_estado": por_estado},
        })

    def perform_create(self, serializer):
        """RN-05: fecha_limite automática según prioridad."""
        prioridad = self.request.data.get("prioridad", "importante")
        serializer.save(
            empresa=self.request.user.empresa,
            fecha_limite=calcular_fecha_limite(prioridad),
        )

    def perform_update(self, serializer):
        """Si cambia la prioridad, recalcular fecha_limite."""
        nueva_prioridad = self.request.data.get("prioridad")
        instance = self.get_object()

        kwargs = {}
        if nueva_prioridad and nueva_prioridad != instance.prioridad:
            kwargs["fecha_limite"] = calcular_fecha_limite(nueva_prioridad)

        serializer.save(**kwargs)

    @action(detail=False, methods=["get"], url_path="resumen")
    def resumen(self, request):
        """GET /api/plan-mejora/resumen → conteos por estado y prioridad."""
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        por_estado = list(
            PlanMejora.objects.filter(empresa=empresa, deleted_at__isnull=True)
            .values("estado")
            .annotate(_count=Count("id"))
        )

        por_prioridad = list(
            PlanMejora.objects.filter(empresa=empresa, deleted_at__isnull=True)
            .exclude(estado="completado")
            .values("prioridad")
            .annotate(_count=Count("id"))
        )

        return Response({
            "por_estado": por_estado,
            "por_prioridad": por_prioridad,
        })
