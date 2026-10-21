# 07 — Documentación Exhaustiva de Módulos de Negocio Restantes

Este documento detalla los 20 dominios de negocio complementarios de FOSST V.I.D.A., explicando el problema que resuelven, el flujo funcional de inicio a fin, las entidades involucradas, endpoints, pantallas frontend, permisos, dependencias y limitaciones conocidas.

---

## 1. Módulo de Cuentas y Control de Acceso (`apps/accounts`)

### 1.1 Problema de Negocio
Las plataformas corporativas de SST manejan información médico-laboral y de accidentes altamente confidencial. Se requiere un control de acceso estricto que garantice que nadie ingrese sin verificación de doble factor, que los intentos de intrusión se bloqueen persistentemente y que los roles estén estrictamente delimitados.

### 1.2 Flujo Funcional de Inicio a Fin
1. **Registro:** El usuario solicita creación de cuenta vinculada a su empresa (`POST /api/auth/registro/`). La cuenta nace inactiva (`is_active=False`) y se emite un `TokenActivacion` de 48 horas enviado por correo.
2. **Activación:** Al hacer clic en el enlace del correo (`ActivarCuentaPage.tsx`), la API (`POST /api/auth/activar/`) valida el token y activa al usuario.
3. **Inicio de Sesión:** El usuario ingresa documento y contraseña en `LoginPage.tsx`. El backend valida el hash Argon2. Si es correcto, genera un `CodigoOTP` de 6 dígitos que expira en 5 minutos y redirige a `OTPPage.tsx`.
4. **Verificación OTP:** El usuario ingresa el código. Al verificarse (`POST /api/auth/verificar-otp/`), el sistema emite el par JWT (`access` 15 min, `refresh` 24h) y el frontend almacena el token en `localStorage` sincronizándolo con `AuthContext`.

### 1.3 Entidades y Reglas
- `Usuario`: Modelo personalizado (`AbstractBaseUser`) con `documento`, `email`, `rol` y relación a `Empresa`.
- `CodigoOTP`: Código de 6 dígitos de un solo uso asociado al usuario.
- **Regla RN-SEG-01:** Política de contraseñas de alta seguridad (8 caracteres, mayúscula, minúscula, dígito y carácter especial).

### 1.4 Endpoints y Frontend
- Endpoints: `/api/auth/registro/`, `/api/auth/activar/`, `/api/auth/login/`, `/api/auth/verificar-otp/`, `/api/auth/password-reset/`, `/api/auth/password-reset-confirm/`.
- Frontend: `LoginPage.tsx`, `OTPPage.tsx`, `RegistroEmpresaPage.tsx`, `ActivarCuentaPage.tsx`, `RecuperarPasswordPage.tsx`, `ResetearPasswordPage.tsx`.

### 1.5 Pruebas y Estado
- Probado mediante `apps/accounts/tests/test_activacion_y_validaciones.py` y `test_smtp_email.py`.
- Estado: **[IMPLEMENTADO Y PROBADO]**.

---

## 2. Módulo de Empresas y Caracterización (`apps/empresas`)

### 2.1 Problema de Negocio
El marco legal colombiano (Decreto 1072/2015 y Res. 0312/2019) exige que los requisitos del SG-SST se determinen de forma obligatoria según el nivel de riesgo ARL (I a V) y el número de trabajadores.

### 2.2 Flujo Funcional de Inicio a Fin
Al registrarse la empresa, el sistema solicita NIT, sector económico (CIIU oficial Decreto 768 de 2022), clase de riesgo ARL y número de trabajadores. La función determinista `clasificar_capitulo` evalúa automáticamente:
- $\le 10$ trabajadores y Riesgo I, II, III $\rightarrow$ **Capítulo I** (7 Estándares).
- $11 - 50$ trabajadores y Riesgo I, II, III $\rightarrow$ **Capítulo II** (21 Estándares).
- $> 50$ trabajadores o Riesgo IV / V (cualquier tamaño) $\rightarrow$ **Capítulo III** (60 Estándares).

### 2.3 Branding y Personalización
Permite almacenar paleta de colores y logotipo (`PATCH /api/empresas/{id}/branding/`), consumido por `BrandingContext.tsx` en el frontend para reflejar la identidad corporativa del cliente.

