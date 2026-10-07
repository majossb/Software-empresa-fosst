import { useState } from 'react'
import { Card, PageHeader, Badge, Button, EmptyState } from '@/components/ui'
import { LoadingSpinner, ErrorDisplay, Modal, FormField, Textarea } from '@/components/ui/forms'
import { useInformes, useGenerarInforme, useDashboardAud } from '@/hooks/useApi'
import { informeService } from '@/services/informe.service'
import { FileText, Plus, ClipboardCheck, Save, CheckCircle2, Lock, Download, AlertTriangle, Scale, Trash2 } from 'lucide-react'

export default function InformeAuditoriaView() {
  const { data, isLoading, error, refetch } = useInformes()
  const dashboard = useDashboardAud()
  const generarMut = useGenerarInforme()

  const [generando, setGenerando] = useState(false)
  const [guardando, setGuardando] = useState(false)
  const [finalizando, setFinalizando] = useState(false)
  const [descartando, setDescartando] = useState(false)
  const [confirmModalOpen, setConfirmModalOpen] = useState(false)
  const [discardModalOpen, setDiscardModalOpen] = useState(false)
  const [selectedInformeId, setSelectedInformeId] = useState<string | null>(null)

  const [narrativa, setNarrativa] = useState<Record<string, { conclusiones: string; recomendaciones: string; observaciones_finales: string }>>({})
  const [successBanner, setSuccessBanner] = useState<string | null>(null)
  const [formError, setFormError] = useState<string | null>(null)

  if (isLoading) return <LoadingSpinner text="Cargando informes de auditoría..." />
  if (error || !data) return <ErrorDisplay message={(error as Error)?.message ?? 'Error al cargar informes'} onRetry={refetch} />

  const informesAuditoria = data.filter(i => i.tipo === 'auditoria')

  const handleGenerar = async () => {
    const evalId = dashboard.data?.evaluacion_id
    if (!evalId) return
    setGenerando(true)
    setFormError(null)
    try {
      await generarMut.mutateAsync({ evaluacion_id: evalId, tipo: 'auditoria' })
      refetch()
    } catch (err: any) {
      setFormError(err?.friendlyMessage || err?.message || 'Error al generar informe')
    } finally {
      setGenerando(false)
    }
  }

  const getNarrativa = (infId: string, contentNarrativa?: any) => {
    if (narrativa[infId]) return narrativa[infId]
    return {
      conclusiones: contentNarrativa?.conclusiones || '',
      recomendaciones: contentNarrativa?.recomendaciones || (typeof contentNarrativa?.recomendaciones === 'string' ? contentNarrativa.recomendaciones : ''),
      observaciones_finales: contentNarrativa?.observaciones_finales || '',
    }
  }

  const updateNarrativaField = (infId: string, field: 'conclusiones' | 'recomendaciones' | 'observaciones_finales', value: string) => {
    setNarrativa(prev => ({
      ...prev,
      [infId]: {
        ...getNarrativa(infId),
        [field]: value
      }
    }))
  }

  const handleGuardarBorrador = async (infId: string) => {
    setGuardando(true)
    setFormError(null)
    const dataNarrativa = getNarrativa(infId)
    try {
      await informeService.guardarBorrador(infId, dataNarrativa)
      setSuccessBanner('El informe se guardó correctamente.')
      setTimeout(() => setSuccessBanner(null), 5000)
      refetch()
    } catch (err: any) {
      setFormError(err?.friendlyMessage || err?.message || 'Error al guardar borrador')
    } finally {
      setGuardando(false)
    }
  }

  const handleConfirmarFinalizar = (infId: string) => {
    setSelectedInformeId(infId)
    setConfirmModalOpen(true)
  }

  const handleFinalizar = async () => {
    if (!selectedInformeId) return
    setFinalizando(true)
    setFormError(null)
    const dataNarrativa = getNarrativa(selectedInformeId)
    try {
      await informeService.finalizar(selectedInformeId, dataNarrativa)
      setConfirmModalOpen(false)
      setSelectedInformeId(null)
      setSuccessBanner('El informe final se generó correctamente.')
      setTimeout(() => setSuccessBanner(null), 5000)
      refetch()
    } catch (err: any) {
      setFormError(err?.friendlyMessage || err?.message || 'Error al finalizar informe')
    } finally {
      setFinalizando(false)
    }
  }

  const handleConfirmarDescartar = (infId: string) => {
    setSelectedInformeId(infId)
    setDiscardModalOpen(true)
  }

  const handleDescartarBorrador = async () => {
    if (!selectedInformeId) return
    setDescartando(true)
    setFormError(null)
    try {
      const res = await informeService.descartarBorrador(selectedInformeId)
      setDiscardModalOpen(false)
      setSelectedInformeId(null)
      setSuccessBanner(res.message || 'El borrador fue descartado correctamente.')
      setTimeout(() => setSuccessBanner(null), 5000)
      refetch()
    } catch (err: any) {
      setFormError(err?.friendlyMessage || err?.message || 'Error al descartar borrador')
    } finally {
      setDescartando(false)
    }
  }

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader 
        title="Informe Final de Auditoría" 
        subtitle="Generación automática y consolidación de observaciones, hallazgos, apelaciones y conclusiones"
        actions={
          <Button variant="primary" className="text-xs" onClick={handleGenerar} disabled={generando}>
            <Plus className="w-3 h-3" /> Generar nuevo informe
          </Button>
        }
      />

      {successBanner && (
        <div className="p-4 rounded-xl bg-green-50 border border-green-200 text-green-800 text-xs font-semibold flex items-center justify-between shadow-sm animate-fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
            <span>{successBanner}</span>
          </div>
          <button onClick={() => setSuccessBanner(null)} className="text-green-600 hover:text-green-800">×</button>
        </div>
      )}

      {formError && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-semibold flex items-center gap-2 shadow-sm">
          <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0" />
          <span>{formError}</span>
        </div>
      )}

      {informesAuditoria.length === 0 ? (
        <EmptyState
          icon={ClipboardCheck}
          title="Sin informes de auditoría"
          description="Genere el informe cuando haya completado la verificación de estándares"
          action={
            <Button variant="primary" onClick={handleGenerar} disabled={generando}>
              Generar Informe Final
            </Button>
          }
        />
      ) : informesAuditoria.map(inf => {
        const c = inf.contenido_json as any
        const estadoInforme = c?.estado || 'BORRADOR'
        const esBorrador = estadoInforme === 'BORRADOR'
        const currentNarrativa = getNarrativa(inf.id, c?.narrativa)

        return (
          <Card key={inf.id}>
            <div className="space-y-6">
              {/* Header del Informe */}
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center flex-shrink-0">
                    <FileText className="w-5 h-5 text-primary-500" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-extrabold text-primary-500">INFORME FINAL DE AUDITORÍA</h3>
                      <Badge variant={esBorrador ? 'orange' : 'green'} icon={esBorrador ? <FileText className="w-3 h-3" /> : <Lock className="w-3 h-3" />}>
                        {estadoInforme}
                      </Badge>
                      <Badge variant="blue">{inf.evaluacion?.anio || c?.meta?.anio}</Badge>
                    </div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      Empresa: <strong>{c?.meta?.empresa}</strong> (NIT {c?.meta?.nit}) · Capítulo: <strong>{c?.meta?.capitulo}</strong>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {!esBorrador && (
                    <Button 
                      variant="ghost" 
                      className="text-xs" 
                      icon={<Download className="w-3.5 h-3.5" />}
                      onClick={() => window.open(`/api/informes/${inf.id}/descargar-pdf`, '_blank')}
                    >
                      Descargar PDF
                    </Button>
                  )}
                </div>
              </div>

              {/* Resultados Estructurados Automáticos */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs">
                <div>
                  <div className="text-[10px] text-slate-400 font-bold uppercase">Cumplimiento Global</div>
                  <div className="text-xl font-extrabold text-primary-500">{c?.resumen_ejecutivo?.cumplimiento_global}%</div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400 font-bold uppercase">Clasificación</div>
                  <Badge variant={c?.clasificacion === 'ACEPTABLE' ? 'green' : c?.clasificacion === 'CRÍTICO' ? 'red' : 'orange'}>
                    {c?.clasificacion}
                  </Badge>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400 font-bold uppercase">Puntaje Obtenido</div>
                  <div className="text-sm font-bold text-slate-700">{c?.resumen_ejecutivo?.puntaje_obtenido} / {c?.resumen_ejecutivo?.puntaje_maximo}</div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400 font-bold uppercase">Estándares Cumplidos</div>
                  <div className="text-sm font-bold text-green-700">{c?.resumen_ejecutivo?.cumple} de {c?.resumen_ejecutivo?.total_estandares}</div>
                </div>
              </div>

              {/* Hallazgos Registrados */}
              {c?.hallazgos?.length > 0 && (
                <div className="space-y-2">
                  <div className="text-xs font-bold text-primary-500 uppercase tracking-wider flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-amber-500" /> Hallazgos y Observaciones Automáticos ({c.hallazgos.length})
                  </div>
                  <div className="space-y-2">
                    {c.hallazgos.map((h: any, idx: number) => (
                      <div key={idx} className="p-3 bg-surface rounded-xl border border-surface-2 text-xs flex items-start justify-between gap-3">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <Badge variant={h.tipo?.includes('no_conformidad') ? 'red' : h.tipo === 'fortaleza' ? 'green' : 'blue'}>
                              {h.tipo?.replace(/_/g, ' ')}
                            </Badge>
                            {h.estandar_codigo && <span className="font-bold text-slate-700">Estándar {h.estandar_codigo}</span>}
                          </div>
                          <p className="text-slate-700 font-medium">{h.descripcion}</p>
                        </div>
                        <span className="text-[10px] text-slate-400 flex-shrink-0">{new Date(h.fecha).toLocaleDateString()}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Apelaciones Registradas */}
              {c?.apelaciones?.length > 0 && (
                <div className="space-y-2">
                  <div className="text-xs font-bold text-primary-500 uppercase tracking-wider flex items-center gap-1.5">
                    <Scale className="w-4 h-4 text-brand-500" /> Historial de Apelaciones ({c.apelaciones.length})
                  </div>
                  <div className="space-y-2">
                    {c.apelaciones.map((ap: any, idx: number) => (
                      <div key={idx} className="p-3 bg-amber-50/50 rounded-xl border border-amber-100 text-xs space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-amber-900">Estándar {ap.estandar_codigo} — {ap.estandar_nombre}</span>
                          <Badge variant={ap.estado === 'aceptada' ? 'green' : ap.estado === 'rechazada' ? 'red' : 'orange'}>
                            {ap.estado}
                          </Badge>
                        </div>
                        <p className="text-slate-700"><strong>Motivo Apelación:</strong> "{ap.motivo}"</p>
                        {ap.respuesta_auditor && <p className="text-blue-900 font-medium"><strong>Respuesta Auditor:</strong> "{ap.respuesta_auditor}"</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Apartados Narrativos Editables / Narrativa Final */}
              <div className="pt-4 border-t border-slate-100 space-y-4">
                <div className="text-xs font-extrabold text-primary-500 uppercase tracking-wider">
                  Apartados Narrativos del Auditor {esBorrador ? '(Editables en Borrador)' : '(Bloqueados en Informe Final)'}
                </div>

                {esBorrador ? (
                  <>
                    <FormField label="Conclusiones del Auditor" helperText="Sustento cualitativo general de la evaluación">
                      <Textarea 
                        value={currentNarrativa.conclusiones} 
                        onChange={e => updateNarrativaField(inf.id, 'conclusiones', e.target.value)} 
                        placeholder="Redactar conclusiones principales del dictamen..." 
                        rows={3} 
                      />
                    </FormField>

                    <FormField label="Recomendaciones" helperText="Acciones recomendadas para el plan de mejoramiento">
                      <Textarea 
                        value={currentNarrativa.recomendaciones} 
                        onChange={e => updateNarrativaField(inf.id, 'recomendaciones', e.target.value)} 
                        placeholder="Redactar recomendaciones específicas..." 
                        rows={3} 
                      />
                    </FormField>

                    <FormField label="Observaciones Finales" helperText="Comentarios finales y cierre del dictamen">
                      <Textarea 
                        value={currentNarrativa.observaciones_finales} 
                        onChange={e => updateNarrativaField(inf.id, 'observaciones_finales', e.target.value)} 
                        placeholder="Redactar comentarios finales..." 
                        rows={3} 
                      />
                    </FormField>

                    <div className="flex items-center justify-end gap-3 pt-2">
                      <Button 
                        variant="ghost" 
                        className="text-xs text-rose-600 hover:text-rose-700 hover:bg-rose-50 border border-rose-200" 
                        icon={<Trash2 className="w-3.5 h-3.5 text-rose-600" />}
                        onClick={() => handleConfirmarDescartar(inf.id)}
                        disabled={descartando || guardando || finalizando}
                      >
                        Descartar borrador
                      </Button>
                      <Button 
                        variant="ghost" 
                        className="text-xs" 
                        icon={<Save className="w-3.5 h-3.5" />}
                        onClick={() => handleGuardarBorrador(inf.id)}
                        disabled={guardando || descartando}
                      >
                        {guardando ? 'Guardando...' : 'Guardar borrador'}
                      </Button>
                      <Button 
                        variant="primary" 
                        className="text-xs" 
                        icon={<Lock className="w-3.5 h-3.5" />}
                        onClick={() => handleConfirmarFinalizar(inf.id)}
                        disabled={finalizando || descartando}
                      >
                        Finalizar informe
                      </Button>
                    </div>
                  </>
                ) : (
                  <div className="space-y-3 bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs">
                    <div>
                      <div className="font-bold text-slate-500 text-[10px] uppercase mb-1">Conclusiones del Auditor:</div>
                      <div className="text-slate-800 italic">{currentNarrativa.conclusiones || 'Sin conclusiones registradas.'}</div>
                    </div>
                    <div>
                      <div className="font-bold text-slate-500 text-[10px] uppercase mb-1">Recomendaciones:</div>
                      <div className="text-slate-800 italic">{currentNarrativa.recomendaciones || 'Sin recomendaciones registradas.'}</div>
                    </div>
                    <div>
                      <div className="font-bold text-slate-500 text-[10px] uppercase mb-1">Observaciones Finales:</div>
                      <div className="text-slate-800 italic">{currentNarrativa.observaciones_finales || 'Sin observaciones finales registradas.'}</div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </Card>
        )
      })}

      {/* Modal de Confirmación para Finalizar */}
      <Modal
        open={confirmModalOpen}
        onClose={() => setConfirmModalOpen(false)}
        title="Confirmar Finalización de Informe"
        footer={
          <>
            <Button variant="ghost" onClick={() => setConfirmModalOpen(false)}>Cancelar</Button>
            <Button variant="primary" onClick={handleFinalizar} disabled={finalizando}>
              {finalizando ? 'Finalizando...' : 'Sí, Finalizar Informe'}
            </Button>
          </>
        }
      >
        <div className="space-y-3 text-xs text-slate-700">
          <p className="font-semibold text-rose-700">
            ¿Está seguro de que desea finalizar el informe?
          </p>
          <p>
            Una vez finalizado, los campos narrativos quedarán permanentemente bloqueados y no podrán ser modificados. Se sellará la trazabilidad final de auditoría.
          </p>
        </div>
      </Modal>

      {/* Modal de Confirmación para Descartar Borrador */}
      <Modal
        open={discardModalOpen}
        onClose={() => setDiscardModalOpen(false)}
        title="¿Descartar este borrador?"
        footer={
          <>
            <Button variant="ghost" onClick={() => setDiscardModalOpen(false)}>Cancelar</Button>
            <Button 
              variant="primary" 
              className="bg-rose-600 hover:bg-rose-700 text-white" 
              onClick={handleDescartarBorrador} 
              disabled={descartando}
            >
              {descartando ? 'Descartando...' : 'Sí, Descartar Borrador'}
            </Button>
          </>
        }
      >
        <div className="space-y-3 text-xs text-slate-700">
          <p className="font-semibold text-rose-700">
            Se eliminará el borrador del Informe Final, pero NO se eliminarán:
          </p>
          <ul className="list-disc list-inside space-y-1 text-slate-600 pl-2">
            <li>Evaluación</li>
            <li>Respuestas y calificaciones</li>
            <li>Hallazgos y observaciones</li>
            <li>Apelaciones y resoluciones</li>
            <li>Evidencias documentales</li>
            <li>Notificaciones enviadas</li>
            <li>Historial de auditoría</li>
          </ul>
        </div>
      </Modal>
    </div>
  )
}
