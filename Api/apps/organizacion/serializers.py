from rest_framework import serializers

from apps.perfilcargo.models import PerfilCargo
from .models import NodoOrganigrama, Proceso, Sede


def _empresa_del_contexto(context):
    """Empresa del usuario autenticado (o la de ?empresa_id= para ADMIN)."""
    request = context.get("request")
    if not request or not hasattr(request, "user"):
        return None
    user = request.user
    empresa = getattr(user, "empresa", None)
    if empresa is None and str(getattr(user, "rol", "")) == "ADMIN":
        from apps.empresas.models import Empresa

        empresa_id = request.query_params.get("empresa_id")
        if empresa_id:
            return Empresa.objects.filter(id=empresa_id).first()
    return empresa


def _usuario_es_admin(context):
    request = context.get("request")
    user = getattr(request, "user", None)
    return str(getattr(user, "rol", "")) == "ADMIN"


class SedeSerializer(serializers.ModelSerializer):
    # Conteo de trabajadores asociados (usado por el frontend para el guard de borrado)
    _count = serializers.SerializerMethodField()

    class Meta:
        model = Sede
        fields = "__all__"
        read_only_fields = ["id", "empresa", "created_at", "updated_at"]

    def get__count(self, obj):
        count = getattr(obj, "trabajadores_count", None)
        if count is None:
            count = obj.trabajadores.count()
        return {"trabajadores": count}


class NodoOrganigramaSerializer(serializers.ModelSerializer):
    padre_id = serializers.PrimaryKeyRelatedField(
        source="padre", queryset=NodoOrganigrama.objects.none(), required=False, allow_null=True
    )
    perfil_cargo = serializers.PrimaryKeyRelatedField(
        queryset=PerfilCargo.objects.none(), required=False, allow_null=True
    )
    nivel = serializers.IntegerField(required=False, default=1)
    hijos = serializers.SerializerMethodField()

    class Meta:
        model = NodoOrganigrama
        fields = "__all__"
        read_only_fields = ["id", "empresa", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scopear_querysets()

    def _scopear_querysets(self):
        empresa = _empresa_del_contexto(self.context)
        if empresa is not None:
            self.fields["padre_id"].queryset = NodoOrganigrama.objects.filter(
                empresa=empresa, activo=True
            )
            self.fields["perfil_cargo"].queryset = PerfilCargo.objects.filter(empresa=empresa)
        elif _usuario_es_admin(self.context):
            self.fields["padre_id"].queryset = NodoOrganigrama.objects.all()
            self.fields["perfil_cargo"].queryset = PerfilCargo.objects.all()
        else:
            self.fields["padre_id"].queryset = NodoOrganigrama.objects.none()
            self.fields["perfil_cargo"].queryset = PerfilCargo.objects.none()

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
        source="padre", queryset=Proceso.objects.none(), required=False, allow_null=True
    )
    subprocesos = serializers.SerializerMethodField()

    class Meta:
        model = Proceso
        fields = "__all__"
        read_only_fields = ["id", "empresa", "nombre_normalizado", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        empresa = _empresa_del_contexto(self.context)
        if empresa is not None:
            self.fields["padre_id"].queryset = Proceso.objects.filter(empresa=empresa, activo=True)
        elif _usuario_es_admin(self.context):
            self.fields["padre_id"].queryset = Proceso.objects.all()
        else:
            self.fields["padre_id"].queryset = Proceso.objects.none()

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
