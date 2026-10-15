import { useState } from 'react'
import { Card, PageHeader, Badge, Button, EmptyState } from '@/components/ui'
import { LoadingSpinner, ErrorDisplay, Modal, FormField, Input } from '@/components/ui/forms'
import { useCapacitaciones, useCrearCapacitacion, useActualizarCapacitacion } from '@/hooks/useApi'
import { BookOpen, Plus, Calendar, CheckCircle2, Users } from 'lucide-react'

export default function CapacitacionesView() {
  const { data, isLoading, error, refetch } = useCapacitaciones()
  const crearMut = useCrearCapacitacion()
  const actualizarMut = useActualizarCapacitacion()
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState({ tema: '', proveedor: '', fecha: '', num_asistentes: 0 })
  const [filtro, setFiltro] = useState('todos')

  if (isLoading) return <LoadingSpinner text="Cargando capacitaciones..." />
  if (error || !data) return <ErrorDisplay message={(error as Error)?.message ?? 'Error'} onRetry={refetch} />

  const { capacitaciones, resumen } = data
  const filtradas = filtro === 'todos' ? capacitaciones : capacitaciones.filter(c => c.estado === filtro)

  const handleCrear = async () => {
    if (!form.tema.trim()) {
      alert('El tema es obligatorio')
      return
    }
    if (!form.fecha) {
      alert('La fecha es obligatoria')
      return
    }
    if (form.num_asistentes < 0) {
      alert('El número de asistentes esperados no puede ser negativo')
      return
    }
    await crearMut.mutateAsync(form)
    setModalOpen(false)
    setForm({ tema: '', proveedor: '', fecha: '', num_asistentes: 0 })
  }

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader 
        title="Capacitaciones" 
        subtitle="Gestión de formación y entrenamiento SST"
        actions={
          <Button 
            variant="primary" 
            className="text-xs" 
            icon={<Plus className="w-3.5 h-3.5" />}
            onClick={() => setModalOpen(true)}
          >
            Programar
          </Button>
        }
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          { label: 'Total', count: resumen.total, icon: BookOpen, color: 'text-primary-500' },
          { label: 'Programadas', count: resumen.programadas, icon: Calendar, color: 'text-blue-600' },
          { label: 'Realizadas', count: resumen.realizadas, icon: CheckCircle2, color: 'text-green-700' },
          { label: 'Canceladas', count: resumen.canceladas, icon: Users, color: 'text-red-700' },
        ].map(k => (
          <Card key={k.label}>
            <div className="flex items-center gap-3">
              <k.icon className={`w-5 h-5 ${k.color}`} />
              <div>
                <div className={`text-xl font-black ${k.color}`}>{k.count}</div>
                <div className="text-[10px] text-slate-500 uppercase">{k.label}</div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="flex gap-2">
        {['todos', 'programada', 'realizada', 'cancelada'].map(f => (
          <button 
            key={f} 
            onClick={() => setFiltro(f)} 
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${filtro === f ? 'bg-brand-50 text-brand-800 border border-brand-200' : 'bg-surface text-slate-500 border border-surface-2'}`}
          >
            {f === 'todos' ? 'Todas' : f.charAt(0).toUpperCase() + f.slice(1) + 's'}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {filtradas.length === 0 ? (
          <EmptyState
            icon={<BookOpen className="w-7 h-7" />}
            title="Sin capacitaciones"
            description={filtro === 'todos' ? 'No hay capacitaciones registradas en el sistema.' : `No hay capacitaciones con estado "${filtro}".`}
            action={
              <Button variant="primary" icon={<Plus className="w-3.5 h-3.5" />} onClick={() => setModalOpen(true)}>
                Programar Capacitación
              </Button>
            }
          />
        ) : filtradas.map(cap => (
          <Card key={cap.id}>
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center flex-shrink-0">
                <BookOpen className="w-5 h-5 text-blue-600" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-bold text-primary-500">{cap.tema}</span>
                  <Badge variant={cap.estado === 'realizada' ? 'green' : cap.estado === 'programada' ? 'blue' : 'red'}>
                    {cap.estado}
                  </Badge>
                </div>
                <div className="text-xs text-slate-500">
                  {cap.proveedor && <span>Proveedor: {cap.proveedor} · </span>}
                  Fecha: {new Date(cap.fecha).toLocaleDateString('es-CO')} · Asistentes: {cap.num_asistentes}
                </div>
              </div>
              {cap.estado === 'programada' && (
                <Button 
                  variant="primary" 
                  className="text-xs py-1 flex-shrink-0"
                  onClick={() => actualizarMut.mutate({ id: cap.id, data: { estado: 'realizada' } })}
                >
                  Marcar realizada
                </Button>
              )}
            </div>
          </Card>
        ))}
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Programar Capacitación" footer={
        <>
          <Button variant="ghost" onClick={() => setModalOpen(false)}>Cancelar</Button>
          <Button variant="primary" onClick={handleCrear} disabled={crearMut.isPending}>Programar</Button>
        </>
      }>
        <FormField label="Tema" required><Input value={form.tema} onChange={e => setForm({...form, tema: e.target.value})} placeholder="Tema de la capacitación" /></FormField>
        <FormField label="Proveedor"><Input value={form.proveedor} onChange={e => setForm({...form, proveedor: e.target.value})} placeholder="Empresa o persona" /></FormField>
        <FormField label="Fecha" required><Input type="date" value={form.fecha} onChange={e => setForm({...form, fecha: e.target.value})} /></FormField>
        <FormField label="Asistentes esperados"><Input type="number" min="0" value={form.num_asistentes} onChange={e => setForm({...form, num_asistentes: parseInt(e.target.value) || 0})} /></FormField>
      </Modal>
    </div>
  )
}
