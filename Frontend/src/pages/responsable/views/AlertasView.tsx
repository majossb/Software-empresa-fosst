import { useState, useEffect } from 'react'
import { Card, Button, EmptyState } from '@/components/ui'
import { LoadingSpinner } from '@/components/ui/forms'
import { alertasService, ReglaAlerta } from '@/services/alertas.service'
import {
  Bell, Play, Clock, CheckCircle2,
  AlertTriangle, ShieldAlert, Sparkles, Filter
} from 'lucide-react'

export default function AlertasView() {
  const [reglas, setReglas] = useState<ReglaAlerta[]>([])
  const [loading, setLoading] = useState(true)
  const [ejecutando, setEjecutando] = useState(false)
  const [mensajeEjecucion, setMensajeEjecucion] = useState<string | null>(null)

  useEffect(() => {
    cargarReglas()
  }, [])

  const cargarReglas = async () => {
    setLoading(true)
    try {
      const res = await alertasService.getReglas()
      setReglas(Array.isArray(res) ? res : res.results || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleEjecutarRevision = async () => {
    setEjecutando(true)
    setMensajeEjecucion(null)
    try {
      const res = await alertasService.ejecutarRevision()
      setMensajeEjecucion(res.mensaje)
    } catch (e: any) {
      setMensajeEjecucion('Error ejecutando revisión de vencimientos.')
    } finally {
      setEjecutando(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Motor de Alertas y Vencimientos
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Monitoreo proactivo de contratos, periodos de prueba, exámenes médicos, licencias y afiliaciones.
          </p>
        </div>
        <Button
          variant="primary"
          onClick={handleEjecutarRevision}
          disabled={ejecutando}
          className="flex items-center gap-2 text-xs py-2"
        >
          <Play className={`w-3.5 h-3.5 ${ejecutando ? 'animate-spin' : ''}`} />
          {ejecutando ? 'Revisando...' : 'Ejecutar Revisión Ahora'}
        </Button>
      </div>

      {/* Execution Feedback */}
      {mensajeEjecucion && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          {mensajeEjecucion}
        </div>
      )}

      {/* Rules List */}
      <Card className="p-4 space-y-4">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 pb-2 border-b border-slate-100">
          <Bell className="w-4 h-4 text-primary-500" />
          Reglas de Alerta Activas ({reglas.length})
        </h3>

        {loading ? (
          <LoadingSpinner text="Cargando reglas de alerta..." />
        ) : reglas.length === 0 ? (
          <EmptyState title="Sin reglas de alerta" description="No se registran reglas de alerta configuradas." />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {reglas.map((r) => (
              <div
                key={r.id}
                className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-3 hover:border-primary-200 transition"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="font-mono text-[10px] font-bold text-primary-500 uppercase">{r.codigo}</span>
                    <h4 className="text-xs font-bold text-slate-900 mt-0.5">{r.nombre}</h4>
                  </div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded capitalize ${
                    r.nivel_criticidad === 'critico' ? 'bg-rose-100 text-rose-700' :
                    r.nivel_criticidad === 'importante' ? 'bg-amber-100 text-amber-700' :
                    'bg-slate-200 text-slate-700'
                  }`}>
                    {r.nivel_criticidad_display || r.nivel_criticidad}
                  </span>
                </div>

                <p className="text-xs text-slate-600 bg-white p-2.5 rounded-lg border border-slate-100 font-mono text-[11px] leading-relaxed">
                  "{r.mensaje_template}"
                </p>

                <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-200/60">
                  <span className="flex items-center gap-1 font-medium">
                    <Clock className="w-3 h-3 text-slate-400" />
                    Anticipación: <strong>{r.dias_anticipacion} días</strong>
                  </span>
                  <span>
                    Destinatarios: <strong>{r.roles_destinatarios?.join(', ') || 'Responsable'}</strong>
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
