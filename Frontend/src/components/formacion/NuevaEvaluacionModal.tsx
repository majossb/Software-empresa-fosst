import React, { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Modal, FormField, Input, Textarea } from '@/components/ui/forms'
import { Button } from '@/components/ui'
import { formacionService } from '@/services/formacion.service'
import { modulo1Service, PerfilCargoDetail, CargoCompetencia } from '@/services/modulo1.service'
import { Trabajador } from '@/services/gestion-humana.service'
import {
  Award, Calendar, FileText, CheckCircle2,
  AlertTriangle, BookOpen, User, ShieldCheck, Zap
} from 'lucide-react'

interface Props {
  isOpen: boolean
  onClose: () => void
  trabajadores: Trabajador[]
  preselectedTrabajadorId?: string
  preselectedCompetenciaId?: string
  onSuccess: () => void
}

const NIVELES = [
  { valor: 1, nombre: 'Básico' },
  { valor: 2, nombre: 'En desarrollo' },
  { valor: 3, nombre: 'Autónomo' },
  { valor: 4, nombre: 'Dominio avanzado' },
  { valor: 5, nombre: 'Referente' },
]

const METODOS = [
  { valor: 'evaluacion_360', label: 'Evaluación 360° / Jefe Directo' },
  { valor: 'observacion_directa', label: 'Observación Directa en Puesto' },
  { valor: 'prueba_tecnica', label: 'Prueba Técnica / Conocimiento' },
  { valor: 'certificacion', label: 'Certificación / Título Acreditado' },
  { valor: 'entrevista', label: 'Entrevista por Competencias' },
  { valor: 'autoevaluacion', label: 'Autoevaluación' },
]