### 2.4 Pruebas y Estado
- Probado mediante `apps/empresas/tests/test_branding.py` y `test_registro_ciiu.py`.
- Estado: **[IMPLEMENTADO Y PROBADO]**.

---

## 3. Módulo de Suscripciones y Plan Gating (`apps/planes`)

### 3.1 Problema de Negocio
Monetización SaaS de la plataforma FOSST V.I.D.A. evitando que empresas con planes básicos accedan a módulos avanzados (MICHC, Reclutamiento, IA) sin la debida suscripción.

### 3.2 Reglas y Mecanismos de Control
- Modelo `Plan`: Catálogo con identificador (`free`, `estandar`, `premium`) y lista de módulos permitidos.
- Decorador `@requiere_plan_modulo(codigo_modulo)` y mixin `PlanGatingMixin`: Interceptan la petición antes de ejecutar el viewset; si la suscripción de la empresa no incluye el módulo, aborta con `403 Forbidden` (`{"error": "PLAN_RESTRICTION", "mensaje": "Su plan actual no incluye acceso a este módulo."}`).

### 3.3 Pruebas y Estado
- Probado mediante `apps/common/tests/test_fase1_integridad_seguridad.py`.
- Estado: **[IMPLEMENTADO Y PROBADO]**.

---

## 4. Módulo de Contexto Organizacional (`apps/organizacion`)

### 4.1 Problema de Negocio
El Capítulo I de los estándares mínimos exige documentar la estructura de la empresa: sedes operativas, organigrama, mapas de proceso y políticas corporativas.

### 4.2 Flujo Funcional y Pantallas
1. **Sedes (`SedesView.tsx`):** Registro de sedes con municipio y clase de riesgo ARL.
2. **Organigrama (`OrganigramaView.tsx`):** Árbol jerárquico recursivo (`NodoOrganigrama`). Permite arrastrar nodos y guardar coordenadas espaciales `(pos_x, pos_y)`. Integra exportación gráfica vía `html2canvas`.
3. **Mapa de Procesos (`ProcesosView.tsx`):** Clasificación en *Estratégicos, Misionales y de Apoyo*.
4. **Identidad (`IdentidadView.tsx`):** Captura de misión, visión, política SST y objetivos.

### 4.3 Pruebas y Estado
- Probado mediante `apps/organizacion/tests/test_organigrama_export.py`.
- Estado: **[IMPLEMENTADO Y PROBADO]**.

---

## 5. Módulo de Perfiles de Cargo (`apps/perfilcargo`)

### 5.1 Problema de Negocio
El descriptor de cargo tradicional es estático. FOSST V.I.D.A. requiere un perfil multidimensional que articule responsabilidades legales (Decreto 1072/2015), peligros asociados (GTC 45) y requerimientos de competencias técnicas.

### 5.2 Reglas Clave
- **Criticidad en 5 Dimensiones:** Valoración (*Baja, Media, Alta, Crítica*) en SST, Operacional, Vial, Ambiental y Estratégica.
- **Versionado Inmutable (`CargoVersion`):** Cada modificación del perfil guarda una instantánea JSON en base de datos (`v1, v2, ...`), permitiendo auditorías retroactivas.
- **Asistencia IA:** Generación de funciones sugeridas según Decreto 1072 vía LLM (`apps/ia`).

### 5.3 Pruebas y Estado
- Probado mediante `apps/perfilcargo/tests/test_fase1_perfil_extendido.py`.
- Estado: **[IMPLEMENTADO Y PROBADO]**.

---

## 6. Módulo de Trabajadores y Capacitaciones (`apps/capacitaciones`)

### 6.1 Problema de Negocio
Gestión del personal activo de la organización, cumplimiento del plan anual de formación y reporte de accidentes laborales.

### 6.2 Flujo Funcional
- Registro de trabajadores independientes de cuentas de usuario (`UniqueConstraint(fields=["empresa", "documento"])`).
- Programación de capacitaciones con control de lista de asistencia y porcentaje de cobertura.
- Exportación del formato oficial **FURAT** en PDF para notificación de accidentes a ARL.

