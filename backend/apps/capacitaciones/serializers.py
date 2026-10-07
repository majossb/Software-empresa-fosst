from rest_framework import serializers

from .models import (
    AfiliacionTrabajador,
    Capacitacion,
    ParticipanteCapacitacion,
    PlanillaSeguridad,
    Trabajador,
)


class TrabajadorSerializer(serializers.ModelSerializer):
    cargo = serializers.CharField(source="perfil_cargo.nombre_cargo", read_only=True, default="")

    class Meta:
        model = Trabajador
        fields = "__all__"
        read_only_fields = [
            "id", "empresa", "created_at", "deleted_at",
            "estado_contractual", "estado_operativo",
        ]


class AfiliacionTrabajadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = AfiliacionTrabajador
        fields = "__all__"
        read_only_fields = ["id", "updated_at"]


class PlanillaSeguridadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanillaSeguridad
        fields = "__all__"
        read_only_fields = ["id", "empresa", "created_at"]


class ParticipanteCapacitacionSerializer(serializers.ModelSerializer):
    trabajador_nombre = serializers.CharField(source="trabajador.nombre", read_only=True)

    class Meta:
        model = ParticipanteCapacitacion
        fields = "__all__"
        read_only_fields = ["id"]


class CapacitacionSerializer(serializers.ModelSerializer):
    participantes = ParticipanteCapacitacionSerializer(many=True, read_only=True)

    class Meta:
        model = Capacitacion
        fields = "__all__"
        read_only_fields = ["id", "empresa", "created_at", "deleted_at"]
