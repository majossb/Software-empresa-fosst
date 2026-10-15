from rest_framework import serializers
from .models import Estandar, Evaluacion, Respuesta, Apelacion


class EstandarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estandar
        fields = "__all__"


class RespuestaSerializer(serializers.ModelSerializer):
    estandar = EstandarSerializer(read_only=True)
    evidencias_count = serializers.SerializerMethodField()

    class Meta:
        model = Respuesta
        fields = "__all__"

    def get_evidencias_count(self, obj):
        # En la fase 4 agregaremos el modelo Evidencia. Por ahora retornamos el conteo si existe la relacion.
        if hasattr(obj, "evidencias"):
            return obj.evidencias.count()
        return 0


class EvaluacionSerializer(serializers.ModelSerializer):
    respuestas = RespuestaSerializer(many=True, read_only=True)

    class Meta:
        model = Evaluacion
        fields = "__all__"


class ApelacionSerializer(serializers.ModelSerializer):
    codigo_estandar = serializers.CharField(source="respuesta.estandar.codigo", read_only=True)
    nombre_estandar = serializers.CharField(source="respuesta.estandar.nombre", read_only=True)
    observacion_original = serializers.CharField(source="respuesta.observacion", read_only=True)
    hallazgo_descripcion = serializers.SerializerMethodField()
    solicitante_nombre = serializers.SerializerMethodField()
    solicitante_email = serializers.EmailField(source="solicitante.email", read_only=True)
    evaluacion_id = serializers.UUIDField(source="respuesta.evaluacion_id", read_only=True)

    class Meta:
        model = Apelacion
        fields = "__all__"
        read_only_fields = ["solicitante", "created_at", "updated_at"]

    def get_hallazgo_descripcion(self, obj):
        try:
            from apps.hallazgos.models import Hallazgo
            h = Hallazgo.objects.filter(
                evaluacion=obj.respuesta.evaluacion,
                estandar=obj.respuesta.estandar
            ).order_by("-created_at").first()
            if h and h.descripcion:
                return h.descripcion
        except Exception:
            pass
        return obj.respuesta.observacion or ""

    def get_solicitante_nombre(self, obj):
        if not obj.solicitante:
            return ""
        full = f"{obj.solicitante.first_name} {obj.solicitante.last_name}".strip()
        return full or obj.solicitante.username

    def validate_motivo(self, value):
        if not value or not str(value).strip():
            raise serializers.ValidationError("El motivo de la apelación es obligatorio.")
        return str(value).strip()

