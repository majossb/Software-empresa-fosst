import React, { useState, useRef, useEffect, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { modulo0Service, Proceso, EmpresaContexto } from '@/services/modulo0.service'
import { Card, Button } from '@/components/ui'
import { Input } from '@/components/ui/forms'
import { useBranding, resolveMapColors } from '@/store/branding.context'
import { contrastText } from '@/utils/color.utils'
import { getLogoDataUrl, printExportSheet, exportSheetToPNG } from '@/components/ui/ExportSheet'
import type { ExportSheetConfig } from '@/components/ui/ExportSheet'
import {
  Workflow, Plus, Trash2, Edit2, Sparkles, AlertTriangle, X,
  Check, Loader2, Map as MapIcon, Download, Printer,
  ShieldCheck, LayoutGrid, Palette, Sliders, ArrowRight,
  RotateCcw, Compass, Target, Wrench, Layers, RefreshCw, ChevronDown
} from 'lucide-react'

// ── Plantillas Estándar SG-SST ──
export interface PlantillaProcesoItem {
  nombre: string
  tipo: 'estrategico' | 'misional' | 'apoyo'
  descripcion: string
  subprocesos?: string[]
}

export interface PlantillaDef {
  id: string
  nombre: string
  descripcion: string
  procesos: PlantillaProcesoItem[]
}

export const PLANTILLAS_SGSST: PlantillaDef[] = [
  {
    id: 'estandar',
    nombre: 'Estándar SG-SST (Decreto 1072 / Res. 0312 de 2019)',
    descripcion: 'Estructura integral de 12 procesos clave para empresas de 11 a 50+ trabajadores.',
    procesos: [
      {
        nombre: 'Direccionamiento Estratégico y Liderazgo SST',
        tipo: 'estrategico',
        descripcion: 'Definición de política, objetivos y asignación de recursos anuales.',
        subprocesos: ['Política y Objetivos SST', 'Rendición de Cuentas', 'Asignación de Recursos Anuales']
      },
      {
        nombre: 'Auditoría y Revisión por la Alta Dirección',
        tipo: 'estrategico',
        descripcion: 'Evaluación periódica del cumplimiento del SG-SST y planes de mejora.',
        subprocesos: ['Auditoría Interna del SG-SST', 'Revisión por la Dirección', 'Planes Correctivos']
      },
      {
        nombre: 'Identificación de Peligros y Valoración de Riesgos',
        tipo: 'misional',
        descripcion: 'Metodología GTC 45, inspecciones de seguridad y controles jerárquicos.',
        subprocesos: ['Matriz GTC 45', 'Inspecciones Planeadas', 'Jerarquía de Controles']
      },
      {
        nombre: 'Medicina Preventiva y Vigilancia Epidemiológica',
        tipo: 'misional',
        descripcion: 'Evaluaciones médicas ocupacionales y sistemas SVE.',
        subprocesos: ['Profesiogramas y Exámenes', 'Sistemas SVE']
      },
      {
        nombre: 'Control Operacional y Tareas de Alto Riesgo',
        tipo: 'misional',
        descripcion: 'Permisos de trabajo seguro en alturas, confinados, caliente.',
        subprocesos: ['Permisos de Trabajo', 'Análisis ATS', 'Inspección de EPP']
      },
      {
        nombre: 'Preparación y Respuesta ante Emergencias',
        tipo: 'misional',
        descripcion: 'Plan de emergencias, brigadas, señalización y simulacros.',
        subprocesos: ['Plan de Emergencias', 'Capacitación Brigadistas', 'Simulacros']
      },
      {
        nombre: 'Formación, Inducción y Competencias SST',
        tipo: 'apoyo',
        descripcion: 'Plan anual de capacitación e inducción.',
        subprocesos: ['Inducción en SST', 'Plan Anual de Capacitación']
      },
      {
        nombre: 'Gestión Documental y Control de Evidencias',
        tipo: 'apoyo',
        descripcion: 'Custodia, retención por 20 años y control de versiones.',
        subprocesos: ['Control de Registros', 'Custodia de Historias Ocupacionales']
      }
    ]
  },
  {
    id: 'alto_riesgo',
    nombre: 'Sector Industrial / Construcción / Alto Riesgo',
    descripcion: 'Enfocado en control estricto de energías, frentes de obra y tareas críticas.',
    procesos: [
      {
        nombre: 'Gobierno Corporativo y Cultura de Seguridad',
        tipo: 'estrategico',
        descripcion: 'Liderazgo en campo y comités de seguridad.',
        subprocesos: ['Liderazgo Visible', 'Comités de Seguridad']
      },
      {
        nombre: 'Gestión de Riesgos Críticos',
        tipo: 'misional',
        descripcion: 'Control exhaustivo de tareas críticas (alturas, izaje, excavaciones).',
        subprocesos: ['Permisos de Trabajo Crítico', 'Procedimientos POE']
      },
      {
        nombre: 'Mantenimiento e Inspecciones Técnicas',
        tipo: 'apoyo',
        descripcion: 'Certificación de maquinaria pesada y calibración.',
        subprocesos: ['Certificación de Equipos', 'Calibración de Instrumentos']
      }
    ]
  }
]

const normalizarStr = (str: string) =>
  str
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()

export default function ProcesosView() {
  const queryClient = useQueryClient()
  const { branding, updateBranding } = useBranding()
  const mapRef = useRef<HTMLDivElement>(null)

  const [viewMode, setViewMode] = useState<'mapa' | 'tarjetas'>('mapa')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingProceso, setEditingProceso] = useState<Proceso | null>(null)
  const [selectedProcessDetail, setSelectedProcessDetail] = useState<Proceso | null>(null)

  const [showCustomizer, setShowCustomizer] = useState(false)
  const [customizerTab, setCustomizerTab] = useState<'colores' | 'entradas_salidas'>('colores')
  const [showTemplates, setShowTemplates] = useState(false)
  const [showIaModal, setShowIaModal] = useState(false)
  const [showActionsMenu, setShowActionsMenu] = useState(false)
  const actionsMenuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (actionsMenuRef.current && !actionsMenuRef.current.contains(e.target as Node)) {
        setShowActionsMenu(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // New item inputs in customizer
  const [newEntradaItem, setNewEntradaItem] = useState('')
  const [newSalidaItem, setNewSalidaItem] = useState('')

  // Form fields
  const [nombre, setNombre] = useState('')
  const [tipo, setTipo] = useState<'estrategico' | 'misional' | 'apoyo'>('estrategico')
  const [descripcion, setDescripcion] = useState('')
  const [errorMsg, setErrorMsg] = useState('')

  // Resuelve dinámicamente los colores y textos del mapa
  const resolved = useMemo(() => resolveMapColors(branding, branding.mapa_procesos), [branding])
  const estrategicoColor = resolved.estrategico
  const misionalColor = resolved.misional
  const apoyoColor = resolved.apoyo
  const entradasColor = resolved.entradas
  const salidasColor = resolved.salidas
  const fondoColor = resolved.fondo
  const textoEntradas = resolved.texto_entradas
  const textoSalidas = resolved.texto_salidas
  const entradasItems = resolved.entradas_items
  const salidasItems = resolved.salidas_items

  // Consultas
  const { data: empresa } = useQuery<EmpresaContexto>({
    queryKey: ['modulo0', 'contexto'],
    queryFn: modulo0Service.getContexto,
    staleTime: 60_000,
  })

  const { data: rawProcesos, isLoading } = useQuery({
    queryKey: ['modulo0', 'procesos'],
    queryFn: modulo0Service.listProcesos,
    staleTime: 60_000,
  })

  const mapaProcesos = useMemo(() => {
    const p = rawProcesos as any
    return {
      estrategico: Array.isArray(p?.estrategico) ? (p.estrategico as Proceso[]) : [],
      misional: Array.isArray(p?.misional) ? (p.misional as Proceso[]) : [],
      apoyo: Array.isArray(p?.apoyo) ? (p.apoyo as Proceso[]) : [],
    }
  }, [rawProcesos])

  const totalProcesos = mapaProcesos.estrategico.length + mapaProcesos.misional.length + mapaProcesos.apoyo.length

  // Conjunto de claves de procesos existentes para cálculo de plantillas
  const existingProcessKeys = useMemo(() => {
    const keys = new Set<string>()
    const flatProcs = [...mapaProcesos.estrategico, ...mapaProcesos.misional, ...mapaProcesos.apoyo]
    flatProcs.forEach(p => {
      keys.add(`${p.tipo}:${normalizarStr(p.nombre)}`)
    })
    return keys
  }, [mapaProcesos])

  // Mutaciones
  const createMutation = useMutation({
    mutationFn: modulo0Service.createProceso,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modulo0'] })
      closeModal()
    },
    onError: (err: any) => setErrorMsg(err.message || 'Error al crear el proceso.')
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Proceso> }) => modulo0Service.updateProceso(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modulo0'] })
      closeModal()
    },
    onError: (err: any) => setErrorMsg(err.message || 'Error al actualizar el proceso.')
  })

  const deleteMutation = useMutation({
    mutationFn: modulo0Service.deleteProceso,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modulo0'] })
      setSelectedProcessDetail(null)
    },
    onError: (err: any) => alert(err.message || 'No se puede eliminar un proceso con subprocesos activos.')
  })

  const aiSuggestMutation = useMutation({
    mutationFn: modulo0Service.sugerirProcesosIA,
    onSuccess: async (data) => {
      const lista = data?.procesos || []
      const flatProcs = [...mapaProcesos.estrategico, ...mapaProcesos.misional, ...mapaProcesos.apoyo]
      const existingKeys = new Set(flatProcs.map(p => `${p.tipo}:${normalizarStr(p.nombre)}`))

      for (const item of lista) {
        const key = `${item.tipo}:${normalizarStr(item.nombre)}`
        if (!existingKeys.has(key)) {
          try {
            await modulo0Service.createProceso({
              nombre: item.nombre,
              tipo: item.tipo,
              descripcion: item.descripcion
            })
            existingKeys.add(key)
          } catch (e) {
            console.error('Error creando sugerencia:', e)
          }
        }
      }
      queryClient.invalidateQueries({ queryKey: ['modulo0'] })
      setShowIaModal(false)
    },
    onError: (err: any) => {
      setShowIaModal(false)
      setErrorMsg(err?.friendlyMessage || err?.message || 'No se pudieron generar las sugerencias con IA.')
    }
  })

  const importTemplateMutation = useMutation({
    mutationFn: (templateKey: string) => modulo0Service.importarPlantilla(templateKey),
    onSuccess: () => {
      setErrorMsg('')
      queryClient.invalidateQueries({ queryKey: ['modulo0'] })
      setShowTemplates(false)
    },
    onError: (err: any) => {
      setErrorMsg(err?.friendlyMessage || err?.message || 'Error al importar la plantilla.')
    }
  })

  const openAddModal = (defaultTipo: 'estrategico' | 'misional' | 'apoyo' = 'estrategico') => {
    setEditingProceso(null)
    setNombre('')
    setTipo(defaultTipo)
    setDescripcion('')
    setErrorMsg('')
    setModalOpen(true)
  }

  const openEditModal = (proc: Proceso) => {
    setEditingProceso(proc)
    setNombre(proc.nombre)
    setTipo(proc.tipo)
    setDescripcion(proc.descripcion || '')
    setErrorMsg('')
    setModalOpen(true)
  }

  const closeModal = () => {
    setModalOpen(false)
    setEditingProceso(null)
    setErrorMsg('')
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!nombre.trim()) {
      setErrorMsg('El nombre del proceso es obligatorio.')
      return
    }
    if (editingProceso) {
      updateMutation.mutate({
        id: editingProceso.id,
        data: { nombre: nombre.trim(), tipo, descripcion: descripcion.trim() || null }
      })
    } else {
      createMutation.mutate({
        nombre: nombre.trim(),
        tipo,
        descripcion: descripcion.trim() || null
      })
    }
  }

  const handleUpdateBrandingMap = (key: string, value: any) => {
    updateBranding({
      mapa_procesos: {
        ...(branding.mapa_procesos || {}),
        [key]: value
      }
    })
  }

  const handleResetColor = (key: 'estrategico' | 'misional' | 'apoyo' | 'entradas' | 'salidas' | 'fondo') => {
    const updated = { ...(branding.mapa_procesos || {}) }
    delete updated[key]
    updateBranding({ mapa_procesos: updated })
  }

  const handleRestoreAllBranding = () => {
    updateBranding({
      mapa_procesos: {
        estrategico: null,
        misional: null,
        apoyo: null,
        entradas: null,
        salidas: null,
        fondo: null,
        texto_entradas: 'Requisitos Legales y de Partes Interesadas (Dec. 1072 / Res. 0312 de 2019)',
        texto_salidas: 'Lugares de Trabajo Seguros, Saludables y Sostenibles',
        entradas_items: [
          'Requisitos del cliente y partes interesadas',
          'Normatividad legal vigente (Dec. 1072 / Res. 0312 de 2019)',
          'Identificación de peligros y valoración de riesgos'
        ],
        salidas_items: [
          'Ambientes de trabajo seguros y saludables',
          'Control de riesgos y prevención de accidentes',
          'Satisfacción y bienestar integral de los trabajadores'
        ]
      }
    })
  }

  // Items handlers
  const handleAddEntradaItem = () => {
    if (!newEntradaItem.trim()) return
    const updated = [...entradasItems, newEntradaItem.trim()]
    handleUpdateBrandingMap('entradas_items', updated)
    setNewEntradaItem('')
  }

  const handleRemoveEntradaItem = (index: number) => {
    const updated = entradasItems.filter((_item: string, i: number) => i !== index)
    handleUpdateBrandingMap('entradas_items', updated)
  }

  const handleAddSalidaItem = () => {
    if (!newSalidaItem.trim()) return
    const updated = [...salidasItems, newSalidaItem.trim()]
    handleUpdateBrandingMap('salidas_items', updated)
    setNewSalidaItem('')
  }

  const handleRemoveSalidaItem = (index: number) => {
    const updated = salidasItems.filter((_item: string, i: number) => i !== index)
    handleUpdateBrandingMap('salidas_items', updated)
  }

  /**
   * Aplica estilos computados inline a cada elemento del clon del mapa.
   * Recorre el DOM original (donde Tailwind ya resolvió las clases) y copia
   * las propiedades CSS críticas como style inline en el clon, para que
   * el HTML sea autosuficiente sin necesidad de hojas de estilo externas.
   */
  const applyComputedInlineStyles = (src: Element, dst: Element) => {
    if (!(src instanceof HTMLElement) || !(dst instanceof HTMLElement)) return

    const cs = window.getComputedStyle(src)
    const props = [
      // Layout
      'display', 'flexDirection', 'flexWrap', 'alignItems', 'justifyContent',
      'gap', 'rowGap', 'columnGap',
      'gridTemplateColumns', 'gridTemplateRows', 'gridColumn', 'gridRow',
      // Box model
      'padding', 'paddingTop', 'paddingRight', 'paddingBottom', 'paddingLeft',
      'margin', 'marginTop', 'marginRight', 'marginBottom', 'marginLeft',
      'width', 'minWidth', 'maxWidth', 'height', 'minHeight', 'maxHeight',
      // Visual
      'backgroundColor', 'backgroundImage', 'background',
      'border', 'borderRadius',
      'borderTopWidth', 'borderTopStyle', 'borderTopColor',
      'borderRightWidth', 'borderRightStyle', 'borderRightColor',
      'borderBottomWidth', 'borderBottomStyle', 'borderBottomColor',
      'borderLeftWidth', 'borderLeftStyle', 'borderLeftColor',
      'boxShadow', 'clipPath', 'overflow', 'opacity',
      // Typography
      'color', 'fontSize', 'fontWeight', 'fontFamily', 'lineHeight',
      'letterSpacing', 'textTransform', 'textAlign', 'whiteSpace',
      // Position
      'position', 'top', 'right', 'bottom', 'left', 'zIndex',
      'flexShrink', 'flexGrow',
    ]

    const existing = dst.getAttribute('style') || ''
    const additions: string[] = []
    for (const prop of props) {
      try {
        const val = (cs as any)[prop]
        if (val == null || val === '') continue
        // Convertir camelCase a kebab-case para CSS
        const kebab = prop.replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`)
        // No sobreescribir estilos ya presentes (los inline originales)
        if (existing.includes(kebab)) continue
        additions.push(`${kebab}:${val}`)
      } catch (_) {}
    }
    if (additions.length > 0) {
      dst.setAttribute('style', existing + (existing ? ';' : '') + additions.join(';'))
    }

    // Recursar en hijos
    const srcChildren = src.children
    const dstChildren = dst.children
    for (let i = 0; i < Math.min(srcChildren.length, dstChildren.length); i++) {
      applyComputedInlineStyles(srcChildren[i], dstChildren[i])
    }
  }

  /**
   * Construye la configuración del ExportSheet a partir de empresa + branding + mapa DOM.
   * Convierte el logo a data URL y aplica estilos computados inline al clon del mapa
   * para que se renderice correctamente incluso sin CSS externo.
   */
  const buildExportConfig = async (): Promise<ExportSheetConfig | null> => {
    if (!mapRef.current) return null

    const logoDataUrl = await getLogoDataUrl(empresa?.logo_url)

    // Clonar el mapa para no alterar el DOM visible
    const mapClone = mapRef.current.cloneNode(true) as HTMLElement

    // Aplicar todos los estilos computados como inline en el clon
    applyComputedInlineStyles(mapRef.current, mapClone)

    return {
      title: 'Mapa de Procesos Organizacional',
      subtitle: 'Según ISO 45001, ISO 9001, Dec. 1072 de 2015 y Res. 0312 de 2019',
      empresaNombre: empresa?.nombre || 'EMPRESA REGISTRADA',
      empresaNit: empresa?.nit,
      logoDataUrl,
      primaryColor: branding.primario || '#002D62',
      secondaryColor: branding.secundario || '#0284C7',
      accentColor: branding.acento || '#F5A800',
      mapInnerHTML: mapClone.outerHTML,
    }
  }

  const exportMapPNG = async () => {
    const cfg = await buildExportConfig()
    if (!cfg) return
    await exportSheetToPNG(cfg, `Mapa_Procesos_Organizacional_${new Date().toISOString().slice(0, 10)}.png`)
  }

  const printMap = async () => {
    const cfg = await buildExportConfig()
    if (!cfg) return
    await printExportSheet(cfg)
  }

  const renderProcessCard = (proc: Proceso, categoryColor: string) => (
    <div
      key={proc.id}
      className="p-4 rounded-xl bg-white border border-slate-200 border-l-4 shadow-xs hover:shadow-md transition-all space-y-2.5 flex flex-col justify-between"
      style={{ borderLeftColor: categoryColor }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="space-y-1">
          <h4 className="text-xs font-bold text-slate-850 leading-snug">{proc.nombre}</h4>
          {proc.descripcion && (
            <p className="text-[11px] text-slate-500 line-clamp-2 leading-relaxed">{proc.descripcion}</p>
          )}
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          <button
            onClick={() => openEditModal(proc)}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition"
            title="Editar proceso"
          >
            <Edit2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => {
              if (confirm(`¿Eliminar el proceso "${proc.nombre}"?`)) deleteMutation.mutate(proc.id)
            }}
            className="p-1 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition"
            title="Eliminar proceso"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {proc.subprocesos && proc.subprocesos.length > 0 && (
        <div className="pt-2 border-t border-slate-100 space-y-1">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Subprocesos:</span>
          <div className="flex flex-wrap gap-1">
            {proc.subprocesos.map((sub) => (
              <span key={sub.id} className="text-[10px] px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 font-semibold border border-slate-200">
                {sub.nombre}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )

  const renderMapBandCard = (proc: Proceso, categoryColor: string) => (
    <div
      key={proc.id}
      onClick={() => setSelectedProcessDetail(proc)}
      className="p-3.5 rounded-xl bg-white border border-slate-200 border-t-4 shadow-xs hover:shadow-md transition-all cursor-pointer space-y-2 flex flex-col justify-between"
      style={{ borderTopColor: categoryColor }}
    >
      <div className="font-bold text-xs text-slate-800 leading-snug">{proc.nombre}</div>
      {proc.subprocesos && proc.subprocesos.length > 0 && (
        <div className="flex flex-wrap gap-1 pt-1">
          {proc.subprocesos.map((sub) => (
            <span key={sub.id} className="text-[9px] font-medium px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
              {sub.nombre}
            </span>
          ))}
        </div>
      )}
    </div>
  )

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
      </div>
    )
  }

  // Lista de colores configurables
  const colorConfigs: { key: 'estrategico' | 'misional' | 'apoyo' | 'entradas' | 'salidas' | 'fondo'; label: string; current: string }[] = [
    { key: 'estrategico', label: 'Procesos Estratégicos', current: estrategicoColor },
    { key: 'misional', label: 'Procesos Misionales', current: misionalColor },
    { key: 'apoyo', label: 'Procesos de Apoyo', current: apoyoColor },
    { key: 'entradas', label: 'Franja Entradas', current: entradasColor },
    { key: 'salidas', label: 'Franja Salidas', current: salidasColor },
    { key: 'fondo', label: 'Fondo del Mapa', current: fondoColor },
  ]

  return (
    <div className="space-y-6 font-sans select-none">
      {/* TOOLBAR PRINCIPAL */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white p-5 rounded-2xl border border-slate-200 shadow-2xs">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-500/10 flex items-center justify-center border border-brand-500/20 text-brand-600 shadow-2xs">
            <Workflow className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-850 tracking-tight">
              Mapa de Procesos Organizacional
            </h1>
            <p className="text-xs text-slate-500">
              Según ISO 45001, ISO 9001, Dec. 1072 de 2015 y Res. 0312 de 2019
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5 flex-nowrap">
          {/* Switcher Fichas / Mapa */}
          <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200 flex-shrink-0">
            <button
              onClick={() => setViewMode('mapa')}
              className={`text-xs px-3 py-1.5 rounded-lg font-bold flex items-center gap-1.5 transition whitespace-nowrap ${
                viewMode === 'mapa' ? 'bg-white text-slate-850 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <MapIcon className="w-3.5 h-3.5" /> Mapa Gráfico
            </button>
            <button
              onClick={() => setViewMode('tarjetas')}
              className={`text-xs px-3 py-1.5 rounded-lg font-bold flex items-center gap-1.5 transition whitespace-nowrap ${
                viewMode === 'tarjetas' ? 'bg-white text-slate-850 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" /> Fichas Operativas
            </button>
          </div>

          {/* Menú Más acciones */}
          <div className="relative flex-shrink-0" ref={actionsMenuRef}>
            <Button
              variant="secondary"
              onClick={() => setShowActionsMenu(!showActionsMenu)}
              className="text-xs h-9 whitespace-nowrap inline-flex items-center gap-1.5"
            >
              <Sliders className="w-4 h-4 text-slate-500" />
              <span>Más acciones</span>
              <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${showActionsMenu ? 'rotate-180' : ''}`} />
            </Button>

            {showActionsMenu && (
              <div className="absolute right-0 mt-1.5 w-52 bg-white rounded-xl shadow-lg border border-slate-200 py-1.5 z-30 animate-fade-in">
                <button
                  type="button"
                  onClick={() => {
                    setShowActionsMenu(false)
                    setShowCustomizer(true)
                    setCustomizerTab('colores')
                  }}
                  className="w-full px-3.5 py-2 text-xs text-left text-slate-700 hover:bg-slate-50 hover:text-slate-900 flex items-center gap-2 font-medium transition whitespace-nowrap"
                >
                  <Sliders className="w-4 h-4 text-slate-500 flex-shrink-0" />
                  <span>Personalizar</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setShowActionsMenu(false)
                    setShowCustomizer(true)
                    setCustomizerTab('entradas_salidas')
                  }}
                  className="w-full px-3.5 py-2 text-xs text-left text-slate-700 hover:bg-slate-50 hover:text-slate-900 flex items-center gap-2 font-medium transition whitespace-nowrap"
                >
                  <Layers className="w-4 h-4 text-brand-600 flex-shrink-0" />
                  <span>Entradas / Salidas</span>
                </button>

                <div className="my-1 border-t border-slate-100" />

                <button
                  type="button"
                  onClick={() => {
                    setShowActionsMenu(false)
                    setShowTemplates(true)
                  }}
                  className="w-full px-3.5 py-2 text-xs text-left text-slate-700 hover:bg-slate-50 hover:text-slate-900 flex items-center gap-2 font-medium transition whitespace-nowrap"
                >
                  <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                  <span>Plantillas SST</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setShowActionsMenu(false)
                    setShowIaModal(true)
                    aiSuggestMutation.mutate()
                  }}
                  disabled={aiSuggestMutation.isPending}
                  className="w-full px-3.5 py-2 text-xs text-left text-slate-700 hover:bg-slate-50 hover:text-slate-900 flex items-center gap-2 font-medium transition whitespace-nowrap"
                >
                  <Sparkles className="w-4 h-4 text-brand-500 flex-shrink-0" />
                  <span>Sugerir con IA</span>
                </button>
              </div>
            )}
          </div>

          {/* Botón Primario: Nuevo Proceso */}
          <Button
            variant="primary"
            onClick={() => openAddModal('estrategico')}
            className="text-xs py-1.5 h-9 whitespace-nowrap flex-shrink-0 inline-flex items-center"
          >
            <Plus className="w-4 h-4 mr-1.5 flex-shrink-0" />
            <span>Nuevo proceso</span>
          </Button>
        </div>
      </div>


      {/* PANEL DE PERSONALIZACIÓN DE MARCA (CON TABS: COLORES Y ENTRADAS/SALIDAS) */}
      {showCustomizer && (
        <Card className="p-5 bg-white border border-slate-200 shadow-md space-y-4 animate-fade-in">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pb-3 border-b border-slate-100">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <Palette className="w-4 h-4 text-brand-500" />
                <h3 className="text-sm font-bold text-slate-800">Personalización del Mapa</h3>
              </div>
              <div className="flex rounded-lg bg-slate-100 p-0.5 border border-slate-200 text-xs">
                <button
                  type="button"
                  onClick={() => setCustomizerTab('colores')}
                  className={`px-3 py-1 rounded-md font-bold transition ${
                    customizerTab === 'colores' ? 'bg-white text-slate-800 shadow-2xs' : 'text-slate-600'
                  }`}
                >
                  Colores ({colorConfigs.filter(c => !!branding.mapa_procesos?.[c.key]).length > 0 ? 'Personalizados' : 'Por Paleta'})
                </button>
                <button
                  type="button"
                  onClick={() => setCustomizerTab('entradas_salidas')}
                  className={`px-3 py-1 rounded-md font-bold transition ${
                    customizerTab === 'entradas_salidas' ? 'bg-white text-slate-800 shadow-2xs' : 'text-slate-600'
                  }`}
                >
                  Entradas y Salidas
                </button>
              </div>
            </div>

            <Button
              variant="ghost"
              onClick={handleRestoreAllBranding}
              className="text-xs py-1 h-8 text-slate-600 hover:text-slate-900 border border-slate-200"
              title="Restablece todos los colores del mapa a la paleta institucional"
            >
              <RotateCcw className="w-3.5 h-3.5 mr-1" /> Restablecer a paleta
            </Button>
          </div>

          {/* TAB 1: COLORES */}
          {customizerTab === 'colores' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
              {colorConfigs.map((cfg) => {
                const isCustom = !!branding.mapa_procesos?.[cfg.key]
                return (
                  <div key={cfg.key} className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-2.5">
                    <div className="flex items-center justify-between">
                      <label className="font-bold text-slate-800">{cfg.label}</label>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          isCustom ? 'bg-amber-100 text-amber-800 border border-amber-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        }`}
                      >
                        {isCustom ? 'Personalizado' : 'Sigue la paleta'}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <input
                        type="color"
                        value={cfg.current}
                        onChange={(e) => handleUpdateBrandingMap(cfg.key, e.target.value)}
                        className="w-8 h-8 rounded-lg border-none cursor-pointer bg-transparent flex-shrink-0"
                      />
                      <input
                        type="text"
                        value={cfg.current}
                        onChange={(e) => handleUpdateBrandingMap(cfg.key, e.target.value)}
                        className="w-full text-xs font-mono font-bold uppercase border border-slate-200 rounded-lg px-2.5 py-1.5 bg-white"
                      />
                      {isCustom && (
                        <button
                          type="button"
                          onClick={() => handleResetColor(cfg.key)}
                          className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-200 rounded-lg transition"
                          title="Volver a derivar automáticamente de la paleta"
                        >
                          <RotateCcw className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {/* TAB 2: ENTRADAS Y SALIDAS */}
          {customizerTab === 'entradas_salidas' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs pt-1">
              {/* Entradas */}
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
                <div className="flex items-center justify-between border-b border-slate-200/80 pb-2">
                  <h4 className="font-bold text-slate-800 text-xs">Franja Izquierda: Entradas</h4>
                  <span className="text-[10px] text-slate-500 font-medium">{entradasItems.length} ítems</span>
                </div>

                <div>
                  <label className="font-bold text-slate-700 block mb-1">Título de la franja:</label>
                  <Input
                    value={textoEntradas}
                    onChange={(e) => handleUpdateBrandingMap('texto_entradas', e.target.value)}
                    placeholder="Ej. Requisitos Legales y de Partes Interesadas"
                    className="bg-white border-slate-200"
                  />
                </div>

                <div className="space-y-2">
                  <label className="font-bold text-slate-700 block">Ítems / Viñetas:</label>
                  <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                    {entradasItems.map((item: string, idx: number) => (
                      <div key={idx} className="flex items-center justify-between gap-2 bg-white px-3 py-1.5 rounded-lg border border-slate-200">
                        <span className="text-xs text-slate-700 leading-tight">• {item}</span>
                        <button
                          type="button"
                          onClick={() => handleRemoveEntradaItem(idx)}
                          className="text-slate-400 hover:text-rose-600 p-0.5 rounded transition"
                          title="Eliminar ítem"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                    {entradasItems.length === 0 && (
                      <div className="text-slate-400 text-xs italic py-1">Sin viñetas agregadas.</div>
                    )}
                  </div>

                  <div className="flex gap-2 pt-1">
                    <Input
                      value={newEntradaItem}
                      onChange={(e) => setNewEntradaItem(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleAddEntradaItem(); } }}
                      placeholder="Nuevo ítem de entrada..."
                      className="bg-white border-slate-200 text-xs"
                    />
                    <Button variant="secondary" onClick={handleAddEntradaItem} className="text-xs py-1.5 h-9 flex-shrink-0">
                      <Plus className="w-3.5 h-3.5 mr-1" /> Agregar
                    </Button>
                  </div>
                </div>
              </div>

              {/* Salidas */}
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
                <div className="flex items-center justify-between border-b border-slate-200/80 pb-2">
                  <h4 className="font-bold text-slate-800 text-xs">Franja Derecha: Salidas</h4>
                  <span className="text-[10px] text-slate-500 font-medium">{salidasItems.length} ítems</span>
                </div>

                <div>
                  <label className="font-bold text-slate-700 block mb-1">Título de la franja:</label>
                  <Input
                    value={textoSalidas}
                    onChange={(e) => handleUpdateBrandingMap('texto_salidas', e.target.value)}
                    placeholder="Ej. Lugares de Trabajo Seguros y Saludables"
                    className="bg-white border-slate-200"
                  />
                </div>

                <div className="space-y-2">
                  <label className="font-bold text-slate-700 block">Ítems / Viñetas:</label>
                  <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                    {salidasItems.map((item: string, idx: number) => (
                      <div key={idx} className="flex items-center justify-between gap-2 bg-white px-3 py-1.5 rounded-lg border border-slate-200">
                        <span className="text-xs text-slate-700 leading-tight">• {item}</span>
                        <button
                          type="button"
                          onClick={() => handleRemoveSalidaItem(idx)}
                          className="text-slate-400 hover:text-rose-600 p-0.5 rounded transition"
                          title="Eliminar ítem"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                    {salidasItems.length === 0 && (
                      <div className="text-slate-400 text-xs italic py-1">Sin viñetas agregadas.</div>
                    )}
                  </div>

                  <div className="flex gap-2 pt-1">
                    <Input
                      value={newSalidaItem}
                      onChange={(e) => setNewSalidaItem(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleAddSalidaItem(); } }}
                      placeholder="Nuevo ítem de salida..."
                      className="bg-white border-slate-200 text-xs"
                    />
                    <Button variant="secondary" onClick={handleAddSalidaItem} className="text-xs py-1.5 h-9 flex-shrink-0">
                      <Plus className="w-3.5 h-3.5 mr-1" /> Agregar
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* VISTA 1: MAPA GRÁFICO TIPO PROCESO */}
      {viewMode === 'mapa' && (
        <div className="space-y-4">
          <div className="flex justify-end gap-2 no-print">
            <Button variant="ghost" onClick={exportMapPNG} className="text-xs py-1.5 bg-white border border-slate-200 text-slate-700 font-bold">
              <Download className="w-4 h-4 text-slate-500 mr-1.5" /> Exportar PNG @2.5x
            </Button>
            <Button variant="ghost" onClick={printMap} className="text-xs py-1.5 bg-white border border-slate-200 text-slate-700 font-bold">
              <Printer className="w-4 h-4 text-slate-500 mr-1.5" /> Imprimir
            </Button>
          </div>

          {/* CANVAS DEL MAPA DE PROCESOS */}
          <div className="p-6 bg-slate-100/60 border border-slate-200 rounded-2xl overflow-x-auto flex justify-center">
            <div
              ref={mapRef}
              id="mapa-procesos-canvas-export"
              className="w-full min-w-[1020px] max-w-[1300px] rounded-2xl border border-slate-300 shadow-md p-6 space-y-5 transition-all"
              style={{ backgroundColor: fondoColor }}
            >
              {/* BANDA 1: PROCESOS ESTRATÉGICOS */}
              <div
                className="p-5 rounded-2xl border border-slate-200/80 space-y-3"
                style={{ background: `linear-gradient(135deg, ${estrategicoColor}0D, ${estrategicoColor}1F)` }}
              >
                <div className="flex items-center gap-2">
                  <span
                    className="px-3 py-1 rounded-lg text-xs font-black uppercase tracking-wider shadow-2xs"
                    style={{ backgroundColor: estrategicoColor, color: contrastText(estrategicoColor) }}
                  >
                    Procesos Estratégicos y Direccionamiento SST
                  </span>
                  <span className="text-xs font-bold text-slate-500 font-mono">({mapaProcesos.estrategico.length})</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3.5">
                  {mapaProcesos.estrategico.map((p) => renderMapBandCard(p, estrategicoColor))}
                  {mapaProcesos.estrategico.length === 0 && (
                    <div className="col-span-full py-4 text-center text-xs text-slate-400 italic">
                      Sin procesos estratégicos registrados.
                    </div>
                  )}
                </div>
              </div>

              {/* SECCIÓN CENTRAL: FLECHA ENTRADAS (col-3) + MISIONALES/APOYO (col-6) + FLECHA SALIDAS (col-3) */}
              <div className="grid grid-cols-12 gap-4 items-stretch">
                {/* FLECHA LATERAL IZQUIERDA: ENTRADAS */}
                <div className="col-span-3 rounded-2xl flex flex-col justify-center relative shadow-md overflow-hidden">
                  {/* Fondo con clip-path independiente */}
                  <div
                    className="absolute inset-0 pointer-events-none"
                    style={{
                      backgroundColor: entradasColor,
                      clipPath: 'polygon(0% 0%, 86% 0%, 100% 50%, 86% 100%, 0% 100%)'
                    }}
                  />
                  {/* Contenido sin clip-path con padding seguro para la forma */}
                  <div
                    className="relative z-10 w-full py-6 pl-6 pr-14 space-y-3"
                    style={{ color: contrastText(entradasColor) }}
                  >
                    <span className="text-[11px] font-black uppercase tracking-wider block opacity-90 border-b border-current/20 pb-1 text-center">
                      Entradas
                    </span>
                    <p className="text-xs font-bold leading-snug text-center">
                      {textoEntradas}
                    </p>
                    {entradasItems.length > 0 && (
                      <ul className="space-y-1.5 pt-1 text-[11px] font-medium leading-relaxed opacity-95">
                        {entradasItems.map((item: string, idx: number) => (
                          <li key={idx} className="flex items-start gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-current flex-shrink-0 mt-1.5 opacity-80" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>

                {/* NÚCLEO CENTRAL: MISIONALES ARRIBA, APOYO ABAJO */}
                <div className="col-span-6 space-y-4">
                  {/* BANDA 2: PROCESOS MISIONALES */}
                  <div
                    className="p-5 rounded-2xl border border-slate-200/80 space-y-3"
                    style={{ background: `linear-gradient(135deg, ${misionalColor}0D, ${misionalColor}1F)` }}
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className="px-3 py-1 rounded-lg text-xs font-black uppercase tracking-wider shadow-2xs"
                        style={{ backgroundColor: misionalColor, color: contrastText(misionalColor) }}
                      >
                        Procesos Misionales / Operativos SG-SST
                      </span>
                      <span className="text-xs font-bold text-slate-500 font-mono">({mapaProcesos.misional.length})</span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-3.5">
                      {mapaProcesos.misional.map((p) => renderMapBandCard(p, misionalColor))}
                      {mapaProcesos.misional.length === 0 && (
                        <div className="col-span-full py-4 text-center text-xs text-slate-400 italic">
                          Sin procesos misionales registrados.
                        </div>
                      )}
                    </div>
                  </div>

                  {/* BANDA 3: PROCESOS DE APOYO */}
                  <div
                    className="p-5 rounded-2xl border border-slate-200/80 space-y-3"
                    style={{ background: `linear-gradient(135deg, ${apoyoColor}0D, ${apoyoColor}1F)` }}
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className="px-3 py-1 rounded-lg text-xs font-black uppercase tracking-wider shadow-2xs"
                        style={{ backgroundColor: apoyoColor, color: contrastText(apoyoColor) }}
                      >
                        Procesos de Apoyo
                      </span>
                      <span className="text-xs font-bold text-slate-500 font-mono">({mapaProcesos.apoyo.length})</span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-3.5">
                      {mapaProcesos.apoyo.map((p) => renderMapBandCard(p, apoyoColor))}
                      {mapaProcesos.apoyo.length === 0 && (
                        <div className="col-span-full py-4 text-center text-xs text-slate-400 italic">
                          Sin procesos de apoyo registrados.
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* FLECHA LATERAL DERECHA: SALIDAS */}
                <div className="col-span-3 rounded-2xl flex flex-col justify-center relative shadow-md overflow-hidden">
                  {/* Fondo con clip-path independiente */}
                  <div
                    className="absolute inset-0 pointer-events-none"
                    style={{
                      backgroundColor: salidasColor,
                      clipPath: 'polygon(0% 0%, 86% 0%, 100% 50%, 86% 100%, 0% 100%, 14% 50%)'
                    }}
                  />
                  {/* Contenido sin clip-path con padding suficiente a la izquierda (evita hendidura) y derecha (evita punta) */}
                  <div
                    className="relative z-10 w-full py-6 pl-14 pr-12 space-y-3"
                    style={{ color: contrastText(salidasColor) }}
                  >
                    <span className="text-[11px] font-black uppercase tracking-wider block opacity-90 border-b border-current/20 pb-1 text-center">
                      Salidas
                    </span>
                    <p className="text-xs font-bold leading-snug text-center">
                      {textoSalidas}
                    </p>
                    {salidasItems.length > 0 && (
                      <ul className="space-y-1.5 pt-1 text-[11px] font-medium leading-relaxed opacity-95">
                        {salidasItems.map((item: string, idx: number) => (
                          <li key={idx} className="flex items-start gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-current flex-shrink-0 mt-1.5 opacity-80" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* VISTA 2: FICHAS OPERATIVAS */}
      {viewMode === 'tarjetas' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          {/* ESTRATÉGICOS */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 space-y-3">
            <div className="flex justify-between items-center pb-2 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: estrategicoColor }} />
                <h3 className="font-bold text-xs text-slate-800 uppercase tracking-wider">Estratégicos</h3>
                <span className="text-[10px] font-bold text-slate-600 bg-white px-2 py-0.5 rounded-md border border-slate-200 font-mono">
                  {mapaProcesos.estrategico.length}
                </span>
              </div>
              <Button variant="ghost" onClick={() => openAddModal('estrategico')} className="p-1 h-7 text-slate-500 hover:text-slate-800">
                <Plus className="w-4 h-4" />
              </Button>
            </div>
            <div className="space-y-3">
              {mapaProcesos.estrategico.map((proc) => renderProcessCard(proc, estrategicoColor))}
              {mapaProcesos.estrategico.length === 0 && (
                <div className="p-6 text-center text-xs text-slate-400 border border-dashed rounded-xl bg-white">
                  Sin procesos estratégicos.
                </div>
              )}
            </div>
          </div>

          {/* MISIONALES */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 space-y-3">
            <div className="flex justify-between items-center pb-2 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: misionalColor }} />
                <h3 className="font-bold text-xs text-slate-800 uppercase tracking-wider">Misionales</h3>
                <span className="text-[10px] font-bold text-slate-600 bg-white px-2 py-0.5 rounded-md border border-slate-200 font-mono">
                  {mapaProcesos.misional.length}
                </span>
              </div>
              <Button variant="ghost" onClick={() => openAddModal('misional')} className="p-1 h-7 text-slate-500 hover:text-slate-800">
                <Plus className="w-4 h-4" />
              </Button>
            </div>
            <div className="space-y-3">
              {mapaProcesos.misional.map((proc) => renderProcessCard(proc, misionalColor))}
              {mapaProcesos.misional.length === 0 && (
                <div className="p-6 text-center text-xs text-slate-400 border border-dashed rounded-xl bg-white">
                  Sin procesos misionales.
                </div>
              )}
            </div>
          </div>

          {/* APOYO */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 space-y-3">
            <div className="flex justify-between items-center pb-2 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: apoyoColor }} />
                <h3 className="font-bold text-xs text-slate-800 uppercase tracking-wider">Apoyo</h3>
                <span className="text-[10px] font-bold text-slate-600 bg-white px-2 py-0.5 rounded-md border border-slate-200 font-mono">
                  {mapaProcesos.apoyo.length}
                </span>
              </div>
              <Button variant="ghost" onClick={() => openAddModal('apoyo')} className="p-1 h-7 text-slate-500 hover:text-slate-800">
                <Plus className="w-4 h-4" />
              </Button>
            </div>
            <div className="space-y-3">
              {mapaProcesos.apoyo.map((proc) => renderProcessCard(proc, apoyoColor))}
              {mapaProcesos.apoyo.length === 0 && (
                <div className="p-6 text-center text-xs text-slate-400 border border-dashed rounded-xl bg-white">
                  Sin procesos de apoyo.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* MODAL FICHA DETALLE DEL PROCESO */}
      {selectedProcessDetail && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fade-in">
          <Card
            title={`Ficha de Proceso — ${selectedProcessDetail.nombre}`}
            subtitle={`Categoría: ${selectedProcessDetail.tipo.toUpperCase()}`}
            className="w-full max-w-lg bg-white border border-slate-200 shadow-2xl relative overflow-hidden"
            action={
              <button onClick={() => setSelectedProcessDetail(null)} className="p-1.5 rounded-xl hover:bg-slate-100 text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            }
          >
            <div className="space-y-4 text-xs mt-2">
              <div>
                <span className="font-bold text-slate-500 block mb-1">Descripción / Alcance:</span>
                <p className="text-slate-800 bg-slate-50 p-3 rounded-xl border border-slate-200 leading-relaxed font-medium">
                  {selectedProcessDetail.descripcion || 'Sin descripción asignada.'}
                </p>
              </div>

              {selectedProcessDetail.subprocesos && selectedProcessDetail.subprocesos.length > 0 && (
                <div className="space-y-2">
                  <span className="font-bold text-slate-500 block">Subprocesos Operativos ({selectedProcessDetail.subprocesos.length}):</span>
                  <div className="space-y-1.5">
                    {selectedProcessDetail.subprocesos.map((sub) => (
                      <div key={sub.id} className="p-2.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center gap-2 text-slate-800 font-semibold">
                        <ArrowRight className="w-3.5 h-3.5 text-brand-500 flex-shrink-0" />
                        <span>{sub.nombre}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 mt-6">
                <Button
                  variant="ghost"
                  onClick={() => {
                    const p = selectedProcessDetail
                    setSelectedProcessDetail(null)
                    openEditModal(p)
                  }}
                  className="text-xs py-2 h-10 border border-slate-200 text-slate-700"
                >
                  Editar Proceso
                </Button>
                <Button variant="primary" onClick={() => setSelectedProcessDetail(null)} className="text-xs py-2 h-10">
                  Cerrar
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* MODAL PLANTILLAS SST */}
      {showTemplates && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fade-in">
          <Card
            title="Plantillas Normativas SG-SST"
            subtitle="Importa estructuras prediseñadas para Decreto 1072 / Res. 0312 de 2019"
            className="w-full max-w-2xl bg-white border border-slate-200 shadow-2xl relative overflow-hidden"
            action={
              <button onClick={() => setShowTemplates(false)} className="p-1.5 rounded-xl hover:bg-slate-100 text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            }
          >
            <div className="space-y-3 mt-3 max-h-[450px] overflow-y-auto pr-1">
              {PLANTILLAS_SGSST.map((t) => {
                const totalProcesosPlantilla = t.procesos.length
                const missingCount = t.procesos.filter(item => {
                  const key = `${item.tipo}:${normalizarStr(item.nombre)}`
                  return !existingProcessKeys.has(key)
                }).length
                const isFullyLoaded = missingCount === 0

                return (
                  <div key={t.id} className="p-4 rounded-xl border border-slate-200 bg-slate-50 hover:bg-white transition flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div className="space-y-1">
                      <h4 className="font-bold text-xs text-slate-850">{t.nombre}</h4>
                      <p className="text-xs text-slate-500">{t.descripcion}</p>
                      <div className="pt-0.5">
                        <span className="text-[11px] font-medium text-slate-600">
                          {isFullyLoaded
                            ? `Plantilla completa (${totalProcesosPlantilla} de ${totalProcesosPlantilla} procesos)`
                            : `Total plantilla: ${totalProcesosPlantilla} procesos • Faltan por cargar: ${missingCount}`
                          }
                        </span>
                      </div>
                    </div>
                    <Button
                      variant={isFullyLoaded ? "secondary" : "primary"}
                      onClick={() => !isFullyLoaded && importTemplateMutation.mutate(t.id)}
                      disabled={importTemplateMutation.isPending || isFullyLoaded}
                      className="text-xs py-2 h-9 flex-shrink-0 whitespace-nowrap"
                    >
                      {importTemplateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-1.5" /> : null}
                      {isFullyLoaded
                        ? 'Ya cargada'
                        : `Agregar ${missingCount} faltantes`
                      }
                    </Button>
                  </div>
                )
              })}
            </div>
          </Card>
        </div>
      )}

      {/* MODAL IA */}
      {showIaModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fade-in">
          <Card
            title="Sugerencia Inteligente de Procesos (IA)"
            subtitle="Estructura sugerida según la actividad económica CIIU de tu empresa"
            className="w-full max-w-md bg-white border border-slate-200 shadow-2xl relative overflow-hidden text-center"
            action={
              <button onClick={() => setShowIaModal(false)} className="p-1.5 rounded-xl hover:bg-slate-100 text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            }
          >
            <div className="py-8 space-y-4">
              <Loader2 className="w-8 h-8 text-brand-500 animate-spin mx-auto" />
              <p className="text-xs font-semibold text-slate-600 leading-relaxed px-4">
                Generando procesos personalizados para tu empresa...
              </p>
            </div>
          </Card>
        </div>
      )}

      {/* MODAL CREAR / EDITAR PROCESO */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fade-in">
          <Card
            title={editingProceso ? 'Editar Proceso' : 'Registrar Nuevo Proceso'}
            className="w-full max-w-md bg-white border border-slate-200 shadow-2xl relative overflow-hidden"
            action={
              <button onClick={closeModal} className="p-1.5 rounded-xl hover:bg-slate-100 text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            }
          >
            <form onSubmit={handleSubmit} className="space-y-4 mt-2">
              {errorMsg && (
                <div className="bg-red-50 border border-red-200 text-red-600 p-3 rounded-xl flex items-center gap-2 text-xs font-semibold">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                  <span>{errorMsg}</span>
                </div>
              )}

              <div>
                <label className="text-xs font-semibold text-slate-600 block mb-1">Nombre del Proceso *</label>
                <Input
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  placeholder="Ej. Control de Tareas de Alto Riesgo"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-600 block mb-1">Tipo de Proceso *</label>
                <select
                  value={tipo}
                  onChange={(e: any) => setTipo(e.target.value)}
                  className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-700 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
                >
                  <option value="estrategico">Estratégico</option>
                  <option value="misional">Misional</option>
                  <option value="apoyo">Apoyo</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-600 block mb-1">Descripción / Alcance</label>
                <textarea
                  value={descripcion}
                  onChange={(e) => setDescripcion(e.target.value)}
                  rows={3}
                  placeholder="Descripción del objetivo del proceso..."
                  className="w-full bg-white border border-slate-200 rounded-xl p-3 text-xs text-slate-700 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 mt-6">
                <Button variant="ghost" onClick={closeModal} className="text-xs py-2 h-10 border border-slate-200 text-slate-700">
                  Cancelar
                </Button>
                <Button variant="primary" type="submit" className="text-xs py-2 h-10" disabled={createMutation.isPending || updateMutation.isPending}>
                  {editingProceso ? 'Guardar Cambios' : 'Registrar Proceso'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}