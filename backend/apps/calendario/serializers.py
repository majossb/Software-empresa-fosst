from rest_framework import serializers
from .models import CalendarioActividad, Incidente, Notificacion


class IncidenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incidente
        fields = "__all__"
        read_only_fields = ["id", "empresa", "created_at", "deleted_at"]


class CalendarioActividadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarioActividad
        fields = "__all__"
        read_only_fields = ["id", "empresa", "created_at"]


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = "__all__"
        read_only_fields = ["id", "empresa", "created_at"]
