import { apiClient } from './api.client'

export interface ParticipanteCapacitacion {
  id: string
  capacitacion: string
  trabajador: string
  trabajador_nombre?: string
  trabajador_documento?: string
  trabajador_cargo?: string
  asistio: boolean
  certificado_url?: string | null
  soporte?: string | null
  soporte_url?: string | null
  nota_evaluacion?: number | null
  nivel_alcanzado?: number | null
  observaciones?: string
  created_at?: string
}

export interface BrechaResumenCapacitacion {
  id: string
  codigo: string
  clasificacion: string
  clasificacion_display: string
  estado: string
  descripcion: string
  trabajador_nombre?: string | null
}

export interface Capacitacion {
  id: string
  empresa: string
  tema: string
  objetivo?: string
  curso?: string | null
  curso_nombre?: string
  competencia?: string | null
  competencia_nombre?: string
  brechas?: string[]
  brechas_detalle?: BrechaResumenCapacitacion[]
  proveedor?: string | null
  fecha: string
  horas_duracion?: number | null
  num_asistentes: number
  tiene_certificado: boolean
  estado: 'programada' | 'realizada' | 'cancelada'
  participantes?: ParticipanteCapacitacion[]
  total_participantes?: number
  total_asistieron?: number
  created_at: string
}

export interface CapacitacionesResponse {
  capacitaciones: Capacitacion[]
  resumen: { total: number; programadas: number; realizadas: number; canceladas: number }
}

export interface ParticipanteSugerido {
  trabajador_id: string
  nombre: string
  documento: string
  cargo: string
  motivos: string[]
  motivo_principal: string
}

export const capacitacionService = {
  listar: (params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : ''
    return apiClient.get<CapacitacionesResponse>(`/capacitaciones${query}`)
  },

  obtener: (id: string) => apiClient.get<Capacitacion>(`/capacitaciones/${id}`),

  crear: (data: {
    tema: string
    objetivo?: string
    curso?: string | null
    competencia?: string | null
    brechas?: string[]
    proveedor?: string
    fecha: string
    horas_duracion?: number
    num_asistentes?: number
    tiene_certificado?: boolean
    estado?: string
  }) => apiClient.post<Capacitacion>('/capacitaciones', data),

  actualizar: (
    id: string,
    data: Partial<Capacitacion>
  ) => apiClient.put<Capacitacion>(`/capacitaciones/${id}`, data),

  sugerirParticipantes: (params: {
    curso_id?: string
    competencia_id?: string
    brecha_ids?: string
  }) => {
    const query = new URLSearchParams()
    if (params.curso_id) query.append('curso_id', params.curso_id)
    if (params.competencia_id) query.append('competencia_id', params.competencia_id)
    if (params.brecha_ids) query.append('brecha_ids', params.brecha_ids)
    return apiClient.get<ParticipanteSugerido[]>(`/capacitaciones/sugerir-participantes?${query.toString()}`)
  },

  inscribirParticipantes: (capacitacionId: string, trabajadores_ids: string[]) =>
    apiClient.post<Capacitacion>(`/capacitaciones/${capacitacionId}/inscribir-participantes`, {
      trabajadores_ids,
    }),

  registrarAsistencia: (
    capacitacionId: string,
    participantes: Array<{
      trabajador_id: string
      asistio: boolean
      certificado_url?: string
      soporte_id?: string
      nota_evaluacion?: number | null
      nivel_alcanzado?: number | null
      observaciones?: string
    }>
  ) =>
    apiClient.post<Capacitacion>(`/capacitaciones/${capacitacionId}/registrar-asistencia`, {
      participantes,
    }),

  finalizar: (capacitacionId: string) =>
    apiClient.post<Capacitacion>(`/capacitaciones/${capacitacionId}/finalizar`, {}),
}
