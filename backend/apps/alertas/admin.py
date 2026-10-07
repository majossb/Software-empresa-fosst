from django.contrib import admin
from .models import ReglaAlerta


@admin.register(ReglaAlerta)
class ReglaAlertaAdmin(admin.ModelAdmin):
    list_display = ["codigo", "nombre", "modelo_origen", "campo_fecha", "dias_anticipacion", "nivel_criticidad", "activa", "empresa"]
    list_filter = ["modelo_origen", "nivel_criticidad", "activa", "empresa"]
    search_fields = ["codigo", "nombre", "mensaje_template"]
