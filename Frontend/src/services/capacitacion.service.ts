import { apiClient } from './api.client'
import type { Capacitacion } from '@/types'

interface CapacitacionesResponse {
  capacitaciones: Capacitacion[]
  resumen: { total: number; programadas: number; realizadas: number; canceladas: number }
}

export const capacitacionService = {
  listar: () => apiClient.get<CapacitacionesResponse>('/capacitaciones'),

  crear: (data: {
    tema: string; proveedor?: string; fecha: string; num_asistentes?: number
  }) => apiClient.post<Capacitacion>('/capacitaciones', data),

  actualizar: (id: string, data: {
    tema?: string; proveedor?: string; fecha?: string
    num_asistentes?: number; estado?: string; tiene_certificado?: boolean
  }) => apiClient.put<Capacitacion>(`/capacitaciones/${id}`, data),
}
