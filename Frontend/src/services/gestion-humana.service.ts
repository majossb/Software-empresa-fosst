import { apiClient } from './api.client'

export interface Trabajador {
  id: string
  nombre: string
  documento: string
  cargo: string
  tipo_vinculacion: string
  tipo_contrato: string
  fecha_ingreso: string
  fecha_fin_contrato: string | null
  estado_contractual: string
  estado_operativo: string
  remuneracion_monto: string | null
  remuneracion_tipo: string
  activo: boolean
}

export interface NovedadLaboral {
  id: string
  trabajador: string
  trabajador_nombre?: string
  tipo: 'vacaciones' | 'licencia' | 'incapacidad' | 'suspension' | 'periodo_prueba' | 'reintegro'
  tipo_display?: string
  fecha_inicio: string
  fecha_fin: string | null
  dias: number | null
  observaciones: string
  created_at?: string
}

export interface ExamenMedico {
  id: string
  trabajador: string
  trabajador_nombre?: string
  tipo: 'ingreso' | 'periodico' | 'egreso' | 'post_incapacidad' | 'cambio_cargo'
  tipo_display?: string
  fecha_examen: string
  fecha_vencimiento: string | null
  concepto_aptitud: 'apto' | 'apto_con_restricciones' | 'no_apto' | 'aplazado'
  concepto_aptitud_display?: string
  presenta_restricciones: boolean
  descripcion_restricciones: string
  medico_evaluador?: string
}

export interface LicenciaConduccion {
  id: string
  trabajador: string
  trabajador_nombre?: string
  categoria: string
  fecha_expedicion: string | null
  fecha_vencimiento: string
  presenta_restricciones: boolean
  descripcion_restricciones: string
}

export interface ExpedienteConsolidado {
  trabajador: Trabajador
  novedades: NovedadLaboral[]
  examenes_medicos: ExamenMedico[]
  licencias_conduccion: LicenciaConduccion[]
}

export interface ImportarMasivoResponse {
  success: boolean
  creadas: number
  errores_count: number
  errores: Array<{ fila: number; identificacion?: string; nombre?: string; motivo: string }>
  mensaje: string
}

export const gestionHumanaService = {
  getTrabajadores: () => {
    return apiClient.get<Trabajador[] | { results: Trabajador[] }>('/trabajadores')
  },
  getExpediente: (trabajadorId: string) => {
    return apiClient.get<ExpedienteConsolidado>(`/gestion-humana/expediente/${trabajadorId}/`)
  },
  getNovedades: () => {
    return apiClient.get<NovedadLaboral[] | { results: NovedadLaboral[] }>('/gestion-humana/novedades/')
  },
  createNovedad: (data: Partial<NovedadLaboral>) => {
    return apiClient.post<NovedadLaboral>('/gestion-humana/novedades/', data)
  },
  getExamenes: () => {
    return apiClient.get<ExamenMedico[] | { results: ExamenMedico[] }>('/gestion-humana/examenes-medicos/')
  },
  createExamen: (data: Partial<ExamenMedico>) => {
    return apiClient.post<ExamenMedico>('/gestion-humana/examenes-medicos/', data)
  },
  getLicencias: () => {
    return apiClient.get<LicenciaConduccion[] | { results: LicenciaConduccion[] }>('/gestion-humana/licencias/')
  },
  createLicencia: (data: Partial<LicenciaConduccion>) => {
    return apiClient.post<LicenciaConduccion>('/gestion-humana/licencias/', data)
  },
  importarMasivo: (file: File) => {
    const formData = new FormData()
    formData.append('archivo', file)
    return apiClient.post<ImportarMasivoResponse>('/gestion-humana/importar-masivo/', formData)
  },
}

