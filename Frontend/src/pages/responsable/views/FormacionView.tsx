import React, { useState, useEffect, useMemo, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Card, Button, EmptyState } from '@/components/ui'
import { LoadingSpinner } from '@/components/ui/forms'
import {
  formacionService,
  EvaluacionCompetencia,
  FormacionResumen,
  MatrizTrabajadorResponse,
  MatrizFormacionResponse,
  MatrizFormacionItem,
  CompetenciaMatriz,
  RegistroFormacion,
  CursoFormacion,
  FormacionCursosResumen,
} from '@/services/formacion.service'
import { gestionHumanaService, Trabajador } from '@/services/gestion-humana.service'
import { modulo0Service, Proceso } from '@/services/modulo0.service'
import { modulo1Service, PerfilCargoListItem } from '@/services/modulo1.service'
import { capacitacionService, Capacitacion } from '@/services/capacitacion.service'
import { hbseoService, Brecha } from '@/services/hbseo.service'
import { useAuth } from '@/store/auth.context'
import { RegistrarCursoModal } from '@/components/formacion/RegistrarCursoModal'
import { NuevaEvaluacionModal } from '@/components/formacion/NuevaEvaluacionModal'
import { DetalleCompetenciaDrawer } from '@/components/formacion/DetalleCompetenciaDrawer'
import { DonutProgress, StackedBar } from '@/components/formacion/ProgressCharts'
import { ExportSheet } from '@/components/ui/ExportSheet'
import {
  GraduationCap, Award, TrendingUp, AlertCircle,
  Plus, CheckCircle2, ArrowRight, User, ShieldCheck,
  Clock, AlertTriangle, XCircle, FileText, ExternalLink,
  BookOpen, Zap, Filter, Download, Printer, Search,
  RefreshCw, Users, Check, Calendar, ChevronRight
} from 'lucide-react'

type TabKey = 'resumen' | 'matriz' | 'evaluaciones' | 'cursos' | 'capacitaciones'

