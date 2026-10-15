import { useState, useEffect, useRef, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { modulo0Service, EmpresaContexto, IdentidadSugerida } from '@/services/modulo0.service'
import { Card, Button } from '@/components/ui'
import { FormField, LoadingSpinner, ErrorDisplay } from '@/components/ui/forms'
import {
  Compass, Target, Sparkles, Check, Loader2, AlertCircle, Info,
  Plus, X, Award, HelpCircle
} from 'lucide-react'

type SaveStatus = 'idle' | 'saving' | 'saved' | 'error'

export default function IdentidadView() {
  const queryClient = useQueryClient()

  // Fetch current company context (which includes mision, vision, valores)
  const { data: empresa, isLoading, error, refetch } = useQuery({
    queryKey: ['modulo0', 'contexto'],
    queryFn: modulo0Service.getContexto,
  })

  // State for forms
  const [form, setForm] = useState<{
    mision: string
    vision: string
    valores: string[]
  }>({
    mision: '',
    vision: '',
    valores: [],
  })

  // Value chip input state
  const [newValueInput, setNewValueInput] = useState('')

  // State for visual indicators
  const [status, setStatus] = useState<SaveStatus>('idle')
  const [iaModalOpen, setIaModalOpen] = useState(false)

  const debounceRef = useRef<ReturnType<typeof setTimeout>>()

  // Sync data from query to local state
  useEffect(() => {
    if (empresa) {
      setForm({
        mision: empresa.mision ?? '',
        vision: empresa.vision ?? '',
        valores: Array.isArray(empresa.valores) ? (empresa.valores as string[]) : [],
      })
    }
  }, [empresa])

  // Save strategic identity mutation
  const saveMutation = useMutation({
    mutationFn: (data: { mision?: string | null; vision?: string | null; valores?: string[] | null }) =>
      modulo0Service.updateIdentidad(data),
    onMutate: () => setStatus('saving'),
    onSuccess: () => {
      setStatus('saved')
      queryClient.invalidateQueries({ queryKey: ['modulo0'] })
      setTimeout(() => setStatus('idle'), 2500)
    },
    onError: () => {
      setStatus('error')
      setTimeout(() => setStatus('idle'), 3000)
    },
  })

  // Fetch AI suggestions manually
  const { data: sugeridosIA, refetch: fetchSugeridosIA, isFetching: isFetchingIA } = useQuery({
    queryKey: ['modulo0', 'sugerencias-identidad'],
    queryFn: modulo0Service.sugerirIdentidadIA,
    enabled: false, // Only triggered by user click
  })

  // Auto-save with debounce helper
  const scheduleAutoSave = useCallback(
    (updated: { mision: string; vision: string; valores: string[] }) => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
      debounceRef.current = setTimeout(() => {
        saveMutation.mutate({
          mision: updated.mision || null,
          vision: updated.vision || null,
          valores: updated.valores.length > 0 ? updated.valores : null,
        })
      }, 1500)
    },
    [saveMutation]
  )

  // Handle generic text change
  const handleTextChange = (field: 'mision' | 'vision', value: string) => {
    const updated = { ...form, [field]: value }
    setForm(updated)
    scheduleAutoSave(updated)
  }

  // Handle adding a corporate value chip
  const handleAddValor = (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    const value = newValueInput.trim()
    if (!value) return

    // Prevent duplicates
    if (form.valores.some(v => v.toLowerCase() === value.toLowerCase())) {
      setNewValueInput('')
      return
    }

    const updatedValores = [...form.valores, value]
    const updated = { ...form, valores: updatedValores }
    setForm(updated)
    setNewValueInput('')
    scheduleAutoSave(updated)
  }

  // Handle deleting a corporate value chip
  const handleDeleteValor = (indexToDelete: number) => {
    const updatedValores = form.valores.filter((_, idx) => idx !== indexToDelete)
    const updated = { ...form, valores: updatedValores }
    setForm(updated)
    scheduleAutoSave(updated)
  }

  // Handle key triggers inside the chip input
  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      handleAddValor()
    }
  }

  // Trigger AI suggestion query & open modal
  const handleSugerirIA = () => {
    setIaModalOpen(true)
    fetchSugeridosIA()
  }

  // Apply the AI suggestions directly to form & save
  const handleApplySugerencia = () => {
    if (!sugeridosIA?.identidad) return

    const { mision, vision, valores } = sugeridosIA.identidad
    const updated = {
      mision: mision || '',
      vision: vision || '',
      valores: Array.isArray(valores) ? valores : [],
    }

    setForm(updated)
    saveMutation.mutate({
      mision: updated.mision || null,
      vision: updated.vision || null,
      valores: updated.valores.length > 0 ? updated.valores : null,
    })
    setIaModalOpen(false)
  }

  if (isLoading) return <LoadingSpinner text="Cargando identidad estratégica corporativa…" />
  if (error) return <ErrorDisplay message={(error as Error).message} onRetry={refetch} />

  return (
    <div className="space-y-6">
      {/* Cabecera y Status Banner */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-md font-bold text-slate-800 flex items-center gap-2">
            <Compass className="w-5 h-5 text-brand-500 animate-spin-slow" />
            Identidad Estratégica
          </h2>
          <p className="text-xs text-slate-500">
            Define la Misión, Visión y Valores Corporativos para estructurar la cultura y el direccionamiento estratégico de la organización.
          </p>
        </div>

        {/* Acciones e Indicador de Autoguardado */}
        <div className="flex items-center gap-4 w-full sm:w-auto justify-between sm:justify-end">
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

          <Button
            onClick={handleSugerirIA}
            variant="secondary"
            className="text-xs py-2 px-3 border-brand-200 text-brand-700 bg-brand-50 hover:bg-brand-100/80 flex items-center gap-1.5 font-bold shadow-sm"
          >
            <Sparkles className="w-4 h-4 text-brand-500 animate-pulse" /> Sugerir con IA
          </Button>
        </div>
      </div>

      {/* Grid de Contenidos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Columna Misión */}
        <Card
          title="Misión Corporativa"
          subtitle="Describe el propósito fundamental, razón de ser y clientes objetivos de la organización."
          className="border-t-4 border-t-brand-500 h-full flex flex-col justify-between"
        >
          <FormField label="Redacción de la Misión">
            <textarea
              value={form.mision}
              onChange={(e) => handleTextChange('mision', e.target.value)}
              rows={8}
              className="w-full rounded-xl border border-surface-2 bg-white text-xs px-3.5 py-3 text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 shadow-sm leading-relaxed"
              placeholder="Ej: Somos una empresa dedicada a proveer soluciones tecnológicas eficientes, garantizando la seguridad en el desarrollo de software..."
            />
          </FormField>
          <div className="mt-2 p-3 bg-slate-50 border border-slate-100 rounded-xl flex items-start gap-2.5">
            <Info className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
            <p className="text-[10px] text-slate-400 leading-normal">
              <strong>Consejo:</strong> Una misión sólida responde a quiénes somos, qué hacemos, a quiénes servimos y cuál es nuestro elemento diferenciador.
            </p>
          </div>
        </Card>

        {/* Columna Visión */}
        <Card
          title="Visión Corporativa"
          subtitle="Define la meta futura de mediano y largo plazo, proyectando dónde se ve la organización."
          className="border-t-4 border-t-amber-500 h-full flex flex-col justify-between"
        >
          <FormField label="Redacción de la Visión">
            <textarea
              value={form.vision}
              onChange={(e) => handleTextChange('vision', e.target.value)}
              rows={8}
              className="w-full rounded-xl border border-surface-2 bg-white text-xs px-3.5 py-3 text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 shadow-sm leading-relaxed"
              placeholder="Ej: Para el año 2030, ser reconocidos a nivel continental como líderes en servicios HSEQ y seguridad informática..."
            />
          </FormField>
          <div className="mt-2 p-3 bg-slate-50 border border-slate-100 rounded-xl flex items-start gap-2.5">
            <Target className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
            <p className="text-[10px] text-slate-400 leading-normal">
              <strong>Consejo:</strong> La visión debe ser inspiradora, retadora pero alcanzable, con un horizonte temporal de cumplimiento claro.
            </p>
          </div>
        </Card>
      </div>

      {/* Valores Corporativos */}
      <Card
        title="Valores Corporativos"
        subtitle="Principios fundamentales y pilares éticos que rigen el comportamiento de los trabajadores y directores."
        className="border-l-4 border-l-blue-500"
      >
        <div className="space-y-4">
          {/* Chip Grid */}
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-2">
              Valores Actuales ({form.valores.length})
            </label>
            
            {form.valores.length === 0 ? (
              <div className="border border-dashed border-slate-200 rounded-xl p-6 text-center select-none bg-slate-50/50">
                <Award className="w-6 h-6 text-slate-300 mx-auto mb-1.5" />
                <p className="text-[10px] text-slate-400 max-w-[280px] mx-auto leading-normal">
                  Aún no has registrado valores corporativos. Agrega elementos usando el campo de abajo o solicita sugerencias con Inteligencia Artificial.
                </p>
              </div>
            ) : (
              <div className="flex flex-wrap gap-2 p-3 bg-slate-50/70 border border-slate-100 rounded-xl">
                {form.valores.map((valor, idx) => (
                  <div
                    key={idx}
                    className="group bg-white border border-slate-200 text-slate-700 hover:border-brand-300 hover:text-brand-700 text-xs font-semibold pl-3 pr-1.5 py-1.5 rounded-xl flex items-center gap-1.5 transition-all shadow-sm duration-150"
                  >
                    <span>{valor}</span>
                    <button
                      type="button"
                      onClick={() => handleDeleteValor(idx)}
                      className="p-0.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                      title={`Eliminar valor "${valor}"`}
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Input para agregar */}
          <form onSubmit={handleAddValor} className="flex gap-2 max-w-md items-end">
            <div className="flex-1">
              <label className="block text-[10px] font-semibold text-slate-400 mb-1">
                Escribe un valor y presiona Enter o Coma (,)
              </label>
              <input
                type="text"
                value={newValueInput}
                onChange={(e) => setNewValueInput(e.target.value)}
                onKeyDown={handleInputKeyDown}
                className="w-full bg-white border border-surface-2 rounded-xl px-3 py-2 text-xs text-slate-700 placeholder:text-slate-400 outline-none transition-all focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
                placeholder="Ej: Compromiso, Integridad, Seguridad..."
              />
            </div>
            <Button
              type="submit"
              variant="primary"
              className="py-2 px-3 text-xs flex items-center justify-center gap-1 shadow-sm h-[38px] rounded-xl"
            >
              <Plus className="w-4 h-4" /> Agregar
            </Button>
          </form>
        </div>
      </Card>

      {/* Modal de Sugerencias de IA */}
      {iaModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-3xl w-full overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            {/* Header Modal */}
            <div className="bg-slate-900 text-white px-5 py-4 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-brand-400 fill-brand-400" />
                <div>
                  <h3 className="font-bold text-sm">Sugerencias de Identidad Estratégica</h3>
                  <p className="text-[10px] text-slate-400">Modelos AI optimizados según la actividad del sector económico.</p>
                </div>
              </div>
              <button onClick={() => setIaModalOpen(false)} className="text-slate-400 hover:text-white transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Contenido */}
            <div className="p-6 space-y-5 max-h-[500px] overflow-y-auto">
              {isFetchingIA ? (
                <div className="flex flex-col items-center justify-center py-16 space-y-3">
                  <Loader2 className="w-10 h-10 animate-spin text-brand-500" />
                  <p className="text-xs font-semibold text-slate-600">
                    Claude está analizando la información económica y el CIIU de la empresa para proponer su Misión, Visión y Valores corporativos...
                  </p>
                  <p className="text-[10px] text-slate-400">Esto tomará solo unos segundos</p>
                </div>
              ) : sugeridosIA ? (
                <div className="space-y-5">
                  {/* Fuente info */}
                  <div className="p-3.5 bg-brand-50 border border-brand-100 rounded-2xl flex items-start gap-2.5 text-brand-800 text-[10px] font-semibold">
                    <Info className="w-4 h-4 text-brand-500 mt-0.5 flex-shrink-0" />
                    <div className="leading-normal">
                      Propuesta generada mediante: <span className="font-black text-brand-700 bg-brand-100 px-1.5 py-0.5 rounded-md border border-brand-200">{sugeridosIA.fuente}</span>.
                      <p className="text-[9px] text-slate-500 mt-1 font-medium">
                        El motor de IA evalúa el nicho específico y formula enunciados alineados con los estándares de SG-SST correspondientes.
                      </p>
                    </div>
                  </div>

                  {/* Comparativa Misión */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="border border-surface-2 rounded-xl p-4 bg-slate-50">
                      <h4 className="text-[10px] font-black text-slate-400 uppercase mb-2">Misión Actual</h4>
                      <p className="text-xs text-slate-600 leading-relaxed italic">
                        {form.mision || 'Ninguna registrada'}
                      </p>
                    </div>
                    <div className="border border-brand-100 rounded-xl p-4 bg-brand-50/10 shadow-sm relative overflow-hidden">
                      <div className="absolute top-0 right-0 bg-brand-100 text-brand-700 text-[8px] font-black px-2 py-0.5 rounded-bl-lg">SUGERIDA</div>
                      <h4 className="text-[10px] font-black text-brand-600 uppercase mb-2 flex items-center gap-1">
                        <Sparkles className="w-3 h-3 text-brand-500" /> Misión Propuesta
                      </h4>
                      <p className="text-xs text-slate-700 font-medium leading-relaxed">
                        {sugeridosIA.identidad.mision}
                      </p>
                    </div>
                  </div>

                  {/* Comparativa Visión */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="border border-surface-2 rounded-xl p-4 bg-slate-50">
                      <h4 className="text-[10px] font-black text-slate-400 uppercase mb-2">Visión Actual</h4>
                      <p className="text-xs text-slate-600 leading-relaxed italic">
                        {form.vision || 'Ninguna registrada'}
                      </p>
                    </div>
                    <div className="border border-amber-100 rounded-xl p-4 bg-amber-50/10 shadow-sm relative overflow-hidden">
                      <div className="absolute top-0 right-0 bg-amber-100 text-amber-700 text-[8px] font-black px-2 py-0.5 rounded-bl-lg">SUGERIDA</div>
                      <h4 className="text-[10px] font-black text-amber-600 uppercase mb-2 flex items-center gap-1">
                        <Sparkles className="w-3 h-3 text-amber-500" /> Visión Propuesta
                      </h4>
                      <p className="text-xs text-slate-700 font-medium leading-relaxed">
                        {sugeridosIA.identidad.vision}
                      </p>
                    </div>
                  </div>

                  {/* Valores sugeridos */}
                  <div className="border border-blue-100 rounded-xl p-4 bg-blue-50/10 shadow-sm">
                    <h4 className="text-[10px] font-black text-blue-600 uppercase mb-3 flex items-center gap-1">
                      <Award className="w-3.5 h-3.5 text-blue-500" /> Valores Corporativos Sugeridos
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {sugeridosIA.identidad.valores.map((val: string, idx: number) => (
                        <span
                          key={idx}
                          className="bg-white border border-blue-200 text-blue-700 text-xs font-semibold px-3 py-1 rounded-xl shadow-sm"
                        >
                          {val}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
                  <p className="text-xs text-slate-600 font-bold">Error al conectar con el servicio de IA</p>
                  <p className="text-[10px] text-slate-400 mt-1">Inténtelo de nuevo en unos momentos.</p>
                </div>
              )}
            </div>

            {/* Footer Modal */}
            {sugeridosIA && !isFetchingIA && (
              <div className="flex justify-between items-center px-5 py-4 border-t border-surface-2 bg-slate-50">
                <span className="text-[10px] text-slate-400 font-semibold flex items-center gap-1">
                  <HelpCircle className="w-3.5 h-3.5 text-slate-400" /> Esto reemplazará tus textos actuales.
                </span>
                <div className="flex gap-2">
                  <Button onClick={() => setIaModalOpen(false)} variant="ghost" className="text-xs py-1.5 px-3">
                    Descartar
                  </Button>
                  <Button
                    onClick={handleApplySugerencia}
                    variant="primary"
                    className="text-xs py-1.5 px-4 flex items-center gap-1 font-bold"
                    disabled={saveMutation.isPending}
                  >
                    {saveMutation.isPending ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" />
                    ) : (
                      <Check className="w-3.5 h-3.5" />
                    )}
                    Aplicar Propuesta de IA
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
