import { useState, useEffect } from 'react'
import { Modal, FormField, Input, Select, Textarea } from '@/components/ui/forms'
import { Button } from '@/components/ui'
import { formacionService, CursoFormacion } from '@/services/formacion.service'
import { Award, Calendar, FileText, CheckCircle2 } from 'lucide-react'

interface Props {
  isOpen: boolean
  onClose: () => void
  trabajadorId: string
  trabajadorNombre: string
  preselectedCursoId?: string
  onSuccess: () => void
}

export function RegistrarCursoModal({
  isOpen,
  onClose,
  trabajadorId,
  trabajadorNombre,
  preselectedCursoId,
  onSuccess,
}: Props) {
  const [cursos, setCursos] = useState<CursoFormacion[]>([])
  const [cursoId, setCursoId] = useState(preselectedCursoId || '')
  const [fechaRealizacion, setFechaRealizacion] = useState(new Date().toISOString().split('T')[0])
  const [fechaVencimiento, setFechaVencimiento] = useState('')
  const [origen, setOrigen] = useState<'capacitacion_interna' | 'proveedor_externo' | 'carga_manual'>('proveedor_externo')
  const [entidadEmisora, setEntidadEmisora] = useState('')
  const [horasDuracion, setHorasDuracion] = useState<string>('')
  const [soporteUrl, setSoporteUrl] = useState('')
  const [observaciones, setObservaciones] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      formacionService.getCursos().then(res => {
        const data = Array.isArray(res) ? res : ((res as any)?.results || [])
        setCursos(data)
      }).catch(console.error)
    }
  }, [isOpen])

  useEffect(() => {
    if (preselectedCursoId) {
      setCursoId(preselectedCursoId)
    }
  }, [preselectedCursoId])

  // Cálculo automático de la fecha de vencimiento
  useEffect(() => {
    if (!cursoId || !fechaRealizacion) return
    const selCurso = cursos.find(c => c.id === cursoId)
    if (selCurso && selCurso.vigencia_meses) {
      try {
        const [year, month, day] = fechaRealizacion.split('-').map(Number)
        const d = new Date(year, month - 1, day)
        d.setMonth(d.getMonth() + selCurso.vigencia_meses)
        const yStr = d.getFullYear()
        const mStr = String(d.getMonth() + 1).padStart(2, '0')
        const dStr = String(d.getDate()).padStart(2, '0')
        setFechaVencimiento(`${yStr}-${mStr}-${dStr}`)
      } catch {
        // mantener valor actual
      }
    } else if (selCurso && !selCurso.vigencia_meses) {
      setFechaVencimiento('')
    }
  }, [cursoId, fechaRealizacion, cursos])

  const selectedCurso = cursos.find(c => c.id === cursoId)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg(null)
    if (!cursoId) {
      setErrorMsg('Seleccione un curso del catálogo.')
      return
    }
    if (!fechaRealizacion) {
      setErrorMsg('La fecha de realización es obligatoria.')
      return
    }

    setSubmitting(true)
    try {
      await formacionService.createRegistro({
        trabajador: trabajadorId,
        curso: cursoId,
        fecha_realizacion: fechaRealizacion,
        fecha_vencimiento: fechaVencimiento || null,
        origen,
        entidad_emisora: entidadEmisora.trim() || undefined,
        horas_duracion: horasDuracion ? parseInt(horasDuracion) : null,
        observaciones: observaciones.trim() || undefined,
      })
      onSuccess()
      onClose()
    } catch (err: any) {
      setErrorMsg(err.message || 'Error al registrar la formación.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal
      open={isOpen}
      onClose={onClose}
      title="Registrar Certificado o Curso de Formación"
      maxWidth="600px"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs">
          <span className="text-slate-500">Trabajador:</span>{' '}
          <strong className="text-slate-900">{trabajadorNombre}</strong>
        </div>

        {errorMsg && (
          <div className="p-3 bg-rose-50 text-rose-700 text-xs rounded-lg border border-rose-200">
            {errorMsg}
          </div>
        )}

        {/* Selección de Curso */}
        <FormField label="Curso o Certificación del Catálogo">
          <select
            value={cursoId}
            onChange={(e) => setCursoId(e.target.value)}
            className="w-full text-xs rounded-lg border-slate-200 py-2 px-3 text-slate-800 focus:ring-brand-500 focus:border-brand-500"
            required
          >
            <option value="">Seleccione el curso realizado...</option>
            {cursos.map(c => (
              <option key={c.id} value={c.id}>
                {c.nombre} ({c.categoria_display || c.categoria.toUpperCase()}) {c.vigencia_meses ? `· Vigencia: ${c.vigencia_meses} meses` : '· Sin vencimiento'}
              </option>
            ))}
          </select>
        </FormField>

        {/* Fechas de Realización y Vencimiento Calculada */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <FormField label="Fecha de Realización / Aprobación">
            <Input
              type="date"
              value={fechaRealizacion}
              onChange={(e) => setFechaRealizacion(e.target.value)}
              required
            />
          </FormField>

          <FormField 
            label="Fecha de Vencimiento" 
            helperText={selectedCurso?.vigencia_meses ? `Calculada automáticamente (${selectedCurso.vigencia_meses} meses de vigencia)` : 'Este curso no vence periódicamente'}
          >
            <Input
              type="date"
              value={fechaVencimiento}
              onChange={(e) => setFechaVencimiento(e.target.value)}
              placeholder="Sin vencimiento"
            />
          </FormField>
        </div>

        {/* Origen y Entidad Emisora */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <FormField label="Origen de la Formación">
            <select
              value={origen}
              onChange={(e: any) => setOrigen(e.target.value)}
              className="w-full text-xs rounded-lg border-slate-200 py-2 px-3 text-slate-800"
            >
              <option value="capacitacion_interna">Capacitación interna</option>
              <option value="proveedor_externo">Proveedor externo</option>
              <option value="carga_manual">Carga manual de certificado</option>
            </select>
          </FormField>

          <FormField label="Entidad Emisora / Proveedor">
            <Input
              type="text"
              placeholder="Ej: SENA, Cruz Roja, ARL Sura..."
              value={entidadEmisora}
              onChange={(e) => setEntidadEmisora(e.target.value)}
            />
          </FormField>
        </div>

        {/* Horas de Duración y Enlace a Soporte */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <FormField label="Horas de Duración">
            <Input
              type="number"
              min="1"
              placeholder="Ej: 50, 20, 8..."
              value={horasDuracion}
              onChange={(e) => setHorasDuracion(e.target.value)}
            />
          </FormField>

          <FormField label="Enlace / URL de Certificado">
            <Input
              type="url"
              placeholder="https://..."
              value={soporteUrl}
              onChange={(e) => setSoporteUrl(e.target.value)}
            />
          </FormField>
        </div>

        <FormField label="Observaciones (Opcional)">
          <Textarea
            value={observaciones}
            onChange={(e) => setObservaciones(e.target.value)}
            placeholder="Detalles sobre el instructor, número de certificado, etc."
            className="min-h-[60px]"
          />
        </FormField>

        <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
          <Button type="button" variant="ghost" onClick={onClose} disabled={submitting}>
            Cancelar
          </Button>
          <Button type="submit" variant="primary" disabled={submitting}>
            {submitting ? 'Guardando...' : 'Guardar Registro'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
