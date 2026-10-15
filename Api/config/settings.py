
import os
from datetime import timedelta
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1",'.trycloudflare.com',])
ENVIRONMENT = env("ENVIRONMENT", default="development").lower()

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Terceros
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "axes",
    "django_filters",
    "drf_spectacular",
    "storages",

    # Apps propias
    "apps.accounts",
    "apps.empresas",
    "apps.auditoria",
    "apps.seguridad",
    "apps.planes",
    "apps.organizacion",
    "apps.estandares",
    "apps.evidencias",
    "apps.informes",
    "apps.hallazgos",
    "apps.capacitaciones",
    "apps.calendario",
    "apps.perfilcargo",
    "apps.dashboard",

    # Fase 2 — Servicio IA genérico + HBSEO
    "apps.ia",
    "apps.hbseo",

    # Fase 3 — Gestión Humana y Motor de Alertas
    "apps.gestion_humana",
    "apps.alertas",

    # Fase 4 — MICHC (Matriz Inteligente de Cumplimiento)
    "apps.michc",

    # Fase 5 — Formación y Desarrollo (MCC)
    "apps.formacion",

    # Módulo 2.1 — Reclutamiento y Selección (FOSST V.I.D.A.)
    "apps.reclutamiento",
]

AUTH_USER_MODEL = "accounts.Usuario"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",                     # bloqueo por intentos fallidos
    "apps.auditoria.middleware.AuditoriaMiddleware",       # registra actividad de cada request
    "apps.seguridad.middleware.DispositivoMiddleware",     # historial de dispositivos / IP
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # plantillas de email (activación, OTP, reset)
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ── Base de datos (PostgreSQL única fuente de verdad) ─────────────────────
DATABASES = {
    "default": env.db("DATABASE_URL", default="postgres://postgres:postgres@localhost:5432/fosst_db")
}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=600)

# ── Almacenamiento de objetos (S3 / MinIO via django-storages) ─────────────
_storage_options = {
    "access_key": env("AWS_ACCESS_KEY_ID", default="minioadmin"),
    "secret_key": env("AWS_SECRET_ACCESS_KEY", default="minioadmin"),
    "bucket_name": env("AWS_STORAGE_BUCKET_NAME", default="fosst-media"),
    "region_name": env("AWS_S3_REGION_NAME", default="us-east-1"),
    "file_overwrite": False,
}
_s3_endpoint = env("AWS_S3_ENDPOINT_URL", default="")
if _s3_endpoint:
    _storage_options["endpoint_url"] = _s3_endpoint

_s3_custom_domain = env("AWS_S3_CUSTOM_DOMAIN", default="")
if _s3_custom_domain:
    _storage_options["custom_domain"] = _s3_custom_domain

STORAGES = {
    "default": {
        "BACKEND": env("STORAGE_BACKEND", default="storages.backends.s3.S3Storage"),
        "OPTIONS": _storage_options,
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

MAX_UPLOAD_SIZE_MB = env.int("MAX_UPLOAD_SIZE_MB", default=20)
ALLOWED_UPLOAD_MIME_TYPES = env.list(
    "ALLOWED_UPLOAD_MIME_TYPES",
    default=[
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv",
    ]
)

# ── Password hashing (Argon2 primero, más robusto que bcrypt) ─────────────
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    {"NAME": "apps.accounts.validators.ComplejidadPasswordValidator"},  # mayúsc/minúsc/número/símbolo
]

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── CORS y CSRF ────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:5173", "http://127.0.0.1:5173"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000"])
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS = [
    "accept", "accept-encoding", "authorization", "content-type",
    "dnt", "origin", "user-agent", "x-requested-with",
]

# ── Seguridad HTTP (cabeceras y cookies) ───────────────────────────────
SECURE_BROWSER_XSS_FILTER = True             # X-XSS-Protection: 1; mode=block
SECURE_CONTENT_TYPE_NOSNIFF = True            # X-Content-Type-Options: nosniff
X_FRAME_OPTIONS = "DENY"                     # Clickjacking: rechaza iframe por terceros
SESSION_COOKIE_HTTPONLY = True                # Previene acceso a cookies via JS
CSRF_COOKIE_HTTPONLY = True                   # CSRF cookie solo por HTTP
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

if ENVIRONMENT in ["uat", "production"]:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ── Django REST Framework ──────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    # Rate limiting global + por endpoint sensible
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",          # No autenticados: 60 req/min (protege login brute-force)
        "user": "200/min",         # Autenticados: 200 req/min (burst cap)
        "login": "10/min",
        "otp": "5/min",
        "password_reset": "5/hour",
        "register": "5/hour",
        "michc_recalcular": "20/min",  # Recálculo manual de MICHC
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    # Renderización: solo JSON en producción (previene HTML debug info leak)
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
    # Manejador global de excepciones — mensajes amigables sin fugas técnicas
    "EXCEPTION_HANDLER": "apps.common.exceptions.custom_exception_handler",
}


# ── JWT (equivalente al jsonwebtoken de Express, pero con refresh + rotación) ──
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": env("JWT_SECRET", default="fosst-jwt-secret-key-default-2026"),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "sub",
}

# ── django-axes: bloqueo por intentos fallidos (usuario + IP) ─────────────
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",   # debe ir primero
    "django.contrib.auth.backends.ModelBackend",
]
AXES_FAILURE_LIMIT = 5                 # intentos antes de bloquear
AXES_COOLOFF_TIME = timedelta(minutes=30)   # tiempo de bloqueo temporal
AXES_LOCKOUT_PARAMETERS = ["username", "ip_address"]   # bloquea por usuario Y por IP
AXES_RESET_ON_SUCCESS = True

