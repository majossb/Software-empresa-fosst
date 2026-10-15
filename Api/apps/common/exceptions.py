"""
apps/common/exceptions.py
Manejador global de excepciones para FOSST V.I.D.A.

REGLAS:
- Ningún traceback, SQL ni nombre interno llega al navegador.
- Cada error tiene un `code` estable que el frontend usa para mostrar mensajes.
- Los detalles técnicos van a los logs de Python.
"""
import logging
from django.db import IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import Http404
from rest_framework import status as drf_status
from rest_framework.views import exception_handler as drf_default_handler
from rest_framework.response import Response
from rest_framework.exceptions import (
    ValidationError as DRFValidationError,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied as DRFPermissionDenied,
    NotFound,
)

logger = logging.getLogger("fosst.errors")

# ─────────────────────────────────────────────────────────────
# Mapa de restricciones de BD a códigos de error
# ─────────────────────────────────────────────────────────────
CONSTRAINT_CODE_MAP: dict[str, tuple[str, str, str | None]] = {
    # (constraint_name): (code, mensaje_amigable, field)
    "uq_usuario_empresa_documento_rol": (
        "DOCUMENT_ALREADY_EXISTS",
        "Este documento ya está registrado en la empresa.",
        "responsable_documento",
    ),
    "uq_trabajador_empresa_documento": (
        "DOCUMENT_ALREADY_EXISTS",
        "Este documento ya está registrado como trabajador.",
        "documento",
    ),
    "unique_candidato_documento_empresa": (
        "DOCUMENT_ALREADY_EXISTS",
        "Este documento ya está registrado como candidato.",
        "documento",
    ),
    "unique_candidato_email_empresa": (
        "EMAIL_ALREADY_EXISTS",
        "Este correo ya está registrado como candidato.",
        "email",
    ),
    "unique_fuente_nombre_por_empresa": (
        "VALIDATION_ERROR",
        "Ya existe una fuente de reclutamiento con ese nombre.",
        "nombre",
    ),
    "unique_perfil_cargo_codigo": (
        "VALIDATION_ERROR",
        "Ya existe un perfil de cargo con ese código.",
        "codigo",
    ),
    "uq_evaluacion_empresa_anio": (
        "VALIDATION_ERROR",
        "Ya existe una evaluación para esta empresa en el año indicado.",
        None,
    ),
}

# Palabras clave en el mensaje de IntegrityError para identificar campo
INTEGRITY_KEYWORD_MAP: list[tuple[str, str, str, str | None]] = [
    ("email", "EMAIL_ALREADY_EXISTS", "Este correo ya está registrado.", "responsable_email"),
    ("nit", "NIT_ALREADY_EXISTS", "Este NIT ya está registrado. Verifica el número ingresado.", "nit"),
    ("username", "DOCUMENT_ALREADY_EXISTS", "Este documento ya está registrado.", "responsable_documento"),
    ("codigo", "VALIDATION_ERROR", "Ya existe un registro con ese código.", "codigo"),
]


def _build_error_response(
    code: str,
    message: str,
    http_status: int,
    field: str | None = None,
    errors: dict | None = None,
) -> Response:
    body: dict = {
        "success": False,
        "code": code,
        "message": message,
    }
    if field:
        body["field"] = field
    if errors:
        body["errors"] = errors

    return Response(body, status=http_status)


def _parse_integrity_error(exc: IntegrityError) -> tuple[str, str, str | None]:
    """
    Intenta identificar qué restricción disparó la IntegrityError.
    Retorna (code, mensaje_amigable, field).
    """
    exc_str = str(exc).lower()

    # 1. Intentar por nombre de constraint
    for constraint_name, (code, msg, field) in CONSTRAINT_CODE_MAP.items():
        if constraint_name in exc_str:
            return code, msg, field

    # 2. Intentar por palabra clave del campo
    for keyword, code, msg, field in INTEGRITY_KEYWORD_MAP:
        if keyword in exc_str:
            return code, msg, field

    # 3. Fallback seguro — nunca exponer exc_str
    return "SERVER_ERROR", "Tenemos un problema temporal. Intenta nuevamente en unos minutos.", None


def _normalize_drf_validation_errors(detail) -> dict:
    """
    Convierte el detail de DRF ValidationError al formato
    {"campo": ["mensaje amigable"]} usando traducciones.
    """
    FIELD_MESSAGE_MAP: dict[str, str] = {
        # Comunes
        "This field is required.": "Este campo es obligatorio.",
        "This field may not be blank.": "Este campo no puede estar vacío.",
        "This field may not be null.": "Este campo es obligatorio.",
        "Enter a valid email address.": "Ingresa un correo electrónico válido.",
        "A valid integer is required.": "Ingresa un número entero válido.",
        "Ensure this value is greater than or equal to 1.": "Ingresa un número entero mayor que cero.",
        "Ensure this value is less than or equal to 5.": "El valor máximo permitido es 5.",
        # Django auth
        "This password is too short. It must contain at least 8 characters.": "La contraseña debe tener mínimo 8 caracteres.",
        "This password is too common.": "La contraseña es demasiado común. Elige una más segura.",
        "This password is entirely numeric.": "La contraseña no puede ser completamente numérica.",
    }

    def translate(msg: str) -> str:
        return FIELD_MESSAGE_MAP.get(msg, msg)

    if isinstance(detail, list):
        return {"non_field_errors": [translate(str(m)) for m in detail]}

    if isinstance(detail, dict):
        normalized: dict = {}
        for field, messages in detail.items():
            if isinstance(messages, list):
                normalized[field] = [translate(str(m)) for m in messages]
            elif isinstance(messages, dict):
                # Nested serializer errors — flatten one level
                normalized[field] = [translate(str(v)) for vals in messages.values() for v in (vals if isinstance(vals, list) else [vals])]
            else:
                normalized[field] = [translate(str(messages))]
        return normalized

    return {"non_field_errors": [translate(str(detail))]}


