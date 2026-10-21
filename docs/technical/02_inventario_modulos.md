# 02 — Inventario Completo de Módulos de FOSST V.I.D.A.

Este documento presenta el análisis individual y exhaustivo de las 22 aplicaciones que componen el backend Django y las áreas funcionales del frontend React de FOSST V.I.D.A.

---

## 1. Inventario de Aplicaciones Backend

### 1.1 `apps/accounts` (Autenticación y Cuentas de Usuario)
- **Responsabilidad:** Gestión del ciclo de vida del usuario, registro, validación de contraseñas de alta complejidad, emisión de tokens JWT, generación/validación de códigos OTP (2FA) y restablecimiento de credenciales.
- **Funcionalidades Verificadas:**
  - Registro de usuarios con estado inactivo inicial (`is_active=False`) y activación mediante token de correo.
  - Login en dos pasos: Credenciales $\rightarrow$ OTP de 6 dígitos con expiración de 5 minutos.
  - Restablecimiento seguro de contraseña vía email con token de un solo uso.
  - Validación de política de contraseñas (longitud mínima 8, mayúscula, minúscula, número y carácter especial).
- **Archivos Principales:** `models.py`, `views.py`, `serializers.py`, `permissions.py`, `validators.py`, `tasks.py`.
- **Modelos:** `Usuario` (extiende `AbstractBaseUser`), `TokenActivacion`, `CodigoOTP`, `TokenRecuperacion`.
- **Endpoints Asociados:** `/api/auth/registro/`, `/api/auth/activar/`, `/api/auth/login/`, `/api/auth/verificar-otp/`, `/api/auth/password-reset/`, `/api/auth/password-reset-confirm/`.
- **Dependencias:**
  - *Entrantes:* Utilizado por todos los módulos mediante `request.user` y decoradores de permisos (`EsAdmin`, `EsResponsableSST`, `EsAuditor`).
  - *Salientes:* `apps/empresas` (FK a `Empresa`), `apps/seguridad` (registro de intentos).
- **Pruebas Existentes:** `apps/accounts/tests/test_activacion_y_validaciones.py`, `test_smtp_email.py`.
- **Estado:** **[IMPLEMENTADO Y PROBADO]**.

---

### 1.2 `apps/empresas` (Administración de Empresas y Branding)
- **Responsabilidad:** Registro, caracterización económica y parametrización de la identidad corporativa de las empresas clientes.
- **Funcionalidades Verificadas:**
  - CRUD de empresas con NIT, Razón Social, Sector Económico (CIIU oficial Decreto 768), nivel de riesgo ARL (I a V) y número de trabajadores.
  - Clasificación automática del capítulo normativo aplicable de la Res. 0312/2019.
  - Configuración de colores corporativos y logotipo para personalización (*Branding*).
- **Archivos Principales:** `models.py`, `views.py`, `serializers.py`, `data/ciiu_768_catalogo.json`.
- **Modelos:** `Empresa` (con campos `nit`, `razon_social`, `ciiu`, `clase_riesgo`, `numero_trabajadores`, `capitulo_vigente`, `branding`).
- **Endpoints Asociados:** `/api/empresas/`, `/api/empresas/{id}/`, `/api/empresas/{id}/branding/`.
- **Dependencias:**
  - *Entrantes:* Es la entidad raíz del aislamiento multi-tenant de casi todas las aplicaciones.
  - *Salientes:* `apps/ia` (sugerencia de código CIIU en lenguaje natural).
- **Pruebas Existentes:** `apps/empresas/tests/test_branding.py`, `test_registro_ciiu.py`.
- **Estado:** **[IMPLEMENTADO Y PROBADO]**.

---

### 1.3 `apps/planes` (Suscripciones y Plan Gating)
- **Responsabilidad:** Gestión de paquetes comerciales (Free, Estándar, Premium), vigencias de contratación y control de acceso granular a módulos según el plan contratado.
- **Funcionalidades Verificadas:**
  - Catálogo de planes y asignación de suscripciones por empresa.
  - Decorador `@requiere_plan_modulo` y mixin `PlanGatingMixin` para proteger endpoints restringidos.
- **Archivos Principales:** `models.py`, `views.py`, `decorators.py`, `mixins.py`.
- **Modelos:** `Plan`, `ModuloSistema`, `SuscripcionEmpresa`.
- **Endpoints Asociados:** `/api/planes/`, `/api/planes/suscripciones/`.
- **Dependencias:**
  - *Entrantes:* Vistas de `organizacion`, `perfilcargo`, `hbseo`, `michc`, `reclutamiento`.
  - *Salientes:* `apps/empresas`.
