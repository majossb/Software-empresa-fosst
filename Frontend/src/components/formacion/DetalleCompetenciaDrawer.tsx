import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui'
import { EvaluacionCompetencia, CompetenciaMatriz } from '@/services/formacion.service'
import {
  X, Award, Calendar, CheckCircle2, AlertTriangle,
  User, BookOpen, Clock, ShieldCheck, ArrowRight
} from 'lucide-react'

interface Props {
  isOpen: boolean
  onClose: () => void
  trabajador: {
    id: string
    nombre: string
    documento?: string
    cargo?: string
  } | null
  competencia: CompetenciaMatriz | null
  historialEvaluaciones: EvaluacionCompetencia[]
  onAbrirEvaluar: () => void
}

export function DetalleCompetenciaDrawer({
  isOpen,
  onClose,
  trabajador,
  competencia,
  historialEvaluaciones,
  onAbrirEvaluar,
}: Props) {
  const navigate = useNavigate()

  if (!isOpen || !trabajador || !competencia) return null

  const cumple = competencia.cumple
  const brecha = competencia.brecha || 0
  const req = competencia.nivel_requerido
  const alc = competencia.nivel_alcanzado

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/50 backdrop-blur-xs flex justify-end">
      <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col transform transition-all duration-300">
        {/* Header */}
        <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div>
            <span className="text-[10px] font-bold text-primary-600 uppercase tracking-wider">
              Detalle de Competencia
            </span>
            <h3 className="text-sm font-bold text-slate-900 leading-tight">
              {competencia.nombre}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Trabajador */}
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
            <div className="text-[11px] font-bold text-slate-500 uppercase">Colaborador</div>
            <div className="font-bold text-sm text-slate-900 mt-0.5">{trabajador.nombre}</div>
            <div className="text-xs text-slate-500">
              {trabajador.cargo || 'Sin cargo asignado'}
              {trabajador.documento ? ` · Doc: ${trabajador.documento}` : ''}
            </div>
          </div>

          {/* Estado de Cumplimiento */}
          <div
            className={`p-4 rounded-xl border space-y-2 ${
              cumple
                ? 'bg-emerald-50/70 border-emerald-200 text-emerald-900'
                : brecha === 1
                ? 'bg-amber-50/70 border-amber-200 text-amber-900'
                : 'bg-rose-50/70 border-rose-200 text-rose-900'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase">Estado de la Competencia</span>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  cumple
                    ? 'bg-emerald-200 text-emerald-900'
                    : brecha === 1
                    ? 'bg-amber-200 text-amber-900'
                    : 'bg-rose-200 text-rose-900'
                }`}
              >
                {cumple ? 'Cumple / Supera' : `Brecha de ${brecha} nivel(es)`}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-200/40 text-center">
              <div>
                <span className="text-[10px] text-slate-500 uppercase font-medium">Requerido</span>
                <div className="text-lg font-black font-mono">
                  L{req} <span className="text-xs font-normal">({competencia.nivel_requerido_nombre || 'Nivel'})</span>
                </div>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase font-medium">Alcanzado</span>
                <div className="text-lg font-black font-mono">
                  {alc > 0 ? `L${alc}` : 'S/E'}{' '}
                  <span className="text-xs font-normal">
                    ({competencia.nivel_alcanzado_nombre || (alc > 0 ? 'Nivel' : 'Sin evaluar')})
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Descripción si existe */}
          {competencia.descripcion && (
            <div className="text-xs text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-200/80">
              <span className="font-bold text-slate-700 block mb-1">Definición de la competencia:</span>
              <p className="leading-relaxed">{competencia.descripcion}</p>
            </div>
          )}

          {/* Historial de Evaluaciones */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-primary-500" />
                Historial de Evaluaciones ({historialEvaluaciones.length})
              </h4>
            </div>

            {historialEvaluaciones.length === 0 ? (
              <div className="p-4 rounded-xl border border-dashed border-slate-200 text-center text-xs text-slate-500">
                No hay evaluaciones registradas para este colaborador en esta competencia.
              </div>
            ) : (
              <div className="space-y-2">
                {historialEvaluaciones.map((evalItem) => (
                  <div
                    key={evalItem.id}
                    className="p-3 rounded-xl border border-slate-200 bg-white shadow-xs space-y-1.5 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900">
                        Nivel L{evalItem.nivel_alcanzado} ({evalItem.nivel_alcanzado_nombre || 'Nivel'})
                      </span>
                      <span className="text-[11px] text-slate-400 font-mono">
                        {evalItem.fecha_evaluacion}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-500 flex items-center justify-between">
                      <span>Método: {evalItem.metodo_display || evalItem.metodo}</span>
                      <span className="capitalize font-medium text-slate-600">
                        {evalItem.rol_evaluador_display || evalItem.rol_evaluador || 'Gestión Humana'}
                      </span>
                    </div>
                    {evalItem.observacion && (
                      <p className="text-[11px] text-slate-600 italic bg-slate-50 p-2 rounded-lg border border-slate-100">
                        "{evalItem.observacion}"
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center gap-2">
          {brecha > 0 && (
            <Button
              variant="secondary"
              onClick={() => {
                onClose()
                navigate(
                  `/app/responsable/capacitaciones?competencia_id=${competencia.competencia_id}&trabajador_id=${trabajador.id}`
                )
              }}
              className="flex-1 text-xs py-2 flex items-center justify-center gap-1.5"
            >
              <BookOpen className="w-3.5 h-3.5 text-indigo-600" />
              Capacitar
            </Button>
          )}
          <Button
            variant="primary"
            onClick={() => {
              onClose()
              onAbrirEvaluar()
            }}
            className="flex-1 text-xs py-2 flex items-center justify-center gap-1.5"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            Evaluar Ahora
          </Button>
        </div>
      </div>
    </div>
  )
}
