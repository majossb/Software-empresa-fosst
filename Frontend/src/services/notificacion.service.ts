import { apiClient } from './api.client'

export interface NotificacionItem {
  id: string
  empresa: string
  usuario?: string | null
  actividad?: string | null
  tipo: 'alerta' | 'recordatorio' | 'informativa'
  nivel: 'normal' | 'importante' | 'critico'
  mensaje: string
  leida: boolean
  enviado_email: boolean
  created_at: string
}

export const notificacionService = {
  listar: () => apiClient.get<NotificacionItem[] | { results: NotificacionItem[] }>('/notificaciones'),
  marcarLeida: (id: string) => apiClient.post<NotificacionItem>(`/notificaciones/${id}/marcar_leida`, {}),
}
