import { useState, useEffect } from 'react'
import { Card, Button, EmptyState } from '@/components/ui'
import { LoadingSpinner } from '@/components/ui/forms'
import {
  formacionService,
  EvaluacionCompetencia,
  FormacionResumen,
  MatrizTrabajadorResponse,
} from '@/services/formacion.service'
import { gestionHumanaService, Trabajador } from '@/services/gestion-humana.service'
import {
  GraduationCap, Award, TrendingUp, AlertCircle,
  Plus, CheckCircle2, ArrowRight, User
} from 'lucide-react'

export default function FormacionView() {
  const [evaluaciones, setEvaluaciones] = useState<EvaluacionCompetencia[]>([])
  const [resumen, setResumen] = useState<FormacionResumen | null>(null)
  const [trabajadores, setTrabajadores] = useState<Trabajador[]>([])
  const [selectedTrabajadorId, setSelectedTrabajadorId] = useState<string>('')
  const [matrizTrabajador, setMatrizTrabajador] = useState<MatrizTrabajadorResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    cargarDatosIniciales()
  }, [])

  useEffect(() => {
    if (selectedTrabajadorId) {
      cargarMatrizTrabajador(selectedTrabajadorId)
    } else {
      setMatrizTrabajador(null)
    }
  }, [selectedTrabajadorId])

  const cargarDatosIniciales = async () => {
    setLoading(true)
    try {
      const [resEvals, resResumen, resTrabajadores] = await Promise.all([
        formacionService.getEvaluaciones(),
        formacionService.getResumen(),
        gestionHumanaService.getTrabajadores(),
      ])
      setEvaluaciones(Array.isArray(resEvals) ? resEvals : resEvals.results || [])
      setResumen(resResumen)
      setTrabajadores(Array.isArray(resTrabajadores) ? resTrabajadores : resTrabajadores.results || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const cargarMatrizTrabajador = async (id: string) => {
    try {
      const data = await formacionService.getMatrizTrabajador(id)
      setMatrizTrabajador(data)
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
            Formación y Desarrollo — Matriz de Competencias del Cargo (MCC)
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Evaluación de competencias técnicas, blandas y organizacionales vs. requisitos del perfil del cargo.
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      {resumen && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="p-4 border-l-4 border-l-primary-500">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-500">Evaluaciones Totales</span>
              <Award className="w-5 h-5 text-primary-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-2">
              {resumen.total_evaluaciones || 0}
            </div>
          </Card>
          <Card className="p-4 border-l-4 border-l-emerald-500">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-500">Competencias Óptimas</span>
              <CheckCircle2 className="w-5 h-5 text-emerald-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-2">
              {resumen.evaluaciones_optimas || 0}
            </div>
          </Card>
          <Card className="p-4 border-l-4 border-l-amber-500">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-500">Brechas Detectadas</span>
              <AlertCircle className="w-5 h-5 text-amber-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-2">
              {resumen.evaluaciones_con_brecha || 0}
            </div>
          </Card>
          <Card className="p-4 border-l-4 border-l-brand-500">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-500">Brecha Promedio</span>
              <TrendingUp className="w-5 h-5 text-brand-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-2">
              {resumen.promedio_brecha} niveles
            </div>
          </Card>
        </div>
      )}

      {/* Worker Competency Matrix Filter */}
      <Card className="p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <User className="w-4 h-4 text-primary-500" />
            <h3 className="text-sm font-bold text-slate-900">Consultar Matriz por Trabajador:</h3>
          </div>
          <select
            value={selectedTrabajadorId}
            onChange={(e) => setSelectedTrabajadorId(e.target.value)}
            className="text-xs rounded-md border-slate-200 py-1.5 px-3 text-slate-700 focus:ring-brand-500 focus:border-brand-500 w-full sm:w-72"
          >
            <option value="">Seleccionar trabajador...</option>
            {trabajadores.map((t) => (
              <option key={t.id} value={t.id}>
                {t.nombre} ({t.cargo || 'Sin cargo'})
              </option>
            ))}
          </select>
        </div>

        {matrizTrabajador && (
          <div className="pt-4 border-t border-slate-100 space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>Trabajador: <strong className="text-slate-800">{matrizTrabajador.trabajador.nombre}</strong></span>
              <span>Cargo: <strong className="text-slate-800">{matrizTrabajador.trabajador.cargo}</strong></span>
            </div>

            <div className="divide-y divide-slate-100">
              {matrizTrabajador.competencias.length === 0 ? (
                <EmptyState title="Sin competencias" description="No hay competencias registradas para este trabajador." />
              ) : (
                matrizTrabajador.competencias.map((c) => (
                  <div key={c.competencia_id} className="py-3 flex items-center justify-between">
                    <div className="space-y-0.5">
                      <span className="text-xs font-semibold text-slate-900">{c.nombre}</span>
                      <p className="text-[11px] text-slate-400 capitalize">Tipo: {c.tipo}</p>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="text-right text-xs">
                        <span className="text-slate-500">Requerido: <strong>L{c.nivel_requerido}</strong></span>
                        <span className="mx-2 text-slate-300">|</span>
                        <span className="text-slate-700">Alcanzado: <strong>L{c.nivel_alcanzado || 0}</strong></span>
                      </div>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        c.cumple ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                      }`}>
                        {c.cumple ? 'Cumple' : `Brecha: -${c.brecha}`}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </Card>

      {/* Recent Evaluations Table */}
      <Card className="p-4 space-y-3">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <GraduationCap className="w-4 h-4 text-primary-500" />
          Historial de Evaluaciones de Competencia ({evaluaciones.length})
        </h3>

        {loading ? (
          <LoadingSpinner text="Cargando evaluaciones..." />
        ) : evaluaciones.length === 0 ? (
          <EmptyState title="Sin evaluaciones" description="No se registran evaluaciones de competencia." />
        ) : (
          <div className="divide-y divide-slate-100 max-h-96 overflow-y-auto pr-1">
            {evaluaciones.map((ev) => (
              <div key={ev.id} className="p-3 hover:bg-slate-50 transition flex items-center justify-between rounded-lg">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-slate-900">{ev.trabajador_nombre}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">{ev.competencia_nombre}</span>
                  </div>
                  <p className="text-xs text-slate-500">
                    Fecha: {ev.fecha_evaluacion} • Método: {ev.metodo_display}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right text-xs">
                    <span className="text-slate-500">Req: L{ev.nivel_requerido} / Alc: L{ev.nivel_alcanzado}</span>
                  </div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    ev.brecha_calculada === 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
                  }`}>
                    {ev.brecha_calculada === 0 ? 'Óptimo' : `Brecha: -${ev.brecha_calculada}`}
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
