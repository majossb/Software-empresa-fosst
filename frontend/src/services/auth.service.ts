import { apiClient } from './api.client'
import type { AuthUser, LoginPayload, OTPRequiredResponse, UserRole } from '@/types'

interface BackendEmpresa {
  id:               string
  nombre:           string
  nit:              string
  capitulo_vigente?: 'I' | 'II' | 'III'
}

interface BackendUser {
  id:        string
  nombre:    string
  documento: string
  rol:       UserRole
  empresa:   BackendEmpresa
}

interface BackendLoginResponse {
  access:  string
  refresh: string
  user:    BackendUser
}

// ── Adaptar respuesta del backend → AuthUser ───────────────────────
function adaptarRespuesta(user: BackendUser): AuthUser {
  return {
    id:        user.id,
    nombre:    user.nombre,
    documento: user.documento,
    rol:       (user.rol || '').toLowerCase() as UserRole,
    empresa:   user.empresa,
  }
}

// ── Persistencia en localStorage ──────────────────────────────────
function guardarSesion(user: AuthUser, access: string, refresh: string) {
  localStorage.setItem('token', access)
  localStorage.setItem('refresh_token', refresh)
  localStorage.setItem('auth_user', JSON.stringify(user))
}

function limpiarSesion() {
  localStorage.removeItem('token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('auth_user')
}

// ── Servicio ───────────────────────────────────────────────────────
export const authService = {

  /**
   * Paso 1: Envía credenciales (sin rol).
   * Si las credenciales son válidas, el backend envía un OTP y retorna
   * { message, usuario_id, otp_expira_en_minutos, expires_at }.
   */
  async login(payload: LoginPayload): Promise<OTPRequiredResponse> {
    const data = await apiClient.post<OTPRequiredResponse>('/auth/login/', payload)
    return data
  },

  /**
   * Paso 2: Verifica el código OTP.
   * Retorna los JWT tokens + usuario completo.
   */
  async verifyOTP(usuarioId: string, codigo: string): Promise<AuthUser> {
    const data = await apiClient.post<BackendLoginResponse>('/auth/verificar-otp/', {
      usuario_id: usuarioId,
      codigo
    })

    const user = adaptarRespuesta(data.user)

    guardarSesion(user, data.access, data.refresh)
    return user
  },

  /**
   * Reenvía el OTP volviendo a hacer login con las credenciales guardadas temporalmente.
   */
  async resendOTP(payload: LoginPayload): Promise<OTPRequiredResponse> {
    return apiClient.post<OTPRequiredResponse>('/auth/login/', payload)
  },

  /**
   * Solicita el reset de contraseña por email.
   */
  async solicitarResetPassword(email: string): Promise<{ message: string }> {
    return apiClient.post<{ message: string }>('/auth/password/solicitar-reset/', { email })
  },

  /**
   * Confirma el reset de contraseña con token + nueva contraseña.
   */
  async confirmarResetPassword(payload: { token: string; password: string }): Promise<{ message: string }> {
    return apiClient.post<{ message: string }>('/auth/password/confirmar-reset/', payload)
  },

  /**
   * Activa la cuenta con el token enviado por correo.
   */
  async activarCuenta(token: string): Promise<{ message: string }> {
    return apiClient.post<{ message: string }>('/auth/activar/', { token })
  },

  /**
   * Registro de nueva empresa + usuario responsable
   */
  async registrarEmpresa(payload: any): Promise<{ message: string; empresa: any; usuario: any }> {
    return apiClient.post<{ message: string; empresa: any; usuario: any }>('/empresa/registro', payload)
  },

  /**
   * Búsqueda pública en catálogo CIIU 768
   */
  async buscarCiiu(query: string): Promise<Array<{
    codigo_768: string
    clase_riesgo: number
    ciiu_rev4: string
    descripcion: string
    sector: string
    division: string
    grupo: string
  }>> {
    if (!query || query.length < 2) return []
    return apiClient.get(`/empresa/ciiu/buscar?q=${encodeURIComponent(query)}`)
  },

  /**
   * GET /api/auth/me/ — obtiene el usuario autenticado actual.
   */
  async me(): Promise<AuthUser | null> {
    const token = localStorage.getItem('token')
    if (!token) return null

    try {
      const data = await apiClient.get<BackendUser>('/auth/me/')
      const user = adaptarRespuesta(data)
      localStorage.setItem('auth_user', JSON.stringify(user))
      return user
    } catch {
      limpiarSesion()
      return null
    }
  },

  /**
   * POST /api/auth/logout/ — invalida el refresh token en el backend.
   */
  async logout() {
    try {
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        await apiClient.post('/auth/logout/', { refresh })
      }
    } catch {
      // Silenciar — el logout local ocurre de todos modos
    } finally {
      limpiarSesion()
    }
  },

  getCurrentUser(): AuthUser | null {
    const stored = localStorage.getItem('auth_user')
    return stored ? (JSON.parse(stored) as AuthUser) : null
  },

  getToken(): string | null {
    return localStorage.getItem('token')
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('token')
  },
}