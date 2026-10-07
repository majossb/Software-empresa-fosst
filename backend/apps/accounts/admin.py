from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CodigoOTP, TokenActivacion, TokenRecuperacion, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "documento", "rol", "empresa", "activo", "email_verificado", "is_active")
    list_filter = ("rol", "activo", "empresa")
    search_fields = ("documento", "email", "first_name", "last_name")


admin.site.register(TokenActivacion)
admin.site.register(CodigoOTP)
admin.site.register(TokenRecuperacion)
