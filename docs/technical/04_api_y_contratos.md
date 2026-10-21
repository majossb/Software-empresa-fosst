# 04 — API REST y Contratos de Integración de FOSST V.I.D.A.

Este documento cataloga exhaustivamente los endpoints expuestos por la API REST de FOSST V.I.D.A., verificados contra los enrutadores Django (`urls.py`), las vistas (`views.py`) y la especificación OpenAPI generada por `drf-spectacular`.

---

## 1. Módulo de Autenticación y Cuentas (`/api/auth/`)

| Método | Ruta | Vista / Función | Permisos | Entrada (Payload JSON) | Respuesta Exitosa | Errores Posibles | Efectos Secundarios |
|---|---|---|---|---|---|---|---|
| `POST` | `/api/auth/registro/` | `RegistroView` | Pública (AllowAny) | `{ nit, razon_social, email, password, documento, nombre }` | `201 Created` `{ message, user_id }` | `400` (NIT duplicado, email inválido, contraseña débil) | Crea `Empresa`, `Usuario` (`is_active=False`) y `TokenActivacion`. Encola email en Celery. |
| `POST` | `/api/auth/activar/` | `ActivarCuentaView` | Pública | `{ token }` | `200 OK` `{ message }` | `400` (Token expirado o inválido) | Activa usuario (`is_active=True`), invalida token. |
| `POST` | `/api/auth/login/` | `LoginView` | Pública (Rate Limit 5/min) | `{ documento, password }` | `200 OK` `{ otp_requerido: true, session_token }` | `401` (Credenciales inválidas), `403` (Usuario inactivo), `429` (Bloqueo Axes) | Genera `CodigoOTP` (5 min), encola email, registra intento en `axes`. |
| `POST` | `/api/auth/verificar-otp/` | `VerificarOTPView` | Pública | `{ session_token, codigo_otp }` | `200 OK` `{ access, refresh, user: {...} }` | `400` (OTP vencido o inválido) | Marca OTP usado, emite JWT Bearer Tokens, actualiza `ultimo_login`. |
| `POST` | `/api/auth/password-reset/` | `PasswordResetRequestView` | Pública | `{ email }` | `200 OK` `{ message }` | `200 OK` (Idempotente, no fuga si email existe) | Genera `TokenRecuperacion`, encola email con link. |
| `POST` | `/api/auth/password-reset-confirm/` | `PasswordResetConfirmView`| Pública | `{ token, new_password }` | `200 OK` `{ message }` | `400` (Token vencido o contraseña débil) | Actualiza hash Argon2 en `Usuario`, invalida token. |

---

## 2. Módulo de Empresas y Organización

| Método | Ruta | Vista / Función | Permisos | Entrada (Payload JSON) | Códigos HTTP | Efectos Secundarios |
|---|---|---|---|---|---|---|
| `GET` | `/api/empresas/` | `EmpresaViewSet.list` | Autenticado (`EsAdmin`) | Query params: `search`, `page` | `200` | Consulta empresas del sistema. |
| `GET` | `/api/empresas/{id}/` | `EmpresaViewSet.retrieve` | Autenticado | Ninguna | `200`, `403`, `404` | Consulta detalle de empresa. |
| `PATCH` | `/api/empresas/{id}/branding/` | `EmpresaViewSet.branding` | Autenticado (`EsAdmin` o `EsResponsableSST`) | Multipart: `logo` (PNG/JPG), `color_primario`, `color_secundario` | `200`, `400` | Actualiza branding institucional y guarda archivo en storage. |
| `POST` | `/api/empresas/clasificar-ciiu-ia/` | `ClasificarCIIUIAView` | Autenticado | `{ descripcion_actividad }` | `200 OK` `{ ciiu, descripcion, riesgo }` | Invoca servicio Anthropic o fallback Decreto 768. |
| `GET/POST`| `/api/modulo0/sedes/` | `SedeViewSet` | Autenticado (Multi-tenant) | `{ nombre, direccion, ciudad, riesgo_arl }` | `200`, `201`, `400` | Crea sede asociada a la empresa. |
| `GET/POST`| `/api/modulo0/organigrama/` | `NodoOrganigramaViewSet` | Autenticado (Multi-tenant) | `{ titulo, cargo_id, padre_id, pos_x, pos_y }` | `200`, `201`, `400` | Estructura recursiva de nodos jerárquicos. |
| `GET/POST`| `/api/modulo0/procesos/` | `ProcesoViewSet` | Autenticado (Multi-tenant) | `{ nombre, tipo, objetivo }` | `200`, `201`, `400` | Registro de procesos (Estratégico, Misional, Apoyo). |
| `GET/PUT` | `/api/modulo0/identidad/` | `ContextoEmpresaViewSet` | Autenticado (Multi-tenant) | `{ mision, vision, politica_sst, valores }` | `200`, `400` | Actualiza textos institucionales de la empresa. |