export default function FormacionView() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { user } = useAuth()

  // Tab activo sincronizado con query param ?tab=
  const initialTab = (searchParams.get('tab') as TabKey) || 'resumen'
  const [activeTab, setActiveTab] = useState<TabKey>(initialTab)

  // Estado general
  const [loading, setLoading] = useState(true)
  const [evaluaciones, setEvaluaciones] = useState<EvaluacionCompetencia[]>([])
  const [resumen, setResumen] = useState<FormacionResumen | null>(null)
  const [resumenCursos, setResumenCursos] = useState<FormacionCursosResumen | null>(null)
  const [trabajadores, setTrabajadores] = useState<Trabajador[]>([])
  const [perfilesCargo, setPerfilesCargo] = useState<PerfilCargoListItem[]>([])
  const [procesos, setProcesos] = useState<Proceso[]>([])
  const [capacitaciones, setCapacitaciones] = useState<Capacitacion[]>([])
  const [brechas, setBrechas] = useState<Brecha[]>([])
  const [registrosFormacion, setRegistrosFormacion] = useState<RegistroFormacion[]>([])

  // Filtros de la Matriz de Competencias
  const [filtroProceso, setFiltroProceso] = useState<string>('')
  const [filtroCargo, setFiltroCargo] = useState<string>('')
  const [filtroTrabajador, setFiltroTrabajador] = useState<string>(searchParams.get('trabajador_id') || '')

  // Matrices por trabajador individual (cargadas dinámicamente)
  const [matrizTrabajadorMap, setMatrizTrabajadorMap] = useState<Record<string, MatrizTrabajadorResponse>>({})
  const [matrizFormacionMap, setMatrizFormacionMap] = useState<Record<string, MatrizFormacionResponse>>({})
  const [loadingMatrices, setLoadingMatrices] = useState(false)

  // Modales y Drawers
  const [showCursoModal, setShowCursoModal] = useState(false)
  const [showEvaluacionModal, setShowEvaluacionModal] = useState(false)
  const [preselectedTrabajadorId, setPreselectedTrabajadorId] = useState<string | undefined>(
    searchParams.get('trabajador_id') || undefined
  )
  const [preselectedCursoId, setPreselectedCursoId] = useState<string | undefined>(
    searchParams.get('curso_id') || undefined
  )
  const [preselectedCompetenciaId, setPreselectedCompetenciaId] = useState<string | undefined>(undefined)

  // Drawer de detalle de celda matricial
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [selectedCeldaTrabajador, setSelectedCeldaTrabajador] = useState<{ id: string; nombre: string; documento?: string; cargo?: string } | null>(null)
  const [selectedCeldaCompetencia, setSelectedCeldaCompetencia] = useState<CompetenciaMatriz | null>(null)

  // Referencia para exportación imprimible
  const exportRef = useRef<HTMLDivElement>(null)

  // Actualizar tab si cambia el query param
  useEffect(() => {
    const t = searchParams.get('tab') as TabKey
    if (t && ['resumen', 'matriz', 'evaluaciones', 'cursos', 'capacitaciones'].includes(t)) {
      setActiveTab(t)
    }
    const tId = searchParams.get('trabajador_id')
    if (tId) {
      setFiltroTrabajador(tId)
      setPreselectedTrabajadorId(tId)
    }
    const cId = searchParams.get('curso_id')
    if (cId) {
      setPreselectedCursoId(cId)
      setShowCursoModal(true)
    }
  }, [searchParams])

  const handleTabChange = (tab: TabKey) => {
    setActiveTab(tab)
    const newParams = new URLSearchParams(searchParams)
    newParams.set('tab', tab)
    setSearchParams(newParams)
  }

  useEffect(() => {
    cargarDatosGenerales()
  }, [])

  const cargarDatosGenerales = async () => {
    setLoading(true)
    try {
      const [
        resEvals,
        resResumen,
        resResumenCursos,
        resTrabajadores,
        resPerfiles,
        resProcesos,
        resCapacitaciones,
        resBrechas,
        resRegistros,
      ] = await Promise.all([
        formacionService.getEvaluaciones(),
        formacionService.getResumen(),
        formacionService.getResumenFormacionCursos().catch(() => null),
        gestionHumanaService.getTrabajadores(),
        modulo1Service.listPerfiles().catch(() => []),
        modulo0Service.listProcesos().catch(() => ({ estrategico: [], misional: [], apoyo: [] })),
        capacitacionService.listar().catch(() => ({ capacitaciones: [], resumen: { total: 0, programadas: 0, realizadas: 0, canceladas: 0 } })),
        hbseoService.getBrechas().catch(() => []),
        formacionService.getRegistros().catch(() => []),
      ])

      setEvaluaciones(Array.isArray(resEvals) ? resEvals : (resEvals as any).results || [])
      setResumen(resResumen)
      setResumenCursos(resResumenCursos)
      const trabList = Array.isArray(resTrabajadores) ? resTrabajadores : (resTrabajadores as any).results || []
      setTrabajadores(trabList)
      setPerfilesCargo(Array.isArray(resPerfiles) ? resPerfiles : (resPerfiles as any).results || [])

      const procList: Proceso[] = [
        ...((resProcesos as any).estrategico || []),
        ...((resProcesos as any).misional || []),
        ...((resProcesos as any).apoyo || []),
      ]
      setProcesos(procList)

      setCapacitaciones(resCapacitaciones.capacitaciones || [])
      setBrechas(Array.isArray(resBrechas) ? resBrechas : (resBrechas as any).results || [])
      setRegistrosFormacion(Array.isArray(resRegistros) ? resRegistros : (resRegistros as any).results || [])

      // Cargar matrices de los trabajadores activos
      await cargarMatricesParaTrabajadores(trabList.slice(0, 15))
    } catch (e) {
      console.error('Error cargando datos de Formación:', e)
    } finally {
      setLoading(false)
    }
  }

  const cargarMatricesParaTrabajadores = async (list: Trabajador[]) => {
    setLoadingMatrices(true)
    const newMCCMap: Record<string, MatrizTrabajadorResponse> = { ...matrizTrabajadorMap }
    const newFormMap: Record<string, MatrizFormacionResponse> = { ...matrizFormacionMap }

    await Promise.all(
      list.map(async (t) => {
        if (!newMCCMap[t.id]) {
          try {
            const dataMCC = await formacionService.getMatrizTrabajador(t.id)
            newMCCMap[t.id] = dataMCC
          } catch (_) {}
        }
        if (!newFormMap[t.id]) {
          try {
            const dataForm = await formacionService.getMatrizFormacionTrabajador(t.id)
            newFormMap[t.id] = dataForm
          } catch (_) {}
        }
      })
    )
    setMatrizTrabajadorMap(newMCCMap)
    setMatrizFormacionMap(newFormMap)
    setLoadingMatrices(false)
  }

  // Filtrado de trabajadores en Matriz de Competencias
  const trabajadoresFiltrados = useMemo(() => {
    return trabajadores.filter((t) => {
      if (filtroTrabajador && t.id !== filtroTrabajador) return false
      if (filtroCargo && t.perfil_cargo !== filtroCargo) return false
      // Filtro por proceso (a través del perfil de cargo)
      if (filtroProceso) {
        const perfil = perfilesCargo.find((p) => p.id === t.perfil_cargo)
        if (perfil && (perfil as any).proceso_id !== filtroProceso) return false
      }
      return true
    })
  }, [trabajadores, filtroTrabajador, filtroCargo, filtroProceso, perfilesCargo])

  // Cargar matrices cuando cambia el filtro si no están en caché
  useEffect(() => {
    if (trabajadoresFiltrados.length > 0) {
      const faltantes = trabajadoresFiltrados.filter((t) => !matrizTrabajadorMap[t.id])
      if (faltantes.length > 0) {
        cargarMatricesParaTrabajadores(faltantes)
      }
    }
  }, [trabajadoresFiltrados])

  // Cálculo de indicadores globales
  const metricasGlobales = useMemo(() => {
    // 1. Competencias cumplidas
    let totalComp = 0
    let cumplidasComp = 0
    Object.values(matrizTrabajadorMap).forEach((m) => {
      m.competencias.forEach((c) => {
        totalComp++
        if (c.cumple) cumplidasComp++
      })
    })

    // 2. Formación obligatoria vigente
    let totalCursosExigidos = 0
    let cursosVigentes = 0
    let cursosPorVencer = 0
    let cursosVencidos = 0
    let cursosFaltantes = 0
    Object.values(matrizFormacionMap).forEach((f) => {
      totalCursosExigidos += f.resumen.total_exigidos
      cursosVigentes += f.resumen.cumplidos
      cursosPorVencer += f.resumen.por_vencer
      cursosVencidos += f.resumen.vencidos
      cursosFaltantes += f.resumen.faltantes
    })

    // 3. Brechas cerradas vs abiertas
    const brechasFormacion = brechas.filter((b) =>
      b.origenes?.some((o) => o.modulo_origen === 'formacion' || o.modulo_origen === 'competencias') ||
      b.descripcion_automatica.toLowerCase().includes('curso') ||
      b.descripcion_automatica.toLowerCase().includes('competencia')
    )
    const brechasCerradas = brechasFormacion.filter((b) => b.estado === 'subsanada' || b.estado === 'cerrada_aceptada').length
    const brechasAbiertas = brechasFormacion.filter((b) => b.estado !== 'subsanada' && b.estado !== 'cerrada_aceptada').length

    return {
      totalComp,
      cumplidasComp,
      pctComp: totalComp > 0 ? Math.round((cumplidasComp / totalComp) * 100) : 0,
      totalCursosExigidos,
      cursosVigentes,
      cursosPorVencer,
      cursosVencidos,
      cursosFaltantes,
      pctCursos: totalCursosExigidos > 0 ? Math.round((cursosVigentes / totalCursosExigidos) * 100) : 0,
      brechasTotal: brechasFormacion.length,
      brechasCerradas,
      brechasAbiertas,
      pctBrechasCerradas: brechasFormacion.length > 0 ? Math.round((brechasCerradas / brechasFormacion.length) * 100) : 0,
    }
  }, [matrizTrabajadorMap, matrizFormacionMap, brechas])

  // "Lo más urgente": cursos por vencer/vencidos + brechas críticas abiertas
  const elementosUrgentes = useMemo(() => {
    const list: Array<{
      id: string
      tipo: 'curso_vencido' | 'curso_por_vencer' | 'brecha_critica'
      titulo: string
      subtitulo: string
      trabajadorId: string
      trabajadorNombre: string
      cursoId?: string
      competenciaId?: string
      dias?: number | null
      prioridad: 'critico' | 'importante' | 'normal'
    }> = []

    // Cursos vencidos o por vencer
    Object.values(matrizFormacionMap).forEach((m) => {
      m.cursos.forEach((c) => {
        if (c.estado === 'vencido' && c.obligatorio) {
          list.push({
            id: `venc-${m.trabajador.id}-${c.curso_id}`,
            tipo: 'curso_vencido',
            titulo: `Certificado Vencido: ${c.curso_nombre}`,
            subtitulo: `Obligatorio para el cargo ${m.trabajador.cargo}`,
            trabajadorId: m.trabajador.id,
            trabajadorNombre: m.trabajador.nombre,
            cursoId: c.curso_id,
            prioridad: 'critico',
          })
        } else if (c.estado === 'por_vencer' && c.obligatorio) {
          list.push({
            id: `xvenc-${m.trabajador.id}-${c.curso_id}`,
            tipo: 'curso_por_vencer',
            titulo: `Vence Pronto: ${c.curso_nombre}`,
            subtitulo: `Vigencia vence en ${c.ultimo_registro?.dias_para_vencer ?? 'pocos'} días`,
            trabajadorId: m.trabajador.id,
            trabajadorNombre: m.trabajador.nombre,
            cursoId: c.curso_id,
            dias: c.ultimo_registro?.dias_para_vencer,
            prioridad: 'importante',
          })
        }
      })
    })

    // Brechas críticas abiertas
    brechas.forEach((b) => {
      if ((b.nivel_atencion === 'critico' || b.nivel_atencion === 'alto') && b.estado === 'abierta') {
        const trab = trabajadores.find((t) => t.id === b.trabajador)
        list.push({
          id: `br-${b.id}`,
          tipo: 'brecha_critica',
          titulo: b.descripcion_automatica || `Brecha ${b.codigo}`,
          subtitulo: `Nivel de atención: ${b.nivel_atencion_display || b.nivel_atencion}`,
          trabajadorId: b.trabajador || '',
          trabajadorNombre: trab?.nombre || b.trabajador_nombre || 'Colaborador',
          prioridad: b.nivel_atencion === 'critico' ? 'critico' : 'importante',
        })
      }
    })

    return list.slice(0, 8) // Mostrar las 8 más prioritarias
  }, [matrizFormacionMap, brechas, trabajadores])

  // Abrir drawer al hacer clic en una celda
  const handleCeldaClick = (trabajador: Trabajador, comp: CompetenciaMatriz) => {
    setSelectedCeldaTrabajador({
      id: trabajador.id,
      nombre: trabajador.nombre,
      documento: trabajador.documento,
      cargo: trabajador.cargo,
    })
    setSelectedCeldaCompetencia(comp)
    setDrawerOpen(true)
  }

  // Exportar matriz a Excel (CSV)
  const handleExportarExcel = () => {
    const rows: string[][] = [
      ['Colaborador', 'Documento', 'Cargo', 'Competencia', 'Tipo', 'Nivel Requerido', 'Nivel Alcanzado', 'Brecha', 'Estado']
    ]
    trabajadoresFiltrados.forEach((t) => {
      const mat = matrizTrabajadorMap[t.id]
      if (mat) {
        mat.competencias.forEach((c) => {
          rows.push([
            `"${t.nombre}"`,
            `"${t.documento || ''}"`,
            `"${t.cargo || ''}"`,
            `"${c.nombre}"`,
            `"${c.tipo || ''}"`,
            `"Nivel ${c.nivel_requerido}"`,
            `"Nivel ${c.nivel_alcanzado}"`,
            `"${c.brecha}"`,
            `"${c.cumple ? 'Cumple' : 'Brecha'}"`,
          ])
        })
      }
    })

    const csvContent = 'data:text/csv;charset=utf-8,\uFEFF' + rows.map((e) => e.join(';')).join('\n')
    const encodedUri = encodeURI(csvContent)
    const link = document.createElement('a')
    link.setAttribute('href', encodedUri)
    link.setAttribute('download', `Matriz_Competencias_${new Date().toISOString().split('T')[0]}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // Exportar matriz a PDF / Imprimir
  const handleExportarPDF = () => {
    window.print()
  }

  // Renderizador de pestañas
  const tabs = [
    { key: 'resumen', label: 'Resumen', icon: TrendingUp },
    { key: 'matriz', label: 'Matriz de competencias', icon: Award },
    { key: 'evaluaciones', label: 'Evaluaciones', icon: ShieldCheck },
    { key: 'cursos', label: 'Cursos y vigencias', icon: GraduationCap },
    { key: 'capacitaciones', label: 'Plan de capacitación', icon: BookOpen },
  ]

  if (loading) {
    return (
      <div className="py-12">
        <LoadingSpinner text="Cargando módulo de Formación & Competencias..." />
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Encabezado Principal */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <GraduationCap className="w-6 h-6 text-primary-600" />
            Formación & Competencias
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Control de requisitos de formación obligatoria, evaluación de competencias del cargo y cierre de brechas.
          </p>
        </div>

        {/* Acciones Rápidas Globales */}
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="secondary"
            onClick={() => {
              setPreselectedTrabajadorId(undefined)
              setPreselectedCompetenciaId(undefined)
              setShowEvaluacionModal(true)
            }}
            className="text-xs py-2 px-3 flex items-center gap-1.5"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-primary-600" />
            Nueva Evaluación
          </Button>

          <Button
            variant="primary"
            onClick={() => {
              setPreselectedCursoId(undefined)
              setShowCursoModal(true)
            }}
            className="text-xs py-2 px-3 flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            Registrar Curso
          </Button>
        </div>
      </div>

      {/* Navegación por Pestañas */}
      <div className="flex overflow-x-auto border-b border-slate-200 scrollbar-none gap-2">
        {tabs.map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.key
          return (
            <button
              key={tab.key}
              onClick={() => handleTabChange(tab.key as TabKey)}
              className={`flex items-center gap-2 py-3 px-4 text-xs font-bold whitespace-nowrap border-b-2 transition-all ${
                isActive
                  ? 'border-primary-600 text-primary-700 bg-primary-50/50 rounded-t-lg'
                  : 'border-transparent text-slate-500 hover:text-slate-900 hover:border-slate-300'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-primary-600' : 'text-slate-400'}`} />
              <span>{tab.label}</span>
            </button>
          )
        })}
      </div>

      {/* ─────────────────────────────────────────────────────────────
          PESTAÑA 1: RESUMEN
      ───────────────────────────────────────────────────────────── */}
      {activeTab === 'resumen' && (
        <div className="space-y-6">
          {/* Anillos de Avance y Métricas */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Anillo 1: Competencias Cumplidas */}
            <Card className="p-5 flex flex-col items-center justify-between text-center space-y-3">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Competencias Cumplidas
              </span>
              <DonutProgress
                value={metricasGlobales.cumplidasComp}
                total={metricasGlobales.totalComp || 1}
                color="#059669"
                size={110}
                strokeWidth={10}
                sublabel="Objetivo"
                altText={`Competencias: ${metricasGlobales.cumplidasComp} cumplidas de ${metricasGlobales.totalComp}`}
              />
              <div className="text-xs text-slate-600">
                <strong>{metricasGlobales.cumplidasComp}</strong> de <strong>{metricasGlobales.totalComp}</strong> evaluaciones en nivel requerido o superior.
              </div>
            </Card>

            {/* Anillo 2: Formación Obligatoria Vigente */}
            <Card className="p-5 flex flex-col items-center justify-between text-center space-y-3">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Cursos Obligatorios Vigentes
              </span>
              <DonutProgress
                value={metricasGlobales.cursosVigentes}
                total={metricasGlobales.totalCursosExigidos || 1}
                color="#0284c7"
                size={110}
                strokeWidth={10}
                sublabel="Vigencia"
                altText={`Cursos: ${metricasGlobales.cursosVigentes} vigentes de ${metricasGlobales.totalCursosExigidos}`}
              />
              <div className="text-xs text-slate-600">
                <strong>{metricasGlobales.cursosVigentes}</strong> vigentes ·{' '}
                <span className="text-amber-600 font-bold">{metricasGlobales.cursosPorVencer} por vencer</span> ·{' '}
                <span className="text-rose-600 font-bold">{metricasGlobales.cursosVencidos} vencidos</span>
              </div>
            </Card>

            {/* Anillo 3: Brechas Subsanadas */}
            <Card className="p-5 flex flex-col items-center justify-between text-center space-y-3">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Brechas Subsanadas
              </span>
              <DonutProgress
                value={metricasGlobales.brechasCerradas}
                total={metricasGlobales.brechasTotal || 1}
                color="#7c3aed"
                size={110}
                strokeWidth={10}
                sublabel="Cierre"
                altText={`Brechas: ${metricasGlobales.brechasCerradas} cerradas de ${metricasGlobales.brechasTotal}`}
              />
              <div className="text-xs text-slate-600">
                <strong>{metricasGlobales.brechasCerradas}</strong> subsanadas de{' '}
                <strong>{metricasGlobales.brechasTotal}</strong> detectadas en el sistema.
              </div>
            </Card>
          </div>

          {/* Distribución de Estados de Formación */}
          <Card className="p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Estado General de Requisitos de Formación
              </h3>
              <span className="text-xs font-mono font-bold text-primary-600">
                {metricasGlobales.totalCursosExigidos} requisitos totales
              </span>
            </div>
            <StackedBar
              segments={[
                { label: 'Vigentes', count: metricasGlobales.cursosVigentes, color: '#10b981' },
                { label: 'Por vencer', count: metricasGlobales.cursosPorVencer, color: '#f59e0b' },
                { label: 'Vencidos', count: metricasGlobales.cursosVencidos, color: '#ef4444' },
                { label: 'Faltantes', count: metricasGlobales.cursosFaltantes, color: '#94a3b8' },
              ]}
              height={14}
              altText="Distribución de requisitos de formación"
            />
          </Card>

          {/* Sección: "Lo más urgente" */}
          <Card className="p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-500" />
                <h3 className="text-sm font-bold text-slate-900">
                  Lo Más Urgente ({elementosUrgentes.length})
                </h3>
              </div>
              <span className="text-xs text-slate-400">
                Atención prioritaria para evitar pérdida de habilitación
              </span>
            </div>

            {elementosUrgentes.length === 0 ? (
              <EmptyState
                icon={CheckCircle2}
                title="Todo al día"
                description="No hay vencimientos inminentes ni brechas críticas abiertas en este momento."
              />
            ) : (
              <div className="divide-y divide-slate-100">
                {elementosUrgentes.map((item) => (
                  <div
                    key={item.id}
                    className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50/60 transition px-2 rounded-lg"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-[9px] font-bold px-2 py-0.5 rounded-full uppercase ${
                            item.prioridad === 'critico'
                              ? 'bg-rose-100 text-rose-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {item.prioridad}
                        </span>
                        <h4 className="text-xs font-bold text-slate-900">{item.titulo}</h4>
                      </div>
                      <p className="text-xs text-slate-500">
                        Colaborador: <strong>{item.trabajadorNombre}</strong> · {item.subtitulo}
                      </p>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      {item.cursoId && (
                        <Button
                          variant="secondary"
                          onClick={() => {
                            setPreselectedTrabajadorId(item.trabajadorId)
                            setPreselectedCursoId(item.cursoId)
                            setShowCursoModal(true)
                          }}
                          className="text-xs py-1.5 px-2.5 flex items-center gap-1 text-primary-700"
                        >
                          <GraduationCap className="w-3.5 h-3.5" />
                          Registrar curso
                        </Button>
                      )}

                      {item.cursoId && (
                        <Button
                          variant="secondary"
                          onClick={() => {
                            navigate(
                              `/app/responsable/capacitaciones?curso_id=${item.cursoId}&trabajador_id=${item.trabajadorId}`
                            )
                          }}
                          className="text-xs py-1.5 px-2.5 flex items-center gap-1 text-indigo-700"
                        >
                          <BookOpen className="w-3.5 h-3.5" />
                          Capacitar
                        </Button>
                      )}

                      {!item.cursoId && (
                        <Button
                          variant="secondary"
                          onClick={() => {
                            setPreselectedTrabajadorId(item.trabajadorId)
                            setShowEvaluacionModal(true)
                          }}
                          className="text-xs py-1.5 px-2.5 flex items-center gap-1 text-emerald-700"
                        >
                          <ShieldCheck className="w-3.5 h-3.5" />
                          Evaluar
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────
          PESTAÑA 2: MATRIZ DE COMPETENCIAS
      ───────────────────────────────────────────────────────────── */}
      {activeTab === 'matriz' && (
        <div className="space-y-4">
          {/* Barra de Filtros Combinables */}
          <Card className="p-4 bg-slate-50 border-slate-200">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {/* Filtro Proceso */}
              <div>
                <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
                  Proceso Organizacional
                </label>
                <select
                  value={filtroProceso}
                  onChange={(e) => setFiltroProceso(e.target.value)}
                  className="w-full text-xs rounded-lg border-slate-300 bg-white py-1.5 px-2.5 text-slate-700 focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
                >
                  <option value="">Todos los procesos</option>
                  {procesos.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.nombre} ({p.tipo})
                    </option>
                  ))}
                </select>
              </div>

              {/* Filtro Cargo */}
              <div>
                <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
                  Perfil de Cargo
                </label>
                <select
                  value={filtroCargo}
                  onChange={(e) => setFiltroCargo(e.target.value)}
                  className="w-full text-xs rounded-lg border-slate-300 bg-white py-1.5 px-2.5 text-slate-700 focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
                >
                  <option value="">Todos los cargos</option>
                  {perfilesCargo.map((pc) => (
                    <option key={pc.id} value={pc.id}>
                      {pc.nombre_cargo}
                    </option>
                  ))}
                </select>
              </div>

              {/* Filtro Trabajador */}
              <div>
                <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
                  Colaborador
                </label>
                <select
                  value={filtroTrabajador}
                  onChange={(e) => setFiltroTrabajador(e.target.value)}
                  className="w-full text-xs rounded-lg border-slate-300 bg-white py-1.5 px-2.5 text-slate-700 focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
                >
                  <option value="">Todos los colaboradores</option>
                  {trabajadores.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.nombre} ({t.cargo || 'Sin cargo'})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Botones de Exportación */}
            <div className="flex items-center justify-between pt-3 mt-3 border-t border-slate-200 text-xs">
              <span className="text-slate-500">
                Mostrando <strong>{trabajadoresFiltrados.length}</strong> colaboradores
              </span>
              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  onClick={handleExportarExcel}
                  className="text-xs py-1.5 px-2.5 flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  Exportar a Excel
                </Button>
                <Button
                  variant="secondary"
                  onClick={handleExportarPDF}
                  className="text-xs py-1.5 px-2.5 flex items-center gap-1.5"
                >
                  <Printer className="w-3.5 h-3.5" />
                  Imprimir / PDF
                </Button>
              </div>
            </div>
          </Card>

          {/* Tabla Matricial */}
          <Card className="p-0 overflow-hidden">
            {loadingMatrices ? (
              <div className="p-8 text-center">
                <LoadingSpinner text="Calculando matrices de cumplimiento de competencias..." />
              </div>
            ) : trabajadoresFiltrados.length === 0 ? (
              <div className="p-8">
                <EmptyState
                  title="Sin colaboradores para mostrar"
                  description="Ajusta los filtros seleccionados o registra nuevos colaboradores en Gestión Humana."
                />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 text-[10px] uppercase font-black tracking-wider">
                      <th className="p-3.5 min-w-[200px]">Colaborador & Cargo</th>
                      <th className="p-3.5 min-w-[300px]">Competencias del Cargo (Req. vs Alc.)</th>
                      <th className="p-3.5 w-32 text-center">Cumplimiento</th>
                      <th className="p-3.5 w-28 text-center">Acción</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {trabajadoresFiltrados.map((trabajador) => {
                      const mat = matrizTrabajadorMap[trabajador.id]
                      const totalC = mat?.competencias.length || 0
                      const cumplidasC = mat?.competencias.filter((c) => c.cumple).length || 0
                      const pct = totalC > 0 ? Math.round((cumplidasC / totalC) * 100) : 0

                      return (
                        <tr key={trabajador.id} className="hover:bg-slate-50/70 transition">
                          {/* Info del trabajador */}
                          <td className="p-3.5 align-top">
                            <div className="font-bold text-slate-900">{trabajador.nombre}</div>
                            <div className="text-[11px] text-slate-500 mt-0.5">
                              {trabajador.cargo || 'Sin cargo asignado'}
                            </div>
                            <span className="inline-block text-[10px] text-slate-400 font-mono mt-1">
                              Doc: {trabajador.documento}
                            </span>
                          </td>

                          {/* Celdas interactivas de competencias en semáforo */}
                          <td className="p-3.5 align-top">
                            {!mat ? (
                              <span className="text-slate-400 text-xs italic">Cargando...</span>
                            ) : mat.competencias.length === 0 ? (
                              <span className="text-slate-400 text-xs italic">
                                El cargo no tiene competencias configuradas.
                              </span>
                            ) : (
                              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                                {mat.competencias.map((comp) => {
                                  const cumple = comp.cumple
                                  const brecha = comp.brecha || 0
                                  return (
                                    <button
                                      type="button"
                                      key={comp.competencia_id}
                                      onClick={() => handleCeldaClick(trabajador, comp)}
                                      className={`p-2 rounded-lg border text-left transition hover:shadow-xs group ${
                                        cumple
                                          ? 'bg-emerald-50/70 border-emerald-200 text-emerald-950 hover:border-emerald-400'
                                          : brecha === 1
                                          ? 'bg-amber-50/70 border-amber-200 text-amber-950 hover:border-amber-400'
                                          : 'bg-rose-50/70 border-rose-200 text-rose-950 hover:border-rose-400'
                                      }`}
                                      title="Haz clic para ver historial y evaluar"
                                    >
                                      <div className="flex items-center justify-between gap-1 mb-1">
                                        <span className="font-bold text-[11px] truncate block flex-1">
                                          {comp.nombre}
                                        </span>
                                        <span
                                          className={`text-[9px] font-black px-1.5 py-0.2 rounded ${
                                            cumple
                                              ? 'bg-emerald-200 text-emerald-800'
                                              : brecha === 1
                                              ? 'bg-amber-200 text-amber-800'
                                              : 'bg-rose-200 text-rose-800'
                                          }`}
                                        >
                                          {cumple ? 'OK' : `-${brecha}`}
                                        </span>
                                      </div>
                                      <div className="text-[10px] text-slate-500 flex items-center justify-between font-mono">
                                        <span>Req: L{comp.nivel_requerido}</span>
                                        <span>Alc: {comp.nivel_alcanzado > 0 ? `L${comp.nivel_alcanzado}` : 'S/E'}</span>
                                      </div>
                                    </button>
                                  )
                                })}
                              </div>
                            )}
                          </td>

                          {/* Cumplimiento porcentual */}
                          <td className="p-3.5 align-top text-center">
                            <div className="inline-flex flex-col items-center">
                              <span
                                className={`text-base font-black font-mono ${
                                  pct >= 85
                                    ? 'text-emerald-700'
                                    : pct >= 60
                                    ? 'text-amber-700'
                                    : 'text-rose-700'
                                }`}
                              >
                                {pct}%
                              </span>
                              <span className="text-[10px] text-slate-400">
                                {cumplidasC} de {totalC}
                              </span>
                            </div>
                          </td>

                          {/* Acción directa */}
                          <td className="p-3.5 align-top text-center">
                            <Button
                              variant="secondary"
                              onClick={() => {
                                setPreselectedTrabajadorId(trabajador.id)
                                setShowEvaluacionModal(true)
                              }}
                              className="text-[11px] py-1 px-2.5 flex items-center gap-1 mx-auto"
                            >
                              <ShieldCheck className="w-3 h-3 text-primary-600" />
                              Evaluar
                            </Button>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────
          PESTAÑA 3: EVALUACIONES
      ───────────────────────────────────────────────────────────── */}
      {activeTab === 'evaluaciones' && (
        <div className="space-y-4">
          <Card className="p-4 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-slate-100">
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-primary-600" />
                  Historial de Evaluaciones de Desempeño y Competencias
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Registro inmutable con roles de evaluador, método aplicado y cálculo automático de brecha.
                </p>
              </div>
              <Button
                variant="primary"
                onClick={() => {
                  setPreselectedTrabajadorId(undefined)
                  setPreselectedCompetenciaId(undefined)
                  setShowEvaluacionModal(true)
                }}
                className="text-xs py-2 px-3 flex items-center gap-1.5 self-start sm:self-auto"
              >
                <Plus className="w-3.5 h-3.5" />
                Nueva Evaluación
              </Button>
            </div>

            {evaluaciones.length === 0 ? (
              <EmptyState
                icon={Award}
                title="Sin evaluaciones registradas"
                description="Comienza realizando la primera evaluación de competencias a un colaborador."
                action={
                  <Button
                    variant="primary"
                    onClick={() => setShowEvaluacionModal(true)}
                    className="text-xs mt-2"
                  >
                    Registrar Primera Evaluación
                  </Button>
                }
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 text-[10px] uppercase font-black tracking-wider">
                      <th className="p-3">Colaborador</th>
                      <th className="p-3">Competencia</th>
                      <th className="p-3 text-center">Req.</th>
                      <th className="p-3 text-center">Alcanzado</th>
                      <th className="p-3 text-center">Brecha</th>
                      <th className="p-3">Evaluador & Rol</th>
                      <th className="p-3">Fecha & Método</th>
                      <th className="p-3 text-center">Acción</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {evaluaciones.map((evalItem) => {
                      const brecha = evalItem.brecha_calculada || 0
                      return (
                        <tr key={evalItem.id} className="hover:bg-slate-50/60 transition">
                          <td className="p-3 font-bold text-slate-900">
                            {evalItem.trabajador_nombre}
                          </td>
                          <td className="p-3">
                            <span className="font-semibold text-slate-800">{evalItem.competencia_nombre}</span>
                            <span className="block text-[10px] text-slate-400 capitalize">{evalItem.competencia_tipo}</span>
                          </td>
                          <td className="p-3 text-center font-mono font-bold text-slate-700">
                            L{evalItem.nivel_requerido}
                          </td>
                          <td className="p-3 text-center font-mono font-bold text-slate-900">
                            L{evalItem.nivel_alcanzado}
                          </td>
                          <td className="p-3 text-center">
                            {brecha === 0 ? (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                                Cumple
                              </span>
                            ) : (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-100 text-rose-800">
                                Brecha (-{brecha})
                              </span>
                            )}
                          </td>
                          <td className="p-3 text-slate-600">
                            <span className="font-medium text-slate-800 block">
                              {evalItem.evaluado_por_nombre || 'Sistema'}
                            </span>
                            <span className="text-[10px] text-slate-500 capitalize">
                              {evalItem.rol_evaluador_display || evalItem.rol_evaluador || 'Gestión Humana'}
                            </span>
                          </td>
                          <td className="p-3 text-slate-500">
                            <span className="font-mono text-slate-700 block">{evalItem.fecha_evaluacion}</span>
                            <span className="text-[10px] text-slate-400">{evalItem.metodo_display || evalItem.metodo}</span>
                          </td>
                          <td className="p-3 text-center">
                            {brecha > 0 && (
                              <Button
                                variant="secondary"
                                onClick={() => {
                                  navigate(
                                    `/app/responsable/capacitaciones?competencia_id=${evalItem.cargo_competencia}&trabajador_id=${evalItem.trabajador}`
                                  )
                                }}
                                className="text-[11px] py-1 px-2 text-indigo-700 border-indigo-200 hover:bg-indigo-50"
                              >
                                Capacitar
                              </Button>
                            )}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────
          PESTAÑA 4: CURSOS Y VIGENCIAS
      ───────────────────────────────────────────────────────────── */}
      {activeTab === 'cursos' && (
        <div className="space-y-4">
          <Card className="p-4 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-slate-100">
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <GraduationCap className="w-4 h-4 text-primary-600" />
                  Cursos Obligatorios y Control de Vigencias
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Seguimiento de certificados, vigencias calculadas y alternativas para cada perfil de cargo.
                </p>
              </div>
              <Button
                variant="primary"
                onClick={() => {
                  setPreselectedCursoId(undefined)
                  setShowCursoModal(true)
                }}
                className="text-xs py-2 px-3 flex items-center gap-1.5 self-start sm:self-auto"
              >
                <Plus className="w-3.5 h-3.5" />
                Registrar Curso
              </Button>
            </div>

            {/* Listado de cursos por trabajador */}
            <div className="space-y-3">
              {trabajadoresFiltrados.map((trabajador) => {
                const matForm = matrizFormacionMap[trabajador.id]
                return (
                  <div
                    key={trabajador.id}
                    className="p-4 rounded-xl border border-slate-200 bg-white shadow-xs space-y-3"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-100">
                      <div>
                        <h4 className="font-bold text-sm text-slate-900">{trabajador.nombre}</h4>
                        <span className="text-xs text-slate-500">
                          {trabajador.cargo || 'Sin cargo asignado'} · Doc: {trabajador.documento}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        {matForm && (
                          <span className="text-xs font-mono font-bold text-primary-700 bg-primary-50 px-2 py-0.5 rounded-full">
                            Cumplimiento: {matForm.resumen.porcentaje_cumplimiento}% ({matForm.resumen.cumplidos}/{matForm.resumen.total_exigidos})
                          </span>
                        )}
                        <Button
                          variant="secondary"
                          onClick={() => {
                            setPreselectedTrabajadorId(trabajador.id)
                            setPreselectedCursoId(undefined)
                            setShowCursoModal(true)
                          }}
                          className="text-xs py-1 px-2.5 flex items-center gap-1"
                        >
                          <Plus className="w-3 h-3" />
                          Registrar curso
                        </Button>
                      </div>
                    </div>

                    {!matForm || matForm.cursos.length === 0 ? (
                      <p className="text-xs text-slate-400 italic">
                        Este cargo no tiene cursos de formación configurados como obligatorios.
                      </p>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
                        {matForm.cursos.map((c) => {
                          const esVigente = c.estado === 'vigente'
                          const esPorVencer = c.estado === 'por_vencer'
                          const esVencido = c.estado === 'vencido'
                          const esAlternativa = c.estado === 'cumple_alternativa'

                          return (
                            <div
                              key={c.curso_id}
                              className={`p-3 rounded-lg border space-y-1.5 ${
                                esVigente
                                  ? 'bg-emerald-50/50 border-emerald-200'
                                  : esPorVencer
                                  ? 'bg-amber-50/50 border-amber-200'
                                  : esVencido
                                  ? 'bg-rose-50/50 border-rose-200'
                                  : esAlternativa
                                  ? 'bg-blue-50/50 border-blue-200'
                                  : 'bg-slate-50 border-slate-200'
                              }`}
                            >
                              <div className="flex items-start justify-between gap-1">
                                <span className="font-bold text-xs text-slate-900 leading-tight">
                                  {c.curso_nombre}
                                </span>
                                <span
                                  className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full capitalize ${
                                    esVigente
                                      ? 'bg-emerald-100 text-emerald-800'
                                      : esPorVencer
                                      ? 'bg-amber-100 text-amber-800'
                                      : esVencido
                                      ? 'bg-rose-100 text-rose-800'
                                      : esAlternativa
                                      ? 'bg-blue-100 text-blue-800'
                                      : 'bg-slate-200 text-slate-700'
                                  }`}
                                >
                                  {c.estado.replace('_', ' ')}
                                </span>
                              </div>

                              <div className="text-[11px] text-slate-500 space-y-0.5">
                                <div>Categoría: {c.categoria_display || c.categoria}</div>
                                {c.ultimo_registro?.fecha_vencimiento && (
                                  <div>
                                    Vence: <strong>{c.ultimo_registro.fecha_vencimiento}</strong>
                                    {c.ultimo_registro.dias_para_vencer !== null && (
                                      <span className="text-[10px] text-slate-400 ml-1">
                                        ({c.ultimo_registro.dias_para_vencer} días)
                                      </span>
                                    )}
                                  </div>
                                )}
                                {c.alternativa_satisfecha && (
                                  <div className="text-[10px] text-blue-700">
                                    Cubierto por: {c.alternativa_cubierta_por}
                                  </div>
                                )}
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </Card>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────
          PESTAÑA 5: PLAN DE CAPACITACIÓN
      ───────────────────────────────────────────────────────────── */}
      {activeTab === 'capacitaciones' && (
        <div className="space-y-4">
          <Card className="p-4 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-slate-100">
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-indigo-600" />
                  Capacitaciones que Cierran Brechas
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Sesiones programadas con vinculación directa a brechas detectadas y cursos obligatorios.
                </p>
              </div>
              <Button
                variant="primary"
                onClick={() => navigate('/app/responsable/capacitaciones')}
                className="text-xs py-2 px-3 flex items-center gap-1.5 self-start sm:self-auto"
              >
                <Plus className="w-3.5 h-3.5" />
                Programar Capacitación
              </Button>
            </div>

            {capacitaciones.length === 0 ? (
              <EmptyState
                icon={BookOpen}
                title="Sin capacitaciones programadas"
                description="Las capacitaciones programadas para cerrar brechas aparecerán aquí con su avance y control de asistencia."
                action={
                  <Button
                    variant="primary"
                    onClick={() => navigate('/app/responsable/capacitaciones')}
                    className="text-xs mt-2"
                  >
                    Programar Primera Capacitación
                  </Button>
                }
              />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {capacitaciones.map((cap) => {
                  const esRealizada = cap.estado === 'realizada'
                  const tieneBrechas = (cap.brechas && cap.brechas.length > 0) || (cap.brechas_detalle && cap.brechas_detalle.length > 0)
                  return (
                    <div
                      key={cap.id}
                      className="p-4 rounded-xl border border-slate-200 bg-white shadow-xs space-y-3 hover:border-indigo-300 transition"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <span
                            className={`text-[9px] font-bold px-2 py-0.5 rounded-full uppercase ${
                              esRealizada ? 'bg-emerald-100 text-emerald-800' : 'bg-indigo-100 text-indigo-800'
                            }`}
                          >
                            {cap.estado}
                          </span>
                          <h4 className="text-sm font-bold text-slate-900 mt-1">{cap.tema}</h4>
                          {cap.objetivo && (
                            <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{cap.objetivo}</p>
                          )}
                        </div>
                      </div>

                      <div className="text-xs text-slate-600 space-y-1 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                        {cap.curso_nombre && (
                          <div className="flex items-center gap-1.5">
                            <GraduationCap className="w-3.5 h-3.5 text-primary-500" />
                            <span>Curso: <strong>{cap.curso_nombre}</strong></span>
                          </div>
                        )}
                        {cap.competencia_nombre && (
                          <div className="flex items-center gap-1.5">
                            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                            <span>Competencia: <strong>{cap.competencia_nombre}</strong></span>
                          </div>
                        )}
                        <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-200/60">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3 text-slate-400" />
                            {cap.fecha ? new Date(cap.fecha).toLocaleDateString('es-CO') : 'Sin fecha'}
                          </span>
                          <span className="flex items-center gap-1 font-bold text-slate-700">
                            <Users className="w-3 h-3 text-slate-400" />
                            {cap.num_asistentes || cap.total_asistieron || 0} asistentes
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between pt-1">
                        {tieneBrechas ? (
                          <span className="text-[10px] font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">
                            Ligua a brechas detectadas
                          </span>
                        ) : (
                          <span className="text-[10px] text-slate-400">Capacitación general</span>
                        )}

                        <Button
                          variant="secondary"
                          onClick={() => navigate('/app/responsable/capacitaciones')}
                          className="text-xs py-1 px-2.5 flex items-center gap-1"
                        >
                          Ver detalle
                          <ChevronRight className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Modales y Drawers */}
      <RegistrarCursoModal
        isOpen={showCursoModal}
        onClose={() => setShowCursoModal(false)}
        trabajadorId={preselectedTrabajadorId || (trabajadores[0]?.id || '')}
        trabajadorNombre={
          trabajadores.find((t) => t.id === (preselectedTrabajadorId || trabajadores[0]?.id))?.nombre || 'Colaborador'
        }
        preselectedCursoId={preselectedCursoId}
        onSuccess={() => {
          cargarDatosGenerales()
        }}
      />

      <NuevaEvaluacionModal
        isOpen={showEvaluacionModal}
        onClose={() => setShowEvaluacionModal(false)}
        trabajadores={trabajadores}
        preselectedTrabajadorId={preselectedTrabajadorId}
        preselectedCompetenciaId={preselectedCompetenciaId}
        onSuccess={() => {
          cargarDatosGenerales()
        }}
      />

      <DetalleCompetenciaDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        trabajador={selectedCeldaTrabajador}
        competencia={selectedCeldaCompetencia}
        historialEvaluaciones={evaluaciones.filter(
          (e) =>
            e.trabajador === selectedCeldaTrabajador?.id &&
            e.cargo_competencia === selectedCeldaCompetencia?.competencia_id
        )}
        onAbrirEvaluar={() => {
          setPreselectedTrabajadorId(selectedCeldaTrabajador?.id)
          setPreselectedCompetenciaId(selectedCeldaCompetencia?.competencia_id)
          setShowEvaluacionModal(true)
        }}
      />
    </div>
  )
}
