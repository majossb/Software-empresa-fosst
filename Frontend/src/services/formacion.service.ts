import { apiClient } from './api.client'

export interface CompetenciaMatriz {
  competencia_id: string
  nombre: string
  tipo: string
  tipo_display?: string
  descripcion?: string
  nivel_requerido: number
  nivel_requerido_nombre?: string
  nivel_alcanzado: number
  nivel_alcanzado_nombre?: string
  brecha: number
  cumple: boolean
  solo_autoevaluado?: boolean
  ultima_evaluacion: any
}

export interface MatrizTrabajadorResponse {
  trabajador: {
    id: string
    nombre: string
    documento: string
    cargo: string
    perfil_cargo_id?: string
  }
  competencias: CompetenciaMatriz[]
}

export interface EvaluacionCompetencia {
  id: string
  trabajador: string
  trabajador_nombre: string
  trabajador_documento?: string
  cargo_competencia: string
  competencia_nombre: string
  competencia_tipo: string
  competencia_descripcion?: string
  nivel_requerido: number
  nivel_requerido_nombre?: string
  nivel_alcanzado: number
  nivel_alcanzado_nombre?: string
  brecha_calculada: number
  fecha_evaluacion: string
  metodo: string
  metodo_display: string
  rol_evaluador?: string
  rol_evaluador_display?: string
  evaluado_por?: string
  evaluado_por_nombre?: string
  observacion?: string
  soporte_archivo?: string
  created_at?: string
  updated_at?: string
}

export interface FormacionResumen {
  total_evaluaciones: number
  evaluaciones_con_brecha: number
  evaluaciones_optimas: number
  promedio_brecha: number
}

// ── Fase 2: Cursos y Certificaciones ───────────────────────────────────

export interface CursoFormacion {
  id: string
  empresa?: string
  nombre: string
  categoria: 'sst' | 'vial' | 'tecnica' | 'brigada' | 'otra' | string
  categoria_display?: string
  vigencia_meses?: number | null
  requiere_certificado: boolean
  descripcion?: string
  activo: boolean
}

export interface CargoRequisitoFormacion {
  id?: string
  perfil_cargo?: string
  curso?: string
  curso_id?: string
  curso_nombre?: string
  curso_categoria?: string
  curso_categoria_display?: string
  curso_requiere_certificado?: boolean
  obligatorio: boolean
  vigencia_meses?: number | null
  grupo_alternativo?: string | null
}

export interface RegistroFormacion {
  id?: string
  trabajador: string
  trabajador_nombre?: string
  trabajador_documento?: string
  trabajador_cargo?: string
  curso: string
  curso_nombre?: string
  curso_categoria?: string
  curso_categoria_display?: string
  fecha_realizacion: string
  fecha_vencimiento?: string | null
  soporte?: string | null
  soporte_nombre?: string | null
  soporte_url?: string | null
  origen: 'capacitacion_interna' | 'proveedor_externo' | 'carga_manual' | string
  origen_display?: string
  entidad_emisora?: string
  horas_duracion?: number | null
  observaciones?: string
  estado_derivado?: 'vigente' | 'por_vencer' | 'vencido' | string
  dias_para_vencer?: number | null
}

export interface MatrizFormacionItem {
  curso_id: string
  curso_nombre: string
  categoria: string
  categoria_display: string
  requiere_certificado: boolean
  obligatorio: boolean
  vigencia_meses: number | null
  grupo_alternativo: string | null
  estado: 'vigente' | 'por_vencer' | 'vencido' | 'falta' | 'cumple_alternativa' | string
  cumple: boolean
  alternativa_satisfecha?: boolean
  alternativa_cubierta_por?: string | null
  ultimo_registro?: {
    id: string
    fecha_realizacion: string | null
    fecha_vencimiento: string | null
    estado_derivado: string
    dias_para_vencer: number | null
    origen: string
    origen_display: string
    entidad_emisora?: string
    horas_duracion?: number | null
    soporte?: { id: string; nombre: string; url: string } | null
  } | null
}

export interface MatrizFormacionResponse {
  trabajador: {
    id: string
    nombre: string
    documento: string
    cargo: string
    perfil_cargo_id?: string
  }
  cursos: MatrizFormacionItem[]
  resumen: {
    total_exigidos: number
    cumplidos: number
    por_vencer: number
    vencidos: number
    faltantes: number
    porcentaje_cumplimiento: number
  }
}

export interface FormacionCursosResumen {
  total_registros: number
  vigentes: number
  por_vencer: number
  vencidos: number
}

export const formacionService = {
  // Evaluaciones de competencias (Fase 1)
  getEvaluaciones: () => {
    return apiClient.get<EvaluacionCompetencia[] | { results: EvaluacionCompetencia[] }>('/formacion/evaluaciones/')
  },
  createEvaluacion: (data: Partial<EvaluacionCompetencia>) => {
    return apiClient.post<EvaluacionCompetencia>('/formacion/evaluaciones/', data)
  },
  getMatrizTrabajador: (trabajadorId: string) => {
    return apiClient.get<MatrizTrabajadorResponse>(`/formacion/evaluaciones/matriz-trabajador/${trabajadorId}/`)
  },
  getResumen: () => {
    return apiClient.get<FormacionResumen>('/formacion/evaluaciones/resumen/')
  },

  // Cursos del catálogo y requisitos (Fase 2)
  getCursos: (params?: { categoria?: string; search?: string }) => {
    const query = new URLSearchParams()
    if (params?.categoria) query.append('categoria', params.categoria)
    if (params?.search) query.append('search', params.search)
    const qs = query.toString()
    return apiClient.get<CursoFormacion[] | { results: CursoFormacion[] }>(`/formacion/cursos/${qs ? `?${qs}` : ''}`)
  },
  createCurso: (data: Partial<CursoFormacion>) => {
    return apiClient.post<CursoFormacion>('/formacion/cursos/', data)
  },
  getRequisitosCargo: (perfilCargoId: string) => {
    return apiClient.get<CargoRequisitoFormacion[] | { results: CargoRequisitoFormacion[] }>(
      `/formacion/requisitos-cargo/?perfil_cargo=${encodeURIComponent(perfilCargoId)}`
    )
  },

  // Registros de formación por trabajador (Fase 2)
  getRegistros: (params?: { trabajador?: string; curso?: string; cargo?: string; estado?: string }) => {
    const query = new URLSearchParams()
    if (params?.trabajador) query.append('trabajador', params.trabajador)
    if (params?.curso) query.append('curso', params.curso)
    if (params?.cargo) query.append('cargo', params.cargo)
    if (params?.estado) query.append('estado', params.estado)
    const qs = query.toString()
    return apiClient.get<RegistroFormacion[] | { results: RegistroFormacion[] }>(`/formacion/registros/${qs ? `?${qs}` : ''}`)
  },
  createRegistro: (data: Partial<RegistroFormacion>) => {
    return apiClient.post<RegistroFormacion>('/formacion/registros/', data)
  },
  getMatrizFormacionTrabajador: (trabajadorId: string) => {
    return apiClient.get<MatrizFormacionResponse>(`/formacion/registros/matriz-trabajador/${trabajadorId}/`)
  },
  getResumenFormacionCursos: () => {
    return apiClient.get<FormacionCursosResumen>('/formacion/registros/resumen/')
  },
}
