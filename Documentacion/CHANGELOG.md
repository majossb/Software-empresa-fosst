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

## [Fase 4] Capacitaciones que Cierran Brechas

### Cambios Realizados
- **Capacitación vinculada a brechas y cursos (`apps/capacitaciones`, `apps/hbseo`, `apps/formacion`)**:
  - Modelo `Capacitacion` enriquecido con relaciones opcionales a `CursoFormacion`, `CargoCompetencia`, `Brecha` (relación M2M) y campo `objetivo`.
  - Endpoint `/api/capacitaciones/sugerir-participantes/` para detectar automáticamente colaboradores con brechas o cursos vencidos/faltantes.
  - Finalización de capacitación: generación automática de `RegistroFormacion` con vigencia calculada para participantes asistentes, generación de reevaluación pendiente para brechas de competencias, y cierre de brechas a estado `subsanada` con evento en línea de tiempo inmutable.
  - Recálculo atómico de estado operativo en MICHC con patrón `transaction.on_commit`.
  - Frontend: `CapacitacionesView.tsx` enriquecido con selector "¿Qué brecha o necesidad cubre?", pre-carga de participantes sugeridos y registro de asistencia con certificado.

---

## [Fase 5] Alertas Preventivas de Formación y Vencimientos

### Cambios Realizados
- **Motor Genérico de Alertas (`apps/alertas`, `apps/calendario`)**:
  - Modelo `ReglaAlerta` ampliado con `TipoHandler` (`exacta`, `vencido_rango`, `sin_registrar`, `evaluacion_pendiente`) y nuevos modelos de origen (`RegistroFormacion`, `EvaluacionCompetencia`).
  - Modelo `Notificacion` extendido con campo estructurado `metadatos` (JSON) para trazabilidad libre de parseo de cadenas.
  - Lógica de evaluación y deduplicación diaria en `alertas/services.py`:
    - Días de anticipación configurables (alerta a los 25 días o 30 días según regla).
    - Detección de cursos obligatorios vencidos (alerta crítica) y cursos obligatorios sin registrar.
    - Detección de competencias requeridas pendientes de evaluación o con brecha abierta.
  - Semillero de reglas (`seed_reglas_alerta`): 4 nuevas reglas estándar del sistema para formación.
  - API REST: `NotificacionViewSet` en `/api/alertas/notificaciones/` con filtros por `leida`, `nivel`, `tipo_alerta`, `trabajador_id` y `cargo`; acciones `marcar-leida`, `marcar-resuelta`, endpoint `resumen` y `accion_url` contextual.
  - Frontend: `AlertasView.tsx` rediseñado con tarjetas KPI, filtros interactivos, acciones directas ("Registrar curso", "Programar capacitación") y panel colapsable de reglas.

---

## [Fase 6] Rediseño de la Pantalla "Formación & Competencias"

### Cambios Realizados
- **Estructura unificada de 5 pestañas en `/app/responsable/formacion`**:
  - **Pestaña 1 (Resumen)**: Indicadores con anillos de avance SVG (`DonutProgress`) para competencias cumplidas, formación vigente y brechas subsanadas; distribución con barra apilada (`StackedBar`) y lista de "Lo más urgente" con botones de acción directa en cada fila.
  - **Pestaña 2 (Matriz de competencias)**: Filtros combinables por Proceso organizacional, Perfil de cargo y Colaborador. Vista matricial con celdas interactivas en semáforo (OK / brecha por nivel). Clic en celda abre panel lateral tipo Drawer (`DetalleCompetenciaDrawer`) con historial y acción de evaluar. Soporte de exportación a Excel (CSV con UTF-8 BOM) e impresión / PDF.
  - **Pestaña 3 (Evaluaciones)**: Historial completo de evaluaciones inmutables con identificación de evaluador y rol (`gestion_humana`, `jefe_inmediato`, `autoevaluacion`), método de evaluación y cálculo de brecha. Modal `NuevaEvaluacionModal` con escala 1 a 5 y sugerencia inmediata de capacitación si se detecta brecha.
  - **Pestaña 4 (Cursos y vigencias)**: Control detallado por trabajador y cargo, semaforización de vencimiento y botón de acción para abrir `RegistrarCursoModal` con cálculo automático de fecha de vencimiento según vigencia del cargo/curso.
  - **Pestaña 5 (Plan de capacitación)**: Vista de capacitaciones programadas y realizadas con participantes, asistencia y verificación de cierre de brechas.
- **Calidad de interfaz y accesibilidad**:
  - Cero texto crudo o códigos técnicos en pantalla.
  - Componentes accesibles con etiquetas semánticas y `aria-label`.
  - Adaptabilidad responsiva validada para resoluciones de 360 px, 768 px y 1280 px.

---

## [Fase 7] Calidad, Auditoría de Textos, Tests y Cierre Técnico

### Cambios Realizados
- **Auditoría Integral de Textos UI**:
  - Búsqueda recursiva en `frontend/src` de cadenas técnicas (`RF-`, `RN-`, `§`, `requerimiento`, `documento del cliente`, `versión 0`, `MCC`).
  - Depuración de textos visibles en `EmpresaContextoView.tsx`, `EstandaresView.tsx`, `GestionHumanaView.tsx` y `ReclutamientoView.tsx` para presentar lenguaje 100% natural al usuario final.
- **Suite de Pruebas Automatizadas Backend**:
  - 69 pruebas unitarias y de integración pasando al 100% (`OK`), cubriendo:
    - Escala de competencias 1 a 5 y validación de roles de evaluador (`apps.formacion`).
    - Requisitos de formación por cargo, vigencias y herencia (`apps.perfilcargo`).
    - Motor MICHC con reconocimiento de formación obligatoria y competencias (`apps.michc`).
    - Capacitaciones con cierre de brechas y participantes sugeridos (`apps.capacitaciones`).
    - Motor de alertas preventivas con anticipación configurable (25 días) y deduplicación (`apps.alertas`).
- **Verificación Frontend**: Compilación TypeScript y Vite en producción sin errores (`✓ built in 9.73s`).

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
