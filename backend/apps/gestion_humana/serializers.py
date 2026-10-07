from rest_framework import serializers
from .models import NovedadLaboral, ExamenMedicoOcupacional, LicenciaConduccion


class NovedadLaboralSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    trabajador_nombre = serializers.CharField(source="trabajador.nombre", read_only=True)
    created_by_nombre = serializers.SerializerMethodField()

    class Meta:
        model = NovedadLaboral
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_created_by_nombre(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None


class ExamenMedicoOcupacionalSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    concepto_aptitud_display = serializers.CharField(source="get_concepto_aptitud_display", read_only=True)
    trabajador_nombre = serializers.CharField(source="trabajador.nombre", read_only=True)

    class Meta:
        model = ExamenMedicoOcupacional
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class LicenciaConduccionSerializer(serializers.ModelSerializer):
    trabajador_nombre = serializers.CharField(source="trabajador.nombre", read_only=True)

    class Meta:
        model = LicenciaConduccion
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ExpedienteTrabajadorSerializer(serializers.Serializer):
    """Vista unificada del expediente del trabajador."""
    trabajador = serializers.DictField()
    novedades = NovedadLaboralSerializer(many=True)
    examenes_medicos = ExamenMedicoOcupacionalSerializer(many=True)
    licencias = LicenciaConduccionSerializer(many=True)
