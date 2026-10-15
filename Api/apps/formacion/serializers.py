from rest_framework import serializers
from .models import EvaluacionCompetencia


class EvaluacionCompetenciaSerializer(serializers.ModelSerializer):
    trabajador_nombre = serializers.CharField(source="trabajador.nombre", read_only=True)
    trabajador_documento = serializers.CharField(source="trabajador.documento", read_only=True)
    competencia_nombre = serializers.CharField(source="cargo_competencia.nombre", read_only=True)
    competencia_tipo = serializers.CharField(source="cargo_competencia.tipo", read_only=True)
    nivel_requerido = serializers.SerializerMethodField()
    metodo_display = serializers.CharField(source="get_metodo_display", read_only=True)
    evaluado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = EvaluacionCompetencia
        fields = [
            "id", "trabajador", "trabajador_nombre", "trabajador_documento",
            "cargo_competencia", "competencia_nombre", "competencia_tipo",
            "nivel_requerido", "nivel_alcanzado", "brecha_calculada",
            "fecha_evaluacion", "metodo", "metodo_display",
            "observacion", "soporte_archivo",
            "evaluado_por", "evaluado_por_nombre",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "brecha_calculada", "created_at", "updated_at"]

    def get_nivel_requerido(self, obj):
        return obj.cargo_competencia.nivel_requerido or obj.cargo_competencia.nivel or 1

    def get_evaluado_por_nombre(self, obj):
        if obj.evaluado_por:
            return obj.evaluado_por.get_full_name() or obj.evaluado_por.username
        return None