---

## 3. Módulo de Perfiles de Cargo (`/api/modulo1/perfiles-cargo/`)

| Método | Ruta | Vista / Función | Permisos | Entrada (Payload JSON) | Códigos HTTP | Efectos Secundarios |
|---|---|---|---|---|---|---|
| `GET` | `/api/modulo1/perfiles-cargo/` | `PerfilCargoViewSet.list` | Autenticado (Multi-tenant) | Query: `sede`, `proceso`, `search` | `200` | Lista perfiles de cargo de la empresa. |
| `POST` | `/api/modulo1/perfiles-cargo/` | `PerfilCargoViewSet.create` | Autenticado (`EsResponsableSST`) | `{ nombre, codigo, area, sede_id, proceso_id, riesgo_arl, criticidades: {...}, competencias: [...] }` | `201`, `400` | Crea perfil y genera versión inicial `v1` en `CargoVersion`. |
| `GET` | `/api/modulo1/perfiles-cargo/{id}/` | `PerfilCargoViewSet.retrieve` | Autenticado | Ninguna | `200`, `404` | Retorna descriptor completo, peligros y EPPs. |
| `PUT/PATCH`| `/api/modulo1/perfiles-cargo/{id}/`| `PerfilCargoViewSet.update` | Autenticado (`EsResponsableSST`) | Campos a modificar | `200`, `400` | Incrementa versión inmutable (`CargoVersion` v+1). |
| `GET` | `/api/modulo1/perfiles-cargo/{id}/versiones/` | `CargoVersionListView` | Autenticado | Ninguna | `200` | Retorna lista de snapshots históricos en JSON. |
| `POST` | `/api/modulo1/perfiles-cargo/generar-ia/` | `GenerarPerfilIAView` | Autenticado | `{ cargo_nombre, sector_economico }` | `200 OK` (JSON estructurado) | Invoca IA para funciones y Decreto 1072. |

---

## 4. Módulo de Reclutamiento y Banco de Talento (`/api/reclutamiento/`)

