import { useState } from 'react'
import { Card, PageHeader, Badge, Button, EmptyState } from '@/components/ui'
import { LoadingSpinner, ErrorDisplay, Modal, FormField, Select, Textarea } from '@/components/ui/forms'
import { estandarService, ApelacionItem } from '@/services/estandar.service'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Scale, CheckCircle2, XCircle, AlertCircle, FileText, User, Calendar, MessageSquare } from 'lucide-react'

export default function ApelacionesAuditorView() {
  const qc = useQueryClient()
  const [filtro, setFiltro] = useState<'todas' | 'pendiente' | 'aceptada' | 'rechazada'>('todas')
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedApelacion, setSelectedApelacion] = useState<ApelacionItem | null>(null)
  const [decision, setDecision] = useState<'aceptada' | 'rechazada' | 'resuelta'>('aceptada')
  const [respuestaAuditor, setRespuestaAuditor] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [successBanner, setSuccessBanner] = useState<string | null>(null)

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['apelaciones-auditor'],
    queryFn: async () => {
      const res = await estandarService.listarApelaciones()
      return Array.isArray(res) ? res : ((res as any)?.results || [])
    },
  })

  const resolverMut = useMutation({
    mutationFn: ({ id, decision, respuestaAuditor }: { id: string; decision: 'aceptada' | 'rechazada' | 'resuelta'; respuestaAuditor: string }) =>
      estandarService.resolverApelacion(id, decision, respuestaAuditor),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['apelaciones-auditor'] })
      qc.invalidateQueries({ queryKey: ['estandares'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
      qc.invalidateQueries({ queryKey: ['notificaciones'] })
    },
  })

  if (isLoading) return <LoadingSpinner text="Cargando apelaciones de auditoría..." />
  if (error) return <ErrorDisplay message={(error as Error)?.message ?? 'Error al cargar apelaciones'} onRetry={refetch} />

  const lista: ApelacionItem[] = data || []
  const filtradas = filtro === 'todas' ? lista : lista.filter(a => a.estado === filtro)

  const abrirModal = (ap: ApelacionItem) => {
    setSelectedApelacion(ap)
    setDecision(ap.estado === 'pendiente' ? 'aceptada' : (ap.estado as any))
    setRespuestaAuditor(ap.respuesta_auditor || '')
    setFormError(null)
    setModalOpen(true)
  }

  const handleResolver = async () => {
    if (!selectedApelacion) return
    setFormError(null)

    if (!respuestaAuditor.trim()) {
      setFormError('Debe ingresar un comentario o justificación para la decisión.')
      return
    }

    try {
      await resolverMut.mutateAsync({
        id: selectedApelacion.id,
        decision,
        respuestaAuditor: respuestaAuditor.trim(),
      })

      setModalOpen(false)
      setSelectedApelacion(null)
      setSuccessBanner(`La apelación fue resuelta como '${decision.toUpperCase()}' exitosamente. Se ha notificado al Responsable SST.`)
      setTimeout(() => setSuccessBanner(null), 6000)
    } catch (err: any) {
      setFormError(err?.friendlyMessage || err?.message || 'Error al resolver la apelación')
    }
  }

  const getEstadoBadge = (estado: string) => {
    switch (estado) {
      case 'pendiente':
        return <Badge variant="orange" icon={<AlertCircle className="w-3 h-3" />}>Pendiente</Badge>
      case 'aceptada':
        return <Badge variant="green" icon={<CheckCircle2 className="w-3 h-3" />}>Aceptada</Badge>
      case 'rechazada':
        return <Badge variant="red" icon={<XCircle className="w-3 h-3" />}>Rechazada</Badge>
      default:
        return <Badge variant="blue">{estado}</Badge>
    }
  }

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        title="Gestión de Apelaciones"
        subtitle="Revisión y resolución de apelaciones a observaciones formuladas por el auditor"
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

      {/* Tabs de Filtro */}
      <div className="flex border-b border-surface-2 gap-6 text-xs font-bold">
        {[
          { key: 'todas', label: `Todas (${lista.length})` },
          { key: 'pendiente', label: `Pendientes (${lista.filter(a => a.estado === 'pendiente').length})` },
          { key: 'aceptada', label: `Aceptadas (${lista.filter(a => a.estado === 'aceptada').length})` },
          { key: 'rechazada', label: `Rechazadas (${lista.filter(a => a.estado === 'rechazada').length})` },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => setFiltro(t.key as any)}
            className={`pb-3 transition-colors relative ${
              filtro === t.key ? 'text-brand-500 border-b-2 border-brand-500' : 'text-slate-400 hover:text-slate-600'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Lista de Apelaciones */}
      <div className="space-y-4">
        {filtradas.length === 0 ? (
          <EmptyState
            icon={Scale}
            title="Sin apelaciones"
            description={filtro === 'todas' ? 'No hay apelaciones registradas en la evaluación actual.' : `No hay apelaciones con estado "${filtro}".`}
          />
        ) : (
          filtradas.map((ap) => (
            <Card key={ap.id}>
              <div className="space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-primary-500">
                      Estándar {ap.codigo_estandar || ''}
                    </span>
                    {ap.nombre_estandar && (
                      <span className="text-xs text-slate-500 max-w-md truncate">
                        - {ap.nombre_estandar}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {getEstadoBadge(ap.estado)}
                    <span className="text-[10px] text-slate-400 flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {new Date(ap.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-50 p-3.5 rounded-xl border border-slate-100 text-xs">
                  <div>
                    <div className="text-[10px] font-extrabold uppercase text-slate-400 tracking-wider mb-1 flex items-center gap-1">
                      <FileText className="w-3 h-3" /> Observación / Contexto Auditor
                    </div>
                    <p className="text-slate-700 italic">
                      "{ap.observacion_original || (ap as any).hallazgo_descripcion || 'Sin observación registrada'}"
                    </p>
                  </div>

                  <div>
                    <div className="text-[10px] font-extrabold uppercase text-brand-700 tracking-wider mb-1 flex items-center gap-1">
                      <MessageSquare className="w-3 h-3 text-brand-500" /> Apelación de Responsable SST
                    </div>
                    <p className="text-slate-800 font-medium">
                      "{ap.motivo}"
                    </p>
                    {ap.solicitante_nombre && (
                      <div className="text-[10px] text-slate-400 mt-1.5 flex items-center gap-1">
                        <User className="w-3 h-3" /> Solicitante: {ap.solicitante_nombre}
                      </div>
                    )}
                  </div>
                </div>

                {ap.respuesta_auditor && (
                  <div className="p-3 bg-blue-50/50 border border-blue-100 rounded-xl text-xs">
                    <div className="text-[10px] font-bold text-blue-700 mb-0.5">Respuesta / Decisión Auditor:</div>
                    <div className="text-slate-700">{ap.respuesta_auditor}</div>
                  </div>
                )}

                <div className="flex justify-end pt-1">
                  <Button
                    variant={ap.estado === 'pendiente' ? 'primary' : 'ghost'}
                    className="text-xs py-1.5"
                    onClick={() => abrirModal(ap)}
                  >
                    {ap.estado === 'pendiente' ? 'Revisar y Resolver Apelación' : 'Ver Detalle / Modificar'}
                  </Button>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>

      {/* Modal de Resolución */}
      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Revisión de Apelación de Auditoría"
        maxWidth="620px"
        footer={
          <>
            <Button variant="ghost" onClick={() => setModalOpen(false)}>Cancelar</Button>
            <Button variant="primary" onClick={handleResolver} disabled={resolverMut.isPending}>
              {resolverMut.isPending ? 'Guardando...' : 'Guardar Decisión'}
            </Button>
          </>
        }
      >
        {selectedApelacion && (
          <div className="space-y-4 text-xs">
            {formError && (
              <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 font-semibold">
                {formError}
              </div>
            )}

            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-2">
              <div className="font-bold text-primary-500 text-sm">
                Estándar {selectedApelacion.codigo_estandar} — {selectedApelacion.nombre_estandar}
              </div>
              <div className="text-slate-600">
                <strong>Observación previa:</strong> "{selectedApelacion.observacion_original || (selectedApelacion as any).hallazgo_descripcion || 'Sin observación'}"
              </div>
              <div className="text-brand-800 font-medium">
                <strong>Motivo de apelación SST:</strong> "{selectedApelacion.motivo}"
              </div>
            </div>

            <FormField label="Decisión sobre la Apelación" required>
              <Select
                value={decision}
                onChange={(e) => setDecision(e.target.value as any)}
                options={[
                  { value: 'aceptada', label: 'Aceptar Apelación (Conceder razón al Responsable SST)' },
                  { value: 'rechazada', label: 'Rechazar Apelación (Mantener observación/calificación previa)' },
                  { value: 'resuelta', label: 'Dar por Resuelta con Ajustes' },
                ]}
              />
            </FormField>

            <FormField label="Comentarios y Justificación Técnica del Auditor" required>
              <Textarea
                value={respuestaAuditor}
                onChange={(e) => setRespuestaAuditor(e.target.value)}
                placeholder="Ingrese el sustento técnico de la decisión adoptada para la trazabilidad..."
                rows={4}
              />
            </FormField>
          </div>
        )}
      </Modal>
    </div>
  )
}
