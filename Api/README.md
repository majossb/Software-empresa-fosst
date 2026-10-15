# Migración DiagnostISST: Express/Prisma → Django REST Framework

## 0. Diagnóstico del proyecto actual

Tu backend real **no usa el SDK/Auth de Supabase**: es **Node + Express + Prisma**,
y Postgres simplemente está *alojado* en Supabase (o donde sea, es Postgres puro).
Eso es una buena noticia: la migración es "solo" de la capa de aplicación
(Express/Prisma → Django/DRF), la base de datos casi no cambia.

El login actual (`auth.controller.ts`) ya hace bastante bien: bcrypt, JWT,
un `LoginAttemptsService` en memoria y alertas por correo tras varios fallos.
Lo que falta para el nivel "empresarial" que describe tu documento es:
activación de cuenta, OTP real en el login, recuperación de contraseña,
auditoría transversal, bloqueo persistente (no en memoria) e historial de
dispositivos. Eso es justo lo que arma el proyecto adjunto.

## 1. Estrategia de migración recomendada (fases)

1. **Fase 0 — Congelar el modelo de datos.** Exporta el `schema.prisma` a SQL
   (`npx prisma migrate diff` o simplemente `pg_dump --schema-only`) y usa
   `python manage.py inspectdb` sobre esa misma base para partir de algo
   fiel. En este starter ya modelé a mano las tablas de `usuarios` y
   `empresas` conservando los mismos nombres de columna (`nit`, `documento`,
   `rol`, `capitulo_vigente`, etc.) para que **no tengas que migrar datos**,
   solo apuntar `DATABASE_URL` a la misma base.
2. **Fase 1 — Autenticación primero.** Es el módulo más sensible y el que
   pediste reforzar. Se migra completo en este entregable.
3. **Fase 2 — Módulos de negocio en paralelo.** Puedes tener Express y
   Django corriendo *a la vez* apuntando a la misma base de datos mientras
   migras módulo por módulo (`empresa`, `evidencia`, `hallazgo`, `informe`,
   `capacitacion`, etc.), y usar un proxy (nginx/Traefik) que enrute
   `/api/auth/*` y `/api/empresas/*` a Django y el resto a Express hasta
   terminar. Esto evita un "big bang" arriesgado.
4. **Fase 3 — Apagar Express** cuando todos los módulos estén migrados y
   probados. El frontend (React) casi no cambia: solo ajustas
   `auth.service.ts` y los demás `*.service.ts` a los nuevos endpoints/tokens.

## 2. Por qué Django/DRF encaja con lo que pide tu evaluación

| Requisito del documento                      | Cómo lo resuelve Django/DRF                                   |
|-----------------------------------------------|----------------------------------------------------------------|
| Mayor control de lógica de negocio            | Modelos, señales (`signals.py`) y servicios explícitos, sin "magia" de un BaaS |
| Mejor organización del código                 | Apps separadas por dominio (`accounts`, `empresas`, `auditoria`, `seguridad`) |
| Seguridad                                     | Hasher Argon2, validadores de contraseña, `django-axes`, throttling de DRF |
| Auditoría                                     | App `auditoria` con middleware transversal + registros explícitos en vistas sensibles |
| Pruebas automatizadas                         | `APITestCase` de DRF, fixtures de Django, `pytest-django` |
| Documentación                                 | `drf-spectacular` genera el OpenAPI/Swagger automáticamente en `/api/docs/` |

## 3. Qué contiene el proyecto adjunto (`diagnostisst_django_backend.zip`)

```
diagnostisst_django/
├── config/                  # settings, urls raíz, celery, wsgi/asgi
├── apps/
│   ├── accounts/            # ← módulo de autenticación (el que pediste)
│   │   ├── models.py        # Usuario, TokenActivacion, CodigoOTP, TokenRecuperacion
│   │   ├── serializers.py
│   │   ├── views.py         # registro, activación, login+OTP, reset password
│   │   ├── permissions.py   # EsAdmin, EsAuditor, EsResponsableSST, EsAltaDireccion...
│   │   ├── validators.py    # complejidad de contraseña
│   │   └── tasks.py         # envío de correos vía Celery (no bloqueante)
│   ├── empresas/            # administración de empresas (CRUD solo ADMIN)
│   ├── auditoria/           # AuditLog + middleware que audita cada escritura
│   └── seguridad/           # dispositivos conocidos, eventos de riesgo, notificaciones
├── templates/emails/        # plantillas de activación, OTP, reset, alerta de acceso
├── requirements.txt
└── .env.example
```

