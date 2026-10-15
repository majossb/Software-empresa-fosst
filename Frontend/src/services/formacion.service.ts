import { apiClient } from './api.client'

export interface CompetenciaMatriz {
  competencia_id: string
  nombre: string
  tipo: string
  nivel_requerido: number
  nivel_alcanzado: number
  brecha: number
  cumple: boolean
  ultima_evaluacion: any
}

export interface MatrizTrabajadorResponse {
  trabajador: {
    id: string
    nombre: string
    documento: string
    cargo: string
  }
  competencias: CompetenciaMatriz[]
}

export interface EvaluacionCompetencia {
  id: string
  trabajador: string
  trabajador_nombre: string
  cargo_competencia: string
  competencia_nombre: string
  competencia_tipo: string
  nivel_requerido: number
  nivel_alcanzado: number
  brecha_calculada: number
  fecha_evaluacion: string
  metodo: string
  metodo_display: string
  observacion?: string
}

export interface FormacionResumen {
  total_evaluaciones: number
  evaluaciones_con_brecha: number
  evaluaciones_optimas: number
  promedio_brecha: number
}

export const formacionService = {
  getEvaluaciones: () => {
    return apiClient.get<EvaluacionCompetencia[] | { results: EvaluacionCompetencia[] }>('/formacion/evaluaciones/')
  },
  createEvaluacion: (data: Partial<EvaluacionCompetencia>) => {
    return apiClient.post<EvaluacionCompetencia>('/formacion/evaluaciones/', data)
  },
  getMatrizTrabajador: (trabajadorId: string) => {
    return apiClient.get<MatrizTrabajadorResponse>(`/formacion/evaluaciones/matriz-trabajador/${trabajadorId}/`)
  },
  getResumen: () => {
    return apiClient.get<FormacionResumen>('/formacion/evaluaciones/resumen/')
  },
}
