from django.apps import AppConfig


class FormacionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.formacion"
    verbose_name = "Formación y Desarrollo — Matriz de Competencias del Cargo (MCC)"

    def ready(self):
        import apps.formacion.signals  # noqa: F401
