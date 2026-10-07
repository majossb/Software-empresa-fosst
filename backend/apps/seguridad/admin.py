from django.contrib import admin
from .models import DispositivoConocido, EventoRiesgo


@admin.register(DispositivoConocido)
class DispositivoConocidoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "ip", "navegador", "sistema_operativo", "ultima_vez")
    search_fields = ("usuario__documento", "usuario__email", "ip")


@admin.register(EventoRiesgo)
class EventoRiesgoAdmin(admin.ModelAdmin):
    list_display = ("tipo", "usuario", "ip", "created_at")
    list_filter = ("tipo", "created_at")
