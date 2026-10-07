import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { modulo0Service, Proceso } from '@/services/modulo0.service'
import { Card, Button } from '@/components/ui'
import {
  Workflow, Plus, Trash2, Edit2, Sparkles, AlertTriangle, X,
  Check, Loader2, Map, Download, Printer,
  ShieldCheck, LayoutGrid, Palette, Sliders, ArrowRight,
  RotateCcw, Type, Compass, Target, Wrench
} from 'lucide-react'
import html2canvas from 'html2canvas'

// ── Plantillas Estándar SG-SST (Dec. 1072 / Res. 0312 / ISO 45001) ──
const PLANTILLAS_SGSST: Record<string, { nombre: string; descripcion: string; procesos: { nombre: string; tipo: 'estrategico' | 'misional' | 'apoyo'; descripcion: string; subprocesos: string[] }[] }> = {
  estandar: {
    nombre: 'Estándar SG-SST (Decreto 1072 / Res. 0312)',
    descripcion: 'Estructura integral de 12 procesos clave para empresas de 11 a 50+ trabajadores en riesgo I a V.',
    procesos: [
      // Estratégicos
      {
        nombre: 'Direccionamiento Estratégico y Liderazgo SST',
        tipo: 'estrategico',
        descripcion: 'Definición de política, objetivos, asignación de recursos anuales y rendición de cuentas.',
        subprocesos: ['Política y Objetivos SST', 'Rendición de Cuentas', 'Asignación de Recursos Anuales']
      },
      {
        nombre: 'Auditoría y Revisión por la Alta Dirección',
        tipo: 'estrategico',
        descripcion: 'Evaluación periódica del cumplimiento del SG-SST, auditoría anual y planes de mejora continua.',
        subprocesos: ['Auditoría Interna del SG-SST', 'Revisión por la Dirección', 'Planes de Acción Correctivos']
      },
      {
        nombre: 'Gestión del Cambio y Requisitos Legales',
        tipo: 'estrategico',
        descripcion: 'Identificación y evaluación de requisitos legales colombianos y control de cambios operativos.',
        subprocesos: ['Matriz de Requisitos Legales', 'Gestión de Cambios Internos y Externos']
      },
      // Misionales
      {
        nombre: 'Identificación de Peligros y Valoración de Riesgos',
        tipo: 'misional',
        descripcion: 'Metodología GTC 45, inspecciones de seguridad y priorización de controles jerárquicos.',
        subprocesos: ['Matriz de Peligros GTC 45', 'Inspecciones Planeadas de Seguridad', 'Jerarquía de Controles']
      },
      {
        nombre: 'Medicina Preventiva y Vigilancia Epidemiológica',
        tipo: 'misional',
        descripcion: 'Evaluaciones médicas ocupacionales de ingreso, periódicos, egreso y sistemas SVE.',
        subprocesos: ['Profesiogramas y Exámenes Médicos', 'Sistemas de Vigilancia Epidemiológica (SVE)', 'Estilos de Vida Saludable']
      },
      {
        nombre: 'Control Operacional y Tareas de Alto Riesgo',
        tipo: 'misional',
        descripcion: 'Permisos de trabajo seguro en alturas, espacios confinados, caliente y energías peligrosas.',
        subprocesos: ['Permisos de Trabajo de Alto Riesgo', 'Análisis de Trabajo Seguro (ATS)', 'Inspección de EPP y Equipos']
      },
      {
        nombre: 'Preparación, Prevención y Respuesta ante Emergencias',
        tipo: 'misional',
        descripcion: 'Plan de emergencias, conformación de brigadas, señalización y simulacros anuales.',
        subprocesos: ['Plan de Emergencias y Contingencias', 'Capacitación de Brigadistas', 'Simulacros de Evacuación']
      },
      {
        nombre: 'Investigación de Incidentes y Accidentes de Trabajo',
        tipo: 'misional',
        descripcion: 'Reporte a ARL/EPS e investigación con equipo investigador interdisciplinario y COPASST.',
        subprocesos: ['Reporte FURAT / FUREP', 'Metodología Árbol de Causas / 5 Porqués', 'Lecciones Aprendidas']
      },
      // Apoyo
      {
        nombre: 'Formación, Inducción y Competencias SST',
        tipo: 'apoyo',
        descripcion: 'Plan anual de capacitación, inducción y reinducción en seguridad y salud en el trabajo.',
        subprocesos: ['Inducción y Reinducción en SST', 'Plan Anual de Capacitación', 'Evaluación de Competencias (MCC)']
      },
      {
        nombre: 'Gestión de Proveedores, Contratistas y Compras',
        tipo: 'apoyo',
        descripcion: 'Selección y evaluación de contratistas con criterios de seguridad y salud en el trabajo.',
        subprocesos: ['Evaluación de Proveedores en SST', 'Afiliación y Control de Contratistas']
      },
      {
        nombre: 'Mantenimiento Preventivo e Infraestructura',
        tipo: 'apoyo',
        descripcion: 'Mantenimiento de instalaciones locativas, maquinaria, herramientas y redes eléctricas.',
        subprocesos: ['Cronograma de Mantenimiento', 'Hojas de Vida de Maquinaria y Equipos']
      },
      {
        nombre: 'Gestión Documental y Control de Evidencias',
        tipo: 'apoyo',
        descripcion: 'Custodia, retención por 20 años y control de versiones de documentos del SG-SST.',
        subprocesos: ['Control de Registros y Evidencias', 'Custodia de Historias Ocupacionales']
      }
    ]
  },
  alto_riesgo: {
    nombre: 'Sector Industrial / Construcción / Alto Riesgo',
    descripcion: 'Enfocado en control estricto de energías, frentes de obra y operaciones críticas.',
    procesos: [
      {
        nombre: 'Gobierno Corporativo y Cultura de Seguridad',
        tipo: 'estrategico',
        descripcion: 'Liderazgo en campo, comités de seguridad de obra y rendición de cuentas.',
        subprocesos: ['Liderazgo Visible en Campo', 'Comités de Seguridad en Obra']
      },
      {
        nombre: 'Gestión Integral de Riesgos Críticos',
        tipo: 'misional',
        descripcion: 'Control exhaustivo de tareas críticas (alturas, izaje de cargas, excavaciones).',
        subprocesos: ['Permisos de Trabajo Crítico', 'Procedimientos Operativos Estandarizados (POE)']
      },
      {
        nombre: 'Seguridad Vial y Transporte de Carga (PESV)',
        tipo: 'misional',
        descripcion: 'Plan Estratégico de Seguridad Vial, mantenimiento de flotas y monitoreo telemático.',
        subprocesos: ['Inspección Preoperacional de Vehículos', 'Capacitación en Manejo Defensivo']
      },
      {
        nombre: 'Mantenimiento Mayor e Inspecciones Técnicas',
        tipo: 'apoyo',
        descripcion: 'Certificación de maquinaria pesada, calibración de detectores y pruebas de carga.',
        subprocesos: ['Certificación de Equipos de Izaje', 'Calibración de Instrumentos']
      }
    ]
  }
}