### 6.3 Pruebas y Estado
- Probado mediante `apps/common/tests/test_fase2_requerimientos_pendientes.py`.
- Estado: **[IMPLEMENTADO Y PROBADO]**.

---

## 7. Módulo de Gestión Humana y Salud Ocupacional (`apps/gestion_humana`)

### 7.1 Problema de Negocio
Vigilancia epidemiológica, aptitud psicofísica y control masivo de la planta de personal.

### 7.2 Flujo Funcional
1. **Exámenes Médicos:** Registro de evaluaciones médicas ocupacionales (Ingreso, Periódico, Egreso) con fechas de vigencia y banderas de restricciones físicas/laborales.
2. **Licencias de Conducción:** Registro de categorías y vencimientos para personal con riesgo vial.
3. **Importador Masivo:** Parser Excel (`importador.py`) que valida documentos, sedes, cargos y fechas, procesando cientos de registros en lote sin bloquear el servidor.

### 7.3 Pruebas y Estado
- Probado mediante `apps/gestion_humana/tests/test_gestion_humana.py` y `apps/common/tests/test_fase2_requerimientos_pendientes.py`.
- Estado: **[IMPLEMENTADO Y PROBADO]**.

---

## 8. Módulo de Evaluación de Competencias (`apps/formacion`)

### 8.1 Problema de Negocio
Medición periódica de la brecha entre las habilidades requeridas por el cargo y el desempeño real del empleado.

### 8.2 Flujo Funcional y Señales
- Se registran evaluaciones en escala de 1 a 4 (*Básico a Experto*).
- El método `save()` calcula automáticamente la brecha: $\text{brecha} = \max(0, \text{nivel\_requerido} - \text{nivel\_alcanzado})$.
- Si la brecha es $> 0$, una señal Django (`signals.py`) crea automáticamente una brecha tipo `COMPETENCIA` en **HBSEO**.

### 8.3 Pruebas y Estado
- Probado mediante `apps/formacion/tests/test_formacion.py`.
- Estado: **[IMPLEMENTADO Y PROBADO]**.

---

## 9. Módulo de Estándares Mínimos y Apelaciones (`apps/estandares`)

### 9.1 Problema de Negocio
Autoevaluación obligatoria del estándar colombiano (Res. 0312/2019) y resolución de controversias entre la empresa y el auditor externo.

### 9.2 Flujo Funcional de Apelaciones
1. El Auditor califica un estándar como "No Cumple" y emite una observación.
2. El Responsable SST radica una apelación (`POST /api/estandares/apelaciones/`) con su justificación técnica, lo cual genera una `Notificacion` inmediata al Auditor.
3. El Auditor revisa la inconformidad en `ApelacionesAuditorView.tsx` y dicta resolución formal (`aceptada` o `rechazada`), actualizándose el estado y notificando de vuelta al Responsable.

### 9.3 Pruebas y Estado
- Probado mediante `apps/common/tests/test_apelaciones_rf_sst_03.py` y `test_transicion_capitulo_rf_usr_03.py`.
- Estado: **[IMPLEMENTADO Y PROBADO]**.

---

## 10. Módulo de Evidencias Digitales (`apps/evidencias`)

### 10.1 Problema de Negocio
Garantizar la autenticidad e integridad legal de los documentos y soportes del SG-SST ante visitas del Ministerio del Trabajo o litigios.

### 10.2 Flujo Criptográfico
Al cargar un archivo (`POST /api/evidencias/`):
1. El backend calcula el digesto **SHA-256** del contenido binario.
2. Almacena el archivo en MinIO / AWS S3 y guarda el hash hexadecimal en la base de datos PostgreSQL.
3. Aplica borrado lógico (`SoftDeleteModel`): ningún soporte se destruye físicamente de la base de datos.

### 10.3 Pruebas y Estado
- Probado mediante `apps/evidencias/tests/test_evidencias.py`.
- Estado: **[IMPLEMENTADO Y PROBADO]**.

---

## 11. Módulo de Hallazgos y Planes de Mejora (`apps/hallazgos`)

### 11.1 Problema de Negocio
Las desviaciones normativas detectadas en auditoría deben traducirse en acciones correctivas con fechas límite legales.

