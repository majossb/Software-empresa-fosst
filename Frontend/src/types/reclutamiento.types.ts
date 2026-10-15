/**
 * Tipos TypeScript para el Módulo de Reclutamiento y Selección — FOSST V.I.D.A.
 * Fases A - G: Modelos de Banco de Talento, Vacantes, Convocatorias,
 * Máquina de Estados, Trazabilidad Inmutable y Portal del Candidato.
 */

export type TipoDocumento = 'CC' | 'CE' | 'PA' | 'PEP' | 'PPT' | 'OTRO'

export type EstadoVacante = 'borrador' | 'abierta' | 'pausada' | 'cerrada' | 'cubierta'

export type ModalidadVacante = 'presencial' | 'remoto' | 'hibrido'

export type EstadoProceso = 'activo' | 'en_pausa' | 'finalizado' | 'cancelado'

export type EstadoPostulacion =
  | 'postulado'
  | 'en_revision'
  | 'preseleccionado'
  | 'en_entrevista'
  | 'en_evaluacion'
  | 'en_validacion'
  | 'seleccionado'
  | 'no_seleccionado'
  | 'retiro_candidatura'
  | 'no_continuo'

export type EstadoSemaforoEtapa = 'no_requerida' | 'completada' | 'en_curso' | 'pendiente'

export interface SemaforoEtapas {
  entrevista: {
    requerida: boolean
    estado: EstadoSemaforoEtapa
  }
  evaluacion: {
    requerida: boolean
    estado: EstadoSemaforoEtapa
  }
  validacion_documental: {
    requerida: boolean
    estado: EstadoSemaforoEtapa
  }
}

export interface FuenteReclutamiento {
  id: string
  nombre: string
  descripcion: string
  activo: boolean
  es_sistema: boolean
  created_at: string
  updated_at: string
}

export interface PerfilCandidato {
  id?: string
  titulo_profesional?: string
  nivel_educativo?: string
  resumen_profesional?: string
  anios_experiencia?: number
  experiencia_laboral?: Array<{
    empresa: string
    cargo: string
    fecha_inicio: string
    fecha_fin?: string
    actual: boolean
    funciones?: string
  }>
  formacion_academica?: Array<{
    institucion: string
    titulo: string
    nivel: string
    anio_graduacion?: number
    en_curso: boolean
  }>
  certificaciones?: Array<string>
  competencias?: Array<string>
  aspiracion_salarial?: number | string | null
  disponibilidad_viaje?: boolean
  disponibilidad_traslado?: boolean
  created_at?: string
  updated_at?: string
}

export interface CandidatoDocumento {
  id: string
  archivo: string
  archivo_nombre?: string
  archivo_url?: string
  tipo_documento: string
  tipo_documento_display: string
  nombre_descriptivo: string
  created_at: string
}

export interface CandidatoListItem {
  id: string
  tipo_documento: TipoDocumento
  tipo_documento_display: string
  documento: string
  nombres: string
  apellidos: string
  nombre_completo: string
  email: string
  telefono: string
  ciudad: string
  fuente_reclutamiento?: string
  fuente_reclutamiento_nombre?: string
  etiquetas: string[]
  autoriza_tratamiento_datos: boolean
  titulo_profesional?: string
  anios_experiencia?: number
  postulaciones_count: number
  created_at: string
}

export interface CandidatoDetail extends CandidatoListItem {
  direccion?: string
  fuente_detalle?: string
  fecha_autorizacion_datos?: string
  notas_internas?: string
  perfil?: PerfilCandidato
  documentos?: CandidatoDocumento[]
  historial_postulaciones?: Array<{
    id: string
    proceso_seleccion_id: string
    vacante_codigo: string
    vacante_titulo: string
    estado: EstadoPostulacion
    estado_display: string
    fecha_postulacion: string
    puntuacion_general?: number | null
    es_activa: boolean
  }>
}

export interface VacanteListItem {
  id: string
  codigo: string
  titulo: string
  slug: string
  perfil_cargo: string
  perfil_cargo_nombre: string
  sede?: string
  sede_nombre?: string
  numero_cupos: number
  numero_seleccionados: number
  cupos_disponibles: number
  esta_cubierta: boolean
  tipo_contrato: string
  modalidad: ModalidadVacante
  modalidad_display: string
  rango_salarial_min?: number | string | null
  rango_salarial_max?: number | string | null
  mostrar_salario_publico: boolean
  estado: EstadoVacante
  estado_display: string
  fecha_apertura?: string
  fecha_cierre_estimada?: string
  publicada_en_portal: boolean
  postulaciones_count: number
  proceso_seleccion_id?: string
  created_at: string
}

export interface VacanteDetail extends VacanteListItem {
  descripcion_publica: string
  fecha_cierre_real?: string
  perfil_cargo_detalle?: {
    id: string
    nombre_cargo: string
    codigo: string
    area: string
    proposito?: string
    educacion?: string
    experiencia?: string
  }
  proceso_seleccion?: {
    id: string
    codigo: string
    estado: EstadoProceso
    requiere_entrevista: boolean
    requiere_evaluacion: boolean
    requiere_validacion_documental: boolean
    total_postulaciones: number
  }
}