// ── Paletas de Color FOSST Oficiales ──
export interface PaletaConfig {
  nombre: string
  estrategico: string
  misional: string
  apoyo: string
  entradas: string
  salidas: string
  fondo: string
  borde: string
  texto: string
}

const PALETAS_COLOR: Record<string, PaletaConfig> = {
  fosst: {
    nombre: 'FOSST Institucional',
    estrategico: '#002D62',   // Azul marino oficial FOSST
    misional: '#0284C7',      // Azul océano técnico
    apoyo: '#334155',         // Slate corporativo
    entradas: '#D97706',      // Ámbar dorado FOSST
    salidas: '#059669',       // Verde esmeralda cumplimiento
    fondo: '#F8FAFC',
    borde: '#0F172A',
    texto: '#FFFFFF',
  },
  seguridad: {
    nombre: 'Seguridad Industrial',
    estrategico: '#0F766E',   // Teal petróleo
    misional: '#EA580C',      // Naranja señalización/riesgo
    apoyo: '#475569',         // Pizarra neutro
    entradas: '#2563EB',      // Azul normativo
    salidas: '#16A34A',       // Verde seguro
    fondo: '#FFFFFF',
    borde: '#1E293B',
    texto: '#FFFFFF',
  },
  corporativo: {
    nombre: 'Corporativo Ejecutivo',
    estrategico: '#1E293B',   // Grafito alta dirección
    misional: '#0369A1',      // Azul cobalto
    apoyo: '#64748B',         // Azul grisáceo
    entradas: '#B45309',      // Ámbar
    salidas: '#047857',       // Verde bosque
    fondo: '#F1F5F9',
    borde: '#334155',
    texto: '#FFFFFF',
  }
}