### 11.2 Regla de Fechas Automáticas (RN-05)
Al crearse un plan de mejora, el sistema calcula la fecha límite máxima de cumplimiento según la prioridad asignada:
- **Urgente:** 3 meses.
- **Importante:** 6 meses.
- **Aceptable:** 12 meses.
Solo el auditor titular que formuló el hallazgo tiene permisos para modificarlo o anularlo (SEC-01).

### 11.3 Pruebas y Estado
- Probado mediante `apps/common/tests/test_auditor_notificaciones.py`.
- Estado: **[IMPLEMENTADO Y PROBADO]**.

---

## 12. Módulo de Informes Oficiales y Estampado Digital (`apps/informes`)

### 12.1 Problema de Negocio
Generación del informe anual consolidado para la Alta Dirección y firma de cierre de auditoría.

### 12.2 Estampado Criptográfico de Firmas (`firmas.py`)
Permite capturar la firma digitalizada del Responsable SST y del Representante Legal, incrustándola en el documento PDF generado por ReportLab junto con:
- Timestamp UTC certificado.
- Hash identificador SHA-256 del documento.
- Datos de identidad y matrícula profesional del firmante.

### 12.3 Pruebas y Estado
- Probado mediante `apps/common/tests/test_fase2_requerimientos_pendientes.py`.
- Estado: **[IMPLEMENTADO Y PROBADO]**.

---

## 13. Módulo de Habilitación y Cumplimiento MICHC (`apps/michc`)

### 13.1 Problema de Negocio
Confrontar si el personal contratado está legal y técnicamente apto para ocupar su cargo, detectando inconsistencias médicas antes de que ocurran accidentes.

### 13.2 Motor Determinista de 9 Factores
El motor `apps/michc/engine.py` evalúa:
1. Nivel académico requerido vs. alcanzado.
2. Experiencia laboral general.
3. Experiencia específica en el rol.
4. Formación técnica especializada.
5. Cursos obligatorios SST (ej. 50 horas, alturas, espacios confinados).
6. Licencia de conducción (categoría y vigencia).
7. Examen médico periódico al día.
8. Concepto médico favorable.
9. **Compatibilidad estricta de restricciones médicas** contra los peligros del cargo (GTC 45).

### 13.3 Semáforo y Tarea IA
- Puntuación $\ge 100\% \rightarrow$ 🟢 Verde (*Habilitado*).
- $80 - 99\% \rightarrow$ 🟡 Amarillo (*Restringido*).
- $< 80\% \rightarrow$ 🔴 Rojo (*No Apto / Brecha Crítica*). Dispara automáticamente registro en **HBSEO** y encola tarea Celery para diagnóstico narrativo con Claude.

### 13.4 Pruebas y Estado
- Probado mediante `apps/michc/tests/test_michc.py`.
- Estado: **[IMPLEMENTADO Y PROBADO]**.

---

## 14. Módulo de Historial de Brechas HBSEO (`apps/hbseo`)

### 14.1 Problema de Negocio
Evitar la dispersión de no conformidades manteniendo una bandeja única de tratamiento donde converjan las fallas de auditoría, las brechas de competencias y las restricciones médicas.

### 14.2 Arquitectura Polimórfica
Utiliza `GenericForeignKey` (`BrechaOrigen`), permitiendo que una brecha provenga de una evaluación MICHC, una prueba de Formación o un Hallazgo de Estándares, administrando un ciclo de vida con estados: *Detectada $\rightarrow$ En Tratamiento $\rightarrow$ Controlada $\rightarrow$ Subsanada $\rightarrow$ Cerrada*.

### 14.3 Pruebas y Estado
- Probado mediante `apps/hbseo/tests/test_brecha_service.py` y `apps/common/tests/test_fase3_brechas_v02.py`.
- Estado: **[IMPLEMENTADO Y PROBADO]**.

---

## 15. Módulo de Calendario e Incidentes (`apps/calendario`)

### 15.1 Problema de Negocio
Planificación anual del cronograma SST y registro formal de incidentes laborales según exigencias de la ARL.

