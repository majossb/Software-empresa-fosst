from django.contrib import admin
from .models import (
    FuenteReclutamiento,
    Candidato,
    PerfilCandidato,
    Vacante,
    ProcesoSeleccion,
    Postulacion,
    PostulacionEvento,
    Entrevista,
    Evaluacion,
    ValidacionDocumental,
    CandidatoDocumento,
    TokenAccesoCandidato,
)


class PerfilCandidatoInline(admin.StackedInline):
    model = PerfilCandidato
    can_delete = False
    extra = 0


class CandidatoDocumentoInline(admin.TabularInline):
    model = CandidatoDocumento
    extra = 0


class EntrevistaInline(admin.TabularInline):
    model = Entrevista
    extra = 0


class EvaluacionInline(admin.TabularInline):
    model = Evaluacion
    extra = 0


class ValidacionDocumentalInline(admin.TabularInline):
    model = ValidacionDocumental
    extra = 0


class PostulacionEventoInline(admin.TabularInline):
    model = PostulacionEvento
    extra = 0
    readonly_fields = ("tipo_evento", "estado_anterior", "estado_nuevo", "descripcion", "motivo", "es_excepcion", "usuario", "created_at")
    can_delete = False


@admin.register(FuenteReclutamiento)
class FuenteReclutamientoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "empresa", "activo", "es_sistema", "created_at")
    list_filter = ("activo", "es_sistema", "empresa")
    search_fields = ("nombre", "descripcion")


@admin.register(Candidato)
class CandidatoAdmin(admin.ModelAdmin):
    list_display = ("tipo_documento", "documento", "nombre_completo", "email", "telefono", "empresa", "created_at")
    list_filter = ("tipo_documento", "empresa", "autoriza_tratamiento_datos")
    search_fields = ("documento", "nombres", "apellidos", "email")
    inlines = [PerfilCandidatoInline, CandidatoDocumentoInline]


@admin.register(Vacante)
class VacanteAdmin(admin.ModelAdmin):
    list_display = ("codigo", "titulo", "perfil_cargo", "sede", "empresa", "numero_cupos", "numero_seleccionados", "estado", "publicada_en_portal")
    list_filter = ("estado", "modalidad", "publicada_en_portal", "empresa")
    search_fields = ("codigo", "titulo", "descripcion_publica")


@admin.register(ProcesoSeleccion)
class ProcesoSeleccionAdmin(admin.ModelAdmin):
    list_display = ("codigo", "vacante", "responsable_rh", "empresa", "estado", "created_at")
    list_filter = ("estado", "requiere_entrevista", "requiere_evaluacion", "requiere_validacion_documental", "empresa")
    search_fields = ("codigo", "vacante__titulo")


@admin.register(Postulacion)
class PostulacionAdmin(admin.ModelAdmin):
    list_display = ("candidato", "proceso_seleccion", "estado", "fecha_postulacion", "puntuacion_general", "es_excepcion")
    list_filter = ("estado", "es_excepcion", "empresa")
    search_fields = ("candidato__nombres", "candidato__apellidos", "candidato__documento", "proceso_seleccion__vacante__titulo")
    inlines = [EntrevistaInline, EvaluacionInline, ValidacionDocumentalInline, PostulacionEventoInline]
    readonly_fields = ("estado", "fecha_postulacion")


@admin.register(Entrevista)
class EntrevistaAdmin(admin.ModelAdmin):
    list_display = ("postulacion", "tipo_entrevista", "modalidad", "fecha_programada", "estado", "concepto", "calificacion")
    list_filter = ("tipo_entrevista", "modalidad", "estado", "concepto")
    search_fields = ("postulacion__candidato__nombres", "postulacion__candidato__documento")


@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ("nombre_prueba", "postulacion", "tipo_evaluacion", "puntaje_obtenido", "puntaje_maximo", "estado")
    list_filter = ("tipo_evaluacion", "estado")
    search_fields = ("nombre_prueba", "postulacion__candidato__nombres")


@admin.register(ValidacionDocumental)
class ValidacionDocumentalAdmin(admin.ModelAdmin):
    list_display = ("tipo_verificacion", "entidad_o_contacto", "postulacion", "estado", "fecha_verificacion")
    list_filter = ("tipo_verificacion", "estado")
    search_fields = ("entidad_o_contacto", "postulacion__candidato__nombres")


@admin.register(PostulacionEvento)
class PostulacionEventoAdmin(admin.ModelAdmin):
    list_display = ("postulacion", "tipo_evento", "estado_anterior", "estado_nuevo", "usuario", "created_at")
    list_filter = ("tipo_evento", "es_excepcion")
    search_fields = ("postulacion__candidato__nombres", "postulacion__candidato__documento", "descripcion")
    readonly_fields = ("postulacion", "tipo_evento", "estado_anterior", "estado_nuevo", "descripcion", "motivo", "es_excepcion", "justificacion_excepcion", "datos_capturados", "usuario", "created_at")


@admin.register(TokenAccesoCandidato)
class TokenAccesoCandidatoAdmin(admin.ModelAdmin):
    list_display = ("candidato", "codigo_otp", "expira_en", "usado", "created_at")
    list_filter = ("usado",)
    search_fields = ("candidato__email", "candidato__documento", "token")
