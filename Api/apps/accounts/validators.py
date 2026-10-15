import re
from django.core.exceptions import ValidationError


def validar_politica_password(password: str):
    """
    Política Única de Seguridad de Contraseñas FOSST V.I.D.A.
    - Mínimo 8 caracteres
    - Al menos 1 letra mayúscula (A-Z)
    - Al menos 1 letra minúscula (a-z)
    - Al menos 1 número (0-9)
    - Al menos 1 carácter especial
    """
    if not password or len(password) < 8:
        raise ValidationError("La contraseña debe tener al menos 8 caracteres.")
    if not re.search(r"[A-Z]", password):
        raise ValidationError("La contraseña debe contener al menos una letra mayúscula (A-Z).")
    if not re.search(r"[a-z]", password):
        raise ValidationError("La contraseña debe contener al menos una letra minúscula (a-z).")
    if not re.search(r"[0-9]", password):
        raise ValidationError("La contraseña debe contener al menos un número (0-9).")
    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValidationError("La contraseña debe contener al menos un carácter especial (ej. !@#$%^&*).")


class ComplejidadPasswordValidator:
    """
    Validador de contraseñas compatible con Django AUTH_PASSWORD_VALIDATORS.
    """
    def validate(self, password, user=None):
        validar_politica_password(password)

    def get_help_text(self):
        return "Tu contraseña debe tener al menos 8 caracteres, incluir mayúsculas, minúsculas, números y caracteres especiales."


def validar_nombre_persona(value: str, field_name: str = "Nombre"):
    """
    Valida nombres en español permitiendo tildes, diéresis, ñ, espacios, apóstrofes y guiones.
    """
    if not value or not value.strip():
        raise ValidationError(f"El campo {field_name.lower()} es obligatorio.")
    regex = r"^[a-zA-ZáéíóúÁÉÍÓÚüÜñÑ\s'\-]+$"
    if not re.match(regex, value.strip()):
        raise ValidationError(f"El {field_name.lower()} solo puede contener letras y espacios.")


def validar_telefono(value: str):
    """
    Valida números telefónicos permitiendo formato nacional e internacional.
    """
    if value and not re.match(r"^\+?[\d\s\-\(\)]{7,20}$", value.strip()):
        raise ValidationError("Introduce un número de teléfono válido.")
