from django.contrib import admin
from .models import Brecha, BrechaOrigen, BrechaEvento, BrechaAccion


class BrechaOrigenInline(admin.TabularInline):
    model = BrechaOrigen
    extra = 0
    readonly_fields = ["modulo_origen", "content_type", "object_id", "es_origen_principal", "created_at"]


class BrechaEventoInline(admin.TabularInline):
    model = BrechaEvento
    extra = 0
    readonly_fields = ["tipo_evento", "descripcion", "usuario", "created_at"]


class BrechaAccionInline(admin.TabularInline):
    model = BrechaAccion
    extra = 0


@admin.register(Brecha)
class BrechaAdmin(admin.ModelAdmin):
    list_display = ["codigo", "empresa", "clasificacion", "estado", "nivel_atencion", "detectado_por", "fecha_deteccion"]
    list_filter = ["estado", "clasificacion", "nivel_atencion", "empresa"]
    search_fields = ["codigo", "descripcion_automatica", "descripcion_complementaria"]
    readonly_fields = ["codigo", "fecha_deteccion", "created_at", "updated_at"]
    inlines = [BrechaOrigenInline, BrechaEventoInline, BrechaAccionInline]


@admin.register(BrechaOrigen)
class BrechaOrigenAdmin(admin.ModelAdmin):
    list_display = ["brecha", "modulo_origen", "es_origen_principal", "created_at"]
    list_filter = ["modulo_origen"]


@admin.register(BrechaEvento)
class BrechaEventoAdmin(admin.ModelAdmin):
    list_display = ["brecha", "tipo_evento", "usuario", "created_at"]
    list_filter = ["tipo_evento"]


@admin.register(BrechaAccion)
class BrechaAccionAdmin(admin.ModelAdmin):
    list_display = ["brecha", "descripcion", "fecha_programada", "estado"]
    list_filter = ["estado"]
