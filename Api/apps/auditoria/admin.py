from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("accion", "usuario", "empresa", "ip", "created_at")
    list_filter = ("accion", "created_at")
    search_fields = ("usuario__documento", "usuario__email", "ip")
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False  # los audit logs solo se crean desde el código, nunca manualmente