### 15.2 Funcionalidades Verificadas
- Cronograma de actividades clasificadas (*Capacitación, Auditoría, Vencimiento, Inspección*).
- Cálculo automático de tasas de accidentalidad: Índice de Frecuencia (IF), Índice de Severidad (IS) e Índice de Lesiones Incapacitantes (ILI) (`/api/calendario/metricas-accidentalidad/`).
- Repositorio central de la tabla `Notificacion`.

### 15.3 Pruebas y Estado
- Probado mediante `apps/common/tests/test_fase2_requerimientos_pendientes.py`.
- Estado: **[IMPLEMENTADO Y PROBADO]**.

---

## 16. Motor de Alertas Preventivas (`apps/alertas`)

### 16.1 Problema de Negocio
Evitar el vencimiento imprevisto de exámenes médicos, licencias y contratos laborales que generen sanciones del Ministerio del Trabajo.

### 16.2 Reglas Dinámicas y Celery Beat
- Permite configurar reglas parametrizadas (`ReglaAlerta`) con días de anticipación (ej. 60, 30, 15 días).
- La tarea programada `revisar_vencimientos` corre diariamente en Celery Beat, aplica deduplicación por día y genera las notificaciones en base de datos.

### 16.3 Pruebas y Estado
- Probado mediante `apps/alertas/tests/test_alertas.py`.
- Estado: **[IMPLEMENTADO Y PROBADO]**.

---

## 17. Módulo de Dashboards y KPIs (`apps/dashboard`)

### 17.1 Problema de Negocio
Ofrecer visibilidad diferenciada según el rol del usuario sin sobrecargar la base de datos relacional con consultas analíticas pesadas.

### 17.2 Páneles con Caché Redis (TTL 300s)
- **Alta Dirección (`DashboardAltaDireccionView`):** Porcentaje macro de cumplimiento de estándares, inversión y semáforo general.
- **Responsable SST (`DashboardResponsableView`):** Estado de autoevaluación actual, brechas abiertas, tareas de calendario y habilitación MICHC.
- **Auditor (`DashboardAuditorView`):** Cobertura de revisión, hallazgos emitidos y apelaciones pendientes.

### 17.3 Estado
- **[IMPLEMENTADO Y PROBADO]** (Caché Redis y endpoints DRF).

---

## 18. Módulo Centralizado de Inteligencia Artificial (`apps/ia`)

### 18.1 Problema de Negocio
Proveer capacidades generativas (clasificación CIIU, perfiles de cargo, redacción de diagnósticos MICHC) con tolerancia a fallos ante caídas de red o indisponibilidad de proveedores externos.

### 18.2 Resiliencia y Fallback
- Cliente wrapper sobre Anthropic API (Claude 3.5 Sonnet).
- Si la API externa no está configurada o falla la conexión, el servicio ejecuta de forma transparente un fallback determinista local basado en palabras clave y en el catálogo del Decreto 768.

### 18.3 Pruebas y Estado
- Probado mediante `apps/ia/tests/test_ia_service.py`.
- Estado: **[IMPLEMENTADO Y PROBADO]**.

---

## 19. Módulo de Auditoría Transversal (`apps/auditoria`)

### 19.1 Problema de Negocio
Exigencia de trazabilidad legal inmutable sobre quién modificó o borró información en el sistema.

### 19.2 Middleware de Auditoría
- `AuditoriaMiddleware` intercepta peticiones no seguras (`POST`, `PUT`, `PATCH`, `DELETE`).
- Captura usuario autenticado, IP remota, User-Agent, ruta, código HTTP, y genera una fila en `AuditLog` guardando los valores anteriores y los valores nuevos serializados.

### 19.3 Estado
- **[IMPLEMENTADO Y VERIFICADO POR MIDDLEWARE]**.

---

## 20. Módulo de Seguridad y Dispositivos (`apps/seguridad`)

### 20.1 Problema de Negocio
Detección de accesos no autorizados desde navegadores o ubicaciones inusuales.

### 20.2 Huella de Dispositivo y Bloqueo
- `DispositivoMiddleware` genera una huella del dispositivo (`User-Agent` normalizado + IP).
- Compara contra `DispositivoConocido`. Si es un dispositivo nuevo, genera un `EventoRiesgo` y dispara correo de advertencia al titular de la cuenta.

### 20.3 Estado
- **[IMPLEMENTADO Y VERIFICADO EN CÓDIGO]**.
