import { apiClient } from './api.client'
import type { EstandarMinimo } from '@/types'

interface EstandaresConRespuestasResponse {
  evaluacion_id: string
  capitulo: string
  estandares: EstandarMinimo[]
}

export interface RespuestaHistoricaItem {
  respuesta_id: string
  estandar_id: string
  codigo: string
  nombre: string
  ciclo_phva: string
  puntaje_maximo: number
  estado: string
  puntaje: number
  observacion: string
  capitulo_estandar: string
  es_capitulo_vigente: boolean
  updated_at: string | null
}

export interface RespuestasHistoricasResponse {
  success: boolean
  evaluacion_id: string | null
  capitulo_vigente: string
  respuestas: RespuestaHistoricaItem[]
  total: number
}

export interface ApelacionItem {
  id: string
  respuesta: string
  solicitante: string
  solicitante_nombre?: string
  solicitante_email?: string
  motivo: string
  respuesta_auditor?: string | null
  estado: 'pendiente' | 'resuelta' | 'aceptada' | 'rechazada'
  codigo_estandar?: string
  nombre_estandar?: string
  observacion_original?: string
  created_at: string
  updated_at: string
}

export const estandarService = {
  listar: () => apiClient.get<any[]>('/estandares'),

  conRespuestas: () => apiClient.get<EstandaresConRespuestasResponse>('/estandares/respuestas'),

  actualizarRespuesta: (estandarId: string, data: {
    estado: string; observacion?: string; puntaje?: number
  }) => apiClient.put<any>(`/estandares/respuesta/${estandarId}`, data),

  getRespuestasHistoricas: () =>
    apiClient.get<RespuestasHistoricasResponse>('/evaluaciones/actual/respuestas-historicas'),

  getHistorial: () =>
    apiClient.get<any[]>('/evaluaciones/historial'),

  // ── RF-SST-03 / SST-04: Apelaciones ───────────────────────────────
  crearApelacion: (respuestaId: string, motivo: string) =>
    apiClient.post<{ success: boolean; message: string; data: ApelacionItem }>('/apelaciones/', {
      respuesta: respuestaId,
      motivo,
    }),

  listarApelaciones: () =>
    apiClient.get<ApelacionItem[] | { results: ApelacionItem[] }>('/apelaciones/'),

  resolverApelacion: (apelacionId: string, decision: 'aceptada' | 'rechazada' | 'resuelta', respuestaAuditor?: string) =>
    apiClient.post<{ success: boolean; message: string; data: ApelacionItem }>(`/apelaciones/${apelacionId}/resolver/`, {
      decision,
      respuesta_auditor: respuestaAuditor,
    }),
}


