import { useState } from 'react'
import { Card, PageHeader, Badge, Button, Table, TableHeader, TableBody, TableRow, TableHead, TableCell, EmptyState } from '@/components/ui'
import { LoadingSpinner, ErrorDisplay, Select, FormField } from '@/components/ui/forms'
import { useEstandaresConRespuestas, useActualizarRespuesta } from '@/hooks/useApi'
import { estandarService, RespuestaHistoricaItem, ApelacionItem } from '@/services/estandar.service'
import { Check, X, AlertTriangle, Pencil, Minus, History, Loader2, BookOpen, MessageSquare, ShieldAlert } from 'lucide-react'
import type { EstadoCumplimiento } from '@/types'

const ESTADO_OPTIONS = [
  { value: 'cumple', label: 'Cumple' },
  { value: 'parcial', label: 'Parcial' },
  { value: 'no_cumple', label: 'No cumple' },
  { value: 'no_aplica', label: 'No aplica' },
]

export default function EstandaresView() {
  const { data, isLoading, error, refetch } = useEstandaresConRespuestas()
  const actualizarMut = useActualizarRespuesta()
  const [editando, setEditando] = useState<string | null>(null)
  const [form, setForm] = useState({ estado: '' as string, observacion: '' })

  // Estado para Modal de Respuestas Históricas (RF-USR-03)
  const [modalHistoricoOpen, setModalHistoricoOpen] = useState(false)
  const [respuestasHistoricas, setRespuestasHistoricas] = useState<RespuestaHistoricaItem[]>([])
  const [loadingHistorico, setLoadingHistorico] = useState(false)
  const [errorHistorico, setErrorHistorico] = useState('')

  // Estado para RF-SST-03 / SST-04: Apelaciones
  const [modalApelarOpen, setModalApelarOpen] = useState(false)
  const [targetRespuesta, setTargetRespuesta] = useState<{ id: string; codigo: string; nombre: string; observacion: string } | null>(null)
  const [motivoApelacion, setMotivoApelacion] = useState('')
  const [isSubmittingApelacion, setIsSubmittingApelacion] = useState(false)
  const [errorApelacion, setErrorApelacion] = useState('')

  const [modalListaApelacionesOpen, setModalListaApelacionesOpen] = useState(false)
  const [listaApelaciones, setListaApelaciones] = useState<ApelacionItem[]>([])
  const [loadingListaApelaciones, setLoadingListaApelaciones] = useState(false)

  const abrirApelarModal = (respuestaId: string, codigo: string, nombre: string, observacion: string) => {
    setTargetRespuesta({ id: respuestaId, codigo, nombre, observacion })
    setMotivoApelacion('')
    setErrorApelacion('')
    setModalApelarOpen(true)
  }

  const handleEnviarApelacion = async () => {
    if (!targetRespuesta) return
    if (!motivoApelacion.trim()) {
      setErrorApelacion('El motivo de la apelación es obligatorio.')
      return
    }

    setIsSubmittingApelacion(true)
    setErrorApelacion('')
    try {
      await estandarService.crearApelacion(targetRespuesta.id, motivoApelacion)
      setModalApelarOpen(false)
      setTargetRespuesta(null)
      setMotivoApelacion('')
      refetch()
    } catch (err: any) {
      setErrorApelacion(err?.friendlyMessage || err?.message || 'Error al presentar la apelación.')
    } finally {
      setIsSubmittingApelacion(false)
    }
  }

  const abrirListaApelaciones = async () => {
    setModalListaApelacionesOpen(true)
    setLoadingListaApelaciones(true)
    try {
      const res = await estandarService.listarApelaciones()
      const list = Array.isArray(res) ? res : res.results || []
      setListaApelaciones(list)
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingListaApelaciones(false)
    }
  }

  const abrirRespuestasHistoricas = async () => {
    setModalHistoricoOpen(true)
    setLoadingHistorico(true)
    setErrorHistorico('')
    try {
      const res = await estandarService.getRespuestasHistoricas()
      setRespuestasHistoricas(res.respuestas)
    } catch (err: any) {
      setErrorHistorico(err?.friendlyMessage || err?.message || 'Error al cargar respuestas históricas.')
    } finally {
      setLoadingHistorico(false)
    }
  }


  if (isLoading) return <LoadingSpinner text="Cargando estándares..." />
  if (error || !data) return <ErrorDisplay message={(error as Error)?.message ?? 'Error'} onRetry={refetch} />

  const { estandares, capitulo } = data

  const ciclos = ['Planear', 'Hacer', 'Verificar', 'Actuar']
  const agrupados = ciclos.map((c) => ({
    ciclo: c,
    items: estandares.filter((e) => e.ciclo_phva === c),
  })).filter((g) => g.items.length > 0)

  const handleGuardar = async (estandarId: string) => {
    await actualizarMut.mutateAsync({
      estandarId,
      data: { estado: form.estado as EstadoCumplimiento, observacion: form.observacion },
    })
    setEditando(null)
  }

  const abrirEditor = (estandarId: string, estado: string, obs: string) => {
    setEditando(estandarId)
    setForm({ estado: estado === 'sin_respuesta' ? 'no_cumple' : estado, observacion: obs })
  }

  const getEstadoBadge = (estado: string) => {
    switch (estado) {
      case 'cumple':
        return <Badge variant="green" icon={Check}>Cumple</Badge>
      case 'parcial':
        return <Badge variant="orange" icon={AlertTriangle}>Parcial</Badge>
      case 'no_cumple':
        return <Badge variant="red" icon={X}>No cumple</Badge>
      case 'no_aplica':
        return <Badge variant="gray" icon={Minus}>No aplica</Badge>
      case 'sin_respuesta':
      default:
        return <Badge variant="purple" icon={Minus}>Sin respuesta</Badge>
    }
  }

  return (
    <div className="animate-fade-in space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <PageHeader title={`Estándares Mínimos — Capítulo ${capitulo}`} subtitle="Res. 0312/2019 · Diligenciamiento interactivo de estándares" />
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Button
            onClick={abrirListaApelaciones}
            variant="ghost"
            className="text-xs py-2 px-3 flex items-center gap-1.5 whitespace-nowrap"
          >
            <MessageSquare className="w-4 h-4 text-amber-600" />
            Ver Apelaciones
          </Button>
          <Button
            onClick={abrirRespuestasHistoricas}
            variant="secondary"
            className="text-xs py-2 px-3 flex items-center gap-1.5 whitespace-nowrap"
          >
            <History className="w-4 h-4 text-brand-500" />
            Respuestas Históricas
          </Button>
        </div>
      </div>



      {agrupados.length === 0 ? (
        <EmptyState title="Sin estándares" description="No hay estándares configurados para mostrar." />
      ) : (
        agrupados.map(({ ciclo, items }) => (
          <Card key={ciclo} title={ciclo.toUpperCase()} subtitle={`${items.length} estándares · ${items.filter((e) => e.estado === 'cumple').length} cumplidos`}>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-20">Código</TableHead>
                  <TableHead>Estándar</TableHead>
                  <TableHead className="text-center w-16">Pts</TableHead>
                  <TableHead className="text-center w-28">Estado</TableHead>
                  <TableHead className="text-center w-16">%</TableHead>
                  <TableHead className="text-center w-20">Evidencias</TableHead>
                  <TableHead className="text-right w-24">Acción</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((est) => {
                  const isEditing = editando === est.estandar_id
                  return (
                    <TableRow key={est.estandar_id}>
                      <TableCell className="font-bold text-slate-900 font-mono">{est.codigo}</TableCell>
                      <TableCell className="max-w-xs sm:max-w-md">
                        <div className="font-semibold text-slate-800" title={est.nombre}>{est.nombre}</div>
                        {est.observacion && <div className="text-[11px] text-slate-500 mt-0.5">{est.observacion}</div>}
                      </TableCell>
                      <TableCell className="text-center font-bold text-slate-600">{est.puntaje_maximo}</TableCell>
                      <TableCell className="text-center">
                        {isEditing ? (
                          <Select value={form.estado} onChange={(e) => setForm({ ...form, estado: e.target.value })} options={ESTADO_OPTIONS} className="text-xs py-1" />
                        ) : (
                          getEstadoBadge(est.estado)
                        )}
                      </TableCell>
                      <TableCell className="text-center font-bold">
                        <span className={est.porcentaje! >= 80 ? 'text-emerald-700' : est.porcentaje! >= 50 ? 'text-amber-700' : 'text-rose-600'}>
                          {est.porcentaje ?? 0}%
                        </span>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant="blue">{est.evidencias}</Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        {isEditing ? (
                          <div className="flex gap-1.5 justify-end">
                            <Button variant="primary" icon={Check} className="text-xs py-1 px-2.5" onClick={() => handleGuardar(est.estandar_id)} disabled={actualizarMut.isPending}>
                              Guardar
                            </Button>
                            <Button variant="ghost" icon={X} className="text-xs py-1 px-2" onClick={() => setEditando(null)}>
                              Cancelar
                            </Button>
                          </div>
                        ) : (
                          <div className="flex gap-1.5 justify-end items-center">
                            {est.respuesta_id && (
                              <Button
                                variant="ghost"
                                icon={MessageSquare}
                                className="text-xs py-1 px-2 text-amber-700 hover:bg-amber-50"
                                onClick={() => abrirApelarModal(est.respuesta_id!, est.codigo, est.nombre, est.observacion || '')}
                                title="Apelar observación"
                              >
                                Apelar
                              </Button>
                            )}
                            <Button variant="ghost" icon={Pencil} className="text-xs py-1 px-3" onClick={() => abrirEditor(est.estandar_id, est.estado, est.observacion)}>
                              Editar
                            </Button>
                          </div>
                        )}
                      </TableCell>

                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </Card>
        ))
      )}

      {/* Modal de Respuestas Históricas (RF-USR-03) */}
      {modalHistoricoOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-4xl w-full overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200 flex flex-col max-h-[85vh]">
            {/* Header Modal */}
            <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 text-white px-6 py-4 flex justify-between items-center">
              <div>
                <h3 className="font-black text-sm flex items-center gap-2">
                  <History className="w-4 h-4 text-brand-400" />
                  Historial Completo de Respuestas (RF-USR-03)
                </h3>
                <p className="text-[10px] text-slate-300">
                  Consulta todas las respuestas registradas en la autoevaluación, incluyendo las diligenciadas bajo capítulos anteriores.
                </p>
              </div>
              <button
                onClick={() => setModalHistoricoOpen(false)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Contenido Modal */}
            <div className="p-6 space-y-4 overflow-y-auto flex-1 bg-slate-50/50">
              {loadingHistorico && (
                <div className="flex flex-col items-center justify-center py-12 space-y-3">
                  <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
                  <span className="text-xs text-slate-500 font-medium">Cargando respuestas históricas...</span>
                </div>
              )}

              {errorHistorico && (
                <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                  <span>{errorHistorico}</span>
                </div>
              )}

              {!loadingHistorico && !errorHistorico && respuestasHistoricas.length === 0 && (
                <EmptyState title="Sin respuestas registradas" description="Aún no hay respuestas registradas en esta autoevaluación." />
              )}

              {!loadingHistorico && !errorHistorico && respuestasHistoricas.length > 0 && (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-20">Código</TableHead>
                      <TableHead>Estándar</TableHead>
                      <TableHead className="text-center w-28">Capítulo</TableHead>
                      <TableHead className="text-center w-24">Estado</TableHead>
                      <TableHead className="text-center w-16">Puntaje</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {respuestasHistoricas.map((item) => (
                      <TableRow key={item.respuesta_id}>
                        <TableCell className="font-bold text-slate-900 font-mono">{item.codigo}</TableCell>
                        <TableCell>
                          <div className="font-semibold text-slate-800">{item.nombre}</div>
                          {item.observacion && <div className="text-[11px] text-slate-500 mt-0.5">{item.observacion}</div>}
                        </TableCell>
                        <TableCell className="text-center">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold ${
                            item.es_capitulo_vigente
                              ? 'bg-brand-50 text-brand-700 border border-brand-200'
                              : 'bg-amber-50 text-amber-700 border border-amber-200'
                          }`}>
                            Capítulo {item.capitulo_estandar}
                            {!item.es_capitulo_vigente && ' (Histórico)'}
                          </span>
                        </TableCell>
                        <TableCell className="text-center">
                          {getEstadoBadge(item.estado)}
                        </TableCell>
                        <TableCell className="text-center font-bold text-slate-700">
                          {item.puntaje} / {item.puntaje_maximo}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </div>

            {/* Footer Modal */}
            <div className="flex gap-3 justify-end px-6 py-4 border-t border-slate-200 bg-white">
              <Button
                onClick={() => setModalHistoricoOpen(false)}
                variant="primary"
                className="text-xs py-2 px-6"
              >
                Cerrar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal para Crear Apelación (RF-SST-03 / SST-04) */}
      {modalApelarOpen && targetRespuesta && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200 flex flex-col">
            {/* Header Modal */}
            <div className="bg-gradient-to-r from-amber-700 via-amber-600 to-amber-800 text-white px-6 py-4 flex justify-between items-center">
              <div className="flex items-center gap-2.5">
                <MessageSquare className="w-5 h-5 text-amber-200" />
                <div>
                  <h3 className="font-black text-sm">Presentar Apelación a Observación</h3>
                  <p className="text-[10px] text-amber-100">RF-SST-03 · Impugnación justificada de observación del auditor</p>
                </div>
              </div>
              <button onClick={() => setModalApelarOpen(false)} className="text-amber-200 hover:text-white transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Cuerpo Modal */}
            <div className="p-6 space-y-4 bg-slate-50/50">
              <div className="bg-white p-3.5 rounded-xl border border-slate-200 space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block font-mono">
                  Estándar {targetRespuesta.codigo}
                </span>
                <div className="text-xs font-bold text-slate-800">{targetRespuesta.nombre}</div>
                {targetRespuesta.observacion ? (
                  <p className="text-xs text-amber-800 bg-amber-50 p-2.5 rounded-lg border border-amber-200 mt-2 italic">
                    &ldquo;{targetRespuesta.observacion}&rdquo;
                  </p>
                ) : (
                  <p className="text-[11px] text-slate-400 italic mt-1">Sin observación previa registrada.</p>
                )}
              </div>

              <FormField label="Motivo y Argumentación de Apelación *">
                <textarea
                  value={motivoApelacion}
                  onChange={(e) => setMotivoApelacion(e.target.value)}
                  placeholder="Explica detalladamente la razón por la cual consideras que el estándar cumple o no aplica, indicando soportes y justificación normativa..."
                  className="w-full text-xs border border-slate-300 rounded-xl p-3 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-500 min-h-[100px]"
                />
              </FormField>

              {errorApelacion && (
                <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                  <span>{errorApelacion}</span>
                </div>
              )}
            </div>

            {/* Footer Modal */}
            <div className="flex gap-3 justify-end px-6 py-4 border-t border-slate-200 bg-white">
              <Button onClick={() => setModalApelarOpen(false)} variant="secondary" className="text-xs py-2 px-4" disabled={isSubmittingApelacion}>
                Cancelar
              </Button>
              <Button
                onClick={handleEnviarApelacion}
                variant="primary"
                className="text-xs py-2 px-5 bg-amber-600 hover:bg-amber-700 text-white border-none shadow-md shadow-amber-600/20 flex items-center gap-1.5"
                disabled={isSubmittingApelacion}
              >
                {isSubmittingApelacion && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                Presentar Apelación
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Lista de Apelaciones Presentadas */}
      {modalListaApelacionesOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-4xl w-full overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200 flex flex-col max-h-[85vh]">
            {/* Header Modal */}
            <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 text-white px-6 py-4 flex justify-between items-center">
              <div className="flex items-center gap-2.5">
                <MessageSquare className="w-5 h-5 text-amber-400" />
                <div>
                  <h3 className="font-black text-sm">Histórico de Apelaciones Presentadas (RF-SST-03)</h3>
                  <p className="text-[10px] text-slate-300">Trazabilidad de impugnaciones y resoluciones de auditoría</p>
                </div>
              </div>
              <button onClick={() => setModalListaApelacionesOpen(false)} className="text-slate-400 hover:text-white transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Contenido Modal */}
            <div className="p-6 space-y-4 overflow-y-auto flex-1 bg-slate-50/50">
              {loadingListaApelaciones && (
                <div className="flex flex-col items-center justify-center py-12 space-y-3">
                  <Loader2 className="w-8 h-8 text-amber-500 animate-spin" />
                  <span className="text-xs text-slate-500 font-medium">Cargando apelaciones...</span>
                </div>
              )}

              {!loadingListaApelaciones && listaApelaciones.length === 0 && (
                <EmptyState title="Sin apelaciones registradas" description="Aún no has presentado apelaciones sobre observaciones de estándares." />
              )}

              {!loadingListaApelaciones && listaApelaciones.length > 0 && (
                <div className="space-y-3">
                  {listaApelaciones.map((ap) => (
                    <div key={ap.id} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-2">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded text-[10px] font-mono font-bold">
                            {ap.codigo_estandar || 'Estándar'}
                          </span>
                          <span className="ml-2 text-xs font-bold text-slate-800">
                            {ap.nombre_estandar || 'Estándar'}
                          </span>
                        </div>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold capitalize ${
                          ap.estado === 'pendiente' ? 'bg-amber-100 text-amber-800 border border-amber-200' :
                          ap.estado === 'aceptada' ? 'bg-green-100 text-green-800 border border-green-200' :
                          ap.estado === 'rechazada' ? 'bg-red-100 text-red-800 border border-red-200' :
                          'bg-blue-100 text-blue-800 border border-blue-200'
                        }`}>
                          {ap.estado}
                        </span>
                      </div>

                      {ap.observacion_original && (
                        <div className="text-[11px] text-slate-500 bg-slate-50 p-2.5 rounded-lg border border-slate-100 italic">
                          <strong className="text-slate-600 not-italic">Observación Original:</strong> &ldquo;{ap.observacion_original}&rdquo;
                        </div>
                      )}

                      <div className="text-xs text-slate-700 bg-amber-50/50 p-3 rounded-lg border border-amber-100">
                        <strong className="text-amber-800">Motivo de Apelación:</strong> {ap.motivo}
                      </div>

                      {ap.respuesta_auditor && (
                        <div className="text-xs text-slate-700 bg-blue-50/50 p-3 rounded-lg border border-blue-100">
                          <strong className="text-blue-800">Respuesta de Resolución:</strong> {ap.respuesta_auditor}
                        </div>
                      )}

                      <div className="text-[10px] text-slate-400 pt-1 border-t border-slate-100 flex justify-between">
                        <span>Presentado por: {ap.solicitante_nombre || ap.solicitante_email}</span>
                        <span>{new Date(ap.created_at).toLocaleDateString()} {new Date(ap.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer Modal */}
            <div className="flex gap-3 justify-end px-6 py-4 border-t border-slate-200 bg-white">
              <Button onClick={() => setModalListaApelacionesOpen(false)} variant="primary" className="text-xs py-2 px-6">
                Cerrar
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


