import { useState } from 'react'
import { Card, PageHeader, Badge, Button, Alert, EmptyState } from '@/components/ui'
import { LoadingSpinner, ErrorDisplay, Modal, FormField, Input, Textarea, Select } from '@/components/ui/forms'
import { useEvidencias, useCrearEvidencia, useEliminarEvidencia, useDashboardResp } from '@/hooks/useApi'
import { Upload, FileText, Trash2, Plus, ArrowRight, ArrowLeft, CheckCircle2, ShieldCheck, AlertTriangle } from 'lucide-react'

export default function EvidenciasView() {
  const { data, isLoading, error, refetch } = useEvidencias()
  const crearMut = useCrearEvidencia()
  const elimMut = useEliminarEvidencia()
  const [modalOpen, setModalOpen] = useState(false)
  const [step, setStep] = useState<1 | 2>(1)
  const { data: dashData } = useDashboardResp()
  
  const opcionesRespuesta = [
    { value: '', label: '-- Seleccione el estándar a respaldar --' },
    ...(dashData?.estandares
      ?.filter((e: any) => e.respuesta_id)
      ?.map((e: any) => ({
        value: String(e.respuesta_id),
        label: `${e.codigo} - ${e.nombre}`
      })) || [])
  ]
  
  const [form, setForm] = useState({
    respuesta_id: '',
    nombre: '',
    descripcion: '',
    fecha_ocurrencia: '',
    responsable: '',
    firma_nombre: '',
    firma_cargo: ''
  })
  const [file, setFile] = useState<File | null>(null)
  const [fileError, setFileError] = useState<string | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null)

  if (isLoading) return <LoadingSpinner text="Cargando evidencias..." />
  if (error || !data) return <ErrorDisplay message={(error as Error)?.message ?? 'Error'} onRetry={refetch} />

  const { evidencias, total } = data

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    setFileError(null)
    if (!f) {
      setFile(null)
      return
    }
    const MAX_SIZE = 10 * 1024 * 1024 // 10MB
    if (f.size > MAX_SIZE) {
      setFileError('El archivo excede el tamaño máximo permitido de 10MB.')
      e.target.value = ''
      setFile(null)
      return
    }
    setFile(f)
  }

  const handleCrear = async () => {
    if (!form.nombre.trim() || !form.respuesta_id.trim() || !file) return
    setSubmitError(null)

    const formData = new FormData()
    formData.append('respuesta_id', form.respuesta_id)
    formData.append('nombre', form.nombre.trim())
    if (form.descripcion.trim()) formData.append('descripcion', form.descripcion.trim())
    if (form.fecha_ocurrencia) formData.append('fecha_ocurrencia', form.fecha_ocurrencia)
    if (form.responsable.trim()) formData.append('responsable', form.responsable.trim())
    if (form.firma_nombre.trim() && form.firma_cargo.trim()) {
      formData.append('firma', `${form.firma_nombre.trim()} - ${form.firma_cargo.trim()}`)
    }
    formData.append('archivo', file)

    try {
      // @ts-ignore: mutation accept parameter depends on useApi.ts definition
      await crearMut.mutateAsync(formData)
      setModalOpen(false)
      setStep(1)
      setForm({ respuesta_id: '', nombre: '', descripcion: '', fecha_ocurrencia: '', responsable: '', firma_nombre: '', firma_cargo: '' })
      setFile(null)
      
      setSubmitSuccess('¡Evidencia subida y vinculada correctamente!')
      setTimeout(() => setSubmitSuccess(null), 5000)
    } catch (err: any) {
      setSubmitError(err.message || 'Error desconocido al subir la evidencia.')
    }
  }

  const isStep1Valid = form.respuesta_id && form.nombre.trim() && file && !fileError

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        title="Cargar Evidencias"
        subtitle={`${total} evidencias cargadas para la evaluación actual`}
        actions={
          <Button variant="primary" icon={Plus} className="text-xs" onClick={() => { setSubmitError(null); setModalOpen(true); setStep(1) }}>
            Cargar evidencia
          </Button>
        }
      />

      {submitSuccess && (
        <Alert variant="success" title="Operación exitosa">
          {submitSuccess}
        </Alert>
      )}

      {evidencias.length === 0 ? (
        <EmptyState
          icon={Upload}
          title="Sin evidencias cargadas"
          description="Cargue evidencias para respaldar el cumplimiento de los estándares mínimos del SG-SST."
          action={
            <Button variant="primary" icon={Plus} className="text-xs" onClick={() => { setSubmitError(null); setModalOpen(true); setStep(1) }}>
              Cargar primera evidencia
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {evidencias.map((ev) => (
            <Card key={ev.id}>
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-primary-500 flex-shrink-0">
                  <FileText className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-bold text-primary-500 truncate">{ev.archivo?.nombre ?? 'Sin nombre'}</div>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="blue">{ev.estandar_codigo}</Badge>
                    <span className="text-xs text-slate-500 truncate font-medium">{ev.estandar_nombre}</span>
                  </div>
                  {ev.descripcion && <div className="text-xs text-slate-600 mt-1">{ev.descripcion}</div>}
                  {ev.responsable && <div className="text-xs text-slate-500 mt-1 font-medium">Resp: {ev.responsable}</div>}
                  {ev.firma && (
                    <div className="flex items-center gap-1 text-[11px] text-emerald-700 font-semibold mt-1">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      <span>Firmado por: {ev.firma}</span>
                    </div>
                  )}
                  <div className="text-[10px] text-slate-400 mt-1">
                    {ev.fecha_ocurrencia ? `Generado el: ${new Date(ev.fecha_ocurrencia).toLocaleDateString()}` : `Subido el: ${new Date(ev.created_at).toLocaleString('es-CO')}`}
                  </div>
                </div>
                <button
                  onClick={() => elimMut.mutate(ev.id)}
                  className="p-1 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors flex-shrink-0"
                  title="Eliminar evidencia"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Cargar Evidencia Directa" footer={
        <>
          {step === 1 ? (
            <>
              <Button variant="ghost" onClick={() => setModalOpen(false)}>Cancelar</Button>
              <Button variant="primary" icon={ArrowRight} onClick={() => setStep(2)} disabled={!isStep1Valid}>
                Siguiente
              </Button>
            </>
          ) : (
            <>
              <Button variant="ghost" icon={ArrowLeft} onClick={() => setStep(1)}>Volver</Button>
              <Button variant="primary" icon={CheckCircle2} onClick={handleCrear} disabled={crearMut.isPending}>
                {crearMut.isPending ? 'Subiendo...' : 'Confirmar y Subir'}
              </Button>
            </>
          )}
        </>
      }>
        {step === 1 ? (
          <div className="space-y-4">
            <FormField label="Estándar Asociado" required>
              <Select
                value={form.respuesta_id}
                onChange={(e) => setForm({ ...form, respuesta_id: e.target.value })}
                options={opcionesRespuesta}
              />
            </FormField>
            
            <FormField label="Nombre del Documento" required>
              <Input
                value={form.nombre}
                onChange={(e) => setForm({ ...form, nombre: e.target.value })}
                placeholder="Ej: Acta COPASST - Sesión Ordinaria"
              />
            </FormField>
            
            <FormField label="Archivo de Soporte (PDF o Imagen)" error={fileError || undefined} required helperText="Formatos admitidos: PDF, JPG, PNG, DOCX, XLSX (máx. 10MB)">
              <Input 
                type="file" 
                accept="image/*, application/pdf, .doc, .docx, .xls, .xlsx"
                onChange={handleFileChange}
                className="cursor-pointer file:mr-4 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-bold file:bg-primary-50 file:text-primary-500 hover:file:bg-primary-100"
              />
            </FormField>
            
            <FormField label="Descripción / Observaciones">
              <Textarea
                value={form.descripcion}
                onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
                placeholder="Contexto o notas adicionales sobre la evidencia cargada"
              />
            </FormField>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField label="Fecha de Generación / Ocurrencia">
                <Input
                  type="date"
                  max={new Date().toISOString().split('T')[0]}
                  value={form.fecha_ocurrencia}
                  onChange={(e) => setForm({ ...form, fecha_ocurrencia: e.target.value })}
                />
              </FormField>
              <FormField label="Persona Responsable">
                <Input
                  value={form.responsable}
                  onChange={(e) => setForm({ ...form, responsable: e.target.value })}
                  placeholder="Nombre del responsable"
                />
              </FormField>
            </div>

            <div className="p-4 border border-slate-200 rounded-xl bg-slate-50 space-y-3">
              <h4 className="text-xs font-bold text-primary-500 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4" />
                Rúbrica Digital (Firma de Responsable)
              </h4>
              <p className="text-[11px] text-slate-500">Opcional: Si desea respaldar la evidencia con firma digital en texto:</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <FormField label="Nombre Completo" className="mb-0">
                  <Input
                    value={form.firma_nombre}
                    onChange={(e) => setForm({ ...form, firma_nombre: e.target.value })}
                    placeholder="Nombre del firmante"
                  />
                </FormField>
                <FormField label="Cargo del Firmante" className="mb-0">
                  <Input
                    value={form.firma_cargo}
                    onChange={(e) => setForm({ ...form, firma_cargo: e.target.value })}
                    placeholder="Ej. Coordinador SST"
                  />
                </FormField>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <h4 className="text-primary-500 font-bold text-sm text-center">Resumen de la Evidencia a Subir</h4>
            <div className="bg-slate-50 rounded-xl p-4 space-y-2.5 text-xs border border-slate-200">
              <p><span className="text-slate-500 font-medium">Estándar:</span> <span className="text-primary-500 font-bold ml-1">{opcionesRespuesta.find((o: any) => o.value === form.respuesta_id)?.label || form.respuesta_id}</span></p>
              <p><span className="text-slate-500 font-medium">Archivo:</span> <span className="text-primary-500 font-semibold ml-1">{file?.name}</span> ({Math.round((file?.size || 0)/1024)} KB)</p>
              <p><span className="text-slate-500 font-medium">Nombre:</span> <span className="text-slate-800 font-semibold ml-1">{form.nombre}</span></p>
              {form.descripcion && <p><span className="text-slate-500 font-medium">Descripción:</span> <span className="text-slate-700 ml-1">{form.descripcion}</span></p>}
              {form.fecha_ocurrencia && <p><span className="text-slate-500 font-medium">Fecha:</span> <span className="text-slate-700 ml-1">{form.fecha_ocurrencia}</span></p>}
              {form.responsable && <p><span className="text-slate-500 font-medium">Responsable:</span> <span className="text-slate-700 ml-1">{form.responsable}</span></p>}
              
              {(form.firma_nombre && form.firma_cargo) ? (
                <div className="mt-3 p-3 border border-emerald-200 bg-emerald-50 rounded-lg flex items-center gap-2 text-emerald-800 font-semibold text-xs">
                  <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                  <span>Firmado digitalmente por: {form.firma_nombre} ({form.firma_cargo})</span>
                </div>
              ) : (
                <div className="mt-2 text-[11px] text-amber-800 flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
                  <span>Se enviará sin firma digital vinculada.</span>
                </div>
              )}
            </div>

            {submitError && (
              <Alert variant="danger" title="Error al procesar evidencia">
                {submitError}
              </Alert>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
