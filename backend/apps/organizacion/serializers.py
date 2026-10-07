from rest_framework import serializers
from .models import NodoOrganigrama, Proceso, Sede


class SedeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sede
        fields = "__all__"
        read_only_fields = ["id", "empresa", "created_at", "updated_at"]


class NodoOrganigramaSerializer(serializers.ModelSerializer):
    padre_id = serializers.PrimaryKeyRelatedField(
        source="padre", queryset=NodoOrganigrama.objects.all(), required=False, allow_null=True
    )
    nivel = serializers.IntegerField(required=False, default=1)
    hijos = serializers.SerializerMethodField()

    class Meta:
        model = NodoOrganigrama
        fields = "__all__"
        read_only_fields = ["id", "empresa", "created_at", "updated_at"]

    def create(self, validated_data):
        padre = validated_data.get("padre")
        if padre:
            validated_data["nivel"] = padre.nivel + 1
        elif "nivel" not in validated_data:
            validated_data["nivel"] = 1
        return super().create(validated_data)

    def get_hijos(self, obj):
        # Solo un nivel de profundidad para no serializar el árbol completo en cada request;
        # el frontend puede pedir /organigrama/?padre_id=<id> para expandir un nodo.
        return NodoOrganigramaSerializer(obj.hijos.filter(activo=True), many=True).data if self.context.get("con_hijos") else None


class SubprocesoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proceso
        fields = ["id", "nombre", "tipo", "descripcion", "activo", "padre"]


class ProcesoSerializer(serializers.ModelSerializer):
    padre_id = serializers.PrimaryKeyRelatedField(
        source="padre", queryset=Proceso.objects.all(), required=False, allow_null=True
    )
    subprocesos = serializers.SerializerMethodField()

    class Meta:
        model = Proceso
        fields = "__all__"
        read_only_fields = ["id", "empresa", "created_at", "updated_at"]

    def get_subprocesos(self, obj):
        return SubprocesoSerializer(obj.subprocesos.filter(activo=True), many=True).data
