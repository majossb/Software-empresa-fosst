"""
Serializers REST para Reclutamiento y Selección — FOSST V.I.D.A.
Fase D: Serializadores de lectura y escritura para Banco de Talento, Vacantes,
Procesos de Selección, Postulaciones (con semáforo de etapas) y Trazabilidad.
RN-R01: El campo `estado` en Postulacion es estrictamente read_only.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.reclutamiento.models import (
    FuenteReclutamiento,
    Candidato,
    PerfilCandidato,
    CandidatoDocumento,
    Vacante,
    ProcesoSeleccion,
    Postulacion,
    PostulacionEvento,
    Entrevista,
    Evaluacion,
    ValidacionDocumental,
    TokenAccesoCandidato,
)

Usuario = get_user_model()


# -----------------------------------------------------------------------------
# 1. Catálogo de Fuentes de Reclutamiento
# -----------------------------------------------------------------------------
class FuenteReclutamientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuenteReclutamiento
        fields = [
            "id",
            "nombre",
            "descripcion",
            "activo",
            "es_sistema",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "es_sistema", "created_at", "updated_at"]


# -----------------------------------------------------------------------------
# 2. Perfil de Candidato y Documentos
# -----------------------------------------------------------------------------
class PerfilCandidatoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilCandidato
        fields = [
            "id",
            "titulo_profesional",
            "nivel_educativo",
            "resumen_profesional",
            "anios_experiencia",
            "experiencia_laboral",
            "formacion_academica",
            "certificaciones",
            "competencias",
            "aspiracion_salarial",
            "disponibilidad_viaje",
            "disponibilidad_traslado",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CandidatoDocumentoSerializer(serializers.ModelSerializer):
    tipo_documento_display = serializers.CharField(source="get_tipo_documento_display", read_only=True)
    archivo_url = serializers.SerializerMethodField()
    archivo_nombre = serializers.SerializerMethodField()

    class Meta:
        model = CandidatoDocumento
        fields = [
            "id",
            "archivo",
            "archivo_nombre",
            "archivo_url",
            "tipo_documento",
            "tipo_documento_display",
            "nombre_descriptivo",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_archivo_url(self, obj):
        if obj.archivo and hasattr(obj.archivo, "archivo") and obj.archivo.archivo:
            return obj.archivo.archivo.url
        return None

    def get_archivo_nombre(self, obj):
        if obj.archivo and hasattr(obj.archivo, "nombre_original"):
            return obj.archivo.nombre_original
        return None


# -----------------------------------------------------------------------------
# 3. Candidato (Banco de Talento)
# -----------------------------------------------------------------------------
class CandidatoListSerializer(serializers.ModelSerializer):
    tipo_documento_display = serializers.CharField(source="get_tipo_documento_display", read_only=True)
    nombre_completo = serializers.CharField(read_only=True)
    fuente_reclutamiento_nombre = serializers.CharField(
        source="fuente_reclutamiento.nombre", read_only=True, default=""
    )
    titulo_profesional = serializers.SerializerMethodField()
    anios_experiencia = serializers.SerializerMethodField()
    postulaciones_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Candidato
        fields = [
            "id",
            "tipo_documento",
            "tipo_documento_display",
            "documento",
            "nombres",
            "apellidos",
            "nombre_completo",
            "email",
            "telefono",
            "ciudad",
            "fuente_reclutamiento",
            "fuente_reclutamiento_nombre",
            "etiquetas",
            "autoriza_tratamiento_datos",
            "titulo_profesional",
            "anios_experiencia",
            "postulaciones_count",
            "created_at",
        ]

    def get_titulo_profesional(self, obj):
        if hasattr(obj, "perfil") and obj.perfil:
            return obj.perfil.titulo_profesional
        return ""

    def get_anios_experiencia(self, obj):
        if hasattr(obj, "perfil") and obj.perfil:
            return float(obj.perfil.anios_experiencia)
        return 0.0


class CandidatoDetailSerializer(serializers.ModelSerializer):
    tipo_documento_display = serializers.CharField(source="get_tipo_documento_display", read_only=True)
    nombre_completo = serializers.CharField(read_only=True)
    fuente_reclutamiento_nombre = serializers.CharField(
        source="fuente_reclutamiento.nombre", read_only=True, default=""
    )
    perfil = PerfilCandidatoSerializer(read_only=True)
    documentos = CandidatoDocumentoSerializer(many=True, read_only=True)
    historial_postulaciones = serializers.SerializerMethodField()

    class Meta:
        model = Candidato
        fields = [
            "id",
            "tipo_documento",
            "tipo_documento_display",
            "documento",
            "nombres",
            "apellidos",
            "nombre_completo",
            "email",
            "telefono",
            "ciudad",
            "direccion",
            "fuente_reclutamiento",
            "fuente_reclutamiento_nombre",
            "fuente_detalle",
            "autoriza_tratamiento_datos",
            "fecha_autorizacion_datos",
            "etiquetas",
            "notas_internas",
            "perfil",
            "documentos",
            "historial_postulaciones",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_historial_postulaciones(self, obj):
        postulaciones = obj.postulaciones.select_related(
            "proceso_seleccion__vacante"
        ).filter(deleted_at__isnull=True).order_by("-fecha_postulacion")
        return [
            {
                "id": str(p.id),
                "proceso_seleccion_id": str(p.proceso_seleccion_id),
                "vacante_codigo": p.proceso_seleccion.vacante.codigo,
                "vacante_titulo": p.proceso_seleccion.vacante.titulo,
                "estado": p.estado,
                "estado_display": p.get_estado_display(),
                "fecha_postulacion": p.fecha_postulacion,
                "puntuacion_general": float(p.puntuacion_general) if p.puntuacion_general is not None else None,
                "es_activa": p.es_activa,
            }
            for p in postulaciones
        ]


class CandidatoCreateUpdateSerializer(serializers.ModelSerializer):
    perfil = PerfilCandidatoSerializer(required=False)

    class Meta:
        model = Candidato
        fields = [
            "id",
            "tipo_documento",
            "documento",
            "nombres",
            "apellidos",
            "email",
            "telefono",
            "ciudad",
            "direccion",
            "fuente_reclutamiento",
            "fuente_detalle",
            "autoriza_tratamiento_datos",
            "fecha_autorizacion_datos",
            "etiquetas",
            "notas_internas",
            "perfil",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        perfil_data = validated_data.pop("perfil", None)
        candidato = Candidato.objects.create(**validated_data)
        if perfil_data:
            PerfilCandidato.objects.create(candidato=candidato, **perfil_data)
        else:
            PerfilCandidato.objects.create(candidato=candidato)
        return candidato

    def update(self, instance, validated_data):
        perfil_data = validated_data.pop("perfil", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if perfil_data:
            perfil, _ = PerfilCandidato.objects.get_or_create(candidato=instance)
            for attr, value in perfil_data.items():
                setattr(perfil, attr, value)
            perfil.save()
        return instance


# -----------------------------------------------------------------------------
# 4. Vacantes
# -----------------------------------------------------------------------------
class VacanteListSerializer(serializers.ModelSerializer):
    perfil_cargo_nombre = serializers.CharField(source="perfil_cargo.nombre_cargo", read_only=True)
    sede_nombre = serializers.CharField(source="sede.nombre", read_only=True, default="")
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    modalidad_display = serializers.CharField(source="get_modalidad_display", read_only=True)
    cupos_disponibles = serializers.IntegerField(read_only=True)
    esta_cubierta = serializers.BooleanField(read_only=True)
    postulaciones_count = serializers.IntegerField(read_only=True, default=0)
    proceso_seleccion_id = serializers.SerializerMethodField()

    class Meta:
        model = Vacante
        fields = [
            "id",
            "codigo",
            "titulo",
            "slug",
            "perfil_cargo",
            "perfil_cargo_nombre",
            "sede",
            "sede_nombre",
            "numero_cupos",
            "numero_seleccionados",
            "cupos_disponibles",
            "esta_cubierta",
            "tipo_contrato",
            "modalidad",
            "modalidad_display",
            "rango_salarial_min",
            "rango_salarial_max",
            "mostrar_salario_publico",
            "estado",
            "estado_display",
            "fecha_apertura",
            "fecha_cierre_estimada",
            "publicada_en_portal",
            "postulaciones_count",
            "proceso_seleccion_id",
            "created_at",
        ]

    def get_proceso_seleccion_id(self, obj):
        if hasattr(obj, "proceso_seleccion") and obj.proceso_seleccion:
            return str(obj.proceso_seleccion.id)
        return None


class VacanteDetailSerializer(serializers.ModelSerializer):
    perfil_cargo_detalle = serializers.SerializerMethodField()
    sede_nombre = serializers.CharField(source="sede.nombre", read_only=True, default="")
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    modalidad_display = serializers.CharField(source="get_modalidad_display", read_only=True)
    cupos_disponibles = serializers.IntegerField(read_only=True)
    esta_cubierta = serializers.BooleanField(read_only=True)
    proceso_seleccion = serializers.SerializerMethodField()

    class Meta:
        model = Vacante
        fields = [
            "id",
            "codigo",
            "titulo",
            "slug",
            "perfil_cargo",
            "perfil_cargo_detalle",
            "sede",
            "sede_nombre",
            "descripcion_publica",
            "numero_cupos",
            "numero_seleccionados",
            "cupos_disponibles",
            "esta_cubierta",
            "tipo_contrato",
            "modalidad",
            "modalidad_display",
            "rango_salarial_min",
            "rango_salarial_max",
            "mostrar_salario_publico",
            "estado",
            "estado_display",
            "fecha_apertura",
            "fecha_cierre_estimada",
            "fecha_cierre_real",
            "publicada_en_portal",
            "proceso_seleccion",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "codigo", "slug", "numero_seleccionados", "created_at", "updated_at"]

    def get_perfil_cargo_detalle(self, obj):
        pc = obj.perfil_cargo
        if not pc:
            return None
        return {
            "id": str(pc.id),
            "nombre_cargo": pc.nombre_cargo,
            "codigo": pc.codigo,
            "area": pc.area,
            "proposito": getattr(pc, "proposito", ""),
            "educacion": getattr(pc, "educacion", ""),
            "experiencia": getattr(pc, "experiencia", ""),
        }

    def get_proceso_seleccion(self, obj):
        if hasattr(obj, "proceso_seleccion") and obj.proceso_seleccion:
            p = obj.proceso_seleccion
            return {
                "id": str(p.id),
                "codigo": p.codigo,
                "estado": p.estado,
                "requiere_entrevista": p.requiere_entrevista,
                "requiere_evaluacion": p.requiere_evaluacion,
                "requiere_validacion_documental": p.requiere_validacion_documental,
                "total_postulaciones": p.postulaciones.filter(deleted_at__isnull=True).count(),
            }
        return None


class VacanteCreateUpdateSerializer(serializers.ModelSerializer):
    auto_crear_proceso = serializers.BooleanField(write_only=True, default=True)
    responsable_rh_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Vacante
        fields = [
            "id",
            "perfil_cargo",
            "sede",
            "titulo",
            "descripcion_publica",
            "numero_cupos",
            "tipo_contrato",
            "modalidad",
            "rango_salarial_min",
            "rango_salarial_max",
            "mostrar_salario_publico",
            "estado",
            "fecha_apertura",
            "fecha_cierre_estimada",
            "publicada_en_portal",
            "auto_crear_proceso",
            "responsable_rh_id",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        auto_crear_proceso = validated_data.pop("auto_crear_proceso", True)
        responsable_rh_id = validated_data.pop("responsable_rh_id", None)
        vacante = Vacante.objects.create(**validated_data)

        if auto_crear_proceso:
            pc = vacante.perfil_cargo
            requisitos_obligatorios = []
            if getattr(pc, "educacion", None):
                requisitos_obligatorios.append(f"Formación mínima: {pc.educacion}")
            if getattr(pc, "experiencia", None):
                requisitos_obligatorios.append(f"Experiencia mínima: {pc.experiencia}")

            ProcesoSeleccion.objects.create(
                empresa=vacante.empresa,
                vacante=vacante,
                responsable_rh_id=responsable_rh_id,
                requiere_entrevista=True,
                requiere_evaluacion=True,
                requiere_validacion_documental=True,
                requisitos_obligatorios=requisitos_obligatorios,
            )
        return vacante


# -----------------------------------------------------------------------------
# 5. Entrevistas, Evaluaciones y Validaciones
# -----------------------------------------------------------------------------
class EntrevistaSerializer(serializers.ModelSerializer):
    tipo_entrevista_display = serializers.CharField(source="get_tipo_entrevista_display", read_only=True)
    modalidad_display = serializers.CharField(source="get_modalidad_display", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    concepto_display = serializers.CharField(source="get_concepto_display", read_only=True)
    entrevistador_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Entrevista
        fields = [
            "id",
            "postulacion",
            "tipo_entrevista",
            "tipo_entrevista_display",
            "modalidad",
            "modalidad_display",
            "fecha_programada",
            "entrevistador",
            "entrevistador_nombre",
            "enlace_reunion",
            "lugar",
            "estado",
            "estado_display",
            "calificacion",
            "concepto",
            "concepto_display",
            "observaciones",
            "aspectos_evaluados",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_entrevistador_nombre(self, obj):
        if obj.entrevistador:
            return f"{obj.entrevistador.first_name} {obj.entrevistador.last_name}".strip() or obj.entrevistador.username
        return ""


class EvaluacionSerializer(serializers.ModelSerializer):
    tipo_evaluacion_display = serializers.CharField(source="get_tipo_evaluacion_display", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    porcentaje_obtenido = serializers.FloatField(read_only=True)
    evaluador_nombre = serializers.SerializerMethodField()
    archivo_informe_url = serializers.SerializerMethodField()

    class Meta:
        model = Evaluacion
        fields = [
            "id",
            "postulacion",
            "tipo_evaluacion",
            "tipo_evaluacion_display",
            "nombre_prueba",
            "fecha_asignacion",
            "fecha_realizacion",
            "evaluador",
            "evaluador_nombre",
            "puntaje_obtenido",
            "puntaje_maximo",
            "porcentaje_aprobacion",
            "porcentaje_obtenido",
            "estado",
            "estado_display",
            "concepto",
            "archivo_informe",
            "archivo_informe_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_evaluador_nombre(self, obj):
        if obj.evaluador:
            return f"{obj.evaluador.first_name} {obj.evaluador.last_name}".strip() or obj.evaluador.username
        return ""

    def get_archivo_informe_url(self, obj):
        if obj.archivo_informe and hasattr(obj.archivo_informe, "archivo") and obj.archivo_informe.archivo:
            return obj.archivo_informe.archivo.url
        return None


class ValidacionDocumentalSerializer(serializers.ModelSerializer):
    tipo_verificacion_display = serializers.CharField(source="get_tipo_verificacion_display", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    verificado_por_nombre = serializers.SerializerMethodField()
    soporte_archivo_url = serializers.SerializerMethodField()

    class Meta:
        model = ValidacionDocumental
        fields = [
            "id",
            "postulacion",
            "tipo_verificacion",
            "tipo_verificacion_display",
            "entidad_o_contacto",
            "telefono_contacto",
            "verificado_por",
            "verificado_por_nombre",
            "fecha_verificacion",
            "estado",
            "estado_display",
            "detalles_verificacion",
            "soporte_archivo",
            "soporte_archivo_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_verificado_por_nombre(self, obj):
        if obj.verificado_por:
            return f"{obj.verificado_por.first_name} {obj.verificado_por.last_name}".strip() or obj.verificado_por.username
        return ""

    def get_soporte_archivo_url(self, obj):
        if obj.soporte_archivo and hasattr(obj.soporte_archivo, "archivo") and obj.soporte_archivo.archivo:
            return obj.soporte_archivo.archivo.url
        return None


# -----------------------------------------------------------------------------
# 6. Postulación y Trazabilidad (Eventos)
# -----------------------------------------------------------------------------
class PostulacionEventoSerializer(serializers.ModelSerializer):
    tipo_evento_display = serializers.CharField(source="get_tipo_evento_display", read_only=True)
    usuario_nombre = serializers.SerializerMethodField()

    class Meta:
        model = PostulacionEvento
        fields = [
            "id",
            "tipo_evento",
            "tipo_evento_display",
            "estado_anterior",
            "estado_nuevo",
            "descripcion",
            "motivo",
            "es_excepcion",
            "justificacion_excepcion",
            "datos_capturados",
            "usuario",
            "usuario_nombre",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_usuario_nombre(self, obj):
        if obj.usuario:
            return f"{obj.usuario.first_name} {obj.usuario.last_name}".strip() or obj.usuario.username
        return "Sistema"


def calcular_semaforo_etapas(postulacion: Postulacion, proceso: ProcesoSeleccion) -> dict:
    """
    RN-R03: Calcula el estado de semáforo por etapa obligatoria/opcional del proceso.
    Valores posibles de estado: 'no_requerida', 'completada', 'en_curso', 'pendiente'.
    """
    etapas_completadas = postulacion.etapas_completadas or []
    estado_actual = postulacion.estado

    def resolver_estado(requerida: bool, clave_etapa: str, estado_coincidente: str):
        if not requerida:
            return "no_requerida"
        if clave_etapa in etapas_completadas:
            return "completada"
        if estado_actual == estado_coincidente:
            return "en_curso"
        return "pendiente"

    return {
        "entrevista": {
            "requerida": proceso.requiere_entrevista,
            "estado": resolver_estado(proceso.requiere_entrevista, "entrevista", Postulacion.Estado.EN_ENTREVISTA),
        },
        "evaluacion": {
            "requerida": proceso.requiere_evaluacion,
            "estado": resolver_estado(proceso.requiere_evaluacion, "evaluacion", Postulacion.Estado.EN_EVALUACION),
        },
        "validacion_documental": {
            "requerida": proceso.requiere_validacion_documental,
            "estado": resolver_estado(proceso.requiere_validacion_documental, "validacion_documental", Postulacion.Estado.EN_VALIDACION),
        },
    }


class PostulacionListSerializer(serializers.ModelSerializer):
    """
    Lectura liviana de postulación para tablas Kanban y listados dentro del proceso.
    RN-R01: estado es read_only.
    """
    candidato_nombre = serializers.CharField(source="candidato.nombre_completo", read_only=True)
    candidato_documento = serializers.CharField(source="candidato.documento", read_only=True)
    candidato_email = serializers.CharField(source="candidato.email", read_only=True)
    candidato_telefono = serializers.CharField(source="candidato.telefono", read_only=True)
    vacante_titulo = serializers.CharField(source="proceso_seleccion.vacante.titulo", read_only=True)
    vacante_codigo = serializers.CharField(source="proceso_seleccion.vacante.codigo", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    semaforo_etapas = serializers.SerializerMethodField()

    class Meta:
        model = Postulacion
        fields = [
            "id",
            "candidato",
            "candidato_nombre",
            "candidato_documento",
            "candidato_email",
            "candidato_telefono",
            "proceso_seleccion",
            "vacante_codigo",
            "vacante_titulo",
            "estado",
            "estado_display",
            "fecha_postulacion",
            "puntuacion_general",
            "etapas_completadas",
            "es_activa",
            "es_excepcion",
            "semaforo_etapas",
            "created_at",
        ]
        read_only_fields = fields

    def get_semaforo_etapas(self, obj):
        return calcular_semaforo_etapas(obj, obj.proceso_seleccion)


class PostulacionDetailSerializer(serializers.ModelSerializer):
    """
    Detalle completo con histórico de eventos inmutables y registros de etapas.
    RN-R01: estado es read_only.
    """
    candidato = CandidatoDetailSerializer(read_only=True)
    vacante_titulo = serializers.CharField(source="proceso_seleccion.vacante.titulo", read_only=True)
    vacante_codigo = serializers.CharField(source="proceso_seleccion.vacante.codigo", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    autorizado_por_nombre = serializers.SerializerMethodField()
    semaforo_etapas = serializers.SerializerMethodField()
    eventos = PostulacionEventoSerializer(many=True, read_only=True)
    entrevistas = EntrevistaSerializer(many=True, read_only=True)
    evaluaciones = EvaluacionSerializer(many=True, read_only=True)
    validaciones_documentales = ValidacionDocumentalSerializer(many=True, read_only=True)

    class Meta:
        model = Postulacion
        fields = [
            "id",
            "candidato",
            "proceso_seleccion",
            "vacante_codigo",
            "vacante_titulo",
            "estado",
            "estado_display",
            "fecha_postulacion",
            "puntuacion_general",
            "calificacion_requisitos",
            "etapas_completadas",
            "motivo_cierre",
            "es_activa",
            "es_excepcion",
            "justificacion_excepcion",
            "autorizado_por",
            "autorizado_por_nombre",
            "semaforo_etapas",
            "eventos",
            "entrevistas",
            "evaluaciones",
            "validaciones_documentales",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_autorizado_por_nombre(self, obj):
        if obj.autorizado_por:
            return f"{obj.autorizado_por.first_name} {obj.autorizado_por.last_name}".strip() or obj.autorizado_por.username
        return None

    def get_semaforo_etapas(self, obj):
        return calcular_semaforo_etapas(obj, obj.proceso_seleccion)


# -----------------------------------------------------------------------------
# 7. Proceso de Selección
# -----------------------------------------------------------------------------
class ProcesoSeleccionDetailSerializer(serializers.ModelSerializer):
    vacante_detalle = VacanteListSerializer(source="vacante", read_only=True)
    responsable_rh_nombre = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    postulaciones = PostulacionListSerializer(many=True, read_only=True)
    resumen_postulaciones = serializers.SerializerMethodField()

    class Meta:
        model = ProcesoSeleccion
        fields = [
            "id",
            "codigo",
            "vacante",
            "vacante_detalle",
            "responsable_rh",
            "responsable_rh_nombre",
            "requiere_entrevista",
            "requiere_evaluacion",
            "requiere_validacion_documental",
            "requisitos_obligatorios",
            "requisitos_deseables",
            "criterios_evaluacion",
            "estado",
            "estado_display",
            "resumen_postulaciones",
            "postulaciones",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "codigo", "created_at", "updated_at"]

    def get_responsable_rh_nombre(self, obj):
        if obj.responsable_rh:
            return f"{obj.responsable_rh.first_name} {obj.responsable_rh.last_name}".strip() or obj.responsable_rh.username
        return ""

    def get_resumen_postulaciones(self, obj):
        from django.db.models import Count
        conteo = (
            obj.postulaciones.filter(deleted_at__isnull=True)
            .values("estado")
            .annotate(total=Count("id"))
        )
        return {item["estado"]: item["total"] for item in conteo}


class ProcesoSeleccionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcesoSeleccion
        fields = [
            "responsable_rh",
            "requiere_entrevista",
            "requiere_evaluacion",
            "requiere_validacion_documental",
            "requisitos_obligatorios",
            "requisitos_deseables",
            "criterios_evaluacion",
            "estado",
        ]


# -----------------------------------------------------------------------------
# 8. Serializadores de Entrada de Acciones / Transiciones (Write Payloads)
# -----------------------------------------------------------------------------
class PostularCandidatoSerializer(serializers.Serializer):
    """Payload para crear o vincular una postulación."""
    candidato_id = serializers.UUIDField(required=True)
    proceso_seleccion_id = serializers.UUIDField(required=True)


class PreseleccionarActionSerializer(serializers.Serializer):
    """Payload para transición RN-R02: PRESELECCIONADO."""
    calificacion_requisitos = serializers.DictField(
        required=True,
        help_text="Evaluación por requisito: {'experiencia': true, 'titulo': true}",
    )
    puntuacion = serializers.FloatField(required=False, min_value=0.0, max_value=100.0)
    es_excepcion = serializers.BooleanField(default=False)
    justificacion_excepcion = serializers.CharField(required=False, allow_blank=True, default="")


class RegistrarEntrevistaActionSerializer(serializers.Serializer):
    """Payload para registrar y completar una entrevista de candidato."""
    tipo_entrevista = serializers.ChoiceField(
        choices=Entrevista.TipoEntrevista.choices,
        default=Entrevista.TipoEntrevista.INICIAL_RH,
    )
    modalidad = serializers.ChoiceField(
        choices=Entrevista.Modalidad.choices,
        default=Entrevista.Modalidad.VIRTUAL,
    )
    fecha_programada = serializers.DateTimeField(required=True)
    entrevistador_id = serializers.UUIDField(required=False, allow_null=True)
    calificacion = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, allow_null=True
    )
    concepto = serializers.ChoiceField(
        choices=Entrevista.Concepto.choices,
        default=Entrevista.Concepto.FAVORABLE,
    )
    observaciones = serializers.CharField(required=False, allow_blank=True, default="")
    aspectos_evaluados = serializers.DictField(required=False, default=dict)
    enlace_reunion = serializers.CharField(required=False, allow_blank=True, default="")
    lugar = serializers.CharField(required=False, allow_blank=True, default="")


class RegistrarEvaluacionActionSerializer(serializers.Serializer):
    """Payload para registrar y calificar una prueba técnica o psicotécnica."""
    tipo_evaluacion = serializers.ChoiceField(
        choices=Evaluacion.TipoEvaluacion.choices,
        default=Evaluacion.TipoEvaluacion.TECNICA,
    )
    nombre_prueba = serializers.CharField(max_length=255, required=True)
    puntaje_obtenido = serializers.DecimalField(max_digits=5, decimal_places=2, required=True)
    puntaje_maximo = serializers.DecimalField(max_digits=5, decimal_places=2, default=100.0)
    porcentaje_aprobacion = serializers.DecimalField(max_digits=5, decimal_places=2, default=70.0)
    concepto = serializers.CharField(required=False, allow_blank=True, default="")
    evaluador_id = serializers.UUIDField(required=False, allow_null=True)
    archivo_informe_id = serializers.UUIDField(required=False, allow_null=True)


class RegistrarValidacionActionSerializer(serializers.Serializer):
    """Payload para registrar la verificación de documentos o antecedentes."""
    tipo_verificacion = serializers.ChoiceField(
        choices=ValidacionDocumental.TipoVerificacion.choices,
        default=ValidacionDocumental.TipoVerificacion.REFERENCIA_LABORAL,
    )
    entidad_o_contacto = serializers.CharField(max_length=255, required=True)
    telefono_contacto = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    estado = serializers.ChoiceField(
        choices=ValidacionDocumental.Estado.choices,
        default=ValidacionDocumental.Estado.VERIFICADO_CONFORME,
    )
    detalles_verificacion = serializers.CharField(required=False, allow_blank=True, default="")
    soporte_archivo_id = serializers.UUIDField(required=False, allow_null=True)


class SeleccionarActionSerializer(serializers.Serializer):
    """Payload para seleccionar candidato con RN-R06 y RN-R09."""
    notas_finales = serializers.CharField(required=False, allow_blank=True, default="")
    es_excepcion = serializers.BooleanField(default=False)
    justificacion_excepcion = serializers.CharField(required=False, allow_blank=True, default="")


class CerrarPostulacionActionSerializer(serializers.Serializer):
    """Payload para cierre con motivo obligatorio (RN-R04)."""
    nuevo_estado = serializers.ChoiceField(
        choices=[
            Postulacion.Estado.NO_SELECCIONADO,
            Postulacion.Estado.RETIRO_CANDIDATURA,
            Postulacion.Estado.NO_CONTINUO,
        ],
        required=True,
    )
    motivo = serializers.CharField(required=True, min_length=5)
    datos_adicionales = serializers.DictField(required=False, default=dict)


class ReabrirPostulacionActionSerializer(serializers.Serializer):
    """Payload para reapertura excepcional con justificación obligatoria (RN-R07/RN-R09)."""
    justificacion = serializers.CharField(required=True, min_length=10)
