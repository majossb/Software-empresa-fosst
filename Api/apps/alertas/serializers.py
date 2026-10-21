from rest_framework import serializers
from apps.calendario.models import Notificacion
from .models import ReglaAlerta


class ReglaAlertaSerializer(serializers.ModelSerializer):
    modelo_origen_display = serializers.CharField(source="get_modelo_origen_display", read_only=True)
    nivel_criticidad_display = serializers.CharField(source="get_nivel_criticidad_display", read_only=True)

    class Meta:
        model = ReglaAlerta
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class NotificacionSerializer(serializers.ModelSerializer):
    """
    Serializer de Notificacion con URL de acción contextual para alertas de formación.

    Campo extra `accion_url`:
      - Si la alerta es de un curso (metadatos.tipo_alerta empieza con FORM_CURSO),
        sugiere ir a /app/responsable/formacion
      - Si es de competencia, sugiere /app/responsable/formacion?tab=competencias
    """
    nivel_display = serializers.CharField(source="get_nivel_display", read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    accion_url = serializers.SerializerMethodField()

    class Meta:
        model = Notificacion
        fields = [
            "id", "empresa", "usuario", "tipo", "tipo_display",
            "nivel", "nivel_display", "mensaje", "leida",
            "enviado_email", "metadatos", "accion_url", "created_at",
        ]
        read_only_fields = ["id", "empresa", "created_at"]

    def get_accion_url(self, obj):
        meta = obj.metadatos or {}
        tipo_alerta = meta.get("tipo_alerta", "")
        if tipo_alerta.startswith("FORM_CURSO"):
            trabajador_id = meta.get("trabajador_id", "")
            curso_id = meta.get("curso_id", "")
            base = "/app/responsable/formacion"
            params = []
            if trabajador_id:
                params.append(f"trabajador_id={trabajador_id}")
            if curso_id:
                params.append(f"curso_id={curso_id}")
            return f"{base}?{'&'.join(params)}" if params else base
        if tipo_alerta == "FORM_EVALUACION_COMPETENCIA_PENDIENTE":
            trabajador_id = meta.get("trabajador_id", "")
            return (
                f"/app/responsable/formacion?tab=competencias&trabajador_id={trabajador_id}"
                if trabajador_id else "/app/responsable/formacion?tab=competencias"
            )
        return None
