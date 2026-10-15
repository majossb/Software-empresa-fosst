// ── Roles ─────────────────────────────────────────────────────────
export type UserRole = 'alta_direccion' | 'responsable' | 'auditor'

export const ROLE_LABELS: Record<UserRole, string> = {
  alta_direccion: 'Alta Dirección',
  responsable:    'Responsable SG-SST',
  auditor:        'Auditor Externo SST',
}

export const ROLE_ROUTES: Record<UserRole, string> = {
  alta_direccion: '/app/alta-direccion',
  responsable:    '/app/responsable',
  auditor:        '/app/auditor',
}

export const ROUTES = {
  login:         '/login',
  altaDireccion: '/app/alta-direccion',
  responsable:   '/app/responsable',
  auditor:       '/app/auditor',
} as const

// ── Empresa anidada ────────────────────────────────────────────────
export interface Empresa {
  id:               string
  nombre:           string
  nit:              string
  capitulo_vigente?: 'I' | 'II' | 'III'
}

// ── Usuario autenticado ────────────────────────────────────────────
export interface AuthUser {
  id:        string
  nombre:    string
  documento: string
  rol:       UserRole
  empresa:   Empresa
}

// ── Payload de login (sin rol — el backend lo detecta) ─────────────
export interface LoginPayload {
  nit:       string
  documento: string
  password:  string
}

export interface OTPRequiredResponse {
  message:               string
  usuario_id:            string
  otp_expira_en_minutos: number
  expires_at:            string
}

// ── Tipos del dominio ──────────────────────────────────────────────
export type CicloPHVA = 'Planear' | 'Hacer' | 'Verificar' | 'Actuar'
export type EstadoCumplimiento = 'cumple' | 'no_cumple' | 'parcial' | 'no_aplica' | 'sin_respuesta'
export type EstadoPlan = 'pendiente' | 'en_progreso' | 'completado'
export type PrioridadPlan = 'urgente' | 'importante' | 'aceptable'
export type TipoHallazgo = 'no_conformidad_mayor' | 'no_conformidad_menor' | 'observacion' | 'oportunidad_mejora' | 'fortaleza'
export type EstadoCapacitacion = 'programada' | 'realizada' | 'cancelada'

export interface EstandarMinimo {
  estandar_id:   string
  codigo:        string
  nombre:        string
  descripcion?:  string
  ciclo_phva:    CicloPHVA
  puntaje_maximo: number
  obligatorio:   boolean
  respuesta_id:  string | null
  estado:        EstadoCumplimiento
  puntaje:       number
  observacion:   string
  evidencias:    number
  porcentaje?:   number
}

export interface PHVAData {
  obtenido:   number
  maximo:     number
  porcentaje: number
}

export interface KpiData {
  label: string
  valor: string | number
  desc:  string
  trend: 'up' | 'down' | 'neutral'
  color: 'blue' | 'green' | 'red' | 'orange' | 'purple'
}

// ── Dashboard Alta Dirección ──────────────────────────────────────
export interface DashboardAD {
  empresa: { nombre: string; nit: string; capitulo_vigente: string; num_trabajadores: number; nivel_riesgo: number }
  cumplimiento: {
    global: number
    puntaje_obtenido: number
    puntaje_maximo: number
    total_estandares: number
    cumplidos: number
    no_cumple: number
    parciales: number
  }
  phva: Record<string, PHVAData>
  estandares_criticos: Array<{
    codigo: string; nombre: string; ciclo: string
    puntaje_maximo: number; puntaje_obtenido: number
    estado: string; porcentaje: number
  }>
  sancion: { potencial: number; evitada: number; smmlv: number; factor: number }
  plan_mejora: Array<{ estado: string; _count: number }>
  historial: Array<{ anio: number; puntaje_total: number | null; estado: string }>
  evaluacion_id: string | null
}

// ── Dashboard Responsable ─────────────────────────────────────────
export interface DashboardResp {
  empresa: { nombre: string; capitulo_vigente: string }
  evaluacion_id: string
  kpis: {
    avance_global: number; cumplidos: number
    total_estandares: number; urgentes: number
    evidencias_cargadas: number
  }
  estandares: EstandarMinimo[]
  planes_urgentes: PlanMejora[]
  capacitaciones_proximas: Capacitacion[]
}

// ── Dashboard Auditor ─────────────────────────────────────────────
export interface DashboardAud {
  empresa: { nombre: string; capitulo_vigente: string }
  evaluacion_id: string | null
  kpis: {
    cumplimiento_general: number
    evidencias_revisadas: number
    hallazgos: { total: number; no_conformidad: number; observacion: number; oportunidad: number; fortaleza: number }
  }
  tabla_verificacion: Array<{
    codigo: string; nombre: string; ciclo_phva: string
    puntaje_maximo: number; estado_empresa: string
    puntaje: number; documentos: number; hallazgo_id: string | null
  }>
  hallazgos_detalle: Hallazgo[]
}

// ── Modelos del dominio ───────────────────────────────────────────
export interface Evaluacion {
  id: string; empresa_id: string; anio: number
  capitulo: string; puntaje_total: number | null
  estado: string; created_at: string
}

export interface Hallazgo {
  id: string; evaluacion_id?: string; evaluacion?: string; auditor_id?: string
  descripcion: string; tipo: TipoHallazgo; created_at: string
  auditor?: { id: string; nombre: string }
  auditor_nombre?: string
  estandar_codigo?: string
  estandar_nombre?: string
}

export interface PlanMejora {
  id: string; empresa_id: string; accion: string
  responsable: string; prioridad: PrioridadPlan
  fecha_limite: string; estado: EstadoPlan; created_at: string
}

export interface Capacitacion {
  id: string; empresa_id: string; tema: string
  proveedor: string | null; fecha: string
  num_asistentes: number; tiene_certificado: boolean
  estado: EstadoCapacitacion; created_at: string
  _count?: { participantes: number }
}

export interface Evidencia {
  id: string; descripcion: string; created_at: string
  estandar_codigo: string; estandar_nombre: string
  respuesta_id: string; estado_estandar: string
  archivo: { id: string; nombre: string; url: string; tipo_mime: string; tamanio_kb: number } | null
  fecha_ocurrencia?: string | null
  responsable?: string | null
  firma?: string | null
}

export interface Informe {
  id: string; evaluacion_id: string; tipo: string
  contenido_json: any; fecha_elaboracion: string
  evaluacion?: { anio: number; capitulo: string }
}

export interface PlanMejoraResumen {
  total: number; pendientes: number; en_progreso: number
  completados: number; urgentes: number; vencidos: number
}