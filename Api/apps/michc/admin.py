from django.contrib import admin
from .models import EvaluacionHabilitacion, DetalleCumplimientoRequisito


class DetalleCumplimientoInline(admin.TabularInline):
    model = DetalleCumplimientoRequisito
    extra = 0
    readonly_fields = ["tipo_requisito", "requisito_descripcion", "cumple", "observacion", "created_at"]


@admin.register(EvaluacionHabilitacion)
class EvaluacionHabilitacionAdmin(admin.ModelAdmin):
    list_display = [
        "trabajador", "perfil_cargo", "porcentaje_cumplimiento",
        "semaforo", "estado_habilitacion", "compatibilidad", "nivel_atencion", "calculado_at"
    ]
    list_filter = ["semaforo", "estado_habilitacion", "compatibilidad", "nivel_atencion"]
    search_fields = ["trabajador__nombre", "trabajador__documento", "perfil_cargo__nombre_cargo"]
    readonly_fields = [
        "porcentaje_cumplimiento", "semaforo", "estado_habilitacion",
        "compatibilidad", "nivel_atencion", "interpretacion_ia",
        "recomendacion_ia", "contexto_hash", "calculado_at"
    ]
    inlines = [DetalleCumplimientoInline]


@admin.register(DetalleCumplimientoRequisito)
class DetalleCumplimientoRequisitoAdmin(admin.ModelAdmin):
    list_display = ["evaluacion_habilitacion", "tipo_requisito", "requisito_descripcion", "cumple"]
    list_filter = ["tipo_requisito", "cumple"]
    search_fields = ["requisito_descripcion", "observacion"]
