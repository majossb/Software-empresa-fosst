import { useState, useEffect } from 'react'
import { Card, Button, Table, TableHeader, TableBody, TableRow, TableHead, TableCell, EmptyState } from '@/components/ui'
import { Modal, LoadingSpinner, ErrorDisplay } from '@/components/ui/forms'
import { reclutamientoService } from '@/services/reclutamiento.service'
import { modulo1Service } from '@/services/modulo1.service'
import {
  CandidatoListItem,
  CandidatoDetail,
  VacanteListItem,
  ProcesoSeleccionDetail,
  PostulacionListItem,
  PostulacionDetail,
  EstadoPostulacion,
} from '@/types/reclutamiento.types'
import {
  Users, Briefcase, GitPullRequest, Search, Plus, Filter,
  CheckCircle2, Clock, XCircle, AlertTriangle, Eye, ShieldCheck,
  Award, FileCheck, Phone, Mail, MapPin, Calendar, ExternalLink,
  ChevronRight, ArrowRight, UserCheck, X, RefreshCw
} from 'lucide-react'

type TabType = 'banco' | 'vacantes' | 'procesos'

export default function ReclutamientoView() {
  const [activeTab, setActiveTab] = useState<TabType>('procesos')
  const [loading, setLoading] = useState(false)

  // ── Tab 1: Banco de Talento ───────────────────────────────────
  const [candidatos, setCandidatos] = useState<CandidatoListItem[]>([])
  const [searchCandidato, setSearchCandidato] = useState('')
  const [selectedCandidato, setSelectedCandidato] = useState<CandidatoDetail | null>(null)
  const [showNewCandidatoModal, setShowNewCandidatoModal] = useState(false)
  const [newCandidatoData, setNewCandidatoData] = useState({
    tipo_documento: 'CC',
    documento: '',
    nombres: '',
    apellidos: '',
    email: '',
    telefono: '',
    ciudad: '',
    titulo_profesional: '',
    nivel_educativo: 'universitario',
    anios_experiencia: 1,
    autoriza_tratamiento_datos: true,
  })

  // ── Tab 2: Vacantes ──────────────────────────────────────────
  const [vacantes, setVacantes] = useState<VacanteListItem[]>([])
  const [perfilesCargo, setPerfilesCargo] = useState<any[]>([])
  const [showNewVacanteModal, setShowNewVacanteModal] = useState(false)
  const [newVacanteData, setNewVacanteData] = useState({
    perfil_cargo: '',
    titulo: '',
    descripcion_publica: '',
    numero_cupos: 1,
    tipo_contrato: 'Termino Indefinido',
    modalidad: 'presencial',
    rango_salarial_min: '',
    rango_salarial_max: '',
    mostrar_salario_publico: true,
    auto_crear_proceso: true,
  })

  // ── Tab 3: Procesos de Selección & Pipeline ───────────────────
  const [selectedVacanteId, setSelectedVacanteId] = useState<string>('')
  const [selectedProceso, setSelectedProceso] = useState<ProcesoSeleccionDetail | null>(null)
  const [selectedPostulacion, setSelectedPostulacion] = useState<PostulacionDetail | null>(null)

  // Modales de Acción de Estado
  const [actionModal, setActionModal] = useState<{
    type: 'preseleccionar' | 'entrevista' | 'evaluacion' | 'validacion' | 'seleccionar' | 'cerrar' | 'reabrir' | 'postular' | null
    postulacion?: PostulacionListItem
  }>({ type: null })

  // Form states para modales de acción
  const [preseleccionarForm, setPreseleccionarForm] = useState({
    experiencia: true,
    formacion: true,
    puntuacion: 90,
  })
  const [entrevistaForm, setEntrevistaForm] = useState({
    tipo_entrevista: 'tecnica',
    modalidad: 'virtual',
    fecha_programada: new Date().toISOString().slice(0, 16),
    calificacion: 85,
    concepto: 'favorable',
    observaciones: '',
  })
  const [evaluacionForm, setEvaluacionForm] = useState({
    tipo_evaluacion: 'tecnica',
    nombre_prueba: 'Evaluación de Normativa SST y GTC 45',
    puntaje_obtenido: 80,
    puntaje_maximo: 100,
    porcentaje_aprobacion: 70,
    concepto: '',
  })
  const [validacionForm, setValidacionForm] = useState({
    tipo_verificacion: 'antecedentes',
    entidad_o_contacto: 'Policía Nacional / Procuraduría',
    estado: 'verificado_conforme',
    detalles_verificacion: 'Sin antecedentes desfavorables',
  })
  const [cerrarForm, setCerrarForm] = useState({
    nuevo_estado: 'no_seleccionado',
    motivo: '',
  })
  const [reabrirForm, setReabrirForm] = useState({
    justificacion: '',
  })
  const [postularCandidatoId, setPostularCandidatoId] = useState('')

  // ── Carga inicial ─────────────────────────────────────────────
  useEffect(() => {
    cargarDatos()
  }, [])

  const cargarDatos = async () => {
    setLoading(true)
    try {
      const [candRes, vacRes, cargosRes] = await Promise.all([
        reclutamientoService.getCandidatos(),
        reclutamientoService.getVacantes(),
        modulo1Service.listPerfiles().catch(() => []),
      ])
      setCandidatos(Array.isArray(candRes) ? candRes : [])
      setVacantes(Array.isArray(vacRes) ? vacRes : [])
      setPerfilesCargo(Array.isArray(cargosRes) ? cargosRes : [])

      if (Array.isArray(vacRes) && vacRes.length > 0 && !selectedVacanteId) {
        const primeraConProceso = vacRes.find(v => v.proceso_seleccion_id) || vacRes[0]
        if (primeraConProceso?.proceso_seleccion_id) {
          setSelectedVacanteId(primeraConProceso.id)
          cargarProceso(primeraConProceso.proceso_seleccion_id)
        }
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const cargarProceso = async (procesoId: string) => {
    try {
      const p = await reclutamientoService.getProcesoById(procesoId)
      setSelectedProceso(p)
    } catch (err) {
      console.error(err)
    }
  }

  const verDetallePostulacion = async (postulacionId: string) => {
    try {
      const p = await reclutamientoService.getPostulacionById(postulacionId)
      setSelectedPostulacion(p)
    } catch (err) {
      console.error(err)
    }
  }

  const verDetalleCandidato = async (candidatoId: string) => {
    try {
      const c = await reclutamientoService.getCandidatoById(candidatoId)
      setSelectedCandidato(c)
    } catch (err) {
      console.error(err)
    }
  }

  // ── Handlers de Acciones de Estado ───────────────────────────
  const handlePreseleccionar = async () => {
    if (!actionModal.postulacion) return
    try {
      await reclutamientoService.preseleccionarPostulacion(actionModal.postulacion.id, {
        calificacion_requisitos: {
          experiencia_requerida: preseleccionarForm.experiencia,
          formacion_academica: preseleccionarForm.formacion,
        },
        puntuacion: Number(preseleccionarForm.puntuacion),
      })
      setActionModal({ type: null })
      if (selectedProceso) cargarProceso(selectedProceso.id)
      if (selectedPostulacion) verDetallePostulacion(selectedPostulacion.id)
    } catch (err: any) {
      alert(err.message || 'Error al preseleccionar')
    }
  }

  const handleRegistrarEntrevista = async () => {
    if (!actionModal.postulacion) return
    try {
      await reclutamientoService.registrarEntrevistaPostulacion(actionModal.postulacion.id, {
        ...entrevistaForm,
        calificacion: Number(entrevistaForm.calificacion),
        fecha_programada: new Date(entrevistaForm.fecha_programada).toISOString(),
      })
      setActionModal({ type: null })
      if (selectedProceso) cargarProceso(selectedProceso.id)
      if (selectedPostulacion) verDetallePostulacion(selectedPostulacion.id)
    } catch (err: any) {
      alert(err.message || 'Error al registrar entrevista')
    }
  }

  const handleRegistrarEvaluacion = async () => {
    if (!actionModal.postulacion) return
    try {
      await reclutamientoService.registrarEvaluacionPostulacion(actionModal.postulacion.id, {
        ...evaluacionForm,
        puntaje_obtenido: Number(evaluacionForm.puntaje_obtenido),
        puntaje_maximo: Number(evaluacionForm.puntaje_maximo),
        porcentaje_aprobacion: Number(evaluacionForm.porcentaje_aprobacion),
      })
      setActionModal({ type: null })
      if (selectedProceso) cargarProceso(selectedProceso.id)
      if (selectedPostulacion) verDetallePostulacion(selectedPostulacion.id)
    } catch (err: any) {
      alert(err.message || 'Error al registrar evaluación')
    }
  }

  const handleRegistrarValidacion = async () => {
    if (!actionModal.postulacion) return
    try {
      await reclutamientoService.registrarValidacionPostulacion(actionModal.postulacion.id, validacionForm)
      setActionModal({ type: null })
      if (selectedProceso) cargarProceso(selectedProceso.id)
      if (selectedPostulacion) verDetallePostulacion(selectedPostulacion.id)
    } catch (err: any) {
      alert(err.message || 'Error al registrar validación')
    }
  }

  const handleSeleccionar = async () => {
    if (!actionModal.postulacion) return
    try {
      await reclutamientoService.seleccionarPostulacion(actionModal.postulacion.id, {
        notas_finales: 'Seleccionado conforme por el comité de contratación.',
      })
      setActionModal({ type: null })
      if (selectedProceso) cargarProceso(selectedProceso.id)
      if (selectedPostulacion) verDetallePostulacion(selectedPostulacion.id)
    } catch (err: any) {
      alert(err.message || 'Error al seleccionar candidato')
    }
  }

  const handleCerrar = async () => {
    if (!actionModal.postulacion) return
    if (!cerrarForm.motivo.trim()) {
      alert('El motivo de cierre es obligatorio (RN-R04).')
      return
    }
    try {
      await reclutamientoService.cerrarPostulacion(actionModal.postulacion.id, cerrarForm)
      setActionModal({ type: null })
      if (selectedProceso) cargarProceso(selectedProceso.id)
      if (selectedPostulacion) verDetallePostulacion(selectedPostulacion.id)
    } catch (err: any) {
      alert(err.message || 'Error al cerrar postulación')
    }
  }

  const handleReabrir = async () => {
    if (!actionModal.postulacion) return
    if (!reabrirForm.justificacion.trim()) {
      alert('La justificación de reapertura es obligatoria (RN-R07/RN-R09).')
      return
    }
    try {
      await reclutamientoService.reabrirPostulacion(actionModal.postulacion.id, reabrirForm)
      setActionModal({ type: null })
      if (selectedProceso) cargarProceso(selectedProceso.id)
      if (selectedPostulacion) verDetallePostulacion(selectedPostulacion.id)
    } catch (err: any) {
      alert(err.message || 'Error al reabrir postulación')
    }
  }

  const handlePostularCandidato = async () => {
    if (!selectedProceso || !postularCandidatoId) return
    try {
      await reclutamientoService.postularCandidatoAProceso(selectedProceso.id, postularCandidatoId)
      setActionModal({ type: null })
      setPostularCandidatoId('')
      cargarProceso(selectedProceso.id)
    } catch (err: any) {
      alert(err.message || 'Error al postular candidato')
    }
  }

  const handleCreateVacante = async () => {
    if (!newVacanteData.perfil_cargo || !newVacanteData.titulo.trim()) {
      alert('Perfil de cargo y título son obligatorios')
      return
    }
    const cupos = Number(newVacanteData.numero_cupos)
    if (isNaN(cupos) || cupos < 1) {
      alert('El número de cupos debe ser mayor o igual a 1')
      return
    }
    const salMin = newVacanteData.rango_salarial_min ? Number(newVacanteData.rango_salarial_min) : null
    const salMax = newVacanteData.rango_salarial_max ? Number(newVacanteData.rango_salarial_max) : null
    if (salMin !== null && salMin < 0) {
      alert('El salario mínimo no puede ser negativo')
      return
    }
    if (salMax !== null && salMax < 0) {
      alert('El salario máximo no puede ser negativo')
      return
    }
    if (salMin !== null && salMax !== null && salMin > salMax) {
      alert('El salario mínimo no puede ser mayor que el salario máximo')
      return
    }
    try {
      await reclutamientoService.createVacante({
        ...newVacanteData,
        numero_cupos: cupos,
        rango_salarial_min: newVacanteData.rango_salarial_min || null,
        rango_salarial_max: newVacanteData.rango_salarial_max || null,
      })
      setShowNewVacanteModal(false)
      cargarDatos()
    } catch (err: any) {
      alert(err.message || 'Error al crear vacante')
    }
  }

  const handleCreateCandidato = async () => {
    if (!newCandidatoData.documento.trim() || !newCandidatoData.nombres.trim() || !newCandidatoData.email.trim()) {
      alert('Documento, nombres y correo son obligatorios')
      return
    }
    const aniosExp = Number(newCandidatoData.anios_experiencia)
    if (isNaN(aniosExp) || aniosExp < 0) {
      alert('Los años de experiencia deben ser un número mayor o igual a 0')
      return
    }
    try {
      await reclutamientoService.createCandidato({
        tipo_documento: newCandidatoData.tipo_documento as any,
        documento: newCandidatoData.documento.trim(),
        nombres: newCandidatoData.nombres.trim(),
        apellidos: newCandidatoData.apellidos.trim(),
        email: newCandidatoData.email.trim(),
        telefono: newCandidatoData.telefono.trim(),
        ciudad: newCandidatoData.ciudad.trim(),
        autoriza_tratamiento_datos: newCandidatoData.autoriza_tratamiento_datos,
        perfil: {
          titulo_profesional: newCandidatoData.titulo_profesional.trim(),
          nivel_educativo: newCandidatoData.nivel_educativo,
          anios_experiencia: aniosExp,
        },
      })
      setShowNewCandidatoModal(false)
      cargarDatos()
    } catch (err: any) {
      alert(err.message || 'Error al crear candidato')
    }
  }

  // ── Render Semáforo de Etapas ─────────────────────────────────
  const renderSemaforoBadge = (etapa: 'entrevista' | 'evaluacion' | 'validacion_documental', semaforo: any) => {
    const info = semaforo?.[etapa]
    if (!info) return null

    const labels: Record<string, string> = {
      entrevista: 'Entrevista',
      evaluacion: 'Evaluación',
      validacion_documental: 'Validación',
    }

    if (info.estado === 'no_requerida') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-400">
          <span className="w-1.5 h-1.5 rounded-full bg-slate-300" />
          {labels[etapa]} N/A
        </span>
      )
    }
    if (info.estado === 'completada') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs bg-emerald-50 text-emerald-700 font-medium border border-emerald-200">
          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
          {labels[etapa]} OK
        </span>
      )
    }
    if (info.estado === 'en_curso') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs bg-amber-50 text-amber-700 font-medium border border-amber-200 animate-pulse">
          <Clock className="w-3 h-3 text-amber-600" />
          {labels[etapa]} En Curso
        </span>
      )
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-600 border border-slate-200">
        <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
        {labels[etapa]} Pendiente
      </span>
    )
  }

  const renderEstadoBadge = (estado: EstadoPostulacion) => {
    const config: Record<string, { bg: string; text: string; label: string }> = {
      postulado: { bg: 'bg-slate-100', text: 'text-slate-700', label: 'Postulado' },
      en_revision: { bg: 'bg-blue-50 border border-blue-200', text: 'text-blue-700', label: 'En Revisión' },
      preseleccionado: { bg: 'bg-blue-50 border border-blue-200', text: 'text-primary-500', label: 'Preseleccionado' },
      en_entrevista: { bg: 'bg-amber-50 border border-amber-200', text: 'text-amber-900', label: 'En Entrevista' },
      en_evaluacion: { bg: 'bg-amber-50 border border-amber-200', text: 'text-amber-700', label: 'En Evaluación' },
      en_validacion: { bg: 'bg-primary-50 border border-primary-200', text: 'text-primary-500', label: 'En Validación' },
      seleccionado: { bg: 'bg-emerald-50 border border-emerald-200', text: 'text-emerald-700 font-bold', label: '¡Seleccionado!' },
      no_seleccionado: { bg: 'bg-rose-50 border border-rose-200', text: 'text-rose-700', label: 'No Seleccionado' },
      retiro_candidatura: { bg: 'bg-orange-50 border border-orange-200', text: 'text-orange-700', label: 'Candidatura Retirada' },
      no_continuo: { bg: 'bg-slate-100 border border-slate-200', text: 'text-slate-500', label: 'No Continuó' },
    }
    const c = config[estado] || { bg: 'bg-slate-100', text: 'text-slate-700', label: estado }
    return <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${c.bg} ${c.text}`}>{c.label}</span>
  }

  return (
    <div className="space-y-6">
      {/* ── Encabezado Principal ───────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <UserCheck className="w-7 h-7 text-primary-500" />
            Reclutamiento y Selección de Personal
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            FOSST V.I.D.A. — Gestión del Banco de Talento, convocatorias, máquina de estados con semáforo y portal público.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            className="text-xs flex items-center gap-1.5"
            onClick={() => window.open('/empleos', '_blank')}
          >
            <ExternalLink className="w-4 h-4 text-slate-600" />
            Ver Portal Público
          </Button>

          {activeTab === 'banco' && (
            <Button
              variant="primary"
              className="text-xs flex items-center gap-1.5"
              onClick={() => setShowNewCandidatoModal(true)}
            >
              <Plus className="w-4 h-4" />
              Nuevo Candidato
            </Button>
          )}

          {activeTab === 'vacantes' && (
            <Button
              variant="primary"
              className="text-xs flex items-center gap-1.5"
              onClick={() => setShowNewVacanteModal(true)}
            >
              <Plus className="w-4 h-4" />
              Nueva Vacante
            </Button>
          )}
        </div>
      </div>

      {/* ── KPI Cards ─────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 flex items-center gap-3 border-l-4 border-l-primary-500">
          <div className="p-2.5 rounded-lg bg-primary-50 text-primary-500">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">{candidatos.length}</div>
            <div className="text-xs text-slate-500 font-medium">Banco de Talento</div>
          </div>
        </Card>

        <Card className="p-4 flex items-center gap-3 border-l-4 border-l-emerald-500">
          <div className="p-2.5 rounded-lg bg-emerald-50 text-emerald-600">
            <Briefcase className="w-5 h-5" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">
              {vacantes.filter(v => v.estado === 'abierta').length} / {vacantes.length}
            </div>
            <div className="text-xs text-slate-500 font-medium">Vacantes Abiertas</div>
          </div>
        </Card>

        <Card className="p-4 flex items-center gap-3 border-l-4 border-l-amber-500">
          <div className="p-2.5 rounded-lg bg-amber-50 text-amber-600">
            <GitPullRequest className="w-5 h-5" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">
              {selectedProceso?.postulaciones.filter(p => p.es_activa).length || 0}
            </div>
            <div className="text-xs text-slate-500 font-medium">Postulaciones Activas</div>
          </div>
        </Card>

        <Card className="p-4 flex items-center gap-3 border-l-4 border-l-brand-500">
          <div className="p-2.5 rounded-lg bg-brand-50 text-brand-700">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">
              {selectedProceso?.postulaciones.filter(p => p.estado === 'seleccionado').length || 0}
            </div>
            <div className="text-xs text-slate-500 font-medium">Seleccionados</div>
          </div>
        </Card>
      </div>

      {/* ── Navegación por Tabs ────────────────────────────────── */}
      <div className="border-b border-slate-200">
        <div className="flex gap-6">
          <button
            onClick={() => setActiveTab('procesos')}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition ${
              activeTab === 'procesos'
                ? 'border-brand-500 text-primary-500 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <GitPullRequest className="w-4 h-4" />
            Convocatoria & Proceso de Selección
          </button>

          <button
            onClick={() => setActiveTab('vacantes')}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition ${
              activeTab === 'vacantes'
                ? 'border-brand-500 text-primary-500 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Briefcase className="w-4 h-4" />
            Vacantes y Requerimientos ({vacantes.length})
          </button>

          <button
            onClick={() => setActiveTab('banco')}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition ${
              activeTab === 'banco'
                ? 'border-brand-500 text-primary-500 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Users className="w-4 h-4" />
            Banco de Talento ({candidatos.length})
          </button>
        </div>
      </div>

      {/* ───────────────────────────────────────────────────────── */}
      {/* TAB 1: CONVOCATORIA & PIPELINE DE SELECCIÓN               */}
      {/* ───────────────────────────────────────────────────────── */}
      {activeTab === 'procesos' && (
        <div className="space-y-6">
          {/* Selector de Vacante Activa */}
          <Card className="p-4 bg-slate-50 border-slate-200">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex-1">
                <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider block mb-1">
                  Convocatoria / Proceso Activo
                </label>
                <select
                  value={selectedVacanteId}
                  onChange={(e) => {
                    setSelectedVacanteId(e.target.value)
                    const v = vacantes.find(item => item.id === e.target.value)
                    if (v?.proceso_seleccion_id) cargarProceso(v.proceso_seleccion_id)
                  }}
                  className="w-full max-w-xl text-sm rounded-lg border-slate-300 bg-white p-2.5 focus:border-brand-500 focus:ring-brand-500 font-medium"
                >
                  {vacantes.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.codigo} — {v.titulo} ({v.estado_display}) • {v.numero_seleccionados}/{v.numero_cupos} cupos
                    </option>
                  ))}
                </select>
              </div>

              {selectedProceso && (
                <div className="flex items-center gap-2">
                  <Button
                    variant="primary"
                    className="text-xs flex items-center gap-1.5"
                    onClick={() => setActionModal({ type: 'postular' })}
                  >
                    <Plus className="w-4 h-4" />
                    Postular del Banco
                  </Button>
                </div>
              )}
            </div>
          </Card>

          {/* Tabla de Postulaciones con Semáforo */}
          {selectedProceso ? (
            <Card className="p-0 overflow-hidden border-slate-200">
              <div className="p-4 bg-white border-b border-slate-100 flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-900">
                    Postulaciones en Convocatoria ({selectedProceso.postulaciones.length})
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Etapas requeridas:{' '}
                    {selectedProceso.requiere_entrevista && '• Entrevista '}
                    {selectedProceso.requiere_evaluacion && '• Evaluación Técnica '}
                    {selectedProceso.requiere_validacion_documental && '• Validación Documental'}
                  </p>
                </div>
              </div>

              {selectedProceso.postulaciones.length === 0 ? (
                <div className="p-12 text-center text-slate-400">
                  <GitPullRequest className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                  <p className="font-semibold text-slate-600 text-sm">No hay candidatos postulados en este proceso.</p>
                  <p className="text-xs text-slate-400 mt-1">Postula candidatos desde el Banco de Talento o espera postulaciones del portal.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase text-[11px] font-semibold">
                        <th className="p-3.5">Candidato</th>
                        <th className="p-3.5">Estado</th>
                        <th className="p-3.5 text-center">Semáforo de Etapas (RN-R03)</th>
                        <th className="p-3.5 text-center">Puntaje</th>
                        <th className="p-3.5 text-right">Acciones de Selección</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {selectedProceso.postulaciones.map((post) => (
                        <tr key={post.id} className="hover:bg-slate-50/80 transition">
                          <td className="p-3.5">
                            <div className="font-bold text-slate-900">{post.candidato_nombre}</div>
                            <div className="text-xs text-slate-500 font-mono">
                              {post.candidato_documento} • {post.candidato_email}
                            </div>
                          </td>

                          <td className="p-3.5">
                            {renderEstadoBadge(post.estado)}
                            {post.es_excepcion && (
                              <span className="inline-flex items-center gap-1 mt-1 text-[11px] text-amber-700 font-semibold">
                                <AlertTriangle className="w-3 h-3 text-amber-600" />
                                <span>Excepción Autorizada</span>
                              </span>
                            )}
                          </td>

                          <td className="p-3.5">
                            <div className="flex items-center justify-center gap-2 flex-wrap">
                              {renderSemaforoBadge('entrevista', post.semaforo_etapas)}
                              {renderSemaforoBadge('evaluacion', post.semaforo_etapas)}
                              {renderSemaforoBadge('validacion_documental', post.semaforo_etapas)}
                            </div>
                          </td>

                          <td className="p-3.5 text-center font-bold text-slate-700">
                            {post.puntuacion_general !== null && post.puntuacion_general !== undefined
                              ? `${post.puntuacion_general} / 100`
                              : '—'}
                          </td>

                          <td className="p-3.5 text-right">
                            <div className="flex items-center justify-end gap-1.5 flex-wrap">
                              {/* Botón Detalle / Línea de tiempo */}
                              <button
                                onClick={() => verDetallePostulacion(post.id)}
                                className="p-1.5 rounded-lg hover:bg-slate-200 text-slate-600"
                                title="Ver Trazabilidad y Detalle"
                              >
                                <Eye className="w-4 h-4" />
                              </button>

                              {/* Acciones de Flujo según estado */}
                              {post.estado === 'postulado' && (
                                <Button
                                  variant="secondary"
                                  className="text-xs py-1 px-2.5 bg-primary-50 text-primary-500 hover:bg-primary-100"
                                  onClick={() => setActionModal({ type: 'preseleccionar', postulacion: post })}
                                >
                                  Preseleccionar
                                </Button>
                              )}

                              {['preseleccionado', 'en_entrevista', 'en_evaluacion', 'en_validacion'].includes(post.estado) && (
                                <>
                                  <button
                                    onClick={() => setActionModal({ type: 'entrevista', postulacion: post })}
                                    className="px-2 py-1 text-xs rounded bg-amber-50 text-amber-900 hover:bg-amber-100 font-medium"
                                  >
                                    + Entrevista
                                  </button>
                                  <button
                                    onClick={() => setActionModal({ type: 'evaluacion', postulacion: post })}
                                    className="px-2 py-1 text-xs rounded bg-amber-50 text-amber-700 hover:bg-amber-100 font-medium"
                                  >
                                    + Evaluación
                                  </button>
                                  <button
                                    onClick={() => setActionModal({ type: 'validacion', postulacion: post })}
                                    className="px-2 py-1 text-xs rounded bg-primary-50 text-primary-500 hover:bg-primary-100 font-medium"
                                  >
                                    + Validación
                                  </button>
                                  <Button
                                    variant="primary"
                                    className="text-xs py-1 px-2.5 bg-emerald-600 hover:bg-emerald-700"
                                    onClick={() => setActionModal({ type: 'seleccionar', postulacion: post })}
                                  >
                                    Seleccionar
                                  </Button>
                                </>
                              )}

                              {post.es_activa && (
                                <button
                                  onClick={() => setActionModal({ type: 'cerrar', postulacion: post })}
                                  className="p-1.5 rounded-lg hover:bg-rose-50 text-rose-600"
                                  title="Cerrar Postulación (No seleccionado / Abandono)"
                                >
                                  <XCircle className="w-4 h-4" />
                                </button>
                              )}

                              {post.estado === 'no_seleccionado' && (
                                <button
                                  onClick={() => setActionModal({ type: 'reabrir', postulacion: post })}
                                  className="px-2 py-1 text-xs rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium"
                                  title="Reapertura Excepcional"
                                >
                                  <RefreshCw className="w-3.5 h-3.5 inline mr-1" />
                                  Reabrir
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          ) : (
            <Card className="p-12 text-center text-slate-400">
              Seleccione una vacante para cargar su proceso de selección.
            </Card>
          )}
        </div>
      )}

      {/* ───────────────────────────────────────────────────────── */}
      {/* TAB 2: VACANTES & CONVOCATORIAS                           */}
      {/* ───────────────────────────────────────────────────────── */}
      {activeTab === 'vacantes' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {vacantes.map((v) => (
              <Card key={v.id} className="p-5 flex flex-col justify-between space-y-4 hover:shadow-md transition">
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="font-mono text-xs font-bold text-slate-500">{v.codigo}</span>
                    <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                      v.estado === 'abierta' ? 'bg-emerald-50 text-emerald-700' :
                      v.estado === 'cubierta' ? 'bg-amber-50 text-amber-900' :
                      v.estado === 'pausada' ? 'bg-amber-50 text-amber-700' : 'bg-slate-100 text-slate-700'
                    }`}>
                      {v.estado_display}
                    </span>
                  </div>

                  <h3 className="font-bold text-slate-900 text-base">{v.titulo}</h3>
                  <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                    <Briefcase className="w-3.5 h-3.5 text-slate-400" />
                    Perfil: {v.perfil_cargo_nombre}
                  </p>

                  <div className="mt-4 pt-3 border-t border-slate-100 grid grid-cols-2 gap-2 text-xs text-slate-600">
                    <div>
                      <span className="text-slate-400 block">Modalidad:</span>
                      <span className="font-medium capitalize">{v.modalidad_display}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Cupos:</span>
                      <span className="font-medium font-mono">{v.numero_seleccionados} / {v.numero_cupos}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Postulaciones:</span>
                      <span className="font-medium font-mono">{v.postulaciones_count}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Portal Público:</span>
                      <span className={`font-medium ${v.publicada_en_portal ? 'text-emerald-600 font-semibold' : 'text-slate-400'}`}>
                        {v.publicada_en_portal ? 'Visible' : 'Oculta'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-3 border-t border-slate-100">
                  <div className="flex items-center gap-1.5">
                    {v.estado === 'borrador' && (
                      <Button
                        variant="primary"
                        className="text-xs py-1 px-2.5"
                        onClick={async () => {
                          await reclutamientoService.publicarVacante(v.id)
                          cargarDatos()
                        }}
                      >
                        Publicar
                      </Button>
                    )}
                    {v.estado === 'abierta' && (
                      <button
                        onClick={async () => {
                          await reclutamientoService.pausarVacante(v.id)
                          cargarDatos()
                        }}
                        className="text-xs px-2.5 py-1 rounded bg-amber-50 text-amber-700 hover:bg-amber-100 font-medium"
                      >
                        Pausar
                      </button>
                    )}
                    {v.estado === 'pausada' && (
                      <button
                        onClick={async () => {
                          await reclutamientoService.publicarVacante(v.id)
                          cargarDatos()
                        }}
                        className="text-xs px-2.5 py-1 rounded bg-emerald-50 text-emerald-700 hover:bg-emerald-100 font-medium"
                      >
                        Reactivar
                      </button>
                    )}
                  </div>

                  <Button
                    variant="secondary"
                    className="text-xs py-1 px-2.5 flex items-center gap-1"
                    onClick={() => {
                      setSelectedVacanteId(v.id)
                      if (v.proceso_seleccion_id) cargarProceso(v.proceso_seleccion_id)
                      setActiveTab('procesos')
                    }}
                  >
                    Ver Proceso
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* ───────────────────────────────────────────────────────── */}
      {/* TAB 3: BANCO DE TALENTO                                   */}
      {/* ───────────────────────────────────────────────────────── */}
      {activeTab === 'banco' && (
        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex flex-col sm:flex-row items-center gap-3">
              <div className="relative flex-1 w-full">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="text"
                  placeholder="Buscar candidato por nombre, cédula, profesión, ciudad, habilidades..."
                  value={searchCandidato}
                  onChange={(e) => setSearchCandidato(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      reclutamientoService.getCandidatos({ search: searchCandidato }).then(setCandidatos)
                    }
                  }}
                  className="w-full text-sm pl-9 pr-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
              <Button
                variant="secondary"
                className="text-xs"
                onClick={() => reclutamientoService.getCandidatos({ search: searchCandidato }).then(setCandidatos)}
              >
                Buscar
              </Button>
            </div>
          </Card>

          <Card className="p-0 overflow-hidden border-slate-200">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase text-[11px] font-semibold">
                    <th className="p-3.5">Candidato</th>
                    <th className="p-3.5">Título / Profesión</th>
                    <th className="p-3.5">Experiencia</th>
                    <th className="p-3.5">Ubicación</th>
                    <th className="p-3.5">Habeas Data</th>
                    <th className="p-3.5 text-right">Acción</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {candidatos.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-50 transition">
                      <td className="p-3.5">
                        <div className="font-bold text-slate-900">{c.nombre_completo}</div>
                        <div className="text-xs text-slate-500 font-mono">
                          {c.tipo_documento_display} {c.documento} • {c.email}
                        </div>
                      </td>
                      <td className="p-3.5 font-medium text-slate-700">
                        {c.titulo_profesional || '—'}
                      </td>
                      <td className="p-3.5 font-mono text-slate-600">
                        {c.anios_experiencia ? `${c.anios_experiencia} años` : '0 años'}
                      </td>
                      <td className="p-3.5 text-slate-600">
                        {c.ciudad || 'No registrada'}
                      </td>
                      <td className="p-3.5">
                        {c.autoriza_tratamiento_datos ? (
                          <span className="inline-flex items-center gap-1 text-xs text-emerald-700 font-medium">
                            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                            Autorizado
                          </span>
                        ) : (
                          <span className="text-xs text-slate-400">Sin autorizar</span>
                        )}
                      </td>
                      <td className="p-3.5 text-right">
                        <Button
                          variant="secondary"
                          className="text-xs py-1 px-2.5"
                          onClick={() => verDetalleCandidato(c.id)}
                        >
                          Ver Perfil
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* ───────────────────────────────────────────────────────── */}
      {/* DRAWER / MODAL: DETALLE Y TRAZABILIDAD DE POSTULACIÓN     */}
      {/* ───────────────────────────────────────────────────────── */}
      {selectedPostulacion && (
        <Modal open={true} onClose={() => setSelectedPostulacion(null)} title="Detalle y Trazabilidad" maxWidth="42rem">
          <div className="space-y-6">
            <div className="pb-2 border-b border-slate-100">
              <span className="text-xs font-mono font-bold text-primary-500">
                {selectedPostulacion.vacante_codigo}
              </span>
              <h2 className="text-lg font-bold text-slate-900">
                {selectedPostulacion.candidato_nombre}
              </h2>
            </div>

            {/* Estado actual & Semáforo */}
            <div className="p-4 bg-slate-50 rounded-xl space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Estado Actual:</span>
                {renderEstadoBadge(selectedPostulacion.estado)}
              </div>

              <div className="pt-2 border-t border-slate-200/60 flex items-center gap-2">
                <span className="text-xs text-slate-500">Semáforo:</span>
                {renderSemaforoBadge('entrevista', selectedPostulacion.semaforo_etapas)}
                {renderSemaforoBadge('evaluacion', selectedPostulacion.semaforo_etapas)}
                {renderSemaforoBadge('validacion_documental', selectedPostulacion.semaforo_etapas)}
              </div>
            </div>

            {/* Entrevistas Registradas */}
            <div className="space-y-3">
              <h4 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                <Users className="w-4 h-4 text-amber-800" />
                Entrevistas ({selectedPostulacion.entrevistas.length})
              </h4>
              {selectedPostulacion.entrevistas.map((ent) => (
                <div key={ent.id} className="p-3 bg-amber-50/50 border border-amber-200 rounded-lg text-xs space-y-1">
                  <div className="flex justify-between font-bold text-slate-800">
                    <span>{ent.tipo_entrevista_display} ({ent.modalidad_display})</span>
                    <span className="text-amber-900">{ent.concepto_display}</span>
                  </div>
                  <div className="text-slate-500">
                    {new Date(ent.fecha_programada).toLocaleString()} • Calificación: {ent.calificacion || 'N/A'}/100
                  </div>
                  {ent.observaciones && <div className="text-slate-600 italic">"{ent.observaciones}"</div>}
                </div>
              ))}
            </div>

            {/* Evaluaciones Registradas */}
            <div className="space-y-3">
              <h4 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                <Award className="w-4 h-4 text-amber-600" />
                Pruebas y Evaluaciones ({selectedPostulacion.evaluaciones.length})
              </h4>
              {selectedPostulacion.evaluaciones.map((ev) => (
                <div key={ev.id} className="p-3 bg-amber-50/50 border border-amber-100 rounded-lg text-xs space-y-1">
                  <div className="flex justify-between font-bold text-slate-800">
                    <span>{ev.nombre_prueba}</span>
                    <span className={ev.estado === 'aprobada' ? 'text-emerald-700' : 'text-rose-700'}>
                      {ev.estado_display} ({ev.porcentaje_obtenido}%)
                    </span>
                  </div>
                  <div className="text-slate-500">
                    Puntaje: {ev.puntaje_obtenido} / {ev.puntaje_maximo} • Aprobación mín: {ev.porcentaje_aprobacion}%
                  </div>
                </div>
              ))}
            </div>

            {/* Validaciones Documentales */}
            <div className="space-y-3">
              <h4 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                <FileCheck className="w-4 h-4 text-primary-500" />
                Validaciones Documentales ({selectedPostulacion.validaciones_documentales.length})
              </h4>
              {selectedPostulacion.validaciones_documentales.map((vd) => (
                <div key={vd.id} className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
                  <div className="flex justify-between font-bold text-slate-800">
                    <span>{vd.tipo_verificacion_display} — {vd.entidad_o_contacto}</span>
                    <span className="text-primary-500 font-semibold">{vd.estado_display}</span>
                  </div>
                  {vd.detalles_verificacion && <div className="text-slate-600">{vd.detalles_verificacion}</div>}
                </div>
              ))}
            </div>

            {/* Línea de Tiempo de Trazabilidad Inmutable (RN-R08) */}
            <div className="space-y-3 pt-4 border-t border-slate-100">
              <h4 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-slate-600" />
                Línea de Tiempo de Trazabilidad (Auditoría Inmutable)
              </h4>
              <div className="space-y-3 pl-2 border-l-2 border-slate-200">
                {selectedPostulacion.eventos.map((ev) => (
                  <div key={ev.id} className="relative pl-4 text-xs space-y-0.5">
                    <span className="absolute -left-[13px] top-1 w-2.5 h-2.5 rounded-full bg-brand-500" />
                    <div className="font-bold text-slate-800 flex items-center justify-between">
                      <span>{ev.descripcion}</span>
                      <span className="text-[10px] text-slate-400">
                        {new Date(ev.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="text-slate-500">
                      Por: {ev.usuario_nombre} • Estado: {ev.estado_anterior || 'Inicio'} → {ev.estado_nuevo}
                    </div>
                    {ev.motivo && <div className="text-slate-600 italic">Motivo: {ev.motivo}</div>}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Modal>
      )}

      {/* ───────────────────────────────────────────────────────── */}
      {/* MODAL: PRESELECCIONAR CANDIDATO                          */}
      {/* ───────────────────────────────────────────────────────── */}
      {actionModal.type === 'preseleccionar' && actionModal.postulacion && (
        <Modal open={true} onClose={() => setActionModal({ type: null })} title="Preseleccionar Candidato (RN-R02)" maxWidth="28rem">
          <div className="space-y-4">
            <p className="text-xs text-slate-500">
              Verifique el cumplimiento de requisitos del perfil de cargo para {actionModal.postulacion.candidato_nombre}.
            </p>

            <div className="space-y-2.5 text-xs">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={preseleccionarForm.experiencia}
                  onChange={(e) => setPreseleccionarForm(p => ({ ...p, experiencia: e.target.checked }))}
                  className="rounded text-primary-500"
                />
                <span>Cumple con los años de experiencia mínima requerida</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={preseleccionarForm.formacion}
                  onChange={(e) => setPreseleccionarForm(p => ({ ...p, formacion: e.target.checked }))}
                  className="rounded text-primary-500"
                />
                <span>Cumple con el nivel educativo y títulos exigidos</span>
              </label>

              <div className="pt-2">
                <label className="block text-slate-700 font-medium mb-1">Calificación Inicial (0 - 100):</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={preseleccionarForm.puntuacion}
                  onChange={(e) => setPreseleccionarForm(p => ({ ...p, puntuacion: Number(e.target.value) }))}
                  className="w-full p-2 border rounded-lg"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" className="text-xs" onClick={() => setActionModal({ type: null })}>
                Cancelar
              </Button>
              <Button variant="primary" className="text-xs" onClick={handlePreseleccionar}>
                Confirmar Preselección
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* ───────────────────────────────────────────────────────── */}
      {/* MODAL: REGISTRAR ENTREVISTA                              */}
      {/* ───────────────────────────────────────────────────────── */}
      {actionModal.type === 'entrevista' && actionModal.postulacion && (
        <Modal open={true} onClose={() => setActionModal({ type: null })} title="Registrar y Calificar Entrevista" maxWidth="28rem">
          <div className="space-y-4">

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Tipo de Entrevista:</label>
                <select
                  value={entrevistaForm.tipo_entrevista}
                  onChange={(e) => setEntrevistaForm(p => ({ ...p, tipo_entrevista: e.target.value }))}
                  className="w-full p-2 border rounded-lg"
                >
                  <option value="inicial_rh">Inicial / Recursos Humanos</option>
                  <option value="tecnica">Técnica / Competencias</option>
                  <option value="jefe_inmediato">Jefe Inmediato</option>
                  <option value="gerencial">Gerencial</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Concepto:</label>
                <select
                  value={entrevistaForm.concepto}
                  onChange={(e) => setEntrevistaForm(p => ({ ...p, concepto: e.target.value }))}
                  className="w-full p-2 border rounded-lg"
                >
                  <option value="favorable">Favorable / Aprobado</option>
                  <option value="con_reservas">Favorable con Reservas</option>
                  <option value="desfavorable">Desfavorable / No Aprobado</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Calificación (0 - 100):</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={entrevistaForm.calificacion}
                  onChange={(e) => setEntrevistaForm(p => ({ ...p, calificacion: Number(e.target.value) }))}
                  className="w-full p-2 border rounded-lg"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Observaciones:</label>
                <textarea
                  rows={3}
                  value={entrevistaForm.observaciones}
                  onChange={(e) => setEntrevistaForm(p => ({ ...p, observaciones: e.target.value }))}
                  className="w-full p-2 border rounded-lg"
                  placeholder="Aspectos destacados, fortalezas y áreas de mejora..."
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" className="text-xs" onClick={() => setActionModal({ type: null })}>
                Cancelar
              </Button>
              <Button variant="primary" className="text-xs" onClick={handleRegistrarEntrevista}>
                Guardar Entrevista
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* ───────────────────────────────────────────────────────── */}
      {/* MODAL: REGISTRAR EVALUACIÓN TÉCNICA                      */}
      {/* ───────────────────────────────────────────────────────── */}
      {actionModal.type === 'evaluacion' && actionModal.postulacion && (
        <Modal open={true} onClose={() => setActionModal({ type: null })} title="Registrar Prueba / Evaluación Técnica" maxWidth="28rem">
          <div className="space-y-4">

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Nombre de la Prueba:</label>
                <input
                  type="text"
                  value={evaluacionForm.nombre_prueba}
                  onChange={(e) => setEvaluacionForm(p => ({ ...p, nombre_prueba: e.target.value }))}
                  className="w-full p-2 border rounded-lg"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Puntaje Obtenido:</label>
                  <input
                    type="number"
                    value={evaluacionForm.puntaje_obtenido}
                    onChange={(e) => setEvaluacionForm(p => ({ ...p, puntaje_obtenido: Number(e.target.value) }))}
                    className="w-full p-2 border rounded-lg font-bold"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Puntaje Máximo:</label>
                  <input
                    type="number"
                    value={evaluacionForm.puntaje_maximo}
                    onChange={(e) => setEvaluacionForm(p => ({ ...p, puntaje_maximo: Number(e.target.value) }))}
                    className="w-full p-2 border rounded-lg"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" className="text-xs" onClick={() => setActionModal({ type: null })}>
                Cancelar
              </Button>
              <Button variant="primary" className="text-xs" onClick={handleRegistrarEvaluacion}>
                Registrar Prueba
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* ───────────────────────────────────────────────────────── */}
      {/* MODAL: REGISTRAR VALIDACIÓN DOCUMENTAL                   */}
      {/* ───────────────────────────────────────────────────────── */}
      {actionModal.type === 'validacion' && actionModal.postulacion && (
        <Modal open={true} onClose={() => setActionModal({ type: null })} title="Validación Documental / Antecedentes" maxWidth="28rem">
          <div className="space-y-4">

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Tipo de Verificación:</label>
                <select
                  value={validacionForm.tipo_verificacion}
                  onChange={(e) => setValidacionForm(p => ({ ...p, tipo_verificacion: e.target.value }))}
                  className="w-full p-2 border rounded-lg"
                >
                  <option value="antecedentes">Antecedentes Judiciales / Procuraduría</option>
                  <option value="referencia_laboral">Referencia Laboral</option>
                  <option value="titulo_academico">Título Académico</option>
                  <option value="licencia_sst">Licencia SST</option>
                  <option value="certificacion_alturas">Certificado Trabajo en Alturas</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Entidad o Contacto:</label>
                <input
                  type="text"
                  value={validacionForm.entidad_o_contacto}
                  onChange={(e) => setValidacionForm(p => ({ ...p, entidad_o_contacto: e.target.value }))}
                  className="w-full p-2 border rounded-lg"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Estado de la Verificación:</label>
                <select
                  value={validacionForm.estado}
                  onChange={(e) => setValidacionForm(p => ({ ...p, estado: e.target.value }))}
                  className="w-full p-2 border rounded-lg"
                >
                  <option value="verificado_conforme">Verificado Conforme / Válido</option>
                  <option value="verificado_con_inconsistencias">Con Inconsistencias</option>
                  <option value="no_pudo_verificarse">No Pudo Verificarse</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" className="text-xs" onClick={() => setActionModal({ type: null })}>
                Cancelar
              </Button>
              <Button variant="primary" className="text-xs" onClick={handleRegistrarValidacion}>
                Confirmar Verificación
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* ───────────────────────────────────────────────────────── */}
      {/* MODAL: SELECCIONAR CANDIDATO                             */}
      {/* ───────────────────────────────────────────────────────── */}
      {actionModal.type === 'seleccionar' && actionModal.postulacion && (
        <Modal open={true} onClose={() => setActionModal({ type: null })} title="Decisión Final de Selección (RN-R06)" maxWidth="28rem">
          <div className="space-y-4">
            <p className="text-xs text-slate-600">
              ¿Desea formalizar la selección de <strong>{actionModal.postulacion.candidato_nombre}</strong> para esta vacante?
              Al completar los cupos disponibles, las demás candidaturas se cerrarán automáticamente.
            </p>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" className="text-xs" onClick={() => setActionModal({ type: null })}>
                Cancelar
              </Button>
              <Button variant="primary" className="text-xs bg-emerald-600 hover:bg-emerald-700" onClick={handleSeleccionar}>
                Confirmar Selección
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* ───────────────────────────────────────────────────────── */}
      {/* MODAL: CERRAR POSTULACIÓN (RN-R04)                        */}
      {/* ───────────────────────────────────────────────────────── */}
      {actionModal.type === 'cerrar' && actionModal.postulacion && (
        <Modal open={true} onClose={() => setActionModal({ type: null })} title="Cierre de Postulación" maxWidth="28rem">
          <div className="space-y-4">
            <p className="text-xs text-slate-500">
              Especifique el motivo obligatorio de no selección o retiro para {actionModal.postulacion.candidato_nombre}.
            </p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Estado de Cierre:</label>
                <select
                  value={cerrarForm.nuevo_estado}
                  onChange={(e) => setCerrarForm(p => ({ ...p, nuevo_estado: e.target.value }))}
                  className="w-full p-2 border rounded-lg"
                >
                  <option value="no_seleccionado">No Seleccionado</option>
                  <option value="retiro_candidatura">Retiro Voluntario de Candidatura</option>
                  <option value="no_continuo">No Continuó en Proceso / Abandono</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Motivo Obligatorio (RN-R04):</label>
                <textarea
                  rows={3}
                  value={cerrarForm.motivo}
                  onChange={(e) => setCerrarForm(p => ({ ...p, motivo: e.target.value }))}
                  className="w-full p-2 border rounded-lg"
                  placeholder="Justifique la decisión..."
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" className="text-xs" onClick={() => setActionModal({ type: null })}>
                Cancelar
              </Button>
              <Button variant="primary" className="text-xs bg-rose-600 hover:bg-rose-700" onClick={handleCerrar}>
                Confirmar Cierre
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* ───────────────────────────────────────────────────────── */}
      {/* MODAL: POSTULAR DEL BANCO DE TALENTO                     */}
      {/* ───────────────────────────────────────────────────────── */}
      {actionModal.type === 'postular' && selectedProceso && (
        <Modal open={true} onClose={() => setActionModal({ type: null })} title="Postular Candidato del Banco" maxWidth="28rem">
          <div className="space-y-4">
            <p className="text-xs text-slate-500">
              Seleccione un candidato registrado en el Banco de Talento para vincularlo a esta convocatoria.
            </p>

            <div>
              <label className="block text-xs text-slate-700 font-medium mb-1">Candidato:</label>
              <select
                value={postularCandidatoId}
                onChange={(e) => setPostularCandidatoId(e.target.value)}
                className="w-full text-xs p-2.5 border rounded-lg"
              >
                <option value="">Seleccione un candidato...</option>
                {candidatos.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nombre_completo} ({c.documento}) — {c.titulo_profesional || 'Sin título'}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" className="text-xs" onClick={() => setActionModal({ type: null })}>
                Cancelar
              </Button>
              <Button variant="primary" className="text-xs" onClick={handlePostularCandidato}>
                Vincular Candidato
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* ───────────────────────────────────────────────────────── */}
      {/* MODAL: CREAR NUEVA VACANTE                                */}
      {/* ───────────────────────────────────────────────────────── */}
      {showNewVacanteModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <Card className="max-w-lg w-full p-6 space-y-4 bg-white max-h-[90vh] overflow-y-auto shadow-2xl">
            <h3 className="text-base font-bold text-slate-900">Crear Requerimiento / Vacante</h3>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Perfil de Cargo Vinculado (Módulo 1):</label>
                <select
                  value={newVacanteData.perfil_cargo}
                  onChange={(e) => {
                    const cargoId = e.target.value
                    const cargo = perfilesCargo.find(c => c.id === cargoId)
                    setNewVacanteData(p => ({
                      ...p,
                      perfil_cargo: cargoId,
                      titulo: cargo ? cargo.nombre_cargo || cargo.cargo : p.titulo,
                    }))
                  }}
                  className="w-full p-2.5 border rounded-lg font-medium"
                >
                  <option value="">Seleccione un perfil de cargo...</option>
                  {perfilesCargo.map((pc) => (
                    <option key={pc.id} value={pc.id}>
                      {pc.codigo} — {pc.nombre_cargo || pc.cargo} ({pc.area || 'Sin área'})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Título de la Convocatoria:</label>
                <input
                  type="text"
                  value={newVacanteData.titulo}
                  onChange={(e) => setNewVacanteData(p => ({ ...p, titulo: e.target.value }))}
                  className="w-full p-2.5 border rounded-lg"
                  placeholder="Ej: Inspector SST para Obra Civil"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Modalidad:</label>
                  <select
                    value={newVacanteData.modalidad}
                    onChange={(e) => setNewVacanteData(p => ({ ...p, modalidad: e.target.value }))}
                    className="w-full p-2 border rounded-lg"
                  >
                    <option value="presencial">Presencial</option>
                    <option value="remoto">Remoto</option>
                    <option value="hibrido">Híbrido</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-700 font-medium mb-1">Número de Cupos:</label>
                  <input
                    type="number"
                    min="1"
                    value={newVacanteData.numero_cupos}
                    onChange={(e) => setNewVacanteData(p => ({ ...p, numero_cupos: Number(e.target.value) }))}
                    className="w-full p-2 border rounded-lg"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Descripción Pública:</label>
                <textarea
                  rows={3}
                  value={newVacanteData.descripcion_publica}
                  onChange={(e) => setNewVacanteData(p => ({ ...p, descripcion_publica: e.target.value }))}
                  className="w-full p-2 border rounded-lg"
                  placeholder="Información visible en el portal público de empleo..."
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" className="text-xs" onClick={() => setShowNewVacanteModal(false)}>
                Cancelar
              </Button>
              <Button variant="primary" className="text-xs" onClick={handleCreateVacante}>
                Crear Vacante
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* ───────────────────────────────────────────────────────── */}
      {/* MODAL: NUEVO CANDIDATO                                    */}
      {/* ───────────────────────────────────────────────────────── */}
      {showNewCandidatoModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <Card className="max-w-lg w-full p-6 space-y-4 bg-white max-h-[90vh] overflow-y-auto shadow-2xl">
            <h3 className="text-base font-bold text-slate-900">Registrar Candidato en Banco de Talento</h3>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Tipo Doc:</label>
                  <select
                    value={newCandidatoData.tipo_documento}
                    onChange={(e) => setNewCandidatoData(p => ({ ...p, tipo_documento: e.target.value }))}
                    className="w-full p-2 border rounded-lg"
                  >
                    <option value="CC">CC</option>
                    <option value="CE">CE</option>
                    <option value="PA">Pasaporte</option>
                    <option value="PEP">PEP</option>
                    <option value="PPT">PPT</option>
                  </select>
                </div>
                <div className="col-span-2">
                  <label className="block text-slate-700 font-medium mb-1">Número de Documento:</label>
                  <input
                    type="text"
                    value={newCandidatoData.documento}
                    onChange={(e) => setNewCandidatoData(p => ({ ...p, documento: e.target.value }))}
                    className="w-full p-2 border rounded-lg"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Nombres:</label>
                  <input
                    type="text"
                    value={newCandidatoData.nombres}
                    onChange={(e) => setNewCandidatoData(p => ({ ...p, nombres: e.target.value }))}
                    className="w-full p-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Apellidos:</label>
                  <input
                    type="text"
                    value={newCandidatoData.apellidos}
                    onChange={(e) => setNewCandidatoData(p => ({ ...p, apellidos: e.target.value }))}
                    className="w-full p-2 border rounded-lg"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Correo Electrónico:</label>
                  <input
                    type="email"
                    value={newCandidatoData.email}
                    onChange={(e) => setNewCandidatoData(p => ({ ...p, email: e.target.value }))}
                    className="w-full p-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Teléfono:</label>
                  <input
                    type="text"
                    value={newCandidatoData.telefono}
                    onChange={(e) => setNewCandidatoData(p => ({ ...p, telefono: e.target.value }))}
                    className="w-full p-2 border rounded-lg"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Título / Profesión:</label>
                <input
                  type="text"
                  value={newCandidatoData.titulo_profesional}
                  onChange={(e) => setNewCandidatoData(p => ({ ...p, titulo_profesional: e.target.value }))}
                  className="w-full p-2 border rounded-lg"
                  placeholder="Ej: Ingeniero SST, Tecnólogo en Alturas"
                />
              </div>

              <div className="pt-2 border-t">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={newCandidatoData.autoriza_tratamiento_datos}
                    onChange={(e) => setNewCandidatoData(p => ({ ...p, autoriza_tratamiento_datos: e.target.checked }))}
                    className="rounded text-primary-500"
                  />
                  <span>Autorización de Habeas Data (Ley 1581 de 2012)</span>
                </label>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" className="text-xs" onClick={() => setShowNewCandidatoModal(false)}>
                Cancelar
              </Button>
              <Button variant="primary" className="text-xs" onClick={handleCreateCandidato}>
                Guardar Candidato
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
