# 00 — Índice y Guía de Lectura de la Documentación Técnica de FOSST V.I.D.A.

## 1. Propósito y Alcance del Documento

El presente compendio técnico constituye la auditoría integral y el manual de transferencia de conocimiento de la plataforma **FOSST V.I.D.A.** (*Sistema Integral Organizacional y Sistema de Gestión de Seguridad y Salud en el Trabajo — SG-SST*). 

Este sistema fue concebido originalmente como una herramienta de diagnóstico de estándares mínimos (anteriormente referenciado como *DiagnostiSST* o *FOSST*) y ha evolucionado hacia una suite empresarial modular que integra la gestión del contexto organizacional, descriptores y perfiles de cargo multidimensionales, administración de talento humano, reclutamiento y selección de personal con portal público, evaluación continua de competencias, matriz inteligente de habilitación y cumplimiento normativo (**MICHC**), historial centralizado de brechas (**HBSEO**), gestión de evidencias con sellado criptográfico, inspecciones, capacitaciones, incidentes de trabajo y auditoría transversal.

El propósito central de este cuerpo documental es posibilitar que cualquier arquitecto de software, ingeniero de desarrollo o líder técnico comprenda con exactitud:
- Cómo opera la arquitectura global del software y cómo interactúan el backend (Django REST Framework) y el frontend (React + Vite + TypeScript).
- Por qué existen sus entidades de datos, señales (`signals`), servicios y flujos asíncronos.
- Qué componentes están respaldados por código y pruebas automatizadas reales, cuáles presentan implementaciones parciales y qué ambigüedades funcionales deben ser resueltas contractualmente con el cliente.
- Cómo mantener, desplegar y evolucionar el código fuente sin introducir regresiones ni vulnerar el aislamiento multi-empresa.

---

## 2. Audiencias Destinatarias

Esta documentación ha sido estructurada para satisfacer las necesidades operativas de diversos perfiles técnicos:

1. **Desarrollador Backend (Python / Django):** Encontrará en los documentos `01`, `02`, `03`, `04`, `05`, `07` y `10` la descripción minuciosa del ORM, transacciones atómicas, middlewares, serializadores, mixins multi-tenant, señales de negocio, tareas Celery y pruebas unitarias/integración.
2. **Desarrollador Frontend (React / TypeScript):** Encontrará en `01`, `02`, `04`, `05`, `06` y `07` la relación de componentes visuales, stores de contexto (autenticación, branding), llamadas Axios tipadas (`services/*.service.ts`), formularios modales y ruteo basado en roles (`guards.tsx`).
3. **Arquitecto de Software y Líder de Seguridad:** Encontrará en `01`, `03`, `10` y `11` el análisis de mitigación de vulnerabilidades, autenticación en dos factores (OTP), control de acceso basado en roles (RBAC), control de acceso modular por suscripción (*Plan Gating*), hashes criptográficos SHA-256 e inmutabilidad de logs.
4. **Analista de Calidad (QA) y Product Owner:** Encontrará en `05`, `06`, `08` y `11` la matriz de trazabilidad de requisitos cliente contra código, el estado real de ejecución de pruebas y el análisis terminológico crítico (Banco de Talento vs. Banco de Trabajo).

---

## 3. Estructura de la Documentación

La carpeta `docs/technical/` agrupa los doce documentos técnicos organizados temáticamente:

