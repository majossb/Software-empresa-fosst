from django.apps import AppConfig


class ReclutamientoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reclutamiento"
    verbose_name = "Reclutamiento y Selección"

    def ready(self):
        try:
            import apps.reclutamiento.signals  # noqa: F401
        except ImportError:
            pass
