import { useState } from 'react'
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  FileCheck2,
  ShieldAlert,
  ArrowUpRight,
  Filter,
  ChevronRight,
  Building2,
  BookOpenCheck,
  FileText,
  Activity
} from 'lucide-react'
import { useDashboardResp } from '@/hooks/useApi'
import { LoadingSpinner, ErrorDisplay } from '@/components/ui/forms'
import { useNavigate } from 'react-router-dom'

// ── Badges cromáticos unificados por Ciclo PHVA ─────────────────────────────
const PHVA_CONFIG: Record<string, { label: string; tag: string; badgeClass: string }> = {
  Planear: {
    label: 'Planear',
    tag: 'P',
    badgeClass: 'bg-primary-50 text-primary-500 border-primary-200',
  },
  Hacer: {
    label: 'Hacer',
    tag: 'H',
    badgeClass: 'bg-amber-50 text-amber-900 border-amber-200',
  },
  Verificar: {
    label: 'Verificar',
    tag: 'V',
    badgeClass: 'bg-slate-100 text-slate-700 border-slate-200',
  },
  Actuar: {
    label: 'Actuar',
    tag: 'A',
    badgeClass: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  },
}

// ── Estado cromático unificado del Estándar ───────────────────────────────
function getEstadoBadge(estado: string, porcentaje: number) {
  if (estado === 'cumple' || porcentaje === 100) {
    return {
      label: 'Cumple',
      bgClass: 'bg-emerald-50 text-emerald-800 border-emerald-200',
      barClass: 'bg-emerald-600',
    }
  }
  if (estado === 'parcial' || (porcentaje > 0 && porcentaje < 100)) {
    return {
      label: 'Parcial',
      bgClass: 'bg-amber-50 text-amber-900 border-amber-200',
      barClass: 'bg-brand-500',
    }
  }
  if (estado === 'no_aplica') {
    return {
      label: 'No Aplica',
      bgClass: 'bg-slate-100 text-slate-700 border-slate-200',
      barClass: 'bg-slate-300',
    }
  }
  return {
    label: 'Pendiente',
    bgClass: 'bg-rose-50 text-rose-800 border-rose-200',
    barClass: 'bg-rose-500',
  }
}