# ── Configuración Email (SMTP Nativo Django) ──────────────────────────────
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=30)

DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL",
    default="DiagnostISST <no-reply@diagnostisst.com>",
)
SERVER_EMAIL = env("SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)

FRONTEND_URL = env(
    "FRONTEND_URL",
    default="http://localhost:5173",
)

# ── Parámetros propios del módulo de autenticación ────────────────────────
OTP_EXPIRATION_MINUTES = 5
ACTIVATION_TOKEN_EXPIRATION_HOURS = 48
PASSWORD_RESET_TOKEN_EXPIRATION_HOURS = 1

# ── Cache (redis en prod/uat/dev, LocMemCache en testing) ──────────────────
import sys
TESTING = 'test' in sys.argv if sys.argv else False

REDIS_URL = env("REDIS_URL", default="redis://127.0.0.1:6379/1")

if TESTING:
    EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-cache",
        }
    }
    CELERY_TASK_ALWAYS_EAGER = True
elif ENVIRONMENT in ["uat", "production"] or (REDIS_URL and "127.0.0.1" not in REDIS_URL and "localhost" not in REDIS_URL):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
    CELERY_TASK_ALWAYS_EAGER = False
else:
    import socket
    _redis_active = False
    try:
        _s = socket.socket()
        _s.settimeout(0.5)
        _redis_active = (_s.connect_ex(('127.0.0.1', 6379)) == 0)
        _s.close()
    except Exception:
        _redis_active = False

    if _redis_active:
        CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.redis.RedisCache",
                "LOCATION": REDIS_URL,
            }
        }
        CELERY_TASK_ALWAYS_EAGER = False
    else:
        CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "default-locmem",
            }
        }
        CELERY_TASK_ALWAYS_EAGER = True

# Celery
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "America/Bogota"

# Celery Beat — Programación de tareas periódicas (§5.2)
from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    "revisar-vencimientos-diario": {
        "task": "apps.alertas.tasks.revisar_vencimientos",
        "schedule": crontab(hour=6, minute=0),  # 6:00 AM America/Bogota
    },
    # ── Backup automático de base de datos ──────────────────────────────────
    "backup-bd-diario": {
        "task": "apps.accounts.tasks.backup_database",
        "schedule": crontab(hour=2, minute=0),  # 2:00 AM America/Bogota (hora de menor tráfico)
    },
    # ── Limpieza de backups antiguos (>30 días) cada domingo a las 3:00 AM ─
    "limpiar-backups-antiguos": {
        "task": "apps.accounts.tasks.limpiar_backups_antiguos",
        "schedule": crontab(hour=3, minute=0, day_of_week="sunday"),
    },
}

# ANTHROPIC SDK API KEY
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", default="")

# ── Validaciones de arranque para Ambiente UAT (§3) ───────────────────────
if ENVIRONMENT == "uat":
    from django.core.exceptions import ImproperlyConfigured

    if DEBUG:
        raise ImproperlyConfigured("UAT ERROR: DEBUG debe ser False en el ambiente UAT.")

    if not SECRET_KEY or "cambia-esto" in SECRET_KEY or "django-insecure" in SECRET_KEY or len(SECRET_KEY) < 32:
        raise ImproperlyConfigured("UAT ERROR: DJANGO_SECRET_KEY no configurada o usando valor por defecto/inseguro en UAT.")

    _jwt_sec = env("JWT_SECRET", default="")
    if not _jwt_sec or "fosst-jwt-secret" in _jwt_sec or len(_jwt_sec) < 32:
        raise ImproperlyConfigured("UAT ERROR: JWT_SECRET no configurada o usando clave insegura por defecto en UAT.")

    if any(h in ["localhost", "127.0.0.1", "*"] for h in ALLOWED_HOSTS):
        raise ImproperlyConfigured("UAT ERROR: ALLOWED_HOSTS no puede incluir localhost, 127.0.0.1 ni '*' en UAT.")

    _db_url = env("DATABASE_URL", default="")
    if not _db_url or "localhost" in _db_url or "127.0.0.1" in _db_url or "sqlite" in _db_url:
        raise ImproperlyConfigured("UAT ERROR: DATABASE_URL debe apuntar a una base de datos PostgreSQL UAT dedicada.")

    if not REDIS_URL or "127.0.0.1" in REDIS_URL or "localhost" in REDIS_URL:
        raise ImproperlyConfigured("UAT ERROR: REDIS_URL debe apuntar a una instancia de Redis UAT dedicada (sin localhost/127.0.0.1).")

    if not FRONTEND_URL.startswith("https://"):
        raise ImproperlyConfigured("UAT ERROR: FRONTEND_URL debe utilizar HTTPS en UAT.")

    _storage_backend = env("STORAGE_BACKEND", default="")
    if "s3" not in _storage_backend.lower():
        raise ImproperlyConfigured("UAT ERROR: STORAGE_BACKEND debe utilizar almacenamiento S3/R2 en UAT.")

    if any(origin.startswith("http://") for origin in CORS_ALLOWED_ORIGINS):
        raise ImproperlyConfigured("UAT ERROR: CORS_ALLOWED_ORIGINS no puede contener origenes HTTP en UAT (debe usar HTTPS).")