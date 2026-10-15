"""
Serializadores para el Portal Público del Candidato — FOSST V.I.D.A.
Fase E: Vacantes públicas, postulación anónima con Habeas Data, OTP y consulta de postulaciones.
"""
from rest_framework import serializers
from apps.reclutamiento.models import (
    Vacante,
    Candidato,
    PerfilCandidato,
    Postulacion,
    TokenAccesoCandidato,
)


class VacantePublicaListSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.CharField(source="empresa.nombre", read_only=True)
    sede_ciudad = serializers.CharField(source="sede.ciudad", read_only=True, default="")
    modalidad_display = serializers.CharField(source="get_modalidad_display", read_only=True)
    salario_display = serializers.SerializerMethodField()

    class Meta:
        model = Vacante
        fields = [
            "id",
            "codigo",
            "titulo",
            "slug",
            "empresa_nombre",
            "sede_ciudad",
            "modalidad",
            "modalidad_display",
            "tipo_contrato",
            "numero_cupos",
            "salario_display",
            "fecha_cierre_estimada",
            "created_at",
        ]

    def get_salario_display(self, obj):
        if not obj.mostrar_salario_publico:
            return "A convenir"
        if obj.rango_salarial_min and obj.rango_salarial_max:
            return f"${obj.rango_salarial_min:,.0f} - ${obj.rango_salarial_max:,.0f}"
        if obj.rango_salarial_min:
            return f"Desde ${obj.rango_salarial_min:,.0f}"
        return "A convenir"


class VacantePublicaDetailSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.CharField(source="empresa.nombre", read_only=True)
    sede_ciudad = serializers.CharField(source="sede.ciudad", read_only=True, default="")
    modalidad_display = serializers.CharField(source="get_modalidad_display", read_only=True)
    salario_display = serializers.SerializerMethodField()
    requisitos_obligatorios = serializers.SerializerMethodField()
    requisitos_deseables = serializers.SerializerMethodField()

    class Meta:
        model = Vacante
        fields = [
            "id",
            "codigo",
            "titulo",
            "slug",
            "empresa_nombre",
            "sede_ciudad",
            "descripcion_publica",
            "modalidad",
            "modalidad_display",
            "tipo_contrato",
            "numero_cupos",
            "salario_display",
            "requisitos_obligatorios",
            "requisitos_deseables",
            "fecha_cierre_estimada",
            "created_at",
        ]

    def get_salario_display(self, obj):
        if not obj.mostrar_salario_publico:
            return "A convenir"
        if obj.rango_salarial_min and obj.rango_salarial_max:
            return f"${obj.rango_salarial_min:,.0f} - ${obj.rango_salarial_max:,.0f}"
        if obj.rango_salarial_min:
            return f"Desde ${obj.rango_salarial_min:,.0f}"
        return "A convenir"

    def get_requisitos_obligatorios(self, obj):
        if hasattr(obj, "proceso_seleccion") and obj.proceso_seleccion:
            return obj.proceso_seleccion.requisitos_obligatorios or []
        return []

    def get_requisitos_deseables(self, obj):
        if hasattr(obj, "proceso_seleccion") and obj.proceso_seleccion:
            return obj.proceso_seleccion.requisitos_deseables or []
        return []


class PostulacionPublicaCreateSerializer(serializers.Serializer):
    """
    Payload para postulación anónima desde el portal público de empleo.
    """
    tipo_documento = serializers.ChoiceField(
        choices=Candidato.TipoDocumento.choices,
        default=Candidato.TipoDocumento.CC,
    )
    documento = serializers.CharField(max_length=50, required=True)
    nombres = serializers.CharField(max_length=150, required=True)
    apellidos = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    telefono = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    ciudad = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    direccion = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    autoriza_tratamiento_datos = serializers.BooleanField(required=True)
    fuente_reclutamiento_id = serializers.UUIDField(required=False, allow_null=True)
    fuente_detalle = serializers.CharField(max_length=255, required=False, allow_blank=True, default="Portal Web")

    # Datos de perfil
    titulo_profesional = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    nivel_educativo = serializers.ChoiceField(
        choices=PerfilCandidato.NivelEducativo.choices,
        required=False,
        default=PerfilCandidato.NivelEducativo.UNIVERSITARIO,
    )
    resumen_profesional = serializers.CharField(required=False, allow_blank=True, default="")
    anios_experiencia = serializers.DecimalField(
        max_digits=4, decimal_places=1, required=False, default=0.0
    )
    aspiracion_salarial = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    archivo_cv_id = serializers.UUIDField(required=False, allow_null=True)

    def validate_autoriza_tratamiento_datos(self, value):
        if not value:
            raise serializers.ValidationError(
                "Es obligatorio autorizar el tratamiento de datos personales conforme a la Ley 1581 de 2012."
            )
        return value


