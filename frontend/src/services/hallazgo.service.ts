import { apiClient } from './api.client'
import type { Hallazgo, TipoHallazgo } from '@/types'

interface HallazgosResponse {
  hallazgos: Hallazgo[]
  total: number
  evaluacion_id: string
}

export const hallazgoService = {
  listar: () => apiClient.get<HallazgosResponse>('/hallazgos'),

  crear: (data: {
    evaluacion_id?: string
    evaluacion?: string
    descripcion: string
    tipo: TipoHallazgo
    estandar_id?: string
    estandar_codigo?: string
    estandar?: string
  }) => apiClient.post<Hallazgo>('/hallazgos', data),

  actualizar: (id: string, data: {
    descripcion?: string; tipo?: TipoHallazgo
  }) => apiClient.put<Hallazgo>(`/hallazgos/${id}`, data),

  eliminar: (id: string) => apiClient.delete<any>(`/hallazgos/${id}`),
}
