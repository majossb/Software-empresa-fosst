from django.contrib import admin
from .models import NovedadLaboral, ExamenMedicoOcupacional, LicenciaConduccion


@admin.register(NovedadLaboral)
class NovedadLaboralAdmin(admin.ModelAdmin):
    list_display = ["trabajador", "tipo", "fecha_inicio", "fecha_fin", "dias", "created_by"]
    list_filter = ["tipo", "fecha_inicio"]
    search_fields = ["trabajador__nombre", "trabajador__documento", "observaciones"]


@admin.register(ExamenMedicoOcupacional)
class ExamenMedicoOcupacionalAdmin(admin.ModelAdmin):
    list_display = ["trabajador", "tipo", "fecha_examen", "fecha_vencimiento", "concepto_aptitud", "presenta_restricciones"]
    list_filter = ["tipo", "concepto_aptitud", "presenta_restricciones"]
    search_fields = ["trabajador__nombre", "trabajador__documento", "descripcion_restricciones"]


@admin.register(LicenciaConduccion)
class LicenciaConduccionAdmin(admin.ModelAdmin):
    list_display = ["trabajador", "categoria", "fecha_vencimiento", "presenta_restricciones"]
    list_filter = ["categoria", "presenta_restricciones"]
    search_fields = ["trabajador__nombre", "trabajador__documento"]
