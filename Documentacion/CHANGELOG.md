# CHANGELOG - FOSST V.I.D.A. Cierre Técnico y Funcional

Este documento registra los cambios técnicos, funcionales, estructurales y de seguridad realizados en **FOSST V.I.D.A.** a lo largo de las 5 fases de ejecución (Fase 0 a Fase 4).

---

## [Fase 0] Infraestructura, Entorno y Persistencia Base

### Cambios Realizados
- **Conexiones PostgreSQL**: Configuración de `CONN_MAX_AGE=600` en `backend/config/settings.py` para soporte de pool de conexiones en entornos de alta concurrencia.
- **Abstracción de Almacenamiento**: Implementación del módulo `apps.common.storage.S3MinIOStorage` para soporte unificado de AWS S3 o MinIO on-premise mediante `django-storages`.
- **Despliegue y Orquestación**:
  - `docker-compose.yml`: Orquestación completa de PostgreSQL 15, Redis 7 y backend Django.
  - `.gitignore`: Archivos `.gitignore` en raíz y backend para excluir entornos virtuales, archivos temporales, logs y secretos.
  - `requirements.txt`: Congelamiento de dependencias backend incluyendo `django-storages`, `boto3`, `reportlab`, `openpyxl`, `pyjwt`, `cryptography`, etc.
- **Documentación**: Actualización del `README.md` con guías de instalación, configuración de variables de entorno y ejecución con Docker / entorno virtual local.

### Variables de Entorno Introducidas
- `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `CONN_MAX_AGE`
- `USE_S3`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_ENDPOINT_URL`, `AWS_S3_REGION_NAME`

---

## [Fase 1] Integridad, Seguridad y Control de Acceso

### Cambios Realizados
- **Soft Delete y Verificación SHA-256 (`apps/evidencias`)**:
  - `SoftDeleteModel` base con `deleted_at` e `is_deleted`.
  - Hashing automático SHA-256 para archivos adjuntos (`Evidencia` y `Archivo`).
  - Filtrado por `deleted_at__isnull=True` en `EvidenciaViewSet`.
- **Gating de Planes y Módulos (`apps/planes`)**:
  - Decorador `@requiere_plan_modulo` y mixin `PlanGatingMixin`.
  - Validación dinámica del plan activo de la empresa contratante ante solicitudes a endpoints modulares (`organizacion`, `perfilcargo`, `hbseo`, `michc`, `reclutamiento`).
- **Control de Acceso Basado en Roles para Reclutamiento (`apps/reclutamiento`)**:
  - Modelo `AsignacionRolProceso` para asignar roles específicos por convocatoria (Evaluador, Reclutador, Visualizador).
  - Permiso personalizado `IsRolReclutamientoPermitido` en ViewSets de reclutamiento.

### Migraciones Generadas
- `apps/evidencias/migrations/0002_softdelete_sha256.py`
- `apps/reclutamiento/migrations/0003_asignacion_rol_proceso.py`

---

## [Fase 2] Carga Masiva, Estampado de Firmas, FURAT y Métricas de Accidentalidad

### Cambios Realizados
- **Importador Masivo de Trabajadores (`apps/gestion_humana`)**:
  - `importador.py`: Parser de hojas `.xlsx` con validación de tipo/número de documento, empresa, perfil de cargo y formato de fechas.
  - Endpoints `/api/gestion-humana/trabajadores/plantilla-excel/` y `/api/gestion-humana/trabajadores/importar-excel/`.
  - Frontend: `GestionHumanaView.tsx` enriquecido con modal de carga masiva de plantilla Excel.
- **Estampado Digital de Firmas en PDF (`apps/informes`)**:
  - `firmas.py`: Servicio de estampa de firma digital (PNG/JPEG) con sello de tiempo e ID de verificación SHA-256 en reportes PDF generados con ReportLab.
  - Endpoint `/api/informes/estampado-firma/`.
- **Exportación de Plantilla FURAT y Métricas de Accidentalidad (`apps/capacitaciones`, `apps/calendario`)**:
  - `services.py`: Exportación completa en formato PDF de la plantilla FURAT para reporte de accidentes de trabajo.
  - Endpoint `/api/calendario/metricas-accidentalidad/`: Cálculo de Índices de Frecuencia (IF), Severidad (IS), Lesiones Incapacitantes (ILI) y Tasa de Accidentalidad según resoluciones SST.

---

## [Fase 3] Brechas del Documento v02 (Módulo 0, 1, HBSEO, MICHC, Reclutamiento)

### Cambios Realizados
- **Módulo 1: Perfil de Cargo (`apps/perfilcargo`)**:
  - Modelo `PerfilCargo` extendido con `jefe_inmediato`, `tipo_cargo` y `cargo_critico`.
  - Migración `0002_perfilcargo_v02_fields.py`.
- **Módulo 0: Contexto Organizacional (`apps/organizacion`)**:
  - Exportador PDF del Mapa de Procesos con inclusión opcional del logo institucional de la empresa.
- **HBSEO (`apps/hbseo`)**:
  - Endpoint `/api/hbseo/reporte-periodico/` para agregación de hallazgos y comportamientos seguros/inseguros filtrados por rango de fechas.
- **MICHC (`apps/michc`)**:
  - `constants.py`: Escalas de semaforización parametrizables (Verde: >= 85%, Amarillo: 70% - 84.99%, Rojo: < 70%).
  - Resuelto bug de variable `semaforo` en `engine.py`.
- **Reclutamiento (`apps/reclutamiento`)**:
  - Endpoint `/api/reclutamiento/embudo-fuentes/`: Métricas del embudo de contratación desglosadas por fuente de reclutamiento (LinkedIn, Portal Interno, Referidos, etc.).

---

## [Fase 4] Suite de Pruebas Automatizadas y Verificación

### Resultados de Ejecución
- **Total de pruebas unitarias**: 77 ejecutadas.
- **Resultado**: 77 exitosas (`OK`), 0 fallas, 0 errores.
- **Cobertura de pruebas**:
  - Multi-tenancy (`EmpresaScopedViewSet`)
  - Soft delete & hashes SHA-256
  - Importación masiva Excel
  - Gating de Planes
  - Estampado de firmas PDF
  - Métricas de accidentalidad & FURAT
  - Embudo de reclutamiento & reportes periódicos HBSEO
  - Cálculo de semaforización MICHC

---

## Guía de Despliegue y Migraciones

1. **Activar Entorno Virtual**:
   ```bash
   cd backend
   .\venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/macOS
   ```
2. **Aplicar Migraciones**:
   ```bash
   python manage.py migrate
   ```
3. **Ejecutar Suite de Pruebas**:
   ```bash
   python manage.py test
   ```
4. **Levantar Servidor de Desarrollo**:
   ```bash
   python manage.py runserver
   ```