export default function ResponsableDashboard() {
  const { data, isLoading, error, refetch } = useDashboardResp()
  const [cicloFiltro, setCicloFiltro] = useState<string>('TODOS')
  const navigate = useNavigate()

  if (isLoading) return <LoadingSpinner text="Cargando panel del responsable SG-SST..." />
  if (error || !data) return <ErrorDisplay message={(error as Error)?.message ?? 'Error cargando datos del dashboard'} onRetry={refetch} />

  const { kpis, estandares, planes_urgentes, empresa } = data

  const ciclos = ['Planear', 'Hacer', 'Verificar', 'Actuar']
  const estandaresFiltrados = cicloFiltro === 'TODOS'
    ? estandares
    : estandares.filter((e) => e.ciclo_phva === cicloFiltro)

  const estandaresPorCiclo = ciclos
    .map((c) => ({ ciclo: c, items: estandaresFiltrados.filter((e) => e.ciclo_phva === c) }))
    .filter((g) => g.items.length > 0)

  const tieneUrgentes = kpis.urgentes > 0

  return (
    <div className="animate-fade-in space-y-6 pb-12 text-slate-800 font-sans">
      {/* ── Encabezado Institucional con Azul Marino Único (#002D62) y FOSST Gold ── */}
      <div className="relative bg-primary-500 rounded-3xl p-6 sm:p-8 text-white overflow-hidden shadow-md">
        {/* Marca de agua limpia sin tonos oscuros extra */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-bold bg-brand-500 text-slate-950 border border-brand-400">
                <Building2 className="w-3.5 h-3.5" /> SG-SST Corporativo
              </span>
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-xs font-semibold bg-white/10 text-white border border-white/20">
                Res. 0312/2019 · Capítulo {empresa.capitulo_vigente}
              </span>
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-xs font-semibold bg-white/10 text-brand-300 border border-white/20">
                Decreto 1072/2015
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white font-sans">
              Mi Panel — Responsable SG-SST
            </h1>
            <p className="text-xs sm:text-sm text-slate-200 font-medium flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Empresa: <strong className="text-white font-bold">{empresa.nombre}</strong> · Evaluación {new Date().getFullYear()}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Reutilización 1 de FOSST Gold: Botón Principal de Acción */}
            <button
              onClick={() => navigate('/app/responsable/estandares')}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-slate-950 font-extrabold text-xs tracking-wide shadow-md transition-all active:scale-95"
            >
              <BookOpenCheck className="w-4 h-4" /> Diligenciar Estándares
            </button>
            <button
              onClick={() => navigate('/app/responsable/evidencias')}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white border border-white/20 font-bold text-xs transition-all"
            >
              <FileText className="w-4 h-4 text-brand-400" /> Soportes
            </button>
          </div>
        </div>
      </div>

      {/* ── Grilla Jerárquica de KPIs con Paleta Unificada ────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: Avance Global */}
        <div className="rounded-2xl bg-white border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-primary-500" /> Avance Global
            </span>
            <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-md border bg-amber-50 text-amber-900 border-amber-200">
              Meta: 85%
            </span>
          </div>

          <div className="flex items-baseline gap-2 mb-2">
            <span className="text-3xl sm:text-4xl font-black tracking-tight text-primary-500 font-mono">
              {kpis.avance_global}%
            </span>
          </div>

          {/* Reutilización 2 de FOSST Gold: Barra de Progreso Global */}
          <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden mb-2">
            <div
              className="h-full bg-brand-500 rounded-full transition-all duration-500"
              style={{ width: `${Math.max(kpis.avance_global, 3)}%` }}
            />
          </div>

          <p className="text-[11px] text-slate-500 font-medium">
            Cumplimiento consolidado del SG-SST
          </p>
        </div>

        {/* KPI 2: Cumplimiento */}
        <div className="rounded-2xl bg-white border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Cumplimiento
            </span>
            <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-md border bg-slate-100 text-slate-700 border-slate-200">
              Cap. {empresa.capitulo_vigente}
            </span>
          </div>

          <div className="flex items-baseline gap-2 mb-2">
            <span className="text-3xl font-black tracking-tight text-primary-500 font-mono">
              {kpis.cumplidos}
            </span>
            <span className="text-xs font-semibold text-slate-500">
              / {kpis.total_estandares} estándares
            </span>
          </div>

          <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden mb-2">
            <div
              className="h-full bg-emerald-600 rounded-full"
              style={{
                width: `${
                  kpis.total_estandares > 0
                    ? Math.round((kpis.cumplidos / kpis.total_estandares) * 100)
                    : 0
                }%`,
              }}
            />
          </div>

          <p className="text-[11px] text-slate-500 font-medium">
            Estándares con evaluación "Cumple"
          </p>
        </div>

        {/* KPI 3: Urgentes Hoy (Único uso del color de alerta #DC2626) */}
        <div
          className={`rounded-2xl p-5 shadow-sm transition-all border ${
            tieneUrgentes
              ? 'bg-rose-50 border-rose-200 text-rose-950'
              : 'bg-white border-slate-200 text-slate-900'
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 text-rose-800">
              <ShieldAlert className="w-3.5 h-3.5 text-rose-600" /> Urgentes Hoy
            </span>
            <span
              className={`inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-md border ${
                tieneUrgentes
                  ? 'bg-rose-100 text-rose-800 border-rose-300'
                  : 'bg-slate-100 text-slate-700 border-slate-200'
              }`}
            >
              {tieneUrgentes ? 'Acción Requerida' : 'Sin Alertas'}
            </span>
          </div>

          <div className="flex items-baseline gap-2 mb-2">
            <span
              className={`text-3xl sm:text-4xl font-black tracking-tight font-mono ${
                tieneUrgentes ? 'text-rose-600' : 'text-primary-500'
              }`}
            >
              {kpis.urgentes}
            </span>
            <span className="text-xs font-semibold text-slate-600">
              planes con vencimiento próximo
            </span>
          </div>

          <p className="text-[11px] text-slate-500 font-medium">
            {tieneUrgentes
              ? 'Requieren atención en Plan de Mejora'
              : 'Sin hallazgos en estado crítico'}
          </p>
        </div>

        {/* KPI 4: Soportes Digitales */}
        <div className="rounded-2xl bg-white border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
              <FileCheck2 className="w-3.5 h-3.5 text-primary-500" /> Soportes Digitales
            </span>
            <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-md border bg-amber-50 text-amber-900 border-amber-200">
              Auditables
            </span>
          </div>

          <div className="flex items-baseline gap-2 mb-2">
            <span className="text-3xl font-black tracking-tight text-primary-500 font-mono">
              {kpis.evidencias_cargadas}
            </span>
            <span className="text-xs font-semibold text-slate-500">archivos adjuntos</span>
          </div>

          <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden mb-2">
            <div
              className="h-full bg-primary-500 rounded-full"
              style={{
                width: `${Math.min(kpis.evidencias_cargadas * 5, 100)}%`,
              }}
            />
          </div>

          <p className="text-[11px] text-slate-500 font-medium">
            Evidencias subidas al sistema
          </p>
        </div>
      </div>

      {/* ── Contenido Principal: Matriz de Estándares & Panel Lateral ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Columna Izquierda (2 Cols): Matriz de Estándares Mínimos */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 sm:p-6">
            {/* Header de la Matriz de Estándares */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4 mb-5">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-black text-primary-500 tracking-tight">
                    Avance por Estándar Mínimo
                  </h2>
                  <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-md border bg-slate-100 text-primary-500 border-slate-200">
                    Capítulo {empresa.capitulo_vigente}
                  </span>
                </div>
                <p className="text-xs text-slate-500 font-medium mt-0.5">
                  Conformidad según Resolución 0312 de 2019
                </p>
              </div>

              {/* Selector / Filtro por Ciclo PHVA */}
              <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200 self-start sm:self-auto">
                <span className="text-[10px] font-black text-slate-500 px-2 uppercase tracking-wider flex items-center gap-1">
                  <Filter className="w-3 h-3" /> Ciclo:
                </span>
                {['TODOS', 'Planear', 'Hacer', 'Verificar', 'Actuar'].map((c) => (
                  <button
                    key={c}
                    onClick={() => setCicloFiltro(c)}
                    className={`px-2.5 py-1 text-xs font-bold rounded-lg transition-all ${
                      cicloFiltro === c
                        ? 'bg-primary-500 text-white shadow-sm'
                        : 'text-slate-700 hover:text-primary-500 hover:bg-slate-200/60'
                    }`}
                  >
                    {c === 'TODOS' ? 'Todos' : c[0]}
                  </button>
                ))}
              </div>
            </div>

            {/* Listado Agrupado por Ciclo PHVA */}
            {estandaresPorCiclo.length === 0 ? (
              <div className="text-center py-10 border border-dashed border-slate-200 rounded-2xl bg-slate-50">
                <BookOpenCheck className="w-10 h-10 text-slate-400 mx-auto mb-2" />
                <p className="text-xs font-bold text-slate-700">Sin estándares en este ciclo</p>
                <p className="text-[11px] text-slate-500 mt-1">Selecciona otro filtro para visualizar los ítems</p>
              </div>
            ) : (
              <div className="space-y-6">
                {estandaresPorCiclo.map(({ ciclo, items }) => {
                  const cfg = PHVA_CONFIG[ciclo] ?? PHVA_CONFIG['Planear']
                  return (
                    <div key={ciclo} className="space-y-3">
                      {/* Subencabezado de Sección de Ciclo */}
                      <div className="flex items-center gap-2 border-b border-slate-100 pb-2">
                        <span className={`inline-flex items-center justify-center w-5 h-5 text-xs font-extrabold rounded border ${cfg.badgeClass}`}>
                          {cfg.tag}
                        </span>
                        <h3 className="text-xs font-black uppercase tracking-wider text-primary-500">
                          {ciclo} ({items.length} estándares)
                        </h3>
                      </div>

                      {/* Items del Ciclo */}
                      <div className="space-y-2">
                        {items.map((e) => {
                          const estInfo = getEstadoBadge(e.estado, e.porcentaje ?? 0)
                          return (
                            <div
                              key={e.estandar_id}
                              onClick={() => navigate('/app/responsable/estandares')}
                              className="group flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-xl border border-slate-200 bg-white hover:border-primary-300 hover:shadow-sm transition-all cursor-pointer"
                            >
                              <div className="flex items-start gap-3 min-w-0 flex-1">
                                <span className="font-mono text-xs font-black text-primary-500 bg-slate-100 px-2 py-1 rounded-md flex-shrink-0 border border-slate-200">
                                  {e.codigo}
                                </span>

                                <div className="min-w-0 flex-1">
                                  <p className="text-xs font-bold text-slate-900 truncate group-hover:text-primary-500 transition-colors">
                                    {e.nombre}
                                  </p>
                                  <div className="flex items-center gap-3 text-[11px] text-slate-500 mt-1 font-medium">
                                    <span>Puntaje Máx: <strong>{e.puntaje_maximo} pts</strong></span>
                                    {e.evidencias > 0 && (
                                      <span className="inline-flex items-center gap-1 text-primary-500 font-bold">
                                        <FileText className="w-3 h-3 text-brand-500" /> {e.evidencias} soporte(s)
                                      </span>
                                    )}
                                  </div>
                                </div>
                              </div>

                              <div className="flex items-center gap-4 flex-shrink-0 sm:w-48 justify-between sm:justify-end">
                                <div className="w-24 sm:w-28 space-y-1">
                                  <div className="flex justify-between text-[11px] font-bold text-slate-700">
                                    <span>{e.porcentaje ?? 0}%</span>
                                    <span className="text-[10px] text-slate-400 font-normal">
                                      {e.puntaje ?? 0}/{e.puntaje_maximo}
                                    </span>
                                  </div>
                                  <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                    <div
                                      className={`h-full rounded-full transition-all ${estInfo.barClass}`}
                                      style={{ width: `${Math.max(e.porcentaje ?? 0, 2)}%` }}
                                    />
                                  </div>
                                </div>

                                <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-md border ${estInfo.bgClass}`}>
                                  {estInfo.label}
                                </span>

                                <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-primary-500 transition-colors hidden sm:block" />
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        {/* Columna Derecha (1 Col): Tareas Urgentes & Desglose Regulatorio */}
        <div className="space-y-6">
          {/* Tarjeta de Tareas Urgentes */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
              <div>
                <h3 className="text-sm font-black text-primary-500 flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-rose-600" /> Tareas Urgentes
                </h3>
                <p className="text-[11px] text-slate-500 font-medium">Plan de mejoramiento con fecha crítica</p>
              </div>
              <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-md border bg-rose-50 text-rose-800 border-rose-200">
                {planes_urgentes.length}
              </span>
            </div>

            {planes_urgentes.length === 0 ? (
              <div className="text-center py-8 bg-emerald-50 border border-emerald-200 rounded-xl">
                <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
                <p className="text-xs font-bold text-emerald-900">Al día en planes de mejora</p>
                <p className="text-[11px] text-emerald-700 mt-0.5 font-medium">Sin tareas pendientes en estado urgente</p>
              </div>
            ) : (
              <div className="space-y-3">
                {planes_urgentes.map((u) => (
                  <div
                    key={u.id}
                    className="p-3.5 rounded-xl border bg-rose-50 border-rose-200 text-rose-950"
                  >
                    <div className="flex items-start gap-2.5">
                      <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-bold tracking-tight text-slate-900 leading-snug">
                          {u.accion}
                        </p>
                        <div className="flex items-center gap-2 text-[10px] font-semibold mt-1.5 text-slate-600">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3 text-slate-400" />
                            Vence: <strong>{new Date(u.fecha_limite).toLocaleDateString('es-CO')}</strong>
                          </span>
                          <span className="inline-flex items-center gap-1 text-[10px] font-extrabold px-1.5 py-0.2 rounded uppercase bg-rose-100 text-rose-800 border border-rose-300">
                            {u.prioridad}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Tarjeta de Resumen Estadístico — Mismo Azul Marino Principal (#002D62) */}
          <div className="bg-primary-500 text-white rounded-2xl border border-primary-600 p-5 shadow-md relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-brand-500/10 rounded-bl-full pointer-events-none" />

            <h3 className="text-xs font-black uppercase tracking-widest text-brand-400 mb-1">
              Desglose Regulatorio
            </h3>
            <p className="text-xs text-slate-200 font-medium mb-4">
              Estado de los {kpis.total_estandares} estándares aplicables
            </p>

            <div className="space-y-2.5">
              {[
                { label: 'Cumplidos', count: kpis.cumplidos, badgeClass: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' },
                { label: 'Pendientes / Sin Respuesta', count: kpis.total_estandares - kpis.cumplidos - kpis.urgentes, badgeClass: 'bg-white/10 text-slate-200 border-white/20' },
                { label: 'Críticos / Con Alerta', count: kpis.urgentes, badgeClass: 'bg-rose-500/20 text-rose-300 border-rose-500/40' },
              ].map((r) => (
                <div key={r.label} className="flex items-center justify-between p-2.5 rounded-xl bg-white/5 border border-white/10">
                  <span className="text-xs font-semibold text-slate-100">{r.label}</span>
                  <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded-md border ${r.badgeClass}`}>
                    {r.count}
                  </span>
                </div>
              ))}
            </div>

            <button
              onClick={() => navigate('/app/responsable/autoevaluacion')}
              className="w-full mt-5 py-2.5 px-4 rounded-xl bg-brand-500 hover:bg-brand-600 text-slate-950 font-extrabold text-xs flex items-center justify-center gap-2 transition-all shadow-sm"
            >
              Ver Informe de Autoevaluación <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
