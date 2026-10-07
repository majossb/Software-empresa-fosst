from django.contrib import admin
from .models import Empresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "nit", "estado", "nivel_riesgo", "created_at")
    list_filter = ("estado", "nivel_riesgo")
    search_fields = ("nombre", "nit")