| Método | Ruta | Vista / Función | Permisos | Entrada | Códigos HTTP | Efectos Secundarios |
|---|---|---|---|---|---|---|
| `GET/POST`| `/api/reclutamiento/candidatos/` | `CandidatoViewSet` | Autenticado (Tenant) | `{ documento, nombres, apellidos, email, telefono, ciudad, autoriza_habeas_data: true }` | `200`, `201`, `400` | Banco de talento. Registra aspirante con validación Habeas Data. |
| `GET/POST`| `/api/reclutamiento/vacantes/` | `VacanteViewSet` | Autenticado (Tenant) | `{ titulo, perfil_cargo_id, cupos, salario, auto_crear_proceso: true }` | `200`, `201`, `400` | Genera código `VAC-YYYY-NNNN` y crea proceso 1:1. |
| `GET/POST`| `/api/reclutamiento/procesos/` | `ProcesoSeleccionViewSet` | Autenticado (Tenant) | `{ vacante_id, etapas_obligatorias: [...] }` | `200`, `201`, `400` | Administra la convocatoria. |
| `GET/POST`| `/api/reclutamiento/postulaciones/` | `PostulacionViewSet` | Autenticado (Tenant) | `{ candidato_id, proceso_id }` | `200`, `201`, `400` | Inicia máquina de estados en `POSTULADO`. Crea `PostulacionEvento`. |
| `POST` | `/api/reclutamiento/postulaciones/{id}/cambiar_estado/` | `PostulacionViewSet.cambiar_estado` | Autenticado (Rol Proceso) | `{ nuevo_estado, motivo, justificacion_excepcion }` | `200`, `400`, `403` | Valida matriz de transiciones (RN-R01) y registra evento inmutable. Si cubre vacante, cierra demás (RN-R06). |
| `POST` | `/api/reclutamiento/postulaciones/{id}/reapertura_excepcional/` | `PostulacionViewSet.reapertura` | Autenticado (Rol Proceso) | `{ motivo, justificacion }` | `200`, `400` | Reabre postulación cerrada (RN-R07) sin borrar historial. |
| `POST` | `/api/reclutamiento/postulaciones/{id}/entrevistas/` | `EntrevistaCreateView` | Autenticado | `{ fecha, entrevistador, resultado, observaciones }` | `201`, `400` | Registra calificación de entrevista. |
| `POST` | `/api/reclutamiento/postulaciones/{id}/evaluaciones/` | `EvaluacionCreateView` | Autenticado | `{ tipo, puntaje, aprobado }` | `201`, `400` | Registra prueba técnica o psicotécnica. |
| `GET` | `/api/reclutamiento/portal/vacantes/` | `VacantePublicaListView`| Pública | Query: `search`, `ciudad` | `200` | Retorna vacantes activas y publicadas en portal. |
| `POST` | `/api/reclutamiento/portal/postular/` | `PostularCandidatoView` | Pública | Form multipart: datos + CV + `autoriza_habeas_data=true` | `201 Created` `{ token_otp, pin }` | Si no existe, crea candidato en Banco de Talento. Crea postulación y emite OTP. |
| `POST` | `/api/reclutamiento/portal/solicitar-otp/` | `SolicitarOTPCandidatoView`| Pública | `{ documento, email }` | `200 OK` | Genera OTP y envía a correo del aspirante. |
| `POST` | `/api/reclutamiento/portal/verificar-otp/` | `VerificarOTPCandidatoView`| Pública | `{ token_acceso, codigo_otp }` | `200 OK` `{ access_token, postulaciones: [...] }` | Acceso a seguimiento de postulaciones. |

---

## 5. Módulo de Gestión Humana y Trabajadores (`/api/gestion-humana/` y `/api/capacitaciones/`)

| Método | Ruta | Vista / Función | Permisos | Entrada | Códigos HTTP | Efectos Secundarios |
|---|---|---|---|---|---|---|
| `GET/POST`| `/api/capacitaciones/trabajadores/` | `TrabajadorViewSet` | Autenticado (Tenant) | `{ documento, nombre, email, perfil_cargo_id, tipo_contrato, fecha_ingreso, salario_base }` | `200`, `201`, `400` | Crea trabajador con validación de unicidad `(empresa, documento)`. |
| `GET` | `/api/gestion-humana/trabajadores/plantilla-excel/` | `PlantillaExcelView` | Autenticado | Ninguna | `200` (Descarga `.xlsx`) | Genera hoja de cálculo formateada con catálogos. |
| `POST` | `/api/gestion-humana/trabajadores/importar-excel/` | `ImportarExcelView` | Autenticado | Multipart: archivo `.xlsx` | `200 OK` `{ importados, errores: [...] }` | Procesa en lote creando o actualizando trabajadores. |
| `GET/POST`| `/api/gestion-humana/examenes/` | `ExamenMedicoViewSet` | Autenticado (Tenant) | `{ trabajador_id, tipo_examen, fecha, concepto, tiene_restricciones, archivo }` | `200`, `201`, `400` | Registra examen y archivo en S3. |
| `GET/POST`| `/api/gestion-humana/licencias/` | `LicenciaConduccionViewSet`| Autenticado (Tenant) | `{ trabajador_id, numero, categoria, fecha_vencimiento }` | `200`, `201`, `400` | Control de vigencia de conducción. |
| `POST` | `/api/capacitaciones/furat-pdf/` | `FuratPDFExportView` | Autenticado | `{ incidente_id }` | `200` (PDF binario) | Genera plantilla oficial FURAT con ReportLab. |

