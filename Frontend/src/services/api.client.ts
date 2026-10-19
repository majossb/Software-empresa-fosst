// src/services/api.client.ts
// Cliente HTTP basado en fetch nativo — manejo unificado de errores
const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'
export const BACKEND_URL = BASE_URL.replace(/\/api\/?$/, '')

export function resolveMediaUrl(path?: string | null): string {
  if (!path) return ''
  if (path.startsWith('blob:') || path.startsWith('data:') || path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  return `${BACKEND_URL}${cleanPath}`
}

// ── Catálogo de códigos de error  ────────
// El frontend usa `code` (estable) en lugar del texto del mensaje.
export const ERROR_CODE_MESSAGES: Record<string, string> = {
  // Duplicidad
  EMAIL_ALREADY_EXISTS:
    'Este correo ya está registrado. Si ya tienes una cuenta, puedes iniciar sesión o recuperar tu contraseña.',
  NIT_ALREADY_EXISTS:
    'Este NIT ya está registrado. Verifica el número ingresado o utiliza la empresa existente.',
  DOCUMENT_ALREADY_EXISTS: 'Este documento ya está registrado.',

  // Validación de campos
  INVALID_EMAIL: 'Ingresa un correo electrónico válido.',
  INVALID_DOCUMENT: 'El documento debe contener únicamente números.',
  INVALID_NAME: 'El nombre solo puede contener letras, espacios, tildes, ñ y guiones.',
  INVALID_PHONE: 'Ingresa un número de teléfono válido.',
  INVALID_PASSWORD:
    'La contraseña debe tener mínimo 8 caracteres, una mayúscula, una minúscula, un número y un carácter especial.',
  PASSWORD_MISMATCH: 'Las contraseñas no coinciden.',
  REQUIRED_FIELD: 'Este campo es obligatorio.',
  VALIDATION_ERROR: 'No pudimos continuar. Revisa los campos marcados.',

  // Autenticación y tokens
  ACCOUNT_NOT_ACTIVATED:
    'Tu cuenta aún no ha sido activada. Revisa tu correo electrónico para activarla.',
  INVALID_ACTIVATION_TOKEN: 'El enlace de activación no es válido.',
  EXPIRED_ACTIVATION_TOKEN: 'El enlace de activación ha expirado. Solicita un nuevo enlace.',
  TOKEN_ALREADY_USED: 'Este enlace de activación ya fue utilizado. Solicita uno nuevo.',
  INVALID_OTP: 'El código ingresado no es válido.',
  EXPIRED_OTP: 'El código ha expirado. Solicita uno nuevo.',
  INVALID_CREDENTIALS: 'El correo o la contraseña no son correctos. Verifica tus datos.',
  PERMISSION_DENIED: 'No tienes permiso para realizar esta acción.',
  NOT_AUTHENTICATED: 'Debes iniciar sesión para acceder a este recurso.',

  // Recursos
  RESOURCE_NOT_FOUND: 'El recurso solicitado no existe.',
  RATE_LIMIT_EXCEEDED:
    'Has realizado demasiadas solicitudes. Espera unos minutos e intenta nuevamente.',

  // Red y servidor
  NETWORK_ERROR:
    'No pudimos conectar con el servidor. Verifica tu conexión e intenta nuevamente.',
  SERVER_ERROR: 'Tenemos un problema temporal. Intenta nuevamente en unos minutos.',
}

// Traducción de nombres de campo técnicos a etiquetas legibles
function getReadableFieldName(key: string): string {
  const names: Record<string, string> = {
    nit: 'NIT de la empresa',
    responsable_email: 'Correo electrónico',
    responsable_documento: 'Número de documento',
    responsable_nombre: 'Nombre del responsable',
    nombre: 'Nombre o Razón Social',
    num_trabajadores: 'Número de trabajadores',
    nivel_riesgo: 'Nivel de riesgo',
    ciiu_codigo: 'Código CIIU',
    ciiu_768_principal: 'Código Actividad Decreto 768',
    confirm_password: 'Confirmación de contraseña',
    password: 'Contraseña',
    email: 'Correo electrónico',
    documento: 'Número de documento',
    non_field_errors: 'Error',
    detail: 'Detalle',
  }
  return names[key] || key.replace(/_/g, ' ')
}

// ── Clase ApiError enriquecida con code, field y errors ─────────────────
export class ApiError extends Error {
  status: number
  code: string
  field?: string
  fieldErrors?: Record<string, string[]>
  data?: any
  isNetworkError: boolean

  constructor(
    message: string,
    status: number,
    options?: {
      code?: string
      field?: string
      fieldErrors?: Record<string, string[]>
      data?: any
      isNetworkError?: boolean
    }
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = options?.code ?? 'SERVER_ERROR'
    this.field = options?.field
    this.fieldErrors = options?.fieldErrors
    this.data = options?.data
    this.isNetworkError = options?.isNetworkError ?? false
  }

  /** Mensaje amigable final — prioriza el catálogo interno por código */
  get friendlyMessage(): string {
    if (this.isNetworkError) return ERROR_CODE_MESSAGES['NETWORK_ERROR']
    if (this.code === 'DOMAIN_ERROR' || this.code === 'VALIDATION_ERROR') {
      return this.message || ERROR_CODE_MESSAGES[this.code] || ERROR_CODE_MESSAGES['SERVER_ERROR']
    }
    return ERROR_CODE_MESSAGES[this.code] ?? this.message
  }
}

// ── Normalización de respuestas de error del backend ────────────────────
function normalizeApiError(
  data: unknown,
  statusText: string,
  httpStatus: number
): { message: string; code: string; field?: string; fieldErrors?: Record<string, string[]>; data?: any } {
  // Respuesta con formato estándar FOSST
  if (data && typeof data === 'object' && 'success' in data) {
    const d = data as Record<string, unknown>
    const code = (d.code as string) ?? 'SERVER_ERROR'
    const message = (d.message as string) ?? ERROR_CODE_MESSAGES[code] ?? 'Error del servidor.'
    const field = d.field as string | undefined
    const extraData = d.data

    // Construir fieldErrors desde el objeto `errors` del backend
    let fieldErrors: Record<string, string[]> | undefined
    if (d.errors && typeof d.errors === 'object') {
      fieldErrors = {}
      for (const [k, v] of Object.entries(d.errors as Record<string, unknown>)) {
        fieldErrors[k] = Array.isArray(v) ? (v as string[]) : [String(v)]
      }
    } else if (field && message) {
      fieldErrors = { [field]: [message] }
    }

    return { message, code, field, fieldErrors, data: extraData }
  }


  // Formato DRF por defecto (sin `success`)
  if (data && typeof data === 'object') {
    const d = data as Record<string, unknown>

    // Campo `error` directo (respuestas propias del backend)
    if (typeof d.error === 'string') {
      return { message: d.error, code: (d.code as string) ?? 'DOMAIN_ERROR' }
    }

    // Campo `message` o `detail` directos
    if (typeof d.message === 'string') {
      return { message: d.message, code: (d.code as string) ?? 'DOMAIN_ERROR' }
    }
    if (typeof d.detail === 'string') {
      // Mapear mensajes conocidos del backend al catálogo
      const msgLower = d.detail.toLowerCase()
      if (msgLower.includes('activa')) {
        return { message: d.detail, code: 'ACCOUNT_NOT_ACTIVATED' }
      }
      if (msgLower.includes('credenciales') || msgLower.includes('incorrect')) {
        return { message: d.detail, code: 'INVALID_CREDENTIALS' }
      }
      return { message: d.detail, code: 'DOMAIN_ERROR' }
    }

    // Errores de campo DRF (objeto de listas)
    const fieldErrors: Record<string, string[]> = {}
    const messages: string[] = []
    for (const [key, value] of Object.entries(d)) {
      if (Array.isArray(value)) {
        fieldErrors[key] = value as string[]
        messages.push(`${getReadableFieldName(key)}: ${(value as string[]).join(', ')}`)
      } else if (typeof value === 'string') {
        fieldErrors[key] = [value]
        messages.push(`${getReadableFieldName(key)}: ${value}`)
      }
    }
    if (messages.length > 0) {
      const globalMsg =
        messages.length === 1 ? messages[0] : 'No pudimos continuar. Revisa los campos marcados.'
      return { message: globalMsg, code: 'VALIDATION_ERROR', fieldErrors }
    }
  }

  // HTML de Django o string puro
  if (typeof data === 'string' && !data.startsWith('<')) {
    return { message: data, code: 'SERVER_ERROR' }
  }

  // Fallback final
  if (httpStatus >= 500) {
    return {
      message: ERROR_CODE_MESSAGES['SERVER_ERROR'],
      code: 'SERVER_ERROR',
    }
  }

  return { message: `Error ${httpStatus}: ${statusText}`, code: 'SERVER_ERROR' }
}

// ── Sanitización: trim recursivo de strings ───────────────────────────
function deepTrimStrings(obj: unknown): unknown {
  if (typeof obj === 'string') return obj.trim()
  if (Array.isArray(obj)) return obj.map(deepTrimStrings)
  if (obj !== null && typeof obj === 'object') {
    return Object.fromEntries(
      Object.entries(obj as Record<string, unknown>).map(([k, v]) => [k, deepTrimStrings(v)])
    )
  }
  return obj
}

// ── Token refresh en progreso ─────────────────────────────────────────
let refreshPromise: Promise<string | null> | null = null

async function tryRefreshToken(): Promise<string | null> {
  if (refreshPromise) return refreshPromise

  refreshPromise = (async () => {
    try {
      const refresh = localStorage.getItem('refresh_token')
      if (!refresh) return null

      const res = await fetch(`${BASE_URL}/auth/token/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      })

      if (!res.ok) return null

      const data = await res.json()
      if (data.access) {
        localStorage.setItem('token', data.access)
        return data.access as string
      }
      return null
    } catch {
      return null
    } finally {
      refreshPromise = null
    }
  })()

  return refreshPromise
}

async function request<T>(
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE',
  path: string,
  body?: unknown
): Promise<T> {
  const token = localStorage.getItem('token')
  const isFormData = body instanceof FormData
  const sanitizedBody = body !== undefined && !isFormData ? deepTrimStrings(body) : body

  const headers: HeadersInit = {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
  if (!isFormData) {
    (headers as Record<string, string>)['Content-Type'] = 'application/json'
  }

  let res: Response
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      ...(sanitizedBody !== undefined
        ? { body: isFormData ? (sanitizedBody as FormData) : JSON.stringify(sanitizedBody) }
        : {}),
    })
  } catch (networkErr) {
    // Error de red real (sin respuesta del servidor)
    throw new ApiError(ERROR_CODE_MESSAGES['NETWORK_ERROR'], 0, {
      code: 'NETWORK_ERROR',
      isNetworkError: true,
    })
  }

  let data: unknown
  const contentType = res.headers.get('content-type') ?? ''
  if (contentType.includes('application/json')) {
    data = await res.json()
  } else {
    data = await res.text()
  }

  if (!res.ok) {
    // Token expirado → intentar refresh automático
    if (res.status === 401 && !path.includes('/auth/login')) {
      const newToken = await tryRefreshToken()
      if (newToken) {
        return request<T>(method, path, body)
      }
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('auth_user')
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }

    const { message, code, field, fieldErrors, data: extraData } = normalizeApiError(data, res.statusText, res.status)
    throw new ApiError(message, res.status, { code, field, fieldErrors, data: extraData })
  }


  return data as T
}

export const apiClient = {
  get:    <T>(path: string)                => request<T>('GET',    path),
  post:   <T>(path: string, body: unknown) => request<T>('POST',   path, body),
  put:    <T>(path: string, body: unknown) => request<T>('PUT',    path, body),
  patch:  <T>(path: string, body: unknown) => request<T>('PATCH',  path, body),
  delete: <T>(path: string)                => request<T>('DELETE', path),
}