- **Pruebas Existentes:** `apps/common/tests/test_fase1_integridad_seguridad.py` (valida bloqueo por suscripción).
- **Estado:** **[IMPLEMENTADO Y PROBADO]**.

---

### 1.4 `apps/organizacion` (Contexto Organizacional)
- **Responsabilidad:** Estructura física, funcional y jerárquica de la empresa.
- **Funcionalidades Verificadas:**
  - Registro de sedes con ciudad, dirección y nivel de riesgo ARL.
  - Organigrama en árbol jerárquico recursivo con persistencia de coordenadas `(pos_x, pos_y)` para renderizado en canvas.
  - Mapa de procesos clasificados en *Estratégicos, Misionales y de Apoyo* con control de unicidad.
  - Misión, visión, valores y políticas institucionales SST.
- **Archivos Principales:** `models.py`, `views.py`, `serializers.py`.
- **Modelos:** `Sede`, `NodoOrganigrama`, `Proceso`, `ContextoEmpresa`.
- **Endpoints Asociados:** `/api/modulo0/sedes/`, `/api/modulo0/organigrama/`, `/api/modulo0/procesos/`, `/api/modulo0/identidad/`.
- **Dependencias:**
  - *Entrantes:* `apps/perfilcargo` (asociación de cargos a sedes y procesos).
  - *Salientes:* `apps/empresas`.
- **Pruebas Existentes:** `apps/organizacion/tests/test_organigrama_export.py`.
- **Estado:** **[IMPLEMENTADO Y PROBADO]**.

---

### 1.5 `apps/perfilcargo` (Descriptores y Perfiles de Cargo)
- **Responsabilidad:** Especificación de requerimientos de los cargos, matriz de criticidad en 5 dimensiones, peligros GTC 45, EPPs y versionado inmutable.
- **Funcionalidades Verificadas:**
  - Perfil de cargo multidimensional (SST, Operacional, Vial, Ambiental, Estratégico).
  - Jerarquía de cargos mediante relación reflexiva `jefe_inmediato` y `suplente`.
  - Matriz de competencias requeridas (escala 1 a 4).
  - Catálogo de peligros de la GTC 45 y asignación de EPPs.
  - Versionado inmutable automático (`CargoVersion`): Cada edición guarda un snapshot en JSON incrementando el número de versión.
  - Asistencia con IA para generación de funciones y propósitos según Decreto 1072/2015.
- **Archivos Principales:** `models.py`, `views.py`, `serializers.py`, `signals.py`.
- **Modelos:** `PerfilCargo`, `CargoVersion`, `CargoCompetencia`, `CatalogoPeligro`, `CargoPeligro`, `CargoEPP`.
- **Endpoints Asociados:** `/api/modulo1/perfiles-cargo/`, `/api/modulo1/perfiles-cargo/{id}/versiones/`, `/api/modulo1/perfiles-cargo/generar-ia/`.
- **Dependencias:**
  - *Entrantes:* `apps/capacitaciones` (Trabajador), `apps/michc` (comparación con perfil), `apps/reclutamiento` (Vacante).
  - *Salientes:* `apps/organizacion`, `apps/ia`.
- **Pruebas Existentes:** `apps/perfilcargo/tests/test_fase1_perfil_extendido.py`.
- **Estado:** **[IMPLEMENTADO Y PROBADO]**.

---

### 1.6 `apps/capacitaciones` (Trabajadores y Capacitación)
- **Responsabilidad:** Maestro de trabajadores, registro de cronogramas de capacitación, asistencia y reporte preliminar de incidentes.
- **Funcionalidades Verificadas:**
  - Gestión de trabajadores independientes de cuentas de usuario con restricción de unicidad por documento en la empresa.
  - Programación y control de asistencia a capacitaciones SST.
  - Cálculo de horas-hombre de formación y cobertura.
  - Generación de plantilla y PDF oficial del FURAT para accidentes laborales.