class SolicitarAccesoOTPSerializer(serializers.Serializer):
    """Solicitud de OTP al correo electrónico."""
    email = serializers.EmailField(required=True)


class VerificarOTPSerializer(serializers.Serializer):
    """Validación del código OTP de 6 dígitos."""
    email = serializers.EmailField(required=True)
    codigo_otp = serializers.CharField(max_length=6, min_length=6, required=True)


class PostulacionCandidatoConsultaSerializer(serializers.ModelSerializer):
    """
    Vista de consulta de postulación para el candidato (sin exponer notas confidenciales).
    """
    vacante_titulo = serializers.CharField(source="proceso_seleccion.vacante.titulo", read_only=True)
    vacante_codigo = serializers.CharField(source="proceso_seleccion.vacante.codigo", read_only=True)
    empresa_nombre = serializers.CharField(source="empresa.nombre", read_only=True)
    estado_publico = serializers.SerializerMethodField()
    etapa_actual = serializers.SerializerMethodField()

    class Meta:
        model = Postulacion
        fields = [
            "id",
            "vacante_codigo",
            "vacante_titulo",
            "empresa_nombre",
            "fecha_postulacion",
            "estado_publico",
            "etapa_actual",
            "es_activa",
        ]

    def get_estado_publico(self, obj):
        # Mapeo amigable para el candidato
        mapeo = {
            Postulacion.Estado.POSTULADO: "Postulación Recibida",
            Postulacion.Estado.EN_REVISION: "En Revisión de Hoja de Vida",
            Postulacion.Estado.PRESELECCIONADO: "Preseleccionado",
            Postulacion.Estado.EN_ENTREVISTA: "En Etapa de Entrevistas",
            Postulacion.Estado.EN_EVALUACION: "En Pruebas y Evaluaciones",
            Postulacion.Estado.EN_VALIDACION: "En Validación de Referencias",
            Postulacion.Estado.SELECCIONADO: "¡Seleccionado!",
            Postulacion.Estado.NO_SELECCIONADO: "Proceso Concluido",
            Postulacion.Estado.RETIRO_CANDIDATURA: "Candidatura Retirada",
            Postulacion.Estado.NO_CONTINUO: "Proceso No Continuado",
        }
        return mapeo.get(obj.estado, obj.get_estado_display())

    def get_etapa_actual(self, obj):
        return obj.get_estado_display()


class CandidatoPerfilConsultaSerializer(serializers.ModelSerializer):
    """
    Datos de perfil del candidato autenticado para autocompletado y 1-click apply.
    """
    titulo_profesional = serializers.CharField(source="perfil.titulo_profesional", read_only=True, default="")
    nivel_educativo = serializers.CharField(source="perfil.nivel_educativo", read_only=True, default="universitario")
    resumen_profesional = serializers.CharField(source="perfil.resumen_profesional", read_only=True, default="")
    anios_experiencia = serializers.DecimalField(source="perfil.anios_experiencia", max_digits=4, decimal_places=1, read_only=True, default=0.0)
    aspiracion_salarial = serializers.DecimalField(source="perfil.aspiracion_salarial", max_digits=12, decimal_places=2, read_only=True, allow_null=True)
    ultima_hoja_vida = serializers.SerializerMethodField()

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
            "titulo_profesional",
            "nivel_educativo",
            "resumen_profesional",
            "anios_experiencia",
            "aspiracion_salarial",
            "ultima_hoja_vida",
        ]

    def get_ultima_hoja_vida(self, obj):
        doc = obj.documentos.filter(
            tipo_documento="hoja_de_vida"
        ).select_related("archivo").order_by("-created_at").first()
        if doc and doc.archivo:
            return {
                "id": str(doc.archivo.id),
                "nombre": doc.archivo.nombre,
                "url": doc.archivo.url,
                "tamanio_kb": doc.archivo.tamanio_kb,
            }
        return None


class RetirarCandidaturaSerializer(serializers.Serializer):
    """Retiro voluntario de candidatura."""
    motivo = serializers.CharField(
        required=False,
        allow_blank=True,
        default="Retiro voluntario solicitado por el candidato en el portal",
    )
