import { apiClient } from './api.client'

// ── Tipos del Modelo ────────────────────────────────────────────────
export interface CargoFuncion {
  id?: string
  descripcion: string
  orden?: number
}

export interface CargoResponsabilidad {
  id?: string
  descripcion: string
  orden?: number
}

export interface CargoCompetencia {
  id?: string
  nombre: string
  nivel?: string
}

export interface CargoIndicador {
  id?: string
  descripcion: string
  meta?: string
}

export interface CatalogoPeligro {
  id: string
  tipo: string
  clasificacion: string
  descripcion?: string
  epps_sugeridos?: CatalogoEPP[]
}

export interface CatalogoEPP {
  id: string
  nombre: string
  descripcion?: string
}

export interface CargoPeligro {
  id?: string
  catalogo_peligro_id?: string
  tipo_personalizado?: string
  clasificacion_personalizada?: string
  catalogo_peligro?: CatalogoPeligro
}

export interface CargoEPP {
  id?: string
  catalogo_epp_id?: string
  nombre_personalizado?: string
  catalogo_epp?: CatalogoEPP
}

export interface CargoVersion {
  id: string
  numero_version: number
  motivo_cambio?: string
  creado_por?: string
  created_at: string
  cambios: string[]
}

export interface PerfilCargoListItem {
  id: string
  codigo: string
  nombre_cargo: string
  area: string | null
  version_actual: number
  sede: string | null
  sede_id: string | null
  trabajadores_vinculados: number
}

export interface PerfilCargoDetail {
  id: string
  codigo: string
  nombre_cargo: string
  area: string | null
  sede_id: string | null
  nodo_organigrama_id: string | null
  proceso_id: string | null
  nivel_riesgo: number | null
  proposito: string | null
  educacion: string | null
  experiencia: string | null
  formacion: string | null
  habilidades: string | null
  version_actual: number
  activo: boolean
  created_at: string
  updated_at: string
  funciones: CargoFuncion[]
  responsabilidades: CargoResponsabilidad[]
  competencias: CargoCompetencia[]
  indicadores: CargoIndicador[]
  peligros: CargoPeligro[]
  epps: CargoEPP[]
  criticidad_sst?: string | null
  criticidad_operacional?: string | null
  criticidad_vial?: string | null
  criticidad_ambiental?: string | null
  criticidad_estrategica?: string | null
  requiere_suplencia?: boolean
  impacto_descripcion?: string | null
  naturaleza_descripcion?: string | null
  sede?: { id: string; nombre: string } | null
}

// ── Objeto del Servicio ──────────────────────────────────────────────
export const modulo1Service = {
  // CRUD Perfiles
  listPerfiles: (filters?: { area?: string; sede_id?: string }) => {
    const query = new URLSearchParams()
    if (filters?.area) query.append('area', filters.area)
    if (filters?.sede_id) query.append('sede_id', filters.sede_id)
    const queryString = query.toString()
    return apiClient.get<PerfilCargoListItem[]>(`/modulo1/perfil-cargo${queryString ? `?${queryString}` : ''}`)
  },

  getPerfil: (id: string) => apiClient.get<PerfilCargoDetail>(`/modulo1/perfil-cargo/${id}`),

  createPerfil: (data: Partial<PerfilCargoDetail> & { motivo_cambio?: string }) =>
    apiClient.post<PerfilCargoDetail>('/modulo1/perfil-cargo', data),

  updatePerfil: (id: string, data: Partial<PerfilCargoDetail> & { motivo_cambio?: string }) =>
    apiClient.put<PerfilCargoDetail>(`/modulo1/perfil-cargo/${id}`, data),

  deletePerfil: (id: string) => apiClient.delete<{ message: string }>(`/modulo1/perfil-cargo/${id}`),

  // Historial de Versiones
  getVersiones: (id: string) => apiClient.get<CargoVersion[]>(`/modulo1/perfil-cargo/${id}/versiones`),

  // PDF
  generarPDF: (id: string) => apiClient.post<{ jobId: string; mensaje: string }>(`/modulo1/perfil-cargo/${id}/pdf`, {}),
  
  estadoPDF: (id: string) => apiClient.get<{ estado: 'procesando' | 'listo' | 'error'; url?: string; error?: string; jobId?: string }>(`/modulo1/perfil-cargo/${id}/pdf/estado`),

  // Catálogos
  listPeligros: () => apiClient.get<Record<string, { id: string; tipo: string; clasificacion: string; descripcion?: string; epps_sugeridos?: { id: string; nombre: string; descripcion?: string }[] }[]>>('/modulo1/catalogos/peligros'),
  
  listEPPs: () => apiClient.get<CatalogoEPP[]>('/modulo1/catalogos/epps'),
  
  getEPPsPorPeligro: (peligroId: string) => apiClient.get<CatalogoEPP[]>(`/modulo1/catalogos/peligros/${peligroId}/epps`),

  sugerirPeligrosEPPs: (data: { nombre_cargo: string; area?: string }) =>
    apiClient.post<{ peligros_sugeridos: string[]; epps_sugeridos: string[]; total_peligros: number; total_epps: number }>('/modulo1/perfil-cargo/sugerir-peligros-epps', data),

  // Asistencia por IA con SSE
  generarCampoIAStream: async (
    data: { campo: 'proposito' | 'funciones' | 'responsabilidades'; nombre_cargo: string; area?: string; contexto_adicional?: string },
    onChunk: (text: string) => void,
    onDone: () => void,
    onError: (err: any) => void
  ) => {
    try {
      const token = localStorage.getItem('token')
      const baseUrl = import.meta.env.VITE_API_URL ?? 'http://localhost:4000/api'
      
      const response = await fetch(`${baseUrl}/modulo1/perfil-cargo/generar-ia`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.message || `Error ${response.status}: ${response.statusText}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('El navegador no soporta lectura de streams de respuesta')
      }

      const decoder = new TextDecoder('utf-8')
      let buffer = ''
      let done = false

      while (!done) {
        const { value, done: doneReading } = await reader.read()
        done = doneReading
        
        if (value) {
          buffer += decoder.decode(value, { stream: !done })
          const lines = buffer.split('\n')
          
          // Guardamos la última línea si está incompleta
          buffer = lines.pop() || ''
          
          for (const line of lines) {
            const trimmed = line.trim()
            if (!trimmed) continue
            
            if (trimmed.startsWith('data: ')) {
              const dataContent = trimmed.substring(6).trim()
              
              if (dataContent === '[DONE]') {
                done = true
                break
              }
              
              try {
                const parsed = JSON.parse(dataContent)
                if (parsed.error) {
                  throw new Error(parsed.error)
                }
                if (parsed.text) {
                  onChunk(parsed.text)
                }
              } catch (e: any) {
                if (e.message?.includes('JSON')) {
                  // Error de parseo si el chunk vino incompleto, lo ignoramos para procesar en el buffer
                } else {
                  throw e
                }
              }
            }
          }
        }
      }
      
      onDone()
    } catch (err: any) {
      onError(err)
    }
  }
}
