from rest_framework import serializers
from apps.common.competencias import obtener_nombre_nivel
from .models import EvaluacionCompetencia


class EvaluacionCompetenciaSerializer(serializers.ModelSerializer):
    trabajador_nombre = serializers.CharField(source="trabajador.nombre", read_only=True)
    trabajador_documento = serializers.CharField(source="trabajador.documento", read_only=True)
    competencia_nombre = serializers.CharField(source="cargo_competencia.nombre", read_only=True)
    competencia_tipo = serializers.CharField(source="cargo_competencia.tipo", read_only=True)
    competencia_descripcion = serializers.CharField(source="cargo_competencia.descripcion", read_only=True)
    nivel_requerido = serializers.SerializerMethodField()
    nivel_requerido_nombre = serializers.SerializerMethodField()
    nivel_alcanzado_nombre = serializers.SerializerMethodField()
    metodo_display = serializers.CharField(source="get_metodo_display", read_only=True)
    rol_evaluador_display = serializers.CharField(source="get_rol_evaluador_display", read_only=True)
    evaluado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = EvaluacionCompetencia
        fields = [
            "id", "trabajador", "trabajador_nombre", "trabajador_documento",
            "cargo_competencia", "competencia_nombre", "competencia_tipo", "competencia_descripcion",
            "nivel_requerido", "nivel_requerido_nombre", "nivel_alcanzado", "nivel_alcanzado_nombre",
            "brecha_calculada", "fecha_evaluacion", "metodo", "metodo_display",
            "rol_evaluador", "rol_evaluador_display",
            "observacion", "soporte_archivo",
            "evaluado_por", "evaluado_por_nombre",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "brecha_calculada", "created_at", "updated_at"]

    def get_nivel_requerido(self, obj):
        from apps.common.competencias import parse_nivel
        return parse_nivel(obj.cargo_competencia.nivel_requerido or obj.cargo_competencia.nivel, default=3)

    def get_nivel_requerido_nombre(self, obj):
        req = self.get_nivel_requerido(obj)
        return obtener_nombre_nivel(req)

    def get_nivel_alcanzado_nombre(self, obj):
        return obtener_nombre_nivel(obj.nivel_alcanzado)

    def get_evaluado_por_nombre(self, obj):
        if obj.evaluado_por:
            return obj.evaluado_por.get_full_name() or obj.evaluado_por.username
        return None


class CursoFormacionSerializer(serializers.ModelSerializer):
    categoria_display = serializers.CharField(source="get_categoria_display", read_only=True)

    class Meta:
        from .models import CursoFormacion
        model = CursoFormacion
        fields = [
            "id", "empresa", "nombre", "categoria", "categoria_display",
            "vigencia_meses", "requiere_certificado", "descripcion", "activo",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CargoRequisitoFormacionSerializer(serializers.ModelSerializer):
    curso_id = serializers.UUIDField(source="curso.id", read_only=True)
    curso_nombre = serializers.CharField(source="curso.nombre", read_only=True)
    curso_categoria = serializers.CharField(source="curso.categoria", read_only=True)
    curso_categoria_display = serializers.CharField(source="curso.get_categoria_display", read_only=True)
    curso_requiere_certificado = serializers.BooleanField(source="curso.requiere_certificado", read_only=True)

    class Meta:
        from .models import CargoRequisitoFormacion
        model = CargoRequisitoFormacion
        fields = [
            "id", "perfil_cargo", "curso", "curso_id", "curso_nombre",
            "curso_categoria", "curso_categoria_display", "curso_requiere_certificado",
            "obligatorio", "vigencia_meses", "grupo_alternativo",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RegistroFormacionSerializer(serializers.ModelSerializer):
    trabajador_nombre = serializers.CharField(source="trabajador.nombre", read_only=True)
    trabajador_documento = serializers.CharField(source="trabajador.documento", read_only=True)
    trabajador_cargo = serializers.CharField(source="trabajador.cargo", read_only=True)
    curso_nombre = serializers.CharField(source="curso.nombre", read_only=True)
    curso_categoria = serializers.CharField(source="curso.categoria", read_only=True)
    curso_categoria_display = serializers.CharField(source="curso.get_categoria_display", read_only=True)
    soporte_nombre = serializers.CharField(source="soporte.nombre", read_only=True)
    soporte_url = serializers.CharField(source="soporte.url", read_only=True)
    origen_display = serializers.CharField(source="get_origen_display", read_only=True)
    estado_derivado = serializers.CharField(read_only=True)
    dias_para_vencer = serializers.IntegerField(read_only=True)

    class Meta:
        from .models import RegistroFormacion
        model = RegistroFormacion
        fields = [
            "id", "trabajador", "trabajador_nombre", "trabajador_documento", "trabajador_cargo",
            "curso", "curso_nombre", "curso_categoria", "curso_categoria_display",
            "fecha_realizacion", "fecha_vencimiento", "soporte", "soporte_nombre", "soporte_url",
            "origen", "origen_display", "entidad_emisora", "horas_duracion", "observaciones",
            "estado_derivado", "dias_para_vencer",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "estado_derivado", "dias_para_vencer", "created_at", "updated_at"]

