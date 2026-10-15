from django.apps import AppConfig

class PerfilcargoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.perfilcargo"

    def ready(self):
        from . import signals  # noqa: F401 — registra los receivers de RN-11
