# 09 — Guía de Instalación, Ejecución y Despliegue de FOSST V.I.D.A.

Este documento detalla los procedimientos técnicos verificados para aprovisionar, configurar, ejecutar y desplegar FOSST V.I.D.A. en entornos de desarrollo local y producción.

---

## 1. Requisitos Previos y Versiones Verificadas

| Componente | Requisito Mínimo Verificado | Recomendado para Producción |
|---|---|---|
| **Sistema Operativo** | Windows 10/11 x64, Linux (Ubuntu 22.04 LTS / Debian 12), macOS Sonoma | Linux Ubuntu 22.04 LTS x64 |
| **Python** | 3.11.x o superior (entorno verificado: 3.14 x64) | 3.11 / 3.12 LTS |
| **Node.js y npm** | Node.js 18.x LTS / npm 9.x (verificado: Node.js 20.x) | Node.js 20.x LTS |
| **Motor de Base de Datos** | PostgreSQL 15 / 16 | PostgreSQL 16 con pooling |
| **Broker de Mensajes / Caché**| Redis 7.x | Redis 7.x (Cluster o Standalone con persistencia AOF) |
| **Almacenamiento de Archivos**| MinIO local (S3 API en `:9000`) | AWS S3 o MinIO Enterprise |
| **Contenedores** | Docker Engine 24+ y Docker Compose v2 | Docker Engine en clúster |

---

## 2. Variables de Entorno del Sistema

Se debe crear un archivo `.env` en la raíz de `backend/` a partir de `backend/.env.example`. 

> [!WARNING]
> Nunca versione el archivo `.env` en Git. Contiene nombres de llaves criptográficas y accesos a la infraestructura.

### 2.1 Backend (`backend/.env`)

```env
# ── Django Core ───────────────────────────────────────────────────────────────
DEBUG=True
SECRET_KEY=clave-secreta-larga-y-aleatoria-de-produccion
ALLOWED_HOSTS=localhost,127.0.0.1,api.fosst.com

# ── Base de Datos Relacional (PostgreSQL) ──────────────────────────────────────
DATABASE_URL=postgres://usuario_db:password_db@localhost:5432/fosst_db
DB_CONN_MAX_AGE=600

# ── Almacenamiento de Archivos (S3 / MinIO) ────────────────────────────────────
STORAGE_BACKEND=storages.backends.s3.S3Storage
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_STORAGE_BUCKET_NAME=fosst-media
AWS_S3_ENDPOINT_URL=http://localhost:9000
AWS_S3_REGION_NAME=us-east-1

# ── Broker Asíncrono y Caché (Redis / Celery) ─────────────────────────────────
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
REDIS_CACHE_URL=redis://localhost:6379/2

# ── Configuración de Seguridad y Fuerza Bruta ─────────────────────────────────
AXES_FAILURE_LIMIT=5
AXES_COOLOFF_TIME=30

# ── Proveedor de Inteligencia Artificial (Anthropic Claude) ────────────────────
ANTHROPIC_API_KEY=sk-ant-api03-...

# ── Correo Electrónico Transaccional (SMTP) ───────────────────────────────────
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.servidor.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=notificaciones@fosst.com
EMAIL_HOST_PASSWORD=tu_password_smtp
DEFAULT_FROM_EMAIL=FOSST V.I.D.A. <notificaciones@fosst.com>
```

### 2.2 Frontend (`frontend/.env`)

```env
VITE_API_URL=http://localhost:8000/api
VITE_MEDIA_URL=http://localhost:8000/uploads
```

---

## 3. Instalación y Puesta en Marcha Paso a Paso

### 3.1 Infraestructura de Soporte (Docker)
Para levantar PostgreSQL, Redis y MinIO localmente:
```bash
# Desde la carpeta raíz del proyecto
docker-compose up -d
```
Servicios que quedarán disponibles:
- PostgreSQL 16: `localhost:5432` (db: `fosst_db`)
- MinIO S3 API: `http://localhost:9000`
- MinIO Consola Web: `http://localhost:9001`
- Redis: `localhost:6379`