- **Archivos Principales:** `models.py`, `views.py`, `services.py`.
- **Modelos:** `Trabajador`, `AfiliacionTrabajador`, `Capacitacion`, `ParticipanteCapacitacion`, `IncidenteTrabajo`.
- **Endpoints Asociados:** `/api/capacitaciones/`, `/api/capacitaciones/trabajadores/`, `/api/capacitaciones/furat-pdf/`.
- **Dependencias:**
  - *Entrantes:* `apps/michc`, `apps/gestion_humana`, `apps/formacion`, `apps/alertas`.
  - *Salientes:* `apps/empresas`, `apps/perfilcargo`.
- **Pruebas Existentes:** `apps/common/tests/test_fase2_requerimientos_pendientes.py` (prueba FURAT y métricas).
- **Estado:** **[IMPLEMENTADO Y PROBADO]**.

---

### 1.7 `apps/gestion_humana` (Administración Ocupacional e Importador)
- **Responsabilidad:** Exámenes médicos ocupacionales, licencias de conducción e importación masiva de personal.
- **Funcionalidades Verificadas:**
  - Registro de conceptos de aptitud médica (Ingreso, Periódico, Egreso, Reintegro) con banderas de restricciones activas.
  - Control de categorías y vigencias de licencias de conducción.
  - Importador masivo de trabajadores desde archivos Excel (`.xlsx`) con validación de columnas y descarga de plantilla oficial.
- **Archivos Principales:** `models.py`, `views.py`, `importador.py`.
- **Modelos:** `ExamenMedicoOcupacional`, `LicenciaConduccion`.
- **Endpoints Asociados:** `/api/gestion-humana/examenes/`, `/api/gestion-humana/licencias/`, `/api/gestion-humana/trabajadores/plantilla-excel/`, `/api/gestion-humana/trabajadores/importar-excel/`.
- **Dependencias:**
  - *Entrantes:* `apps/michc` (cálculo de compatibilidad médica), `apps/alertas` (vencimientos).
  - *Salientes:* `apps/capacitaciones` (Trabajador), `apps/empresas`.
- **Pruebas Existentes:** `apps/gestion_humana/tests/test_gestion_humana.py`, `apps/common/tests/test_fase2_requerimientos_pendientes.py`.
- **Estado:** **[IMPLEMENTADO Y PROBADO]**.

---

### 1.8 `apps/reclutamiento` (Selección de Personal y Banco de Talento)
- **Responsabilidad:** Banco de talento multi-tenant, vacantes, procesos de selección, máquina de estados de postulación, etapas (entrevistas, evaluaciones, validaciones) y portal público del candidato.
- **Funcionalidades Verificadas:**
  - Banco de talento aislado con consentimiento de Habeas Data (Ley 1581 de 2012).
  - Códigos correlativos automáticos (`VAC-YYYY-NNNN`, `PROC-YYYY-NNNN`).
  - Máquina de 8 estados con transiciones estrictas y línea de tiempo inmutable (`PostulacionEvento`).
  - Control de cupos y cierre automático al cubrir vacante (RN-R06).
  - Reapertura excepcional justificada sin destrucción de historial (RN-R07, RN-R09).
  - Portal público con autenticación passwordless mediante token OTP por correo.
- **Archivos Principales:** `models.py`, `views.py`, `portal_views.py`, `services.py`.
- **Modelos:** `FuenteReclutamiento`, `Candidato`, `PerfilCandidato`, `CandidatoDocumento`, `Vacante`, `ProcesoSeleccion`, `AsignacionRolProceso`, `Postulacion`, `PostulacionEvento`, `Entrevista`, `Evaluacion`, `ValidacionDocumental`, `TokenAccesoCandidato`.
- **Endpoints Asociados:** `/api/reclutamiento/candidatos/`, `/api/reclutamiento/vacantes/`, `/api/reclutamiento/procesos/`, `/api/reclutamiento/postulaciones/`, `/api/reclutamiento/portal/vacantes/`, `/api/reclutamiento/portal/solicitar-otp/`, `/api/reclutamiento/portal/verificar-otp/`.
- **Dependencias:**
  - *Entrantes:* Frontend Portal y Panel Administrativo de Selección.
  - *Salientes:* `apps/empresas`, `apps/perfilcargo`, `apps/accounts`.
- **Pruebas Existentes:** `apps/reclutamiento/tests/test_fase_a.py`, `test_fase_b_transiciones.py`, `test_fase_c_etapas.py`, `test_fase_d_endpoints.py`, `test_fase_e_portal.py` (25 pruebas ejecutadas satisfactoriamente).
- **Estado:** **[IMPLEMENTADO Y PROBADO]**.