Ya validé que el proyecto corre `python manage.py check` sin errores y que
`makemigrations` genera migraciones consistentes para los 4 apps.

## 4. Cómo se implementó cada punto del "Módulo de Autenticación" pedido

- **Registro de usuarios** → `POST /api/auth/registro/`. Crea el usuario
  **inactivo** (`is_active=False`) hasta que confirme el correo.
- **Activación de cuenta por correo** → `POST /api/auth/activar/` con un
  token de un solo uso (`TokenActivacion`, vence en 48h, configurable en
  `settings.ACTIVATION_TOKEN_EXPIRATION_HOURS`).
- **Inicio de sesión** → `POST /api/auth/login/`. Valida NIT + documento +
  rol + contraseña (mismo esquema que ya usabas), pero en vez de devolver
  el JWT de una vez, dispara el paso de OTP.
- **Verificación por OTP al correo** → `POST /api/auth/verificar-otp/`.
  Código de 6 dígitos, vence en 5 minutos, máximo 5 intentos. Solo aquí se
  emite el JWT (access + refresh, vía `djangorestframework-simplejwt`).
- **Recuperación de contraseña por correo** →
  `POST /api/auth/password/solicitar-reset/` y
  `POST /api/auth/password/confirmar-reset/`, con token de un solo uso que
  vence en 1 hora. La respuesta es siempre genérica (no revela si el correo
  existe).
- **Gestión de roles y permisos** → `permissions.py` define permisos DRF por
  rol (`EsAdmin`, `EsAuditor`, `EsResponsableSST`, `EsAltaDireccion`) más
  `PerteneceAMismaEmpresa` para aislar datos entre empresas (multi-tenant).
- **Administración de empresas** → `apps/empresas` con un `ModelViewSet`
  completo restringido a `EsAdmin`.

## 5. Cómo se implementó el "Módulo de Auditoría y Seguridad"

**Auditoría**
- Login/logout, intentos fallidos, activación, cambio de contraseña →
  registrados explícitamente en las vistas de `accounts/views.py`.
- Toda operación de escritura (`POST/PUT/PATCH/DELETE`) del resto de módulos
  se audita automáticamente vía `AuditoriaMiddleware`, sin tener que tocar
  cada vista de negocio.
- Historial de cambios: cuando migres cada módulo de negocio, guarda
  `valores_anteriores`/`valores_nuevos` (ya están en el modelo `AuditLog`)
  serializando el objeto antes/después de un `update`.

**Seguridad**
- **Fuerza bruta / bloqueo temporal por usuario e IP** → `django-axes`
  (`AXES_FAILURE_LIMIT=5`, `AXES_COOLOFF_TIME=30 min`, bloquea por
  `username` **y** por `ip_address` a la vez). Esto reemplaza el
  `LoginAttemptsService` en memoria (que se perdía al reiniciar el server)
  por un bloqueo persistente en base de datos.
- **Rate limiting** → `ScopedRateThrottle` de DRF en cada endpoint sensible
  (`login`: 10/min, `otp`: 5/min, `password_reset`: 5/hora, `register`:
  5/hora, configurable en `settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]`).
- **Protección DDoS** → a nivel de aplicación Django/DRF solo mitiga parte
  del problema (rate limiting); la protección real contra DDoS volumétrico
  debe ir en la capa de infraestructura (Cloudflare, AWS Shield, un WAF, o
  al menos `nginx limit_req`). Vale la pena dejarlo explícito en la
  documentación de arquitectura como responsabilidad de infraestructura, no
  solo de código.
- **Registro de dispositivos e historial de acceso** → modelo
  `DispositivoConocido` (fingerprint de user-agent + IP) actualizado en cada
  login exitoso vía `DispositivoMiddleware`.
- **Notificación de accesos inusuales** → si el fingerprint del dispositivo
  es nuevo para ese usuario, se dispara un correo (`notificaciones.py`) y se
  registra un `EventoRiesgo`.
