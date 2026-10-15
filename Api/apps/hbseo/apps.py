from django.apps import AppConfig


class HbseoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.hbseo"
    verbose_name = "HBSEO — Historial de Brechas, Subsanaciones y Evolución Organizacional"

    def ready(self):
        import apps.hbseo.signals  # noqa: F401
