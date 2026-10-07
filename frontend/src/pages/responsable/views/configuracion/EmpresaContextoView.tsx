import { useState, useEffect, useRef, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { modulo0Service, EmpresaContexto } from '@/services/modulo0.service'
import { resolveMediaUrl } from '@/services/api.client'
import { Card, Button, Badge } from '@/components/ui'
import { FormField, Input, Select, LoadingSpinner, ErrorDisplay } from '@/components/ui/forms'
import { Camera, Check, Loader2, AlertCircle, Building2, Sparkles, BookOpen, X, Cpu, ImageOff, ShieldAlert, ArrowRight } from 'lucide-react'


type SaveStatus = 'idle' | 'saving' | 'saved' | 'error'

const NIVEL_RIESGO_OPTIONS = [
  { value: '1', label: 'I — Riesgo Mínimo' },
  { value: '2', label: 'II — Riesgo Bajo' },
  { value: '3', label: 'III — Riesgo Medio' },
  { value: '4', label: 'IV — Riesgo Alto' },
  { value: '5', label: 'V — Riesgo Máximo' },
]

const SECTOR_OPTIONS = [
  { value: '', label: 'Seleccionar sector…' },
  { value: 'agricultura', label: 'Agricultura' },
  { value: 'comercio', label: 'Comercio' },
  { value: 'construccion', label: 'Construcción' },
  { value: 'educacion', label: 'Educación' },
  { value: 'financiero', label: 'Financiero' },
  { value: 'industria', label: 'Industria' },
  { value: 'mineria', label: 'Minería' },
  { value: 'salud', label: 'Salud' },
  { value: 'servicios', label: 'Servicios' },
  { value: 'tecnologia', label: 'Tecnología' },
  { value: 'transporte', label: 'Transporte' },
  { value: 'otro', label: 'Otro' },
]

export default function EmpresaContextoView() {
  const queryClient = useQueryClient()

  const { data: empresa, isLoading, error, refetch } = useQuery({
    queryKey: ['modulo0', 'contexto'],
    queryFn: modulo0Service.getContexto,
  })

  const [form, setForm] = useState<Partial<EmpresaContexto>>({})
  const [status, setStatus] = useState<SaveStatus>('idle')
  const debounceRef = useRef<ReturnType<typeof setTimeout>>()

  // Estados para Autocompletado Automático
  const [autoSuggested, setAutoSuggested] = useState(false)
  const [isAutoSuggesting, setIsAutoSuggesting] = useState(false)
  const [mostrarAdvertenciaContexto, setMostrarAdvertenciaContexto] = useState(false)

  // Estados para Modal de Sugerencia CIIU
  const [sugerirModalOpen, setSugerirModalOpen] = useState(false)
  const [descLibre, setDescLibre] = useState('')
  const [sugerenciaResult, setSugerenciaResult] = useState<any>(null)
  const [isSugerirPending, setIsSugerirPending] = useState(false)
  const [sugerirError, setSugerirError] = useState('')

  // Estados para Modal de Descripción CIIU
  const [descModalOpen, setDescModalOpen] = useState(false)
  const [descResult, setDescResult] = useState<any>(null)
  const [isDescPending, setIsDescPending] = useState(false)
  const [descError, setDescError] = useState('')

  // Estados para Logo
  const [logoPreviewUrl, setLogoPreviewUrl] = useState<string | null>(null)
  const [logoError, setLogoError] = useState('')

  // Estados para RF-USR-03: Transición de Capítulo
  const [transicionModalData, setTransicionModalData] = useState<{
    capitulo_anterior: string
    capitulo_nuevo: string
    num_trabajadores: number
    nivel_riesgo: number
  } | null>(null)
  const [motivoTransicion, setMotivoTransicion] = useState('')
  const [isConfirmingTransicion, setIsConfirmingTransicion] = useState(false)
  const [transicionError, setTransicionError] = useState('')

  // Constantes de validación de logo
  const LOGO_ACCEPTED_TYPES = ['image/png', 'image/jpeg', 'image/webp']
  const LOGO_ACCEPTED_EXTENSIONS = '.png,.jpg,.jpeg,.webp'
  const LOGO_MAX_SIZE_MB = 2
  const LOGO_MAX_SIZE_BYTES = LOGO_MAX_SIZE_MB * 1024 * 1024

  // Sincronizar datos del servidor al form
  useEffect(() => {
    if (empresa) {
      setForm({
        ciiu_codigo: empresa.ciiu_codigo,
        ciiu_descripcion: empresa.ciiu_descripcion,
        ciiu_768_principal: empresa.ciiu_768_principal,
        ciiu_768_secundarios: empresa.ciiu_768_secundarios,
        ciiu_768_metadata: empresa.ciiu_768_metadata,
        representante_legal: empresa.representante_legal,
        arl: empresa.arl,
        sector_economico: empresa.sector_economico,
        ciudad: empresa.ciudad,
        num_trabajadores: empresa.num_trabajadores,
        nivel_riesgo: empresa.nivel_riesgo,
      })
      // Si ya hay metadata y contenía falta_contexto, mostrar la advertencia
      if (empresa.ciiu_768_metadata?.falta_contexto) {
        setMostrarAdvertenciaContexto(true)
      }
    }
  }, [empresa])

  // Limpiar URL de vista previa en unmount
  useEffect(() => {
    return () => {
      if (logoPreviewUrl) {
        URL.revokeObjectURL(logoPreviewUrl)
      }
    }
  }, [logoPreviewUrl])

  // URL activa para mostrar en el componente de logo
  const displayLogo = logoPreviewUrl || (empresa?.logo_url ? resolveMediaUrl(empresa.logo_url) : null)

  const triggerAutoSuggestion = async (sectorVal?: string, riesgoVal?: number) => {
    if (!empresa) return
    const targetSector = sectorVal !== undefined ? sectorVal : form.sector_economico
    const targetRiesgo = riesgoVal !== undefined ? riesgoVal : form.nivel_riesgo
    
    if (!targetSector) return

    setIsAutoSuggesting(true)
    setMostrarAdvertenciaContexto(false)
    try {
      const response = await modulo0Service.sugerirCiiuIA(undefined, targetSector, targetRiesgo)
      if (response && response.resultado) {
        const principal = response.resultado.actividad_principal
        const secundarias = (response.resultado.actividades_secundarias || []).map((s: any) => s.codigo_768)

        const updated = {
          ...form,
          sector_economico: targetSector,
          nivel_riesgo: targetRiesgo || principal.clase_riesgo,
          ciiu_codigo: principal.ciiu_rev4,
          ciiu_descripcion: principal.descripcion,
          ciiu_768_principal: principal.codigo_768,
          ciiu_768_secundarios: secundarias,
          ciiu_768_metadata: response,
        }

        setForm(updated)
        saveMutation.mutate(updated)
        setMostrarAdvertenciaContexto(!!response.falta_contexto)
      }
    } catch (err) {
      console.error('Error al sugerir CIIU automáticamente:', err)
    } finally {
      setIsAutoSuggesting(false)
    }
  }

  const saveMutation = useMutation({
    mutationFn: (data: Partial<EmpresaContexto>) => modulo0Service.updateContexto(data),
    onMutate: () => setStatus('saving'),
    onSuccess: () => {
      setStatus('saved')
      queryClient.invalidateQueries({ queryKey: ['modulo0'] })
      setTimeout(() => setStatus('idle'), 2500)
    },
    onError: (err: any) => {
      if (err?.code === 'CHAPTER_CHANGE_REQUIRES_CONFIRMATION' && err?.data) {
        setTransicionModalData(err.data)
        setStatus('idle')
        return
      }
      setStatus('error')
      setTimeout(() => setStatus('idle'), 3000)
    },
  })


  const logoMutation = useMutation({
    mutationFn: (file: File) => modulo0Service.uploadLogo(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modulo0', 'contexto'] })
      // Clear local preview — the server URL from the refetch will be used
      if (logoPreviewUrl) {
        URL.revokeObjectURL(logoPreviewUrl)
      }
      setLogoPreviewUrl(null)
      setLogoError('')
    },
    onError: (err: Error) => {
      // Revert preview on upload failure
      if (logoPreviewUrl) {
        URL.revokeObjectURL(logoPreviewUrl)
      }
      setLogoPreviewUrl(null)
      setLogoError(err.message || 'Error al subir el logotipo.')
    },
  })

  // Auto-save con debounce
  const scheduleAutoSave = useCallback(
    (updated: Partial<EmpresaContexto>) => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
      debounceRef.current = setTimeout(() => {
        saveMutation.mutate(updated)
      }, 1500)
    },
    [saveMutation]
  )

  const handleChange = (field: keyof EmpresaContexto, value: string | number) => {
    const updated = { ...form, [field]: value }
    setForm(updated)
    scheduleAutoSave(updated)
  }

  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Reset previous error
    setLogoError('')

    // Validate file type
    if (!LOGO_ACCEPTED_TYPES.includes(file.type)) {
      setLogoError('Formato no válido. Solo se admiten PNG, JPG/JPEG o WebP.')
      e.target.value = ''
      return
    }

    // Validate file size
    if (file.size > LOGO_MAX_SIZE_BYTES) {
      setLogoError(`La imagen excede el límite de ${LOGO_MAX_SIZE_MB}MB.`)
      e.target.value = ''
      return
    }

    // Generate immediate local preview
    if (logoPreviewUrl) {
      URL.revokeObjectURL(logoPreviewUrl)
    }
    const previewUrl = URL.createObjectURL(file)
    setLogoPreviewUrl(previewUrl)

    // Upload to server
    logoMutation.mutate(file)

    // Reset input so the same file can be re-selected if needed
    e.target.value = ''
  }

  const handleSugerirCiiu = async () => {
    setIsSugerirPending(true)
    setSugerirError('')
    try {
      const response = await modulo0Service.sugerirCiiuIA(descLibre)
      setSugerenciaResult(response)
    } catch (err: any) {
      setSugerirError(err.message || 'Error al obtener sugerencias de la IA.')
    } finally {
      setIsSugerirPending(false)
    }
  }

  const handleAplicarSugerencia = (sug: any) => {
    const principal = sug.actividad_principal
    const secundarias = (sug.actividades_secundarias || []).map((s: any) => s.codigo_768)

    const updated = {
      ...form,
      ciiu_codigo: principal.ciiu_rev4,
      ciiu_descripcion: principal.descripcion,
      nivel_riesgo: principal.clase_riesgo,
      ciiu_768_principal: principal.codigo_768,
      ciiu_768_secundarios: secundarias,
      ciiu_768_metadata: sugerenciaResult,
    }

    setForm(updated)
    saveMutation.mutate(updated)
    setSugerirModalOpen(false)
    setSugerenciaResult(null)
    setDescLibre('')
  }

  const handleVerDescripcion = async () => {
    const principalCode = form.ciiu_768_principal
    const secundariasCodes = form.ciiu_768_secundarios || []
    if (!principalCode) return

    setDescModalOpen(true)
    setIsDescPending(true)
    setDescError('')
    try {
      const response = await modulo0Service.describirCiiuIA(principalCode, secundariasCodes)
      setDescResult(response.resultado)
    } catch (err: any) {
      setDescError(err.message || 'Error al obtener la descripción de la IA.')
    } finally {
      setIsDescPending(false)
    }
  }

  const handleConfirmarTransicion = async () => {
    if (!transicionModalData) return
    setIsConfirmingTransicion(true)
    setTransicionError('')
    try {
      await modulo0Service.confirmarTransicionCapitulo({
        num_trabajadores: transicionModalData.num_trabajadores,
        nivel_riesgo: transicionModalData.nivel_riesgo,
        motivo: motivoTransicion,
      })
      setTransicionModalData(null)
      setMotivoTransicion('')
      queryClient.invalidateQueries({ queryKey: ['modulo0'] })
      queryClient.invalidateQueries({ queryKey: ['estandares'] })
      setStatus('saved')
      setTimeout(() => setStatus('idle'), 2500)
    } catch (err: any) {
      setTransicionError(err?.friendlyMessage || err?.message || 'Error al realizar la transición de capítulo.')
    } finally {
      setIsConfirmingTransicion(false)
    }
  }

  const handleCancelarTransicion = () => {
    setTransicionModalData(null)
    setMotivoTransicion('')
    setTransicionError('')
    if (empresa) {
      setForm({
        ...form,
        num_trabajadores: empresa.num_trabajadores,
        nivel_riesgo: empresa.nivel_riesgo,
      })
    }
  }

  const getRiesgoBadge = (clase: number) => {

    switch (clase) {
      case 1: return <Badge variant="green">Clase I (Mínimo)</Badge>
      case 2: return <Badge variant="blue">Clase II (Bajo)</Badge>
      case 3: return <Badge variant="orange">Clase III (Medio)</Badge>
      case 4: return <Badge variant="orange">Clase IV (Alto)</Badge>
      case 5: return <Badge variant="red">Clase V (Máximo)</Badge>
      default: return <Badge variant="gray">Clase {clase}</Badge>
    }
  }

  if (isLoading) return <LoadingSpinner text="Cargando información de la empresa…" />
  if (error) return <ErrorDisplay message={(error as Error).message} onRetry={refetch} />

  return (
    <div className="space-y-6">
      {/* Indicador de estado */}
      <div className="flex justify-end">
        <div
          className={`
            inline-flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-lg
            transition-all duration-300
            ${status === 'saving' ? 'bg-blue-50 text-blue-600 border border-blue-200' : ''}
            ${status === 'saved'  ? 'bg-green-50 text-green-600 border border-green-200' : ''}
            ${status === 'error'  ? 'bg-red-50 text-red-600 border border-red-200' : ''}
            ${status === 'idle'   ? 'opacity-0' : 'opacity-100'}
          `}
        >
          {status === 'saving' && <><Loader2 className="w-3 h-3 animate-spin" /> Guardando…</>}
          {status === 'saved'  && <><Check className="w-3 h-3" /> Guardado</>}
          {status === 'error'  && <><AlertCircle className="w-3 h-3" /> Error al guardar</>}
        </div>
      </div>

      {/* Logo + Info básica */}
      <Card title="Información General" subtitle="Datos principales de la empresa">
        <div className="flex flex-col sm:flex-row gap-6 items-start">
          {/* Logo */}
          <div className="flex-shrink-0 flex flex-col items-center">
            <label className="relative group cursor-pointer block">
              <div
                className={`w-24 h-24 rounded-full overflow-hidden flex items-center justify-center transition-all ${
                  displayLogo
                    ? 'border-2 border-surface-2 bg-white shadow-sm'
                    : 'border-2 border-dashed border-slate-300 bg-slate-50'
                } group-hover:border-brand-500 group-hover:shadow-md`}
              >
                {displayLogo ? (
                  <img
                    src={displayLogo}
                    alt="Logo de la empresa"
                    className="w-full h-full object-cover rounded-full select-none"
                    onError={() => {
                      if (!logoPreviewUrl) {
                        setLogoError('No se pudo cargar la imagen del logo.')
                      }
                    }}
                  />
                ) : (
                  <div className="flex flex-col items-center justify-center text-slate-400 select-none">
                    <Building2 className="w-6 h-6 mb-0.5 text-slate-300 group-hover:text-brand-500 transition-colors" />
                    <span className="text-[11px] font-bold text-slate-400 group-hover:text-brand-600 transition-colors">Logo</span>
                  </div>
                )}
                {/* Overlay al hacer hover */}
                <div className="absolute inset-0 rounded-full bg-black/45 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center text-white backdrop-blur-[1px]">
                  <Camera className="w-5 h-5 mb-0.5" />
                  <span className="text-[9px] font-bold tracking-tight">Cambiar</span>
                </div>
              </div>
              <input
                type="file"
                accept=".png,.jpg,.jpeg,.webp,image/png,image/jpeg,image/webp"
                className="hidden"
                onChange={handleLogoChange}
              />
            </label>
            {logoMutation.isPending && (
              <div className="text-center mt-2 flex items-center justify-center gap-1.5 text-xs text-brand-600 font-semibold">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-brand-500" />
                <span>Guardando...</span>
              </div>
            )}
            {logoError && (
              <p className="text-red-500 text-[10px] font-semibold mt-1.5 max-w-[120px] text-center leading-tight animate-in fade-in duration-150">
                {logoError}
              </p>
            )}
          </div>

          {/* Nombre y NIT (solo lectura) */}
          <div className="flex-1 space-y-1">
            <div className="text-lg font-black text-primary-500">{empresa?.nombre}</div>
            <div className="text-sm text-slate-500">NIT: {empresa?.nit}</div>
            <div className="flex gap-3 mt-3">
              <div className="text-xs bg-surface px-2.5 py-1 rounded-lg text-slate-600 font-semibold">
                {empresa?._count.sedes ?? 0} sedes
              </div>
              <div className="text-xs bg-surface px-2.5 py-1 rounded-lg text-slate-600 font-semibold">
                {empresa?._count.procesos ?? 0} procesos
              </div>
              <div className="text-xs bg-surface px-2.5 py-1 rounded-lg text-slate-600 font-semibold">
                {empresa?._count.organigrama ?? 0} cargos
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Datos CIIU y clasificación */}
      <Card
        title="Clasificación Económica"
        subtitle={
          isAutoSuggesting
            ? "Sugerencia de IA en curso basada en los datos de la empresa..."
            : "Código CIIU, sector y nivel de riesgo"
        }
        action={
          <div className="flex gap-2">
            <Button
              onClick={() => triggerAutoSuggestion()}
              variant="secondary"
              className="text-xs py-1.5 px-3 flex items-center gap-1.5"
              disabled={isAutoSuggesting}
            >
              {isAutoSuggesting ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-brand-500" />
              ) : (
                <Cpu className="w-3.5 h-3.5 text-brand-500" />
              )}
              Generar Automático
            </Button>
            <Button
              onClick={() => {
                setSugerirModalOpen(true)
                setDescLibre(form.ciiu_descripcion || '')
              }}
              variant="secondary"
              className="text-xs py-1.5 px-3 flex items-center gap-1.5"
            >
              <Sparkles className="w-3.5 h-3.5 text-brand-500" />
              Sugerir con IA
            </Button>
            {form.ciiu_768_principal && (
              <Button
                onClick={handleVerDescripcion}
                variant="ghost"
                className="text-xs py-1.5 px-3 flex items-center gap-1.5"
              >
                <BookOpen className="w-3.5 h-3.5" />
                Ver descripción
              </Button>
            )}
          </div>
        }
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
          {mostrarAdvertenciaContexto && (
            <div className="col-span-full mb-4 p-4 bg-amber-50 border border-amber-200 rounded-2xl flex items-start gap-3 text-amber-800 animate-in fade-in slide-in-from-top-4 duration-200">
              <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div className="text-xs space-y-1">
                <span className="font-bold">Clasificación Automática con Contexto Limitado</span>
                <p className="text-amber-700 leading-relaxed">
                  El código CIIU y la descripción generada automáticamente pueden tener variaciones debido a la falta de contexto total de la empresa (misión, visión o procesos de negocio no registrados).
                </p>
              </div>
            </div>
          )}
          <FormField label="Código CIIU">
            <Input
              value={form.ciiu_codigo ?? ''}
              onChange={(e) => handleChange('ciiu_codigo', e.target.value)}
              placeholder="Ej: 6201"
            />
          </FormField>
          <FormField label="Descripción CIIU">
            <Input
              value={form.ciiu_descripcion ?? ''}
              onChange={(e) => handleChange('ciiu_descripcion', e.target.value)}
              placeholder="Ej: Desarrollo de software"
            />
          </FormField>
          <FormField label="Sector Económico">
            <Select
              options={SECTOR_OPTIONS}
              value={form.sector_economico ?? ''}
              onChange={(e) => handleChange('sector_economico', e.target.value)}
            />
          </FormField>
          <FormField label="Nivel de Riesgo">
            <Select
              options={NIVEL_RIESGO_OPTIONS}
              value={String(form.nivel_riesgo ?? 1)}
              onChange={(e) => handleChange('nivel_riesgo', Number(e.target.value))}
            />
          </FormField>

          {form.ciiu_768_principal && (
            <div className="col-span-full mt-4 p-4 bg-slate-50 border border-slate-100 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <span className="text-[10px] uppercase font-black text-slate-400 tracking-wider">Código Decreto 768 / CIIU Rev 4 A.C.</span>
                <div className="text-sm font-bold text-slate-800 flex flex-wrap items-center gap-2 mt-1">
                  <span className="bg-brand-50 text-brand-700 px-2 py-0.5 rounded font-mono text-xs border border-brand-100" title="Código Decreto 768">
                    Decreto 768: {form.ciiu_768_principal}
                  </span>
                  {form.ciiu_codigo && (
                    <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono text-xs border border-slate-200" title="Código CIIU Rev. 4">
                      CIIU Rev. 4: {form.ciiu_codigo}
                    </span>
                  )}
                  <span className="ml-1 text-slate-600 text-xs font-semibold">
                    {form.ciiu_768_metadata?.resultado?.actividad_principal?.descripcion || form.ciiu_descripcion}
                  </span>
                </div>
              </div>
              <div className="flex-shrink-0">
                {getRiesgoBadge(form.nivel_riesgo || 1)}
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Datos de contacto */}
      <Card title="Datos de la Empresa" subtitle="Representante, ARL y ubicación">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
          <FormField label="Representante Legal">
            <Input
              value={form.representante_legal ?? ''}
              onChange={(e) => handleChange('representante_legal', e.target.value)}
              placeholder="Nombre completo"
            />
          </FormField>
          <FormField label="ARL">
            <Input
              value={form.arl ?? ''}
              onChange={(e) => handleChange('arl', e.target.value)}
              placeholder="Ej: SURA, Positiva, Colmena"
            />
          </FormField>
          <FormField label="Ciudad">
            <Input
              value={form.ciudad ?? ''}
              onChange={(e) => handleChange('ciudad', e.target.value)}
              placeholder="Ej: Bogotá"
            />
          </FormField>
          <FormField label="Número de Trabajadores">
            <Input
              type="number"
              min={1}
              value={form.num_trabajadores ?? ''}
              onChange={(e) => handleChange('num_trabajadores', Number(e.target.value))}
              placeholder="Ej: 50"
            />
          </FormField>
        </div>
      </Card>

      {/* Modal Sugerir con IA */}
      {sugerirModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200 flex flex-col max-h-[85vh]">
            {/* Header Modal */}
            <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 text-white px-6 py-4 flex justify-between items-center">
              <div>
                <h3 className="font-black text-sm flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-brand-400" />
                  Sugerir Clasificación CIIU 768 con IA
                </h3>
                <p className="text-[10px] text-slate-300">Identifica códigos y clases de riesgo según el Decreto 768.</p>
              </div>
              <button
                onClick={() => {
                  setSugerirModalOpen(false)
                  setSugerenciaResult(null)
                }}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Contenido */}
            <div className="p-6 space-y-4 overflow-y-auto flex-1">
              {!sugerenciaResult ? (
                <>
                  <div className="text-xs text-slate-500">
                    Proporciona una descripción breve de la actividad económica principal de la empresa. La IA analizará el catálogo de 1,115 códigos para encontrar los que mejor correspondan a tu organización.
                  </div>
                  <FormField label="Descripción de la Actividad Económica">
                    <textarea
                      value={descLibre}
                      onChange={(e) => setDescLibre(e.target.value)}
                      placeholder="Ej: Prestación de servicios de consultoría informática, desarrollo de software a medida, y diseño de portales web..."
                      className="w-full text-sm border border-surface-2 rounded-xl p-3 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-brand-400 min-h-[100px]"
                    />
                  </FormField>
                  {sugerirError && (
                    <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 flex-shrink-0" />
                      <span>{sugerirError}</span>
                    </div>
                  )}
                </>
              ) : (
                <div className="space-y-4">
                  {/* Actividad Principal */}
                  <div className="border border-brand-200 rounded-xl p-4 bg-brand-50/20 relative overflow-hidden">
                    <div className="absolute top-0 right-0 bg-brand-500 text-white text-[10px] font-black px-3 py-1 rounded-bl-lg">
                      PRINCIPAL SUGERIDA
                    </div>
                    <div className="flex items-center gap-2 text-xs font-semibold text-brand-700 uppercase tracking-wider mb-1">
                      Actividad Económica Principal
                    </div>
                    <div className="flex items-start justify-between gap-4 mt-2">
                      <div className="flex-1">
                        <div className="font-bold text-slate-800 flex flex-wrap items-center gap-2 text-sm">
                          <span className="bg-brand-100 text-brand-800 font-mono px-2 py-0.5 rounded text-xs" title="Decreto 768">
                            Decreto 768: {sugerenciaResult.resultado.actividad_principal.codigo_768}
                          </span>
                          <span className="bg-slate-100 text-slate-700 font-mono px-2 py-0.5 rounded text-xs" title="CIIU Rev. 4">
                            CIIU Rev. 4: {sugerenciaResult.resultado.actividad_principal.ciiu_rev4}
                          </span>
                          <span className="w-full sm:w-auto text-slate-800 mt-1 sm:mt-0">
                            {sugerenciaResult.resultado.actividad_principal.descripcion}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 mt-2 italic bg-white/50 p-2.5 rounded-lg border border-slate-100">
                          &ldquo;{sugerenciaResult.resultado.actividad_principal.justificacion}&rdquo;
                        </p>
                      </div>
                      <div className="flex-shrink-0">
                        {getRiesgoBadge(sugerenciaResult.resultado.actividad_principal.clase_riesgo)}
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 mt-3 pt-3 border-t border-slate-100 text-[10px] text-slate-400">
                      <div><strong className="text-slate-500">División:</strong> {sugerenciaResult.resultado.actividad_principal.division}</div>
                      <div><strong className="text-slate-500">Grupo:</strong> {sugerenciaResult.resultado.actividad_principal.grupo}</div>
                    </div>
                  </div>

                  {/* Actividades Secundarias */}
                  {sugerenciaResult.resultado.actividades_secundarias && sugerenciaResult.resultado.actividades_secundarias.length > 0 && (
                    <div className="space-y-3">
                      <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                        Actividades Secundarias Sugeridas
                      </div>
                      <div className="space-y-2">
                        {sugerenciaResult.resultado.actividades_secundarias.map((sec: any, idx: number) => (
                          <div key={idx} className="border border-surface-2 rounded-xl p-3 bg-slate-50/50 hover:bg-slate-50 transition-all flex items-start justify-between gap-4">
                            <div className="space-y-1.5 flex-1">
                              <div className="font-bold text-slate-800 flex flex-wrap items-center gap-2 text-xs">
                                <span className="bg-slate-100 text-slate-700 font-mono px-2 py-0.5 rounded text-[10px]" title="Decreto 768">
                                  Decreto 768: {sec.codigo_768}
                                </span>
                                <span className="bg-slate-50 text-slate-600 font-mono px-2 py-0.5 rounded text-[10px] border border-slate-200" title="CIIU Rev. 4">
                                  CIIU Rev. 4: {sec.ciiu_rev4}
                                </span>
                                <span className="w-full sm:w-auto text-slate-800 mt-1 sm:mt-0">
                                  {sec.descripcion}
                                </span>
                              </div>
                              <p className="text-[11px] text-slate-500 italic">
                                &ldquo;{sec.justificacion}&rdquo;
                              </p>
                            </div>
                            <div className="flex-shrink-0">
                              {getRiesgoBadge(sec.clase_riesgo)}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="text-[10px] text-slate-400 flex items-center justify-between border-t border-slate-100 pt-3">
                    <span>Fuente: <strong className="text-slate-500">{sugerenciaResult.fuente}</strong></span>
                    <span>Candidatos analizados del catálogo: <strong className="text-slate-500">{sugerenciaResult.candidatos_evaluados?.length || 0}</strong></span>
                  </div>
                </div>
              )}
            </div>

            {/* Footer Modal */}
            <div className="flex gap-3 justify-end px-6 py-4 border-t border-surface-2 bg-slate-50">
              {!sugerenciaResult ? (
                <>
                  <Button
                    onClick={() => setSugerirModalOpen(false)}
                    variant="secondary"
                    className="text-xs py-2 px-4"
                  >
                    Cancelar
                  </Button>
                  <Button
                    onClick={handleSugerirCiiu}
                    variant="primary"
                    className="text-xs py-2 px-5 flex items-center gap-1.5"
                    disabled={isSugerirPending}
                  >
                    {isSugerirPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                    Sugerir Actividades
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    onClick={() => setSugerenciaResult(null)}
                    variant="secondary"
                    className="text-xs py-2 px-4"
                  >
                    Volver a Consultar
                  </Button>
                  <Button
                    onClick={() => handleAplicarSugerencia(sugerenciaResult.resultado)}
                    variant="primary"
                    className="text-xs py-2 px-5 flex items-center gap-1.5 bg-green-600 hover:bg-green-700 border-none text-white shadow-md shadow-green-500/20"
                  >
                    <Check className="w-4 h-4" />
                    Aplicar Clasificación
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal Ver Descripción */}
      {descModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200 flex flex-col max-h-[85vh]">
            {/* Header Modal */}
            <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 text-white px-6 py-4 flex justify-between items-center">
              <div>
                <h3 className="font-black text-sm flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-brand-400" />
                  Descripción Contextualizada de Actividad Económica
                </h3>
                <p className="text-[10px] text-slate-300">Análisis operativo y consideraciones preventivas de SST.</p>
              </div>
              <button
                onClick={() => {
                  setDescModalOpen(false)
                  setDescResult(null)
                }}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Contenido */}
            <div className="p-6 space-y-5 overflow-y-auto flex-1 bg-slate-50/30">
              {isDescPending && (
                <div className="flex flex-col items-center justify-center py-12 space-y-3">
                  <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
                  <span className="text-xs text-slate-500 font-medium">Analizando actividades económicas con IA...</span>
                </div>
              )}

              {descError && (
                <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{descError}</span>
                </div>
              )}

              {descResult && (
                <div className="space-y-6">
                  {/* Actividad Principal */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                      <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex flex-wrap items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-brand-500" />
                        Actividad Principal (Decreto 768: {descResult.actividad_principal.codigo_768} | CIIU Rev. 4: {descResult.actividad_principal.ciiu_rev4})
                      </h4>
                      {getRiesgoBadge(descResult.actividad_principal.clase_riesgo)}
                    </div>
                    <div className="space-y-1.5">
                      <div className="text-sm font-bold text-slate-800">
                        {descResult.actividad_principal.descripcion}
                      </div>
                      <div className="grid grid-cols-2 gap-3 bg-slate-100/55 p-3.5 rounded-xl text-[10px] text-slate-500 border border-slate-100">
                        <div><strong>Sector:</strong> {descResult.actividad_principal.sector}</div>
                        <div><strong>División:</strong> {descResult.actividad_principal.division}</div>
                        <div className="col-span-2 mt-1"><strong>Grupo:</strong> {descResult.actividad_principal.grupo}</div>
                      </div>
                      <div className="text-xs text-slate-700 leading-relaxed bg-white border border-surface-2 p-5 rounded-2xl mt-4 shadow-sm whitespace-pre-line">
                        {descResult.actividad_principal.descripcion_contextualizada}
                      </div>
                    </div>
                  </div>

                  {/* Actividades Secundarias */}
                  {descResult.actividades_secundarias && descResult.actividades_secundarias.length > 0 && (
                    <div className="space-y-4 pt-2">
                      <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-slate-400" />
                        Actividades Secundarias
                      </h4>
                      <div className="space-y-3">
                        {descResult.actividades_secundarias.map((sec: any, idx: number) => (
                          <div key={idx} className="border border-surface-2 rounded-2xl p-4 bg-white/70 hover:bg-white transition-all space-y-2 shadow-sm">
                            <div className="flex justify-between items-start gap-4">
                              <div className="text-xs font-bold text-slate-800 flex flex-wrap items-center gap-2">
                                <span className="bg-slate-100 text-slate-700 font-mono px-2 py-0.5 rounded text-[10px]" title="Decreto 768">
                                  Decreto 768: {sec.codigo_768}
                                </span>
                                <span className="bg-slate-50 text-slate-600 font-mono px-2 py-0.5 rounded text-[10px] border border-slate-200" title="CIIU Rev. 4">
                                  CIIU Rev. 4: {sec.ciiu_rev4}
                                </span>
                                <span>{sec.descripcion}</span>
                              </div>
                              {getRiesgoBadge(sec.clase_riesgo)}
                            </div>
                            <div className="text-xs text-slate-600 leading-relaxed pl-3 border-l-2 border-slate-200 mt-2">
                              {sec.descripcion_contextualizada}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Footer Modal */}
            <div className="flex gap-3 justify-end px-6 py-4 border-t border-surface-2 bg-slate-50">
              <Button
                onClick={() => {
                  setDescModalOpen(false)
                  setDescResult(null)
                }}
                variant="primary"
                className="text-xs py-2 px-6"
              >
                Cerrar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Confirmación de Transición de Capítulo (RF-USR-03) */}
      {transicionModalData && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200 flex flex-col">
            {/* Header Modal */}
            <div className="bg-gradient-to-r from-amber-600 via-amber-500 to-amber-700 text-white px-6 py-5 flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-white/20 rounded-xl backdrop-blur-sm">
                  <ShieldAlert className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="font-black text-base">Transición de Capítulo Normativo</h3>
                  <p className="text-xs text-amber-100">
                    Cambio en las condiciones organizacionales detectado (RF-USR-03)
                  </p>
                </div>
              </div>
              <button
                onClick={handleCancelarTransicion}
                className="text-amber-200 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Cuerpo del Modal */}
            <div className="p-6 space-y-5 bg-slate-50/50">
              {/* Resumen del cambio */}
              <div className="bg-white p-4 rounded-xl border border-amber-200 shadow-sm flex items-center justify-between gap-4">
                <div className="text-center flex-1 p-3 bg-amber-50/50 rounded-lg border border-amber-100">
                  <span className="text-[10px] font-bold text-amber-700 uppercase tracking-wider block">Capítulo Actual</span>
                  <span className="text-2xl font-black text-slate-800">Capítulo {transicionModalData.capitulo_anterior}</span>
                </div>
                <ArrowRight className="w-6 h-6 text-amber-500 flex-shrink-0" />
                <div className="text-center flex-1 p-3 bg-brand-50/50 rounded-lg border border-brand-100">
                  <span className="text-[10px] font-bold text-brand-700 uppercase tracking-wider block">Nuevo Capítulo</span>
                  <span className="text-2xl font-black text-brand-700">Capítulo {transicionModalData.capitulo_nuevo}</span>
                </div>
              </div>

              {/* Explicación amigable del comportamiento */}
              <div className="text-xs text-slate-600 space-y-2 bg-white p-4 rounded-xl border border-slate-200 leading-relaxed">
                <p className="font-semibold text-slate-800 flex items-center gap-1.5">
                  <Check className="w-4 h-4 text-green-600" />
                  Preservación garantizada de respuestas históricas
                </p>
                <p>
                  Las respuestas y evidencias diligenciadas bajo el Capítulo {transicionModalData.capitulo_anterior} <strong>permanecerán intactas en la base de datos</strong>. Ninguna información será eliminada ni reiniciada.
                </p>
                <p className="text-slate-500 text-[11px] pt-1 border-t border-slate-100">
                  El porcentaje de cumplimiento actual se recalculará en función de los estándares aplicables al <strong>Capítulo {transicionModalData.capitulo_nuevo}</strong>. Podrás consultar tus respuestas anteriores en la sección de Historial.
                </p>
              </div>

              {/* Campo para motivo opcional */}
              <FormField label="Motivo o Justificación del Cambio (Opcional)">
                <textarea
                  value={motivoTransicion}
                  onChange={(e) => setMotivoTransicion(e.target.value)}
                  placeholder="Ej: Aumento de la nómina de personal a más de 11 trabajadores..."
                  className="w-full text-xs border border-slate-300 rounded-xl p-3 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 min-h-[70px]"
                />
              </FormField>

              {transicionError && (
                <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{transicionError}</span>
                </div>
              )}
            </div>

            {/* Footer del Modal */}
            <div className="flex gap-3 justify-end px-6 py-4 border-t border-slate-200 bg-slate-100">
              <Button
                onClick={handleCancelarTransicion}
                variant="secondary"
                className="text-xs py-2 px-4"
                disabled={isConfirmingTransicion}
              >
                Cancelar y Revertir
              </Button>
              <Button
                onClick={handleConfirmarTransicion}
                variant="primary"
                className="text-xs py-2 px-5 bg-amber-600 hover:bg-amber-700 text-white border-none shadow-md shadow-amber-600/20 flex items-center gap-1.5"
                disabled={isConfirmingTransicion}
              >
                {isConfirmingTransicion && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                Confirmar Transición a Capítulo {transicionModalData.capitulo_nuevo}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