export interface PostulacionEvento {
  id: string
  tipo_evento: string
  tipo_evento_display: string
  estado_anterior: string
  estado_nuevo: string
  descripcion: string
  motivo?: string
  es_excepcion: boolean
  justificacion_excepcion?: string
  datos_capturados?: Record<string, any>
  usuario?: string
  usuario_nombre?: string
  created_at: string
}

export interface Entrevista {
  id: string
  postulacion: string
  tipo_entrevista: string
  tipo_entrevista_display: string
  modalidad: string
  modalidad_display: string
  fecha_programada: string
  entrevistador?: string
  entrevistador_nombre?: string
  enlace_reunion?: string
  lugar?: string
  estado: string
  estado_display: string
  calificacion?: number | null
  concepto: string
  concepto_display: string
  observaciones?: string
  aspectos_evaluados?: Record<string, any>
  created_at: string
}

export interface Evaluacion {
  id: string
  postulacion: string
  tipo_evaluacion: string
  tipo_evaluacion_display: string
  nombre_prueba: string
  fecha_asignacion: string
  fecha_realizacion?: string
  evaluador?: string
  evaluador_nombre?: string
  puntaje_obtenido?: number | null
  puntaje_maximo: number
  porcentaje_aprobacion: number
  porcentaje_obtenido?: number | null
  estado: string
  estado_display: string
  concepto?: string
  archivo_informe?: string
  archivo_informe_url?: string
  created_at: string
}

export interface ValidacionDocumental {
  id: string
  postulacion: string
  tipo_verificacion: string
  tipo_verificacion_display: string
  entidad_o_contacto: string
  telefono_contacto?: string
  verificado_por?: string
  verificado_por_nombre?: string
  fecha_verificacion?: string
  estado: string
  estado_display: string
  detalles_verificacion?: string
  soporte_archivo?: string
  soporte_archivo_url?: string
  created_at: string
}

export interface PostulacionListItem {
  id: string
  candidato: string
  candidato_nombre: string
  candidato_documento: string
  candidato_email: string
  candidato_telefono: string
  proceso_seleccion: string
  vacante_codigo: string
  vacante_titulo: string
  estado: EstadoPostulacion
  estado_display: string
  fecha_postulacion: string
  puntuacion_general?: number | null
  etapas_completadas: string[]
  es_activa: boolean
  es_excepcion: boolean
  semaforo_etapas: SemaforoEtapas
  created_at: string
}

export interface PostulacionDetail extends PostulacionListItem {
  candidato_detalle?: CandidatoDetail
  calificacion_requisitos?: Record<string, boolean>
  motivo_cierre?: string
  justificacion_excepcion?: string
  autorizado_por?: string
  autorizado_por_nombre?: string
  eventos: PostulacionEvento[]
  entrevistas: Entrevista[]
  evaluaciones: Evaluacion[]
  validaciones_documentales: ValidacionDocumental[]
}

export interface ProcesoSeleccionDetail {
  id: string
  codigo: string
  vacante: string
  vacante_detalle?: VacanteListItem
  responsable_rh?: string
  responsable_rh_nombre?: string
  requiere_entrevista: boolean
  requiere_evaluacion: boolean
  requiere_validacion_documental: boolean
  requisitos_obligatorios: string[]
  requisitos_deseables: string[]
  criterios_evaluacion: Record<string, any>
  estado: EstadoProceso
  estado_display: string
  resumen_postulaciones: Record<string, number>
  postulaciones: PostulacionListItem[]
  created_at: string
  updated_at: string
}

// ── Portal del Candidato (Público) ──────────────────────────────
export interface VacantePublicaListItem {
  id: string
  codigo: string
  titulo: string
  slug: string
  empresa_nombre: string
  sede_ciudad: string
  modalidad: ModalidadVacante
  modalidad_display: string
  tipo_contrato: string
  numero_cupos: number
  salario_display: string
  fecha_cierre_estimada?: string
  created_at: string
}

export interface VacantePublicaDetail extends VacantePublicaListItem {
  descripcion_publica: string
  requisitos_obligatorios: string[]
  requisitos_deseables: string[]
}

export interface PostulacionCandidatoPublica {
  id: string
  vacante_codigo: string
  vacante_titulo: string
  empresa_nombre: string
  fecha_postulacion: string
  estado_publico: string
  etapa_actual: string
  es_activa: boolean
}

export interface CandidatoPerfilCompleto {
  id: string
  tipo_documento: TipoDocumento
  documento: string
  nombres: string
  apellidos: string
  email: string
  telefono: string
  ciudad: string
  direccion: string
  titulo_profesional: string
  nivel_educativo: string
  resumen_profesional: string
  anios_experiencia: number
  aspiracion_salarial?: number | null
  ultima_hoja_vida?: {
    id: string
    nombre: string
    url: string
    tamanio_kb: number
  } | null
}

