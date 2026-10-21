# FOSST V.I.D.A. — Documentación Técnica Integral y Auditoría de Software

Bienvenido al repositorio central de documentación técnica y manual de transferencia de conocimiento de **FOSST V.I.D.A.** (*Sistema Integral Organizacional y Sistema de Gestión de Seguridad y Salud en el Trabajo — SG-SST*).

Esta documentación fue construida mediante una auditoría técnica exhaustiva sobre el 100% del código fuente (backend Django DRF y frontend React Vite TypeScript), las 199 pruebas automatizadas ejecutadas y los documentos oficiales de requisitos del cliente.

---

## 📚 Mapa de Navegación Documental

Haga clic en cualquiera de los documentos para acceder a su contenido detallado:

| Archivo | Documento | Propósito Técnico |
|---|---|---|
| [`00_indice_y_guia_lectura.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/00_indice_y_guia_lectura.md) | **00 — Índice y Guía de Lectura** | Audiencias, convenciones, criterios de evidencia y glosario funcional unificado. |
| [`01_arquitectura_general.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/01_arquitectura_general.md) | **01 — Arquitectura General** | Stack tecnológico, flujo cliente-servidor, multi-tenancy, middlewares, MinIO S3 y Celery. |
| [`02_inventario_modulos.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/02_inventario_modulos.md) | **02 — Inventario de Módulos** | Detalle de las 22 aplicaciones backend y todas las vistas del frontend. |
| [`03_modelo_de_datos.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/03_modelo_de_datos.md) | **03 — Modelo de Datos y Persistencia** | Esquema relacional, llaves foráneas, GenericFK, restricciones de unicidad, borrado lógico y ERD Mermaid. |
| [`04_api_y_contratos.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/04_api_y_contratos.md) | **04 — API REST y Contratos** | Catálogo exhaustivo de endpoints, payloads JSON de entrada, códigos HTTP y serializadores. |
| [`05_reclutamiento_profundo.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/05_reclutamiento_profundo.md) | **05 — Reclutamiento Profundo** | Análisis de extremo a extremo: Banco de talento, vacantes, máquina de estados, portal del candidato y roles. |
| [`06_banco_de_trabajo_y_talento.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/06_banco_de_trabajo_y_talento.md) | **06 — Banco de Trabajo vs. Talento** | Investigación y resolución de ambigüedades funcionales entre requisitos y código. |
| [`07_documentacion_modulos_restantes.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/07_documentacion_modulos_restantes.md) | **07 — Módulos de Negocio Restantes** | Explicación detallada de los 20 dominios de negocio (MICHC, HBSEO, Perfiles, Estándares, etc.). |
| [`08_trazabilidad_requisitos.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/08_trazabilidad_requisitos.md) | **08 — Trazabilidad de Requisitos** | Matriz 1:1 de requisitos del cliente contra código, endpoints y pruebas ejecutadas. |
| [`09_instalacion_ejecucion_despliegue.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/09_instalacion_ejecucion_despliegue.md) | **09 — Instalación y Despliegue** | Variables de entorno, aprovisionamiento Docker, migraciones, seeders y comandos de ejecución. |
| [`10_seguridad_riesgos_mantenimiento.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/10_seguridad_riesgos_mantenimiento.md) | **10 — Seguridad y Mantenimiento** | Aislamiento tenant, mitigación de fuerza bruta, SHA-256, auditoría y playbook para nuevas extensiones. |
| [`11_informe_auditoria_tecnica.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/11_informe_auditoria_tecnica.md) | **11 — Informe de Cierre de Auditoría** | Balance final de estabilidad, pruebas verificadas, brechas detectadas y decisiones del cliente. |

---

## 🚀 Guías de Lectura Rápida según tu Rol

- **Si eres un Desarrollador Backend nuevo en el proyecto:**
  1. Comienza por [`01_arquitectura_general.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/01_arquitectura_general.md) para entender la comunicación y el multi-tenant.
  2. Lee [`03_modelo_de_datos.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/03_modelo_de_datos.md) para dominar el ORM y las relaciones.
  3. Revisa [`09_instalacion_ejecucion_despliegue.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/09_instalacion_ejecucion_despliegue.md) para levantar tu entorno local.
  4. Consulta [`10_seguridad_riesgos_mantenimiento.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/10_seguridad_riesgos_mantenimiento.md) antes de agregar cualquier modelo o endpoint.

- **Si eres un Desarrollador Frontend:**
  1. Comienza por [`01_arquitectura_general.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/01_arquitectura_general.md) y [`04_api_y_contratos.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/04_api_y_contratos.md) para conocer las firmas de las rutas.
  2. Revisa [`05_reclutamiento_profundo.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/05_reclutamiento_profundo.md) y [`06_banco_de_trabajo_y_talento.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/06_banco_de_trabajo_y_talento.md) para entender la lógica de los estados en la interfaz.

- **Si eres Product Owner o Evaluador de Calidad:**
  1. Lee [`08_trazabilidad_requisitos.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/08_trazabilidad_requisitos.md) para verificar el cumplimiento contractual.
  2. Revisa [`11_informe_auditoria_tecnica.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/11_informe_auditoria_tecnica.md) para conocer las decisiones pendientes y las pruebas ejecutadas.

---

## 📋 Archivos Recomendados para Compartir con ChatGPT

Si necesitas alimentar a ChatGPT o a otro modelo de lenguaje para generar manuales de usuario, presentaciones ejecutivas o guías operativas, te recomendamos adjuntar los siguientes documentos en este orden:

1. **Para un Manual de Usuario General:**
   - [`00_indice_y_guia_lectura.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/00_indice_y_guia_lectura.md)
   - [`07_documentacion_modulos_restantes.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/07_documentacion_modulos_restantes.md)
2. **Para el Manual del Módulo de Reclutamiento y Selección:**
   - [`05_reclutamiento_profundo.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/05_reclutamiento_profundo.md)
   - [`06_banco_de_trabajo_y_talento.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/06_banco_de_trabajo_y_talento.md)
3. **Para la Sustentación Técnica o Arquitectónica ante Jurado / Cliente:**
   - [`01_arquitectura_general.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/01_arquitectura_general.md)
   - [`08_trazabilidad_requisitos.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/08_trazabilidad_requisitos.md)
   - [`11_informe_auditoria_tecnica.md`](file:///c:/Users/Maria%20Jose/Downloads/Fosst-software-main_fase1/docs/technical/11_informe_auditoria_tecnica.md)
