from django.contrib import admin
from .models import EvaluacionCompetencia


@admin.register(EvaluacionCompetencia)
class EvaluacionCompetenciaAdmin(admin.ModelAdmin):
    list_display = [
        "trabajador", "cargo_competencia", "nivel_alcanzado",
        "brecha_calculada", "fecha_evaluacion", "metodo", "evaluado_por"
    ]
    list_filter = ["metodo", "brecha_calculada", "fecha_evaluacion"]
    search_fields = ["trabajador__nombre", "cargo_competencia__nombre", "observacion"]
    readonly_fields = ["brecha_calculada", "created_at", "updated_at"]