---

## 6. Módulo MICHC y HBSEO (`/api/michc/` y `/api/hbseo/`)

| Método | Ruta | Vista / Función | Permisos | Entrada | Códigos HTTP | Efectos Secundarios |
|---|---|---|---|---|---|---|
| `POST` | `/api/michc/evaluaciones/evaluar-trabajador/` | `EvaluarTrabajadorView`| Autenticado | `{ trabajador_id }` | `200 OK` `{ porcentaje, semaforo, estado, factores }` | Ejecuta motor MICHC. Si porcentaje $<80\%$, señal dispara brecha automática en HBSEO. |
| `GET` | `/api/michc/matriz/` | `MatrizHabilitacionListView`| Autenticado | Query: `cargo`, `semaforo` | `200 OK` | Retorna tabla consolidada de habilitación por empresa. |
| `GET/POST`| `/api/hbseo/brechas/` | `BrechaViewSet` | Autenticado (Tenant) | `{ tipo, titulo, descripcion, criticidad }` | `200`, `201`, `400` | Hub central de brechas. |
| `POST` | `/api/hbseo/brechas/{id}/acciones/` | `BrechaAccionCreateView` | Autenticado | `{ accion, responsable_id, fecha_compromiso }` | `201`, `400` | Agrega plan de mitigación a la brecha. |

---

## 7. Módulo de Estándares Mínimos, Evidencias, Informes y Alertas

| Método | Ruta | Vista / Función | Permisos | Entrada | Códigos HTTP | Efectos Secundarios |
|---|---|---|---|---|---|---|
| `GET` | `/api/estandares/` | `EstandarListView` | Autenticado | Query: `ciclo`, `capitulo` | `200` | Catálogo de estándares Resolución 0312. |
| `GET/POST`| `/api/evaluaciones/` | `EvaluacionViewSet` | Autenticado (Tenant) | `{ anio }` | `200`, `201` | Autoevaluación anual SG-SST. |
| `POST` | `/api/respuestas/{id}/calificar/` | `CalificarEstandarView` | Autenticado (`EsResponsableSST`) | `{ cumple: true/false, no_aplica, justificacion }` | `200`, `400` | Actualiza puntaje anual de la empresa. |
| `POST` | `/api/estandares/apelaciones/` | `ApelacionViewSet.create` | Autenticado (`EsResponsableSST`) | `{ respuesta_id, motivo }` | `201`, `400` | Impugna calificación y notifica al Auditor. |
| `POST` | `/api/estandares/apelaciones/{id}/resolver/` | `ApelacionViewSet.resolver`| Autenticado (`EsAuditor`) | `{ decision: 'aceptada'/'rechazada', respuesta_auditor }` | `200`, `403` | Dictamen de auditoría y notificación al Responsable. |
| `POST` | `/api/evidencias/` | `EvidenciaViewSet.create` | Autenticado | Multipart: `respuesta_id`, `archivo`, `descripcion` | `201`, `400` | Calcula SHA-256, sube a S3 y asocia a respuesta. |
| `GET` | `/api/informes/{id}/pdf/` | `InformePDFExportView` | Autenticado | Ninguna | `200` (PDF) | Genera informe de auditoría con firma estampada. |
| `POST` | `/api/informes/estampado-firma/` | `EstampadoFirmaView` | Autenticado (`AltaDireccion`/`Responsable`) | Multipart: `informe_id`, `firma_imagen` | `200`, `400` | Estampa firma con sello de tiempo e ID SHA-256. |
| `GET` | `/api/notificaciones/` | `NotificacionListView` | Autenticado | Ninguna | `200 OK` | Bandeja de notificaciones del usuario autenticado. |
| `POST` | `/api/notificaciones/{id}/marcar_leida/`| `MarcarLeidaView` | Autenticado | Ninguna | `200 OK` | Actualiza `leida=True`. |
