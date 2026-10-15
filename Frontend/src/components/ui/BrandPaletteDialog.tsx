import React, { useState, useEffect, useRef } from 'react'
import { useBranding } from '@/store/branding.context'
import { resolveMediaUrl } from '@/services/api.client'
import {
  getContrastRatio,
  contrastText,
  generatePaletteScale,
  extractDominantColors,
  autoAssignBrandPalette,
  parseHexList,
} from '@/utils/color.utils'
import {
  Palette,
  Check,
  X,
  Sparkles,
  AlertTriangle,
  Upload,
  Pipette,
  Wand2,
  Loader2,
  Eye,
  ShieldCheck,
  Image as ImageIcon,
  RotateCcw,
  GitBranch,
  Workflow,
  ArrowRight,
  ClipboardPaste,
} from 'lucide-react'
import { Input } from '@/components/ui/forms'

export interface BrandPreset {
  id: string
  nombre: string
  primario: string
  secundario: string
  acento: string
}

export const BRAND_PRESETS: BrandPreset[] = [
  {
    id: 'azul_fosst',
    nombre: 'Azul FOSST',
    primario: '#002D62',
    secundario: '#0284C7',
    acento: '#F5A800',
  },
  {
    id: 'oceano_profundo',
    nombre: 'Océano profundo',
    primario: '#0B3C5D',
    secundario: '#1D7A8C',
    acento: '#F2A541',
  },
  {
    id: 'bosque_sereno',
    nombre: 'Bosque sereno',
    primario: '#1F4D3A',
    secundario: '#4C8C6B',
    acento: '#D9A441',
  },
  {
    id: 'indigo_moderno',
    nombre: 'Índigo moderno',
    primario: '#312E81',
    secundario: '#6366F1',
    acento: '#F59E0B',
  },
  {
    id: 'terracota_elegante',
    nombre: 'Terracota elegante',
    primario: '#7C3A2D',
    secundario: '#C2674A',
    acento: '#E8C07D',
  },
  {
    id: 'grafito_cobre',
    nombre: 'Grafito y cobre',
    primario: '#1F2933',
    secundario: '#52606D',
    acento: '#B87333',
  },
  {
    id: 'vino_arena',
    nombre: 'Vino y arena',
    primario: '#5B1E3A',
    secundario: '#8E3B5A',
    acento: '#D9B382',
  },
]

interface BrandPaletteDialogProps {
  isOpen: boolean
  onClose: () => void
  logoUrl?: string | null
}

