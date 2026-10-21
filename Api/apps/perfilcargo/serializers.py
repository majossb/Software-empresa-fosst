from rest_framework import serializers
from apps.organizacion.models import Proceso
from .models import (
    CatalogoEPP, CatalogoPeligro, PerfilCargo, CargoVersion,
    CargoFuncion, CargoResponsabilidad, CargoCompetencia,
    CargoIndicador, CargoPeligro, CargoEPP,
    CargoAptitud, CargoInteraccion, CargoRestriccion, CargoSuplente
)

class CatalogoEPPSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogoEPP
        fields = '__all__'

class CatalogoPeligroSerializer(serializers.ModelSerializer):
    epps_sugeridos = CatalogoEPPSerializer(many=True, read_only=True)
    class Meta:
        model = CatalogoPeligro
        fields = '__all__'

class CargoVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoVersion
        fields = '__all__'

class CargoFuncionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoFuncion
        fields = ['id', 'descripcion', 'orden']

class CargoResponsabilidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoResponsabilidad
        fields = ['id', 'descripcion', 'orden']

from apps.common.competencias import obtener_nombre_nivel

class CargoCompetenciaSerializer(serializers.ModelSerializer):
    nivel_nombre = serializers.SerializerMethodField()

    class Meta:
        model = CargoCompetencia
        fields = ['id', 'nombre', 'nivel', 'tipo', 'nivel_requerido', 'descripcion', 'nivel_nombre']

    def get_nivel_nombre(self, obj):
        return obtener_nombre_nivel(obj.nivel_requerido or 0)

class CargoIndicadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoIndicador
        fields = ['id', 'descripcion', 'meta']

class CargoPeligroSerializer(serializers.ModelSerializer):
    catalogo_peligro_id = serializers.PrimaryKeyRelatedField(
        queryset=CatalogoPeligro.objects.all(), source='catalogo_peligro', required=False, allow_null=True
    )
    catalogo_peligro = CatalogoPeligroSerializer(read_only=True)

    class Meta:
        model = CargoPeligro
        fields = ['id', 'catalogo_peligro_id', 'catalogo_peligro', 'tipo_personalizado', 'clasificacion_personalizada']

class CargoEPPSerializer(serializers.ModelSerializer):
    catalogo_epp_id = serializers.PrimaryKeyRelatedField(
        queryset=CatalogoEPP.objects.all(), source='catalogo_epp', required=False, allow_null=True
    )
    catalogo_epp = CatalogoEPPSerializer(read_only=True)

    class Meta:
        model = CargoEPP
        fields = ['id', 'catalogo_epp_id', 'catalogo_epp', 'nombre_personalizado']

class CargoAptitudSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoAptitud
        fields = ['id', 'tipo', 'nombre', 'requerida', 'observacion']


class CargoInteraccionSerializer(serializers.ModelSerializer):
    proceso_id = serializers.PrimaryKeyRelatedField(
        source='proceso', queryset=Proceso.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = CargoInteraccion
        fields = ['id', 'parte_interesada', 'proceso_id', 'tipo', 'descripcion']


class CargoRestriccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoRestriccion
        fields = ['id', 'descripcion', 'activa']


class CargoSuplenteSerializer(serializers.ModelSerializer):
    cargo_suplente_id = serializers.PrimaryKeyRelatedField(
        source='cargo_suplente', queryset=PerfilCargo.objects.all()
    )
    cargo_suplente_nombre = serializers.CharField(source='cargo_suplente.nombre_cargo', read_only=True)

    class Meta:
        model = CargoSuplente
        fields = ['id', 'cargo_suplente_id', 'cargo_suplente_nombre', 'orden_prioridad']


class PerfilCargoSerializer(serializers.ModelSerializer):
    funciones = CargoFuncionSerializer(many=True, read_only=True)
    responsabilidades = CargoResponsabilidadSerializer(many=True, read_only=True)
    competencias = CargoCompetenciaSerializer(many=True, read_only=True)
    indicadores = CargoIndicadorSerializer(many=True, read_only=True)
    peligros = CargoPeligroSerializer(many=True, read_only=True)
    epps = CargoEPPSerializer(many=True, read_only=True)
    aptitudes = CargoAptitudSerializer(many=True, read_only=True)
    interacciones = CargoInteraccionSerializer(many=True, read_only=True)
    restricciones = CargoRestriccionSerializer(many=True, read_only=True)
    suplentes = CargoSuplenteSerializer(many=True, read_only=True)
    versiones = CargoVersionSerializer(many=True, read_only=True)
    requisitos_formacion = serializers.SerializerMethodField()
    trabajadores_count = serializers.IntegerField(read_only=True)
    vacantes_activas_count = serializers.IntegerField(read_only=True, default=0)
    procesos_activos_count = serializers.IntegerField(read_only=True, default=0)
    sede_nombre = serializers.SerializerMethodField()
    sede_ciudad = serializers.SerializerMethodField()

    def get_requisitos_formacion(self, obj):
        from apps.formacion.models import CargoRequisitoFormacion
        from apps.formacion.serializers import CargoRequisitoFormacionSerializer
        reqs = CargoRequisitoFormacion.objects.filter(perfil_cargo=obj).select_related("curso")
        return CargoRequisitoFormacionSerializer(reqs, many=True).data

    def get_sede_nombre(self, obj):
        return obj.sede.nombre if obj.sede_id else None

    def get_sede_ciudad(self, obj):
        return obj.sede.ciudad if obj.sede_id else None

    class Meta:
        model = PerfilCargo
        fields = '__all__'