def custom_exception_handler(exc, context):
    """
    Manejador global de excepciones para DRF.

    Registrado en settings.py:
        REST_FRAMEWORK = {
            "EXCEPTION_HANDLER": "apps.common.exceptions.custom_exception_handler"
        }
    """
    request = context.get("request")
    view = context.get("view")
    endpoint = getattr(request, "path", "unknown") if request else "unknown"
    method = getattr(request, "method", "unknown") if request else "unknown"
    user_info = "anon"
    if request and hasattr(request, "user") and request.user and request.user.is_authenticated:
        user_info = str(getattr(request.user, "email", request.user.pk))

    # ── 1. DRF ValidationError → errores de campo amigables ───────────
    if isinstance(exc, DRFValidationError):
        normalized = _normalize_drf_validation_errors(exc.detail)
        # Mensaje global resumido
        first_field = next(iter(normalized), "non_field_errors")
        first_msgs = normalized.get(first_field, ["Error de validación."])
        global_msg = first_msgs[0] if first_msgs else "Revisa los campos del formulario."
        if len(normalized) > 1:
            global_msg = "No pudimos continuar. Revisa los campos marcados."

        return _build_error_response(
            code="VALIDATION_ERROR",
            message=global_msg,
            http_status=exc.status_code,
            errors=normalized,
        )

    # ── 2. Django ValidationError ──────────────────────────────────────
    if isinstance(exc, DjangoValidationError):
        msgs = exc.messages if hasattr(exc, "messages") else [str(exc)]
        logger.warning("Django ValidationError en %s %s [user=%s]: %s", method, endpoint, user_info, msgs)
        return _build_error_response(
            code="VALIDATION_ERROR",
            message=msgs[0] if msgs else "Dato inválido.",
            http_status=drf_status.HTTP_400_BAD_REQUEST,
        )

    # ── 3. IntegrityError de base de datos ─────────────────────────────
    if isinstance(exc, IntegrityError):
        code, msg, field = _parse_integrity_error(exc)
        logger.error(
            "IntegrityError en %s %s [user=%s]: %s",
            method, endpoint, user_info, str(exc),
            exc_info=True,
        )
        if code == "SERVER_ERROR":
            return _build_error_response(
                code=code,
                message=msg,
                http_status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        errors_map = {field: [msg]} if field else None
        return _build_error_response(
            code=code,
            message=msg,
            http_status=drf_status.HTTP_409_CONFLICT,
            field=field,
            errors=errors_map,
        )

    # ── 4. Http404 / ObjectDoesNotExist ───────────────────────────────
    if isinstance(exc, (Http404, NotFound, ObjectDoesNotExist)):
        logger.info("404 en %s %s [user=%s]", method, endpoint, user_info)
        return _build_error_response(
            code="RESOURCE_NOT_FOUND",
            message="El recurso solicitado no existe.",
            http_status=drf_status.HTTP_404_NOT_FOUND,
        )

    # ── 5. PermissionDenied ────────────────────────────────────────────
    if isinstance(exc, (PermissionDenied, DRFPermissionDenied)):
        return _build_error_response(
            code="PERMISSION_DENIED",
            message="No tienes permiso para realizar esta acción.",
            http_status=drf_status.HTTP_403_FORBIDDEN,
        )

    # ── 6. AuthenticationFailed / NotAuthenticated ─────────────────────
    if isinstance(exc, AuthenticationFailed):
        return _build_error_response(
            code="INVALID_CREDENTIALS",
            message="Las credenciales proporcionadas no son válidas.",
            http_status=drf_status.HTTP_401_UNAUTHORIZED,
        )

    if isinstance(exc, NotAuthenticated):
        return _build_error_response(
            code="NOT_AUTHENTICATED",
            message="Debes iniciar sesión para acceder a este recurso.",
            http_status=drf_status.HTTP_401_UNAUTHORIZED,
        )

    # ── 7. Delegar al handler default de DRF (ThrottleExceeded, etc.) ──
    response = drf_default_handler(exc, context)
    if response is not None:
        # Envolver respuesta existente en formato estándar
        data = response.data
        if isinstance(data, dict) and "success" in data:
            return response  # Ya tiene el formato estándar

        code = "SERVER_ERROR"
        message = "Tenemos un problema temporal. Intenta nuevamente en unos minutos."

        if isinstance(data, dict):
            if "detail" in data:
                detail_str = str(data["detail"])
                # Throttle
                if "throttl" in detail_str.lower() or "request was throttled" in detail_str.lower():
                    code = "RATE_LIMIT_EXCEEDED"
                    message = "Has realizado demasiadas solicitudes. Espera unos minutos e intenta nuevamente."
                else:
                    message = detail_str
            elif "message" in data:
                message = str(data["message"])
                code = data.get("code", "SERVER_ERROR")

        response.data = {
            "success": False,
            "code": code,
            "message": message,
        }
        return response

    # ── 8. Excepción no controlada → 500 limpio ────────────────────────
    logger.error(
        "Excepción no controlada en %s %s [user=%s]: %s",
        method, endpoint, user_info, type(exc).__name__,
        exc_info=True,
    )
    return _build_error_response(
        code="SERVER_ERROR",
        message="Tenemos un problema temporal. Intenta nuevamente en unos minutos.",
        http_status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
