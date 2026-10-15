from django.apps import AppConfig


class GestionHumanaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.gestion_humana"
    verbose_name = "Gestión Humana y Administración Laboral"

    def ready(self):
        import apps.gestion_humana.signals  # noqa: F401
