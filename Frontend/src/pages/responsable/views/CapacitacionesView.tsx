import { useState, useEffect, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Card, PageHeader, Badge, Button, EmptyState } from '@/components/ui'
import { LoadingSpinner, ErrorDisplay, Modal, FormField, Input, Textarea } from '@/components/ui/forms'
import {
  useCapacitaciones,
  useCrearCapacitacion,
  useActualizarCapacitacion,
  useInscribirParticipantes,
  useRegistrarAsistencia,
  useFinalizarCapacitacion,
} from '@/hooks/useApi'
import {
  capacitacionService,
  Capacitacion,
  ParticipanteCapacitacion,
  ParticipanteSugerido,
} from '@/services/capacitacion.service'
import { formacionService, CursoFormacion } from '@/services/formacion.service'
import { hbseoService, Brecha } from '@/services/hbseo.service'
import { gestionHumanaService, Trabajador } from '@/services/gestion-humana.service'
import {
  BookOpen, Plus, Calendar, CheckCircle2, Users, AlertTriangle,
  Award, Clock, ExternalLink, UserCheck, ShieldCheck, UserPlus,
  RefreshCw, Check, Info
} from 'lucide-react'

export default function CapacitacionesView() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { data, isLoading, error, refetch } = useCapacitaciones()
  const crearMut = useCrearCapacitacion()
  const actualizarMut = useActualizarCapacitacion()
  const inscribirMut = useInscribirParticipantes()
  const registrarAsistenciaMut = useRegistrarAsistencia()
  const finalizarMut = useFinalizarCapacitacion()

  const [filtro, setFiltro] = useState('todos')

  // Catálogos auxiliares para selector de brechas y cursos
  const [cursosCatalogo, setCursosCatalogo] = useState<CursoFormacion[]>([])
  const [brechasAbiertas, setBrechasAbiertas] = useState<Brecha[]>([])
  const [trabajadores, setTrabajadores] = useState<Trabajador[]>([])

  // Modal Programar
  const [modalProgramarOpen, setModalProgramarOpen] = useState(false)
  const [tipoNecesidad, setTipoNecesidad] = useState<'brecha' | 'curso' | 'libre'>('brecha')
  const [selectedCursoId, setSelectedCursoId] = useState<string>('')
  const [selectedBrechaId, setSelectedBrechaId] = useState<string>('')
  const [sugeridos, setSugeridos] = useState<ParticipanteSugerido[]>([])
  const [selectedSugeridosIds, setSelectedSugeridosIds] = useState<Set<string>>(new Set())
  const [loadingSugeridos, setLoadingSugeridos] = useState(false)

  const [formProgramar, setFormProgramar] = useState({
    tema: '',
    objetivo: '',
    proveedor: '',
    fecha: '',
    horas_duracion: 4,
    tiene_certificado: true,
  })

  // Modal Detalle / Asistencia
  const [modalDetalleOpen, setModalDetalleOpen] = useState(false)
  const [capacitacionSeleccionada, setCapacitacionSeleccionada] = useState<Capacitacion | null>(null)
  const [asistenciaState, setAsistenciaState] = useState<
    Record<
      string,
      {
        asistio: boolean
        certificado_url: string
        nota_evaluacion: string
        nivel_alcanzado: number
        observaciones: string
      }
    >
  >({})
  const [trabajadorAInscribirId, setTrabajadorAInscribirId] = useState('')
  const [guardandoAsistencia, setGuardandoAsistencia] = useState(false)
  const [finalizando, setFinalizando] = useState(false)

  // Carga inicial de datos auxiliares
  useEffect(() => {
    cargarAuxiliares()
  }, [])

  const cargarAuxiliares = async () => {
    try {
      const [resCursos, resBrechas, resTrabajadores] = await Promise.all([
        formacionService.getCursos(),
        hbseoService.getBrechas({ estado: 'abierta' }),
        gestionHumanaService.getTrabajadores(),
      ])

      const cursosList = Array.isArray(resCursos) ? resCursos : (resCursos as any)?.results || []
      const brechasList = Array.isArray(resBrechas) ? resBrechas : (resBrechas as any)?.results || []
      const trabList = Array.isArray(resTrabajadores) ? resTrabajadores : (resTrabajadores as any)?.results || []

      setCursosCatalogo(cursosList)
      setBrechasAbiertas(brechasList)
      setTrabajadores(trabList)
    } catch (e) {
      console.error('Error cargando catálogos auxiliares:', e)
    }
  }

  // Detectar parámetros de URL (ej. ?curso_id=... o ?brecha_ids=...) para pre-abrir modal
  useEffect(() => {
    const cursoParam = searchParams.get('curso_id')
    const brechaParam = searchParams.get('brecha_ids') || searchParams.get('brecha_id')

    if (cursoParam) {
      setTipoNecesidad('curso')
      setSelectedCursoId(cursoParam)
      setModalProgramarOpen(true)
      // Buscar el curso para llenar sugerencia
      const curso = cursosCatalogo.find((c) => c.id === cursoParam)
      if (curso) {
        setFormProgramar((prev) => ({
          ...prev,
          tema: `Capacitación y Certificación: ${curso.nombre}`,
          objetivo: `Cerrar brecha y actualizar vigencia del curso obligatorio ${curso.nombre}`,
        }))
      }
      consultarSugeridos({ curso_id: cursoParam })
    } else if (brechaParam) {
      setTipoNecesidad('brecha')
      setSelectedBrechaId(brechaParam)
      setModalProgramarOpen(true)
      consultarSugeridos({ brecha_ids: brechaParam })
    }
  }, [searchParams, cursosCatalogo])

  const consultarSugeridos = async (params: { curso_id?: string; competencia_id?: string; brecha_ids?: string }) => {
    setLoadingSugeridos(true)
    try {
      const res = await capacitacionService.sugerirParticipantes(params)
      setSugeridos(res)
      // Por defecto seleccionar a todos los sugeridos
      setSelectedSugeridosIds(new Set(res.map((s) => s.trabajador_id)))
    } catch (e) {
      console.error('Error consultando participantes sugeridos:', e)
    } finally {
      setLoadingSugeridos(false)
    }
  }

  const handleTipoNecesidadChange = (tipo: 'brecha' | 'curso' | 'libre') => {
    setTipoNecesidad(tipo)
    setSelectedCursoId('')
    setSelectedBrechaId('')
    setSugeridos([])
    setSelectedSugeridosIds(new Set())
  }

  const handleSelectBrecha = (brechaId: string) => {
    setSelectedBrechaId(brechaId)
    const b = brechasAbiertas.find((x) => x.id === brechaId)
    if (b) {
      setFormProgramar((prev) => ({
        ...prev,
        tema: `Cierre de Brecha: ${b.codigo} - ${b.clasificacion_display || b.clasificacion}`,
        objetivo: b.descripcion_automatica || b.descripcion_complementaria || `Subsanar brecha ${b.codigo}`,
      }))
      consultarSugeridos({ brecha_ids: brechaId })
    }
  }

  const handleSelectCurso = (cursoId: string) => {
    setSelectedCursoId(cursoId)
    const c = cursosCatalogo.find((x) => x.id === cursoId)
    if (c) {
      setFormProgramar((prev) => ({
        ...prev,
        tema: `Capacitación y Certificación: ${c.nombre}`,
        objetivo: `Cerrar brecha y renovar vigencia del requisito obligatorio ${c.nombre}`,
      }))
      consultarSugeridos({ curso_id: cursoId })
    }
  }

  const toggleSugerido = (tid: string) => {
    const next = new Set(selectedSugeridosIds)
    if (next.has(tid)) {
      next.delete(tid)
    } else {
      next.add(tid)
    }
    setSelectedSugeridosIds(next)
  }

  const handleCrear = async () => {
    if (!formProgramar.tema.trim()) {
      alert('El tema es obligatorio')
      return
    }
    if (!formProgramar.fecha) {
      alert('La fecha es obligatoria')
      return
    }

    try {
      const payload: any = {
        tema: formProgramar.tema.trim(),
        objetivo: formProgramar.objetivo.trim(),
        proveedor: formProgramar.proveedor.trim() || undefined,
        fecha: formProgramar.fecha,
        horas_duracion: formProgramar.horas_duracion || undefined,
        tiene_certificado: formProgramar.tiene_certificado,
        estado: 'programada',
      }

      if (tipoNecesidad === 'curso' && selectedCursoId) {
        payload.curso = selectedCursoId
      }
      if (tipoNecesidad === 'brecha' && selectedBrechaId) {
        payload.brechas = [selectedBrechaId]
      }

      const nuevaCap = await crearMut.mutateAsync(payload)

      // Inscribir a los participantes sugeridos seleccionados
      const idsAInscribir = Array.from(selectedSugeridosIds)
      if (idsAInscribir.length > 0 && nuevaCap.id) {
        await inscribirMut.mutateAsync({
          capacitacionId: nuevaCap.id,
          trabajadoresIds: idsAInscribir,
        })
      }

      setModalProgramarOpen(false)
      setSearchParams({})
      setFormProgramar({
        tema: '',
        objetivo: '',
        proveedor: '',
        fecha: '',
        horas_duracion: 4,
        tiene_certificado: true,
      })
      setSelectedCursoId('')
      setSelectedBrechaId('')
      setSugeridos([])
      setSelectedSugeridosIds(new Set())
      refetch()
    } catch (e: any) {
      alert(e?.response?.data?.error || e?.message || 'Error al programar capacitación')
    }
  }

  // Abrir modal de detalles y asistencia
  const abrirDetalleCapacitacion = async (cap: Capacitacion) => {
    try {
      const capFull = await capacitacionService.obtener(cap.id)
      setCapacitacionSeleccionada(capFull)

      // Inicializar el estado local de asistencia para cada participante
      const map: Record<string, any> = {}
      ;(capFull.participantes || []).forEach((p: ParticipanteCapacitacion) => {
        map[p.trabajador] = {
          asistio: p.asistio ?? false,
          certificado_url: p.certificado_url || '',
          nota_evaluacion: p.nota_evaluacion !== null && p.nota_evaluacion !== undefined ? String(p.nota_evaluacion) : '',
          nivel_alcanzado: p.nivel_alcanzado ?? 3,
          observaciones: p.observaciones || '',
        }
      })
      setAsistenciaState(map)
      setModalDetalleOpen(true)
    } catch (e) {
      console.error(e)
    }
  }

  const handleInscribirTrabajadorExtra = async () => {
    if (!trabajadorAInscribirId || !capacitacionSeleccionada) return
    try {
      const res = await inscribirMut.mutateAsync({
        capacitacionId: capacitacionSeleccionada.id,
        trabajadoresIds: [trabajadorAInscribirId],
      })
      setCapacitacionSeleccionada(res)
      setTrabajadorAInscribirId('')
      // Actualizar estado de asistencia local
      setAsistenciaState((prev) => ({
        ...prev,
        [trabajadorAInscribirId]: {
          asistio: false,
          certificado_url: '',
          nota_evaluacion: '',
          nivel_alcanzado: 3,
          observaciones: '',
        },
      }))
    } catch (e: any) {
      alert(e?.response?.data?.error || e?.message || 'Error al inscribir trabajador')
    }
  }

  const handleGuardarAsistencia = async () => {
    if (!capacitacionSeleccionada) return
    setGuardandoAsistencia(true)
    try {
      const payload = Object.entries(asistenciaState).map(([trabajadorId, st]) => ({
        trabajador_id: trabajadorId,
        asistio: st.asistio,
        certificado_url: st.certificado_url || undefined,
        nota_evaluacion: st.nota_evaluacion ? parseFloat(st.nota_evaluacion) : undefined,
        nivel_alcanzado: capacitacionSeleccionada.competencia ? st.nivel_alcanzado : undefined,
        observaciones: st.observaciones || undefined,
      }))

      const res = await registrarAsistenciaMut.mutateAsync({
        capacitacionId: capacitacionSeleccionada.id,
        participantes: payload,
      })
      setCapacitacionSeleccionada(res)
      alert('Asistencia registrada correctamente.')
      refetch()
    } catch (e: any) {
      alert(e?.response?.data?.error || e?.message || 'Error guardando asistencia')
    } finally {
      setGuardandoAsistencia(false)
    }
  }

  const handleFinalizarCapacitacion = async () => {
    if (!capacitacionSeleccionada) return
    if (!confirm('¿Desea marcar esta capacitación como REALIZADA?\n\nEsto creará/actualizará los registros de formación de los asistentes, reevaluará las competencias correspondientes, subsanará automáticamente las brechas en HBSEO y recalculará la habilitación en MICHC.')) {
      return
    }

    setFinalizando(true)
    try {
      // Guardar asistencia pendiente primero si la hubiera
      const payload = Object.entries(asistenciaState).map(([trabajadorId, st]) => ({
        trabajador_id: trabajadorId,
        asistio: st.asistio,
        certificado_url: st.certificado_url || undefined,
        nota_evaluacion: st.nota_evaluacion ? parseFloat(st.nota_evaluacion) : undefined,
        nivel_alcanzado: capacitacionSeleccionada.competencia ? st.nivel_alcanzado : undefined,
        observaciones: st.observaciones || undefined,
      }))
      await registrarAsistenciaMut.mutateAsync({
        capacitacionId: capacitacionSeleccionada.id,
        participantes: payload,
      })

      // Finalizar la capacitación
      const res = await finalizarMut.mutateAsync(capacitacionSeleccionada.id)
      setCapacitacionSeleccionada(res)
      alert('¡Capacitación finalizada con éxito!\nLas brechas ligadas han sido actualizadas y el índice MICHC ha sido recalculado.')
      setModalDetalleOpen(false)
      refetch()
    } catch (e: any) {
      alert(e?.response?.data?.error || e?.message || 'Error finalizando capacitación')
    } finally {
      setFinalizando(false)
    }
  }

  if (isLoading) return <LoadingSpinner text="Cargando capacitaciones..." />
  if (error || !data) return <ErrorDisplay message={(error as Error)?.message ?? 'Error'} onRetry={refetch} />

  const { capacitaciones, resumen } = data
  const filtradas = filtro === 'todos' ? capacitaciones : capacitaciones.filter((c) => c.estado === filtro)

  return (
    <div className="animate-fade-in space-y-6 pb-12">
      <PageHeader
        title="Capacitaciones & Cierre de Brechas"
        subtitle="Entrenamiento orientado a competencias y cierre automático de brechas de habilitación"
        actions={
          <Button
            variant="primary"
            className="text-xs"
            icon={<Plus className="w-3.5 h-3.5" />}
            onClick={() => {
              setSearchParams({})
              setModalProgramarOpen(true)
            }}
          >
            Programar Capacitación
          </Button>
        }
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          { label: 'Total', count: resumen.total, icon: BookOpen, color: 'text-primary-500' },
          { label: 'Programadas', count: resumen.programadas, icon: Calendar, color: 'text-blue-600' },
          { label: 'Realizadas', count: resumen.realizadas, icon: CheckCircle2, color: 'text-emerald-700' },
          { label: 'Canceladas', count: resumen.canceladas, icon: Users, color: 'text-rose-700' },
        ].map((k) => (
          <Card key={k.label}>
            <div className="flex items-center gap-3">
              <k.icon className={`w-5 h-5 ${k.color}`} />
              <div>
                <div className={`text-xl font-black ${k.color}`}>{k.count}</div>
                <div className="text-[10px] text-slate-500 uppercase font-semibold">{k.label}</div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Filtros de estado */}
      <div className="flex gap-2">
        {['todos', 'programada', 'realizada', 'cancelada'].map((f) => (
          <button
            key={f}
            onClick={() => setFiltro(f)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              filtro === f
                ? 'bg-brand-50 text-brand-800 border border-brand-200'
                : 'bg-surface text-slate-500 border border-surface-2'
            }`}
          >
            {f === 'todos' ? 'Todas' : f.charAt(0).toUpperCase() + f.slice(1) + 's'}
          </button>
        ))}
      </div>

      {/* Listado de Capacitaciones */}
      <div className="space-y-3">
        {filtradas.length === 0 ? (
          <EmptyState
            icon={<BookOpen className="w-7 h-7" />}
            title="Sin capacitaciones"
            description={
              filtro === 'todos'
                ? 'No hay capacitaciones registradas en el sistema.'
                : `No hay capacitaciones con estado "${filtro}".`
            }
            action={
              <Button
                variant="primary"
                icon={<Plus className="w-3.5 h-3.5" />}
                onClick={() => setModalProgramarOpen(true)}
              >
                Programar Capacitación
              </Button>
            }
          />
        ) : (
          filtradas.map((cap) => (
            <Card key={cap.id} className="p-4 hover:shadow-sm transition-all border border-slate-200">
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                <div className="flex items-start gap-3.5 flex-1">
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                      cap.estado === 'realizada'
                        ? 'bg-emerald-100 text-emerald-600'
                        : cap.estado === 'programada'
                        ? 'bg-blue-100 text-blue-600'
                        : 'bg-rose-100 text-rose-600'
                    }`}
                  >
                    {cap.estado === 'realizada' ? (
                      <CheckCircle2 className="w-5 h-5" />
                    ) : (
                      <BookOpen className="w-5 h-5" />
                    )}
                  </div>

                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-bold text-slate-900">{cap.tema}</span>
                      <Badge
                        variant={
                          cap.estado === 'realizada'
                            ? 'green'
                            : cap.estado === 'programada'
                            ? 'blue'
                            : 'red'
                        }
                      >
                        {cap.estado}
                      </Badge>

                      {cap.curso_nombre && (
                        <span className="text-[10px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded-full font-medium border border-slate-200">
                          Curso: {cap.curso_nombre}
                        </span>
                      )}

                      {cap.competencia_nombre && (
                        <span className="text-[10px] bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full font-medium border border-purple-200">
                          Competencia: {cap.competencia_nombre}
                        </span>
                      )}
                    </div>

                    {cap.objetivo && (
                      <p className="text-xs text-slate-600 italic">
                        &ldquo;{cap.objetivo}&rdquo;
                      </p>
                    )}

                    {/* Brechas ligadas */}
                    {cap.brechas_detalle && cap.brechas_detalle.length > 0 && (
                      <div className="flex items-center gap-2 flex-wrap pt-1">
                        <span className="text-[11px] text-slate-500 font-semibold flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3 text-amber-500" /> Cierra brecha:
                        </span>
                        {cap.brechas_detalle.map((b) => (
                          <span
                            key={b.id}
                            className={`text-[10px] px-2 py-0.5 rounded-md font-semibold border ${
                              b.estado === 'subsanada'
                                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                : 'bg-amber-50 text-amber-700 border-amber-200'
                            }`}
                            title={b.descripcion}
                          >
                            {b.codigo} ({b.clasificacion_display || b.clasificacion}) — {b.estado}
                          </span>
                        ))}
                      </div>
                    )}

                    <div className="text-xs text-slate-500 flex items-center gap-4 flex-wrap pt-1">
                      {cap.proveedor && <span>Proveedor: <strong>{cap.proveedor}</strong></span>}
                      <span>
                        Fecha: <strong>{new Date(cap.fecha).toLocaleDateString('es-CO')}</strong>
                      </span>
                      {cap.horas_duracion && <span>Duración: <strong>{cap.horas_duracion}h</strong></span>}
                      <span className="flex items-center gap-1 font-semibold text-slate-700">
                        <Users className="w-3.5 h-3.5 text-primary-500" />
                        Participantes: {cap.total_asistieron || 0} / {cap.total_participantes || cap.num_asistentes || 0} asistieron
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
                  <Button
                    variant="ghost"
                    className="text-xs py-1.5 px-3 border border-slate-200 bg-white hover:bg-slate-50"
                    icon={<UserCheck className="w-3.5 h-3.5" />}
                    onClick={() => abrirDetalleCapacitacion(cap)}
                  >
                    Asistencia & Participantes
                  </Button>

                  {cap.estado === 'programada' && (
                    <Button
                      variant="primary"
                      className="text-xs py-1.5 px-3"
                      icon={<Check className="w-3.5 h-3.5" />}
                      onClick={() => abrirDetalleCapacitacion(cap)}
                    >
                      Finalizar
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          ))
        )}
      </div>

      {/* MODAL 1: PROGRAMAR CAPACITACIÓN CON BÚSQUEDA DE BRECHAS Y PARTICIPANTES SUGERIDOS */}
      <Modal
        open={modalProgramarOpen}
        onClose={() => setModalProgramarOpen(false)}
        title="Programar Capacitación & Cierre de Brechas"
        maxWidth="680px"
        footer={
          <>
            <Button variant="ghost" onClick={() => setModalProgramarOpen(false)}>
              Cancelar
            </Button>
            <Button
              variant="primary"
              onClick={handleCrear}
              disabled={crearMut.isPending || inscribirMut.isPending}
            >
              Programar Capacitación
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {/* Selector: ¿Qué necesidad cubre? */}
          <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
            <label className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-primary-500" />
              ¿Qué brecha o necesidad formativa cubre esta capacitación?
            </label>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => handleTipoNecesidadChange('brecha')}
                className={`flex-1 py-1.5 px-2.5 rounded-lg text-xs font-semibold border transition ${
                  tipoNecesidad === 'brecha'
                    ? 'bg-amber-500 text-white border-amber-600 shadow-sm'
                    : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'
                }`}
              >
                Brecha abierta HBSEO
              </button>
              <button
                type="button"
                onClick={() => handleTipoNecesidadChange('curso')}
                className={`flex-1 py-1.5 px-2.5 rounded-lg text-xs font-semibold border transition ${
                  tipoNecesidad === 'curso'
                    ? 'bg-brand-600 text-white border-brand-700 shadow-sm'
                    : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'
                }`}
              >
                Curso del Catálogo
              </button>
              <button
                type="button"
                onClick={() => handleTipoNecesidadChange('libre')}
                className={`flex-1 py-1.5 px-2.5 rounded-lg text-xs font-semibold border transition ${
                  tipoNecesidad === 'libre'
                    ? 'bg-slate-800 text-white border-slate-900 shadow-sm'
                    : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'
                }`}
              >
                Capacitación Libre
              </button>
            </div>

            {/* Selector de Brecha */}
            {tipoNecesidad === 'brecha' && (
              <div className="space-y-1.5">
                <label className="text-[11px] font-semibold text-slate-600">
                  Seleccione la brecha abierta a resolver:
                </label>
                <select
                  value={selectedBrechaId}
                  onChange={(e) => handleSelectBrecha(e.target.value)}
                  className="w-full text-xs rounded-xl border border-slate-200 p-2.5 bg-white text-slate-800 focus:ring-brand-500"
                >
                  <option value="">Seleccione una brecha detectada...</option>
                  {brechasAbiertas.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.codigo} — {b.trabajador_nombre || 'General'} ({b.clasificacion_display || b.clasificacion}) — {b.descripcion_automatica?.slice(0, 70)}...
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Selector de Curso */}
            {tipoNecesidad === 'curso' && (
              <div className="space-y-1.5">
                <label className="text-[11px] font-semibold text-slate-600">
                  Seleccione el curso de formación:
                </label>
                <select
                  value={selectedCursoId}
                  onChange={(e) => handleSelectCurso(e.target.value)}
                  className="w-full text-xs rounded-xl border border-slate-200 p-2.5 bg-white text-slate-800 focus:ring-brand-500"
                >
                  <option value="">Seleccione un curso del catálogo...</option>
                  {cursosCatalogo.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nombre} ({c.categoria_display || c.categoria}) — Vigencia: {c.vigencia_meses ? `${c.vigencia_meses}m` : 'Permanente'}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* Participantes sugeridos */}
          {(selectedCursoId || selectedBrechaId) && (
            <div className="p-3.5 bg-blue-50/70 border border-blue-200 rounded-xl space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-blue-900 flex items-center gap-1.5">
                  <Users className="w-4 h-4 text-blue-700" />
                  Participantes Sugeridos Automáticamente ({sugeridos.length})
                </span>
                <span className="text-[11px] text-blue-600">
                  {selectedSugeridosIds.size} seleccionados
                </span>
              </div>

              {loadingSugeridos ? (
                <div className="text-center py-2 text-xs text-blue-600">
                  Buscando trabajadores con la brecha o curso vencido...
                </div>
              ) : sugeridos.length === 0 ? (
                <p className="text-xs text-slate-500 italic">
                  No se detectaron trabajadores con este curso vencido o faltante en este momento.
                </p>
              ) : (
                <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                  {sugeridos.map((s) => (
                    <div
                      key={s.trabajador_id}
                      onClick={() => toggleSugerido(s.trabajador_id)}
                      className={`p-2 rounded-lg border text-xs flex items-center justify-between cursor-pointer transition ${
                        selectedSugeridosIds.has(s.trabajador_id)
                          ? 'bg-blue-100/90 border-blue-300 text-blue-900 font-semibold'
                          : 'bg-white border-slate-200 text-slate-600'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={selectedSugeridosIds.has(s.trabajador_id)}
                          onChange={() => {}}
                          className="rounded text-blue-600"
                        />
                        <div>
                          <span>{s.nombre} ({s.documento})</span>
                          <span className="text-[10px] text-slate-500 block">{s.cargo}</span>
                        </div>
                      </div>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-rose-100 text-rose-800 font-medium">
                        {s.motivo_principal}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Campos estándar */}
          <FormField label="Tema de la capacitación" required>
            <Input
              value={formProgramar.tema}
              onChange={(e) => setFormProgramar({ ...formProgramar, tema: e.target.value })}
              placeholder="Ej. Re-entrenamiento en Trabajo Seguro en Alturas"
            />
          </FormField>

          <FormField label="Objetivo de aprendizaje / Cierre de brecha" helperText="Describe qué conocimiento o estándar busca asegurar">
            <Textarea
              rows={2}
              value={formProgramar.objetivo}
              onChange={(e) => setFormProgramar({ ...formProgramar, objetivo: e.target.value })}
              placeholder="Ej. Asegurar las competencias operativas y renovar la certificación legal para habilitación en MICHC."
            />
          </FormField>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <FormField label="Fecha y Hora de Realización" required>
              <Input
                type="date"
                value={formProgramar.fecha}
                onChange={(e) => setFormProgramar({ ...formProgramar, fecha: e.target.value })}
              />
            </FormField>

            <FormField label="Duración estimada (Horas)">
              <Input
                type="number"
                min="1"
                value={formProgramar.horas_duracion}
                onChange={(e) =>
                  setFormProgramar({ ...formProgramar, horas_duracion: parseInt(e.target.value) || 0 })
                }
              />
            </FormField>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <FormField label="Proveedor / Facilitador">
              <Input
                value={formProgramar.proveedor}
                onChange={(e) => setFormProgramar({ ...formProgramar, proveedor: e.target.value })}
                placeholder="Ej. ARL Sura / Centro de Entrenamiento SAS"
              />
            </FormField>

            <div className="flex items-center gap-2 pt-6">
              <input
                type="checkbox"
                id="tiene_certificado"
                checked={formProgramar.tiene_certificado}
                onChange={(e) =>
                  setFormProgramar({ ...formProgramar, tiene_certificado: e.target.checked })
                }
                className="rounded text-brand-600 focus:ring-brand-500 w-4 h-4"
              />
              <label htmlFor="tiene_certificado" className="text-xs font-semibold text-slate-700 cursor-pointer">
                Genera o exige certificado / constancia
              </label>
            </div>
          </div>
        </div>
      </Modal>

      {/* MODAL 2: DETALLE, LISTA DE ASISTENCIA Y CIERRE DE BRECHAS */}
      {capacitacionSeleccionada && (
        <Modal
          open={modalDetalleOpen}
          onClose={() => setModalDetalleOpen(false)}
          title={`Capacitación: ${capacitacionSeleccionada.tema}`}
          maxWidth="840px"
          footer={
            <div className="flex items-center justify-between w-full">
              <div className="text-[11px] text-slate-500">
                Estado: <strong>{capacitacionSeleccionada.estado}</strong>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="ghost" onClick={() => setModalDetalleOpen(false)}>
                  Cerrar
                </Button>
                <Button
                  variant="secondary"
                  onClick={handleGuardarAsistencia}
                  disabled={guardandoAsistencia}
                  icon={<UserCheck className="w-4 h-4" />}
                >
                  {guardandoAsistencia ? 'Guardando...' : 'Guardar Asistencia'}
                </Button>
                {capacitacionSeleccionada.estado === 'programada' && (
                  <Button
                    variant="primary"
                    onClick={handleFinalizarCapacitacion}
                    disabled={finalizando || guardandoAsistencia}
                    icon={<CheckCircle2 className="w-4 h-4" />}
                  >
                    {finalizando ? 'Finalizando...' : 'Finalizar y Cerrar Brechas'}
                  </Button>
                )}
              </div>
            </div>
          }
        >
          <div className="space-y-4">
            {/* Resumen de la Capacitación */}
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5 text-xs text-slate-700">
              {capacitacionSeleccionada.objetivo && (
                <p><strong>Objetivo:</strong> {capacitacionSeleccionada.objetivo}</p>
              )}
              <div className="flex items-center gap-4 flex-wrap text-slate-500">
                {capacitacionSeleccionada.curso_nombre && (
                  <span>Curso vinculado: <strong>{capacitacionSeleccionada.curso_nombre}</strong></span>
                )}
                {capacitacionSeleccionada.competencia_nombre && (
                  <span>Competencia vinculada: <strong>{capacitacionSeleccionada.competencia_nombre}</strong></span>
                )}
                <span>Fecha: <strong>{new Date(capacitacionSeleccionada.fecha).toLocaleDateString('es-CO')}</strong></span>
                {capacitacionSeleccionada.proveedor && (
                  <span>Proveedor: <strong>{capacitacionSeleccionada.proveedor}</strong></span>
                )}
              </div>

              {capacitacionSeleccionada.brechas_detalle && capacitacionSeleccionada.brechas_detalle.length > 0 && (
                <div className="pt-1 flex items-center gap-2 flex-wrap">
                  <span className="font-semibold text-amber-700">Brechas HBSEO enlazadas:</span>
                  {capacitacionSeleccionada.brechas_detalle.map((b) => (
                    <span
                      key={b.id}
                      className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-800"
                    >
                      {b.codigo} ({b.estado})
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Inscribir Trabajador Extra */}
            <div className="flex items-center gap-2 p-3 bg-white border border-slate-200 rounded-xl">
              <UserPlus className="w-4 h-4 text-slate-400" />
              <select
                value={trabajadorAInscribirId}
                onChange={(e) => setTrabajadorAInscribirId(e.target.value)}
                className="flex-1 text-xs rounded-lg border-slate-200 py-1.5 px-2.5 bg-white text-slate-800"
              >
                <option value="">Inscribir a otro trabajador en esta capacitación...</option>
                {trabajadores
                  .filter(
                    (t) =>
                      !(capacitacionSeleccionada.participantes || []).some(
                        (p) => p.trabajador === t.id
                      )
                  )
                  .map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.nombre} — {t.cargo || 'Sin cargo'} ({t.documento})
                    </option>
                  ))}
              </select>
              <Button
                variant="secondary"
                className="text-xs py-1 px-3"
                onClick={handleInscribirTrabajadorExtra}
                disabled={!trabajadorAInscribirId || inscribirMut.isPending}
              >
                Inscribir
              </Button>
            </div>

            {/* Tabla de Participantes y Asistencia */}
            <div className="border border-slate-200 rounded-xl overflow-hidden">
              <div className="bg-slate-100/75 px-4 py-2 border-b border-slate-200 flex items-center justify-between text-xs font-bold text-slate-700">
                <span>Participantes Inscritos ({capacitacionSeleccionada.participantes?.length || 0})</span>
                <span className="text-[11px] font-normal text-slate-500">
                  Marque asistencia y adjunte certificado/calificación por persona
                </span>
              </div>

              {!capacitacionSeleccionada.participantes || capacitacionSeleccionada.participantes.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-400">
                  No hay trabajadores inscritos en esta capacitación. Utilice el selector superior para inscribirlos.
                </div>
              ) : (
                <div className="divide-y divide-slate-100 max-h-96 overflow-y-auto">
                  {capacitacionSeleccionada.participantes.map((part) => {
                    const st = asistenciaState[part.trabajador] || {
                      asistio: false,
                      certificado_url: '',
                      nota_evaluacion: '',
                      nivel_alcanzado: 3,
                      observaciones: '',
                    }

                    return (
                      <div
                        key={part.id}
                        className={`p-3.5 space-y-2 transition ${
                          st.asistio ? 'bg-emerald-50/40' : 'bg-white'
                        }`}
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <div>
                            <span className="text-xs font-bold text-slate-900">
                              {part.trabajador_nombre}
                            </span>
                            <span className="text-[11px] text-slate-500 block">
                              {part.trabajador_cargo || 'Sin cargo'} · Doc: {part.trabajador_documento}
                            </span>
                          </div>

                          <label className="flex items-center gap-2 cursor-pointer self-start sm:self-center bg-white px-3 py-1 rounded-lg border border-slate-200 shadow-2xs">
                            <input
                              type="checkbox"
                              checked={st.asistio}
                              onChange={(e) =>
                                setAsistenciaState({
                                  ...asistenciaState,
                                  [part.trabajador]: { ...st, asistio: e.target.checked },
                                })
                              }
                              className="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4"
                            />
                            <span
                              className={`text-xs font-bold ${
                                st.asistio ? 'text-emerald-700' : 'text-slate-500'
                              }`}
                            >
                              {st.asistio ? 'Asistió' : 'No asistió'}
                            </span>
                          </label>
                        </div>

                        {/* Campos de evaluación y soporte por participante */}
                        {st.asistio && (
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1 border-t border-slate-100 text-xs">
                            <div>
                              <label className="text-[10px] text-slate-500 font-semibold block mb-0.5">
                                URL Certificado / Soporte:
                              </label>
                              <input
                                type="url"
                                placeholder="https://..."
                                value={st.certificado_url}
                                onChange={(e) =>
                                  setAsistenciaState({
                                    ...asistenciaState,
                                    [part.trabajador]: { ...st, certificado_url: e.target.value },
                                  })
                                }
                                className="w-full text-xs rounded border border-slate-200 p-1.5 bg-white"
                              />
                            </div>

                            {capacitacionSeleccionada.competencia && (
                              <div>
                                <label className="text-[10px] text-slate-500 font-semibold block mb-0.5">
                                  Nivel alcanzado (1..5):
                                </label>
                                <select
                                  value={st.nivel_alcanzado}
                                  onChange={(e) =>
                                    setAsistenciaState({
                                      ...asistenciaState,
                                      [part.trabajador]: {
                                        ...st,
                                        nivel_alcanzado: parseInt(e.target.value) || 1,
                                      },
                                    })
                                  }
                                  className="w-full text-xs rounded border border-slate-200 p-1.5 bg-white font-semibold"
                                >
                                  <option value={1}>1 · Básico</option>
                                  <option value={2}>2 · En desarrollo</option>
                                  <option value={3}>3 · Autónomo</option>
                                  <option value={4}>4 · Dominio avanzado</option>
                                  <option value={5}>5 · Referente</option>
                                </select>
                              </div>
                            )}

                            <div>
                              <label className="text-[10px] text-slate-500 font-semibold block mb-0.5">
                                Nota / Observación:
                              </label>
                              <input
                                type="text"
                                placeholder="Ej. Aprobó examen con 95%"
                                value={st.observaciones}
                                onChange={(e) =>
                                  setAsistenciaState({
                                    ...asistenciaState,
                                    [part.trabajador]: { ...st, observaciones: e.target.value },
                                  })
                                }
                                className="w-full text-xs rounded border border-slate-200 p-1.5 bg-white"
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

            {/* Alerta de cierre automático */}
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-2 text-xs text-amber-900">
              <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <strong>Impacto automático al finalizar:</strong> Por cada asistente confirmado se generará o actualizará su registro de formación vigente. Las brechas vinculadas se cerrarán con el estado <em>Subsanada</em> y se registrará el evento correspondiente en la línea de tiempo de HBSEO y en la habilitación operativa MICHC.
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
