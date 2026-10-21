from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin

from apps.calendario.models import Notificacion
from apps.common.mixins import EmpresaScopedViewSet
from apps.planes.mixins import PlanGatingMixin
from apps.accounts.models import UserRole
from .models import ReglaAlerta
from .serializers import ReglaAlertaSerializer, NotificacionSerializer
from .services import evaluar_reglas_alertas


class ReglaAlertaViewSet(PlanGatingMixin, EmpresaScopedViewSet):
    """
    Gestión de reglas de alerta por empresa (o consulta de reglas globales).
    """
    queryset = ReglaAlerta.objects.all()
    serializer_class = ReglaAlertaSerializer
    filterset_fields = ["modelo_origen", "activa", "nivel_criticidad"]
    required_feature = "tiene_alertas_email"

    def get_queryset(self):
        user = self.request.user
        if user.rol == UserRole.ADMIN:
            return ReglaAlerta.objects.all()
        # Ver reglas globales + reglas específicas de la empresa
        return ReglaAlerta.objects.filter(Q(empresa=user.empresa) | Q(empresa__isnull=True))

    @action(detail=False, methods=["post"], url_path="ejecutar-revision")
    def ejecutar_revision(self, request):
        """Dispara manualmente la revisión de vencimientos para la empresa."""
        empresa = request.user.empresa
        total = evaluar_reglas_alertas(empresa=empresa)
        return Response({
            "mensaje": f"Revisión completada exitosamente. Se generaron {total} alerta(s).",
            "alertas_generadas": total,
        }, status=status.HTTP_200_OK)


class NotificacionViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    Listado y gestión de notificaciones/alertas del usuario autenticado.

    Filtros disponibles (query params):
      - leida=true|false
      - nivel=normal|importante|critico
      - tipo_alerta=FORM_CURSO_VENCIDO (filtra por metadatos.tipo_alerta)
      - trabajador_id=<uuid>  (filtra por metadatos.trabajador_id)
      - cargo=<texto>         (búsqueda parcial en metadatos.cargo)

    Acciones:
      POST /alertas/notificaciones/{id}/marcar-leida/
      POST /alertas/notificaciones/{id}/marcar-resuelta/
      GET  /alertas/notificaciones/resumen/
    """
    serializer_class = NotificacionSerializer

    def get_queryset(self):
        user = self.request.user
        empresa = user.empresa

        qs = Notificacion.objects.filter(empresa=empresa)

        # Filtro por usuario: usuarios normales solo ven las propias;
        # ADMIN y ALTA_DIRECCION pueden ver todas las de la empresa.
        if user.rol not in (UserRole.ADMIN, getattr(UserRole, "ALTA_DIRECCION", None)):
            qs = qs.filter(Q(usuario=user) | Q(usuario__isnull=True))

        params = self.request.query_params

        leida = params.get("leida")
        if leida is not None:
            qs = qs.filter(leida=leida.lower() == "true")

        nivel = params.get("nivel")
        if nivel:
            qs = qs.filter(nivel=nivel)

        tipo_alerta = params.get("tipo_alerta")
        if tipo_alerta:
            qs = qs.filter(metadatos__tipo_alerta=tipo_alerta)

        trabajador_id = params.get("trabajador_id")
        if trabajador_id:
            qs = qs.filter(metadatos__trabajador_id=trabajador_id)

        cargo = params.get("cargo")
        if cargo:
            qs = qs.filter(metadatos__cargo__icontains=cargo)

        return qs.select_related("usuario", "empresa")

    @action(detail=True, methods=["post"], url_path="marcar-leida")
    def marcar_leida(self, request, pk=None):
        """Marca la notificación como leída."""
        notif = self.get_object()
        notif.leida = True
        notif.save(update_fields=["leida"])
        return Response(self.get_serializer(notif).data)

    @action(detail=True, methods=["post"], url_path="marcar-resuelta")
    def marcar_resuelta(self, request, pk=None):
        """
        Marca la notificación como resuelta (también la marca como leída).
        Guarda estado 'resuelta' en metadatos para el frontend.
        """
        notif = self.get_object()
        notif.leida = True
        meta = notif.metadatos or {}
        meta["resuelta"] = True
        notif.metadatos = meta
        notif.save(update_fields=["leida", "metadatos"])
        return Response(self.get_serializer(notif).data)

    @action(detail=False, methods=["get"], url_path="resumen")
    def resumen(self, request):
        """
        Devuelve un resumen de notificaciones no leídas por nivel.
        Útil para la campana de notificaciones del header.
        """
        qs = self.get_queryset()
        total = qs.count()
        no_leidas = qs.filter(leida=False).count()
        criticas = qs.filter(leida=False, nivel=Notificacion.Nivel.CRITICO).count()
        importantes = qs.filter(leida=False, nivel=Notificacion.Nivel.IMPORTANTE).count()
        normales = qs.filter(leida=False, nivel=Notificacion.Nivel.NORMAL).count()
        return Response({
            "total": total,
            "no_leidas": no_leidas,
            "por_nivel": {
                "critico": criticas,
                "importante": importantes,
                "normal": normales,
            },
        })
