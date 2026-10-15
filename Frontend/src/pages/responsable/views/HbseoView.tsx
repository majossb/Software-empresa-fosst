import { useState, useEffect } from 'react'
import { Card, Button, Badge, EmptyState } from '@/components/ui'
import { LoadingSpinner } from '@/components/ui/forms'
import { hbseoService, Brecha, BrechaResumen } from '@/services/hbseo.service'
import { AlertCircle, CheckCircle2, Clock, Filter, Sparkles, TrendingUp, Calendar, ArrowRight } from 'lucide-react'

export default function HbseoView() {
  const [brechas, setBrechas] = useState<Brecha[]>([])
  const [resumen, setResumen] = useState<BrechaResumen | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedBrecha, setSelectedBrecha] = useState<Brecha | null>(null)
  const [filtroEstado, setFiltroEstado] = useState<string>('')

  useEffect(() => {
    cargarDatos()
  }, [filtroEstado])

  const cargarDatos = async () => {
    setLoading(true)
    try {
      const params = filtroEstado ? { estado: filtroEstado } : undefined
      const [resBrechas, resResumen] = await Promise.all([
        hbseoService.getBrechas(params),
        hbseoService.getResumen(),
      ])
      setBrechas(Array.isArray(resBrechas) ? resBrechas : resBrechas.results || [])
      setResumen(resResumen)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const verDetalle = async (id: string) => {
    try {
      const detalle = await hbseoService.getBrechaById(id)
      setSelectedBrecha(detalle)
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            HBSEO — Historial de Brechas y Evolución Organizacional
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Trazabilidad transversal de brechas, subsanaciones y planes de acción preventivos/correctivos.
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      {resumen && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="p-4 border-l-4 border-l-rose-500">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-500">Brechas Detectadas</span>
              <AlertCircle className="w-5 h-5 text-rose-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-2">
              {resumen.por_estado.detectada || 0}
            </div>
          </Card>
          <Card className="p-4 border-l-4 border-l-amber-500">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-500">En Tratamiento / Control</span>
              <Clock className="w-5 h-5 text-amber-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-2">
              {(resumen.por_estado.en_tratamiento || 0) + (resumen.por_estado.controlada || 0)}
            </div>
          </Card>
          <Card className="p-4 border-l-4 border-l-emerald-500">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-500">Subsanadas / Cerradas</span>
              <CheckCircle2 className="w-5 h-5 text-emerald-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-2">
              {(resumen.por_estado.subsanada || 0) + (resumen.por_estado.cerrada || 0)}
            </div>
          </Card>
          <Card className="p-4 border-l-4 border-l-primary-500">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-500">Total Histórico</span>
              <TrendingUp className="w-5 h-5 text-primary-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-2">
              {resumen.total || 0}
            </div>
          </Card>
        </div>
      )}

      {/* Main Content: Table and Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* List Column */}
        <div className={selectedBrecha ? "lg:col-span-2 space-y-4" : "lg:col-span-3 space-y-4"}>
          <Card className="p-4">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4 text-slate-400" />
                <span className="text-sm font-medium text-slate-700">Filtrar por estado:</span>
                <select
                  value={filtroEstado}
                  onChange={(e) => setFiltroEstado(e.target.value)}
                  className="text-xs rounded-md border-slate-200 py-1 px-2 text-slate-700 focus:ring-brand-500 focus:border-brand-500"
                >
                  <option value="">Todos los estados</option>
                  <option value="detectada">Detectada</option>
                  <option value="en_tratamiento">En Tratamiento</option>
                  <option value="controlada">Controlada</option>
                  <option value="subsanada">Subsanada</option>
                  <option value="cerrada">Cerrada</option>
                </select>
              </div>
            </div>

            {loading ? (
              <LoadingSpinner text="Cargando brechas..." />
            ) : brechas.length === 0 ? (
              <EmptyState title="Sin brechas" description="No se registran brechas con los filtros seleccionados." />
            ) : (
              <div className="divide-y divide-slate-100">
                {brechas.map((b) => (
                  <div
                    key={b.id}
                    onClick={() => verDetalle(b.id)}
                    className={`p-4 hover:bg-slate-50 transition cursor-pointer flex items-center justify-between rounded-lg ${
                      selectedBrecha?.id === b.id ? 'bg-primary-50/60 border border-primary-200' : ''
                    }`}
                  >
                    <div className="space-y-1 pr-4">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-primary-500">{b.codigo}</span>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium capitalize">
                          {b.clasificacion_display}
                        </span>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                          b.nivel_atencion === 'critico' ? 'bg-rose-100 text-rose-700' :
                          b.nivel_atencion === 'alto' ? 'bg-orange-100 text-orange-700' :
                          'bg-slate-100 text-slate-700'
                        }`}>
                          {b.nivel_atencion_display}
                        </span>
                      </div>
                      <p className="text-sm font-medium text-slate-800 line-clamp-1">
                        {b.descripcion_automatica || b.descripcion_complementaria || 'Sin descripción'}
                      </p>
                      {b.trabajador_nombre && (
                        <p className="text-xs text-slate-500">
                          Trabajador: <span className="font-medium text-slate-700">{b.trabajador_nombre}</span>
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`text-xs font-semibold px-2.5 py-1 rounded-md capitalize ${
                        b.estado === 'abierta' ? 'bg-rose-50 text-rose-600 border border-rose-200' :
                        b.estado === 'subsanada' ? 'bg-emerald-50 text-emerald-600 border border-emerald-200' :
                        'bg-amber-50 text-amber-600 border border-amber-200'
                      }`}>
                        {b.estado_display}
                      </span>
                      <ArrowRight className="w-4 h-4 text-slate-300" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Detail Panel */}
        {selectedBrecha && (
          <div className="lg:col-span-1 space-y-4">
            <Card className="p-5 space-y-4 border-slate-200 shadow-md">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div>
                  <span className="font-mono text-sm font-bold text-primary-500">{selectedBrecha.codigo}</span>
                  <p className="text-xs text-slate-400 mt-0.5">Detectado: {selectedBrecha.fecha_deteccion}</p>
                </div>
                <button
                  onClick={() => setSelectedBrecha(null)}
                  className="text-xs text-slate-400 hover:text-slate-600 font-medium"
                >
                  Cerrar
                </button>
              </div>

              {/* IA Diagnosis */}
              {selectedBrecha.recomendacion_ia && (
                <div className="p-3.5 bg-gradient-to-br from-slate-50 to-primary-50/40 rounded-xl border border-primary-100 space-y-1.5">
                  <div className="flex items-center gap-1.5 text-primary-500 font-semibold text-xs">
                    <Sparkles className="w-3.5 h-3.5" />
                    Recomendación Inteligente (IA)
                  </div>
                  <p className="text-xs text-slate-800 leading-relaxed">
                    {selectedBrecha.recomendacion_ia}
                  </p>
                </div>
              )}

              {/* Description */}
              <div className="space-y-1">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Descripción del Hallazgo</span>
                <p className="text-xs text-slate-700 bg-slate-50 p-2.5 rounded-md border border-slate-100 leading-relaxed">
                  {selectedBrecha.descripcion_automatica}
                </p>
              </div>

              {/* Timeline of Events */}
              {selectedBrecha.eventos && selectedBrecha.eventos.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-slate-100">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Línea de Vida (Eventos)</span>
                  <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                    {selectedBrecha.eventos.map((ev) => (
                      <div key={ev.id} className="text-xs p-2 rounded bg-slate-50 border border-slate-100">
                        <div className="flex items-center justify-between text-slate-500">
                          <span className="font-semibold text-slate-700 capitalize">{ev.tipo_evento_display}</span>
                          <span className="text-[10px]">{new Date(ev.created_at).toLocaleDateString()}</span>
                        </div>
                        <p className="text-slate-600 mt-1">{ev.descripcion}</p>
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