---

### 1.9 `apps/michc` (Matriz Inteligente de Habilitación y Cumplimiento)
- **Responsabilidad:** Motor determinista de cálculo de cumplimiento técnico y legal entre el perfil del trabajador y las exigencias de su cargo.
- **Funcionalidades Verificadas:**
  - Evaluación ponderada de 9 factores: Nivel educativo, experiencia general, experiencia específica, formación técnica, cursos obligatorios SST, licencias de conducción, exámenes médicos periódicos, concepto de aptitud y compatibilidad de restricciones.
  - Semáforo operativo unificado: 🟢 Verde ($\ge 100\%$), 🟡 Amarillo ($80-99\%$), 🔴 Rojo ($<80\%$).
  - Detección de incompatibilidades médicas cruzadas contra los peligros del cargo.
  - Disparo de señales hacia `apps/hbseo` cuando el cumplimiento es inferior al 80%.
  - Tarea Celery para redacción de diagnóstico clínico-operativo con IA.
- **Archivos Principales:** `models.py`, `views.py`, `engine.py`, `signals.py`, `tasks.py`.
- **Modelos:** `EvaluacionHabilitacion`, `DetalleEvaluacionHabilitacion`, `InterpretacionIA`.
- **Endpoints Asociados:** `/api/michc/evaluaciones/`, `/api/michc/evaluaciones/evaluar-trabajador/`, `/api/michc/matriz/`.
- **Dependencias:**
  - *Entrantes:* Dashboard, Vistas de Gestión Humana.
  - *Salientes:* `apps/capacitaciones`, `apps/perfilcargo`, `apps/gestion_humana`, `apps/hbseo`, `apps/ia`.
- **Pruebas Existentes:** `apps/michc/tests/test_michc.py`.
- **Estado:** **[IMPLEMENTADO Y PROBADO]**.

---

### 1.10 `apps/hbseo` (Historial de Brechas)
- **Responsabilidad:** Hub unificado para la gestión y cierre de brechas normativas, de habilitación y de competencias.
- **Funcionalidades Verificadas:**
  - Estructura polimórfica basada en `GenericForeignKey` (`BrechaOrigen`) para vincular brechas generadas desde MICHC, Formación o Hallazgos.
  - Línea de tiempo inmutable de cambios de estado (`BrechaEvento`).
  - Planes de acción con seguimiento y responsables (`BrechaAccion`).
- **Archivos Principales:** `models.py`, `views.py`, `services.py`.
- **Modelos:** `Brecha`, `BrechaOrigen`, `BrechaEvento`, `BrechaAccion`.
- **Endpoints Asociados:** `/api/hbseo/brechas/`, `/api/hbseo/acciones/`.
- **Dependencias:**
  - *Entrantes:* `apps/michc`, `apps/formacion`, `apps/hallazgos`.
  - *Salientes:* `apps/empresas`.
- **Pruebas Existentes:** `apps/hbseo/tests/test_brecha_service.py`, `apps/common/tests/test_fase3_brechas_v02.py`.
- **Estado:** **[IMPLEMENTADO Y PROBADO]**.

---

### 1.11 `apps/formacion` (Evaluación de Competencias)
- **Responsabilidad:** Evaluación periódica del desempeño de competencias del trabajador contra la escala 1 a 4 requerida por el cargo.
- **Funcionalidades Verificadas:**
  - Registro de evaluaciones (360°, pruebas técnicas o prácticas).
  - Cálculo automático de la brecha negativa (`max(0, nivel_requerido - nivel_alcanzado)`).
  - Disparo de señales hacia `apps/hbseo` ante brechas mayores a cero.
- **Archivos Principales:** `models.py`, `views.py`, `signals.py`.
- **Modelos:** `EvaluacionCompetencia`.
- **Endpoints Asociados:** `/api/formacion/evaluaciones/`.
- **Dependencias:**
  - *Entrantes:* Dashboard de talento humano.
  - *Salientes:* `apps/capacitaciones`, `apps/perfilcargo`, `apps/hbseo`.
- **Pruebas Existentes:** `apps/formacion/tests/test_formacion.py`.
- **Estado:** **[IMPLEMENTADO Y PROBADO]**.

---

