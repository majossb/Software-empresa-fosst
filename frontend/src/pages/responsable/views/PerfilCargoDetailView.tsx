import { useState, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { usePerfilCargo, useVersionesPerfilCargo } from '@/hooks/useApi'
import { modulo1Service } from '@/services/modulo1.service'
import { LoadingSpinner, ErrorDisplay, Modal } from '@/components/ui/forms'
import { Button, Table, TableHeader, TableBody, TableRow, TableHead, TableCell, EmptyState } from '@/components/ui'
import { 
  ArrowLeft, Edit3, FileText, Calendar, User, Users, History, Shield, 
  Activity, Briefcase, GraduationCap, CheckCircle2,
  ShieldCheck, Printer, Target, Settings, Award, Compass,
  Car, Ban, Moon, HeartPulse, Check, Sparkles, Building2, MapPin
} from 'lucide-react'

// Helper para formatear fechas
function formatLocalDate(dateStr?: string) {
  if (!dateStr) return '20/05/2025'
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('es-CO', { year: 'numeric', month: '2-digit', day: '2-digit' })
  } catch {
    return dateStr
  }
}

export default function PerfilCargoDetailView() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const printRef = useRef<HTMLDivElement>(null)

  // ── States ──────────────────────────────────────────────────────────
  const [selectedVersion, setSelectedVersion] = useState<any | null>(null)
  const [isVersionModalOpen, setIsVersionModalOpen] = useState(false)

  // ── Queries ─────────────────────────────────────────────────────────
  const { 
    data: perfil, 
    isLoading: loadingPerfil, 
    error: errorPerfil,
    refetch: refetchPerfil 
  } = usePerfilCargo(id || null)

  const { 
    data: versiones, 
    isLoading: loadingVersiones 
  } = useVersionesPerfilCargo(id!)

  const handlePrint = () => {
    window.print()
  }

  if (loadingPerfil) {
    return <LoadingSpinner text="Cargando perfil de cargo oficial FOSST V.I.D.A..." />
  }

  if (errorPerfil || !perfil) {
    return <ErrorDisplay message={errorPerfil ? (errorPerfil as Error).message : 'El perfil solicitado no existe.'} onRetry={refetchPerfil} />
  }

  // Mapeo de criticidad
  const criticidadText = (perfil.criticidad_sst || 'alto').toUpperCase()
  const criticidadColor = 
    criticidadText === 'CRITICO' || criticidadText === 'ALTO' || criticidadText === 'ALTA' 
      ? 'bg-rose-600 text-white' 
      : criticidadText === 'MEDIO' || criticidadText === 'MEDIA'
      ? 'bg-amber-500 text-slate-900'
      : 'bg-emerald-600 text-white'

  // Competencias con 4 niveles (1=Básico, 2=Intermedio, 3=Avanzado, 4=Experto)
  const renderLevelDots = (level: number = 3, dotColor: string = 'text-emerald-500') => {
    return (
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4].map((dot) => (
          <span
            key={dot}
            className={`w-2 h-2 rounded-full ${
              dot <= level 
                ? (dotColor === 'text-emerald-500' ? 'bg-emerald-500' : dotColor === 'text-blue-500' ? 'bg-blue-500' : 'bg-primary-500') 
                : 'bg-slate-300 dark:bg-slate-700'
            }`}
          />
        ))}
      </div>
    )
  }

  return (
    <div className="animate-fade-in space-y-6 pb-16">
      
      {/* ── Barra Superior de Acciones (Oculta al Imprimir) ───────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 print:hidden bg-slate-900/80 p-4 rounded-2xl border border-slate-800 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <Button 
            onClick={() => navigate('/app/responsable/perfiles-cargo')}
            className="!p-2 !bg-slate-800 !border-slate-700 hover:!bg-slate-700 !text-slate-300"
            title="Volver al catálogo"
            icon={<ArrowLeft className="w-5 h-5" />}
          >
            {""}
          </Button>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-500/30 px-2 py-0.5 rounded">
                {perfil.codigo}
              </span>
              <span className="text-xs font-bold text-slate-400">
                Versión {perfil.version_actual}.0
              </span>
            </div>
            <h1 className="text-lg font-black text-white">{perfil.nombre_cargo}</h1>
          </div>
        </div>

        {/* Botones de acción */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <Button
            onClick={() => setIsVersionModalOpen(true)}
            className="!px-3.5 !py-2 !bg-slate-800 hover:!bg-slate-700 !text-slate-200 !border-slate-700"
            icon={<History className="w-4 h-4 text-emerald-400" />}
          >
            Historial ({versiones?.length || 1})
          </Button>

          <Button
            onClick={() => navigate(`/app/responsable/perfiles-cargo/${perfil.id}/editar`)}
            className="!px-3.5 !py-2 !bg-slate-800 hover:!bg-slate-700 !text-slate-200 !border-slate-700"
            icon={<Edit3 className="w-4 h-4 text-brand-400" />}
          >
            Editar
          </Button>

          <Button
            onClick={handlePrint}
            className="!px-4 !py-2 !bg-emerald-600 hover:!bg-emerald-500 !text-white !border-emerald-600 shadow-lg shadow-emerald-600/30"
            icon={<Printer className="w-4 h-4" />}
          >
            Imprimir / Guardar PDF
          </Button>
        </div>
      </div>

      {/* ── HOJA OFICIAL PERFIL DE CARGO FOSST V.I.D.A. (Print-Ready) ─── */}
      <div 
        ref={printRef}
        className="max-w-[1050px] mx-auto bg-white text-slate-900 shadow-2xl rounded-2xl border border-slate-300 p-6 sm:p-8 space-y-4 print:shadow-none print:border-none print:p-0 print:m-0 print:max-w-none print:w-full font-sans text-xs"
        style={{ color: '#0F172A' }}
      >
        
        {/* ── ENCABEZADO OFICIAL ────────────────────────────────────────── */}
        <header className="bg-slate-900 text-white rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4 border-b-2 border-emerald-500 print:rounded-none">
          {/* Logo Brand */}
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-emerald-500 to-brand-500 flex items-center justify-center text-slate-950 font-black text-xl shadow-md">
              <ShieldCheck className="w-7 h-7 text-slate-950" />
            </div>
            <div>
              <div className="font-extrabold text-base tracking-wider text-white">FOSST</div>
              <div className="font-black text-emerald-400 text-sm tracking-widest leading-none">V.I.D.A.</div>
              <p className="text-[9px] text-slate-400 tracking-tight mt-0.5">Gestión Integral • Seguridad • Desempeño</p>
            </div>
          </div>

          {/* Title in center */}
          <div className="text-center">
            <h2 className="text-xs font-bold tracking-widest text-slate-300 uppercase">PERFIL DEL CARGO</h2>
            <h1 className="text-xl font-black text-emerald-400 uppercase tracking-wide">{perfil.nombre_cargo}</h1>
          </div>

          {/* Metadata Badges */}
          <div className="grid grid-cols-2 gap-2 text-[10px] text-slate-300 bg-slate-800/80 p-2.5 rounded-lg border border-slate-700">
            <div className="flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-emerald-400" />
              <span>Código: <strong className="text-white font-mono">{perfil.codigo}</strong></span>
            </div>
            <div className="flex items-center gap-1.5">
              <Compass className="w-3.5 h-3.5 text-emerald-400" />
              <span>Versión: <strong className="text-white font-mono">{perfil.version_actual}.0</strong></span>
            </div>
            <div className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-emerald-400" />
              <span>Actualización: <strong className="text-white">{formatLocalDate(perfil.updated_at)}</strong></span>
            </div>
            <div className="flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-emerald-400" />
              <span>Página: <strong className="text-white">1 de 1</strong></span>
            </div>
          </div>
        </header>

        {/* ── CUERPO PRINCIPAL (3 COLUMNAS / GRID MODULAR) ─────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          
          {/* ── COLUMNA IZQUIERDA (Secciones 1 y 4) ────────────────────── */}
          <div className="lg:col-span-4 space-y-4">
            
            {/* 1. Identificación del Cargo */}
            <div className="border border-slate-300 rounded-xl overflow-hidden shadow-sm">
              <div className="bg-slate-900 text-white px-3 py-1.5 font-bold text-[11px] uppercase tracking-wide flex items-center gap-1.5">
                <span className="w-4 h-4 rounded-full bg-emerald-500 text-slate-950 flex items-center justify-center text-[10px]">1</span>
                IDENTIFICACIÓN DEL CARGO
              </div>
              <div className="p-3 space-y-2 text-[11px] bg-slate-50/50">
                <div className="flex justify-between border-b border-slate-200 pb-1">
                  <span className="text-slate-600 font-medium">Nombre del cargo:</span>
                  <span className="font-bold text-slate-900">{perfil.nombre_cargo}</span>
                </div>
                <div className="flex justify-between border-b border-slate-200 pb-1">
                  <span className="text-slate-600 font-medium">Área / Proceso:</span>
                  <span className="font-semibold text-slate-800">{perfil.area || 'Operaciones / Transporte'}</span>
                </div>
                <div className="flex justify-between border-b border-slate-200 pb-1">
                  <span className="text-slate-600 font-medium">Dependencia jerárquica:</span>
                  <span className="font-semibold text-slate-800">{perfil.nodo_organigrama_id || 'Coordinador de Operaciones'}</span>
                </div>
                <div className="flex justify-between border-b border-slate-200 pb-1">
                  <span className="text-slate-600 font-medium">Nivel organizacional:</span>
                  <span className="font-semibold text-slate-800">Operativo</span>
                </div>
                <div className="flex justify-between border-b border-slate-200 pb-1">
                  <span className="text-slate-600 font-medium">Cargo(s) que supervisa:</span>
                  <span className="font-semibold text-slate-800">N/A</span>
                </div>
                <div className="flex justify-between border-b border-slate-200 pb-1">
                  <span className="text-slate-600 font-medium">Tipo de contrato:</span>
                  <span className="font-semibold text-slate-800">Término indefinido</span>
                </div>
                <div className="flex justify-between border-b border-slate-200 pb-1">
                  <span className="text-slate-600 font-medium">Jornada:</span>
                  <span className="font-semibold text-slate-800">Diurna / Rotativa (según programación)</span>
                </div>
                <div className="flex justify-between border-b border-slate-200 pb-1">
                  <span className="text-slate-600 font-medium">Lugar de trabajo:</span>
                  <span className="font-semibold text-slate-800">{perfil.sede?.nombre || 'Sedes operativas y rutas asignadas'}</span>
                </div>
                <div className="flex justify-between items-center pt-0.5">
                  <span className="text-slate-600 font-medium">Criticidad del cargo:</span>
                  <span className={`px-2 py-0.5 rounded font-black text-[10px] tracking-wider uppercase ${criticidadColor}`}>
                    {criticidadText}
                  </span>
                </div>
              </div>
            </div>

            {/* 4. Responsabilidades Clave */}
            <div className="border border-slate-300 rounded-xl overflow-hidden shadow-sm">
              <div className="bg-slate-900 text-white px-3 py-1.5 font-bold text-[11px] uppercase tracking-wide flex items-center gap-1.5">
                <span className="w-4 h-4 rounded-full bg-emerald-500 text-slate-950 flex items-center justify-center text-[10px]">4</span>
                RESPONSABILIDADES CLAVE
              </div>
              <div className="p-3 bg-slate-50/50 space-y-2">
                <ul className="space-y-1.5 text-[11px] text-slate-700">
                  {perfil.responsabilidades && perfil.responsabilidades.length > 0 ? (
                    perfil.responsabilidades.map((r: any, idx: number) => (
                      <li key={idx} className="flex items-start gap-1.5">
                        <span className="text-emerald-600 font-bold mt-0.5">•</span>
                        <span>{r.descripcion}</span>
                      </li>
                    ))
                  ) : (
                    <>
                      <li className="flex items-start gap-1.5">
                        <span className="text-emerald-600 font-bold mt-0.5">•</span>
                        <span>Preservar la vida e integridad de pasajeros, peatones y demás actores viales.</span>
                      </li>
                      <li className="flex items-start gap-1.5">
                        <span className="text-emerald-600 font-bold mt-0.5">•</span>
                        <span>Cumplir la normatividad de tránsito y el Plan Estratégico de Seguridad Vial (PESV).</span>
                      </li>
                      <li className="flex items-start gap-1.5">
                        <span className="text-emerald-600 font-bold mt-0.5">•</span>
                        <span>Reportar oportunamente incidentes, accidentes, fallas mecánicas y actos inseguros.</span>
                      </li>
                      <li className="flex items-start gap-1.5">
                        <span className="text-emerald-600 font-bold mt-0.5">•</span>
                        <span>Mantener la documentación del vehículo y personal vigente y disponible.</span>
                      </li>
                      <li className="flex items-start gap-1.5">
                        <span className="text-emerald-600 font-bold mt-0.5">•</span>
                        <span>Contribuir al cumplimiento de indicadores operacionales y de seguridad.</span>
                      </li>
                    </>
                  )}
                </ul>

                <div className="pt-2 flex justify-end">
                  <div className="w-7 h-7 rounded-full border border-emerald-500 text-emerald-600 flex items-center justify-center">
                    <Check className="w-4 h-4" />
                  </div>
                </div>
              </div>
            </div>

          </div>

          {/* ── COLUMNA CENTRAL (Secciones 2, 3 y 5) ───────────────────── */}
          <div className="lg:col-span-5 space-y-4">
            
            {/* 2. Propósito del Cargo */}
            <div className="border border-slate-300 rounded-xl overflow-hidden shadow-sm">
              <div className="bg-slate-900 text-white px-3 py-1.5 font-bold text-[11px] uppercase tracking-wide flex items-center gap-1.5">
                <span className="w-4 h-4 rounded-full bg-emerald-500 text-slate-950 flex items-center justify-center text-[10px]">2</span>
                PROPÓSITO DEL CARGO
              </div>
              <div className="p-3 bg-slate-50/50 flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0 mt-0.5">
                  <Target className="w-5 h-5" />
                </div>
                <p className="text-[11px] text-slate-800 leading-relaxed font-medium">
                  {perfil.proposito || 'Garantizar la operación segura y eficiente del transporte de pasajeros mediante la conducción responsable y el cumplimiento de los lineamientos operacionales, normativos y de seguridad vial.'}
                </p>
              </div>
            </div>

            {/* 3. Funciones Principales */}
            <div className="border border-slate-300 rounded-xl overflow-hidden shadow-sm">
              <div className="bg-slate-900 text-white px-3 py-1.5 font-bold text-[11px] uppercase tracking-wide flex items-center gap-1.5">
                <span className="w-4 h-4 rounded-full bg-emerald-500 text-slate-950 flex items-center justify-center text-[10px]">3</span>
                FUNCIONES PRINCIPALES
              </div>
              <div className="divide-y divide-slate-200 bg-white">
                {perfil.funciones && perfil.funciones.length > 0 ? (
                  perfil.funciones.map((f: any, idx: number) => (
                    <div key={idx} className="flex items-start gap-2.5 p-2 text-[11px] hover:bg-slate-50">
                      <span className="w-5 h-5 rounded bg-slate-100 font-bold text-slate-700 flex items-center justify-center text-[10px] shrink-0">
                        {idx + 1}
                      </span>
                      <span className="text-slate-800 leading-snug">{f.descripcion}</span>
                    </div>
                  ))
                ) : (
                  [
                    'Conducir el vehículo asignado cumpliendo normas de tránsito y lineamientos del PESV.',
                    'Realizar inspecciones preoperacionales y postoperacionales del vehículo.',
                    'Cumplir rutas, horarios y servicios asignados asegurando la puntualidad y seguridad.',
                    'Garantizar la seguridad, comodidad y buen trato a los pasajeros.',
                    'Reportar novedades, incidentes y condiciones inseguras de forma inmediata.',
                    'Velar por el cuidado, limpieza y buen uso del vehículo y equipos asignados.',
                    'Diligenciar formatos, documentos y aplicativos requeridos para la operación.',
                    'Participar en capacitaciones, inducciones y actividades de seguridad vial y SST.'
                  ].map((func, idx) => (
                    <div key={idx} className="flex items-start gap-2.5 p-2 text-[11px] hover:bg-slate-50">
                      <span className="w-5 h-5 rounded bg-slate-100 font-bold text-slate-700 flex items-center justify-center text-[10px] shrink-0">
                        {idx + 1}
                      </span>
                      <span className="text-slate-800 leading-snug">{func}</span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* 5. Requisitos del Cargo */}
            <div className="border border-slate-300 rounded-xl overflow-hidden shadow-sm">
              <div className="bg-slate-900 text-white px-3 py-1.5 font-bold text-[11px] uppercase tracking-wide flex items-center gap-1.5">
                <span className="w-4 h-4 rounded-full bg-emerald-500 text-slate-950 flex items-center justify-center text-[10px]">5</span>
                REQUISITOS DEL CARGO
              </div>
              <div className="p-3 bg-slate-50/50 space-y-2 text-[11px]">
                <div>
                  <span className="font-bold text-slate-900 block flex items-center gap-1.5">
                    <GraduationCap className="w-4 h-4 text-emerald-600" />
                    Formación académica:
                  </span>
                  <p className="text-slate-700 pl-5">{perfil.educacion || 'Bachiller académico (mínimo).'}</p>
                </div>

                <div>
                  <span className="font-bold text-slate-900 block flex items-center gap-1.5">
                    <Briefcase className="w-4 h-4 text-emerald-600" />
                    Experiencia:
                  </span>
                  <p className="text-slate-700 pl-5">{perfil.experiencia || 'Mínimo 2 años conduciendo vehículos de servicio público o especial.'}</p>
                </div>

                <div>
                  <span className="font-bold text-slate-900 block flex items-center gap-1.5">
                    <Car className="w-4 h-4 text-emerald-600" />
                    Licencia de conducción:
                  </span>
                  <p className="text-slate-700 pl-5">Categoría C2 o C1 (según tipo de vehículo).</p>
                </div>

                <div>
                  <span className="font-bold text-slate-900 block flex items-center gap-1.5">
                    <Award className="w-4 h-4 text-emerald-600" />
                    Certificaciones requeridas:
                  </span>
                  <ul className="text-slate-700 pl-5 space-y-0.5">
                    <li>• Curso de Conducción Defensiva (vigente)</li>
                    <li>• Curso PESV (vigente)</li>
                    <li>• Primeros Auxilios (deseable)</li>
                  </ul>
                </div>

                <div>
                  <span className="font-bold text-slate-900 block flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    Otros requisitos:
                  </span>
                  <ul className="text-slate-700 pl-5 space-y-0.5">
                    <li>• Sin comparendos graves ni muy graves vigentes.</li>
                    <li>• Disponibilidad para horarios y rutas asignadas.</li>
                  </ul>
                </div>
              </div>
            </div>

          </div>

          {/* ── COLUMNA DERECHA (Sidebar + Sección 6) ─────────────────── */}
          <div className="lg:col-span-3 space-y-4">
            
            {/* Tarjeta de Impacto y Relaciones Clave */}
            <div className="p-3 bg-slate-50 border border-slate-300 rounded-xl space-y-3 text-[11px]">
              <div>
                <span className="font-bold text-slate-900 uppercase tracking-wider text-[10px] block mb-1">
                  IMPACTO DEL CARGO
                </span>
                <p className="text-slate-700 leading-relaxed">
                  {perfil.impacto_descripcion || 'Afecta directamente la seguridad de las personas, la continuidad del servicio y el cumplimiento legal y operacional de la organización.'}
                </p>
              </div>

              <div className="pt-2 border-t border-slate-200">
                <span className="font-bold text-slate-900 uppercase tracking-wider text-[10px] block mb-1.5">
                  RELACIONES CLAVE
                </span>
                <ul className="space-y-1.5 text-slate-700">
                  <li className="flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5 text-slate-500" />
                    <span>Coordinador de Operaciones</span>
                  </li>
                  <li className="flex items-center gap-1.5">
                    <Compass className="w-3.5 h-3.5 text-slate-500" />
                    <span>Despacho / Control de Rutas</span>
                  </li>
                  <li className="flex items-center gap-1.5">
                    <Settings className="w-3.5 h-3.5 text-slate-500" />
                    <span>Mantenimiento</span>
                  </li>
                  <li className="flex items-center gap-1.5">
                    <Users className="w-3.5 h-3.5 text-slate-500" />
                    <span>Usuarios / Pasajeros</span>
                  </li>
                  <li className="flex items-center gap-1.5">
                    <Shield className="w-3.5 h-3.5 text-slate-500" />
                    <span>Autoridades de Tránsito</span>
                  </li>
                </ul>
              </div>

              <div className="pt-2 border-t border-slate-200">
                <span className="font-bold text-slate-900 uppercase tracking-wider text-[10px] block mb-1">
                  NATURALEZA DEL CARGO
                </span>
                <p className="text-slate-700 leading-relaxed">
                  {perfil.naturaleza_descripcion || 'Cargo operativo de responsabilidad directa sobre la vida de los pasajeros, el vehículo y la operación segura en vía.'}
                </p>
              </div>
            </div>

            {/* 6. Competencias Requeridas */}
            <div className="border border-slate-300 rounded-xl overflow-hidden shadow-sm">
              <div className="bg-slate-900 text-white px-3 py-1.5 font-bold text-[11px] uppercase tracking-wide flex items-center gap-1.5">
                <span className="w-4 h-4 rounded-full bg-emerald-500 text-slate-950 flex items-center justify-center text-[10px]">6</span>
                COMPETENCIAS REQUERIDAS
              </div>
              <div className="p-3 bg-white space-y-3 text-[11px]">
                {/* Técnicas */}
                <div>
                  <div className="flex justify-between items-center mb-1 text-emerald-800 font-bold border-b border-emerald-100 pb-0.5">
                    <span>Técnicas (Saber hacer)</span>
                    <span className="text-[9px] text-slate-500">Nivel</span>
                  </div>
                  <div className="space-y-1 text-slate-700">
                    <div className="flex justify-between items-center">
                      <span>• Conducción defensiva</span>
                      {renderLevelDots(3, 'text-emerald-500')}
                    </div>
                    <div className="flex justify-between items-center">
                      <span>• Normas de tránsito y PESV</span>
                      {renderLevelDots(4, 'text-emerald-500')}
                    </div>
                    <div className="flex justify-between items-center">
                      <span>• Inspección preoperacional</span>
                      {renderLevelDots(4, 'text-emerald-500')}
                    </div>
                    <div className="flex justify-between items-center">
                      <span>• Conocimiento de rutas</span>
                      {renderLevelDots(3, 'text-emerald-500')}
                    </div>
                    <div className="flex justify-between items-center">
                      <span>• Manejo de emergencias viales</span>
                      {renderLevelDots(3, 'text-emerald-500')}
                    </div>
                  </div>
                </div>

                {/* Blandas */}
                <div>
                  <div className="flex justify-between items-center mb-1 text-primary-500 font-bold border-b border-primary-100 pb-0.5">
                    <span>Blandas (Saber ser)</span>
                    <span className="text-[9px] text-slate-500">Nivel</span>
                  </div>
                  <div className="space-y-1 text-slate-700">
                    <div className="flex justify-between items-center">
                      <span>• Responsabilidad</span>
                      {renderLevelDots(4, 'text-primary-500')}
                    </div>
                    <div className="flex justify-between items-center">
                      <span>• Atención al detalle</span>
                      {renderLevelDots(3, 'text-primary-500')}
                    </div>
                    <div className="flex justify-between items-center">
                      <span>• Autocontrol y calma</span>
                      {renderLevelDots(4, 'text-primary-500')}
                    </div>
                    <div className="flex justify-between items-center">
                      <span>• Orientación al servicio</span>
                      {renderLevelDots(3, 'text-primary-500')}
                    </div>
                  </div>
                </div>

                {/* Organizacionales */}
                <div>
                  <div className="flex justify-between items-center mb-1 text-primary-500 font-bold border-b border-slate-100 pb-0.5">
                    <span>Organizacionales (Saber actuar)</span>
                    <span className="text-[9px] text-slate-500">Nivel</span>
                  </div>
                  <div className="space-y-1 text-slate-700">
                    <div className="flex justify-between items-center">
                      <span>• Cumplimiento normativo</span>
                      {renderLevelDots(4, 'text-primary-500')}
                    </div>
                    <div className="flex justify-between items-center">
                      <span>• Compromiso con la seguridad</span>
                      {renderLevelDots(4, 'text-primary-500')}
                    </div>
                    <div className="flex justify-between items-center">
                      <span>• Ética y transparencia</span>
                      {renderLevelDots(4, 'text-primary-500')}
                    </div>
                  </div>
                </div>

                {/* Leyenda */}
                <div className="pt-2 border-t border-slate-200 text-[9px] text-slate-500 flex justify-between">
                  <span>1. Básico</span>
                  <span>2. Intermedio</span>
                  <span>3. Avanzado</span>
                  <span>4. Experto</span>
                </div>
              </div>
            </div>

          </div>

        </div>

        {/* ── SECCIONES INFERIORES: MATRICES Y TABLAS ───────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          
          {/* 7. Peligros y Riesgos Asociados al Cargo (GTC 45) */}
          <div className="lg:col-span-7 border border-slate-300 rounded-xl overflow-hidden shadow-sm">
            <div className="bg-slate-900 text-white px-3 py-1.5 font-bold text-[11px] uppercase tracking-wide flex items-center gap-1.5">
              <span className="w-4 h-4 rounded-full bg-emerald-500 text-slate-950 flex items-center justify-center text-[10px]">7</span>
              PELIGROS Y RIESGOS ASOCIADOS AL CARGO (GTC 45)
            </div>
            <Table className="!border-none !shadow-none">
              <TableHeader className="!bg-slate-100 !text-slate-700 !border-b !border-slate-300">
                <TableRow className="border-none hover:bg-transparent">
                  <TableHead className="!p-2 !font-bold">Peligros</TableHead>
                  <TableHead className="!p-2 !font-bold">Riesgos</TableHead>
                  <TableHead className="!p-2 !font-bold">Nivel</TableHead>
                  <TableHead className="!p-2 !font-bold">Controles Principales</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody className="!divide-y !divide-slate-200">
                <TableRow>
                  <TableCell className="!p-2 !font-semibold">
                    <div className="flex items-center gap-1">
                      <Car className="w-3.5 h-3.5 text-rose-500 shrink-0" />
                      Riesgo vial
                    </div>
                  </TableCell>
                  <TableCell className="!p-2 !text-slate-700">Accidentes de tránsito, atropellos</TableCell>
                  <TableCell className="!p-2 !font-bold !text-rose-600">
                    <span className="inline-block w-2 h-2 rounded-full bg-rose-500 mr-1" />
                    Alto
                  </TableCell>
                  <TableCell className="!p-2 !text-slate-600">Conducción defensiva, PESV, monitoreo GPS, capacitación.</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="!p-2 !font-semibold">
                    <div className="flex items-center gap-1">
                      <Settings className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                      Mecánicos
                    </div>
                  </TableCell>
                  <TableCell className="!p-2 !text-slate-700">Fallas del vehículo, atrapamientos</TableCell>
                  <TableCell className="!p-2 !font-bold !text-amber-600">
                    <span className="inline-block w-2 h-2 rounded-full bg-amber-500 mr-1" />
                    Medio
                  </TableCell>
                  <TableCell className="!p-2 !text-slate-600">Inspección preoperacional, mantenimiento preventivo.</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="!p-2 !font-semibold">
                    <div className="flex items-center gap-1">
                      <User className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                      Ergonómicos
                    </div>
                  </TableCell>
                  <TableCell className="!p-2 !text-slate-700">Fatiga, lesiones osteomusculares</TableCell>
                  <TableCell className="!p-2 !font-bold !text-amber-600">
                    <span className="inline-block w-2 h-2 rounded-full bg-amber-500 mr-1" />
                    Medio
                  </TableCell>
                  <TableCell className="!p-2 !text-slate-600">Pausas activas, ajuste de silla, rotación de jornadas.</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="!p-2 !font-semibold">
                    <div className="flex items-center gap-1">
                      <HeartPulse className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                      Psicosociales
                    </div>
                  </TableCell>
                  <TableCell className="!p-2 !text-slate-700">Estrés, fatiga mental, agresiones</TableCell>
                  <TableCell className="!p-2 !font-bold !text-amber-600">
                    <span className="inline-block w-2 h-2 rounded-full bg-amber-500 mr-1" />
                    Medio
                  </TableCell>
                  <TableCell className="!p-2 !text-slate-600">Gestión de tiempos, apoyo psicosocial, pausas.</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>

          {/* 8. Restricciones y Condiciones Críticas */}
          <div className="lg:col-span-5 border border-slate-300 rounded-xl overflow-hidden shadow-sm">
            <div className="bg-slate-900 text-white px-3 py-1.5 font-bold text-[11px] uppercase tracking-wide flex items-center gap-1.5">
              <span className="w-4 h-4 rounded-full bg-emerald-500 text-slate-950 flex items-center justify-center text-[10px]">8</span>
              RESTRICCIONES Y CONDICIONES CRÍTICAS
            </div>
            <div className="p-3 bg-slate-50/50 space-y-2 text-[11px]">
              <div className="flex items-start gap-2">
                <Car className="w-4 h-4 text-slate-700 shrink-0 mt-0.5" />
                <span className="text-slate-800">Requiere licencia de conducción vigente y sin restricciones que limiten el tipo de vehículo.</span>
              </div>
              <div className="flex items-start gap-2">
                <Moon className="w-4 h-4 text-slate-700 shrink-0 mt-0.5" />
                <span className="text-slate-800">No apto para trabajo nocturno o jornadas que excedan lo permitido por ley (según normatividad vigente).</span>
              </div>
              <div className="flex items-start gap-2">
                <Ban className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                <span className="text-slate-800"><strong>Tolerancia cero:</strong> Prohibición estricta de consumo de alcohol y sustancias psicoactivas.</span>
              </div>
              <div className="flex items-start gap-2">
                <HeartPulse className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span className="text-slate-800">Requiere aptitud médica ocupacional vigente con énfasis osteomuscular y visual.</span>
              </div>
            </div>
          </div>

        </div>

        {/* ── FILA FINAL: INDICADORES, CONDICIONES E INTERACCIÓN DE PROCESOS ─ */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          
          {/* 9. Indicadores Asociados */}
          <div className="border border-slate-300 rounded-xl overflow-hidden shadow-sm">
            <div className="bg-slate-900 text-white px-3 py-1.5 font-bold text-[11px] uppercase tracking-wide flex items-center gap-1.5">
              <span className="w-4 h-4 rounded-full bg-emerald-500 text-slate-950 flex items-center justify-center text-[10px]">9</span>
              INDICADORES ASOCIADOS
            </div>
            <div className="p-2.5 space-y-1.5 text-[10px] bg-white">
              <div className="flex justify-between items-center border-b border-slate-100 pb-1">
                <span>Accidentalidad vial</span>
                <span className="font-bold text-slate-700">0 accidentes / Mensual</span>
              </div>
              <div className="flex justify-between items-center border-b border-slate-100 pb-1">
                <span>Cumplimiento de rutas</span>
                <span className="font-bold text-slate-700">≥ 98% / Diario</span>
              </div>
              <div className="flex justify-between items-center border-b border-slate-100 pb-1">
                <span>Inspección preoperacional</span>
                <span className="font-bold text-slate-700">100% / Diario</span>
              </div>
              <div className="flex justify-between items-center">
                <span>PQRS de usuarios</span>
                <span className="font-bold text-slate-700">0 quejas / Mensual</span>
              </div>
            </div>
          </div>

          {/* 10. Condiciones de Trabajo & EPP */}
          <div className="border border-slate-300 rounded-xl overflow-hidden shadow-sm">
            <div className="bg-slate-900 text-white px-3 py-1.5 font-bold text-[11px] uppercase tracking-wide flex items-center gap-1.5">
              <span className="w-4 h-4 rounded-full bg-emerald-500 text-slate-950 flex items-center justify-center text-[10px]">10</span>
              CONDICIONES DE TRABAJO
            </div>
            <div className="p-2.5 space-y-1.5 text-[10px] bg-slate-50/50 text-slate-800">
              <p><strong>Esfuerzo físico:</strong> Moderado (conducción prolongada, postura sentada).</p>
              <p><strong>Esfuerzo mental:</strong> Alto (atención constante al entorno vial).</p>
              <p><strong>Ambiente:</strong> Exposición a clima, tráfico y ruido exterior.</p>
              <p><strong>EPP obligatorio:</strong> Chaleco reflectivo, calzado antideslizante, protección visual.</p>
            </div>
          </div>

          {/* 11. Interacción de Procesos */}
          <div className="border border-slate-300 rounded-xl overflow-hidden shadow-sm">
            <div className="bg-slate-900 text-white px-3 py-1.5 font-bold text-[11px] uppercase tracking-wide flex items-center gap-1.5">
              <span className="w-4 h-4 rounded-full bg-emerald-500 text-slate-950 flex items-center justify-center text-[10px]">11</span>
              INTERACCIÓN DE PROCESOS
            </div>
            <div className="p-3 bg-white flex flex-col items-center justify-center text-center">
              <div className="relative w-24 h-24 flex items-center justify-center">
                {/* Círculo central */}
                <div className="w-12 h-12 rounded-full bg-slate-900 text-emerald-400 flex flex-col items-center justify-center z-10 shadow-lg border-2 border-emerald-500">
                  <User className="w-4 h-4" />
                  <span className="text-[6px] font-black uppercase tracking-tight mt-0.5">CARGO</span>
                </div>
                {/* Órbitas */}
                <div className="absolute inset-0 rounded-full border-2 border-dashed border-emerald-300/80" />
              </div>
              <div className="grid grid-cols-2 gap-1 text-[8px] font-bold text-slate-600 mt-1 w-full text-center">
                <span className="text-emerald-700">Operaciones</span>
                <span className="text-primary-500">SST / PESV</span>
                <span className="text-slate-700">Mantenimiento</span>
                <span className="text-amber-700">Usuarios / Pasajeros</span>
              </div>
            </div>
          </div>

        </div>

        {/* ── FOOTER OFICIAL: CONTROL DE DOCUMENTOS Y FIRMAS ────────────── */}
        <footer className="pt-3 border-t-2 border-slate-300 grid grid-cols-1 md:grid-cols-12 gap-3 items-center text-[10px]">
          <div className="md:col-span-5 flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <span className="font-bold text-slate-900 block">DOCUMENTO CONTROLADO EN FOSST V.I.D.A.</span>
              <p className="text-slate-500 text-[9px] leading-tight">
                Este perfil de cargo es un documento maestro. La evaluación de cumplimiento se realiza en el expediente del trabajador.
              </p>
            </div>
          </div>

          <div className="md:col-span-7 grid grid-cols-3 gap-2 text-center">
            <div className="p-2 border border-slate-200 rounded-lg bg-slate-50">
              <span className="text-[9px] text-slate-500 uppercase block font-bold">Elaboró</span>
              <span className="font-extrabold text-slate-800 text-[10px]">Talento Humano</span>
            </div>
            <div className="p-2 border border-slate-200 rounded-lg bg-slate-50">
              <span className="text-[9px] text-slate-500 uppercase block font-bold">Revisó</span>
              <span className="font-extrabold text-slate-800 text-[10px]">Coordinación SST</span>
            </div>
            <div className="p-2 border border-slate-200 rounded-lg bg-slate-50">
              <span className="text-[9px] text-slate-500 uppercase block font-bold">Aprobó</span>
              <span className="font-extrabold text-slate-800 text-[10px]">Gerencia General</span>
            </div>
          </div>
        </footer>

      </div>

      {/* ── MODAL HISTORIAL DE VERSIONES ─────────────────────────────── */}
      <Modal
        open={isVersionModalOpen}
        onClose={() => setIsVersionModalOpen(false)}
        title="Historial de Versiones y Control de Cambios"
        maxWidth="650px"
      >
        <div className="space-y-4 text-xs">
          <p className="text-slate-400">
            Registro inmutable de todas las revisiones y modificaciones realizadas a este perfil de cargo conforme a la norma ISO 9001 / SG-SST.
          </p>

          <div className="divide-y divide-slate-700 border border-slate-700 rounded-xl overflow-hidden bg-slate-900">
            {versiones && versiones.length > 0 ? (
              versiones.map((v: any) => (
                <div key={v.id} className="p-4 space-y-2 hover:bg-slate-800/60 transition">
                  <div className="flex justify-between items-center">
                    <span className="font-mono font-bold text-emerald-400 text-sm">
                      Versión {v.numero_version}.0
                    </span>
                    <span className="text-slate-400 text-[11px]">
                      {new Date(v.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-slate-300">
                    <strong>Motivo de cambio:</strong> {v.motivo_cambio || 'Actualización periódica del perfil de cargo'}
                  </p>
                  <p className="text-[11px] text-slate-400">
                    Modificado por: <strong className="text-slate-300">{v.creado_por || 'Responsable SST'}</strong>
                  </p>
                </div>
              ))
            ) : (
              <EmptyState
                title="Sin historial"
                description="Versión inicial vigente (v1.0)."
                icon={History}
                className="bg-transparent border-none text-slate-400"
              />
            )}
          </div>
        </div>
      </Modal>

    </div>
  )
}
