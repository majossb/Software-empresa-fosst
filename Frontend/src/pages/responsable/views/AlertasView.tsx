import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Button, EmptyState } from '@/components/ui'
import { LoadingSpinner } from '@/components/ui/forms'
import {
  alertasService,
  ReglaAlerta,
  Notificacion,
  NotificacionResumen,
} from '@/services/alertas.service'
import { gestionHumanaService, Trabajador } from '@/services/gestion-humana.service'
import {
  Bell, Play, Clock, CheckCircle2,
  AlertTriangle, ShieldAlert, Sparkles, Filter,
  Check, Eye, ArrowRight, BookOpen, GraduationCap,
  ChevronDown, ChevronUp, User, Search, RefreshCw,
  FolderCheck, ShieldCheck
} from 'lucide-react'

export default function AlertasView() {
  const navigate = useNavigate()

  // Estado general
  const [notificaciones, setNotificaciones] = useState<Notificacion[]>([])
  const [resumen, setResumen] = useState<NotificacionResumen | null>(null)
  const [reglas, setReglas] = useState<ReglaAlerta[]>([])
  const [trabajadores, setTrabajadores] = useState<Trabajador[]>([])

  const [loading, setLoading] = useState(true)
  const [loadingList, setLoadingList] = useState(false)
  const [ejecutando, setEjecutando] = useState(false)
  const [mensajeEjecucion, setMensajeEjecucion] = useState<string | null>(null)
  const [showReglas, setShowReglas] = useState(false)

  // Filtros
  const [filtroEstado, setFiltroEstado] = useState<'todas' | 'nueva' | 'vista' | 'resuelta'>('todas')
  const [filtroTipo, setFiltroTipo] = useState<string>('todos')
  const [filtroTrabajador, setFiltroTrabajador] = useState<string>('')
  const [filtroCargo, setFiltroCargo] = useState<string>('')

  useEffect(() => {
    cargarDatosIniciales()
  }, [])

  useEffect(() => {
    cargarNotificaciones()
  }, [filtroEstado, filtroTipo, filtroTrabajador, filtroCargo])

  const cargarDatosIniciales = async () => {
    setLoading(true)
    try {
      const [resReglas, resResumen, resTrabajadores] = await Promise.all([
        alertasService.getReglas(),
        alertasService.getResumen(),
        gestionHumanaService.getTrabajadores(),
      ])
      setReglas(Array.isArray(resReglas) ? resReglas : resReglas.results || [])
      setResumen(resResumen)
      setTrabajadores(Array.isArray(resTrabajadores) ? resTrabajadores : (resTrabajadores as any).results || [])
      await cargarNotificaciones()
    } catch (e) {
      console.error('Error cargando datos iniciales de alertas:', e)
    } finally {
      setLoading(false)
    }
  }

  const cargarNotificaciones = async () => {
    setLoadingList(true)
    try {
      const params: any = {}
      if (filtroEstado === 'nueva') params.leida = false
      if (filtroEstado === 'vista') params.leida = true
      if (filtroTipo !== 'todos') params.tipo_alerta = filtroTipo
      if (filtroTrabajador) params.trabajador_id = filtroTrabajador
      if (filtroCargo.trim()) params.cargo = filtroCargo.trim()

      const res = await alertasService.getNotificaciones(params)
      let list = Array.isArray(res) ? res : res.results || []

      // Filtro local adicional para estado "resuelta" si aplica
      if (filtroEstado === 'resuelta') {
        list = list.filter((n) => n.metadatos?.resuelta === true)
      } else if (filtroEstado === 'vista') {
        list = list.filter((n) => !n.metadatos?.resuelta)
      } else if (filtroEstado === 'nueva') {
        list = list.filter((n) => !n.metadatos?.resuelta)
      }

      setNotificaciones(list)
    } catch (e) {
      console.error('Error cargando notificaciones:', e)
    } finally {
      setLoadingList(false)
    }
  }

  const handleEjecutarRevision = async () => {
    setEjecutando(true)
    setMensajeEjecucion(null)
    try {
      const res = await alertasService.ejecutarRevision()
      setMensajeEjecucion(res.mensaje)
      // Recargar notificaciones y resumen
      const [resumenActualizado] = await Promise.all([
        alertasService.getResumen(),
        cargarNotificaciones(),
      ])
      setResumen(resumenActualizado)
    } catch (e: any) {
      setMensajeEjecucion('Error ejecutando revisión de vencimientos.')
    } finally {
      setEjecutando(false)
    }
  }

  const handleMarcarLeida = async (id: string) => {
    try {
      await alertasService.marcarLeida(id)
      setNotificaciones((prev) =>
        prev.map((n) => (n.id === id ? { ...n, leida: true } : n))
      )
      const resResumen = await alertasService.getResumen()
      setResumen(resResumen)
    } catch (e) {
      console.error('Error marcando como leída:', e)
    }
  }

  const handleMarcarResuelta = async (id: string) => {
    try {
      await alertasService.marcarResuelta(id)
      setNotificaciones((prev) =>
        prev.map((n) =>
          n.id === id
            ? {
                ...n,
                leida: true,
                metadatos: { ...(n.metadatos || {}), resuelta: true },
              }
            : n
        )
      )
      const resResumen = await alertasService.getResumen()
      setResumen(resResumen)
    } catch (e) {
      console.error('Error marcando como resuelta:', e)
    }
  }

  // Métricas calculadas
  const counts = useMemo(() => {
    const total = notificaciones.length
    const criticas = notificaciones.filter((n) => n.nivel === 'critico').length
    const noLeidas = notificaciones.filter((n) => !n.leida && !n.metadatos?.resuelta).length
    const resueltas = notificaciones.filter((n) => n.metadatos?.resuelta).length
    return { total, criticas, noLeidas, resueltas }
  }, [notificaciones])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Bell className="w-6 h-6 text-primary-600" />
            Alertas de Formación y Vencimientos
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Monitoreo preventivo de cursos obligatorios, evaluaciones de competencia, contratos y exámenes.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            onClick={cargarNotificaciones}
            disabled={loadingList}
            className="flex items-center gap-1.5 text-xs py-2"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingList ? 'animate-spin' : ''}`} />
            Actualizar
          </Button>
          <Button
            variant="primary"
            onClick={handleEjecutarRevision}
            disabled={ejecutando}
            className="flex items-center gap-2 text-xs py-2 shadow-sm"
          >
            <Play className={`w-3.5 h-3.5 ${ejecutando ? 'animate-spin' : ''}`} />
            {ejecutando ? 'Evaluando Reglas...' : 'Ejecutar Revisión Ahora'}
          </Button>
        </div>
      </div>

      {/* Execution Feedback */}
      {mensajeEjecucion && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span>{mensajeEjecucion}</span>
          </div>
          <button
            onClick={() => setMensajeEjecucion(null)}
            className="text-emerald-600 hover:text-emerald-900 font-bold ml-4"
          >
            ✕
          </button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4 border-l-4 border-l-primary-500">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Total Alertas</span>
            <Bell className="w-4 h-4 text-primary-500" />
          </div>
          <p className="text-2xl font-bold text-slate-900 mt-2">{resumen?.total ?? counts.total}</p>
          <span className="text-[11px] text-slate-400">En registro</span>
        </Card>

        <Card className="p-4 border-l-4 border-l-rose-500">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-rose-600">Críticas (Urgentes)</span>
            <ShieldAlert className="w-4 h-4 text-rose-500" />
          </div>
          <p className="text-2xl font-bold text-rose-700 mt-2">
            {resumen?.por_nivel?.critico ?? counts.criticas}
          </p>
          <span className="text-[11px] text-rose-500 font-medium">Cursos vencidos / suspensión</span>
        </Card>

        <Card className="p-4 border-l-4 border-l-amber-500">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-amber-600">Nuevas (Sin leer)</span>
            <Clock className="w-4 h-4 text-amber-500" />
          </div>
          <p className="text-2xl font-bold text-amber-700 mt-2">
            {resumen?.no_leidas ?? counts.noLeidas}
          </p>
          <span className="text-[11px] text-amber-600 font-medium">Requieren atención</span>
        </Card>

        <Card className="p-4 border-l-4 border-l-emerald-500">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-600">Resueltas</span>
            <FolderCheck className="w-4 h-4 text-emerald-500" />
          </div>
          <p className="text-2xl font-bold text-emerald-700 mt-2">{counts.resueltas}</p>
          <span className="text-[11px] text-emerald-600 font-medium">Atendidas / renovadas</span>
        </Card>
      </div>

      {/* Filter Bar */}
      <Card className="p-4 bg-slate-50 border-slate-200">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Estado */}
          <div>
            <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
              Estado
            </label>
            <select
              value={filtroEstado}
              onChange={(e) => setFiltroEstado(e.target.value as any)}
              className="w-full text-xs rounded-lg border-slate-300 bg-white py-1.5 px-2.5 text-slate-700 focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
            >
              <option value="todas">Todos los estados</option>
              <option value="nueva">Nuevas (no leídas)</option>
              <option value="vista">Vistas (leídas)</option>
              <option value="resuelta">Resueltas</option>
            </select>
          </div>

          {/* Tipo de Alerta */}
          <div>
            <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
              Tipo de Alerta
            </label>
            <select
              value={filtroTipo}
              onChange={(e) => setFiltroTipo(e.target.value)}
              className="w-full text-xs rounded-lg border-slate-300 bg-white py-1.5 px-2.5 text-slate-700 focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
            >
              <option value="todos">Todos los tipos</option>
              <option value="FORM_CURSO_VENCIDO">Curso Vencido (Crítico)</option>
              <option value="FORM_CURSO_POR_VENCER_30D">Curso por Vencer (30d)</option>
              <option value="FORM_CURSO_SIN_REGISTRAR">Curso Sin Registrar</option>
              <option value="FORM_EVALUACION_COMPETENCIA_PENDIENTE">Brecha en Competencia</option>
              <option value="VENC_EXAMEN_MEDICO_30D">Examen Médico</option>
              <option value="VENC_LICENCIA_CONDUCCION_30D">Licencia Conducción</option>
              <option value="VENC_CONTRATO_60D">Vencimiento Contrato</option>
            </select>
          </div>

          {/* Trabajador */}
          <div>
            <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
              Trabajador
            </label>
            <select
              value={filtroTrabajador}
              onChange={(e) => setFiltroTrabajador(e.target.value)}
              className="w-full text-xs rounded-lg border-slate-300 bg-white py-1.5 px-2.5 text-slate-700 focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
            >
              <option value="">Todos los trabajadores</option>
              {trabajadores.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.nombre} ({t.documento})
                </option>
              ))}
            </select>
          </div>

          {/* Cargo */}
          <div>
            <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
              Cargo (búsqueda)
            </label>
            <div className="relative">
              <input
                type="text"
                placeholder="Ej: Inspector, Conductor..."
                value={filtroCargo}
                onChange={(e) => setFiltroCargo(e.target.value)}
                className="w-full text-xs rounded-lg border-slate-300 bg-white py-1.5 pl-8 pr-2.5 text-slate-700 focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
              />
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
            </div>
          </div>
        </div>
      </Card>

      {/* Alert Feed */}
      <Card className="p-4 space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-slate-100">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Bell className="w-4 h-4 text-primary-500" />
            Listado de Alertas Activas ({notificaciones.length})
          </h3>
          {(filtroEstado !== 'todas' || filtroTipo !== 'todos' || filtroTrabajador || filtroCargo) && (
            <span className="text-xs text-primary-600 font-medium bg-primary-50 px-2 py-0.5 rounded-full">
              Filtros activos
            </span>
          )}
        </div>

        {loadingList ? (
          <LoadingSpinner text="Cargando alertas..." />
        ) : notificaciones.length === 0 ? (
          <EmptyState
            title="Sin alertas registradas"
            description="No hay alertas que coincidan con los filtros seleccionados o el sistema está al día."
          />
        ) : (
          <div className="space-y-3">
            {notificaciones.map((notif) => {
              const meta = notif.metadatos || {}
              const esResuelta = meta.resuelta === true
              const esCritico = notif.nivel === 'critico'
              const esImportante = notif.nivel === 'importante'
              const esFormacion = meta.tipo_alerta?.startsWith('FORM_')

              return (
                <div
                  key={notif.id}
                  className={`p-4 rounded-xl border transition-all ${
                    esResuelta
                      ? 'bg-slate-50/70 border-slate-200 opacity-75'
                      : esCritico
                      ? 'bg-rose-50/40 border-rose-200 hover:border-rose-300 shadow-sm'
                      : esImportante
                      ? 'bg-amber-50/30 border-amber-200 hover:border-amber-300'
                      : 'bg-white border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
                    {/* Contenido principal */}
                    <div className="space-y-2 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        {/* Nivel badge */}
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                            esCritico
                              ? 'bg-rose-600 text-white'
                              : esImportante
                              ? 'bg-amber-500 text-white'
                              : 'bg-slate-200 text-slate-700'
                          }`}
                        >
                          {notif.nivel_display || notif.nivel}
                        </span>

                        {/* Estado badge */}
                        {esResuelta ? (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 flex items-center gap-1">
                            <Check className="w-3 h-3" /> Resuelta
                          </span>
                        ) : notif.leida ? (
                          <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 flex items-center gap-1">
                            <Eye className="w-3 h-3" /> Vista
                          </span>
                        ) : (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-primary-100 text-primary-700 animate-pulse">
                            Nueva
                          </span>
                        )}

                        {/* Tipo de alerta */}
                        {meta.tipo_alerta && (
                          <span className="font-mono text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                            {meta.tipo_alerta}
                          </span>
                        )}

                        {/* Cargo tag */}
                        {meta.cargo && (
                          <span className="text-[11px] font-medium text-slate-600 bg-white border border-slate-200 px-2 py-0.5 rounded-md">
                            Cargo: <strong>{meta.cargo}</strong>
                          </span>
                        )}
                      </div>

                      {/* Mensaje */}
                      <p className="text-xs font-medium text-slate-800 leading-relaxed">
                        {notif.mensaje}
                      </p>

                      {/* Timestamp */}
                      <div className="flex items-center gap-1 text-[11px] text-slate-400">
                        <Clock className="w-3 h-3" />
                        <span>{new Date(notif.created_at).toLocaleString('es-CO')}</span>
                      </div>
                    </div>

                    {/* Acciones directas de formación */}
                    <div className="flex flex-wrap sm:flex-nowrap items-center gap-2 pt-2 md:pt-0 border-t md:border-t-0 border-slate-100">
                      {/* Botón directo: Registrar Curso */}
                      {meta.curso_id && (
                        <Button
                          variant="secondary"
                          onClick={() => {
                            const params = new URLSearchParams()
                            if (meta.trabajador_id) params.set('trabajador_id', meta.trabajador_id)
                            if (meta.curso_id) params.set('curso_id', meta.curso_id)
                            navigate(`/app/responsable/formacion?${params.toString()}`)
                          }}
                          className="text-xs py-1.5 px-3 flex items-center gap-1 text-primary-700 border-primary-200 hover:bg-primary-50"
                        >
                          <GraduationCap className="w-3.5 h-3.5" />
                          Registrar Curso
                        </Button>
                      )}

                      {/* Botón directo: Programar Capacitación */}
                      {meta.curso_id && (
                        <Button
                          variant="secondary"
                          onClick={() => {
                            const params = new URLSearchParams()
                            if (meta.curso_id) params.set('curso_id', meta.curso_id)
                            if (meta.trabajador_id) params.set('trabajador_id', meta.trabajador_id)
                            navigate(`/app/responsable/capacitaciones?${params.toString()}`)
                          }}
                          className="text-xs py-1.5 px-3 flex items-center gap-1 text-indigo-700 border-indigo-200 hover:bg-indigo-50"
                        >
                          <BookOpen className="w-3.5 h-3.5" />
                          Programar Capacitación
                        </Button>
                      )}

                      {/* Botón directo: Evaluar Competencia */}
                      {meta.tipo_alerta === 'FORM_EVALUACION_COMPETENCIA_PENDIENTE' && (
                        <Button
                          variant="secondary"
                          onClick={() => {
                            const params = new URLSearchParams({ tab: 'competencias' })
                            if (meta.trabajador_id) params.set('trabajador_id', meta.trabajador_id)
                            navigate(`/app/responsable/formacion?${params.toString()}`)
                          }}
                          className="text-xs py-1.5 px-3 flex items-center gap-1 text-emerald-700 border-emerald-200 hover:bg-emerald-50"
                        >
                          <ShieldCheck className="w-3.5 h-3.5" />
                          Evaluar Competencia
                        </Button>
                      )}

                      {/* Marcar como leída / vista */}
                      {!notif.leida && !esResuelta && (
                        <Button
                          variant="ghost"
                          onClick={() => handleMarcarLeida(notif.id)}
                          className="text-xs py-1.5 px-2.5 text-slate-500 hover:text-slate-700"
                          title="Marcar como vista"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </Button>
                      )}

                      {/* Marcar como resuelta */}
                      {!esResuelta && (
                        <Button
                          variant="ghost"
                          onClick={() => handleMarcarResuelta(notif.id)}
                          className="text-xs py-1.5 px-2.5 text-emerald-600 hover:text-emerald-800 hover:bg-emerald-50"
                          title="Marcar alerta como resuelta"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </Card>

      {/* Reglas de Alerta Configuradas (Acordeón colapsable) */}
      <Card className="p-4 space-y-4">
        <button
          onClick={() => setShowReglas(!showReglas)}
          className="w-full flex items-center justify-between text-left pb-2 border-b border-slate-100"
        >
          <div className="flex items-center gap-2">
            <Bell className="w-4 h-4 text-slate-500" />
            <h3 className="text-sm font-bold text-slate-800">
              Reglas de Alerta Configuradas en el Motor ({reglas.length})
            </h3>
          </div>
          <div className="flex items-center gap-1 text-xs text-slate-500">
            <span>{showReglas ? 'Ocultar' : 'Ver reglas'}</span>
            {showReglas ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </button>

        {showReglas && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
            {reglas.map((r) => (
              <div
                key={r.id}
                className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 space-y-2 text-xs"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="font-mono text-[10px] font-bold text-primary-600 uppercase">
                      {r.codigo}
                    </span>
                    <h4 className="text-xs font-bold text-slate-900 mt-0.5">{r.nombre}</h4>
                  </div>
                  <span
                    className={`text-[9px] font-bold px-1.5 py-0.5 rounded capitalize ${
                      r.nivel_criticidad === 'critico'
                        ? 'bg-rose-100 text-rose-700'
                        : r.nivel_criticidad === 'importante'
                        ? 'bg-amber-100 text-amber-700'
                        : 'bg-slate-200 text-slate-700'
                    }`}
                  >
                    {r.nivel_criticidad_display || r.nivel_criticidad}
                  </span>
                </div>

                <p className="text-[11px] text-slate-600 bg-white p-2 rounded border border-slate-100 font-mono">
                  "{r.mensaje_template}"
                </p>

                <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-200/60">
                  <span>
                    Modelo: <strong>{r.modelo_origen}</strong>
                  </span>
                  <span>
                    Anticipación: <strong>{r.dias_anticipacion}d</strong>
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
