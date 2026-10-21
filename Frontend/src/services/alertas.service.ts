import { apiClient } from './api.client'

export interface ReglaAlerta {
  id: string
  codigo: string
  nombre: string
  modelo_origen: string
  modelo_origen_display: string
  campo_fecha: string
  tipo_handler?: 'exacta' | 'vencido_rango' | 'sin_registrar' | 'evaluacion_pendiente'
  dias_anticipacion: number
  nivel_criticidad: 'normal' | 'importante' | 'critico'
  nivel_criticidad_display: string
  mensaje_template: string
  roles_destinatarios: string[]
  activa: boolean
}

export interface Notificacion {
  id: string
  empresa: string
  usuario?: string
  tipo: string
  tipo_display: string
  nivel: 'normal' | 'importante' | 'critico'
  nivel_display: string
  mensaje: string
  leida: boolean
  enviado_email: boolean
  metadatos?: {
    tipo_alerta?: string
    curso_id?: string
    trabajador_id?: string
    cargo?: string
    registro_id?: string
    cargo_competencia_id?: string
    resuelta?: boolean
  } | null
  accion_url?: string | null
  created_at: string
}

export interface NotificacionResumen {
  total: number
  no_leidas: number
  por_nivel: {
    critico: number
    importante: number
    normal: number
  }
}

export interface FiltrosNotificaciones {
  leida?: boolean
  nivel?: string
  tipo_alerta?: string
  trabajador_id?: string
  cargo?: string
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
  getNotificaciones: (params?: FiltrosNotificaciones) => {
    const query = new URLSearchParams()
    if (params) {
      if (params.leida !== undefined) query.append('leida', String(params.leida))
      if (params.nivel) query.append('nivel', params.nivel)
      if (params.tipo_alerta) query.append('tipo_alerta', params.tipo_alerta)
      if (params.trabajador_id) query.append('trabajador_id', params.trabajador_id)
      if (params.cargo) query.append('cargo', params.cargo)
    }
    const qs = query.toString()
    return apiClient.get<{ results: Notificacion[]; count?: number } | Notificacion[]>(
      `/alertas/notificaciones/${qs ? `?${qs}` : ''}`
    )
  },
  marcarLeida: (id: string) => {
    return apiClient.post<Notificacion>(`/alertas/notificaciones/${id}/marcar-leida/`, {})
  },
  marcarResuelta: (id: string) => {
    return apiClient.post<Notificacion>(`/alertas/notificaciones/${id}/marcar-resuelta/`, {})
  },
  getResumen: () => {
    return apiClient.get<NotificacionResumen>('/alertas/notificaciones/resumen/')
  },
}
