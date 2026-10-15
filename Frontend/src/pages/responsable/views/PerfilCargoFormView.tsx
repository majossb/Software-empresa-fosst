import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { 
  usePerfilCargo, 
  useCrearPerfilCargo, 
  useActualizarPerfilCargo,
  usePeligrosGTC45,
  useEPPsCatalog
} from '@/hooks/useApi'
import { modulo0Service } from '@/services/modulo0.service'
import { modulo1Service } from '@/services/modulo1.service'
import { Card, PageHeader, Badge, Button } from '@/components/ui'
import { FormField, Input, Select, Textarea, LoadingSpinner, ErrorDisplay, Modal } from '@/components/ui/forms'
import { 
  ArrowLeft, Save, Sparkles, Plus, Trash2, ShieldAlert, 
  Layers, Settings, User, GraduationCap, CheckSquare, Shield, Activity, BrainCircuit,
  Loader2, Check
} from 'lucide-react'

type TabType = 'general' | 'requisitos' | 'funciones' | 'peligros' | 'indicadores'

export default function PerfilCargoFormView() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isEdit = !!id

  const [activeTab, setActiveTab] = useState<TabType>('general')
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // ── AI Assistant State ─────────────────────────────────────────────
  const [aiModalOpen, setAiModalOpen] = useState(false)
  const [aiField, setAiField] = useState<'proposito' | 'funciones' | 'responsabilidades' | null>(null)
  const [aiCargoName, setAiCargoName] = useState('')
  const [aiContext, setAiContext] = useState('')
  const [isAiStreaming, setIsAiStreaming] = useState(false)
  const [aiStreamResult, setAiStreamResult] = useState('')

  // ── Form State ─────────────────────────────────────────────────────
  const [codigo, setCodigo] = useState('')
  const [nombreCargo, setNombreCargo] = useState('')
  const [area, setArea] = useState('')
  const [sedeId, setSedeId] = useState('')
  const [nodoOrganigramaId, setNodoOrganigramaId] = useState('')
  const [procesoId, setProcesoId] = useState('')
  const [nivelRiesgo, setNivelRiesgo] = useState<number>(1)
  const [proposito, setProposito] = useState('')

  // Requisitos
  const [educacion, setEducacion] = useState('')
  const [experiencia, setExperiencia] = useState('')
  const [formacion, setFormacion] = useState('')
  const [habilidades, setHabilidades] = useState('')

  // Listas Dinámicas
  const [funcionesList, setFuncionesList] = useState<{ descripcion: string; orden: number }[]>([])
  const [responsabilidadesList, setResponsabilidadesList] = useState<{ descripcion: string; orden: number }[]>([])
  const [competenciasList, setCompetenciasList] = useState<{ nombre: string; nivel: string }[]>([])
  const [indicadoresList, setIndicadoresList] = useState<{ descripcion: string; meta: string }[]>([])

  // Peligros y EPPs
  const [selectedPeligros, setSelectedPeligros] = useState<string[]>([])
  const [selectedEpps, setSelectedEpps] = useState<string[]>([])
  const [customEpps, setCustomEpps] = useState<string[]>([])

  // Motivo del Cambio (Requerido solo al editar)
  const [motivoCambio, setMotivoCambio] = useState('')

  // ── Queries y Mutaciones ───────────────────────────────────────────
  const { data: perfilData, isLoading: loadingPerfil, error: errorPerfil } = usePerfilCargo(id || null)
  
  const { data: sedes } = useQuery({
    queryKey: ['modulo0', 'sedes'],
    queryFn: modulo0Service.listSedes,
  })

  const { data: nodosOrganigrama } = useQuery({
    queryKey: ['modulo0', 'organigrama'],
    queryFn: modulo0Service.getOrganigrama,
  })

  const { data: procesosData } = useQuery({
    queryKey: ['modulo0', 'procesos'],
    queryFn: modulo0Service.listProcesos,
  })

  const { data: catalogoPeligros } = usePeligrosGTC45()
  const { data: catalogoEpps } = useEPPsCatalog()

  const createMutation = useCrearPerfilCargo()
  const updateMutation = useActualizarPerfilCargo()

  // ── Cargar Datos en Edición ────────────────────────────────────────
  useEffect(() => {
    if (isEdit && perfilData) {
      setCodigo(perfilData.codigo || '')
      setNombreCargo(perfilData.nombre_cargo || '')
      setArea(perfilData.area || '')
      setSedeId(perfilData.sede_id || '')
      setNodoOrganigramaId(perfilData.nodo_organigrama_id || '')
      setProcesoId(perfilData.proceso_id || '')
      setNivelRiesgo(perfilData.nivel_riesgo || 1)
      setProposito(perfilData.proposito || '')

      setEducacion(perfilData.educacion || '')
      setExperiencia(perfilData.experiencia || '')
      setFormacion(perfilData.formacion || '')
      setHabilidades(perfilData.habilidades || '')

      setFuncionesList(perfilData.funciones?.map(f => ({ descripcion: f.descripcion, orden: f.orden ?? 0 })) || [])
      setResponsabilidadesList(perfilData.responsabilidades?.map(r => ({ descripcion: r.descripcion, orden: r.orden ?? 0 })) || [])
      setCompetenciasList(perfilData.competencias?.map(c => ({ nombre: c.nombre, nivel: c.nivel || 'Intermedio' })) || [])
      setIndicadoresList(perfilData.indicadores?.map(i => ({ descripcion: i.descripcion, meta: i.meta || '' })) || [])

      setSelectedPeligros(perfilData.peligros?.map(p => p.catalogo_peligro_id).filter(Boolean) as string[] || [])
      setSelectedEpps(perfilData.epps?.filter(e => e.catalogo_epp_id).map(e => e.catalogo_epp_id as string) || [])
      setCustomEpps(perfilData.epps?.filter(e => !e.catalogo_epp_id && e.nombre_personalizado).map(e => e.nombre_personalizado as string) || [])
    }
  }, [isEdit, perfilData])

  // Alinear el nombre del cargo para el asistente de IA
  useEffect(() => {
    if (nombreCargo) {
      setAiCargoName(nombreCargo)
    }
  }, [nombreCargo])

  // Flatten Procesos para Dropdown
  const flattenedProcesos = procesosData ? [
    ...(procesosData.estrategico || []).map(p => ({ ...p, display: `[Estratégico] ${p.nombre}` })),
    ...(procesosData.misional || []).map(p => ({ ...p, display: `[Misional] ${p.nombre}` })),
    ...(procesosData.apoyo || []).map(p => ({ ...p, display: `[Apoyo] ${p.nombre}` })),
  ] : []

  // ── Controladores de Listas Dinámicas ──────────────────────────────
  const addFuncion = () => {
    setFuncionesList([...funcionesList, { descripcion: '', orden: funcionesList.length }])
  }
  const updateFuncion = (index: number, val: string) => {
    const list = [...funcionesList]
    list[index].descripcion = val
    setFuncionesList(list)
  }
  const removeFuncion = (index: number) => {
    setFuncionesList(funcionesList.filter((_, i) => i !== index))
  }

  const addResponsabilidad = () => {
    setResponsabilidadesList([...responsabilidadesList, { descripcion: '', orden: responsabilidadesList.length }])
  }
  const updateResponsabilidad = (index: number, val: string) => {
    const list = [...responsabilidadesList]
    list[index].descripcion = val
    setResponsabilidadesList(list)
  }
  const removeResponsabilidad = (index: number) => {
    setResponsabilidadesList(responsabilidadesList.filter((_, i) => i !== index))
  }

  const addCompetencia = () => {
    setCompetenciasList([...competenciasList, { nombre: '', nivel: 'Intermedio' }])
  }
  const updateCompetencia = (index: number, key: 'nombre' | 'nivel', val: string) => {
    const list = [...competenciasList]
    list[index] = { ...list[index], [key]: val }
    setCompetenciasList(list)
  }
  const removeCompetencia = (index: number) => {
    setCompetenciasList(competenciasList.filter((_, i) => i !== index))
  }

  const addIndicador = () => {
    setIndicadoresList([...indicadoresList, { descripcion: '', meta: '' }])
  }
  const updateIndicador = (index: number, key: 'descripcion' | 'meta', val: string) => {
    const list = [...indicadoresList]
    list[index] = { ...list[index], [key]: val }
    setIndicadoresList(list)
  }
  const removeIndicador = (index: number) => {
    setIndicadoresList(indicadoresList.filter((_, i) => i !== index))
  }

  // ── Peligros y EPP Toggle & Smart Suggestion ───────────────────────
  const [isSugerirPeligrosLoading, setIsSugerirPeligrosLoading] = useState(false)

  const togglePeligro = (peligroId: string) => {
    setSelectedPeligros(prev => {
      const isSelected = prev.includes(peligroId)
      if (isSelected) {
        return prev.filter(id => id !== peligroId)
      } else {
        // Al seleccionar un peligro, preseleccionar automáticamente sus EPPs sugeridos
        if (catalogoPeligros) {
          for (const list of Object.values(catalogoPeligros)) {
            const p = list.find((item: any) => item.id === peligroId)
            if (p && p.epps_sugeridos && p.epps_sugeridos.length > 0) {
              const suggestedEppIds = p.epps_sugeridos.map((e: any) => e.id)
              setSelectedEpps(currEpps => Array.from(new Set([...currEpps, ...suggestedEppIds])))
            }
          }
        }
        return [...prev, peligroId]
      }
    })
  }

  const toggleEpp = (eppId: string) => {
    setSelectedEpps(prev => 
      prev.includes(eppId) ? prev.filter(id => id !== eppId) : [...prev, eppId]
    )
  }

  const getPeligroDisplay = (pId: string) => {
    const cleanId = String(pId).trim().toLowerCase()
    if (catalogoPeligros && typeof catalogoPeligros === 'object') {
      for (const list of Object.values(catalogoPeligros)) {
        if (Array.isArray(list)) {
          const found = list.find((p: any) => String(p.id).trim().toLowerCase() === cleanId)
          if (found) return { clasificacion: found.clasificacion, tipo: found.tipo, epps_sugeridos: found.epps_sugeridos || [] }
        }
      }
    }
    const fromPerfil = perfilData?.peligros?.find((p: any) => 
      String(p.catalogo_peligro_id).trim().toLowerCase() === cleanId || 
      String(p.id).trim().toLowerCase() === cleanId
    )
    if (fromPerfil) {
      return {
        clasificacion: fromPerfil.catalogo_peligro?.clasificacion || fromPerfil.clasificacion_personalizada || 'Peligro GTC-45 Identificado',
        tipo: fromPerfil.catalogo_peligro?.tipo || fromPerfil.tipo_personalizado || 'GTC 45',
        epps_sugeridos: fromPerfil.catalogo_peligro?.epps_sugeridos || []
      }
    }
    return { clasificacion: 'Peligro GTC-45', tipo: 'Identificado', epps_sugeridos: [] }
  }

  const getEppDisplay = (eId: string) => {
    const cleanId = String(eId).trim().toLowerCase()
    if (catalogoEpps && Array.isArray(catalogoEpps)) {
      const found = catalogoEpps.find((e: any) => String(e.id).trim().toLowerCase() === cleanId)
      if (found) return { nombre: found.nombre, descripcion: found.descripcion || '' }
    }
    const fromPerfil = perfilData?.epps?.find((e: any) => 
      String(e.catalogo_epp_id).trim().toLowerCase() === cleanId || 
      String(e.id).trim().toLowerCase() === cleanId
    )
    if (fromPerfil) {
      return {
        nombre: fromPerfil.catalogo_epp?.nombre || fromPerfil.nombre_personalizado || 'Elemento de Protección Personal',
        descripcion: fromPerfil.catalogo_epp?.descripcion || ''
      }
    }
    return { nombre: 'Elemento de Protección', descripcion: '' }
  }

  const eppsAgrupadosPorTipo = (() => {
    if (!catalogoEpps) return {}
    const grupos: Record<string, any[]> = {
      'Protección Craneal y Facial': [],
      'Protección Ocular': [],
      'Protección Auditiva': [],
      'Protección Respiratoria': [],
      'Protección Manual': [],
      'Calzado de Seguridad': [],
      'Trabajo en Alturas': [],
      'Protección Corporal y Vial': [],
      'Otros Equipos': []
    }
    catalogoEpps.forEach((e: any) => {
      const n = e.nombre.toLowerCase()
      if (n.includes('casco') || n.includes('barbuquejo') || n.includes('careta')) {
        grupos['Protección Craneal y Facial'].push(e)
      } else if (n.includes('gafas') || n.includes('monogafas')) {
        grupos['Protección Ocular'].push(e)
      } else if (n.includes('auditivo') || n.includes('oído')) {
        grupos['Protección Auditiva'].push(e)
      } else if (n.includes('respirador') || n.includes('mascarilla')) {
        grupos['Protección Respiratoria'].push(e)
      } else if (n.includes('guantes')) {
        grupos['Protección Manual'].push(e)
      } else if (n.includes('botas') || n.includes('calzado')) {
        grupos['Calzado de Seguridad'].push(e)
      } else if (n.includes('arnés') || n.includes('eslinga') || n.includes('línea de vida')) {
        grupos['Trabajo en Alturas'].push(e)
      } else if (n.includes('chaleco') || n.includes('delantal') || n.includes('ignífuga') || n.includes('ropa')) {
        grupos['Protección Corporal y Vial'].push(e)
      } else {
        grupos['Otros Equipos'].push(e)
      }
    })
    return Object.fromEntries(Object.entries(grupos).filter(([_, items]) => items.length > 0))
  })()

  const handleAutoSugerirPeligrosYEPPs = async () => {
    if (!nombreCargo.trim()) {
      setErrorMsg('Por favor ingrese el Nombre del Cargo en la pestaña "Información General" para identificar los peligros aplicables.')
      setActiveTab('general')
      return
    }
    setIsSugerirPeligrosLoading(true)
    try {
      const res = await modulo1Service.sugerirPeligrosEPPs({
        nombre_cargo: nombreCargo,
        area: area || undefined
      })
      if (res && res.peligros_sugeridos) {
        setSelectedPeligros(res.peligros_sugeridos)
        setSelectedEpps(res.epps_sugeridos || [])
      }
    } catch (err) {
      console.error('Error sugiriendo peligros y EPPs:', err)
    } finally {
      setIsSugerirPeligrosLoading(false)
    }
  }

  // ── AI Generation Assistant ────────────────────────────────────────
  const openAiAssistant = (field: 'proposito' | 'funciones' | 'responsabilidades') => {
    setAiField(field)
    setAiStreamResult('')
    setAiModalOpen(true)
  }

  const handleAiGenerate = async () => {
    if (!aiCargoName.trim() || !aiField) return
    setIsAiStreaming(true)
    setAiStreamResult('')

    try {
      await modulo1Service.generarCampoIAStream(
        {
          campo: aiField,
          nombre_cargo: aiCargoName,
          area: area || undefined,
          contexto_adicional: aiContext || undefined
        },
        (chunk) => {
          setAiStreamResult(prev => prev + chunk)
        },
        () => {
          setIsAiStreaming(false)
        },
        (err) => {
          console.error(err)
          setErrorMsg('Error durante la generación con IA. Asegúrese de que el backend está corriendo.')
          setIsAiStreaming(false)
        }
      )
    } catch (err: any) {
      setErrorMsg(err.message || 'Error en la conexión del stream con la IA.')
      setIsAiStreaming(false)
    }
  }

  const applyAiResult = () => {
    if (!aiField || !aiStreamResult) return

    if (aiField === 'proposito') {
      setProposito(aiStreamResult.trim())
    } else if (aiField === 'funciones') {
      // Intentar dividir por líneas o viñetas
      const lines = aiStreamResult
        .split(/\n+/)
        .map(l => l.replace(/^[-*•\d.]\s*/, '').trim())
        .filter(l => l.length > 3)
      
      const newFuncs = lines.map((desc, idx) => ({ descripcion: desc, orden: funcionesList.length + idx }))
      setFuncionesList([...funcionesList, ...newFuncs])
    } else if (aiField === 'responsabilidades') {
      const lines = aiStreamResult
        .split(/\n+/)
        .map(l => l.replace(/^[-*•\d.]\s*/, '').trim())
        .filter(l => l.length > 3)
      
      const newResps = lines.map((desc, idx) => ({ descripcion: desc, orden: responsabilidadesList.length + idx }))
      setResponsabilidadesList([...responsabilidadesList, ...newResps])
    }

    setAiModalOpen(false)
    setAiContext('')
    setAiStreamResult('')
  }

  // ── Guardar Formulario ─────────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg(null)

    if (!nombreCargo.trim()) {
      setErrorMsg('El nombre del cargo es un campo obligatorio.')
      setActiveTab('general')
      return
    }

    if (isEdit && !motivoCambio.trim()) {
      setErrorMsg('Al actualizar un perfil de cargo, debe justificar el motivo del cambio para el control de versiones.')
      return
    }

    // Estructurar el payload
    const payload: any = {
      codigo: codigo.trim() || undefined, // si va vacío el backend lo genera
      nombre_cargo: nombreCargo.trim(),
      area: area.trim() || null,
      sede_id: sedeId || null,
      nodo_organigrama_id: nodoOrganigramaId || null,
      proceso_id: procesoId || null,
      nivel_riesgo: Number(nivelRiesgo) || null,
      proposito: proposito.trim() || null,
      educacion: educacion.trim() || null,
      experiencia: experiencia.trim() || null,
      formacion: formacion.trim() || null,
      habilidades: habilidades.trim() || null,
      funciones: funcionesList.filter(f => f.descripcion.trim() !== ''),
      responsabilidades: responsabilidadesList.filter(r => r.descripcion.trim() !== ''),
      competencias: competenciasList.filter(c => c.nombre.trim() !== ''),
      indicadores: indicadoresList.filter(i => i.descripcion.trim() !== ''),
      peligros: selectedPeligros.map(id => ({ catalogo_peligro_id: id })),
      epps: [
        ...selectedEpps.map(id => ({ catalogo_epp_id: id })),
        ...customEpps.map(name => ({ nombre_personalizado: name }))
      ],
      motivo_cambio: isEdit ? motivoCambio : 'Registro inicial del cargo'
    }

    try {
      if (isEdit) {
        await updateMutation.mutateAsync({ id: id!, data: payload })
      } else {
        await createMutation.mutateAsync(payload)
      }
      navigate('/app/responsable/perfiles-cargo')
    } catch (err: any) {
      setErrorMsg(err.message || 'Ocurrió un error al guardar el perfil de cargo.')
    }
  }

  if (isEdit && loadingPerfil) {
    return <LoadingSpinner text="Cargando perfil de cargo..." />
  }

  if (isEdit && errorPerfil) {
    return <ErrorDisplay message={(errorPerfil as Error).message} onRetry={() => navigate('/app/responsable/perfiles-cargo')} />
  }

  return (
    <div className="animate-fade-in space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button 
          onClick={() => navigate('/app/responsable/perfiles-cargo')}
          className="p-2 bg-white border border-surface-2 hover:bg-slate-50 rounded-xl transition-all text-slate-500 shadow-sm"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <PageHeader 
          title={isEdit ? `Editar Perfil: ${perfilData?.nombre_cargo}` : 'Crear Perfil de Cargo'} 
          subtitle={isEdit ? 'Modifica los requisitos, funciones o peligros de esta posición.' : 'Estructura un nuevo perfil de cargo para tu organización.'}
        />
      </div>

      {errorMsg && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-2xl flex gap-3 items-start text-red-700 animate-pulse">
          <ShieldAlert className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-bold text-sm">Error en el formulario</h4>
            <p className="text-xs mt-0.5">{errorMsg}</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex bg-slate-100 p-1.5 rounded-2xl border border-surface-2 max-w-2xl text-xs gap-1">
        <button
          onClick={() => setActiveTab('general')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold transition-all w-full justify-center ${activeTab === 'general' ? 'bg-white text-primary-500 shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}
        >
          <User className="w-3.5 h-3.5" /> General
        </button>
        <button
          onClick={() => setActiveTab('requisitos')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold transition-all w-full justify-center ${activeTab === 'requisitos' ? 'bg-white text-primary-500 shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}
        >
          <GraduationCap className="w-3.5 h-3.5" /> Requisitos
        </button>
        <button
          onClick={() => setActiveTab('funciones')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold transition-all w-full justify-center ${activeTab === 'funciones' ? 'bg-white text-primary-500 shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}
        >
          <CheckSquare className="w-3.5 h-3.5" /> Funciones y Competencias
        </button>
        <button
          onClick={() => setActiveTab('peligros')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold transition-all w-full justify-center ${activeTab === 'peligros' ? 'bg-white text-primary-500 shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}
        >
          <Shield className="w-3.5 h-3.5" /> Peligros y EPP
        </button>
        <button
          onClick={() => setActiveTab('indicadores')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold transition-all w-full justify-center ${activeTab === 'indicadores' ? 'bg-white text-primary-500 shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}
        >
          <Activity className="w-3.5 h-3.5" /> Indicadores
        </button>
      </div>

      {/* Form Body */}
      <form onSubmit={handleSubmit} className="space-y-6">
        
        {/* Tab 1: General */}
        {activeTab === 'general' && (
          <Card title="Datos Identificativos del Cargo">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField label="Nombre del Cargo" required>
                <Input 
                  value={nombreCargo}
                  onChange={(e) => setNombreCargo(e.target.value)}
                  placeholder="Ej: Auxiliar Administrativo"
                />
              </FormField>

              <FormField label="Código de Perfil de Cargo" error={isEdit ? 'El código es autogenerado o inmutable al crear.' : undefined}>
                <Input 
                  value={codigo}
                  onChange={(e) => setCodigo(e.target.value)}
                  placeholder={isEdit ? '' : 'Ej: PC-2026-0001 (Dejar vacío para autogenerar)'}
                  disabled={isEdit}
                />
              </FormField>

              <FormField label="Área Funcional">
                <Input 
                  value={area}
                  onChange={(e) => setArea(e.target.value)}
                  placeholder="Ej: Gestión Humana, Operaciones"
                />
              </FormField>

              <FormField label="Sede de Asignación">
                <Select 
                  value={sedeId}
                  onChange={(e) => setSedeId(e.target.value)}
                  options={[
                    { value: '', label: 'Seleccione sede...' },
                    ...(sedes?.map(s => ({ value: s.id, label: s.nombre })) || [])
                  ]}
                />
              </FormField>

              <FormField label="Ubicación en Organigrama">
                <Select 
                  value={nodoOrganigramaId}
                  onChange={(e) => setNodoOrganigramaId(e.target.value)}
                  options={[
                    { value: '', label: 'Seleccione nodo...' },
                    ...(nodosOrganigrama?.map(n => ({ value: n.id, label: `${n.nombre_cargo} (${n.area || 'Sin área'})` })) || [])
                  ]}
                />
              </FormField>

              <FormField label="Proceso Vinculado">
                <Select 
                  value={procesoId}
                  onChange={(e) => setProcesoId(e.target.value)}
                  options={[
                    { value: '', label: 'Seleccione proceso...' },
                    ...flattenedProcesos.map(p => ({ value: p.id, label: p.display }))
                  ]}
                />
              </FormField>

              <FormField label="Nivel de Riesgo (ARL)">
                <Select 
                  value={String(nivelRiesgo)}
                  onChange={(e) => setNivelRiesgo(Number(e.target.value))}
                  options={[
                    { value: '1', label: 'Riesgo I (Mínimo) - Ej: Administrativo' },
                    { value: '2', label: 'Riesgo II (Bajo)' },
                    { value: '3', label: 'Riesgo III (Medio)' },
                    { value: '4', label: 'Riesgo IV (Alto)' },
                    { value: '5', label: 'Riesgo V (Máximo) - Ej: Construcción' }
                  ]}
                />
              </FormField>
            </div>

            {/* Propósito con Asistente IA */}
            <div className="mt-4">
              <FormField label="Propósito / Objetivo General del Cargo">
                <div className="relative">
                  <Textarea 
                    value={proposito}
                    onChange={(e) => setProposito(e.target.value)}
                    placeholder="Describe de forma concisa la misión de este cargo en la empresa..."
                    className="min-h-[120px] pr-12"
                  />
                  <button
                    type="button"
                    onClick={() => openAiAssistant('proposito')}
                    className="absolute right-3 bottom-3 p-2 bg-gradient-to-tr from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-700 text-slate-950 text-white rounded-xl shadow-md flex items-center justify-center hover:scale-105 transition-all"
                    title="Generar con Inteligencia Artificial"
                  >
                    <Sparkles className="w-4 h-4" />
                  </button>
                </div>
              </FormField>
            </div>
          </Card>
        )}

        {/* Tab 2: Requisitos */}
        {activeTab === 'requisitos' && (
          <Card title="Perfil de Requisitos y Competencias Técnicas">
            <div className="space-y-4">
              <FormField label="Educación Requerida">
                <Textarea 
                  value={educacion}
                  onChange={(e) => setEducacion(e.target.value)}
                  placeholder="Ej: Profesional en Ingeniería Industrial, Tecnólogo en Administración de Empresas..."
                  className="min-h-[80px]"
                />
              </FormField>

              <FormField label="Experiencia Laboral Requerida">
                <Textarea 
                  value={experiencia}
                  onChange={(e) => setExperiencia(e.target.value)}
                  placeholder="Ej: Mínimo 2 años en cargos similares liderando equipos..."
                  className="min-h-[80px]"
                />
              </FormField>

              <FormField label="Formación o Conocimientos Adicionales">
                <Textarea 
                  value={formacion}
                  onChange={(e) => setFormacion(e.target.value)}
                  placeholder="Ej: Curso de 50 horas SG-SST, Especialización en Gerencia de Proyectos..."
                  className="min-h-[80px]"
                />
              </FormField>

              <FormField label="Habilidades Blandas / Atributos Personales">
                <Textarea 
                  value={habilidades}
                  onChange={(e) => setHabilidades(e.target.value)}
                  placeholder="Ej: Liderazgo positivo, Negociación asertiva, Trabajo en equipo..."
                  className="min-h-[80px]"
                />
              </FormField>
            </div>
          </Card>
        )}

        {/* Tab 3: Funciones y Competencias */}
        {activeTab === 'funciones' && (
          <div className="space-y-6">
            
            {/* Funciones */}
            <Card 
              title="Funciones Principales" 
              subtitle="Describe las actividades clave que realiza el empleado."
              action={
                <div className="flex gap-2">
                  <Button onClick={() => openAiAssistant('funciones')} variant="secondary" className="flex items-center gap-1.5 py-1 text-xs">
                    <Sparkles className="w-3.5 h-3.5 text-brand-600" /> Generar Funciones
                  </Button>
                  <Button onClick={addFuncion} variant="ghost" className="flex items-center gap-1.5 py-1 text-xs bg-slate-50 border border-slate-200">
                    <Plus className="w-3.5 h-3.5" /> Agregar
                  </Button>
                </div>
              }
            >
              {funcionesList.length === 0 ? (
                <div className="py-6 text-center text-xs text-slate-400 italic">No se han registrado funciones para este cargo.</div>
              ) : (
                <div className="space-y-3">
                  {funcionesList.map((f, idx) => (
                    <div key={idx} className="flex gap-3 items-center group">
                      <span className="text-xs font-bold text-slate-400 w-5">{idx + 1}.</span>
                      <Input 
                        value={f.descripcion}
                        onChange={(e) => updateFuncion(idx, e.target.value)}
                        placeholder="Descripción de la función del cargo..."
                        className="flex-grow text-xs py-2"
                      />
                      <button
                        type="button"
                        onClick={() => removeFuncion(idx)}
                        className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg opacity-40 group-hover:opacity-100 transition-all"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </Card>

            {/* Responsabilidades */}
            <Card 
              title="Responsabilidades Específicas" 
              subtitle="Responsabilidades asociadas a la gestión o uso de recursos."
              action={
                <div className="flex gap-2">
                  <Button onClick={() => openAiAssistant('responsabilidades')} variant="secondary" className="flex items-center gap-1.5 py-1 text-xs">
                    <Sparkles className="w-3.5 h-3.5 text-brand-600" /> Generar Responsabilidades
                  </Button>
                  <Button onClick={addResponsabilidad} variant="ghost" className="flex items-center gap-1.5 py-1 text-xs bg-slate-50 border border-slate-200">
                    <Plus className="w-3.5 h-3.5" /> Agregar
                  </Button>
                </div>
              }
            >
              {responsabilidadesList.length === 0 ? (
                <div className="py-6 text-center text-xs text-slate-400 italic">No se han registrado responsabilidades para este cargo.</div>
              ) : (
                <div className="space-y-3">
                  {responsabilidadesList.map((r, idx) => (
                    <div key={idx} className="flex gap-3 items-center group">
                      <span className="text-xs font-bold text-slate-400 w-5">{idx + 1}.</span>
                      <Input 
                        value={r.descripcion}
                        onChange={(e) => updateResponsabilidad(idx, e.target.value)}
                        placeholder="Descripción de la responsabilidad..."
                        className="flex-grow text-xs py-2"
                      />
                      <button
                        type="button"
                        onClick={() => removeResponsabilidad(idx)}
                        className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg opacity-40 group-hover:opacity-100 transition-all"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </Card>

            {/* Competencias Específicas */}
            <Card 
              title="Competencias Específicas del Rol" 
              action={
                <Button onClick={addCompetencia} variant="ghost" className="flex items-center gap-1.5 py-1 text-xs bg-slate-50 border border-slate-200">
                  <Plus className="w-3.5 h-3.5" /> Agregar Competencia
                </Button>
              }
            >
              {competenciasList.length === 0 ? (
                <div className="py-6 text-center text-xs text-slate-400 italic">No se han registrado competencias.</div>
              ) : (
                <div className="space-y-3">
                  {competenciasList.map((c, idx) => (
                    <div key={idx} className="flex gap-3 items-center group">
                      <span className="text-xs font-bold text-slate-400 w-5">{idx + 1}.</span>
                      <Input 
                        value={c.nombre}
                        onChange={(e) => updateCompetencia(idx, 'nombre', e.target.value)}
                        placeholder="Ej: Dominio de software CAD, Trabajo bajo presión..."
                        className="flex-grow text-xs py-2"
                      />
                      <Select 
                        value={c.nivel}
                        onChange={(e) => updateCompetencia(idx, 'nivel', e.target.value)}
                        options={[
                          { value: 'Básico', label: 'Básico' },
                          { value: 'Intermedio', label: 'Intermedio' },
                          { value: 'Avanzado', label: 'Avanzado' },
                          { value: 'Experto', label: 'Experto' }
                        ]}
                        className="w-40 text-xs py-2"
                      />
                      <button
                        type="button"
                        onClick={() => removeCompetencia(idx)}
                        className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg opacity-40 group-hover:opacity-100 transition-all"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        )}

        {/* Tab 4: Peligros y EPP */}
        {activeTab === 'peligros' && (
          <div className="space-y-6">

            {/* ─── RESUMEN: Peligros y EPPs Actualmente Asignados ─── */}
            <div className="p-5 rounded-3xl bg-gradient-to-br from-[#002D62] to-slate-900 text-white shadow-xl space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-white/10 rounded-2xl">
                    <Shield className="w-6 h-6 text-[#F5A800]" />
                  </div>
                  <div>
                    <h3 className="font-black text-sm">Peligros y EPP Asignados a este Cargo</h3>
                    <p className="text-[10px] text-slate-300 mt-0.5">Resumen en tiempo real de los factores de riesgo y elementos de protección configurados.</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleAutoSugerirPeligrosYEPPs}
                  disabled={isSugerirPeligrosLoading}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-[#F5A800] hover:bg-[#e09800] text-[#002D62] text-xs font-black shadow transition whitespace-nowrap"
                >
                  {isSugerirPeligrosLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                  Auto-identificar según "{nombreCargo || 'Cargo'}"
                </button>
              </div>

              {/* Peligros Asignados */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-[10px] font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                    <ShieldAlert className="w-3.5 h-3.5 text-amber-400" /> Peligros GTC 45 Identificados ({selectedPeligros.length})
                  </h4>
                  {selectedPeligros.length > 0 && (
                    <button
                      type="button"
                      onClick={() => setSelectedPeligros([])}
                      className="text-[10px] text-slate-400 hover:text-red-300 transition"
                    >
                      Limpiar peligros
                    </button>
                  )}
                </div>
                {selectedPeligros.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {selectedPeligros.map(pId => {
                      const pInfo = getPeligroDisplay(pId)
                      return (
                        <div key={pId} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white/10 rounded-xl border border-white/15 text-xs group hover:bg-white/15 transition">
                          <span className="w-2 h-2 rounded-full bg-amber-400 flex-shrink-0" />
                          <span className="font-bold text-white">{pInfo.clasificacion}</span>
                          <span className="text-[10px] text-amber-200/80">({pInfo.tipo})</span>
                          <button
                            type="button"
                            onClick={() => togglePeligro(pId)}
                            className="ml-1 p-0.5 rounded hover:bg-red-500/30 text-slate-400 hover:text-red-300 transition"
                            title="Quitar este peligro"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">Ningún peligro seleccionado. Use la lista desplegable o el catálogo para agregar.</p>
                )}
              </div>

              {/* EPPs Asignados */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-[10px] font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                    <Check className="w-3.5 h-3.5 text-emerald-400" /> Elementos de Protección Personal Asignados ({selectedEpps.length + customEpps.length})
                  </h4>
                  {(selectedEpps.length > 0 || customEpps.length > 0) && (
                    <button
                      type="button"
                      onClick={() => { setSelectedEpps([]); setCustomEpps([]); }}
                      className="text-[10px] text-slate-400 hover:text-red-300 transition"
                    >
                      Limpiar EPPs
                    </button>
                  )}
                </div>
                {(selectedEpps.length > 0 || customEpps.length > 0) ? (
                  <div className="flex flex-wrap gap-2">
                    {selectedEpps.map(eId => {
                      const eInfo = getEppDisplay(eId)
                      return (
                        <div key={eId} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white/10 rounded-xl border border-white/15 text-xs group hover:bg-white/15 transition">
                          <span className="w-2 h-2 rounded-full bg-emerald-400 flex-shrink-0" />
                          <span className="font-bold text-white">{eInfo.nombre}</span>
                          <button
                            type="button"
                            onClick={() => toggleEpp(eId)}
                            className="ml-1 p-0.5 rounded hover:bg-red-500/30 text-slate-400 hover:text-red-300 transition"
                            title="Quitar este EPP"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      )
                    })}
                    {customEpps.map((ce, idx) => (
                      <div key={idx} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/20 rounded-xl border border-emerald-400/30 text-xs text-emerald-100 group">
                        <span className="w-2 h-2 rounded-full bg-emerald-400 flex-shrink-0" />
                        <span className="font-bold">{ce}</span>
                        <span className="text-[9px] text-emerald-300 font-semibold">(Personalizado)</span>
                        <button
                          type="button"
                          onClick={() => setCustomEpps(prev => prev.filter((_, i) => i !== idx))}
                          className="ml-1 p-0.5 rounded hover:bg-red-500/30 text-slate-400 hover:text-red-300 transition"
                          title="Quitar este EPP personalizado"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">Ningún EPP asignado. Al seleccionar peligros, los EPP sugeridos se añaden automáticamente.</p>
                )}
              </div>

              {/* ── Listas Desplegables para Agregar Rápido ── */}
              <div className="pt-4 border-t border-white/15 grid grid-cols-1 md:grid-cols-2 gap-4">
                
                {/* Desplegable Peligros GTC 45 */}
                <div className="space-y-1.5">
                  <label className="text-[11px] font-bold text-amber-300 flex items-center gap-1">
                    <Plus className="w-3.5 h-3.5" /> Agregar Peligro GTC 45 (Lista Desplegable)
                  </label>
                  <select
                    defaultValue=""
                    onChange={(e) => {
                      const val = e.target.value
                      if (val) {
                        togglePeligro(val)
                        e.target.value = ''
                      }
                    }}
                    className="w-full px-3 py-2.5 rounded-xl bg-white/10 border border-white/20 text-white text-xs focus:outline-none focus:ring-2 focus:ring-[#F5A800] [&>optgroup]:bg-[#002D62] [&>optgroup]:text-amber-300 [&>optgroup]:font-bold [&>option]:bg-slate-900 [&>option]:text-white"
                  >
                    <option value="" disabled className="text-slate-400">Seleccione un peligro para agregar...</option>
                    {catalogoPeligros && Object.entries(catalogoPeligros).map(([grupo, list]) => (
                      <optgroup key={grupo} label={`── ${grupo.toUpperCase()} ──`}>
                        {list.map((p: any) => {
                          const isAlreadySelected = selectedPeligros.some(id => String(id) === String(p.id))
                          return (
                            <option key={p.id} value={p.id} disabled={isAlreadySelected}>
                              {isAlreadySelected ? `[Asignado] ${p.clasificacion}` : p.clasificacion}
                            </option>
                          )
                        })}
                      </optgroup>
                    ))}
                  </select>
                </div>

                {/* Desplegable EPPs Normativos */}
                <div className="space-y-1.5">
                  <label className="text-[11px] font-bold text-emerald-300 flex items-center gap-1">
                    <Plus className="w-3.5 h-3.5" /> Agregar EPP Normativo (Lista Desplegable)
                  </label>
                  <select
                    defaultValue=""
                    onChange={(e) => {
                      const val = e.target.value
                      if (val) {
                        toggleEpp(val)
                        e.target.value = ''
                      }
                    }}
                    className="w-full px-3 py-2.5 rounded-xl bg-white/10 border border-white/20 text-white text-xs focus:outline-none focus:ring-2 focus:ring-emerald-400 [&>optgroup]:bg-[#002D62] [&>optgroup]:text-emerald-300 [&>optgroup]:font-bold [&>option]:bg-slate-900 [&>option]:text-white"
                  >
                    <option value="" disabled className="text-slate-400">Seleccione un EPP según la necesidad...</option>
                    {eppsAgrupadosPorTipo && Object.entries(eppsAgrupadosPorTipo).map(([categoria, list]) => (
                      <optgroup key={categoria} label={`── ${categoria.toUpperCase()} ──`}>
                        {list.map((e: any) => {
                          const isAlreadySelected = selectedEpps.some(id => String(id) === String(e.id))
                          return (
                            <option key={e.id} value={e.id} disabled={isAlreadySelected}>
                              {isAlreadySelected ? `[Asignado] ${e.nombre}` : e.nombre}
                            </option>
                          )
                        })}
                      </optgroup>
                    ))}
                  </select>
                </div>

              </div>

              {/* EPP Personalizado */}
              <div className="pt-3 border-t border-white/10">
                <h4 className="text-[10px] font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1">
                  <Plus className="w-3.5 h-3.5 text-slate-400" /> Agregar EPP Personalizado (Especial / Marca específica)
                </h4>
                <div className="flex gap-2">
                  <input
                    id="custom-epp-input"
                    type="text"
                    placeholder="Ej: Tapaoídos moldeados con protección activa, overol antifluido..."
                    className="flex-grow px-3 py-2 rounded-xl bg-white/10 border border-white/15 text-white placeholder-slate-400 text-xs focus:outline-none focus:ring-2 focus:ring-[#F5A800]/40"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        const val = (e.target as HTMLInputElement).value.trim()
                        if (val) {
                          setCustomEpps(prev => [...prev, val]);
                          (e.target as HTMLInputElement).value = ''
                        }
                      }
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => {
                      const input = document.getElementById('custom-epp-input') as HTMLInputElement
                      if (input && input.value.trim()) {
                        setCustomEpps(prev => [...prev, input.value.trim()])
                        input.value = ''
                      }
                    }}
                    className="px-3.5 py-2 rounded-xl bg-white/15 hover:bg-white/25 border border-white/20 text-white text-xs font-bold transition flex items-center gap-1"
                  >
                    <Plus className="w-4 h-4" /> Agregar
                  </button>
                </div>
              </div>
            </div>

            {/* ─── CATÁLOGO: Peligros GTC-45 para Agregar ─── */}
            <Card
              title="Catálogo de Peligros GTC 45"
              subtitle="Seleccione o deseleccione los factores de riesgo. Al marcar un peligro, los EPP sugeridos se asignan automáticamente."
            >
              {catalogoPeligros ? (
                <div className="space-y-6">
                  {Object.entries(catalogoPeligros).map(([grupo, peligros]) => {
                    const selectedInGroup = peligros.filter((p: any) => selectedPeligros.includes(p.id)).length
                    return (
                      <div key={grupo} className="border-b border-surface-2/60 pb-5 last:border-0 last:pb-0">
                        <h4 className="text-xs font-bold text-primary-500 uppercase tracking-wide mb-3 flex items-center gap-1.5">
                          <Layers className="w-4 h-4 text-brand-500" />
                          {grupo}
                          <span className={`text-[10px] font-bold ml-1 px-1.5 py-0.5 rounded ${selectedInGroup > 0 ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-400'}`}>
                            {selectedInGroup} / {peligros.length}
                          </span>
                        </h4>
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                          {peligros.map((p: any) => {
                            const isSelected = selectedPeligros.includes(p.id)
                            return (
                              <div
                                key={p.id}
                                onClick={() => togglePeligro(p.id)}
                                className={`
                                  p-3 rounded-2xl border text-xs cursor-pointer transition-all flex items-start gap-2.5 select-none
                                  ${isSelected
                                    ? 'bg-amber-50/70 border-amber-400 ring-2 ring-amber-500/15 shadow-sm'
                                    : 'bg-white border-surface-2 hover:bg-slate-50'
                                  }
                                `}
                              >
                                <div className={`
                                  w-4 h-4 rounded border mt-0.5 flex-shrink-0 flex items-center justify-center transition-all
                                  ${isSelected ? 'bg-amber-500 border-amber-500 text-white' : 'border-slate-300 bg-white'}
                                `}>
                                  {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                                </div>
                                <div>
                                  <span className="font-bold text-slate-800 block leading-tight">{p.clasificacion}</span>
                                  {p.descripcion && <p className="text-[10px] text-slate-500 mt-1 leading-normal">{p.descripcion}</p>}
                                  {p.epps_sugeridos && p.epps_sugeridos.length > 0 && (
                                    <span className="inline-flex items-center gap-1 mt-1.5 text-[9px] text-[#002D62] font-semibold bg-blue-50 px-1.5 py-0.5 rounded border border-blue-100">
                                      <Shield className="w-3 h-3 text-primary-500" />
                                      {p.epps_sugeridos.length} EPP sugeridos
                                    </span>
                                  )}
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <LoadingSpinner text="Cargando catálogo de peligros GTC 45..." />
              )}
            </Card>

            {/* ─── CATÁLOGO: EPPs para Agregar ─── */}
            <Card
              title="Catálogo de Elementos de Protección Personal"
              subtitle="Seleccione o deseleccione EPP adicionales que requiera este cargo."
              action={
                <span className="text-[11px] font-bold text-slate-600 bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200">
                  {selectedEpps.length} del catálogo + {customEpps.length} personalizados
                </span>
              }
            >
              {catalogoEpps ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {catalogoEpps.map((e: any) => {
                    const isSelected = selectedEpps.includes(e.id)
                    return (
                      <div
                        key={e.id}
                        onClick={() => toggleEpp(e.id)}
                        className={`
                          p-3 rounded-2xl border text-xs cursor-pointer transition-all flex items-start gap-2.5 select-none
                          ${isSelected
                            ? 'bg-primary-50/70 border-primary-400 ring-2 ring-primary-500/15 shadow-sm'
                            : 'bg-white border-surface-2 hover:bg-slate-50'
                          }
                        `}
                      >
                        <div className={`
                          w-4 h-4 rounded border mt-0.5 flex-shrink-0 flex items-center justify-center transition-all
                          ${isSelected ? 'bg-[#002D62] border-[#002D62] text-white' : 'border-slate-300 bg-white'}
                        `}>
                          {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                        </div>
                        <div>
                          <span className="font-bold text-slate-800 block leading-tight">{e.nombre}</span>
                          {e.descripcion && <p className="text-[10px] text-slate-500 mt-1 leading-normal">{e.descripcion}</p>}
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <LoadingSpinner text="Cargando catálogo de EPP..." />
              )}
            </Card>
          </div>
        )}

        {/* Tab 5: Indicadores */}
        {activeTab === 'indicadores' && (
          <Card 
            title="Indicadores de Gestión del Cargo" 
            subtitle="Define metas cuantitativas para medir la efectividad en este rol."
            action={
              <Button onClick={addIndicador} variant="ghost" className="flex items-center gap-1.5 py-1 text-xs bg-slate-50 border border-slate-200">
                <Plus className="w-3.5 h-3.5" /> Agregar Indicador
              </Button>
            }
          >
            {indicadoresList.length === 0 ? (
              <div className="py-6 text-center text-xs text-slate-400 italic">No se han definido indicadores para este perfil de cargo.</div>
            ) : (
              <div className="space-y-3">
                {indicadoresList.map((i, idx) => (
                  <div key={idx} className="flex gap-3 items-center group">
                    <span className="text-xs font-bold text-slate-400 w-5">{idx + 1}.</span>
                    <Input 
                      value={i.descripcion}
                      onChange={(e) => updateIndicador(idx, 'descripcion', e.target.value)}
                      placeholder="Ej: Cumplimiento mensual de capacitaciones programadas..."
                      className="flex-grow text-xs py-2"
                    />
                    <Input 
                      value={i.meta}
                      onChange={(e) => updateIndicador(idx, 'meta', e.target.value)}
                      placeholder="Ej: >= 90%"
                      className="w-40 text-xs py-2"
                    />
                    <button
                      type="button"
                      onClick={() => removeIndicador(idx)}
                      className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg opacity-40 group-hover:opacity-100 transition-all"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </Card>
        )}

        {/* Control de Versión al Editar */}
        {isEdit && (
          <Card title="Control de Historial y Versiones" className="bg-brand-50/10 border-brand-200">
            <div className="space-y-2">
              <div className="flex items-center gap-2 mb-1">
                <Badge variant="orange">Control de Cambios</Badge>
                <span className="text-[10px] text-slate-500">Se incrementará la versión a v{(perfilData?.version_actual || 1) + 1} de confirmarse cambios significativos.</span>
              </div>
              <FormField label="Motivo de las Modificaciones" required>
                <Textarea 
                  value={motivoCambio}
                  onChange={(e) => setMotivoCambio(e.target.value)}
                  placeholder="Justifique el motivo de los cambios para los registros de auditoría y actas del SG-SST (Ej: Actualización de requisitos académicos y asignación de nuevos EPPs)."
                  className="min-h-[80px] border-brand-300/60 focus:border-brand-500"
                />
              </FormField>
            </div>
          </Card>
        )}

        {/* Form Actions */}
        <div className="flex justify-end gap-3 pt-4">
          <Button 
            onClick={() => navigate('/app/responsable/perfiles-cargo')}
            variant="ghost"
            disabled={createMutation.isPending || updateMutation.isPending}
          >
            Cancelar
          </Button>
          <Button 
            type="submit" 
            variant="primary"
            disabled={createMutation.isPending || updateMutation.isPending}
            className="flex items-center gap-2 bg-gradient-to-tr from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-700 text-slate-950 text-white shadow-lg shadow-brand-500/10"
          >
            {createMutation.isPending || updateMutation.isPending ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            {isEdit ? 'Actualizar Cargo' : 'Registrar Cargo'}
          </Button>
        </div>

      </form>

      {/* ── AI Assistant Stream Modal ─────────────────────────────────── */}
      <Modal
        open={aiModalOpen}
        onClose={() => { if (!isAiStreaming) setAiModalOpen(false) }}
        title={`Asistente IA: Generar ${aiField === 'proposito' ? 'Propósito' : aiField === 'funciones' ? 'Funciones' : 'Responsabilidades'}`}
        maxWidth="600px"
        footer={
          <div className="flex gap-2">
            <Button onClick={() => setAiModalOpen(false)} disabled={isAiStreaming} variant="ghost">
              Cerrar
            </Button>
            {aiStreamResult ? (
              <Button onClick={applyAiResult} disabled={isAiStreaming} variant="primary" icon={Sparkles} className="bg-brand-500 hover:bg-brand-600 text-slate-950 font-bold">
                Aplicar Propuesta
              </Button>
            ) : (
              <Button onClick={handleAiGenerate} disabled={isAiStreaming || !aiCargoName.trim()} variant="primary" icon={Sparkles} className="bg-brand-500 hover:bg-brand-600 text-slate-950 font-bold">
                Comenzar Generación
              </Button>
            )}
          </div>
        }
      >
        <div className="space-y-4">
          <FormField label="Nombre del Cargo" required>
            <Input 
              value={aiCargoName}
              onChange={(e) => setAiCargoName(e.target.value)}
              placeholder="Ej: Supervisor de Logística"
              disabled={isAiStreaming}
            />
          </FormField>

          <FormField label="Contexto Adicional o Indicaciones (Opcional)">
            <Textarea 
              value={aiContext}
              onChange={(e) => setAiContext(e.target.value)}
              placeholder="Ej: Enfocado en control de inventarios, reportará a gerencia de operaciones, requiere manejar montacargas."
              disabled={isAiStreaming}
              className="min-h-[70px]"
            />
          </FormField>

          {/* Stream Result Box */}
          {(aiStreamResult || isAiStreaming) && (
            <div className="space-y-1.5 mt-2">
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wide flex items-center gap-1">
                <BrainCircuit className={`w-3.5 h-3.5 text-brand-600 ${isAiStreaming ? 'animate-bounce' : ''}`} />
                {isAiStreaming ? 'Generando propuesta en tiempo real...' : 'Propuesta Generada'}
              </label>
              <div 
                className={`
                  p-4 rounded-xl border max-h-60 overflow-y-auto text-xs leading-relaxed bg-slate-50 text-slate-700 whitespace-pre-wrap transition-all duration-300
                  ${isAiStreaming ? 'border-brand-400 ring-2 ring-brand-500/10 shadow-lg shadow-brand-500/5 animate-pulse' : 'border-surface-2'}
                `}
              >
                {aiStreamResult || <span className="text-slate-400 italic">Esperando stream de respuesta...</span>}
              </div>
            </div>
          )}
        </div>
      </Modal>
    </div>
  )
}