### 1.12 `apps/estandares` (Estándares Mínimos Res. 0312/2019)
- **Responsabilidad:** Núcleo normativo del SG-SST. Evaluación anual y apelaciones.
- **Funcionalidades Verificadas:**
  - Catálogo de los 60 estándares clasificados por ciclo PHVA y capítulos I, II y III.
  - Registro de autoevaluaciones anuales y ponderación de puntajes.
  - Módulo de Apelaciones: El responsable SST apela calificaciones de auditoría y el auditor resuelve con justificación técnica.
- **Archivos Principales:** `models.py`, `views.py`, `management/commands/seed_estandares.py`.
- **Modelos:** `Estandar`, `Evaluacion`, `Respuesta`, `Apelacion`.
- **Endpoints Asociados:** `/api/estandares/`, `/api/estandares/evaluaciones/`, `/api/estandares/evaluacion-actual/`, `/api/estandares/apelaciones/`.
- **Dependencias:**
  - *Entrantes:* `apps/evidencias`, `apps/hallazgos`, `apps/informes`.
  - *Salientes:* `apps/empresas`, `apps/calendario` (Notificaciones).
- **Pruebas Existentes:** `apps/common/tests/test_apelaciones_rf_sst_03.py`, `test_transicion_capitulo_rf_usr_03.py`.
- **Estado:** **[IMPLEMENTADO Y PROBADO]**.

---

### 1.13 `apps/evidencias` (Gestión Documental y Hashes SHA-256)
- **Responsabilidad:** Almacenamiento seguro e íntegro de soportes y archivos de auditoría.
- **Funcionalidades Verificadas:**
  - Carga multipart de archivos PDF, imágenes y documentos ofimáticos.
  - Cálculo de hash SHA-256 en tiempo de almacenamiento.
  - Borrado lógico (`soft delete`) para preservar la cadena de custodia.
- **Archivos Principales:** `models.py`, `views.py`.
- **Modelos:** `Evidencia`, `Archivo`.
- **Endpoints Asociados:** `/api/evidencias/`, `/api/evidencias/archivos/`.
- **Dependencias:**
  - *Entrantes:* `apps/estandares` (Respuesta).
  - *Salientes:* MinIO / AWS S3 Storage.
- **Pruebas Existentes:** `apps/evidencias/tests/test_evidencias.py`, `apps/common/tests/test_fase1_integridad_seguridad.py`.
- **Estado:** **[IMPLEMENTADO Y PROBADO]**.

---

### 1.14 `apps/hallazgos` (No Conformidades y Planes de Mejora)
- **Responsabilidad:** Registro de observaciones de auditoría y cálculo automático de planes de mejora.
- **Funcionalidades Verificadas:**
  - Registro de hallazgos tipificados (*No conformidad mayor, menor, observación, oportunidad de mejora*).
  - Creación atómica de notificaciones a responsables SST al crear un hallazgo.
  - Cálculo automático de fecha límite según prioridad (Urgente: 3 meses, Importante: 6 meses, Aceptable: 12 meses).
  - Control de propiedad: Solo el auditor autor puede modificar su hallazgo.
- **Archivos Principales:** `models.py`, `views.py`.
- **Modelos:** `Hallazgo`, `PlanMejora`.
- **Endpoints Asociados:** `/api/hallazgos/`, `/api/plan-mejora/`, `/api/plan-mejora/resumen/`.
- **Dependencias:**
  - *Entrantes:* Vistas de Auditor y Responsable.
  - *Salientes:* `apps/estandares`, `apps/calendario`.
- **Pruebas Existentes:** `apps/common/tests/test_auditor_notificaciones.py`.
- **Estado:** **[IMPLEMENTADO Y PROBADO]**.

---

### 1.15 `apps/informes` (Reportes Oficiales y Firma Digital)
- **Responsabilidad:** Generación de balances consolidados de autoevaluación y auditoría en formato PDF con estampado de firma.
- **Funcionalidades Verificadas:**
  - Estructuración JSON inmutable del estado de la autoevaluación anual.
  - Motor ReportLab para renderizado del documento oficial.
  - Estampado de firma digitalizada con sello de tiempo e ID SHA-256 (`apps/informes/firmas.py`).
- **Archivos Principales:** `models.py`, `views.py`, `firmas.py`.
- **Modelos:** `Informe`.
- **Endpoints Asociados:** `/api/informes/`, `/api/informes/{id}/pdf/`, `/api/informes/estampado-firma/`.
- **Dependencias:**
  - *Entrantes:* Alta Dirección y Auditoría.
  - *Salientes:* `apps/estandares`, `apps/empresas`.
