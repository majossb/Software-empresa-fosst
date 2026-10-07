/**
 * Servicio API para Reclutamiento y Selección — FOSST V.I.D.A.
 * Fases D y E: Comunicación con endpoints REST internos y Portal Público.
 */
import { apiClient } from './api.client'
import {
  CandidatoListItem,
  CandidatoDetail,
  VacanteListItem,
  VacanteDetail,
  ProcesoSeleccionDetail,
  PostulacionListItem,
  PostulacionDetail,
  FuenteReclutamiento,
  VacantePublicaListItem,
  VacantePublicaDetail,
  PostulacionCandidatoPublica,
} from '@/types/reclutamiento.types'

const CANDIDATE_TOKEN_KEY = 'candidate_portal_token'

export const reclutamientoService = {
  // ── 1. Banco de Talento (Candidatos) ─────────────────────────
  getCandidatos: (params?: { search?: string; fuente_id?: string; etiqueta?: string }) => {
    const query = new URLSearchParams()
    if (params?.search) query.set('search', params.search)
    if (params?.fuente_id) query.set('fuente_id', params.fuente_id)
    if (params?.etiqueta) query.set('etiqueta', params.etiqueta)
    const qs = query.toString() ? `?${query.toString()}` : ''
    return apiClient.get<CandidatoListItem[]>(`/reclutamiento/candidatos/${qs}`)
  },

  getCandidatoById: (id: string) => {
    return apiClient.get<CandidatoDetail>(`/reclutamiento/candidatos/${id}/`)
  },

  createCandidato: (data: Partial<CandidatoDetail>) => {
    return apiClient.post<CandidatoDetail>('/reclutamiento/candidatos/', data)
  },

  updateCandidato: (id: string, data: Partial<CandidatoDetail>) => {
    return apiClient.put<CandidatoDetail>(`/reclutamiento/candidatos/${id}/`, data)
  },

  deleteCandidato: (id: string) => {
    return apiClient.delete(`/reclutamiento/candidatos/${id}/`)
  },

  vincularDocumentoCandidato: (candidatoId: string, payload: { archivo_id: string; tipo_documento: string; nombre_descriptivo?: string }) => {
    return apiClient.post(`/reclutamiento/candidatos/${candidatoId}/vincular-documento/`, payload)
  },

  // ── 2. Fuentes de Reclutamiento ──────────────────────────────
  getFuentes: () => {
    return apiClient.get<FuenteReclutamiento[]>('/reclutamiento/fuentes/')
  },

  createFuente: (data: { nombre: string; descripcion?: string }) => {
    return apiClient.post<FuenteReclutamiento>('/reclutamiento/fuentes/', data)
  },

  // ── 3. Vacantes ──────────────────────────────────────────────
  getVacantes: (params?: { estado?: string; modalidad?: string; perfil_cargo_id?: string; sede_id?: string }) => {
    const query = new URLSearchParams()
    if (params?.estado) query.set('estado', params.estado)
    if (params?.modalidad) query.set('modalidad', params.modalidad)
    if (params?.perfil_cargo_id) query.set('perfil_cargo_id', params.perfil_cargo_id)
    if (params?.sede_id) query.set('sede_id', params.sede_id)
    const qs = query.toString() ? `?${query.toString()}` : ''
    return apiClient.get<VacanteListItem[]>(`/reclutamiento/vacantes/${qs}`)
  },

  getVacanteById: (id: string) => {
    return apiClient.get<VacanteDetail>(`/reclutamiento/vacantes/${id}/`)
  },

  createVacante: (data: any) => {
    return apiClient.post<VacanteDetail>('/reclutamiento/vacantes/', data)
  },

  updateVacante: (id: string, data: any) => {
    return apiClient.put<VacanteDetail>(`/reclutamiento/vacantes/${id}/`, data)
  },

  publicarVacante: (id: string) => {
    return apiClient.post<VacanteDetail>(`/reclutamiento/vacantes/${id}/publicar/`, {})
  },

  pausarVacante: (id: string) => {
    return apiClient.post<VacanteDetail>(`/reclutamiento/vacantes/${id}/pausar/`, {})
  },

  cerrarVacante: (id: string) => {
    return apiClient.post<VacanteDetail>(`/reclutamiento/vacantes/${id}/cerrar/`, {})
  },

  // ── 4. Procesos de Selección ─────────────────────────────────
  getProcesoById: (id: string) => {
    return apiClient.get<ProcesoSeleccionDetail>(`/reclutamiento/procesos/${id}/`)
  },

  postularCandidatoAProceso: (procesoId: string, candidatoId: string) => {
    return apiClient.post<PostulacionDetail>(`/reclutamiento/procesos/${procesoId}/postular/`, {
      candidato_id: candidatoId,
    })
  },

  // ── 5. Postulaciones y Máquina de Estados ───────────────────
  getPostulaciones: (params?: { proceso_seleccion_id?: string; estado?: string; candidato_id?: string }) => {
    const query = new URLSearchParams()
    if (params?.proceso_seleccion_id) query.set('proceso_seleccion_id', params.proceso_seleccion_id)
    if (params?.estado) query.set('estado', params.estado)
    if (params?.candidato_id) query.set('candidato_id', params.candidato_id)
    const qs = query.toString() ? `?${query.toString()}` : ''
    return apiClient.get<PostulacionListItem[]>(`/reclutamiento/postulaciones/${qs}`)
  },

  getPostulacionById: (id: string) => {
    return apiClient.get<PostulacionDetail>(`/reclutamiento/postulaciones/${id}/`)
  },

  preseleccionarPostulacion: (
    id: string,
    payload: {
      calificacion_requisitos: Record<string, boolean>
      puntuacion?: number
      es_excepcion?: boolean
      justificacion_excepcion?: string
    }
  ) => {
    return apiClient.post<PostulacionDetail>(`/reclutamiento/postulaciones/${id}/preseleccionar/`, payload)
  },

  registrarEntrevistaPostulacion: (id: string, payload: any) => {
    return apiClient.post<{ entrevista: any; postulacion: PostulacionDetail }>(
      `/reclutamiento/postulaciones/${id}/registrar-entrevista/`,
      payload
    )
  },

  registrarEvaluacionPostulacion: (id: string, payload: any) => {
    return apiClient.post<{ evaluacion: any; postulacion: PostulacionDetail }>(
      `/reclutamiento/postulaciones/${id}/registrar-evaluacion/`,
      payload
    )
  },

  registrarValidacionPostulacion: (id: string, payload: any) => {
    return apiClient.post<{ validacion: any; postulacion: PostulacionDetail }>(
      `/reclutamiento/postulaciones/${id}/registrar-validacion/`,
      payload
    )
  },

  seleccionarPostulacion: (
    id: string,
    payload?: { notas_finales?: string; es_excepcion?: boolean; justificacion_excepcion?: string }
  ) => {
    return apiClient.post<PostulacionDetail>(`/reclutamiento/postulaciones/${id}/seleccionar/`, payload ?? {})
  },

  cerrarPostulacion: (id: string, payload: { nuevo_estado: string; motivo: string; datos_adicionales?: any }) => {
    return apiClient.post<PostulacionDetail>(`/reclutamiento/postulaciones/${id}/cerrar/`, payload)
  },

  reabrirPostulacion: (id: string, payload: { justificacion: string }) => {
    return apiClient.post<PostulacionDetail>(`/reclutamiento/postulaciones/${id}/reabrir/`, payload)
  },

  // ── 6. Portal Público del Candidato ─────────────────────────
  getVacantesPublicas: (params?: { search?: string; modalidad?: string; empresa_id?: string }) => {
    const query = new URLSearchParams()
    if (params?.search) query.set('search', params.search)
    if (params?.modalidad) query.set('modalidad', params.modalidad)
    if (params?.empresa_id) query.set('empresa_id', params.empresa_id)
    const qs = query.toString() ? `?${query.toString()}` : ''
    return apiClient.get<VacantePublicaListItem[]>(`/reclutamiento/portal/vacantes/${qs}`)
  },

  getVacantePublicaDetail: (slugOrId: string) => {
    return apiClient.get<VacantePublicaDetail>(`/reclutamiento/portal/vacantes/${slugOrId}/`)
  },

  postularPublicamente: async (slugOrId: string, payload: FormData | any) => {
    const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'
    if (payload instanceof FormData) {
      const res = await fetch(`${BASE_URL}/reclutamiento/portal/vacantes/${slugOrId}/postular/`, {
        method: 'POST',
        body: payload,
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Ocurrió un error al enviar su postulación.')
      }
      return res.json()
    }
    return apiClient.post<{ detail: string; postulacion_id: string; token_acceso: string; codigo_otp: string; expira_en: string }>(
      `/reclutamiento/portal/vacantes/${slugOrId}/postular/`,
      payload
    )
  },

  postularRapido: async (slugOrId: string) => {
    const token = localStorage.getItem(CANDIDATE_TOKEN_KEY)
    const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'
    const res = await fetch(`${BASE_URL}/reclutamiento/portal/vacantes/${slugOrId}/postular-rapido/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'No se pudo registrar la postulación rápida.')
    }
    return res.json()
  },

  buscarPerfilPrevio: (email?: string, documento?: string) => {
    return apiClient.post<{ encontrado: boolean; datos: any }>(
      '/reclutamiento/portal/auth/buscar-perfil-previo/',
      { email, documento }
    )
  },

  getMiPerfil: async () => {
    const token = localStorage.getItem(CANDIDATE_TOKEN_KEY)
    if (!token) return null
    const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'
    const res = await fetch(`${BASE_URL}/reclutamiento/portal/mi-perfil/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    })
    if (!res.ok) return null
    return res.json()
  },

  solicitarAccesoOTP: (email: string) => {
    return apiClient.post<{ detail: string; codigo_otp?: string; expira_en: string }>(
      '/reclutamiento/portal/auth/solicitar-acceso/',
      { email }
    )
  },

  verificarOTP: async (email: string, codigoOtp: string) => {
    const res = await apiClient.post<{
      token: string
      candidato: { id: string; nombre_completo: string; email: string }
      expira_en: string
    }>('/reclutamiento/portal/auth/verificar-otp/', { email, codigo_otp: codigoOtp })

    if (res.token) {
      localStorage.setItem(CANDIDATE_TOKEN_KEY, res.token)
    }
    return res
  },

  getCandidateToken: () => {
    return localStorage.getItem(CANDIDATE_TOKEN_KEY)
  },

  logoutCandidato: () => {
    localStorage.removeItem(CANDIDATE_TOKEN_KEY)
  },

  getMisPostulaciones: async () => {
    const token = localStorage.getItem(CANDIDATE_TOKEN_KEY)
    const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'
    const res = await fetch(`${BASE_URL}/reclutamiento/portal/mis-postulaciones/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    })
    if (!res.ok) {
      throw new Error('No se pudieron consultar sus postulaciones. Verifique su sesión.')
    }
    return res.json() as Promise<PostulacionCandidatoPublica[]>
  },

  retirarMiPostulacion: async (postulacionId: string, motivo?: string) => {
    const token = localStorage.getItem(CANDIDATE_TOKEN_KEY)
    const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'
    const res = await fetch(`${BASE_URL}/reclutamiento/portal/mis-postulaciones/${postulacionId}/retirar/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ motivo }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Error al retirar la postulación.')
    }
    return res.json()
  },
}
