import { apiClient } from './api.client'

// ── Tipos ──────────────────────────────────────────────────────────
export interface EmpresaContexto {
  id: string
  nombre: string
  nit: string
  ciiu_codigo: string | null
  ciiu_descripcion: string | null
  ciiu_768_principal: string | null
  ciiu_768_secundarios: string[] | null
  ciiu_768_metadata: any | null
  representante_legal: string | null
  arl: string | null
  sector_economico: string | null
  ciudad: string | null
  num_trabajadores: number
  nivel_riesgo: number
  logo_url: string | null
  mision: string | null
  vision: string | null
  valores: string[] | null
  _count: { sedes: number; procesos: number; organigrama: number }
}

export interface Sede {
  id: string
  nombre: string
  ciudad: string
  direccion: string | null
  telefono: string | null
  responsable: string | null
  es_principal: boolean
  activa: boolean
  _count?: { trabajadores: number }
}

export interface NodoOrganigrama {
  id: string
  nombre_cargo: string
  area: string | null
  nivel: number
  padre_id: string | null
  orden: number
  activo: boolean
}

export interface Proceso {
  id: string
  nombre: string
  tipo: 'estrategico' | 'misional' | 'apoyo'
  descripcion: string | null
  padre_id: string | null
  activo: boolean
  subprocesos?: Proceso[]
}

export interface Completitud {
  porcentaje: number
  hitos: { nombre: string; completado: boolean }[]
  campos_faltantes: string[]
}

export interface ProcesoSugerido {
  nombre: string
  tipo: 'estrategico' | 'misional' | 'apoyo'
  descripcion: string
}

export interface IdentidadSugerida {
  mision: string
  vision: string
  valores: string[]
}

export interface CiiuEntry {
  codigo_768: string
  clase_riesgo: number
  ciiu_rev4: string
  descripcion: string
  sector: string
  division: string
  grupo: string
}

export interface CiiuActividadSugerida extends CiiuEntry {
  justificacion: string
}

export interface CiiuSugerenciaResponse {
  resultado: {
    actividad_principal: CiiuActividadSugerida
    actividades_secundarias: CiiuActividadSugerida[]
  }
  fuente: string
  candidatos_evaluados: CiiuEntry[]
  falta_contexto?: boolean
}

export interface CiiuActividadDescripcion extends CiiuEntry {
  descripcion_contextualizada: string
}

export interface CiiuDescripcionResponse {
  resultado: {
    actividad_principal: CiiuActividadDescripcion
    actividades_secundarias: CiiuActividadDescripcion[]
  }
  fuente: string
}

// ── RF-USR-03: Transición de Capítulo ─────────────────────────────
export interface TransicionCapituloPayload {
  /** Nuevo número de trabajadores que origina el cambio */
  num_trabajadores: number
  /** Nuevo nivel de riesgo que origina el cambio */
  nivel_riesgo: number
  /** Motivo libre del responsable SST (opcional) */
  motivo?: string
}

export interface TransicionCapituloResult {
  id: string
  capitulo_anterior: string
  capitulo_nuevo: string
  created_at: string
  evaluacion_id: string
}

export interface TransicionCapituloResponse {
  success: boolean
  message: string
  empresa: EmpresaContexto
  transicion: TransicionCapituloResult
}

export interface HistorialTransicionItem {
  id: string
  capitulo_anterior: string
  capitulo_nuevo: string
  motivo: string
  usuario_nombre: string
  created_at: string
  contexto_anterior: { num_trabajadores: number; nivel_riesgo: number }
  contexto_nuevo: { num_trabajadores: number; nivel_riesgo: number }
}

export const modulo0Service = {
  // Contexto
  getContexto: () => apiClient.get<EmpresaContexto>('/modulo0/contexto'),
  updateContexto: (data: Partial<EmpresaContexto>) => apiClient.put<EmpresaContexto>('/modulo0/contexto', data),
  uploadLogo: (file: File) => {
    const form = new FormData()
    form.append('logo', file)
    return apiClient.post<{ logo_url: string }>('/modulo0/contexto/logo', form)
  },
  getCompletitud: () => apiClient.get<Completitud>('/modulo0/completitud'),

  // Sedes
  listSedes: () => apiClient.get<Sede[]>('/modulo0/sedes'),
  createSede: (data: Omit<Sede, 'id' | 'activa' | '_count'>) => apiClient.post<Sede>('/modulo0/sedes', data),
  updateSede: (id: string, data: Partial<Sede>) => apiClient.put<Sede>(`/modulo0/sedes/${id}`, data),
  deleteSede: (id: string) => apiClient.delete<void>(`/modulo0/sedes/${id}`),

  // Organigrama
  getOrganigrama: () => apiClient.get<NodoOrganigrama[]>('/modulo0/organigrama'),
  createNodo: (data: { nombre_cargo: string; area?: string | null; padre_id?: string | null; orden?: number }) =>
    apiClient.post<NodoOrganigrama>('/modulo0/organigrama', data),
  updateNodo: (id: string, data: Partial<NodoOrganigrama>) =>
    apiClient.put<NodoOrganigrama>(`/modulo0/organigrama/${id}`, data),
  deleteNodo: (id: string) => apiClient.delete<void>(`/modulo0/organigrama/${id}`),

  // Procesos
  listProcesos: () => apiClient.get<{ estrategico: Proceso[]; misional: Proceso[]; apoyo: Proceso[] }>('/modulo0/procesos'),
  createProceso: (data: { nombre: string; tipo: string; descripcion?: string | null; padre_id?: string | null }) =>
    apiClient.post<Proceso>('/modulo0/procesos', data),
  updateProceso: (id: string, data: Partial<Proceso>) => apiClient.put<Proceso>(`/modulo0/procesos/${id}`, data),
  deleteProceso: (id: string) => apiClient.delete<void>(`/modulo0/procesos/${id}`),
  sugerirProcesosIA: () => apiClient.post<{ procesos: ProcesoSugerido[]; fuente: string }>('/modulo0/procesos/sugerir-ia', {}),

  // Identidad
  updateIdentidad: (data: { mision?: string | null; vision?: string | null; valores?: string[] | null }) =>
    apiClient.put<EmpresaContexto>('/modulo0/identidad', data),
  sugerirIdentidadIA: () => apiClient.post<{ identidad: IdentidadSugerida; fuente: string }>('/modulo0/identidad/sugerir-ia', {}),

  // CIIU 768
  sugerirCiiuIA: (descripcionActividad?: string, sector?: string, claseRiesgo?: number) =>
    apiClient.post<CiiuSugerenciaResponse>('/modulo0/contexto/ciiu/sugerir', { descripcion_actividad: descripcionActividad, sector, clase_riesgo: claseRiesgo }),
  describirCiiuIA: (codigoPrincipal: string, codigosSecundarios?: string[]) =>
    apiClient.post<CiiuDescripcionResponse>('/modulo0/contexto/ciiu/describir', {
      codigo_principal: codigoPrincipal,
      codigos_secundarios: codigosSecundarios,
    }),

  // ── RF-USR-03: Transición de Capítulo ──────────────────────────
  /**
   * Confirma atómicamente una transición de capítulo.
   * Solo debe llamarse tras mostrar el modal de confirmación al usuario.
   */
  confirmarTransicionCapitulo: (payload: TransicionCapituloPayload) =>
    apiClient.post<TransicionCapituloResponse>('/modulo0/transicion-capitulo', payload),

  /** Consulta el historial inmutable de transiciones de capítulo. */
  getHistorialTransiciones: () =>
    apiClient.get<HistorialTransicionItem[]>('/modulo0/historial-transiciones'),
}