- **Métricas de seguridad** → el modelo `EventoRiesgo` ya queda listo para
  alimentar un dashboard (contar eventos por tipo/usuario/fecha); solo falta
  construir el endpoint de agregación cuando migres el módulo de dashboard.

## 6. Próximos pasos concretos

1. `cp .env.example .env` y completa `DATABASE_URL` con la misma cadena de
   conexión que usa tu Prisma actual (o una réplica de staging primero).
2. `pip install -r requirements.txt`
3. Si vas a partir de una base **ya poblada** por Prisma: en vez de
   `makemigrations`/`migrate`, usa
   `python manage.py migrate --fake-initial` después de ajustar los nombres
   de tabla/columna en los modelos para que calcen 1:1 con lo que ya existe
   (ya dejé `db_table` y nombres de columna iguales a los de Prisma como
   punto de partida).
4. Levanta Redis y un worker de Celery (`celery -A config worker -l info`)
   para que el envío de correos (activación, OTP, reset, alertas) no
   bloquee las peticiones.
5. Corre `python manage.py createsuperuser` para tener un admin de Django
   y gestionar usuarios/empresas desde `/admin/` mientras migras el resto
   de vistas de negocio.
6. Documentación automática disponible en `/api/docs/` (Swagger, vía
   drf-spectacular) — te sirve directo para el punto de "Documentación
   Pendiente" de tu informe (arquitectura + casos de uso los seguirás
   redactando aparte, pero el contrato de API queda autogenerado).

## 8. Estado de la migración completa (actualizado)

| Módulo | App Django | Estado |
|---|---|---|
| Autenticación | `accounts` | ✅ Completo (login+OTP, activación, reset, permisos) |
| Empresas | `empresas` | ✅ Completo (CRUD admin) |
| Auditoría | `auditoria` | ✅ Completo (middleware transversal) |
| Seguridad | `seguridad` | ✅ Completo (dispositivos, eventos de riesgo) |
| Planes y suscripciones | `planes` | ✅ Completo (CRUD) |
| Sedes / Organigrama / Procesos | `organizacion` | ✅ Completo (CRUD + jerarquía en árbol) |
| Hallazgos / Plan de mejora | `hallazgos` | ✅ Completo (CRUD) |
| Capacitaciones / Trabajadores / Afiliaciones | `capacitaciones` | ✅ Completo (CRUD) |
| Calendario / Notificaciones / Incidentes | `calendario` | ✅ Completo (CRUD + acción "marcar leída") |
| Estándares / Evaluaciones / Respuestas | `estandares` | 🟡 Solo modelos (falta lógica de cálculo de puntaje) |
| Archivos / Evidencias | `evidencias` | 🟡 Solo modelos (falta subida de archivos) |
| Informes | `informes` | 🟡 Solo modelos (falta generación de contenido) |
| Perfil de cargo + catálogos | `perfilcargo` | 🟡 Solo modelos (falta CRUD, IA y generación de PDF) |
| Dashboard | `dashboard` | ⬜ Pendiente (agregaciones de todos los módulos) |

Los módulos marcados 🟡 ya tienen sus **modelos** completos (`models.py`) y las
migraciones ya se generaron y validaron sin errores (`makemigrations` corrió
limpio con las 14 apps juntas, incluidas las referencias cruzadas entre
`organizacion` ↔ `perfilcargo` ↔ `capacitaciones`). Lo que falta en esos es
`serializers.py`, `views.py` y `urls.py` — que es la parte con lógica de
negocio propia de cada uno (cálculo de puntajes, subida de archivos a un
storage, generación de PDF, llamadas a un servicio de IA).

Todas las rutas de los módulos ✅ ya están registradas en `config/urls.py`.

## 7. Ajustes que necesitarás en el frontend (React)

- `auth.service.ts`: el login ya no devuelve el token directamente; ahora
  hace dos llamadas: `POST /api/auth/login/` (devuelve `usuario_id`) y
  luego `POST /api/auth/verificar-otp/` con el código que el usuario recibe
  por correo (agrega una pantalla intermedia de "ingresa el código").
- Los tokens ahora son `access` (15 min) + `refresh` (7 días, con rotación);
  usa `POST /api/auth/token/refresh/` en vez de tu endpoint anterior de
  `refresh`.
- Añade pantallas de "activar cuenta" y "recuperar contraseña" que ya
  tienen su endpoint listo.