export function BrandPaletteDialog({ isOpen, onClose, logoUrl }: BrandPaletteDialogProps) {
  const { branding, updateBranding, isUpdating } = useBranding()

  const [selectedPreset, setSelectedPreset] = useState<string>(branding.preset || 'azul_fosst')
  const [primario, setPrimario] = useState<string>(branding.primario || '#002D62')
  const [secundario, setSecundario] = useState<string>(branding.secundario || '#0284C7')
  const [acento, setAcento] = useState<string>(branding.acento || '#F5A800')

  // Estado de imagen de referencia
  const [imageSrc, setImageSrc] = useState<string | null>(null)
  const [isProcessingImage, setIsProcessingImage] = useState<boolean>(false)
  const [extractedSwatches, setExtractedSwatches] = useState<string[]>([])
  const [activeSwatchMenu, setActiveSwatchMenu] = useState<string | null>(null)
  const [pastedHexText, setPastedHexText] = useState<string>('')
  const [statusMessage, setStatusMessage] = useState<{ text: string; type: 'info' | 'success' | 'error' } | null>(null)

  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const previewCanvasRef = useRef<HTMLCanvasElement | null>(null)
  const imgRef = useRef<HTMLImageElement | null>(null)

  // Sincronizar estado cuando se abre el diálogo
  useEffect(() => {
    if (isOpen) {
      setSelectedPreset(branding.preset || 'azul_fosst')
      setPrimario(branding.primario || '#002D62')
      setSecundario(branding.secundario || '#0284C7')
      setAcento(branding.acento || '#F5A800')
      setStatusMessage(null)
      setActiveSwatchMenu(null)
    }
  }, [isOpen, branding])

  if (!isOpen) return null

  const handleSelectPreset = (preset: BrandPreset) => {
    setSelectedPreset(preset.id)
    setPrimario(preset.primario)
    setSecundario(preset.secundario)
    setAcento(preset.acento)
    setStatusMessage({ text: `Paleta "${preset.nombre}" aplicada.`, type: 'info' })
  }

  const handleCustomColorChange = (field: 'primario' | 'secundario' | 'acento', val: string) => {
    setSelectedPreset('custom')
    const upper = val.toUpperCase()
    if (field === 'primario') setPrimario(upper)
    if (field === 'secundario') setSecundario(upper)
    if (field === 'acento') setAcento(upper)
  }

  // ── Procesamiento de Imagen Local (File / Drag & Drop / Logo) ─────────────────

  const processImageElement = (img: HTMLImageElement) => {
    try {
      setIsProcessingImage(true)
      const colors = extractDominantColors(img, 8)
      if (colors.length > 0) {
        setExtractedSwatches(colors)
        setStatusMessage({
          text: `Se extrajeron ${colors.length} colores dominantes. Haz clic en una muestra para asignarlo o usa "Asignar automáticamente".`,
          type: 'success',
        })

        // Dibujar en el canvas de preview para el cuentagotas manual
        if (previewCanvasRef.current) {
          const cvs = previewCanvasRef.current
          const ctx = cvs.getContext('2d')
          if (ctx) {
            const aspect = (img.naturalWidth || img.width) / (img.naturalHeight || img.height)
            cvs.width = 240
            cvs.height = Math.round(240 / aspect)
            ctx.drawImage(img, 0, 0, cvs.width, cvs.height)
          }
        }
      } else {
        setStatusMessage({
          text: 'No se detectaron suficientes colores distintos en la imagen seleccionada.',
          type: 'error',
        })
      }
    } catch (e: any) {
      setStatusMessage({
        text: 'Error al procesar la imagen en el navegador. Intenta con otro archivo.',
        type: 'error',
      })
    } finally {
      setIsProcessingImage(false)
    }
  }

  const handleFileChange = (file: File) => {
    if (!file.type.startsWith('image/')) {
      setStatusMessage({ text: 'Por favor selecciona un archivo de imagen válido (PNG, JPG, WEBP).', type: 'error' })
      return
    }

    const reader = new FileReader()
    reader.onload = (e) => {
      const dataUrl = e.target?.result as string
      setImageSrc(dataUrl)

      const img = new Image()
      img.onload = () => processImageElement(img)
      img.src = dataUrl
      imgRef.current = img
    }
    reader.readAsDataURL(file)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0])
    }
  }

  const handleLoadLogo = () => {
    const mediaUrl = logoUrl ? resolveMediaUrl(logoUrl) : null
    if (!mediaUrl) {
      setStatusMessage({ text: 'La empresa aún no tiene un logotipo cargado.', type: 'error' })
      return
    }

    setIsProcessingImage(true)
    setStatusMessage({ text: 'Analizando el logotipo de la empresa...', type: 'info' })

    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => {
      setImageSrc(mediaUrl)
      imgRef.current = img
      processImageElement(img)
    }
    img.onerror = () => {
      setIsProcessingImage(false)
      setStatusMessage({ text: 'No fue posible cargar el logotipo corporativo (error de acceso CORS).', type: 'error' })
    }
    img.src = mediaUrl
  }

  // ── Asignación Automática y Manual ──────────────────────────────────────────

  const handleAutoAssign = () => {
    if (extractedSwatches.length === 0) return
    const assigned = autoAssignBrandPalette(extractedSwatches)
    setSelectedPreset('custom')
    setPrimario(assigned.primario)
    setSecundario(assigned.secundario)
    setAcento(assigned.acento)
    setStatusMessage({
      text: 'Paleta asignada automáticamente: Primario (base oscura), Secundario (tono distintivo) y Acento (tono cálido/vívido).',
      type: 'success',
    })
  }

  const assignSwatch = (hex: string, role: 'primario' | 'secundario' | 'acento') => {
    handleCustomColorChange(role, hex)
    setActiveSwatchMenu(null)
    setStatusMessage({ text: `Color ${hex} asignado como ${role.toUpperCase()}.`, type: 'info' })
  }

  // ── Cuentagotas (EyeDropper Nativo o Canvas) ────────────────────────────────

  const handleNativeEyeDropper = async () => {
    if (typeof window !== 'undefined' && 'EyeDropper' in window) {
      try {
        const eyeDropper = new (window as any).EyeDropper()
        const result = await eyeDropper.open()
        if (result?.sRGBHex) {
          const pickedHex = result.sRGBHex.toUpperCase()
          if (!extractedSwatches.includes(pickedHex)) {
            setExtractedSwatches((prev) => [pickedHex, ...prev.slice(0, 7)])
          }
          assignSwatch(pickedHex, 'primario')
          setStatusMessage({ text: `Color tomado: ${pickedHex}. Asignado a Primario.`, type: 'success' })
        }
      } catch (e) {
        // Canceled by user
      }
    } else {
      setStatusMessage({
        text: 'Haz clic directamente sobre la imagen cargada para seleccionar un píxel.',
        type: 'info',
      })
    }
  }

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = previewCanvasRef.current
    if (!canvas) return
    const rect = canvas.getBoundingClientRect()
    const x = Math.floor((e.clientX - rect.left) * (canvas.width / rect.width))
    const y = Math.floor((e.clientY - rect.top) * (canvas.height / rect.height))

    const ctx = canvas.getContext('2d')
    if (!ctx) return
    const pixel = ctx.getImageData(x, y, 1, 1).data
    const r = pixel[0]
    const g = pixel[1]
    const b = pixel[2]
    const toHex = (c: number) => c.toString(16).padStart(2, '0').toUpperCase()
    const pickedHex = `#${toHex(r)}${toHex(g)}${toHex(b)}`

    if (!extractedSwatches.includes(pickedHex)) {
      setExtractedSwatches((prev) => [pickedHex, ...prev.slice(0, 7)])
    }
    setActiveSwatchMenu(pickedHex)
  }

  // ── Pegar Colores HEX ───────────────────────────────────────────────────────

  const handleParsePastedHex = () => {
    const parsed = parseHexList(pastedHexText)
    if (parsed.length === 0) {
      setStatusMessage({ text: 'No se encontraron códigos HEX válidos en el texto ingresado.', type: 'error' })
      return
    }

    setExtractedSwatches(parsed.slice(0, 8))
    if (parsed.length >= 3) {
      setSelectedPreset('custom')
      setPrimario(parsed[0])
      setSecundario(parsed[1])
      setAcento(parsed[2])
      setStatusMessage({
        text: `Se aplicaron los 3 primeros colores (${parsed[0]}, ${parsed[1]}, ${parsed[2]}).`,
        type: 'success',
      })
    } else {
      assignSwatch(parsed[0], 'primario')
      setStatusMessage({ text: `Se cargó el color ${parsed[0]} como Primario.`, type: 'info' })
    }
    setPastedHexText('')
  }

  // ── Cálculos de Escalas Tonales y Contraste WCAG ───────────────────────────

  const primaryScale = generatePaletteScale(primario)
  const secondaryScale = generatePaletteScale(secundario)
  const accentScale = generatePaletteScale(acento)

  const contrastWhite = getContrastRatio('#FFFFFF', primario)
  const contrastDark = getContrastRatio('#0F172A', primario)
  const isPrimaryLowContrast = contrastWhite < 4.5 && contrastDark < 4.5
  const recommendedTextForPrimary = contrastText(primario)

  // Guardar configuración sin sobrescribir mapa_procesos con valores fijos
  const handleSave = async () => {
    await updateBranding({
      preset: selectedPreset,
      primario,
      secundario,
      acento,
    })
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-3 sm:p-5">
      <div className="bg-white rounded-2xl max-w-5xl w-full overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200 flex flex-col max-h-[92vh]">
        {/* Header Modal */}
        <div className="bg-slate-900 text-white px-6 py-4 flex justify-between items-center border-b border-slate-800 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-brand-500/20 text-brand-400">
              <Palette className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-extrabold text-base tracking-tight">
                Identidad Visual y Paleta Corporativa
              </h3>
              <p className="text-xs text-slate-400">
                Define la armonía cromática para todo el software, el organigrama y el mapa de procesos
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Mensaje de estado dinámico */}
        {statusMessage && (
          <div
            className={`px-6 py-2.5 text-xs flex items-center justify-between border-b transition-all flex-shrink-0 ${
              statusMessage.type === 'error'
                ? 'bg-rose-50 text-rose-800 border-rose-200'
                : statusMessage.type === 'success'
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : 'bg-blue-50 text-blue-800 border-blue-200'
            }`}
          >
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 flex-shrink-0" />
              <span className="font-medium">{statusMessage.text}</span>
            </div>
            <button
              onClick={() => setStatusMessage(null)}
              className="p-1 hover:opacity-75 text-current"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Cuerpo del Modal */}
        <div className="p-6 overflow-y-auto flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Columna Izquierda: Herramientas de Creación y Selección */}
          <div className="lg:col-span-7 space-y-6">
            {/* 1. SECCIÓN: PALETA DESDE IMAGEN DE REFERENCIA */}
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-3.5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-xs font-extrabold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                  <ImageIcon className="w-4 h-4 text-brand-600" />
                  Paleta desde Imagen de Referencia
                </span>
                <div className="flex items-center gap-2">
                  {logoUrl && (
                    <button
                      type="button"
                      onClick={handleLoadLogo}
                      disabled={isProcessingImage}
                      className="text-xs font-bold text-brand-700 bg-brand-50 hover:bg-brand-100 border border-brand-200 px-2.5 py-1 rounded-lg flex items-center gap-1 transition"
                    >
                      <Wand2 className="w-3.5 h-3.5" />
                      Usar logo de la empresa
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={handleNativeEyeDropper}
                    className="text-xs font-bold text-slate-700 bg-white hover:bg-slate-100 border border-slate-200 px-2.5 py-1 rounded-lg flex items-center gap-1 transition"
                    title="Tomar color exacto de cualquier punto de la pantalla"
                  >
                    <Pipette className="w-3.5 h-3.5 text-slate-600" />
                    Cuentagotas
                  </button>
                </div>
              </div>

              {/* Zona Drag & Drop o Selector */}
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`
                  border-2 border-dashed rounded-xl p-3 text-center cursor-pointer transition-all flex flex-col items-center justify-center gap-2
                  ${
                    imageSrc
                      ? 'border-brand-400 bg-brand-50/20'
                      : 'border-slate-300 hover:border-brand-400 hover:bg-slate-100/50'
                  }
                `}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      handleFileChange(e.target.files[0])
                    }
                  }}
                />

                {imageSrc ? (
                  <div className="flex items-center gap-3 w-full justify-center">
                    <canvas
                      ref={previewCanvasRef}
                      onClick={(e) => {
                        e.stopPropagation()
                        handleCanvasClick(e)
                      }}
                      className="max-h-24 max-w-full rounded-lg border border-slate-200 shadow-xs cursor-crosshair object-contain bg-white"
                      title="Haz clic sobre la imagen para tomar un color exacto"
                    />
                    <div className="text-left text-xs space-y-1">
                      <span className="font-bold text-slate-800 block">Imagen cargada</span>
                      <span className="text-[11px] text-slate-500 block">
                        Haz clic en la imagen con la mira para seleccionar un color específico
                      </span>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          setImageSrc(null)
                          setExtractedSwatches([])
                        }}
                        className="text-[11px] font-bold text-rose-600 hover:underline"
                      >
                        Quitar imagen
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="w-8 h-8 rounded-full bg-brand-50 text-brand-600 flex items-center justify-center">
                      <Upload className="w-4 h-4" />
                    </div>
                    <div className="text-xs text-slate-600">
                      <span className="font-bold text-brand-600">Haz clic para subir</span> o arrastra una imagen (manual de marca, captura de paleta o logo)
                    </div>
                    <span className="text-[10px] text-slate-400">PNG, JPG o WEBP (procesada localmente en tu navegador)</span>
                  </>
                )}
              </div>

              {/* Muestras Extraídas de la Imagen */}
              {extractedSwatches.length > 0 && (
                <div className="space-y-2 pt-1 border-t border-slate-200">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold text-slate-600">
                      Colores dominantes detectados ({extractedSwatches.length}):
                    </span>
                    <button
                      type="button"
                      onClick={handleAutoAssign}
                      className="text-xs font-bold text-brand-700 hover:text-brand-800 flex items-center gap-1"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      Asignar automáticamente
                    </button>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    {extractedSwatches.map((hex) => {
                      const isPrim = primario === hex
                      const isSec = secundario === hex
                      const isAce = acento === hex
                      const isMenuOpen = activeSwatchMenu === hex

                      return (
                        <div key={hex} className="relative">
                          <button
                            type="button"
                            onClick={() => setActiveSwatchMenu(isMenuOpen ? null : hex)}
                            className="group flex flex-col items-center gap-1 p-1 rounded-xl border border-slate-200 hover:border-brand-500 bg-white transition shadow-xs"
                          >
                            <span
                              className="w-7 h-7 rounded-lg shadow-inner flex items-center justify-center text-[10px] font-extrabold text-white"
                              style={{ backgroundColor: hex }}
                            >
                              {isPrim && 'P'}
                              {isSec && 'S'}
                              {isAce && 'A'}
                            </span>
                            <span className="text-[10px] font-mono font-bold text-slate-700">
                              {hex}
                            </span>
                          </button>

                          {/* Popover de Asignación */}
                          {isMenuOpen && (
                            <div className="absolute top-full mt-1.5 left-0 z-30 bg-slate-900 text-white rounded-xl shadow-xl p-2 min-w-[150px] space-y-1 text-xs animate-in fade-in duration-150">
                              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider px-2 py-0.5 block">
                                Asignar {hex} como:
                              </span>
                              <button
                                type="button"
                                onClick={() => assignSwatch(hex, 'primario')}
                                className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-slate-800 font-bold flex items-center justify-between text-brand-300"
                              >
                                Primario {isPrim && <Check className="w-3.5 h-3.5" />}
                              </button>
                              <button
                                type="button"
                                onClick={() => assignSwatch(hex, 'secundario')}
                                className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-slate-800 font-bold flex items-center justify-between text-sky-300"
                              >
                                Secundario {isSec && <Check className="w-3.5 h-3.5" />}
                              </button>
                              <button
                                type="button"
                                onClick={() => assignSwatch(hex, 'acento')}
                                className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-slate-800 font-bold flex items-center justify-between text-amber-300"
                              >
                                Acento {isAce && <Check className="w-3.5 h-3.5" />}
                              </button>
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Pegar colores HEX */}
              <div className="pt-2 border-t border-slate-200 flex items-center gap-2">
                <div className="relative flex-1">
                  <Input
                    value={pastedHexText}
                    onChange={(e) => setPastedHexText(e.target.value)}
                    placeholder="Pegar colores HEX (ej. #002D62, #0284C7, #F5A800)"
                    className="text-xs font-mono py-1.5 pr-2 bg-white"
                  />
                </div>
                <button
                  type="button"
                  onClick={handleParsePastedHex}
                  className="px-3 py-2 bg-slate-200 hover:bg-slate-300 text-slate-800 rounded-xl text-xs font-bold flex items-center gap-1 transition flex-shrink-0"
                >
                  <ClipboardPaste className="w-3.5 h-3.5" />
                  Aplicar HEX
                </button>
              </div>
            </div>

            {/* 2. SECCIÓN: SELECTORES MANUALES Y ESCALA TONAL 50-900 */}
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-4">
              <span className="text-xs font-extrabold text-slate-700 uppercase tracking-wider block">
                Calibración y Escalas Tonales (50–900)
              </span>

              {/* Selector Primario */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-[11px] font-bold text-slate-700">
                    Color Primario (Estructura, Botón principal, Procesos Estratégicos)
                  </label>
                  <span className="text-[10px] font-mono text-slate-500">{primario}</span>
                </div>
                <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-xl p-1.5 shadow-xs">
                  <input
                    type="color"
                    value={primario}
                    onChange={(e) => handleCustomColorChange('primario', e.target.value)}
                    className="w-8 h-8 rounded-lg border-none cursor-pointer bg-transparent"
                  />
                  <input
                    type="text"
                    value={primario}
                    onChange={(e) => handleCustomColorChange('primario', e.target.value)}
                    className="text-xs font-mono font-bold text-slate-800 w-full focus:outline-none uppercase"
                  />
                </div>
                {/* Tira escala tonal 50-900 */}
                <div className="grid grid-cols-10 h-3 rounded-md overflow-hidden border border-slate-200 shadow-2xs">
                  {([50, 100, 200, 300, 400, 500, 600, 700, 800, 900] as const).map((shade) => (
                    <div
                      key={shade}
                      style={{ backgroundColor: primaryScale[shade].hex }}
                      title={`Tono ${shade}: ${primaryScale[shade].hex}`}
                    />
                  ))}
                </div>
              </div>

              {/* Selector Secundario */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-[11px] font-bold text-slate-700">
                    Color Secundario (Chips de área, Procesos Misionales, Botón secundario)
                  </label>
                  <span className="text-[10px] font-mono text-slate-500">{secundario}</span>
                </div>
                <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-xl p-1.5 shadow-xs">
                  <input
                    type="color"
                    value={secundario}
                    onChange={(e) => handleCustomColorChange('secundario', e.target.value)}
                    className="w-8 h-8 rounded-lg border-none cursor-pointer bg-transparent"
                  />
                  <input
                    type="text"
                    value={secundario}
                    onChange={(e) => handleCustomColorChange('secundario', e.target.value)}
                    className="text-xs font-mono font-bold text-slate-800 w-full focus:outline-none uppercase"
                  />
                </div>
                {/* Tira escala tonal 50-900 */}
                <div className="grid grid-cols-10 h-3 rounded-md overflow-hidden border border-slate-200 shadow-2xs">
                  {([50, 100, 200, 300, 400, 500, 600, 700, 800, 900] as const).map((shade) => (
                    <div
                      key={shade}
                      style={{ backgroundColor: secondaryScale[shade].hex }}
                      title={`Tono ${shade}: ${secondaryScale[shade].hex}`}
                    />
                  ))}
                </div>
              </div>

              {/* Selector Acento */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-[11px] font-bold text-slate-700">
                    Color de Acento (Alertas, Franja Entradas, Distintivos activos)
                  </label>
                  <span className="text-[10px] font-mono text-slate-500">{acento}</span>
                </div>
                <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-xl p-1.5 shadow-xs">
                  <input
                    type="color"
                    value={acento}
                    onChange={(e) => handleCustomColorChange('acento', e.target.value)}
                    className="w-8 h-8 rounded-lg border-none cursor-pointer bg-transparent"
                  />
                  <input
                    type="text"
                    value={acento}
                    onChange={(e) => handleCustomColorChange('acento', e.target.value)}
                    className="text-xs font-mono font-bold text-slate-800 w-full focus:outline-none uppercase"
                  />
                </div>
                {/* Tira escala tonal 50-900 */}
                <div className="grid grid-cols-10 h-3 rounded-md overflow-hidden border border-slate-200 shadow-2xs">
                  {([50, 100, 200, 300, 400, 500, 600, 700, 800, 900] as const).map((shade) => (
                    <div
                      key={shade}
                      style={{ backgroundColor: accentScale[shade].hex }}
                      title={`Tono ${shade}: ${accentScale[shade].hex}`}
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* 3. SECCIÓN: PRESETS RECOMENDADOS */}
            <div className="space-y-2.5">
              <span className="text-xs font-extrabold text-slate-700 uppercase tracking-wider block">
                Paletas Recomendadas Curadas
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {BRAND_PRESETS.map((preset) => {
                  const isSelected = selectedPreset === preset.id
                  return (
                    <button
                      key={preset.id}
                      type="button"
                      onClick={() => handleSelectPreset(preset)}
                      className={`
                        p-2.5 rounded-xl border text-left transition-all flex items-center justify-between group
                        ${
                          isSelected
                            ? 'border-brand-500 bg-brand-50/20 shadow-xs ring-1 ring-brand-500'
                            : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                        }
                      `}
                    >
                      <div className="space-y-1">
                        <span className="text-xs font-bold text-slate-800 block">
                          {preset.nombre}
                        </span>
                        <div className="flex items-center gap-1.5">
                          <span
                            className="w-3.5 h-3.5 rounded-full border border-black/10 shadow-2xs"
                            style={{ backgroundColor: preset.primario }}
                            title="Primario"
                          />
                          <span
                            className="w-3.5 h-3.5 rounded-full border border-black/10 shadow-2xs"
                            style={{ backgroundColor: preset.secundario }}
                            title="Secundario"
                          />
                          <span
                            className="w-3.5 h-3.5 rounded-full border border-black/10 shadow-2xs"
                            style={{ backgroundColor: preset.acento }}
                            title="Acento"
                          />
                        </div>
                      </div>
                      {isSelected && (
                        <div className="w-5 h-5 rounded-full bg-brand-500 text-white flex items-center justify-center flex-shrink-0">
                          <Check className="w-3 h-3" />
                        </div>
                      )}
                    </button>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Columna Derecha: Vista Previa en Vivo Completa */}
          <div className="lg:col-span-5 space-y-4">
            <span className="text-xs font-extrabold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
              <Eye className="w-4 h-4 text-slate-500" />
              Vista Previa en Vivo de Identidad
            </span>

            <div className="border border-slate-200 rounded-2xl overflow-hidden bg-slate-100/70 p-4 space-y-4 shadow-inner">
              {/* 1. Muestra Encabezado Corporativo */}
              <div
                className="p-4 rounded-xl shadow-md text-white transition-all space-y-2"
                style={{ backgroundColor: primario, color: recommendedTextForPrimary }}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-black uppercase tracking-wider opacity-90">
                    FOSST V.I.D.A.
                  </span>
                  <span
                    className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold shadow-xs"
                    style={{ backgroundColor: acento, color: contrastText(acento) }}
                  >
                    Activo
                  </span>
                </div>
                <div className="text-sm font-extrabold">Sistema Integrado de Gestión SG-SST</div>
                <div
                  className="h-1.5 rounded-full opacity-50 overflow-hidden"
                  style={{ backgroundColor: secundario }}
                >
                  <div className="h-full w-3/4 bg-white" />
                </div>
              </div>

              {/* 2. Botones de Interfaz */}
              <div className="p-3 bg-white rounded-xl border border-slate-200 space-y-2">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                  Estilos de Botón
                </span>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    className="px-3 py-1.5 rounded-lg text-xs font-bold text-white shadow-xs transition-all"
                    style={{ backgroundColor: primario, color: recommendedTextForPrimary }}
                  >
                    Botón Primario
                  </button>
                  <button
                    type="button"
                    className="px-3 py-1.5 rounded-lg text-xs font-bold text-white shadow-xs transition-all"
                    style={{ backgroundColor: secundario, color: contrastText(secundario) }}
                  >
                    Secundario
                  </button>
                  <button
                    type="button"
                    className="px-3 py-1.5 rounded-lg text-xs font-bold shadow-xs transition-all"
                    style={{ backgroundColor: acento, color: contrastText(acento) }}
                  >
                    Acento
                  </button>
                </div>
              </div>

              {/* 3. Miniatura del Organigrama */}
              <div className="p-3 bg-white rounded-xl border border-slate-200 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                    <GitBranch className="w-3 h-3 text-slate-500" />
                    Miniatura Organigrama
                  </span>
                  <span className="text-[9px] font-bold text-slate-400">Layout Jerárquico</span>
                </div>

                <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100 flex flex-col items-center gap-2">
                  {/* Nodo Padre */}
                  <div
                    className="px-3 py-1.5 rounded-lg bg-white border border-slate-200 shadow-2xs border-l-4 text-[10px] font-bold text-slate-800 flex items-center gap-1.5"
                    style={{ borderLeftColor: primario }}
                  >
                    <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: primario }} />
                    Gerencia General
                  </div>

                  {/* Conector */}
                  <div className="w-px h-3 bg-slate-300 relative">
                    <div className="absolute top-full left-1/2 -translate-x-1/2 w-28 h-px bg-slate-300" />
                  </div>

                  {/* Hijos */}
                  <div className="flex items-center gap-3 pt-1">
                    <div
                      className="px-2.5 py-1 rounded-lg bg-white border border-slate-200 shadow-2xs border-l-4 text-[9px] font-semibold text-slate-700 flex items-center gap-1"
                      style={{ borderLeftColor: secundario }}
                    >
                      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: secundario }} />
                      Responsable SST
                    </div>
                    <div
                      className="px-2.5 py-1 rounded-lg bg-white border border-slate-200 shadow-2xs border-l-4 text-[9px] font-semibold text-slate-700 flex items-center gap-1"
                      style={{ borderLeftColor: acento }}
                    >
                      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: acento }} />
                      Operaciones
                    </div>
                  </div>
                </div>
              </div>

              {/* 4. Miniatura del Mapa de Procesos */}
              <div className="p-3 bg-white rounded-xl border border-slate-200 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                    <Workflow className="w-3 h-3 text-slate-500" />
                    Miniatura Mapa de Procesos
                  </span>
                  <span className="text-[9px] font-bold text-slate-400">Entradas / Núcleo / Salidas</span>
                </div>

                <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100 grid grid-cols-12 gap-1.5 items-center">
                  {/* Flecha Entradas */}
                  <div
                    className="col-span-3 rounded-md p-1.5 text-center shadow-2xs"
                    style={{ backgroundColor: acento, color: contrastText(acento) }}
                  >
                    <span className="text-[8px] font-black uppercase block leading-tight">Entradas</span>
                    <span className="text-[7px] opacity-90 block truncate">Requisitos</span>
                  </div>

                  {/* Núcleo Central */}
                  <div className="col-span-6 space-y-1">
                    <div
                      className="px-2 py-1 rounded text-[8px] font-bold truncate text-center shadow-2xs"
                      style={{ backgroundColor: primario, color: recommendedTextForPrimary }}
                    >
                      Estratégicos
                    </div>
                    <div
                      className="px-2 py-1 rounded text-[8px] font-bold truncate text-center shadow-2xs"
                      style={{ backgroundColor: secundario, color: contrastText(secundario) }}
                    >
                      Misionales
                    </div>
                    <div className="px-2 py-1 rounded text-[8px] font-bold truncate text-center bg-slate-200 text-slate-700 shadow-2xs">
                      Apoyo
                    </div>
                  </div>

                  {/* Flecha Salidas */}
                  <div className="col-span-3 rounded-md p-1.5 text-center bg-emerald-600 text-white shadow-2xs">
                    <span className="text-[8px] font-black uppercase block leading-tight">Salidas</span>
                    <span className="text-[7px] opacity-90 block truncate">Resultados</span>
                  </div>
                </div>
              </div>

              {/* Advertencia de Contraste WCAG si aplica */}
              {isPrimaryLowContrast && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-2.5 text-amber-900">
                  <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                  <div className="text-[11px] space-y-0.5">
                    <span className="font-extrabold block">Advertencia de Contraste (WCAG 2.1)</span>
                    <p className="text-amber-800 leading-tight">
                      El contraste sobre blanco es {contrastWhite.toFixed(1)}:1. El texto se adaptará automáticamente a {recommendedTextForPrimary === '#FFFFFF' ? 'blanco' : 'oscuro'}.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer Modal */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between flex-shrink-0">
          <div className="text-xs text-slate-500 font-medium flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            Cumple con contraste WCAG 2.1 AA
          </div>

          <div className="flex gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-bold text-slate-600 hover:text-slate-800 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition-all"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={isUpdating}
              className="px-5 py-2 text-xs font-bold text-white bg-slate-900 hover:bg-slate-800 rounded-xl shadow-md transition-all flex items-center gap-1.5"
            >
              {isUpdating ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Check className="w-4 h-4 text-emerald-400" />
              )}
              Guardar Identidad Visual
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
