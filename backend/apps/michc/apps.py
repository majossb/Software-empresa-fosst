from django.apps import AppConfig


class MichcConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.michc"
    verbose_name = "MICHC — Matriz Inteligente de Cumplimiento y Habilitación del Cargo"

    def ready(self):
        import apps.michc.signals  # noqa: F401