export function NuevaEvaluacionModal({
  isOpen,
  onClose,
  trabajadores,
  preselectedTrabajadorId,
  preselectedCompetenciaId,
  onSuccess,
}: Props) {
  const navigate = useNavigate()

  const [trabajadorId, setTrabajadorId] = useState(preselectedTrabajadorId || '')
  const [competenciasCargo, setCompetenciasCargo] = useState<CargoCompetencia[]>([])
  const [cargoCompetenciaId, setCargoCompetenciaId] = useState(preselectedCompetenciaId || '')
  const [nivelAlcanzado, setNivelAlcanzado] = useState<number>(3)
  const [metodo, setMetodo] = useState('evaluacion_360')
  const [fechaEvaluacion, setFechaEvaluacion] = useState(new Date().toISOString().split('T')[0])
  const [observacion, setObservacion] = useState('')
  const [loadingCompetencias, setLoadingCompetencias] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    if (preselectedTrabajadorId) setTrabajadorId(preselectedTrabajadorId)
  }, [preselectedTrabajadorId])

  useEffect(() => {
    if (preselectedCompetenciaId) setCargoCompetenciaId(preselectedCompetenciaId)
  }, [preselectedCompetenciaId])

  // Cargar las competencias requeridas por el cargo del trabajador seleccionado
  useEffect(() => {
    if (!trabajadorId) {
      setCompetenciasCargo([])
      return
    }
    const t = trabajadores.find((item) => item.id === trabajadorId)
    if (!t || !t.perfil_cargo) {
      setCompetenciasCargo([])
      return
    }

    setLoadingCompetencias(true)
    modulo1Service
      .getPerfil(t.perfil_cargo)
      .then((perfil: PerfilCargoDetail) => {
        setCompetenciasCargo(perfil.competencias || [])
        if (!preselectedCompetenciaId && perfil.competencias?.length) {
          setCargoCompetenciaId(perfil.competencias[0].id || '')
        }
      })
      .catch((e) => {
        console.error('Error cargando competencias del cargo:', e)
        setCompetenciasCargo([])
      })
      .finally(() => setLoadingCompetencias(false))
  }, [trabajadorId, trabajadores, preselectedCompetenciaId])

  // Competencia actual seleccionada
  const competenciaSeleccionada = useMemo(() => {
    return competenciasCargo.find((c) => c.id === cargoCompetenciaId)
  }, [competenciasCargo, cargoCompetenciaId])

  const nivelRequerido = competenciaSeleccionada?.nivel_requerido || (competenciaSeleccionada?.nivel ? parseInt(String(competenciaSeleccionada.nivel), 10) : 3)
  const brechaCalculada = Math.max(0, nivelRequerido - nivelAlcanzado)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!trabajadorId || !cargoCompetenciaId) {
      setErrorMsg('Selecciona el trabajador y la competencia a evaluar.')
      return
    }

    setSubmitting(true)
    setErrorMsg(null)

    try {
      await formacionService.createEvaluacion({
        trabajador: trabajadorId,
        cargo_competencia: cargoCompetenciaId,
        nivel_alcanzado: nivelAlcanzado,
        metodo,
        fecha_evaluacion: fechaEvaluacion,
        observacion: observacion.trim() || undefined,
      })
      onSuccess()
      onClose()
    } catch (err: any) {
      setErrorMsg(err.message || 'Error registrando la evaluación de competencia.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal
      open={isOpen}
      onClose={onClose}
      title="Registrar Evaluación de Competencia"
      maxWidth="600px"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {errorMsg && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Trabajador */}
        <FormField label="Trabajador a Evaluar" required>
          <select
            value={trabajadorId}
            onChange={(e) => {
              setTrabajadorId(e.target.value)
              setCargoCompetenciaId('')
            }}
            disabled={!!preselectedTrabajadorId}
            className="w-full text-xs rounded-xl border border-slate-200 bg-white p-2.5 text-slate-800 focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
          >
            <option value="">Selecciona un colaborador...</option>
            {trabajadores.map((t) => (
              <option key={t.id} value={t.id}>
                {t.nombre} ({t.cargo || 'Sin cargo asignado'})
              </option>
            ))}
          </select>
        </FormField>

        {/* Competencia del Cargo */}
        <FormField
          label="Competencia del Cargo"
          required
          helperText={
            loadingCompetencias
              ? 'Cargando competencias del perfil de cargo...'
              : competenciasCargo.length === 0
              ? 'El cargo del trabajador no tiene competencias registradas.'
              : undefined
          }
        >
          <select
            value={cargoCompetenciaId}
            onChange={(e) => setCargoCompetenciaId(e.target.value)}
            disabled={loadingCompetencias || competenciasCargo.length === 0}
            className="w-full text-xs rounded-xl border border-slate-200 bg-white p-2.5 text-slate-800 focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
          >
            <option value="">Selecciona una competencia...</option>
            {competenciasCargo.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nombre} (Req: Nivel {c.nivel_requerido || c.nivel || 3} - {c.tipo || 'Técnica'})
              </option>
            ))}
          </select>
        </FormField>

        {/* Nivel Alcanzado */}
        <FormField label="Nivel Alcanzado por el Colaborador" required>
          <div className="grid grid-cols-1 sm:grid-cols-5 gap-1.5 pt-1">
            {NIVELES.map((n) => {
              const seleccionado = nivelAlcanzado === n.valor
              return (
                <button
                  type="button"
                  key={n.valor}
                  onClick={() => setNivelAlcanzado(n.valor)}
                  className={`p-2 rounded-xl border text-center transition-all ${
                    seleccionado
                      ? 'bg-primary-50 border-primary-500 ring-2 ring-primary-500/20 text-primary-900 font-bold'
                      : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300'
                  }`}
                >
                  <div className="text-sm font-black font-mono">L{n.valor}</div>
                  <div className="text-[10px] leading-tight truncate">{n.nombre}</div>
                </button>
              )
            })}
          </div>
        </FormField>

        {/* Feedback visual instantáneo de brecha */}
        {competenciaSeleccionada && (
          <div
            className={`p-3 rounded-xl border flex items-center justify-between text-xs ${
              brechaCalculada === 0
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : brechaCalculada === 1
                ? 'bg-amber-50 border-amber-200 text-amber-900'
                : 'bg-rose-50 border-rose-200 text-rose-900'
            }`}
          >
            <div>
              <span className="font-bold">
                Nivel Requerido: L{nivelRequerido} vs Alcanzado: L{nivelAlcanzado}
              </span>
              <p className="text-[11px] mt-0.5">
                {brechaCalculada === 0
                  ? 'Cumple con el nivel esperado para el cargo.'
                  : `Brecha detectada: falta ${brechaCalculada} nivel(es) para alcanzar el estándar.`}
              </p>
            </div>
            {brechaCalculada > 0 && (
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  onClose()
                  navigate(
                    `/app/responsable/capacitaciones?competencia_id=${cargoCompetenciaId}&trabajador_id=${trabajadorId}`
                  )
                }}
                className="text-[11px] py-1 px-2.5 flex items-center gap-1 bg-white border shadow-xs"
              >
                <BookOpen className="w-3.5 h-3.5 text-indigo-600" />
                Programar Capacitación
              </Button>
            )}
          </div>
        )}

        {/* Método y Fecha */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <FormField label="Método de Evaluación" required>
            <select
              value={metodo}
              onChange={(e) => setMetodo(e.target.value)}
              className="w-full text-xs rounded-xl border border-slate-200 bg-white p-2.5 text-slate-800 focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
            >
              {METODOS.map((m) => (
                <option key={m.valor} value={m.valor}>
                  {m.label}
                </option>
              ))}
            </select>
          </FormField>

          <FormField label="Fecha de Evaluación" required>
            <Input
              type="date"
              value={fechaEvaluacion}
              onChange={(e) => setFechaEvaluacion(e.target.value)}
            />
          </FormField>
        </div>

        {/* Observaciones */}
        <FormField label="Observaciones o Comentarios del Evaluador">
          <Textarea
            rows={2}
            placeholder="Detalles del desempeño observado, fortalezas o aspectos a mejorar..."
            value={observacion}
            onChange={(e) => setObservacion(e.target.value)}
          />
        </FormField>

        {/* Acciones */}
        <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
          <Button type="button" variant="secondary" onClick={onClose} disabled={submitting}>
            Cancelar
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={submitting || !trabajadorId || !cargoCompetenciaId}
          >
            {submitting ? 'Guardando...' : 'Guardar Evaluación'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