- **Pruebas Existentes:** `apps/common/tests/test_fase2_requerimientos_pendientes.py`.
- **Estado:** **[IMPLEMENTADO Y PROBADO]**.

---

### 1.16 `apps/calendario` (Agenda, Incidentes y Notificaciones)
- **Responsabilidad:** Calendario unificado de actividades SST, consolidación de incidentes/accidentes y bandeja persistente de notificaciones.
- **Funcionalidades Verificadas:**
  - CRUD de actividades con estados de cumplimiento.
  - Registro de incidentes y cálculo de indicadores de frecuencia y severidad.
  - Modelo `Notificacion` con niveles (*Crítico, Importante, Normal*) y marca de lectura.
- **Archivos Principales:** `models.py`, `views.py`.
- **Modelos:** `CalendarioActividad`, `Incidente`, `Notificacion`.
- **Endpoints Asociados:** `/api/calendario/actividades/`, `/api/calendario/metricas-accidentalidad/`, `/api/notificaciones/`.
- **Dependencias:**
  - *Entrantes:* Disparadores de `hallazgos`, `estandares`, `alertas`.
  - *Salientes:* `apps/empresas`.
- **Pruebas Existentes:** `apps/common/tests/test_fase2_requerimientos_pendientes.py`.
- **Estado:** **[IMPLEMENTADO Y PROBADO]**.

---

### 1.17 `apps/alertas` (Motor de Reglas y Vencimientos)
- **Responsabilidad:** Evaluación parametrizada de alertas preventivas.
- **Funcionalidades Verificadas:**
  - Modelo `ReglaAlerta` configurable por empresa o global con días de anticipación.
  - Tarea periódica Celery Beat `revisar_vencimientos` con deduplicación diaria.
- **Archivos Principales:** `models.py`, `services.py`, `tasks.py`.
- **Modelos:** `ReglaAlerta`.
- **Endpoints Asociados:** `/api/alertas/reglas/`.
- **Dependencias:**
  - *Entrantes:* Celery Beat Scheduler.
  - *Salientes:* `apps/calendario` (Notificacion), `apps/gestion_humana`, `apps/capacitaciones`.
- **Pruebas Existentes:** `apps/alertas/tests/test_alertas.py`.
- **Estado:** **[IMPLEMENTADO Y PROBADO]**.

---

### 1.18 `apps/dashboard` (Páneles de Control Analíticos)
- **Responsabilidad:** Agregación de métricas estratégicas con caché de alto rendimiento.
- **Funcionalidades Verificadas:**
  - Tres vistas diferenciadas: Alta Dirección (financiero y cumplimiento macro), Responsable SST (operativo y brechas) y Auditor (cobertura de revisión).
  - Almacenamiento en caché en Redis con TTL de 300 segundos.
- **Archivos Principales:** `views.py`.
- **Endpoints Asociados:** `/api/dashboard/alta-direccion/`, `/api/dashboard/responsable/`, `/api/dashboard/auditor/`.
- **Dependencias:**
  - *Entrantes:* Vistas principales del frontend.
  - *Salientes:* `estandares`, `michc`, `hbseo`, `capacitaciones`.
- **Estado:** **[IMPLEMENTADO Y PROBADO]**.

---

### 1.19 `apps/ia` (Servicio Central de Inteligencia Artificial)
- **Responsabilidad:** Integración resiliente con modelos de lenguaje.
- **Funcionalidades Verificadas:**
  - Clasificación de actividad económica CIIU.
  - Generación de propósitos y funciones de perfiles de cargo.
  - Fallbacks deterministas locales si la API de Anthropic Claude no responde o falla la red.
- **Archivos Principales:** `service.py`, `prompts.py`.
- **Dependencias:**
  - *Entrantes:* `apps/empresas`, `apps/perfilcargo`, `apps/michc`.
- **Pruebas Existentes:** `apps/ia/tests/test_ia_service.py`.
- **Estado:** **[IMPLEMENTADO Y PROBADO]**.

---

### 1.20 `apps/auditoria` (Trazabilidad y AuditLog)
- **Responsabilidad:** Registro inmutable de transacciones de escritura.
- **Funcionalidades Verificadas:**
  - `AuditoriaMiddleware` intercepta peticiones `POST`, `PUT`, `PATCH`, `DELETE` y captura usuario, IP, ruta, payload anterior y nuevo.
