import { useState, useEffect } from 'react'
import { Card, Button } from '@/components/ui'
import { michcService, EvaluacionHabilitacion, MichcResumen } from '@/services/michc.service'
import {
  ShieldCheck, AlertTriangle, XCircle, RefreshCw,
  Sparkles, CheckCircle2, FileText, UserCheck, ArrowRight, Lightbulb
} from 'lucide-react'

export default function MichcView() {
  const [evaluaciones, setEvaluaciones] = useState<EvaluacionHabilitacion[]>([])
  const [resumen, setResumen] = useState<MichcResumen | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedEval, setSelectedEval] = useState<EvaluacionHabilitacion | null>(null)
  const [recalculating, setRecalculating] = useState(false)

  useEffect(() => {
    cargarMatriz()
  }, [])

  const cargarMatriz = async () => {
    setLoading(true)
    try {
      const [resMatriz, resResumen] = await Promise.all([
        michcService.getMatriz(),
        michcService.getResumen(),
      ])
      setEvaluaciones(Array.isArray(resMatriz) ? resMatriz : resMatriz.results || [])
      setResumen(resResumen)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const verDetalle = async (id: string) => {
    try {
      const detalle = await michcService.getEvaluacionById(id)
      setSelectedEval(detalle)
    } catch (e) {
      console.error(e)
    }
  }

  const handleRecalcular = async (id: string) => {
    setRecalculating(true)
    try {
      const actualizada = await michcService.recalcular(id)
      setSelectedEval(actualizada)
      await cargarMatriz()
    } catch (e) {
      console.error(e)
    } finally {
      setRecalculating(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            MICHC — Matriz Inteligente de Cumplimiento y Habilitación
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Reconciliación continua del perfil de cargo contra el expediente médico, laboral y normativo del trabajador.
          </p>
        </div>
        <Button
          variant="secondary"
          onClick={cargarMatriz}
          className="flex items-center gap-2 text-xs"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Actualizar Matriz
        </Button>
      </div>

      {/* KPI Cards */}
      {resumen && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="p-4 border-l-4 border-l-emerald-500">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-500">Habilitados (Verde)</span>
              <ShieldCheck className="w-5 h-5 text-emerald-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-2">
              {resumen.por_semaforo.verde || 0}
            </div>
          </Card>
          <Card className="p-4 border-l-4 border-l-amber-500">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-500">Observaciones (Amarillo)</span>
              <AlertTriangle className="w-5 h-5 text-amber-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-2">
              {resumen.por_semaforo.amarillo || 0}
            </div>
          </Card>
          <Card className="p-4 border-l-4 border-l-rose-500">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-500">Crítico / Incompatible (Rojo)</span>
              <XCircle className="w-5 h-5 text-rose-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-2">
              {resumen.por_semaforo.rojo || 0}
            </div>
          </Card>
          <Card className="p-4 border-l-4 border-l-primary-500">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-500">Cumplimiento Global</span>
              <UserCheck className="w-5 h-5 text-primary-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-2">
              {resumen.promedio_cumplimiento}%
            </div>
          </Card>
        </div>
      )}

      {/* Main Grid: Matrix & Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Matrix Table */}
        <div className={selectedEval ? "lg:col-span-2 space-y-4" : "lg:col-span-3 space-y-4"}>
          <Card className="p-4">
            {loading ? (
              <div className="py-12 text-center text-slate-400 text-sm">Cargando matriz MICHC...</div>
            ) : evaluaciones.length === 0 ? (
              <div className="py-12 text-center text-slate-400 text-sm">
                No hay trabajadores evaluados actualmente.
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {evaluaciones.map((ev) => (
                  <div
                    key={ev.id}
                    onClick={() => verDetalle(ev.id)}
                    className={`p-4 hover:bg-slate-50 transition cursor-pointer flex items-center justify-between rounded-lg ${
                      selectedEval?.id === ev.id ? 'bg-primary-50/60 border border-primary-200' : ''
                    }`}
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-slate-900">{ev.trabajador_nombre}</span>
                        <span className="text-xs text-slate-400 font-mono">({ev.trabajador_documento})</span>
                      </div>
                      <p className="text-xs text-slate-500">
                        Cargo: <span className="font-medium text-slate-700">{ev.cargo_nombre || 'Sin Asignar'}</span>
                        {ev.sede_nombre && ` • Sede: ${ev.sede_nombre}`}
                      </p>
                    </div>

                    <div className="flex items-center gap-4">
                      {/* Semaforo Badge */}
                      <div className="text-right">
                        <div className="text-sm font-bold text-slate-900">{ev.porcentaje_cumplimiento}%</div>
                        <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${
                          ev.semaforo === 'verde' ? 'bg-emerald-100 text-emerald-700' :
                          ev.semaforo === 'amarillo' ? 'bg-amber-100 text-amber-700' :
                          'bg-rose-100 text-rose-700'
                        }`}>
                          {ev.estado_habilitacion_display}
                        </span>
                      </div>
                      <ArrowRight className="w-4 h-4 text-slate-300" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Detail & Diagnostic Column */}
        {selectedEval && (
          <div className="lg:col-span-1 space-y-4">
            <Card className="p-5 space-y-4 border-slate-200 shadow-md">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div>
                  <h3 className="font-bold text-sm text-slate-900">{selectedEval.trabajador_nombre}</h3>
                  <p className="text-xs text-slate-400 mt-0.5">{selectedEval.cargo_nombre || 'Sin Cargo'}</p>
                </div>
                <Button
                  variant="secondary"
                  onClick={() => handleRecalcular(selectedEval.id)}
                  disabled={recalculating}
                  className="text-xs py-1 px-2 flex items-center gap-1.5"
                >
                  <RefreshCw className={`w-3 h-3 ${recalculating ? 'animate-spin' : ''}`} />
                  Recalcular
                </Button>
              </div>

              {/* IA Narrative */}
              {selectedEval.interpretacion_ia && (
                <div className="p-3.5 bg-gradient-to-br from-slate-50 to-primary-50/40 rounded-xl border border-primary-100 space-y-1.5">
                  <div className="flex items-center gap-1.5 text-primary-500 font-semibold text-xs">
                    <Sparkles className="w-3.5 h-3.5" />
                    Diagnóstico Inteligente (IA)
                  </div>
                  <p className="text-xs text-slate-800 leading-relaxed">
                    {selectedEval.interpretacion_ia}
                  </p>
                  {selectedEval.recomendacion_ia && (
                    <p className="text-xs text-primary-500 font-medium pt-1 border-t border-slate-200 flex items-start gap-1.5">
                      <Lightbulb className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                      <span>{selectedEval.recomendacion_ia}</span>
                    </p>
                  )}
                </div>
              )}

              {/* Breakdown of Requirements */}
              {selectedEval.detalles_requisitos && selectedEval.detalles_requisitos.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-slate-100">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Desglose de Requisitos</span>
                  <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                    {selectedEval.detalles_requisitos.map((d) => (
                      <div key={d.id} className="text-xs p-2.5 rounded bg-slate-50 border border-slate-100 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-slate-700">{d.requisito_descripcion}</span>
                          <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded capitalize ${
                            d.cumple === 'si' ? 'bg-emerald-100 text-emerald-700' :
                            d.cumple === 'parcial' ? 'bg-amber-100 text-amber-700' :
                            'bg-rose-100 text-rose-700'
                          }`}>
                            {d.cumple_display}
                          </span>
                        </div>
                        {d.observacion && (
                          <p className="text-[11px] text-slate-500 leading-tight">{d.observacion}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
