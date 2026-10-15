import { useState } from 'react'
import { Card, PageHeader, Badge, Button, EmptyState } from '@/components/ui'
import { LoadingSpinner, ErrorDisplay, Modal, FormField, Input, Select, Textarea } from '@/components/ui/forms'
import { usePlanMejora, useCrearPlanMejora, useActualizarPlanMejora } from '@/hooks/useApi'
import { Plus, Clock, CheckCircle2, AlertTriangle, AlertCircle, RefreshCw, ClipboardCheck } from 'lucide-react'
import type { PrioridadPlan, EstadoPlan } from '@/types'

const PRIORIDAD_CONFIG: Record<string, { label: string; variant: 'red' | 'orange' | 'blue' }> = {
  urgente:    { label: 'Urgente (3 meses)', variant: 'red' },
  importante: { label: 'Importante (6 meses)', variant: 'orange' },
  aceptable:  { label: 'Aceptable (12 meses)', variant: 'blue' },
}

const ESTADO_CONFIG: Record<string, { label: string; variant: 'gray' | 'orange' | 'green' }> = {
  pendiente:   { label: 'Pendiente', variant: 'gray' },
  en_progreso: { label: 'En progreso', variant: 'orange' },
  completado:  { label: 'Completado', variant: 'green' },
}

export default function PlanMejoraView() {
  const { data, isLoading, error, refetch } = usePlanMejora()
  const crearMut = useCrearPlanMejora()
  const actualizarMut = useActualizarPlanMejora()
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState({ accion: '', responsable: '', prioridad: 'importante' as PrioridadPlan })
  const [filtro, setFiltro] = useState<string>('todos')

  if (isLoading) return <LoadingSpinner text="Cargando plan de mejora..." />
  if (error || !data) return <ErrorDisplay message={(error as Error)?.message ?? 'Error'} onRetry={refetch} />

  const { planes, resumen } = data
  const planesFiltrados = filtro === 'todos' ? planes : planes.filter((p) => p.estado === filtro)

  const handleCrear = async () => {
    if (!form.accion.trim() || !form.responsable.trim()) return
    await crearMut.mutateAsync(form)
    setModalOpen(false)
    setForm({ accion: '', responsable: '', prioridad: 'importante' })
  }

  const handleCambiarEstado = async (id: string, estado: EstadoPlan) => {
    await actualizarMut.mutateAsync({ id, data: { estado } })
  }

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        title="Plan de Mejora"
        subtitle="Acciones correctivas y preventivas · Res. 0312/2019"
        actions={<Button variant="primary" icon={Plus} className="text-xs" onClick={() => setModalOpen(true)}>Nueva acción</Button>}
      />

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        {[
          { label: 'Total', count: resumen.total, icon: ClipboardCheck, color: 'text-primary-500' },
          { label: 'Pendientes', count: resumen.pendientes, icon: Clock, color: 'text-slate-500' },
          { label: 'En progreso', count: resumen.en_progreso, icon: RefreshCw, color: 'text-brand-700' },
          { label: 'Completados', count: resumen.completados, icon: CheckCircle2, color: 'text-emerald-700' },
          { label: 'Vencidos', count: resumen.vencidos, icon: AlertCircle, color: 'text-rose-600' },
        ].map((k) => (
          <div key={k.label} className="bg-white border border-slate-200 rounded-xl p-4 text-center shadow-sm">
            <div className="flex justify-center mb-1 text-slate-400">
              <k.icon className="w-5 h-5" />
            </div>
            <div className={`text-xl font-black ${k.color}`}>{k.count}</div>
            <div className="text-[10px] text-slate-500 uppercase font-bold">{k.label}</div>
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        {['todos', 'pendiente', 'en_progreso', 'completado'].map((f) => (
          <button
            key={f}
            onClick={() => setFiltro(f)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              filtro === f
                ? 'bg-brand-500/15 text-primary-500 border border-brand-300 font-bold'
                : 'bg-white text-slate-500 border border-slate-200 hover:text-primary-500'
            }`}
          >
            {f === 'todos' ? 'Todos' : f === 'en_progreso' ? 'En progreso' : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {planesFiltrados.length === 0 ? (
          <EmptyState
            icon={ClipboardCheck}
            title="Sin acciones registradas"
            description="No se encontraron acciones para el filtro seleccionado."
          />
        ) : planesFiltrados.map((plan) => {
          const prioConfig = PRIORIDAD_CONFIG[plan.prioridad] ?? PRIORIDAD_CONFIG.importante
          const estadoConfig = ESTADO_CONFIG[plan.estado] ?? ESTADO_CONFIG.pendiente
          const vencido = plan.estado !== 'completado' && new Date(plan.fecha_limite) < new Date()
          return (
            <Card key={plan.id}>
              <div className="flex items-start gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant={prioConfig.variant}>{prioConfig.label}</Badge>
                    <Badge variant={estadoConfig.variant}>{estadoConfig.label}</Badge>
                    {vencido && <Badge variant="red" icon={AlertTriangle}>Vencido</Badge>}
                  </div>
                  <div className="text-sm text-primary-500 font-semibold mt-2">{plan.accion}</div>
                  <div className="text-xs text-slate-500 mt-1">
                    Responsable: <span className="text-slate-700 font-medium">{plan.responsable}</span>
                    {' · '}Vence: <span className={vencido ? 'text-rose-600 font-semibold' : 'text-slate-700'}>
                      {new Date(plan.fecha_limite).toLocaleDateString('es-CO')}
                    </span>
                  </div>
                </div>
                {plan.estado !== 'completado' && (
                  <div className="flex gap-2 flex-shrink-0">
                    {plan.estado === 'pendiente' && (
                      <Button variant="ghost" className="text-xs py-1" onClick={() => handleCambiarEstado(plan.id, 'en_progreso')}>
                        Iniciar
                      </Button>
                    )}
                    <Button variant="primary" icon={CheckCircle2} className="text-xs py-1" onClick={() => handleCambiarEstado(plan.id, 'completado')}>
                      Completar
                    </Button>
                  </div>
                )}
              </div>
            </Card>
          )
        })}
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Nueva Acción de Mejora" footer={
        <>
          <Button variant="ghost" onClick={() => setModalOpen(false)}>Cancelar</Button>
          <Button variant="primary" onClick={handleCrear} disabled={crearMut.isPending}>
            {crearMut.isPending ? 'Creando...' : 'Crear acción'}
          </Button>
        </>
      }>
        <FormField label="Acción" required>
          <Textarea value={form.accion} onChange={(e) => setForm({ ...form, accion: e.target.value })} placeholder="Describir la acción correctiva o preventiva..." />
        </FormField>
        <FormField label="Responsable" required>
          <Input value={form.responsable} onChange={(e) => setForm({ ...form, responsable: e.target.value })} placeholder="Nombre del responsable" />
        </FormField>
        <FormField label="Prioridad" required>
          <Select value={form.prioridad} onChange={(e) => setForm({ ...form, prioridad: e.target.value as PrioridadPlan })} options={[
            { value: 'urgente', label: 'Urgente — 3 meses' },
            { value: 'importante', label: 'Importante — 6 meses' },
            { value: 'aceptable', label: 'Aceptable — 12 meses' },
          ]} />
        </FormField>
      </Modal>
    </div>
  )
}
