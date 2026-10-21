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
    trabajador_documento = serializers.CharField(source="trabajador.documento", read_only=True)
    trabajador_cargo = serializers.CharField(source="trabajador.cargo", read_only=True, default="")
    soporte_url = serializers.CharField(source="soporte.url", read_only=True, default=None)

    class Meta:
        model = ParticipanteCapacitacion
        fields = "__all__"
        read_only_fields = ["id", "created_at"]


class CapacitacionSerializer(serializers.ModelSerializer):
    participantes = ParticipanteCapacitacionSerializer(many=True, read_only=True)
    curso_nombre = serializers.CharField(source="curso.nombre", read_only=True, default="")
    competencia_nombre = serializers.CharField(source="competencia.nombre", read_only=True, default="")
    brechas_detalle = serializers.SerializerMethodField()
    total_participantes = serializers.SerializerMethodField()
    total_asistieron = serializers.SerializerMethodField()

    class Meta:
        model = Capacitacion
        fields = "__all__"
        read_only_fields = ["id", "empresa", "created_at", "deleted_at"]

    def get_brechas_detalle(self, obj):
        return [
            {
                "id": str(b.id),
                "codigo": b.codigo,
                "clasificacion": b.clasificacion,
                "clasificacion_display": b.get_clasificacion_display(),
                "estado": b.estado,
                "descripcion": b.descripcion_automatica or b.descripcion_complementaria or "",
                "trabajador_nombre": b.trabajador.nombre if b.trabajador else None,
            }
            for b in obj.brechas.all()
        ]

    def get_total_participantes(self, obj):
        return obj.participantes.count()

    def get_total_asistieron(self, obj):
        return obj.participantes.filter(asistio=True).count()