### 3.2 Aprovisionamiento del Backend
```bash
cd backend

# 1. Crear y activar entorno virtual
python -m venv venv
# En Windows PowerShell:
.\venv\Scripts\Activate.ps1
# En Linux / macOS:
source venv/bin/activate

# 2. Instalar dependencias exactas
pip install -r requirements.txt

# 3. Aplicar migraciones ordenadas
python manage.py migrate

# 4. Sembrar catálogo oficial de Estándares Mínimos (Res. 0312 de 2019)
python manage.py seed_estandares

# 5. Iniciar servidor de desarrollo
python manage.py runserver 0.0.0.0:8000
```

### 3.3 Aprovisionamiento de Celery (Trabajador y Programador)
En una terminal independiente con el entorno virtual activo:
```bash
cd backend

# En Windows (requiere -P solo por limitación de multiproceso en Windows):
.\venv\Scripts\python.exe -m celery -A config worker -l info -P solo

# En Linux / macOS (Prefork con concurrencia):
celery -A config worker -l info --concurrency=4

# Iniciar planificador de tareas diarias (en otra terminal):
celery -A config beat -l info
```

### 3.4 Aprovisionamiento y Compilación del Frontend
```bash
cd frontend

# 1. Instalar dependencias
npm install

# 2. Ejecutar servidor de desarrollo con Hot Module Replacement (HMR)
npm run dev

# 3. Compilación verificada para producción:
npm run build
```
*Resultado verificado de compilación:* Genera el directorio optimizado `frontend/dist/` en **24.03 segundos** sin errores tipográficos de TypeScript.

---

## 4. Comandos de Verificación y Pruebas Automatizadas

Para validar que la instalación está íntegra antes de pasar a producción:

```bash
cd backend

# 1. Verificación del sistema sin errores de configuración
python manage.py check

# 2. Ejecutar la suite completa de Reclutamiento (25 pruebas unitarias e integración)
python manage.py test apps.reclutamiento

# 3. Ejecutar la suite transversal de todas las aplicaciones (78 pruebas)
python manage.py test apps

# 4. Ejecutar la suite de regresión y seguridad (96 pruebas)
python manage.py test apps.common.tests
```

---

## 5. Respaldos y Recuperación de Desastres

El repositorio cuenta con evidencia real de copias de seguridad consistentes en la carpeta `backups/`:
- **Ejemplo verificado:** `backups/backup_development_20261015_150614.json` (413 KB), que contiene el volcado íntegro de la estructura relacional, empresas, estándares y catálogos semilla.
- **Comando de Generación de Backup:**
  ```bash
  python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 2 > backups/backup_$(date +%Y%m%d_%H%M%S).json
  ```
- **Comando de Restauración de Backup:**
  ```bash
  python manage.py loaddata backups/backup_development_20261015_150614.json
  ```

---

## 6. Diagnóstico de Problemas Habituales

| Síntoma / Error | Causa Raíz Probable | Solución Verificada |
|---|---|---|
| `django.db.utils.OperationalError: could not connect to server` | PostgreSQL no está en ejecución en el puerto 5432 o `docker-compose` está caído. | Ejecutar `docker-compose ps` y verificar que el contenedor de `postgres` esté `Up`. |
| `Celery: ValueError: not enough values to unpack` en Windows | Bug clásico de `billiard` (multiproceso de Celery) en entornos Windows. | Ejecutar siempre Celery con el flag `-P solo`: `python -m celery -A config worker -l info -P solo`. |
| `429 Too Many Requests` en `/api/auth/login/` | El middleware `django-axes` bloqueó la IP tras 5 intentos fallidos consecutivos. | Desbloquear mediante CLI: `python manage.py axes_reset` o esperar los 30 minutos de cool-off. |
| `botocore.exceptions.EndpointConnectionError` | MinIO local no está iniciado en el puerto 9000 o las credenciales no coinciden. | Levantar MinIO con `docker-compose up -d minio` o conmutar temporalmente a almacenamiento local. |
| `403 Forbidden` ("Plan no incluye este módulo") | La empresa del usuario no tiene una suscripción activa o su plan no incluye el módulo solicitado. | Asignar suscripción desde el panel Django Admin (`/admin/planes/suscripcionempresa/`). |
