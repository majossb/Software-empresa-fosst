from rest_framework import serializers
from .models import Hallazgo, PlanMejora


class HallazgoSerializer(serializers.ModelSerializer):
    auditor_nombre = serializers.CharField(source="auditor.get_full_name", read_only=True)
    estandar_codigo = serializers.CharField(source="estandar.codigo", read_only=True, default=None)
    estandar_nombre = serializers.CharField(source="estandar.nombre", read_only=True, default=None)

    class Meta:
        model = Hallazgo
        fields = "__all__"
        read_only_fields = ["id", "auditor", "created_at"]


class PlanMejoraSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanMejora
        fields = "__all__"
        read_only_fields = ["id", "empresa", "created_at", "updated_at", "deleted_at"]
