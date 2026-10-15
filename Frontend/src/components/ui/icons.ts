/**
 * Catálogo Centralizado de Iconografía — FOSST V.I.D.A.
 * Garantiza consistencia visual outline (stroke 1.8-2px) en todos los módulos.
 */
import {
  Users, User, UserCheck, UserX, UserPlus,
  Settings, Building2, MapPin, GitBranch, Workflow,
  Briefcase, FileText, FileCheck, ClipboardCheck,
  GraduationCap, Award, Bell, AlertTriangle, AlertCircle,
  CheckCircle2, Check, Search, Pencil, Edit3, Trash2,
  Eye, EyeOff, Download, Upload, Calendar, Sparkles,
  History, Shield, ShieldCheck, ShieldAlert,
  Stethoscope, HeartPulse, Lock, LogOut, ArrowRight,
  ArrowLeft, ChevronDown, ChevronRight, ChevronLeft,
  X, Plus, RefreshCw, Layers, TrendingUp, TrendingDown,
  Scale, FileSpreadsheet, Send, Phone, Mail, Link as LinkIcon
} from 'lucide-react'

export const FOSST_ICONS = {
  // Organización y Estructura
  empresa: Building2,
  sede: MapPin,
  organigrama: GitBranch,
  proceso: Workflow,
  cargo: Briefcase,
  configuracion: Settings,

  // Personas y Talento
  usuarios: Users,
  usuario: User,
  candidatoHabilitado: UserCheck,
  candidatoRechazado: UserX,
  nuevoUsuario: UserPlus,

  // Documentos y Evidencias
  documento: FileText,
  evidencia: FileCheck,
  auditoria: ClipboardCheck,
  reporte: FileSpreadsheet,

  // Capacitación y Competencias
  formacion: GraduationCap,
  certificacion: Award,

  // Seguridad y Salud Ocupacional (SST)
  seguridad: Shield,
  seguridadOk: ShieldCheck,
  riesgo: ShieldAlert,
  medicinaOcupacional: Stethoscope,
  salud: HeartPulse,

  // Notificaciones y Estados
  alerta: Bell,
  advertencia: AlertTriangle,
  error: AlertCircle,
  exito: CheckCircle2,
  check: Check,

  // Acciones UI
  buscar: Search,
  editar: Pencil,
  editarAlt: Edit3,
  eliminar: Trash2,
  ver: Eye,
  ocultar: EyeOff,
  descargar: Download,
  subir: Upload,
  actualizar: RefreshCw,
  agregar: Plus,
  cerrar: X,
  enviar: Send,

  // Navegación y Tiempo
  calendario: Calendar,
  historial: History,
  asistenteIA: Sparkles,
  siguiente: ArrowRight,
  anterior: ArrowLeft,
  chevronAbajo: ChevronDown,
  chevronDerecha: ChevronRight,
  chevronIzquierda: ChevronLeft,

  // Tendencias
  tendenciaSubida: TrendingUp,
  tendenciaBajada: TrendingDown,
  balance: Scale,
  capas: Layers,

  // Contacto y Autenticación
  candado: Lock,
  cerrarSesion: LogOut,
  telefono: Phone,
  email: Mail,
  enlace: LinkIcon,
} as const

export type FosstIconName = keyof typeof FOSST_ICONS
