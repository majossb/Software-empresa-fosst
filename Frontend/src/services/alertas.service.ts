import { apiClient } from './api.client'

export interface ReglaAlerta {
  id: string
  codigo: string
  nombre: string
  modelo_origen: string
  modelo_origen_display: string
  campo_fecha: string
  dias_anticipacion: number
  nivel_criticidad: 'normal' | 'importante' | 'critico'
  nivel_criticidad_display: string
  mensaje_template: string
  roles_destinatarios: string[]
  activa: boolean
}

export const alertasService = {
  getReglas: () => {
    return apiClient.get<ReglaAlerta[] | { results: ReglaAlerta[] }>('/alertas/reglas/')
  },
  createRegla: (data: Partial<ReglaAlerta>) => {
    return apiClient.post<ReglaAlerta>('/alertas/reglas/', data)
  },
  updateRegla: (id: string, data: Partial<ReglaAlerta>) => {
    return apiClient.patch<ReglaAlerta>(`/alertas/reglas/${id}/`, data)
  },
  ejecutarRevision: () => {
    return apiClient.post<{ mensaje: string; alertas_generadas: number }>('/alertas/reglas/ejecutar-revision/', {})
  },
}