export default function ProcesosView() {
  const queryClient = useQueryClient()
  const mapExportRef = useRef<HTMLDivElement>(null)

  // Vista activa: 'tarjetas' | 'mapa'
  const [vistaActiva, setVistaActiva] = useState<'tarjetas' | 'mapa'>('tarjetas')

  // Modals state
  const [modalOpen, setModalOpen] = useState(false)
  const [iaModalOpen, setIaModalOpen] = useState(false)
  const [plantillaModalOpen, setPlantillaModalOpen] = useState(false)
  const [editingProceso, setEditingProceso] = useState<Proceso | null>(null)
  const [selectedProcessDetail, setSelectedProcessDetail] = useState<Proceso | null>(null)

  // Customization state for Process Map
  const [mapaColores, setMapaColores] = useState<PaletaConfig>(PALETAS_COLOR.fosst)
  const [textoEntradas, setTextoEntradas] = useState('Requisitos Legales y de Partes Interesadas (Dec. 1072 / Res. 0312)')
  const [textoSalidas, setTextoSalidas] = useState('Lugares de Trabajo Seguros, Saludables y Sostenibles')
  const [mostrarCustomizer, setMostrarCustomizer] = useState(false)
  const [customizerTab, setCustomizerTab] = useState<'colores' | 'textos'>('colores')
  const [isExporting, setIsExporting] = useState(false)
  const [isPrinting, setIsPrinting] = useState(false)

  // Form fields
  const [nombre, setNombre] = useState('')
  const [tipo, setTipo] = useState<'estrategico' | 'misional' | 'apoyo'>('estrategico')
  const [descripcion, setDescripcion] = useState('')
  const [errorMsg, setErrorMsg] = useState('')

  // Fetch Processes
  const { data: mapaProcesos, isLoading } = useQuery({
    queryKey: ['modulo0', 'procesos'],
    queryFn: modulo0Service.listProcesos,
  })

  // Safe data normalization: always returns an array
  const rawProcesos = (mapaProcesos as any)
  const normalizedProcesos: { estrategico: Proceso[]; misional: Proceso[]; apoyo: Proceso[] } = {
    estrategico: Array.isArray(rawProcesos?.estrategico)
      ? (rawProcesos.estrategico as Proceso[])
      : Array.isArray(rawProcesos)
      ? (rawProcesos.filter((p: any) => p.tipo === 'estrategico' && !p.padre_id && !p.padre) as Proceso[])
      : Array.isArray(rawProcesos?.results)
      ? (rawProcesos.results.filter((p: any) => p.tipo === 'estrategico' && !p.padre_id && !p.padre) as Proceso[])
      : [],
    misional: Array.isArray(rawProcesos?.misional)
      ? (rawProcesos.misional as Proceso[])
      : Array.isArray(rawProcesos)
      ? (rawProcesos.filter((p: any) => p.tipo === 'misional' && !p.padre_id && !p.padre) as Proceso[])
      : Array.isArray(rawProcesos?.results)
      ? (rawProcesos.results.filter((p: any) => p.tipo === 'misional' && !p.padre_id && !p.padre) as Proceso[])
      : [],
    apoyo: Array.isArray(rawProcesos?.apoyo)
      ? (rawProcesos.apoyo as Proceso[])
      : Array.isArray(rawProcesos)
      ? (rawProcesos.filter((p: any) => p.tipo === 'apoyo' && !p.padre_id && !p.padre) as Proceso[])
      : Array.isArray(rawProcesos?.results)
      ? (rawProcesos.results.filter((p: any) => p.tipo === 'apoyo' && !p.padre_id && !p.padre) as Proceso[])
      : [],
  }

  // Fetch AI suggestions
  const { data: sugeridosIA, refetch: fetchSugeridosIA, isFetching: isFetchingIA } = useQuery({
    queryKey: ['modulo0', 'sugerencias-procesos'],
    queryFn: modulo0Service.sugerirProcesosIA,
    enabled: false,
  })

  const createMutation = useMutation({
    mutationFn: modulo0Service.createProceso,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modulo0'] })
      closeModal()
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Error al crear el proceso.')
    }
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Proceso> }) =>
      modulo0Service.updateProceso(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modulo0'] })
      closeModal()
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Error al actualizar el proceso.')
    }
  })

  const deleteMutation = useMutation({
    mutationFn: modulo0Service.deleteProceso,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modulo0'] })
      if (selectedProcessDetail) setSelectedProcessDetail(null)
    },
    onError: (err: any) => {
      alert(err.message || 'No se puede eliminar un proceso que posee subprocesos activos.')
    }
  })

  const importTemplateMutation = useMutation({
    mutationFn: async (templateKey: string) => {
      const template = PLANTILLAS_SGSST[templateKey]
      if (!template) return
      for (const item of template.procesos) {
        const proc = await modulo0Service.createProceso({
          nombre: item.nombre,
          tipo: item.tipo,
          descripcion: item.descripcion,
          padre_id: null
        })
        for (const sub of item.subprocesos) {
          await modulo0Service.createProceso({
            nombre: sub,
            tipo: item.tipo,
            descripcion: `Subproceso de ${item.nombre}`,
            padre_id: proc.id
          })
        }
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modulo0'] })
      setPlantillaModalOpen(false)
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

  const handleSubmit = async (e: React.FormEvent) => {
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
        descripcion: descripcion.trim() || null,
        padre_id: null
      })
    }
  }

  // Update individual color in customizer
  const updateCustomColor = (key: keyof PaletaConfig, value: string) => {
    setMapaColores(prev => ({
      ...prev,
      nombre: 'Personalizada',
      [key]: value
    }))
  }

  // Export high resolution PNG
  const exportarMapaPNG = async () => {
    const el = document.getElementById('mapa-procesos-canvas-export')
    if (!el) return
    setIsExporting(true)
    try {
      const canvas = await html2canvas(el, {
        scale: 2.5,
        useCORS: true,
        backgroundColor: mapaColores.fondo
      })
      const link = document.createElement('a')
      link.download = `Mapa_Procesos_SGSST_${new Date().toISOString().slice(0, 10)}.png`
      link.href = canvas.toDataURL('image/png')
      link.click()
    } catch (err) {
      console.error('Error exportando PNG:', err)
      alert('Hubo un error al generar la imagen PNG del mapa.')
    } finally {
      setIsExporting(false)
    }
  }

  // High quality landscape print without web page clutter
  const imprimirMapa = async () => {
    const el = document.getElementById('mapa-procesos-canvas-export')
    if (!el) return
    setIsPrinting(true)
    try {
      const canvas = await html2canvas(el, {
        scale: 2.5,
        useCORS: true,
        backgroundColor: mapaColores.fondo
      })
      const imgData = canvas.toDataURL('image/png')
      const printWindow = window.open('', '_blank')
      if (!printWindow) {
        alert('Por favor habilita las ventanas emergentes para poder imprimir el mapa de procesos.')
        return
      }

      const htmlContent = `
        <!DOCTYPE html>
        <html>
        <head>
          <title>Mapa de Procesos SG-SST — Impresión</title>
          <meta charset="utf-8" />
          <style>
            @page {
              size: landscape;
              margin: 8mm;
            }
            @media print {
              body {
                background: white !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
              }
            }
            body {
              margin: 0;
              padding: 12px;
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
              background: #f8fafc;
            }
            .header-info {
              width: 100%;
              max-width: 1200px;
              display: flex;
              justify-content: space-between;
              align-items: center;
              margin-bottom: 12px;
              padding-bottom: 8px;
              border-bottom: 1.5px solid #cbd5e1;
              color: #1e293b;
            }
            .header-title {
              font-size: 14px;
              font-weight: 800;
              color: #002D62;
              display: flex;
              align-items: center;
              gap: 6px;
            }
            .header-meta {
              font-size: 11px;
              color: #64748b;
              font-weight: 500;
            }
            .map-image-wrapper {
              width: 100%;
              max-width: 1200px;
              display: flex;
              justify-content: center;
            }
            img {
              width: 100%;
              max-height: 85vh;
              object-fit: contain;
              border-radius: 12px;
              box-shadow: 0 4px 16px rgba(0,0,0,0.08);
            }
          </style>
        </head>
        <body>
          <div class="header-info">
            <div class="header-title">
              <span>FOSST</span> • Mapa de Procesos del SG-SST (ISO 45001 / Dec. 1072)
            </div>
            <div class="header-meta">
              Fecha de Impresión: ${new Date().toLocaleDateString('es-CO', { year: 'numeric', month: 'long', day: 'numeric' })}
            </div>
          </div>
          <div class="map-image-wrapper">
            <img src="${imgData}" alt="Mapa de Procesos SG-SST" />
          </div>
          <script>
            window.onload = function() {
              setTimeout(function() {
                window.print();
                window.close();
              }, 350);
            }
          </script>
        </body>
        </html>
      `
      printWindow.document.open()
      printWindow.document.write(htmlContent)
      printWindow.document.close()
    } catch (err) {
      console.error('Error al imprimir:', err)
      alert('No se pudo preparar la impresión del mapa.')
    } finally {
      setIsPrinting(false)
    }
  }

  const renderProcessCard = (proc: Proceso, colorKey: 'estrategico' | 'misional' | 'apoyo') => {
    const borderAccent = {
      estrategico: 'border-l-[#002D62]',
      misional: 'border-l-[#0284C7]',
      apoyo: 'border-l-[#334155]',
    }[colorKey]

    return (
      <div
        key={proc.id}
        className={`p-3.5 rounded-xl bg-white border border-slate-200 border-l-4 shadow-sm hover:shadow-md transition-all space-y-2.5 ${borderAccent}`}
      >
        <div className="flex items-start justify-between gap-2">
          <div>
            <h4 className="text-xs font-bold text-slate-900 leading-tight">{proc.nombre}</h4>
            {proc.descripcion && (
              <p className="text-[11px] text-slate-500 mt-1 line-clamp-2 leading-relaxed">{proc.descripcion}</p>
            )}
          </div>
          <div className="flex items-center gap-1 flex-shrink-0">
            <button
              onClick={() => openEditModal(proc)}
              className="p-1 rounded-lg text-slate-400 hover:text-primary hover:bg-slate-100 transition"
              title="Editar proceso"
            >
              <Edit2 className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => {
                if (confirm(`¿Eliminar el proceso "${proc.nombre}"?`)) {
                  deleteMutation.mutate(proc.id)
                }
              }}
              className="p-1 rounded-lg text-slate-400 hover:text-alert hover:bg-red-50 transition"
              title="Eliminar proceso"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {proc.subprocesos && proc.subprocesos.length > 0 && (
          <div className="pt-2 border-t border-slate-100 space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Subprocesos ({proc.subprocesos.length}):</span>
            <div className="flex flex-wrap gap-1">
              {proc.subprocesos.map((sub) => (
                <span key={sub.id} className="text-[10px] px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 font-medium">
                  {sub.nombre}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header Principal */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-primary-50 flex items-center justify-center border border-primary-100">
              <Workflow className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                Mapa de Procesos del SG-SST
              </h1>
              <p className="text-xs text-slate-500">
                Arquitectura interactiva por procesos según ISO 45001, Dec. 1072 de 2015 y Res. 0312.
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Switcher de Vista */}
          <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200">
            <button
              onClick={() => setVistaActiva('tarjetas')}
              className={`text-xs px-3 py-1.5 rounded-lg font-bold flex items-center gap-1.5 transition ${
                vistaActiva === 'tarjetas'
                  ? 'bg-white text-primary shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" /> Fichas de Procesos
            </button>
            <button
              onClick={() => setVistaActiva('mapa')}
              className={`text-xs px-3 py-1.5 rounded-lg font-bold flex items-center gap-1.5 transition ${
                vistaActiva === 'mapa'
                  ? 'bg-white text-primary shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Map className="w-3.5 h-3.5" /> Mapa Gráfico SG-SST
            </button>
          </div>

          <button
            onClick={() => setPlantillaModalOpen(true)}
            className="inline-flex items-center gap-1.5 text-xs font-bold px-3.5 py-2 rounded-xl bg-white hover:bg-slate-50 text-slate-800 border border-slate-300 shadow-xs transition h-9"
          >
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Plantillas SST</span>
          </button>

          <button
            onClick={() => { setIaModalOpen(true); fetchSugeridosIA(); }}
            className="inline-flex items-center gap-1.5 text-xs font-bold px-3.5 py-2 rounded-xl bg-[#002D62] hover:bg-[#00244e] text-white shadow-sm transition h-9"
          >
            <Sparkles className="w-4 h-4 text-[#F5A800]" />
            <span>Sugerir con IA</span>
          </button>
        </div>
      </div>

      {/* VISTA 1: TARJETAS OPERATIVAS */}
      {vistaActiva === 'tarjetas' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          {/* ESTRATÉGICOS */}
          <div className="bg-slate-50/70 border border-slate-200 rounded-2xl p-4 space-y-4">
            <div className="flex justify-between items-center pb-2 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#002D62]" />
                <h3 className="font-bold text-xs text-slate-800 uppercase tracking-wider">Estratégicos / Liderazgo</h3>
                <span className="text-[10px] font-bold text-slate-600 bg-white px-2 py-0.5 rounded-md border border-slate-200">
                  {normalizedProcesos.estrategico.length}
                </span>
              </div>
              <button
                onClick={() => openAddModal('estrategico')}
                className="p-1 rounded-lg text-slate-400 hover:text-primary hover:bg-white transition"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-3">
              {normalizedProcesos.estrategico.map((proc) => renderProcessCard(proc, 'estrategico'))}
              {normalizedProcesos.estrategico.length === 0 && (
                <div className="p-6 text-center text-xs text-slate-400 border border-dashed rounded-xl bg-white">
                  Sin procesos estratégicos registrados.
                </div>
              )}
            </div>
          </div>

          {/* MISIONALES */}
          <div className="bg-slate-50/70 border border-slate-200 rounded-2xl p-4 space-y-4">
            <div className="flex justify-between items-center pb-2 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#0284C7]" />
                <h3 className="font-bold text-xs text-slate-800 uppercase tracking-wider">Misionales / Control de Riesgo</h3>
                <span className="text-[10px] font-bold text-slate-600 bg-white px-2 py-0.5 rounded-md border border-slate-200">
                  {normalizedProcesos.misional.length}
                </span>
              </div>
              <button
                onClick={() => openAddModal('misional')}
                className="p-1 rounded-lg text-slate-400 hover:text-primary hover:bg-white transition"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-3">
              {normalizedProcesos.misional.map((proc) => renderProcessCard(proc, 'misional'))}
              {normalizedProcesos.misional.length === 0 && (
                <div className="p-6 text-center text-xs text-slate-400 border border-dashed rounded-xl bg-white">
                  Sin procesos misionales registrados.
                </div>
              )}
            </div>
          </div>

          {/* APOYO */}
          <div className="bg-slate-50/70 border border-slate-200 rounded-2xl p-4 space-y-4">
            <div className="flex justify-between items-center pb-2 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#334155]" />
                <h3 className="font-bold text-xs text-slate-800 uppercase tracking-wider">Apoyo / Soporte SST</h3>
                <span className="text-[10px] font-bold text-slate-600 bg-white px-2 py-0.5 rounded-md border border-slate-200">
                  {normalizedProcesos.apoyo.length}
                </span>
              </div>
              <button
                onClick={() => openAddModal('apoyo')}
                className="p-1 rounded-lg text-slate-400 hover:text-primary hover:bg-white transition"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-3">
              {normalizedProcesos.apoyo.map((proc) => renderProcessCard(proc, 'apoyo'))}
              {normalizedProcesos.apoyo.length === 0 && (
                <div className="p-6 text-center text-xs text-slate-400 border border-dashed rounded-xl bg-white">
                  Sin procesos de apoyo registrados.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* VISTA 2: MAPA GRÁFICO INTERACTIVO SG-SST */}
      {vistaActiva === 'mapa' && (
        <div className="space-y-4">
          {/* Barra de herramientas del Mapa */}
          <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            {/* Paletas rápidas */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5 mr-1">
                <Palette className="w-4 h-4 text-primary" /> Estilo:
              </span>
              {Object.entries(PALETAS_COLOR).map(([key, paleta]) => (
                <button
                  key={key}
                  onClick={() => setMapaColores(paleta)}
                  className={`text-xs px-3 py-1.5 rounded-xl border font-bold transition flex items-center gap-2 ${
                    mapaColores.nombre === paleta.nombre
                      ? 'bg-primary text-white border-primary shadow-sm'
                      : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  <div className="flex -space-x-1">
                    <span className="w-3 h-3 rounded-full border border-white" style={{ backgroundColor: paleta.estrategico }} />
                    <span className="w-3 h-3 rounded-full border border-white" style={{ backgroundColor: paleta.misional }} />
                    <span className="w-3 h-3 rounded-full border border-white" style={{ backgroundColor: paleta.entradas }} />
                  </div>
                  {paleta.nombre}
                </button>
              ))}
            </div>

            {/* Acciones principales */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setMostrarCustomizer(!mostrarCustomizer)}
                className={`inline-flex items-center gap-1.5 text-xs font-bold px-3.5 py-2 rounded-xl border shadow-xs transition h-9 ${
                  mostrarCustomizer
                    ? 'bg-[#002D62] text-white border-[#002D62]'
                    : 'bg-white hover:bg-slate-50 text-slate-800 border-slate-300'
                }`}
              >
                <Sliders className="w-3.5 h-3.5" />
                <span>{mostrarCustomizer ? 'Cerrar Ajustes' : 'Personalizar Mapa'}</span>
              </button>

              <button
                onClick={exportarMapaPNG}
                disabled={isExporting}
                className="inline-flex items-center gap-1.5 text-xs font-bold px-3.5 py-2 rounded-xl bg-white hover:bg-slate-50 text-slate-800 border border-slate-300 shadow-xs transition h-9 disabled:opacity-50"
              >
                {isExporting ? <Loader2 className="w-3.5 h-3.5 animate-spin text-slate-600" /> : <Download className="w-3.5 h-3.5 text-slate-600" />}
                <span>Exportar PNG</span>
              </button>

              <button
                onClick={imprimirMapa}
                disabled={isPrinting}
                className="inline-flex items-center gap-1.5 text-xs font-bold px-3.5 py-2 rounded-xl bg-white hover:bg-slate-50 text-slate-800 border border-slate-300 shadow-xs transition h-9 disabled:opacity-50"
              >
                {isPrinting ? <Loader2 className="w-3.5 h-3.5 animate-spin text-slate-600" /> : <Printer className="w-3.5 h-3.5 text-slate-600" />}
                <span>Imprimir</span>
              </button>
            </div>
          </div>

          {/* Panel de Personalización Total (Colapsable y Elegante) */}
          {mostrarCustomizer && (
            <Card className="p-5 bg-white border border-primary-200 shadow-md space-y-4 animate-in fade-in slide-in-from-top-2 duration-200">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-primary" />
                  <h4 className="text-sm font-bold text-slate-900">Personalizador del Mapa de Procesos</h4>
                </div>

                <div className="flex items-center gap-2">
                  <div className="flex bg-slate-100 p-0.5 rounded-lg border border-slate-200">
                    <button
                      onClick={() => setCustomizerTab('colores')}
                      className={`text-xs px-2.5 py-1 rounded-md font-bold transition flex items-center gap-1.5 ${
                        customizerTab === 'colores' ? 'bg-white text-primary shadow-xs' : 'text-slate-600'
                      }`}
                    >
                      <Palette className="w-3.5 h-3.5" /> Colores
                    </button>
                    <button
                      onClick={() => setCustomizerTab('textos')}
                      className={`text-xs px-2.5 py-1 rounded-md font-bold transition flex items-center gap-1.5 ${
                        customizerTab === 'textos' ? 'bg-white text-primary shadow-xs' : 'text-slate-600'
                      }`}
                    >
                      <Type className="w-3.5 h-3.5" /> Textos
                    </button>
                  </div>

                  <button
                    onClick={() => setMapaColores(PALETAS_COLOR.fosst)}
                    className="text-xs text-slate-500 hover:text-primary flex items-center gap-1 px-2 py-1 rounded hover:bg-slate-50 transition"
                    title="Restablecer a valores FOSST por defecto"
                  >
                    <RotateCcw className="w-3.5 h-3.5" /> Restablecer
                  </button>
                </div>
              </div>

              {/* TAB 1: COLORES LIBRES */}
              {customizerTab === 'colores' && (
                <div className="space-y-4">
                  <p className="text-xs text-slate-500">
                    Selecciona cualquier color personalizado haciendo clic en las muestras de color:
                  </p>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                    {/* Estratégico */}
                    <div className="p-2.5 rounded-xl border border-slate-200 bg-slate-50/50 flex items-center justify-between">
                      <div>
                        <span className="text-[11px] font-bold text-slate-800 block">Procesos Estratégicos</span>
                        <span className="text-[10px] text-slate-400 font-mono uppercase">{mapaColores.estrategico}</span>
                      </div>
                      <input
                        type="color"
                        value={mapaColores.estrategico}
                        onChange={(e) => updateCustomColor('estrategico', e.target.value)}
                        className="w-8 h-8 rounded-lg cursor-pointer border-0 bg-transparent"
                      />
                    </div>

                    {/* Misional */}
                    <div className="p-2.5 rounded-xl border border-slate-200 bg-slate-50/50 flex items-center justify-between">
                      <div>
                        <span className="text-[11px] font-bold text-slate-800 block">Procesos Misionales</span>
                        <span className="text-[10px] text-slate-400 font-mono uppercase">{mapaColores.misional}</span>
                      </div>
                      <input
                        type="color"
                        value={mapaColores.misional}
                        onChange={(e) => updateCustomColor('misional', e.target.value)}
                        className="w-8 h-8 rounded-lg cursor-pointer border-0 bg-transparent"
                      />
                    </div>

                    {/* Apoyo */}
                    <div className="p-2.5 rounded-xl border border-slate-200 bg-slate-50/50 flex items-center justify-between">
                      <div>
                        <span className="text-[11px] font-bold text-slate-800 block">Procesos de Apoyo</span>
                        <span className="text-[10px] text-slate-400 font-mono uppercase">{mapaColores.apoyo}</span>
                      </div>
                      <input
                        type="color"
                        value={mapaColores.apoyo}
                        onChange={(e) => updateCustomColor('apoyo', e.target.value)}
                        className="w-8 h-8 rounded-lg cursor-pointer border-0 bg-transparent"
                      />
                    </div>

                    {/* Entradas */}
                    <div className="p-2.5 rounded-xl border border-slate-200 bg-slate-50/50 flex items-center justify-between">
                      <div>
                        <span className="text-[11px] font-bold text-slate-800 block">Lateral Entradas</span>
                        <span className="text-[10px] text-slate-400 font-mono uppercase">{mapaColores.entradas}</span>
                      </div>
                      <input
                        type="color"
                        value={mapaColores.entradas}
                        onChange={(e) => updateCustomColor('entradas', e.target.value)}
                        className="w-8 h-8 rounded-lg cursor-pointer border-0 bg-transparent"
                      />
                    </div>

                    {/* Salidas */}
                    <div className="p-2.5 rounded-xl border border-slate-200 bg-slate-50/50 flex items-center justify-between">
                      <div>
                        <span className="text-[11px] font-bold text-slate-800 block">Lateral Salidas</span>
                        <span className="text-[10px] text-slate-400 font-mono uppercase">{mapaColores.salidas}</span>
                      </div>
                      <input
                        type="color"
                        value={mapaColores.salidas}
                        onChange={(e) => updateCustomColor('salidas', e.target.value)}
                        className="w-8 h-8 rounded-lg cursor-pointer border-0 bg-transparent"
                      />
                    </div>

                    {/* Fondo Canvas */}
                    <div className="p-2.5 rounded-xl border border-slate-200 bg-slate-50/50 flex items-center justify-between">
                      <div>
                        <span className="text-[11px] font-bold text-slate-800 block">Fondo del Mapa</span>
                        <span className="text-[10px] text-slate-400 font-mono uppercase">{mapaColores.fondo}</span>
                      </div>
                      <input
                        type="color"
                        value={mapaColores.fondo}
                        onChange={(e) => updateCustomColor('fondo', e.target.value)}
                        className="w-8 h-8 rounded-lg cursor-pointer border-0 bg-transparent"
                      />
                    </div>

                    {/* Bordes */}
                    <div className="p-2.5 rounded-xl border border-slate-200 bg-slate-50/50 flex items-center justify-between">
                      <div>
                        <span className="text-[11px] font-bold text-slate-800 block">Color de Bordes</span>
                        <span className="text-[10px] text-slate-400 font-mono uppercase">{mapaColores.borde}</span>
                      </div>
                      <input
                        type="color"
                        value={mapaColores.borde}
                        onChange={(e) => updateCustomColor('borde', e.target.value)}
                        className="w-8 h-8 rounded-lg cursor-pointer border-0 bg-transparent"
                      />
                    </div>

                    {/* Textos */}
                    <div className="p-2.5 rounded-xl border border-slate-200 bg-slate-50/50 flex items-center justify-between">
                      <div>
                        <span className="text-[11px] font-bold text-slate-800 block">Color de Textos</span>
                        <span className="text-[10px] text-slate-400 font-mono uppercase">{mapaColores.texto}</span>
                      </div>
                      <input
                        type="color"
                        value={mapaColores.texto}
                        onChange={(e) => updateCustomColor('texto', e.target.value)}
                        className="w-8 h-8 rounded-lg cursor-pointer border-0 bg-transparent"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: TEXTOS DEL MAPA */}
              {customizerTab === 'textos' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div>
                    <label className="font-bold text-slate-700 block mb-1.5 flex items-center gap-1.5">
                      <ArrowRight className="w-3.5 h-3.5 text-primary" />
                      Texto Franja Lateral Izquierda (Entradas / Requisitos):
                    </label>
                    <input
                      type="text"
                      value={textoEntradas}
                      onChange={(e) => setTextoEntradas(e.target.value)}
                      placeholder="Ej: Requisitos Legales y de Partes Interesadas (Dec. 1072 / Res. 0312)"
                      className="w-full text-xs rounded-xl border border-slate-200 p-2.5 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition"
                    />
                  </div>
                  <div>
                    <label className="font-bold text-slate-700 block mb-1.5 flex items-center gap-1.5">
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                      Texto Franja Lateral Derecha (Salidas / Resultados):
                    </label>
                    <input
                      type="text"
                      value={textoSalidas}
                      onChange={(e) => setTextoSalidas(e.target.value)}
                      placeholder="Ej: Lugares de Trabajo Seguros, Saludables y Sostenibles"
                      className="w-full text-xs rounded-xl border border-slate-200 p-2.5 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition"
                    />
                  </div>
                </div>
              )}
            </Card>
          )}

          {/* Canvas del Mapa de Procesos (Exportable a PNG / Imprimible) */}
          <div className="p-6 bg-slate-100/80 rounded-2xl border border-slate-200 overflow-x-auto flex justify-center">
            <div
              id="mapa-procesos-canvas-export"
              ref={mapExportRef}
              className="w-full min-w-[900px] max-w-[1250px] rounded-2xl overflow-hidden shadow-lg border-2 transition-all"
              style={{
                backgroundColor: mapaColores.fondo,
                borderColor: mapaColores.borde,
              }}
            >
              {/* BANDA SUPERIOR: PROCESOS ESTRATÉGICOS */}
              <div
                className="p-5 text-center border-b-2 space-y-3"
                style={{
                  backgroundColor: mapaColores.estrategico,
                  borderColor: mapaColores.borde,
                }}
              >
                <h3 className="text-xs font-black uppercase tracking-widest text-white flex items-center justify-center gap-2">
                  <Compass className="w-4 h-4" /> PROCESOS ESTRATÉGICOS Y DIRECCIONAMIENTO SST <Compass className="w-4 h-4" />
                </h3>
                <div className="flex flex-wrap justify-center gap-3">
                  {normalizedProcesos.estrategico.length > 0 ? (
                    normalizedProcesos.estrategico.map((proc) => (
                      <div
                        key={proc.id}
                        onClick={() => setSelectedProcessDetail(proc)}
                        className="p-3 rounded-xl border text-center transition-all cursor-pointer min-w-[180px] max-w-[240px] hover:scale-105 shadow-sm"
                        style={{
                          backgroundColor: 'rgba(255, 255, 255, 0.16)',
                          borderColor: 'rgba(255, 255, 255, 0.3)',
                          color: mapaColores.texto,
                        }}
                      >
                        <div className="font-bold text-xs leading-tight">{proc.nombre}</div>
                        {proc.subprocesos && proc.subprocesos.length > 0 && (
                          <div className="mt-1.5 flex flex-wrap justify-center gap-1">
                            {proc.subprocesos.map((s) => (
                              <span key={s.id} className="text-[9px] px-1.5 py-0.5 rounded bg-white/20 text-white font-medium">
                                {s.nombre}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="text-white/70 text-xs italic py-2">Sin procesos estratégicos registrados</div>
                  )}
                </div>
              </div>

              {/* SECCIÓN INTERMEDIA: LATERAL IZQ, CENTRO (MISIONAL + APOYO), LATERAL DER */}
              <div className="flex min-h-[380px]">
                {/* Lateral Izquierdo: REQUISITOS / ENTRADAS */}
                <div
                  className="p-4 flex items-center justify-center text-center font-black text-xs uppercase tracking-widest border-r-2 select-none"
                  style={{
                    backgroundColor: mapaColores.entradas,
                    borderColor: mapaColores.borde,
                    color: mapaColores.texto,
                    writingMode: 'vertical-rl',
                    transform: 'rotate(180deg)',
                    width: '65px',
                  }}
                >
                  {textoEntradas}
                </div>

                {/* Zona Central: MISIONALES ARRIBA + APOYO ABAJO */}
                <div className="flex-1 flex flex-col">
                  {/* PROCESOS MISIONALES */}
                  <div
                    className="p-5 text-center flex-1 flex flex-col justify-center items-center gap-3 border-b-2"
                    style={{
                      backgroundColor: mapaColores.misional,
                      borderColor: mapaColores.borde,
                    }}
                  >
                    <h3 className="text-xs font-black uppercase tracking-widest text-white flex items-center justify-center gap-2">
                      <Target className="w-4 h-4" /> PROCESOS MISIONALES / CONTROL OPERACIONAL DEL RIESGO <Target className="w-4 h-4" />
                    </h3>
                    <div className="flex flex-wrap justify-center gap-3 w-full">
                      {normalizedProcesos.misional.length > 0 ? (
                        normalizedProcesos.misional.map((proc) => (
                          <div
                            key={proc.id}
                            onClick={() => setSelectedProcessDetail(proc)}
                            className="p-3 rounded-xl border text-center transition-all cursor-pointer min-w-[180px] max-w-[240px] hover:scale-105 shadow-sm"
                            style={{
                              backgroundColor: 'rgba(255, 255, 255, 0.16)',
                              borderColor: 'rgba(255, 255, 255, 0.3)',
                              color: mapaColores.texto,
                            }}
                          >
                            <div className="font-bold text-xs leading-tight">{proc.nombre}</div>
                            {proc.subprocesos && proc.subprocesos.length > 0 && (
                              <div className="mt-1.5 flex flex-wrap justify-center gap-1">
                                {proc.subprocesos.map((s) => (
                                  <span key={s.id} className="text-[9px] px-1.5 py-0.5 rounded bg-white/20 text-white font-medium">
                                    {s.nombre}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        ))
                      ) : (
                        <div className="text-white/70 text-xs italic py-2">Sin procesos misionales registrados</div>
                      )}
                    </div>
                  </div>

                  {/* PROCESOS DE APOYO */}
                  <div
                    className="p-5 text-center flex flex-col justify-center items-center gap-3"
                    style={{
                      backgroundColor: mapaColores.apoyo,
                      color: mapaColores.texto,
                    }}
                  >
                    <h3 className="text-xs font-black uppercase tracking-widest text-white flex items-center justify-center gap-2">
                      <Wrench className="w-4 h-4" /> PROCESOS DE APOYO Y SOPORTE SST <Wrench className="w-4 h-4" />
                    </h3>
                    <div className="flex flex-wrap justify-center gap-3 w-full">
                      {normalizedProcesos.apoyo.length > 0 ? (
                        normalizedProcesos.apoyo.map((proc) => (
                          <div
                            key={proc.id}
                            onClick={() => setSelectedProcessDetail(proc)}
                            className="p-3 rounded-xl border text-center transition-all cursor-pointer min-w-[180px] max-w-[240px] hover:scale-105 shadow-sm"
                            style={{
                              backgroundColor: 'rgba(255, 255, 255, 0.16)',
                              borderColor: 'rgba(255, 255, 255, 0.3)',
                              color: mapaColores.texto,
                            }}
                          >
                            <div className="font-bold text-xs leading-tight">{proc.nombre}</div>
                            {proc.subprocesos && proc.subprocesos.length > 0 && (
                              <div className="mt-1.5 flex flex-wrap justify-center gap-1">
                                {proc.subprocesos.map((s) => (
                                  <span key={s.id} className="text-[9px] px-1.5 py-0.5 rounded bg-white/20 text-white font-medium">
                                    {s.nombre}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        ))
                      ) : (
                        <div className="text-white/70 text-xs italic py-2">Sin procesos de apoyo registrados</div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Lateral Derecho: SATISFACCIÓN / SALIDAS */}
                <div
                  className="p-4 flex items-center justify-center text-center font-black text-xs uppercase tracking-widest border-l-2 select-none"
                  style={{
                    backgroundColor: mapaColores.salidas,
                    borderColor: mapaColores.borde,
                    color: mapaColores.texto,
                    writingMode: 'vertical-rl',
                    transform: 'rotate(180deg)',
                    width: '65px',
                  }}
                >
                  {textoSalidas}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal Ficha Detalle del Proceso al hacer clic */}
      {selectedProcessDetail && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200 space-y-4 p-5">
            <div className="flex items-start justify-between pb-3 border-b border-slate-100">
              <div>
                <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                  selectedProcessDetail.tipo === 'estrategico' ? 'bg-primary-50 text-primary-700' :
                  selectedProcessDetail.tipo === 'misional' ? 'bg-sky-50 text-sky-700' :
                  'bg-slate-100 text-slate-700'
                }`}>
                  Proceso {selectedProcessDetail.tipo}
                </span>
                <h3 className="text-base font-bold text-slate-900 mt-1">{selectedProcessDetail.nombre}</h3>
              </div>
              <button onClick={() => setSelectedProcessDetail(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="font-bold text-slate-600">Descripción del Proceso:</span>
                <p className="text-slate-700 bg-slate-50 p-2.5 rounded-lg border border-slate-100 mt-1">
                  {selectedProcessDetail.descripcion || 'Sin descripción detallada.'}
                </p>
              </div>

              {selectedProcessDetail.subprocesos && selectedProcessDetail.subprocesos.length > 0 && (
                <div>
                  <span className="font-bold text-slate-600">Subprocesos Operativos:</span>
                  <div className="space-y-1 mt-1">
                    {selectedProcessDetail.subprocesos.map((s) => (
                      <div key={s.id} className="p-2 rounded bg-slate-50 border border-slate-100 flex items-center gap-2">
                        <ArrowRight className="w-3 h-3 text-primary flex-shrink-0" />
                        <span className="font-medium text-slate-800">{s.nombre}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
              <Button
                onClick={() => {
                  const p = selectedProcessDetail
                  setSelectedProcessDetail(null)
                  openEditModal(p)
                }}
                variant="secondary"
                className="text-xs py-1.5 px-3"
              >
                Editar Proceso
              </Button>
              <Button onClick={() => setSelectedProcessDetail(null)} variant="primary" className="text-xs py-1.5 px-4">
                Cerrar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Plantillas SG-SST */}
      {plantillaModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <div className="bg-[#002D62] text-white px-6 py-4 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <div>
                  <h3 className="font-bold text-sm">Plantillas Estándar de Procesos SG-SST</h3>
                  <p className="text-[10px] text-slate-300">Importa instantáneamente la estructura normativa colombiana.</p>
                </div>
              </div>
              <button onClick={() => setPlantillaModalOpen(false)} className="text-slate-300 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4 max-h-[450px] overflow-auto">
              {Object.entries(PLANTILLAS_SGSST).map(([key, item]) => (
                <div key={key} className="p-4 rounded-xl border border-slate-200 bg-slate-50 hover:bg-white hover:border-primary-200 transition space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">{item.nombre}</h4>
                      <p className="text-xs text-slate-500 mt-0.5">{item.descripcion}</p>
                    </div>
                    <Button
                      onClick={() => importTemplateMutation.mutate(key)}
                      disabled={importTemplateMutation.isPending}
                      variant="primary"
                      className="text-xs py-1.5 px-3 flex items-center gap-1 font-bold flex-shrink-0"
                    >
                      {importTemplateMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                      Cargar Plantilla
                    </Button>
                  </div>

                  <div className="text-[11px] text-slate-600 bg-white p-2 rounded-lg border border-slate-100">
                    <strong>Incluye {item.procesos.length} procesos clave:</strong> {item.procesos.map(p => p.nombre).join(', ')}.
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Modal Crear / Editar Proceso */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <div className="bg-[#002D62] text-white px-5 py-4 flex justify-between items-center">
              <div>
                <h3 className="font-bold text-sm">{editingProceso ? 'Editar Proceso' : 'Crear Proceso'}</h3>
                <p className="text-[10px] text-slate-300">Estructura la ficha operativa del proceso.</p>
              </div>
              <button onClick={closeModal} className="text-slate-300 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-5 space-y-4">
              {errorMsg && (
                <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                  <span>{errorMsg}</span>
                </div>
              )}

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Nombre del Proceso *</label>
                <input
                  type="text"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  placeholder="Ej: Medicina Preventiva y del Trabajo"
                  className="w-full text-xs rounded-lg border border-slate-200 p-2 focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Tipo de Proceso *</label>
                <select
                  value={tipo}
                  onChange={(e: any) => setTipo(e.target.value)}
                  className="w-full text-xs rounded-lg border border-slate-200 p-2 focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                >
                  <option value="estrategico">Estratégico / Liderazgo</option>
                  <option value="misional">Misional / Control de Riesgos</option>
                  <option value="apoyo">Apoyo / Soporte</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Descripción / Objetivo</label>
                <textarea
                  value={descripcion}
                  onChange={(e) => setDescripcion(e.target.value)}
                  rows={3}
                  placeholder="Describe el objetivo y alcance del proceso en el SG-SST..."
                  className="w-full text-xs rounded-lg border border-slate-200 p-2 focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                />
              </div>

              <div className="flex gap-2 justify-end pt-3 border-t border-slate-100">
                <Button type="button" onClick={closeModal} variant="secondary" className="text-xs py-2 px-4">
                  Cancelar
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  className="text-xs py-2 px-5 font-bold"
                  disabled={createMutation.isPending || updateMutation.isPending}
                >
                  {editingProceso ? 'Guardar Cambios' : 'Registrar Proceso'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Sugerencias IA */}
      {iaModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <div className="bg-[#002D62] text-white px-5 py-4 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-brand-400" />
                <div>
                  <h3 className="font-bold text-sm">Sugerencias IA según Actividad CIIU</h3>
                  <p className="text-[10px] text-slate-300">Propuesta personalizada para tu sector económico.</p>
                </div>
              </div>
              <button onClick={() => setIaModalOpen(false)} className="text-slate-300 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4 max-h-[450px] overflow-auto">
              {isFetchingIA ? (
                <div className="flex flex-col items-center justify-center py-12 space-y-3">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                  <p className="text-xs font-semibold text-slate-500">
                    Analizando sector económico y normatividad SST aplicable...
                  </p>
                </div>
              ) : sugeridosIA ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {sugeridosIA.procesos.map((item, idx) => (
                      <div key={idx} className="border border-slate-200 rounded-xl p-3 bg-slate-50 space-y-1">
                        <div className="flex justify-between items-center">
                          <h5 className="font-bold text-xs text-slate-900">{item.nombre}</h5>
                          <span className="text-[9px] font-bold uppercase px-2 py-0.5 rounded bg-white border border-slate-200">
                            {item.tipo}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 line-clamp-2">{item.descripcion}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-xs text-slate-400">
                  No se pudieron cargar sugerencias en este momento.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}