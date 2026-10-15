import { apiClient } from './api.client'
import type { Evidencia } from '@/types'

interface EvidenciasResponse {
  evidencias: Evidencia[]
  total: number
  evaluacion_id: string
}

export const evidenciaService = {
  listar: () => apiClient.get<EvidenciasResponse>('/evidencias'),

  crear: (data: FormData) => apiClient.post<any>('/evidencias', data),

  eliminar: (id: string) => apiClient.delete<any>(`/evidencias/${id}`),
}
