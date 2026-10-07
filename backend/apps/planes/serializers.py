from rest_framework import serializers
from .models import Plan, Suscripcion


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = "__all__"
        read_only_fields = ["id", "created_at"]


class SuscripcionSerializer(serializers.ModelSerializer):
    plan_nombre = serializers.CharField(source="plan.nombre", read_only=True)

    class Meta:
        model = Suscripcion
        fields = "__all__"
        read_only_fields = ["id", "created_at", "empresa"]
