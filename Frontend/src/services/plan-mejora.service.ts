import { apiClient } from './api.client'
import type { PlanMejora, PlanMejoraResumen, PrioridadPlan, EstadoPlan } from '@/types'

interface PlanMejoraResponse {
  planes: PlanMejora[]
  resumen: PlanMejoraResumen
}

export const planMejoraService = {
  listar: () => apiClient.get<PlanMejoraResponse>('/plan-mejora'),

  resumen: () => apiClient.get<any>('/plan-mejora/resumen'),

  crear: (data: {
    accion: string; responsable: string
    prioridad: PrioridadPlan; evaluacion_id?: string
  }) => apiClient.post<PlanMejora>('/plan-mejora', data),

  actualizar: (id: string, data: {
    accion?: string; responsable?: string
    prioridad?: PrioridadPlan; estado?: EstadoPlan
  }) => apiClient.put<PlanMejora>(`/plan-mejora/${id}`, data),
}