- **Archivos Principales:** `models.py`, `middleware.py`, `helpers.py`.
- **Modelos:** `AuditLog`.
- **Endpoints Asociados:** `/api/auditoria/logs/` (solo rol ADMIN y AUDITOR).
- **Dependencias:**
  - Intercepta transversalmente todas las peticiones HTTP del sistema.
- **Estado:** **[IMPLEMENTADO Y PROBADO]**.

---

### 1.21 `apps/seguridad` (Defensa Perimetral y Dispositivos)
- **Responsabilidad:** Control de sesiones, detección de dispositivos no reconocidos y mitigación de intrusiones.
- **Funcionalidades Verificadas:**
  - Middleware de huella de navegador e IP (`DispositivoMiddleware`).
  - Registro de eventos de riesgo (`EventoRiesgo`) ante inicios de sesión sospechosos.
- **Archivos Principales:** `models.py`, `middleware.py`.
- **Modelos:** `DispositivoConocido`, `EventoRiesgo`.
- **Dependencias:**
  - *Entrantes:* `apps/accounts`.
- **Estado:** **[IMPLEMENTADO Y PROBADO]**.

---

### 1.22 `apps/common` (Núcleo Compartido)
- **Responsabilidad:** Componentes transversales, mixins de seguridad y adaptadores de infraestructura.
- **Funcionalidades Verificadas:**
  - `SoftDeleteModel` y `SoftDeleteQuerySet`.
  - `EmpresaScopedViewSet` (inyección obligatoria del tenant).
  - `S3MinIOStorage` (abstracción de almacenamiento S3/MinIO).
- **Archivos Principales:** `models.py`, `mixins.py`, `storage.py`.
- **Estado:** **[IMPLEMENTADO Y PROBADO]**.

---

## 2. Inventario de Áreas Funcionales del Frontend

| Área / Carpeta | Componentes Principales | Responsabilidad Funcional | Estado |
|---|---|---|---|
| `pages/auth/` | `LoginPage`, `OTPPage`, `RegistroEmpresaPage`, `ActivarCuentaPage`, `RecuperarPasswordPage`, `ResetearPasswordPage` | Autenticación, registro empresarial, validación 2FA OTP y recuperación de acceso. | **IMPLEMENTADO Y COMPILADO** |
| `pages/portal/` | `PortalVacantesPage`, `PortalVacanteDetailPage`, `PortalSeguimientoPage` | Portal público y mobile-friendly para consulta de vacantes, postulación con Habeas Data y consulta OTP de estado. | **IMPLEMENTADO Y COMPILADO** |
| `pages/responsable/` | `Dashboard`, `AutoevaluacionView`, `EstandaresView`, `EvidenciasView`, `InformesView`, `HallazgosView`, `PlanMejoraView`, `FormacionView`, `GestionHumanaView`, `MichcView`, `HbseoView`, `ReclutamientoView`, `CapacitacionesView`, `AlertasView` | Operación integral del Responsable SG-SST: diagnóstico, evidencias, matriz MICHC, importación Excel, vacantes y brechas. | **IMPLEMENTADO Y COMPILADO** |
| `pages/responsable/views/configuracion/` | `EmpresaContextoView`, `IdentidadView`, `SedesView`, `OrganigramaView`, `ProcesosView`, `PerfilesCargoView`, `PerfilCargoDetailView`, `PerfilCargoFormView`, `SancionesView` | Parametrización institucional, árbol visual de organigrama, mapas de proceso y edición de descriptores de cargo. | **IMPLEMENTADO Y COMPILADO** |
| `pages/auditor/` | `Dashboard`, `EvidenciasAuditorView`, `HallazgosView`, `ApelacionesAuditorView`, `HistorialAuditorView`, `InformeAuditoriaView` | Revisión técnica de evidencias, registro de no conformidades, resolución motivada de apelaciones y balance auditor. | **IMPLEMENTADO Y COMPILADO** |
| `pages/altadireccion/` | `Dashboard`, `CumplimientoView`, `InformesView`, `HistorialView`, `SedesView` | Seguimiento ejecutivo de indicadores macro del SG-SST, mapas de calor de sedes y revisión de informes finales. | **IMPLEMENTADO Y COMPILADO** |
| `components/layout/` | `AppShell`, `NotificationPopover` | Estructura principal con barra lateral dinámica según rol, cabecera corporativa y campana de notificaciones. | **IMPLEMENTADO Y COMPILADO** |
