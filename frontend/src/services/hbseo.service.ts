import { apiClient } from './api.client'

export interface BrechaOrigen {
  id: string
  modulo_origen: string
  modulo_origen_display: string
  es_origen_principal: boolean
  descripcion: string
  created_at: string
}

export interface BrechaEvento {
  id: string
  tipo_evento: string
  tipo_evento_display: string
  descripcion: string
  usuario_nombre: string | null
  created_at: string
}

export interface BrechaAccion {
  id: string
  descripcion: string
  fecha_programada: string
  fecha_ejecucion: string | null
  estado: 'pendiente' | 'en_proceso' | 'completada' | 'cancelada'
  responsable_nombre: string | null
  created_at: string
}

export interface Brecha {
  id: string
  codigo: string
  clasificacion: 'incumplimiento' | 'incompatibilidad' | 'oportunidad_mejora' | 'riesgo_no_mitigado' | 'vencimiento' | 'hallazgo_auditoria' | 'otro'
  clasificacion_display: string
  estado: 'abierta' | 'en_analisis' | 'plan_accion' | 'subsanada' | 'cerrada_aceptada'
  estado_display: string
  nivel_atencion: 'bajo' | 'medio' | 'alto' | 'critico'
  nivel_atencion_display: string
  descripcion_automatica: string
  descripcion_complementaria: string
  recomendacion_ia: string
  trabajador: string | null
  trabajador_nombre: string | null
  detectado_por: string
  fecha_deteccion: string
  origenes?: BrechaOrigen[]
  eventos?: BrechaEvento[]
  acciones?: BrechaAccion[]
}

export interface BrechaResumen {
  total: number
  por_estado: Record<string, number>
  por_clasificacion: Record<string, number>
  por_nivel_atencion: Record<string, number>
}

export const hbseoService = {
  getBrechas: (params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : ''
    return apiClient.get<Brecha[] | { results: Brecha[] }>(`/hbseo/brechas/${query}`)
  },
  getBrechaById: (id: string) => {
    return apiClient.get<Brecha>(`/hbseo/brechas/${id}/`)
  },
  updateBrecha: (id: string, data: Partial<Brecha>) => {
    return apiClient.patch<Brecha>(`/hbseo/brechas/${id}/`, data)
  },
  getResumen: () => {
    return apiClient.get<BrechaResumen>('/hbseo/brechas/resumen/')
  },
  getAcciones: (brechaId: string) => {
    return apiClient.get<BrechaAccion[]>(`/hbseo/brechas/${brechaId}/acciones/`)
  },
  createAccion: (brechaId: string, data: { descripcion: string; fecha_programada: string; responsable_id?: string }) => {
    return apiClient.post<BrechaAccion>(`/hbseo/brechas/${brechaId}/acciones/`, data)
  },
}
