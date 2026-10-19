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
  FuenteReclutamiento,
  IndicadorFuente,
} from '@/types/reclutamiento.types'
import {
  Users, Briefcase, GitPullRequest, Search, Plus, Filter,
  CheckCircle2, Clock, XCircle, AlertTriangle, Eye, ShieldCheck,
  Award, FileCheck, Phone, Mail, MapPin, Calendar, ExternalLink,
  ChevronRight, ArrowRight, UserCheck, X, RefreshCw,
  Tag, TrendingUp, Pencil, FileText, Download, History, ListChecks
} from 'lucide-react'

type TabType = 'banco' | 'vacantes' | 'procesos' | 'fuentes' | 'historico'

const DOC_TIPOS: Array<[string, string]> = [
  ['hoja_de_vida', 'Hoja de Vida'],
  ['cedula', 'Cédula'],
  ['certificacion_academica', 'Certificación académica'],
  ['certificacion_laboral', 'Certificación laboral'],
  ['licencia_conduccion', 'Licencia de conducción'],
  ['licencia_sst', 'Licencia SST'],
  ['certificacion_alturas', 'Certificación alturas'],
  ['otro', 'Otro'],
]

const docLabel = (tipo: string) => DOC_TIPOS.find(([value]) => value === tipo)?.[1] || tipo

