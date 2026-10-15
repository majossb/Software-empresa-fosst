from django.db.models import Count
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.mixins import EmpresaScopedViewSet
from .models import Brecha, BrechaAccion
from .serializers import (
    BrechaListSerializer,
    BrechaDetailSerializer,
    BrechaUpdateSerializer,
    BrechaAccionSerializer,
)


class BrechaViewSet(EmpresaScopedViewSet):
    """
    ViewSet para gestión de Brechas.

    Las brechas NO se crean por API directamente — se crean exclusivamente via
    hbseo.services.registrar_o_vincular_brecha() desde los módulos que detectan
    condiciones (MICHC, Formación, Gestión Humana, SST, etc.).

    Este viewset expone:
      - GET  /api/hbseo/brechas/           → listado con filtros
      - GET  /api/hbseo/brechas/{id}/      → detalle con orígenes, eventos, acciones
      - PATCH /api/hbseo/brechas/{id}/     → actualizar campos editables
      - GET  /api/hbseo/brechas/resumen/   → contadores por estado y clasificación
    """
    queryset = Brecha.objects.all()
    serializer_class = BrechaListSerializer
    filterset_fields = ["estado", "clasificacion", "nivel_atencion", "trabajador"]
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        qs = super().get_queryset()

        # Annotate para el listado
        qs = qs.annotate(origenes_count=Count("origenes"))

        # Filtro adicional por módulo de origen (query param, no filterset)
        modulo_origen = self.request.query_params.get("modulo_origen")
        if modulo_origen:
            qs = qs.filter(origenes__modulo_origen=modulo_origen).distinct()

        # Filtro por responsable
        responsable_id = self.request.query_params.get("responsable_id")
        if responsable_id:
            qs = qs.filter(responsable_seguimiento_id=responsable_id)

        return qs.select_related(
            "trabajador", "responsable_seguimiento", "sede", "proceso",
        ).prefetch_related("origenes")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return BrechaDetailSerializer
        if self.action == "partial_update":
            return BrechaUpdateSerializer
        return BrechaListSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Prefetch all relations for detail view
        qs = Brecha.objects.filter(pk=instance.pk).prefetch_related(
            "origenes__content_type",
            "eventos__usuario",
            "acciones",
        )
        instance = qs.first()
        serializer = BrechaDetailSerializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def resumen(self, request):
        """Contadores por estado y clasificación para dashboard."""
        qs = self.get_queryset()

        por_estado = {}
        for estado_val, estado_label in Brecha.Estado.choices:
            por_estado[estado_val] = qs.filter(estado=estado_val).count()

        por_clasificacion = {}
        for clas_val, clas_label in Brecha.Clasificacion.choices:
            count = qs.filter(clasificacion=clas_val).count()
            if count > 0:
                por_clasificacion[clas_val] = count

        por_nivel = {}
        for nivel_val, nivel_label in Brecha.NivelAtencion.choices:
            count = qs.filter(nivel_atencion=nivel_val).count()
            if count > 0:
                por_nivel[nivel_val] = count

        return Response({
            "total": qs.count(),
            "por_estado": por_estado,
            "por_clasificacion": por_clasificacion,
            "por_nivel_atencion": por_nivel,
        })

    @action(detail=False, methods=["get"], url_path="informes-periodo")
    def informes_periodo(self, request):
        """
        GET /api/hbseo/brechas/informes-periodo/?periodo=trimestral|semestral|anual|bienal
        Genera informe consolidado de brechas filtrado por ventana de tiempo (§3.2.2.1).
        """
        from datetime import timedelta
        from django.utils import timezone

        periodo = request.query_params.get("periodo", "anual")
        fecha_inicio_param = request.query_params.get("fecha_inicio")
        fecha_fin_param = request.query_params.get("fecha_fin")

        now = timezone.now()
        if fecha_inicio_param and fecha_fin_param:
            try:
                from datetime import datetime
                fecha_inicio = datetime.strptime(fecha_inicio_param, "%Y-%m-%d")
                fecha_fin = datetime.strptime(fecha_fin_param, "%Y-%m-%d")
            except ValueError:
                return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD."}, status=400)
        else:
            dias_map = {
                "trimestral": 90,
                "semestral": 180,
                "anual": 365,
                "bienal": 730,
            }
            dias = dias_map.get(periodo, 365)
            fecha_inicio = now - timedelta(days=dias)
            fecha_fin = now

        qs = self.get_queryset().filter(fecha_deteccion__gte=fecha_inicio, fecha_deteccion__lte=fecha_fin)

        total_brechas = qs.count()
        subsanadas = qs.filter(estado=Brecha.Estado.SUBSANADA).count()
        cerradas = qs.filter(estado=Brecha.Estado.CERRADA).count()
        en_tratamiento = qs.filter(estado=Brecha.Estado.EN_TRATAMIENTO).count()
        detectadas = qs.filter(estado=Brecha.Estado.DETECTADA).count()

        por_clasificacion = {}
        for clas_val, clas_label in Brecha.Clasificacion.choices:
            count = qs.filter(clasificacion=clas_val).count()
            if count > 0:
                por_clasificacion[clas_val] = count

        return Response({
            "periodo": periodo,
            "fecha_inicio": fecha_inicio.isoformat(),
            "fecha_fin": fecha_fin.isoformat(),
            "total_brechas": total_brechas,
            "subsanadas": subsanadas,
            "cerradas": cerradas,
            "en_tratamiento": en_tratamiento,
            "detectadas": detectadas,
            "tasa_cierre_porcentaje": round(((subsanadas + cerradas) / total_brechas) * 100, 2) if total_brechas > 0 else 0.0,
            "por_clasificacion": por_clasificacion,
        })


class BrechaAccionViewSet(EmpresaScopedViewSet):
    """
    Gestión de acciones programadas para brechas.

    Se accede como recurso anidado: /api/hbseo/brechas/{brecha_id}/acciones/
    """
    queryset = BrechaAccion.objects.all()
    serializer_class = BrechaAccionSerializer
    empresa_field = "brecha__empresa"

    def get_queryset(self):
        qs = super().get_queryset()
        brecha_id = self.kwargs.get("brecha_pk")
        if brecha_id:
            qs = qs.filter(brecha_id=brecha_id)
        return qs

    def perform_create(self, serializer):
        brecha_id = self.kwargs.get("brecha_pk")
        if brecha_id:
            serializer.save(brecha_id=brecha_id)
        else:
            serializer.save()
