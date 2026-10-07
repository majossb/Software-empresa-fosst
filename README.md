# FOSST V.I.D.A. — Sistema Integral Organizacional y SG-SST

Plataforma organizacional y Sistema de Gestión de Seguridad y Salud en el Trabajo (SG-SST), que integra los módulos de Contexto Organizacional, Gestión Humana, Reclutamiento, Matriz Inteligente de Habilitación y Cumplimiento (MICHC) e Historial de Brechas (HBSEO).

---

## Requisitos Previos

- **Python**: 3.11+
- **Node.js**: 18+ / npm 9+
- **Docker & Docker Compose** (para PostgreSQL, MinIO y Redis locales)

---

## 1. Configuración del Entorno de Desarrollo Local

### 1.1 Clonar el Repositorio e Iniciar Servicios (PostgreSQL, MinIO, Redis)

```bash
# Levantar PostgreSQL 16, MinIO (S3-compatible) y Redis en contenedores
docker-compose up -d
```

Servicios levantados:
- **PostgreSQL**: `localhost:5432` (db: `fosst_db`, user: `postgres`, pass: `postgres`)
- **MinIO Console**: `http://localhost:9001` (user: `minioadmin`, pass: `minioadmin`)
- **MinIO S3 API**: `http://localhost:9000`
- **Redis**: `localhost:6379`

### 1.2 Configurar Variables de Entorno del Backend

Copiar `.env.example` a `.env` dentro del directorio `backend/`:

```bash
cd backend
cp .env.example .env
```

Asegurar que `.env` contenga la configuración para PostgreSQL y MinIO local:
```env
DATABASE_URL=postgres://postgres:postgres@localhost:5432/fosst_db
STORAGE_BACKEND=storages.backends.s3.S3Storage
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_STORAGE_BUCKET_NAME=fosst-media
AWS_S3_ENDPOINT_URL=http://localhost:9000
```

---

## 2. Iniciar Backend (Django DRF)

```bash
cd backend

# Crear y activar entorno virtual
python -m venv venv
# En Windows PowerShell:
.\venv\Scripts\Activate.ps1
# En Linux/macOS:
source venv/bin/activate

# Instalar dependencias congeladas
pip install -r requirements.txt

# Ejecutar migraciones de PostgreSQL
python manage.py migrate

# Cargar catálogo oficial de Estándares Mínimos (Res. 0312 de 2019)
python manage.py seed_estandares

# Iniciar servidor de desarrollo en http://localhost:8000
python manage.py runserver 8000
```

---

## 3. Iniciar Celery (Tareas Asíncronas)

En una terminal independiente dentro de `backend/`:

```bash
# En Windows:
.\venv\Scripts\python.exe -m celery -A config worker -l info -P solo

# En Linux/macOS:
celery -A config worker -l info
```

---

## 4. Iniciar Frontend (React + TypeScript + Vite)

En una terminal independiente dentro de `frontend/`:

```bash
cd frontend
npm install
npm run dev
```

Acceder a la aplicación en `http://localhost:5173`.

---

## 5. Ejecutar Suite de Pruebas Automatizadas

```bash
cd backend
python manage.py test
```

---

## 6. Documentación API (OpenAPI 3.0 / Swagger)

Con el backend en ejecución, la documentación OpenAPI interactiva se encuentra en:
- **Swagger UI**: `http://localhost:8000/api/docs/`
- **Redoc**: `http://localhost:8000/api/redoc/`
- **Esquema JSON**: `http://localhost:8000/api/schema/`
