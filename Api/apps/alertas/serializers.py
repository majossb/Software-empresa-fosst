from rest_framework import serializers
from .models import ReglaAlerta


class ReglaAlertaSerializer(serializers.ModelSerializer):
    modelo_origen_display = serializers.CharField(source="get_modelo_origen_display", read_only=True)
    nivel_criticidad_display = serializers.CharField(source="get_nivel_criticidad_display", read_only=True)

    class Meta:
        model = ReglaAlerta
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