| Archivo | Título del Documento | Contenido Principal |
|---|---|---|
| [`00_indice_y_guia_lectura.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/00_indice_y_guia_lectura.md) | **Índice y Guía de Lectura** | Propósito, convenciones, criterios de evidencia y glosario funcional unificado. |
| [`01_arquitectura_general.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/01_arquitectura_general.md) | **Arquitectura General del Sistema** | Stack tecnológico, flujo cliente-servidor, multi-tenancy, middlewares, almacenamiento S3/MinIO y Celery. |
| [`02_inventario_modulos.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/02_inventario_modulos.md) | **Inventario Completo de Módulos** | Detalle app por app (20 aplicaciones backend y vistas frontend), responsabilidades y dependencias. |
| [`03_modelo_de_datos.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/03_modelo_de_datos.md) | **Modelo de Datos y Persistencia** | Esquema relacional, llaves foráneas, GenericForeignKeys, restricciones de unicidad, borrado lógico y ERD Mermaid. |
| [`04_api_y_contratos.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/04_api_y_contratos.md) | **API REST y Contratos de Integración** | Catálogo exhaustivo de endpoints, métodos, autenticación, payload JSON, códigos HTTP y serializadores. |
| [`05_reclutamiento_profundo.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/05_reclutamiento_profundo.md) | **Módulo de Reclutamiento Profundo** | Análisis de extremo a extremo: Banco de talento, vacantes, máquina de estados, portal del candidato y roles de proceso. |
| [`06_banco_de_trabajo_y_talento.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/06_banco_de_trabajo_y_talento.md) | **Investigación: Banco de Trabajo vs. Banco de Talento** | Despeje de ambigüedades funcionales, contraste entre especificación del cliente (`MODULOS A TRABAJAR V02`) y UI real. |
| [`07_documentacion_modulos_restantes.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/07_documentacion_modulos_restantes.md) | **Documentación de Módulos de Negocio** | Análisis exhaustivo de los módulos restantes: Cuentas, Empresas, Organización, PerfilCargo, MICHC, HBSEO, Estándares, Evidencias, Informes, etc. |
| [`08_trazabilidad_requisitos.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/08_trazabilidad_requisitos.md) | **Matriz de Trazabilidad de Requisitos** | Mapeo 1:1 entre requisitos del cliente, código fuente, pruebas unitarias y estado de completitud. |
| [`09_instalacion_ejecucion_despliegue.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/09_instalacion_ejecucion_despliegue.md) | **Guía de Instalación y Despliegue** | Puesta a punto de PostgreSQL, Redis, MinIO, migraciones, seeders, Celery worker y Vite build. |
| [`10_seguridad_riesgos_mantenimiento.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/10_seguridad_riesgos_mantenimiento.md) | **Seguridad, Riesgos Técnicos y Mantenimiento** | Aislamiento tenant, mitigación de fuerza bruta, SHA-256, RBAC, auditoría y guía de extensiones seguras. |
| [`11_informe_auditoria_tecnica.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/11_informe_auditoria_tecnica.md) | **Informe de Cierre de Auditoría** | Balance final del sistema, pruebas ejecutadas, hallazgos, brechas funcionales y recomendaciones. |
| [`README.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/README.md) | **Página Principal de Documentación** | Resumen ejecutivo, accesos rápidos y mapa de navegación técnica. |

---

## 4. Convenciones y Criterios de Evidencia

Para preservar la absoluta rigurosidad científica y técnica, se aplican los siguientes criterios taxativos a lo largo de toda la documentación:

- **[IMPLEMENTADO Y VERIFICADO POR CÓDIGO]:** La funcionalidad existe en las entidades de backend (`models.py`), controladores (`views.py`), rutas (`urls.py`) y componentes frontend (`.tsx`). Se cita el archivo exacto y el bloque lógico.
- **[PROBADO MEDIANTE PRUEBA EJECUTADA]:** Se ha corrido formalmente el comando de prueba (ej. `python manage.py test` o `npm run build`), registrándose la suite, el tiempo de respuesta y el resultado `OK` sin errores.
- **[PRESENTE EN CÓDIGO NO VERIFICADO EN EJECUCIÓN]:** El código existe y compila, pero no cuenta con un test automatizado específico en la suite de pruebas o depende de un servicio externo simulado.
- **[PARCIAL]:** Existe la estructura de datos o los endpoints, pero la interfaz de usuario está incompleta, o viceversa (ej. endpoints sin pantalla asociada o botones sin conexión).
- **[PENDIENTE]:** El requerimiento fue solicitado en documentos del cliente pero no existe evidencia de implementación en backend ni frontend.
- **[REQUISITO AMBIGUO O SIN EVIDENCIA SUFICIENTE]:** El término o regla de negocio presenta discrepancias conceptuales entre los documentos de especificación y la nomenclatura del código (ej. el término *Banco de Trabajo*).

---

## 5. Glosario Funcional y Técnico

- **Multi-Tenant (Aislamiento por Empresa):** Esquema arquitectónico donde múltiples empresas clientes comparten la misma instancia de aplicación y base de datos relacional, pero sus datos se encuentran estrictamente particionados y aislados mediante filtros obligatorios `empresa_id` a nivel ORM y sesión JWT.
- **SG-SST:** Sistema de Gestión de la Seguridad y Salud en el Trabajo reglamentado en Colombia por el Decreto 1072 de 2015 y la Resolución 0312 de 2019.
- **Estándares Mínimos (Res. 0312 de 2019):** Conjunto de normas y requisitos obligatorios que varían según el tamaño (número de trabajadores) y nivel de riesgo ARL (I a V) de la empresa, divididos en Capítulo I (7 estándares), Capítulo II (21 estándares) y Capítulo III (60 estándares).
- **MICHC (Matriz Inteligente de Habilitación y Cumplimiento):** Motor de reglas de negocio (`apps/michc/engine.py`) que confronta dinámicamente los requisitos exigidos por el perfil de cargo contra el perfil real, estudios, licencias, cursos y exámenes médicos del trabajador, generando un porcentaje de cumplimiento y un semáforo operativo (Verde, Amarillo, Rojo).
- **HBSEO (Historial de Brechas de Seguridad, Estrategia y Operación):** Módulo centralizador de no conformidades (`apps/hbseo`) que recibe eventos automáticos de desviaciones normativas o de competencias mediante señales Django y coordina planes de acción correctivos.
- **Banco de Talento:** Repositorio estructurado de personas aspirantes y candidatos (`apps/reclutamiento/models.py:Candidato`) segregado por empresa, con consentimiento de Habeas Data (Ley 1581 de 2012) e historial de postulaciones.
- **FURAT:** Formato Único de Reporte de Accidentes de Trabajo.
- **Plan Gating:** Mecanismo de control de acceso en backend (`apps/planes`) que restringe el uso de rutas de la API de acuerdo al paquete contratado por la empresa.
- **Soft Delete:** Patrón de persistencia donde los registros eliminados no se borran físicamente (`DELETE FROM`), sino que se marcan con una fecha y bandera lógica (`is_deleted=True, deleted_at=timezone.now()`), garantizando la preservación probatoria requerida por el SG-SST.