export default function ReclutamientoView() {
  const [activeTab, setActiveTab] = useState<TabType>('procesos')
  const [loading, setLoading] = useState(false)

  // ── Tab 1: Banco de Talento ───────────────────────────────────
  const [candidatos, setCandidatos] = useState<CandidatoListItem[]>([])
  const [searchCandidato, setSearchCandidato] = useState('')
  const [filtroFuente, setFiltroFuente] = useState('')
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
    profesion: '',
    area_conocimiento: '',
    nivel_educativo: 'universitario',
    anios_experiencia: 1,
    autoriza_tratamiento_datos: true,
    fuente_reclutamiento: '',
  })
  const [editingCandidato, setEditingCandidato] = useState(false)
  const [editCandidatoData, setEditCandidatoData] = useState<any>({})
  const [docUpload, setDocUpload] = useState<{ tipo_documento: string; file: File | null }>({
    tipo_documento: 'hoja_de_vida',
    file: null,
  })

  // ── Tab 4: Fuentes de Reclutamiento ──────────────────────────
  const [fuentes, setFuentes] = useState<FuenteReclutamiento[]>([])
  const [indicadores, setIndicadores] = useState<IndicadorFuente[]>([])
  const [showNewFuenteModal, setShowNewFuenteModal] = useState(false)
  const [newFuenteData, setNewFuenteData] = useState({ nombre: '', descripcion: '' })

  // ── Tab 2: Vacantes ──────────────────────────────────────────
  const [vacantes, setVacantes] = useState<VacanteListItem[]>([])
  const [perfilesCargo, setPerfilesCargo] = useState<any[]>([])
  const [showNewVacanteModal, setShowNewVacanteModal] = useState(false)
  const [editingVacanteId, setEditingVacanteId] = useState<string | null>(null)
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
    requiere_entrevista: true,
    requiere_evaluacion: true,
    requiere_validacion_documental: true,
    documentos_requeridos: ['hoja_de_vida'] as string[],
  })

  // ── Tab 3: Procesos de Selección & Pipeline ───────────────────
  const [selectedVacanteId, setSelectedVacanteId] = useState<string>('')
  const [selectedProceso, setSelectedProceso] = useState<ProcesoSeleccionDetail | null>(null)
  const [selectedPostulacion, setSelectedPostulacion] = useState<PostulacionDetail | null>(null)
  const [paqueteVinculacion, setPaqueteVinculacion] = useState<any | null>(null)
  const [historico, setHistorico] = useState<PostulacionListItem[]>([])
  const [historicoEstado, setHistoricoEstado] = useState('')
  const [historicoVacante, setHistoricoVacante] = useState('')
  const [showBatchModal, setShowBatchModal] = useState(false)
  const [batchIds, setBatchIds] = useState<string[]>([])
  const [noSeleccionarMotivo, setNoSeleccionarMotivo] = useState('')

  // Modales de Acción de Estado
  const [actionModal, setActionModal] = useState<{
    type: 'preseleccionar' | 'entrevista' | 'evaluacion' | 'validacion' | 'seleccionar' | 'no_seleccionar' | 'cerrar' | 'reabrir' | 'postular' | null
    postulacion?: PostulacionListItem
  }>({ type: null })

  // Form states para modales de acción
  const [preseleccionarForm, setPreseleccionarForm] = useState({
    experiencia: true,
    formacion: true,
    puntuacion: 90,
    es_excepcion: false,
    justificacion_excepcion: '',
  })
  const [seleccionarForm, setSeleccionarForm] = useState({
    notas_finales: '',
    es_excepcion: false,
    justificacion_excepcion: '',
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

      const [fuentesRes, indRes] = await Promise.all([
        reclutamientoService.getFuentes().catch(() => []),
        reclutamientoService.getIndicadoresFuentes().catch(() => []),
      ])
      setFuentes(Array.isArray(fuentesRes) ? fuentesRes : [])
      setIndicadores(Array.isArray(indRes) ? indRes : [])

      const posts = await reclutamientoService.getPostulaciones().catch(() => [])
      setHistorico(Array.isArray(posts) ? posts : [])

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
  const errMsg = (err: any, fallback: string) => err?.friendlyMessage || err?.message || fallback

  const handlePreseleccionar = async () => {
    if (!actionModal.postulacion) return
    if (preseleccionarForm.es_excepcion && !preseleccionarForm.justificacion_excepcion.trim()) {
      alert('Debe justificar la excepción (RN-R09).')
      return
    }
    try {
      await reclutamientoService.preseleccionarPostulacion(actionModal.postulacion.id, {
        calificacion_requisitos: {
          experiencia_requerida: preseleccionarForm.experiencia,
          formacion_academica: preseleccionarForm.formacion,
        },
        puntuacion: Number(preseleccionarForm.puntuacion),
        es_excepcion: preseleccionarForm.es_excepcion,
        justificacion_excepcion: preseleccionarForm.justificacion_excepcion,
      })
      setActionModal({ type: null })
      if (selectedProceso) cargarProceso(selectedProceso.id)
      if (selectedPostulacion) verDetallePostulacion(selectedPostulacion.id)
    } catch (err: any) {
      alert(errMsg(err, 'Error al preseleccionar'))
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
      alert(errMsg(err, 'Error al registrar entrevista'))
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
      alert(errMsg(err, 'Error al registrar evaluación'))
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
      alert(errMsg(err, 'Error al registrar validación'))
    }
  }

  const handleSeleccionar = async () => {
    if (!actionModal.postulacion) return
    if (seleccionarForm.es_excepcion && !seleccionarForm.justificacion_excepcion.trim()) {
      alert('Debe justificar la excepción (RN-R09).')
      return
    }
    try {
      await reclutamientoService.seleccionarPostulacion(actionModal.postulacion.id, {
        notas_finales: seleccionarForm.notas_finales || 'Seleccionado conforme por el comité de contratación.',
        es_excepcion: seleccionarForm.es_excepcion,
        justificacion_excepcion: seleccionarForm.justificacion_excepcion,
      })
      setActionModal({ type: null })
      if (selectedProceso) cargarProceso(selectedProceso.id)
      if (selectedPostulacion) verDetallePostulacion(selectedPostulacion.id)
    } catch (err: any) {
      alert(errMsg(err, 'Error al seleccionar candidato'))
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
      alert(errMsg(err, 'Error al cerrar postulación'))
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
      alert(errMsg(err, 'Error al reabrir postulación'))
    }
  }

  const handleNoSeleccionar = async () => {
    if (!actionModal.postulacion) return
    if (!noSeleccionarMotivo.trim()) {
      alert('Debe indicar el motivo de no selección (RN-R04).')
      return
    }
    try {
      await reclutamientoService.cerrarPostulacion(actionModal.postulacion.id, {
        nuevo_estado: 'no_seleccionado',
        motivo: noSeleccionarMotivo.trim(),
      })
      setActionModal({ type: null })
      setNoSeleccionarMotivo('')
      if (selectedProceso) cargarProceso(selectedProceso.id)
      cargarDatos()
    } catch (err: any) {
      alert(errMsg(err, 'No se pudo registrar la no selección.'))
    }
  }

  const handleSeleccionMasiva = async () => {
    if (batchIds.length === 0) {
      alert('Seleccione al menos un candidato.')
      return
    }
    try {
      const res = await reclutamientoService.seleccionarMasivo(batchIds)
      setShowBatchModal(false)
      setBatchIds([])
      if (selectedProceso) cargarProceso(selectedProceso.id)
      cargarDatos()
      alert(`Seleccionados: ${res.seleccionados}. Cupos disponibles: ${res.cupos_disponibles}.`)
    } catch (err: any) {
      alert(errMsg(err, 'No se pudo realizar la selección múltiple.'))
    }
  }

  const handleFaltaDocumentos = async (post: PostulacionListItem) => {
    if (!confirm(`¿Cerrar el proceso de ${post.candidato_nombre} por falta de documentación y notificarlo?`)) return
    try {
      await reclutamientoService.cerrarPorFaltaDocumentos(post.id)
      if (selectedProceso) cargarProceso(selectedProceso.id)
      cargarDatos()
    } catch (err: any) {
      alert(errMsg(err, 'No se pudo cerrar por falta de documentos.'))
    }
  }

  const handleExportarHistorico = async (formato: 'csv' | 'xlsx' | 'pdf') => {
    try {
      const blob = await reclutamientoService.exportarHistorico(formato, {
        vacante_id: historicoVacante || undefined,
        estado: historicoEstado || undefined,
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `historico_postulaciones.${formato}`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (err: any) {
      alert(errMsg(err, 'No se pudo exportar el histórico.'))
    }
  }

  const handleIniciarVinculacion = async (post: PostulacionListItem) => {
    try {
      const paquete = await reclutamientoService.iniciarVinculacion(post.id)
      setPaqueteVinculacion(paquete)
    } catch (err: any) {
      alert(errMsg(err, 'No se pudo iniciar la vinculación.'))
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

  const abrirNuevaVacante = () => {
    setEditingVacanteId(null)
    setNewVacanteData({
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
      requiere_entrevista: true,
      requiere_evaluacion: true,
      requiere_validacion_documental: true,
      documentos_requeridos: ['hoja_de_vida'],
    })
    setShowNewVacanteModal(true)
  }

  const abrirEdicionVacante = async (id: string) => {
    try {
      const v = await reclutamientoService.getVacanteById(id)
      setNewVacanteData({
        perfil_cargo: v.perfil_cargo,
        titulo: v.titulo,
        descripcion_publica: v.descripcion_publica || '',
        numero_cupos: v.numero_cupos,
        tipo_contrato: v.tipo_contrato || 'Termino Indefinido',
        modalidad: v.modalidad,
        rango_salarial_min: v.rango_salarial_min != null ? String(v.rango_salarial_min) : '',
        rango_salarial_max: v.rango_salarial_max != null ? String(v.rango_salarial_max) : '',
        mostrar_salario_publico: v.mostrar_salario_publico,
        auto_crear_proceso: true,
        requiere_entrevista: v.proceso_seleccion?.requiere_entrevista ?? true,
        requiere_evaluacion: v.proceso_seleccion?.requiere_evaluacion ?? true,
        requiere_validacion_documental: v.proceso_seleccion?.requiere_validacion_documental ?? true,
        documentos_requeridos: v.proceso_seleccion?.documentos_requeridos || [],
      })
      setEditingVacanteId(id)
      setShowNewVacanteModal(true)
    } catch (err: any) {
      alert(errMsg(err, 'No se pudo cargar la vacante.'))
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
    const payload = {
      ...newVacanteData,
      numero_cupos: cupos,
      rango_salarial_min: newVacanteData.rango_salarial_min || null,
      rango_salarial_max: newVacanteData.rango_salarial_max || null,
    }
    try {
      if (editingVacanteId) {
        await reclutamientoService.updateVacante(editingVacanteId, payload)
      } else {
        await reclutamientoService.createVacante(payload)
      }
      setShowNewVacanteModal(false)
      setEditingVacanteId(null)
      cargarDatos()
    } catch (err: any) {
      alert(errMsg(err, editingVacanteId ? 'Error al actualizar vacante' : 'Error al crear vacante'))
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
        fuente_reclutamiento: newCandidatoData.fuente_reclutamiento || undefined,
        autoriza_tratamiento_datos: newCandidatoData.autoriza_tratamiento_datos,
        perfil: {
          titulo_profesional: newCandidatoData.titulo_profesional.trim(),
          profesion: newCandidatoData.profesion.trim(),
          area_conocimiento: newCandidatoData.area_conocimiento.trim(),
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

  const handleCreateFuente = async () => {
    if (!newFuenteData.nombre.trim()) {
      alert('El nombre de la fuente es obligatorio')
      return
    }
    try {
      await reclutamientoService.createFuente({
        nombre: newFuenteData.nombre.trim(),
        descripcion: newFuenteData.descripcion.trim(),
      })
      setShowNewFuenteModal(false)
      setNewFuenteData({ nombre: '', descripcion: '' })
      cargarDatos()
    } catch (err: any) {
      alert(err.message || 'Error al crear la fuente')
    }
  }

  const abrirEdicionCandidato = (c: CandidatoDetail) => {
    setEditCandidatoData({
      tipo_documento: c.tipo_documento,
      documento: c.documento,
      nombres: c.nombres,
      apellidos: c.apellidos,
      email: c.email,
      telefono: c.telefono || '',
      ciudad: c.ciudad || '',
      departamento: c.departamento || '',
      municipio: c.municipio || '',
      direccion: c.direccion || '',
      estado_perfil: c.estado_perfil || 'activo',
      fuente_reclutamiento: c.fuente_reclutamiento || '',
      notas_internas: c.notas_internas || '',
      autoriza_tratamiento_datos: c.autoriza_tratamiento_datos,
      perfil: {
        titulo_profesional: c.perfil?.titulo_profesional || '',
        profesion: c.perfil?.profesion || '',
        area_conocimiento: c.perfil?.area_conocimiento || '',
        nivel_educativo: c.perfil?.nivel_educativo || '',
        resumen_profesional: c.perfil?.resumen_profesional || '',
        anios_experiencia: c.perfil?.anios_experiencia ?? 0,
        competencias: c.perfil?.competencias || [],
        certificaciones: c.perfil?.certificaciones || [],
        cargos_interes: c.perfil?.cargos_interes || [],
        disponibilidad: c.perfil?.disponibilidad || '',
        disponibilidad_viaje: c.perfil?.disponibilidad_viaje || false,
        disponibilidad_traslado: c.perfil?.disponibilidad_traslado || false,
        aspiracion_salarial: c.perfil?.aspiracion_salarial ?? null,
      },
    })
    setEditingCandidato(true)
  }

  const handleSaveCandidato = async () => {
    if (!selectedCandidato) return
    try {
      const updated = await reclutamientoService.updateCandidato(selectedCandidato.id, editCandidatoData)
      setSelectedCandidato(updated)
      setEditingCandidato(false)
      cargarDatos()
    } catch (err: any) {
      alert(err.message || 'Error al guardar el candidato')
    }
  }

  const handleSubirDocumento = async () => {
    if (!selectedCandidato || !docUpload.file) {
      alert('Selecciona un archivo para subir.')
      return
    }
    try {
      const fd = new FormData()
      fd.append('archivo', docUpload.file)
      fd.append('tipo_documento', docUpload.tipo_documento)
      await reclutamientoService.subirDocumentoCandidato(selectedCandidato.id, fd)
      const refreshed = await reclutamientoService.getCandidatoById(selectedCandidato.id)
      setSelectedCandidato(refreshed)
      setDocUpload({ tipo_documento: 'hoja_de_vida', file: null })
      cargarDatos()
    } catch (err: any) {
      alert(err?.friendlyMessage || err?.message || 'No se pudo subir el documento.')
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
              onClick={abrirNuevaVacante}
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

          <button
            onClick={() => setActiveTab('fuentes')}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition ${
              activeTab === 'fuentes'
                ? 'border-brand-500 text-primary-500 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Tag className="w-4 h-4" />
            Fuentes ({fuentes.length})
          </button>

          <button
            onClick={() => setActiveTab('historico')}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition ${
              activeTab === 'historico'
                ? 'border-brand-500 text-primary-500 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <History className="w-4 h-4" />
            Histórico ({historico.length})
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
                    variant="secondary"
                    className="text-xs flex items-center gap-1.5"
                    onClick={() => { setBatchIds([]); setShowBatchModal(true) }}
                  >
                    <ListChecks className="w-4 h-4" />
                    Selección múltiple
                  </Button>
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
                        <th className="p-3.5 text-center">Entrevista</th>
                        <th className="p-3.5 text-center">Evaluación</th>
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
                            <div className="mt-1 flex items-center gap-2 text-[10px]">
                              <button
                                onClick={() => verDetallePostulacion(post.id)}
                                className="inline-flex items-center gap-1 text-slate-500 hover:text-primary-600 font-semibold"
                                title="Ver documentos del aspirante"
                              >
                                <FileText className="w-3 h-3" />
                                {post.documentos_count || 0} docs
                              </button>
                              {!!post.documentos_faltantes?.length && (
                                <span className="text-rose-600 font-bold">
                                  Faltan {post.documentos_faltantes.length}
                                </span>
                              )}
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

                          <td className="p-3.5 text-center">
                            <div className="font-bold text-slate-700">
                              {post.entrevista_calificacion !== null && post.entrevista_calificacion !== undefined
                                ? `${post.entrevista_calificacion} / 100`
                                : '—'}
                            </div>
                            {post.entrevista_concepto && (
                              <div className={`text-[10px] font-semibold ${post.entrevista_concepto === 'desfavorable' ? 'text-rose-700' : 'text-amber-800'}`}>
                                {post.entrevista_concepto.replace('_', ' ')}
                              </div>
                            )}
                          </td>
                          <td className="p-3.5 text-center">
                            <div className="font-bold text-slate-700">
                              {post.evaluacion_porcentaje !== null && post.evaluacion_porcentaje !== undefined
                                ? `${post.evaluacion_porcentaje}%`
                                : '—'}
                            </div>
                            {post.evaluacion_clasificacion && (
                              <div className={`text-[10px] font-semibold ${
                                post.evaluacion_clasificacion === 'critico' ? 'text-rose-700'
                                  : post.evaluacion_clasificacion === 'alerta' ? 'text-amber-700' : 'text-emerald-700'
                              }`}>
                                {post.evaluacion_clasificacion === 'critico' ? 'Crítico'
                                  : post.evaluacion_clasificacion === 'alerta' ? 'Alerta (refuerzo)' : 'Apto'}
                              </div>
                            )}
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
                                  {selectedProceso?.requiere_entrevista && post.semaforo_etapas?.entrevista?.estado !== 'completada' && (
                                    <button
                                      onClick={() => setActionModal({ type: 'entrevista', postulacion: post })}
                                      className="px-2 py-1 text-xs rounded bg-amber-50 text-amber-900 hover:bg-amber-100 font-medium"
                                    >
                                      + Entrevista
                                    </button>
                                  )}
                                  {selectedProceso?.requiere_evaluacion && post.semaforo_etapas?.evaluacion?.estado !== 'completada' && (
                                    <button
                                      onClick={() => setActionModal({ type: 'evaluacion', postulacion: post })}
                                      className="px-2 py-1 text-xs rounded bg-amber-50 text-amber-700 hover:bg-amber-100 font-medium"
                                    >
                                      + Evaluación
                                    </button>
                                  )}
                                  {selectedProceso?.requiere_validacion_documental && post.semaforo_etapas?.validacion_documental?.estado !== 'completada' && (
                                    <button
                                      onClick={() => setActionModal({ type: 'validacion', postulacion: post })}
                                      className="px-2 py-1 text-xs rounded bg-primary-50 text-primary-500 hover:bg-primary-100 font-medium"
                                    >
                                      + Validación
                                    </button>
                                  )}
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

                              {post.es_activa && (
                                <button
                                  onClick={() => { setNoSeleccionarMotivo(''); setActionModal({ type: 'no_seleccionar', postulacion: post }) }}
                                  className="px-2 py-1 text-xs rounded bg-rose-50 text-rose-700 hover:bg-rose-100 font-medium"
                                  title="No seleccionar (motivo obligatorio)"
                                >
                                  No seleccionar
                                </button>
                              )}

                              {post.es_activa && (
                                <button
                                  onClick={() => handleFaltaDocumentos(post)}
                                  className="px-2 py-1 text-xs rounded bg-amber-50 text-amber-800 hover:bg-amber-100 font-medium"
                                  title="Cerrar por falta de documentos y notificar"
                                >
                                  Falta docs
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

                              {post.estado === 'seleccionado' && (
                                <Button
                                  variant="primary"
                                  className="text-xs py-1 px-2.5 bg-primary-500 hover:bg-primary-600 flex items-center gap-1"
                                  onClick={() => handleIniciarVinculacion(post)}
                                >
                                  <UserCheck className="w-3.5 h-3.5" />
                                  Iniciar vinculación
                                </Button>
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
                    {['abierta', 'pausada'].includes(v.estado) && (
                      <button
                        onClick={async () => {
                          if (!confirm('¿Cerrar esta vacante? No admitirá más postulaciones.')) return
                          try {
                            await reclutamientoService.cerrarVacante(v.id)
                            cargarDatos()
                          } catch (err: any) {
                            alert(errMsg(err, 'No se pudo cerrar la vacante.'))
                          }
                        }}
                        className="text-xs px-2.5 py-1 rounded bg-rose-50 text-rose-700 hover:bg-rose-100 font-medium"
                      >
                        Cerrar
                      </button>
                    )}
                    {!['cubierta', 'cerrada'].includes(v.estado) && (
                      <button
                        onClick={() => abrirEdicionVacante(v.id)}
                        className="text-xs px-2.5 py-1 rounded bg-slate-100 text-slate-700 hover:bg-slate-200 font-medium"
                      >
                        Editar
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
                      reclutamientoService.getCandidatos({ search: searchCandidato, fuente_id: filtroFuente || undefined }).then(setCandidatos).catch(() => {})
                    }
                  }}
                  className="w-full text-sm pl-9 pr-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
              <select
                value={filtroFuente}
                onChange={(e) => {
                  const value = e.target.value
                  setFiltroFuente(value)
                  reclutamientoService.getCandidatos({ search: searchCandidato, fuente_id: value || undefined }).then(setCandidatos).catch(() => {})
                }}
                className="text-xs p-2 border rounded-lg"
              >
                <option value="">Todas las fuentes</option>
                {fuentes.map((f) => (
                  <option key={f.id} value={f.id}>{f.nombre}</option>
                ))}
              </select>
              <Button
                variant="secondary"
                className="text-xs"
                onClick={() => reclutamientoService.getCandidatos({ search: searchCandidato, fuente_id: filtroFuente || undefined }).then(setCandidatos).catch(() => {})}
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
                    <th className="p-3.5">Fuente</th>
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
                      <td className="p-3.5 text-slate-600">
                        {c.fuente_reclutamiento_nombre || '—'}
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
      {/* TAB 5: HISTÓRICO DE POSTULACIONES                          */}
      {/* ───────────────────────────────────────────────────────── */}
      {activeTab === 'historico' && (
        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-2">
                <select
                  value={historicoVacante}
                  onChange={(e) => setHistoricoVacante(e.target.value)}
                  className="text-xs p-2 border rounded-lg"
                >
                  <option value="">Todas las vacantes</option>
                  {vacantes.map((v) => (
                    <option key={v.id} value={v.id}>{v.codigo} — {v.titulo}</option>
                  ))}
                </select>
                <select
                  value={historicoEstado}
                  onChange={(e) => setHistoricoEstado(e.target.value)}
                  className="text-xs p-2 border rounded-lg"
                >
                  <option value="">Todos los estados</option>
                  {['postulado', 'en_revision', 'preseleccionado', 'en_entrevista', 'en_evaluacion', 'en_validacion', 'seleccionado', 'no_seleccionado', 'retiro_candidatura', 'no_continuo'].map((e) => (
                    <option key={e} value={e}>{e.replace('_', ' ')}</option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="secondary" className="text-xs flex items-center gap-1.5" onClick={() => handleExportarHistorico('csv')}>
                  <Download className="w-3.5 h-3.5" /> CSV
                </Button>
                <Button variant="secondary" className="text-xs flex items-center gap-1.5" onClick={() => handleExportarHistorico('xlsx')}>
                  <Download className="w-3.5 h-3.5" /> Excel
                </Button>
                <Button variant="secondary" className="text-xs flex items-center gap-1.5" onClick={() => handleExportarHistorico('pdf')}>
                  <Download className="w-3.5 h-3.5" /> PDF
                </Button>
              </div>
            </div>
          </Card>

          <Card className="p-0 overflow-hidden border-slate-200">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase text-[11px] font-semibold">
                    <th className="p-3.5">Vacante</th>
                    <th className="p-3.5">Candidato</th>
                    <th className="p-3.5">Estado</th>
                    <th className="p-3.5 text-center">Entrevista</th>
                    <th className="p-3.5 text-center">Evaluación</th>
                    <th className="p-3.5">Motivo cierre</th>
                    <th className="p-3.5">Fecha</th>
                    <th className="p-3.5 text-right">Ver</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {historico
                    .filter(h => {
                      if (historicoEstado && h.estado !== historicoEstado) return false
                      if (historicoVacante) {
                        const vac = vacantes.find(v => v.id === historicoVacante)
                        if (vac?.proceso_seleccion_id && h.proceso_seleccion !== vac.proceso_seleccion_id) return false
                      }
                      return true
                    })
                    .map((h) => (
                      <tr key={h.id} className="hover:bg-slate-50 transition">
                        <td className="p-3.5">
                          <div className="font-mono text-slate-500">{h.vacante_codigo}</div>
                          <div className="font-medium text-slate-800">{h.vacante_titulo}</div>
                        </td>
                        <td className="p-3.5">
                          <div className="font-bold text-slate-900">{h.candidato_nombre}</div>
                          <div className="text-slate-500 font-mono">{h.candidato_documento}</div>
                        </td>
                        <td className="p-3.5">{renderEstadoBadge(h.estado)}</td>
                        <td className="p-3.5 text-center">
                          <div className="font-bold text-slate-700">{h.entrevista_calificacion != null ? `${h.entrevista_calificacion}/100` : '—'}</div>
                          {h.entrevista_concepto && <div className="text-[10px] text-amber-800 capitalize">{h.entrevista_concepto.replace('_', ' ')}</div>}
                        </td>
                        <td className="p-3.5 text-center">
                          <div className="font-bold text-slate-700">{h.evaluacion_porcentaje != null ? `${h.evaluacion_porcentaje}%` : '—'}</div>
                          {h.evaluacion_clasificacion && (
                            <div className={`text-[10px] font-semibold ${
                              h.evaluacion_clasificacion === 'critico' ? 'text-rose-700'
                                : h.evaluacion_clasificacion === 'alerta' ? 'text-amber-700' : 'text-emerald-700'
                            }`}>
                              {h.evaluacion_clasificacion}
                            </div>
                          )}
                        </td>
                        <td className="p-3.5 text-slate-600 max-w-[16rem] truncate" title={h.motivo_cierre || ''}>{h.motivo_cierre || '—'}</td>
                        <td className="p-3.5 text-slate-600">{new Date(h.fecha_postulacion).toLocaleDateString('es-CO')}</td>
                        <td className="p-3.5 text-right">
                          <button onClick={() => verDetallePostulacion(h.id)} className="p-1.5 rounded-lg hover:bg-slate-200 text-slate-600" title="Ver historial y observaciones">
                            <Eye className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  {historico.length === 0 && (
                    <tr><td colSpan={8} className="p-8 text-center text-slate-400">Sin postulaciones registradas.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* ───────────────────────────────────────────────────────── */}
      {/* TAB 4: FUENTES DE RECLUTAMIENTO                           */}
      {/* ───────────────────────────────────────────────────────── */}
      {activeTab === 'fuentes' && (
        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-primary-500" /> Embudo de conversión por fuente
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">Candidatos → Preseleccionados → Entrevistados → Contratados</p>
              </div>
              <Button
                variant="primary"
                className="text-xs flex items-center gap-1.5"
                onClick={() => setShowNewFuenteModal(true)}
              >
                <Plus className="w-4 h-4" /> Nueva Fuente
              </Button>
            </div>
          </Card>

          <Card className="p-0 overflow-hidden border-slate-200">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase text-[11px] font-semibold">
                    <th className="p-3.5">Fuente</th>
                    <th className="p-3.5 text-center">Candidatos</th>
                    <th className="p-3.5 text-center">Preseleccionados</th>
                    <th className="p-3.5 text-center">Entrevistados</th>
                    <th className="p-3.5 text-center">Contratados</th>
                    <th className="p-3.5 text-center">Conversión</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {indicadores.map((i) => (
                    <tr key={i.fuente_id} className="hover:bg-slate-50 transition">
                      <td className="p-3.5 font-semibold text-slate-800">{i.fuente_nombre}</td>
                      <td className="p-3.5 text-center font-mono">{i.candidatos}</td>
                      <td className="p-3.5 text-center font-mono text-blue-700">{i.preseleccionados}</td>
                      <td className="p-3.5 text-center font-mono text-amber-700">{i.entrevistados}</td>
                      <td className="p-3.5 text-center font-mono text-emerald-700 font-bold">{i.contratados}</td>
                      <td className="p-3.5 text-center">
                        <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700">
                          {i.tasa_conversion_porcentaje}%
                        </span>
                      </td>
                    </tr>
                  ))}
                  {indicadores.length === 0 && (
                    <tr>
                      <td colSpan={6} className="p-8 text-center text-slate-400">
                        Aún no hay fuentes de reclutamiento configuradas.
                      </td>
                    </tr>
                  )}
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
                  {ev.clasificacion && (
                    <div className={`font-semibold ${
                      ev.clasificacion === 'critico' ? 'text-rose-700'
                        : ev.clasificacion === 'alerta' ? 'text-amber-700' : 'text-emerald-700'
                    }`}>
                      {ev.clasificacion_display || ev.clasificacion}
                      {ev.requiere_refuerzo ? ' — Requiere refuerzo de competencia' : ''}
                    </div>
                  )}
                  {ev.concepto && <div className="text-slate-600 italic">"{ev.concepto}"</div>}
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

            {/* Documentos del aspirante */}
            <div className="space-y-2">
              <h4 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                <FileText className="w-4 h-4 text-primary-500" />
                Documentos del aspirante ({selectedPostulacion.documentos?.length || 0})
              </h4>

              {!!selectedPostulacion.documentos_requeridos?.length && (
                <div className={`p-3 rounded-lg border text-xs ${
                  selectedPostulacion.documentos_faltantes?.length
                    ? 'bg-rose-50 border-rose-200 text-rose-700'
                    : 'bg-emerald-50 border-emerald-200 text-emerald-700'
                }`}>
                  {selectedPostulacion.documentos_faltantes?.length ? (
                    <span><b>Faltan documentos:</b> {selectedPostulacion.documentos_faltantes.map(docLabel).join(', ')}</span>
                  ) : (
                    <span><b>Documentación requerida completa.</b></span>
                  )}
                </div>
              )}

              {selectedPostulacion.documentos?.length ? (
                <ul className="space-y-1.5">
                  {selectedPostulacion.documentos.map((d) => (
                    <li key={d.id} className="flex items-center justify-between bg-slate-50 rounded-lg px-3 py-2 text-xs">
                      <span className="text-slate-700">
                        <b>{d.tipo_documento_display}</b>: {d.nombre_descriptivo || d.archivo_nombre || 'Documento'}
                      </span>
                      {d.archivo_url && (
                        <a href={d.archivo_url} target="_blank" rel="noopener noreferrer" className="text-primary-500 hover:underline flex items-center gap-1">
                          Ver <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="text-xs text-slate-400">Sin documentos cargados.</div>
              )}
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

              <div className="pt-2 border-t">
                <label className="flex items-center gap-2 cursor-pointer text-amber-800">
                  <input
                    type="checkbox"
                    checked={preseleccionarForm.es_excepcion}
                    onChange={(e) => setPreseleccionarForm(p => ({ ...p, es_excepcion: e.target.checked }))}
                    className="rounded text-amber-600"
                  />
                  <span className="font-medium">Autorizar por excepción (RN-R09)</span>
                </label>
                {preseleccionarForm.es_excepcion && (
                  <textarea
                    rows={2}
                    className="w-full mt-2 p-2 border rounded-lg"
                    placeholder="Justificación obligatoria de la excepción..."
                    value={preseleccionarForm.justificacion_excepcion}
                    onChange={(e) => setPreseleccionarForm(p => ({ ...p, justificacion_excepcion: e.target.value }))}
                  />
                )}
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

            <div className="space-y-2 text-xs">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Notas finales (opcional):</label>
                <textarea
                  rows={2}
                  className="w-full p-2 border rounded-lg"
                  value={seleccionarForm.notas_finales}
                  onChange={(e) => setSeleccionarForm(p => ({ ...p, notas_finales: e.target.value }))}
                />
              </div>

              <div className="pt-2 border-t">
                <label className="flex items-center gap-2 cursor-pointer text-amber-800">
                  <input
                    type="checkbox"
                    checked={seleccionarForm.es_excepcion}
                    onChange={(e) => setSeleccionarForm(p => ({ ...p, es_excepcion: e.target.checked }))}
                    className="rounded text-amber-600"
                  />
                  <span className="font-medium">Seleccionar por excepción (RN-R09)</span>
                </label>
                {seleccionarForm.es_excepcion && (
                  <textarea
                    rows={2}
                    className="w-full mt-2 p-2 border rounded-lg"
                    placeholder="Justificación obligatoria de la excepción..."
                    value={seleccionarForm.justificacion_excepcion}
                    onChange={(e) => setSeleccionarForm(p => ({ ...p, justificacion_excepcion: e.target.value }))}
                  />
                )}
              </div>
            </div>

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
            <h3 className="text-base font-bold text-slate-900">
              {editingVacanteId ? 'Editar Requerimiento / Vacante' : 'Crear Requerimiento / Vacante'}
            </h3>

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

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Tipo de Contrato:</label>
                  <select
                    value={newVacanteData.tipo_contrato}
                    onChange={(e) => setNewVacanteData(p => ({ ...p, tipo_contrato: e.target.value }))}
                    className="w-full p-2 border rounded-lg"
                  >
                    <option value="Termino Indefinido">Término Indefinido</option>
                    <option value="Termino Fijo">Término Fijo</option>
                    <option value="Obra o Labor">Obra o Labor</option>
                    <option value="Prestación de Servicios">Prestación de Servicios</option>
                    <option value="Aprendizaje">Aprendizaje</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Salario (mín / máx):</label>
                  <div className="flex gap-2">
                    <input
                      type="number" min="0" placeholder="Mín"
                      value={newVacanteData.rango_salarial_min}
                      onChange={(e) => setNewVacanteData(p => ({ ...p, rango_salarial_min: e.target.value }))}
                      className="w-full p-2 border rounded-lg"
                    />
                    <input
                      type="number" min="0" placeholder="Máx"
                      value={newVacanteData.rango_salarial_max}
                      onChange={(e) => setNewVacanteData(p => ({ ...p, rango_salarial_max: e.target.value }))}
                      className="w-full p-2 border rounded-lg"
                    />
                  </div>
                </div>
              </div>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={newVacanteData.mostrar_salario_publico}
                  onChange={(e) => setNewVacanteData(p => ({ ...p, mostrar_salario_publico: e.target.checked }))}
                  className="rounded text-primary-500"
                />
                <span>Mostrar salario en el portal público</span>
              </label>

              <div className="pt-2 border-t">
                <label className="block text-slate-700 font-medium mb-1.5">Etapas obligatorias del proceso:</label>
                <div className="flex flex-wrap gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={newVacanteData.requiere_entrevista}
                      onChange={(e) => setNewVacanteData(p => ({ ...p, requiere_entrevista: e.target.checked }))}
                      className="rounded text-primary-500"
                    />
                    <span>Entrevista</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={newVacanteData.requiere_evaluacion}
                      onChange={(e) => setNewVacanteData(p => ({ ...p, requiere_evaluacion: e.target.checked }))}
                      className="rounded text-primary-500"
                    />
                    <span>Evaluación</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={newVacanteData.requiere_validacion_documental}
                      onChange={(e) => setNewVacanteData(p => ({ ...p, requiere_validacion_documental: e.target.checked }))}
                      className="rounded text-primary-500"
                    />
                    <span>Validación documental</span>
                  </label>
                </div>
              </div>

              <div className="pt-2 border-t">
                <label className="block text-slate-700 font-medium mb-1.5">Documentos requeridos del aspirante:</label>
                <div className="flex flex-wrap gap-x-4 gap-y-2">
                  {DOC_TIPOS.map(([value, label]) => (
                    <label key={value} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={newVacanteData.documentos_requeridos.includes(value)}
                        onChange={(e) => setNewVacanteData((p) => ({
                          ...p,
                          documentos_requeridos: e.target.checked
                            ? [...p.documentos_requeridos, value]
                            : p.documentos_requeridos.filter((x) => x !== value),
                        }))}
                        className="rounded text-primary-500"
                      />
                      <span>{label}</span>
                    </label>
                  ))}
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
              <Button variant="secondary" className="text-xs" onClick={() => { setShowNewVacanteModal(false); setEditingVacanteId(null) }}>
                Cancelar
              </Button>
              <Button variant="primary" className="text-xs" onClick={handleCreateVacante}>
                {editingVacanteId ? 'Guardar Cambios' : 'Crear Vacante'}
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* ───────────────────────────────────────────────────────── */}
      {/* MODAL: NO SELECCIONAR (RN-R04)                            */}
      {/* ───────────────────────────────────────────────────────── */}
      {actionModal.type === 'no_seleccionar' && actionModal.postulacion && (
        <Modal open={true} onClose={() => setActionModal({ type: null })} title="No seleccionar candidato (RN-R04)" maxWidth="28rem">
          <div className="space-y-4 text-xs">
            <p className="text-slate-600">
              Registra el motivo por el cual <b>{actionModal.postulacion.candidato_nombre}</b> no continúa en el proceso.
            </p>
            <textarea
              rows={3}
              className="w-full p-2 border rounded-lg"
              placeholder="Motivo obligatorio..."
              value={noSeleccionarMotivo}
              onChange={(e) => setNoSeleccionarMotivo(e.target.value)}
            />
            <div className="flex justify-end gap-2">
              <Button variant="secondary" className="text-xs" onClick={() => setActionModal({ type: null })}>Cancelar</Button>
              <Button variant="primary" className="text-xs bg-rose-600 hover:bg-rose-700" onClick={handleNoSeleccionar}>No seleccionar</Button>
            </div>
          </div>
        </Modal>
      )}

      {/* ───────────────────────────────────────────────────────── */}
      {/* MODAL: SELECCIÓN MÚLTIPLE POR CUPOS                       */}
      {/* ───────────────────────────────────────────────────────── */}
      {showBatchModal && selectedProceso && (() => {
        const disponibles = selectedProceso.vacante_detalle?.cupos_disponibles ?? 0
        const elegibles = selectedProceso.postulaciones.filter(p =>
          ['preseleccionado', 'en_entrevista', 'en_evaluacion', 'en_validacion'].includes(p.estado)
        )
        return (
          <Modal open={true} onClose={() => setShowBatchModal(false)} title="Selección múltiple de candidatos" maxWidth="40rem">
            <div className="space-y-4 text-xs">
              <p className="text-slate-600">
                Cupos disponibles en la vacante: <b>{disponibles}</b>. Seleccione hasta esa cantidad.
              </p>
              <div className="max-h-80 overflow-y-auto border rounded-lg divide-y divide-slate-100">
                {elegibles.map((p) => {
                  const checked = batchIds.includes(p.id)
                  const disabled = !checked && batchIds.length >= disponibles
                  return (
                    <label key={p.id} className={`flex items-center gap-3 p-3 cursor-pointer hover:bg-slate-50 ${disabled ? 'opacity-50' : ''}`}>
                      <input
                        type="checkbox"
                        checked={checked}
                        disabled={disabled}
                        onChange={(e) => setBatchIds((prev) =>
                          e.target.checked ? [...prev, p.id] : prev.filter((x) => x !== p.id)
                        )}
                        className="rounded text-primary-500"
                      />
                      <span className="flex-1">
                        <span className="font-bold text-slate-800">{p.candidato_nombre}</span>
                        <span className="text-slate-500"> · {p.estado.replace('_', ' ')}</span>
                      </span>
                      {p.entrevista_calificacion != null && (
                        <span className="text-slate-500">Entrevista {p.entrevista_calificacion}/100</span>
                      )}
                      {p.evaluacion_porcentaje != null && (
                        <span className="text-slate-500">Evaluación {p.evaluacion_porcentaje}%</span>
                      )}
                    </label>
                  )
                })}
                {elegibles.length === 0 && (
                  <div className="p-6 text-center text-slate-400">No hay candidatos elegibles para seleccionar.</div>
                )}
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="secondary" className="text-xs" onClick={() => setShowBatchModal(false)}>Cancelar</Button>
                <Button variant="primary" className="text-xs" onClick={handleSeleccionMasiva}>
                  Confirmar selección ({batchIds.length})
                </Button>
              </div>
            </div>
          </Modal>
        )
      })()}

      {/* ───────────────────────────────────────────────────────── */}
      {/* MODAL: PAQUETE DE VINCULACIÓN (Hand-off)                  */}
      {/* ───────────────────────────────────────────────────────── */}
      {paqueteVinculacion && (
        <Modal
          open={true}
          onClose={() => setPaqueteVinculacion(null)}
          title="Paquete de Vinculación — Hand-off a Gestión Humana"
          maxWidth="42rem"
        >
          <div className="space-y-4 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="bg-slate-50 rounded-lg p-3">
                <div className="font-bold text-slate-800 mb-1">Candidato</div>
                <div className="text-slate-700">{paqueteVinculacion.candidato?.nombres} {paqueteVinculacion.candidato?.apellidos}</div>
                <div className="text-slate-500 font-mono">{paqueteVinculacion.candidato?.tipo_documento} {paqueteVinculacion.candidato?.documento}</div>
                <div className="text-slate-500">{paqueteVinculacion.candidato?.email}</div>
              </div>
              <div className="bg-slate-50 rounded-lg p-3">
                <div className="font-bold text-slate-800 mb-1">Cargo propuesto</div>
                <div className="text-slate-700">{paqueteVinculacion.cargo_propuesto?.nombre_cargo}</div>
                <div className="text-slate-500 font-mono">{paqueteVinculacion.cargo_propuesto?.codigo} · {paqueteVinculacion.cargo_propuesto?.area}</div>
              </div>
              <div className="bg-slate-50 rounded-lg p-3 sm:col-span-2">
                <div className="font-bold text-slate-800 mb-1">Condiciones laborales</div>
                <div className="text-slate-600">Sede: {paqueteVinculacion.condiciones_laborales?.sede_nombre || '—'} · Modalidad: {paqueteVinculacion.condiciones_laborales?.modalidad} · Contrato: {paqueteVinculacion.condiciones_laborales?.tipo_contrato}</div>
                <div className="text-slate-600">Salario: {paqueteVinculacion.condiciones_laborales?.rango_salarial}</div>
              </div>
            </div>

            <div>
              <div className="font-bold text-slate-800 mb-2">Checklist de ingreso</div>
              <ul className="space-y-1">
                {(paqueteVinculacion.checklist_ingreso || []).map((c: any, i: number) => (
                  <li key={i} className="flex items-center gap-2 text-slate-700">
                    <span className="w-2 h-2 rounded-full bg-slate-300" /> {c.item}
                  </li>
                ))}
              </ul>
            </div>

            {!!(paqueteVinculacion.documentos_soporte || []).length && (
              <div>
                <div className="font-bold text-slate-800 mb-2">Documentos ({paqueteVinculacion.documentos_soporte.length})</div>
                <ul className="space-y-1">
                  {paqueteVinculacion.documentos_soporte.map((d: any, i: number) => (
                    <li key={i} className="flex items-center justify-between text-slate-700">
                      <span>{d.tipo}: {d.nombre}</span>
                      {d.url && (
                        <a href={d.url} target="_blank" rel="noopener noreferrer" className="text-primary-500 hover:underline">Ver</a>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <p className="text-[11px] text-slate-400 border-t pt-2">
              Este paquete es el hand-off hacia el módulo de Gestión Humana / Contratación.
            </p>

            <div className="flex justify-end">
              <Button variant="secondary" className="text-xs" onClick={() => setPaqueteVinculacion(null)}>Cerrar</Button>
            </div>
          </div>
        </Modal>
      )}

      {/* ───────────────────────────────────────────────────────── */}
      {/* MODAL: DETALLE DEL CANDIDATO (Banco de Talento)           */}
      {/* ───────────────────────────────────────────────────────── */}
      {selectedCandidato && (
        <Modal
          open={true}
          onClose={() => { setSelectedCandidato(null); setEditingCandidato(false) }}
          title="Perfil del Candidato"
          maxWidth="48rem"
        >
          <div className="space-y-5 text-xs">
            {/* Encabezado + acciones */}
            <div className="flex items-start justify-between gap-3 border-b border-slate-100 pb-3">
              <div>
                <div className="text-base font-bold text-slate-900">{selectedCandidato.nombre_completo}</div>
                <div className="text-slate-500 font-mono">
                  {selectedCandidato.tipo_documento_display} {selectedCandidato.documento} • {selectedCandidato.email}
                </div>
                {selectedCandidato.fuente_reclutamiento_nombre && (
                  <div className="text-slate-400 mt-0.5">Fuente: {selectedCandidato.fuente_reclutamiento_nombre}</div>
                )}
              </div>
              {editingCandidato ? (
                <div className="flex gap-2 flex-shrink-0">
                  <Button variant="secondary" className="text-xs" onClick={() => setEditingCandidato(false)}>Cancelar</Button>
                  <Button variant="primary" className="text-xs" onClick={handleSaveCandidato}>Guardar</Button>
                </div>
              ) : (
                <Button
                  variant="secondary"
                  className="text-xs flex items-center gap-1.5 flex-shrink-0"
                  onClick={() => abrirEdicionCandidato(selectedCandidato)}
                >
                  <Pencil className="w-3.5 h-3.5" /> Editar
                </Button>
              )}
            </div>

            {editingCandidato ? (
              /* ── Modo edición ── */
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-700 font-medium mb-1">Nombres</label>
                    <input className="w-full p-2 border rounded-lg" value={editCandidatoData.nombres || ''}
                      onChange={(e) => setEditCandidatoData((p: any) => ({ ...p, nombres: e.target.value }))} />
                  </div>
                  <div>
                    <label className="block text-slate-700 font-medium mb-1">Apellidos</label>
                    <input className="w-full p-2 border rounded-lg" value={editCandidatoData.apellidos || ''}
                      onChange={(e) => setEditCandidatoData((p: any) => ({ ...p, apellidos: e.target.value }))} />
                  </div>
                  <div>
                    <label className="block text-slate-700 font-medium mb-1">Correo</label>
                    <input className="w-full p-2 border rounded-lg" value={editCandidatoData.email || ''}
                      onChange={(e) => setEditCandidatoData((p: any) => ({ ...p, email: e.target.value }))} />
                  </div>
                  <div>
                    <label className="block text-slate-700 font-medium mb-1">Teléfono</label>
                    <input className="w-full p-2 border rounded-lg" value={editCandidatoData.telefono || ''}
                      onChange={(e) => setEditCandidatoData((p: any) => ({ ...p, telefono: e.target.value }))} />
                  </div>
                  <div>
                    <label className="block text-slate-700 font-medium mb-1">Ciudad</label>
                    <input className="w-full p-2 border rounded-lg" value={editCandidatoData.ciudad || ''}
                      onChange={(e) => setEditCandidatoData((p: any) => ({ ...p, ciudad: e.target.value }))} />
                  </div>
                  <div>
                    <label className="block text-slate-700 font-medium mb-1">Dirección</label>
                    <input className="w-full p-2 border rounded-lg" value={editCandidatoData.direccion || ''}
                      onChange={(e) => setEditCandidatoData((p: any) => ({ ...p, direccion: e.target.value }))} />
                  </div>
                  <div>
                    <label className="block text-slate-700 font-medium mb-1">Departamento</label>
                    <input className="w-full p-2 border rounded-lg" value={editCandidatoData.departamento || ''}
                      onChange={(e) => setEditCandidatoData((p: any) => ({ ...p, departamento: e.target.value }))} />
                  </div>
                  <div>
                    <label className="block text-slate-700 font-medium mb-1">Municipio</label>
                    <input className="w-full p-2 border rounded-lg" value={editCandidatoData.municipio || ''}
                      onChange={(e) => setEditCandidatoData((p: any) => ({ ...p, municipio: e.target.value }))} />
                  </div>
                  <div>
                    <label className="block text-slate-700 font-medium mb-1">Estado del perfil</label>
                    <select className="w-full p-2 border rounded-lg" value={editCandidatoData.estado_perfil || 'activo'}
                      onChange={(e) => setEditCandidatoData((p: any) => ({ ...p, estado_perfil: e.target.value }))}>
                      <option value="activo">Activo</option>
                      <option value="en_busqueda">En búsqueda</option>
                      <option value="contratado">Contratado</option>
                      <option value="descartado">Descartado</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-slate-700 font-medium mb-1">Fuente de reclutamiento</label>
                    <select className="w-full p-2 border rounded-lg" value={editCandidatoData.fuente_reclutamiento || ''}
                      onChange={(e) => setEditCandidatoData((p: any) => ({ ...p, fuente_reclutamiento: e.target.value || null }))}>
                      <option value="">— Sin especificar —</option>
                      {fuentes.map((f) => (
                        <option key={f.id} value={f.id}>{f.nombre}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-700 font-medium mb-1">Título / Profesión</label>
                    <input className="w-full p-2 border rounded-lg" value={editCandidatoData.perfil?.titulo_profesional || ''}
                      onChange={(e) => setEditCandidatoData((p: any) => ({ ...p, perfil: { ...p.perfil, titulo_profesional: e.target.value } }))} />
                  </div>
                  <div>
                    <label className="block text-slate-700 font-medium mb-1">Nivel educativo</label>
                    <select className="w-full p-2 border rounded-lg" value={editCandidatoData.perfil?.nivel_educativo || ''}
                      onChange={(e) => setEditCandidatoData((p: any) => ({ ...p, perfil: { ...p.perfil, nivel_educativo: e.target.value } }))}>
                      <option value="">—</option>
                      <option value="primaria">Primaria</option>
                      <option value="bachillerato">Bachillerato</option>
                      <option value="tecnico">Técnico</option>
                      <option value="tecnologo">Tecnólogo</option>
                      <option value="universitario">Universitario</option>
                      <option value="especializacion">Especialización</option>
                      <option value="maestria">Maestría</option>
                      <option value="doctorado">Doctorado</option>
                      <option value="otro">Otro</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-slate-700 font-medium mb-1">Años de experiencia</label>
                    <input type="number" min={0} step={0.5} className="w-full p-2 border rounded-lg" value={editCandidatoData.perfil?.anios_experiencia ?? 0}
                      onChange={(e) => setEditCandidatoData((p: any) => ({ ...p, perfil: { ...p.perfil, anios_experiencia: Number(e.target.value) } }))} />
                  </div>
                  <div>
                    <label className="block text-slate-700 font-medium mb-1">Aspiración salarial</label>
                    <input type="number" min={0} className="w-full p-2 border rounded-lg" value={editCandidatoData.perfil?.aspiracion_salarial ?? ''}
                      onChange={(e) => setEditCandidatoData((p: any) => ({ ...p, perfil: { ...p.perfil, aspiracion_salarial: e.target.value ? Number(e.target.value) : null } }))} />
                  </div>
                  <div>
                    <label className="block text-slate-700 font-medium mb-1">Profesión</label>
                    <input className="w-full p-2 border rounded-lg" value={editCandidatoData.perfil?.profesion || ''}
                      onChange={(e) => setEditCandidatoData((p: any) => ({ ...p, perfil: { ...p.perfil, profesion: e.target.value } }))} />
                  </div>
                  <div>
                    <label className="block text-slate-700 font-medium mb-1">Área de conocimiento</label>
                    <input className="w-full p-2 border rounded-lg" value={editCandidatoData.perfil?.area_conocimiento || ''}
                      onChange={(e) => setEditCandidatoData((p: any) => ({ ...p, perfil: { ...p.perfil, area_conocimiento: e.target.value } }))} />
                  </div>
                  <div>
                    <label className="block text-slate-700 font-medium mb-1">Disponibilidad</label>
                    <select className="w-full p-2 border rounded-lg" value={editCandidatoData.perfil?.disponibilidad || ''}
                      onChange={(e) => setEditCandidatoData((p: any) => ({ ...p, perfil: { ...p.perfil, disponibilidad: e.target.value } }))}>
                      <option value="">—</option>
                      <option value="inmediata">Inmediata</option>
                      <option value="con_preaviso">Con preaviso</option>
                      <option value="no_disponible">No disponible</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-slate-700 font-medium mb-1">Resumen profesional</label>
                  <textarea rows={3} className="w-full p-2 border rounded-lg" value={editCandidatoData.perfil?.resumen_profesional || ''}
                    onChange={(e) => setEditCandidatoData((p: any) => ({ ...p, perfil: { ...p.perfil, resumen_profesional: e.target.value } }))} />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-700 font-medium mb-1">Competencias (separadas por coma)</label>
                    <input className="w-full p-2 border rounded-lg"
                      value={Array.isArray(editCandidatoData.perfil?.competencias) ? editCandidatoData.perfil.competencias.join(', ') : ''}
                      onChange={(e) => setEditCandidatoData((p: any) => ({ ...p, perfil: { ...p.perfil, competencias: e.target.value.split(',').map((s: string) => s.trim()).filter(Boolean) } }))} />
                  </div>
                  <div>
                    <label className="block text-slate-700 font-medium mb-1">Certificaciones / Licencias (separadas por coma)</label>
                    <input className="w-full p-2 border rounded-lg"
                      value={Array.isArray(editCandidatoData.perfil?.certificaciones) ? editCandidatoData.perfil.certificaciones.join(', ') : ''}
                      onChange={(e) => setEditCandidatoData((p: any) => ({ ...p, perfil: { ...p.perfil, certificaciones: e.target.value.split(',').map((s: string) => s.trim()).filter(Boolean) } }))} />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-slate-700 font-medium mb-1">Cargos de interés (separados por coma)</label>
                    <input className="w-full p-2 border rounded-lg"
                      value={Array.isArray(editCandidatoData.perfil?.cargos_interes) ? editCandidatoData.perfil.cargos_interes.join(', ') : ''}
                      onChange={(e) => setEditCandidatoData((p: any) => ({ ...p, perfil: { ...p.perfil, cargos_interes: e.target.value.split(',').map((s: string) => s.trim()).filter(Boolean) } }))} />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-700 font-medium mb-1">Notas internas</label>
                  <textarea rows={2} className="w-full p-2 border rounded-lg" value={editCandidatoData.notas_internas || ''}
                    onChange={(e) => setEditCandidatoData((p: any) => ({ ...p, notas_internas: e.target.value }))} />
                </div>
              </div>
            ) : (
              /* ── Modo lectura ── */
              <div className="space-y-5">
                {/* Datos personales */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div><div className="text-slate-400">Teléfono</div><div className="font-medium text-slate-800">{selectedCandidato.telefono || '—'}</div></div>
                  <div><div className="text-slate-400">Ciudad</div><div className="font-medium text-slate-800">{selectedCandidato.ciudad || '—'}</div></div>
                  <div><div className="text-slate-400">Dirección</div><div className="font-medium text-slate-800">{selectedCandidato.direccion || '—'}</div></div>
                  <div><div className="text-slate-400">Habeas Data</div><div className="font-medium text-slate-800">{selectedCandidato.autoriza_tratamiento_datos ? 'Autorizado' : 'Sin autorizar'}</div></div>
                  <div><div className="text-slate-400">Estado del perfil</div><div className="font-medium text-slate-800">{selectedCandidato.estado_perfil_display || selectedCandidato.estado_perfil || '—'}</div></div>
                </div>

                {/* Perfil profesional */}
                <div className="bg-slate-50 rounded-lg p-4 space-y-3">
                  <div className="font-bold text-slate-800 flex items-center gap-2"><Award className="w-4 h-4 text-primary-500" /> Perfil Profesional</div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    <div><div className="text-slate-400">Título</div><div className="font-medium text-slate-800">{selectedCandidato.perfil?.titulo_profesional || '—'}</div></div>
                    <div><div className="text-slate-400">Profesión</div><div className="font-medium text-slate-800">{selectedCandidato.perfil?.profesion || '—'}</div></div>
                    <div><div className="text-slate-400">Área de conocimiento</div><div className="font-medium text-slate-800">{selectedCandidato.perfil?.area_conocimiento || '—'}</div></div>
                    <div><div className="text-slate-400">Nivel educativo</div><div className="font-medium text-slate-800">{selectedCandidato.perfil?.nivel_educativo || '—'}</div></div>
                    <div><div className="text-slate-400">Disponibilidad</div><div className="font-medium text-slate-800">{selectedCandidato.perfil?.disponibilidad || '—'}</div></div>
                    <div><div className="text-slate-400">Experiencia</div><div className="font-medium text-slate-800">{selectedCandidato.perfil?.anios_experiencia ?? 0} años</div></div>
                    <div><div className="text-slate-400">Aspiración salarial</div><div className="font-medium text-slate-800">{selectedCandidato.perfil?.aspiracion_salarial ? `$${Number(selectedCandidato.perfil.aspiracion_salarial).toLocaleString('es-CO')}` : '—'}</div></div>
                    <div><div className="text-slate-400">Disponibilidad viaje</div><div className="font-medium text-slate-800">{selectedCandidato.perfil?.disponibilidad_viaje ? 'Sí' : 'No'}</div></div>
                    <div><div className="text-slate-400">Disponibilidad traslado</div><div className="font-medium text-slate-800">{selectedCandidato.perfil?.disponibilidad_traslado ? 'Sí' : 'No'}</div></div>
                  </div>
                  {selectedCandidato.perfil?.resumen_profesional && (
                    <div><div className="text-slate-400 mb-1">Resumen</div><p className="text-slate-700">{selectedCandidato.perfil.resumen_profesional}</p></div>
                  )}
                  {!!selectedCandidato.perfil?.competencias?.length && (
                    <div>
                      <div className="text-slate-400 mb-1">Competencias</div>
                      <div className="flex flex-wrap gap-1.5">
                        {selectedCandidato.perfil.competencias.map((c, i) => (
                          <span key={i} className="px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-700">{c}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  {!!selectedCandidato.perfil?.cargos_interes?.length && (
                    <div>
                      <div className="text-slate-400 mb-1">Cargos de interés</div>
                      <div className="flex flex-wrap gap-1.5">
                        {selectedCandidato.perfil.cargos_interes.map((c, i) => (
                          <span key={i} className="px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-700">{c}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  {!!selectedCandidato.perfil?.certificaciones?.length && (
                    <div>
                      <div className="text-slate-400 mb-1">Certificaciones / Licencias</div>
                      <div className="flex flex-wrap gap-1.5">
                        {selectedCandidato.perfil.certificaciones.map((c, i) => (
                          <span key={i} className="px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-700">{c}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Documentos */}
                <div>
                  <div className="font-bold text-slate-800 flex items-center gap-2 mb-2"><FileText className="w-4 h-4 text-primary-500" /> Documentos ({selectedCandidato.documentos?.length || 0})</div>
                  {selectedCandidato.documentos?.length ? (
                    <ul className="space-y-1.5">
                      {selectedCandidato.documentos.map((d) => (
                        <li key={d.id} className="flex items-center justify-between bg-slate-50 rounded-lg px-3 py-2">
                          <span className="text-slate-700">{d.tipo_documento_display}: <span className="font-medium">{d.nombre_descriptivo || d.archivo_nombre || 'Documento'}</span></span>
                          {d.archivo_url && (
                            <a href={d.archivo_url} target="_blank" rel="noopener noreferrer" className="text-primary-500 hover:underline flex items-center gap-1">
                              Ver <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <div className="text-slate-400">Sin documentos cargados.</div>
                  )}

                  <div className="mt-3 flex flex-col sm:flex-row gap-2 sm:items-center bg-white border border-dashed border-slate-300 rounded-lg p-3">
                    <select
                      value={docUpload.tipo_documento}
                      onChange={(e) => setDocUpload((p) => ({ ...p, tipo_documento: e.target.value }))}
                      className="p-2 border rounded-lg"
                    >
                      <option value="hoja_de_vida">Hoja de Vida</option>
                      <option value="certificacion_laboral">Certificación Laboral</option>
                      <option value="certificacion_academica">Certificación Académica</option>
                      <option value="licencia_conduccion">Licencia de Conducción</option>
                      <option value="licencia_sst">Licencia SST</option>
                      <option value="certificacion_alturas">Certificación Alturas</option>
                      <option value="cedula">Documento de Identidad</option>
                      <option value="otro">Otro</option>
                    </select>
                    <input
                      type="file"
                      accept=".pdf,.jpg,.jpeg,.png,.webp,.docx,.xlsx,.csv"
                      onChange={(e) => setDocUpload((p) => ({ ...p, file: e.target.files?.[0] || null }))}
                      className="flex-1 text-slate-600"
                    />
                    <Button
                      variant="primary"
                      className="text-xs"
                      onClick={handleSubirDocumento}
                      disabled={!docUpload.file}
                    >
                      Subir Documento
                    </Button>
                  </div>
                </div>

                {/* Historial de postulaciones */}
                <div>
                  <div className="font-bold text-slate-800 flex items-center gap-2 mb-2"><GitPullRequest className="w-4 h-4 text-primary-500" /> Historial de Postulaciones ({selectedCandidato.historial_postulaciones?.length || 0})</div>
                  {selectedCandidato.historial_postulaciones?.length ? (
                    <div className="overflow-x-auto border border-slate-100 rounded-lg">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="bg-slate-50 text-slate-500 uppercase text-[10px] font-semibold">
                            <th className="p-2.5">Vacante</th>
                            <th className="p-2.5">Estado</th>
                            <th className="p-2.5">Fecha</th>
                            <th className="p-2.5 text-right">Puntaje</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {selectedCandidato.historial_postulaciones.map((h) => (
                            <tr key={h.id}>
                              <td className="p-2.5">
                                <div className="font-mono text-slate-500">{h.vacante_codigo}</div>
                                <div className="font-medium text-slate-800">{h.vacante_titulo}</div>
                              </td>
                              <td className="p-2.5">{renderEstadoBadge(h.estado)}</td>
                              <td className="p-2.5 text-slate-600">{new Date(h.fecha_postulacion).toLocaleDateString('es-CO')}</td>
                              <td className="p-2.5 text-right font-mono text-slate-700">{h.puntuacion_general ?? '—'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="text-slate-400">Sin postulaciones registradas.</div>
                  )}
                </div>
              </div>
            )}
          </div>
        </Modal>
      )}

      {/* ───────────────────────────────────────────────────────── */}
      {/* MODAL: NUEVA FUENTE DE RECLUTAMIENTO                     */}
      {/* ───────────────────────────────────────────────────────── */}
      {showNewFuenteModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <Card className="max-w-md w-full p-6 space-y-4 bg-white shadow-2xl">
            <h3 className="text-base font-bold text-slate-900">Nueva Fuente de Reclutamiento</h3>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Nombre</label>
                <input className="w-full p-2 border rounded-lg" value={newFuenteData.nombre}
                  onChange={(e) => setNewFuenteData((p) => ({ ...p, nombre: e.target.value }))}
                  placeholder="Ej: LinkedIn, Servicio Público de Empleo, Referido" />
              </div>
              <div>
                <label className="block text-slate-700 font-medium mb-1">Descripción</label>
                <textarea rows={2} className="w-full p-2 border rounded-lg" value={newFuenteData.descripcion}
                  onChange={(e) => setNewFuenteData((p) => ({ ...p, descripcion: e.target.value }))} />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="secondary" className="text-xs" onClick={() => setShowNewFuenteModal(false)}>Cancelar</Button>
              <Button variant="primary" className="text-xs" onClick={handleCreateFuente}>Guardar Fuente</Button>
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

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Profesión:</label>
                  <input
                    type="text"
                    value={newCandidatoData.profesion}
                    onChange={(e) => setNewCandidatoData(p => ({ ...p, profesion: e.target.value }))}
                    className="w-full p-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Área de conocimiento:</label>
                  <input
                    type="text"
                    value={newCandidatoData.area_conocimiento}
                    onChange={(e) => setNewCandidatoData(p => ({ ...p, area_conocimiento: e.target.value }))}
                    className="w-full p-2 border rounded-lg"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Ciudad:</label>
                  <input
                    type="text"
                    value={newCandidatoData.ciudad}
                    onChange={(e) => setNewCandidatoData(p => ({ ...p, ciudad: e.target.value }))}
                    className="w-full p-2 border rounded-lg"
                    placeholder="Ej: Popayán"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Nivel Educativo:</label>
                  <select
                    value={newCandidatoData.nivel_educativo}
                    onChange={(e) => setNewCandidatoData(p => ({ ...p, nivel_educativo: e.target.value }))}
                    className="w-full p-2 border rounded-lg"
                  >
                    <option value="primaria">Primaria</option>
                    <option value="bachillerato">Bachillerato</option>
                    <option value="tecnico">Técnico</option>
                    <option value="tecnologo">Tecnólogo</option>
                    <option value="universitario">Universitario</option>
                    <option value="especializacion">Especialización</option>
                    <option value="maestria">Maestría</option>
                    <option value="doctorado">Doctorado</option>
                    <option value="otro">Otro</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Años de Experiencia:</label>
                <input
                  type="number"
                  min={0}
                  step={0.5}
                  value={newCandidatoData.anios_experiencia}
                  onChange={(e) => setNewCandidatoData(p => ({ ...p, anios_experiencia: Number(e.target.value) }))}
                  className="w-full p-2 border rounded-lg"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Fuente de reclutamiento:</label>
                <select
                  value={newCandidatoData.fuente_reclutamiento}
                  onChange={(e) => setNewCandidatoData(p => ({ ...p, fuente_reclutamiento: e.target.value }))}
                  className="w-full p-2 border rounded-lg"
                >
                  <option value="">— Sin especificar —</option>
                  {fuentes.map((f) => (
                    <option key={f.id} value={f.id}>{f.nombre}</option>
                  ))}
                </select>
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
