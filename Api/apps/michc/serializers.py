from rest_framework import serializers
from .models import EvaluacionHabilitacion, DetalleCumplimientoRequisito


class DetalleCumplimientoRequisitoSerializer(serializers.ModelSerializer):
    tipo_requisito_display = serializers.CharField(source="get_tipo_requisito_display", read_only=True)
    cumple_display = serializers.CharField(source="get_cumple_display", read_only=True)

    class Meta:
        model = DetalleCumplimientoRequisito
        fields = [
            "id", "tipo_requisito", "tipo_requisito_display",
            "requisito_descripcion", "cumple", "cumple_display",
            "observacion", "evidencia_id", "created_at"
        ]
        read_only_fields = fields


class EvaluacionHabilitacionListSerializer(serializers.ModelSerializer):
    trabajador_nombre = serializers.CharField(source="trabajador.nombre", read_only=True)
    trabajador_documento = serializers.CharField(source="trabajador.documento", read_only=True)
    cargo_nombre = serializers.CharField(source="perfil_cargo.nombre_cargo", read_only=True)
    semaforo_display = serializers.CharField(source="get_semaforo_display", read_only=True)
    estado_habilitacion_display = serializers.CharField(source="get_estado_habilitacion_display", read_only=True)
    compatibilidad_display = serializers.CharField(source="get_compatibilidad_display", read_only=True)
    nivel_atencion_display = serializers.CharField(source="get_nivel_atencion_display", read_only=True)
    sede_nombre = serializers.CharField(source="trabajador.sede.nombre", read_only=True)

    class Meta:
        model = EvaluacionHabilitacion
        fields = [
            "id", "trabajador", "trabajador_nombre", "trabajador_documento",
            "perfil_cargo", "cargo_nombre", "sede_nombre",
            "porcentaje_cumplimiento", "semaforo", "semaforo_display",
            "estado_habilitacion", "estado_habilitacion_display",
            "compatibilidad", "compatibilidad_display",
            "nivel_atencion", "nivel_atencion_display",
            "calculado_at"
        ]
        read_only_fields = fields


class EvaluacionHabilitacionDetailSerializer(serializers.ModelSerializer):
    trabajador_nombre = serializers.CharField(source="trabajador.nombre", read_only=True)
    trabajador_documento = serializers.CharField(source="trabajador.documento", read_only=True)
    cargo_nombre = serializers.CharField(source="perfil_cargo.nombre_cargo", read_only=True)
    semaforo_display = serializers.CharField(source="get_semaforo_display", read_only=True)
    estado_habilitacion_display = serializers.CharField(source="get_estado_habilitacion_display", read_only=True)
    compatibilidad_display = serializers.CharField(source="get_compatibilidad_display", read_only=True)
    nivel_atencion_display = serializers.CharField(source="get_nivel_atencion_display", read_only=True)
    sede_nombre = serializers.CharField(source="trabajador.sede.nombre", read_only=True)
    detalles_requisitos = DetalleCumplimientoRequisitoSerializer(many=True, read_only=True)

    class Meta:
        model = EvaluacionHabilitacion
        fields = [
            "id", "trabajador", "trabajador_nombre", "trabajador_documento",
            "perfil_cargo", "cargo_nombre", "sede_nombre",
            "porcentaje_cumplimiento", "semaforo", "semaforo_display",
            "estado_habilitacion", "estado_habilitacion_display",
            "compatibilidad", "compatibilidad_display",
            "nivel_atencion", "nivel_atencion_display",
            "interpretacion_ia", "recomendacion_ia",
            "detalles_requisitos",
            "calculado_at"
        ]
        read_only_fields = fields
