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
        read_only_fields = ["id", "empresa", "nombre_normalizado", "created_at", "updated_at"]

    def validate(self, attrs):
        from .models import normalizar_texto

        request = self.context.get("request")
        empresa = getattr(request.user, "empresa", None) if request and hasattr(request, "user") else None
        if not empresa and request and hasattr(request, "query_params"):
            empresa_id = request.query_params.get("empresa_id")
            if empresa_id:
                from apps.empresas.models import Empresa
                empresa = Empresa.objects.filter(id=empresa_id).first()
        if not empresa and self.instance:
            empresa = self.instance.empresa
        if not empresa and "empresa" in attrs:
            empresa = attrs["empresa"]

        nombre = attrs.get("nombre", self.instance.nombre if self.instance else "")
        tipo = attrs.get("tipo", self.instance.tipo if self.instance else "")
        padre = attrs.get("padre", self.instance.padre if self.instance else None)

        if nombre and empresa:
            norm = normalizar_texto(nombre)
            qs = Proceso.objects.filter(
                empresa=empresa,
                tipo=tipo,
                padre=padre,
                nombre_normalizado=norm,
            )
            if self.instance:
                qs = qs.exclude(id=self.instance.id)
            if qs.exists():
                raise serializers.ValidationError({
                    "nombre": "Ya existe un proceso con este nombre para la misma categoría y nivel."
                })

        return attrs

    def get_subprocesos(self, obj):
        return SubprocesoSerializer(obj.subprocesos.filter(activo=True), many=True).data
