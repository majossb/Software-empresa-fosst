import { apiClient } from './api.client'

export interface DetalleRequisito {
  id: string
  tipo_requisito: string
  tipo_requisito_display: string
  requisito_descripcion: string
  cumple: 'si' | 'no' | 'parcial' | 'no_aplica'
  cumple_display: string
  observacion: string
}

export interface EvaluacionHabilitacion {
  id: string
  trabajador: string
  trabajador_nombre: string
  trabajador_documento: string
  perfil_cargo: string | null
  cargo_nombre: string | null
  sede_nombre: string | null
  porcentaje_cumplimiento: string | number
  semaforo: 'verde' | 'amarillo' | 'rojo'
  semaforo_display: string
  estado_habilitacion: 'habilitado' | 'restringido' | 'pendiente_documental' | 'no_apto'
  estado_habilitacion_display: string
  compatibilidad: 'compatible' | 'compatible_con_restricciones' | 'incompatible_temporal'
  compatibilidad_display: string
  nivel_atencion: 'bajo' | 'medio' | 'alto' | 'critico'
  nivel_atencion_display: string
  interpretacion_ia?: string
  recomendacion_ia?: string
  detalles_requisitos?: DetalleRequisito[]
  calculado_at: string
}

export interface MichcResumen {
  total_evaluaciones: number
  promedio_cumplimiento: number
  por_semaforo: {
    verde: number
    amarillo: number
    rojo: number
  }
  por_estado_habilitacion: Record<string, number>
  por_compatibilidad: Record<string, number>
}

export const michcService = {
  getMatriz: (params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : ''
    return apiClient.get<EvaluacionHabilitacion[] | { results: EvaluacionHabilitacion[] }>(`/michc/matriz/${query}`)
  },
  getEvaluacionById: (id: string) => {
    return apiClient.get<EvaluacionHabilitacion>(`/michc/matriz/${id}/`)
  },
  recalcular: (id: string) => {
    return apiClient.post<EvaluacionHabilitacion>(`/michc/matriz/${id}/recalcular/`, {})
  },
  getResumen: () => {
    return apiClient.get<MichcResumen>('/michc/matriz/resumen/')
  },
}
