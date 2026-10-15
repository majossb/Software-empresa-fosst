from rest_framework import serializers

from .models import Brecha, BrechaOrigen, BrechaEvento, BrechaAccion


class BrechaOrigenSerializer(serializers.ModelSerializer):
    modulo_origen_display = serializers.CharField(
        source="get_modulo_origen_display", read_only=True,
    )
    referencia_tipo = serializers.CharField(
        source="content_type.model", read_only=True,
    )

    class Meta:
        model = BrechaOrigen
        fields = [
            "id", "modulo_origen", "modulo_origen_display",
            "referencia_tipo", "object_id",
            "es_origen_principal", "descripcion", "created_at",
        ]
        read_only_fields = fields


class BrechaEventoSerializer(serializers.ModelSerializer):
    tipo_evento_display = serializers.CharField(
        source="get_tipo_evento_display", read_only=True,
    )
    usuario_nombre = serializers.SerializerMethodField()

    class Meta:
        model = BrechaEvento
        fields = [
            "id", "tipo_evento", "tipo_evento_display",
            "descripcion", "usuario", "usuario_nombre", "created_at",
        ]
        read_only_fields = fields

    def get_usuario_nombre(self, obj):
        if obj.usuario:
            return obj.usuario.get_full_name() or obj.usuario.username
        return "Sistema"


class BrechaAccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrechaAccion
        fields = [
            "id", "brecha", "descripcion",
            "fecha_programada", "estado", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class BrechaListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados — sin relaciones anidadas."""
    clasificacion_display = serializers.CharField(
        source="get_clasificacion_display", read_only=True,
    )
    estado_display = serializers.CharField(
        source="get_estado_display", read_only=True,
    )
    nivel_atencion_display = serializers.CharField(
        source="get_nivel_atencion_display", read_only=True,
    )
    responsable_nombre = serializers.SerializerMethodField()
    trabajador_nombre = serializers.CharField(
        source="trabajador.nombre", read_only=True, default=None,
    )
    origenes_count = serializers.IntegerField(read_only=True)
    modulo_origen_principal = serializers.SerializerMethodField()

    class Meta:
        model = Brecha
        fields = [
            "id", "codigo", "empresa",
            "clasificacion", "clasificacion_display",
            "estado", "estado_display",
            "nivel_atencion", "nivel_atencion_display",
            "detectado_por", "fecha_deteccion",
            "descripcion_automatica",
            "trabajador", "trabajador_nombre",
            "responsable_seguimiento", "responsable_nombre",
            "origenes_count", "modulo_origen_principal",
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_responsable_nombre(self, obj):
        if obj.responsable_seguimiento:
            return (
                obj.responsable_seguimiento.get_full_name()
                or obj.responsable_seguimiento.username
            )
        return None

    def get_modulo_origen_principal(self, obj):
        # Prefetched — busca el origen principal en los orígenes ya cargados
        for origen in getattr(obj, "_prefetched_objects_cache", {}).get("origenes", []):
            if origen.es_origen_principal:
                return origen.get_modulo_origen_display()
        # Fallback a query si no hay prefetch
        principal = obj.origenes.filter(es_origen_principal=True).first()
        return principal.get_modulo_origen_display() if principal else None


class BrechaDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalle — incluye orígenes, eventos y acciones."""
    clasificacion_display = serializers.CharField(
        source="get_clasificacion_display", read_only=True,
    )
    estado_display = serializers.CharField(
        source="get_estado_display", read_only=True,
    )
    nivel_atencion_display = serializers.CharField(
        source="get_nivel_atencion_display", read_only=True,
    )
    responsable_nombre = serializers.SerializerMethodField()
    trabajador_nombre = serializers.CharField(
        source="trabajador.nombre", read_only=True, default=None,
    )
    origenes = BrechaOrigenSerializer(many=True, read_only=True)
    eventos = BrechaEventoSerializer(many=True, read_only=True)
    acciones = BrechaAccionSerializer(many=True, read_only=True)

    class Meta:
        model = Brecha
        fields = [
            "id", "codigo", "empresa",
            "sede", "proceso", "area",
            "trabajador", "trabajador_nombre",
            "clasificacion", "clasificacion_display",
            "estado", "estado_display",
            "detectado_por", "fecha_deteccion",
            "descripcion_automatica", "descripcion_complementaria",
            "interpretacion_ia", "recomendacion_automatica",
            "nivel_atencion", "nivel_atencion_display",
            "responsable_seguimiento", "responsable_nombre",
            "origenes", "eventos", "acciones",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "codigo", "empresa", "detectado_por", "fecha_deteccion",
            "descripcion_automatica", "interpretacion_ia", "recomendacion_automatica",
            "origenes", "eventos", "created_at", "updated_at",
        ]

    def get_responsable_nombre(self, obj):
        if obj.responsable_seguimiento:
            return (
                obj.responsable_seguimiento.get_full_name()
                or obj.responsable_seguimiento.username
            )
        return None


class BrechaUpdateSerializer(serializers.ModelSerializer):
    """Serializer para PATCH — solo campos editables por el usuario."""

    class Meta:
        model = Brecha
        fields = [
            "estado", "descripcion_complementaria",
            "responsable_seguimiento", "nivel_atencion",
        ]
