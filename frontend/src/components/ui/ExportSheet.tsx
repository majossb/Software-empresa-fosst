import React, { useEffect, useState } from 'react'
import { resolveMediaUrl } from '@/services/api.client'
import { contrastText } from '@/utils/color.utils'
import { ShieldCheck } from 'lucide-react'

export interface ExportSheetProps {
  title: string
  subtitle?: string
  empresaNombre?: string
  empresaNit?: string
  logoUrl?: string | null
  primaryColor?: string
  secondaryColor?: string
  accentColor?: string
  children: React.ReactNode
}

/**
 * Convierte una imagen (URL o relativa) a Data URL base64 para evitar errores CORS en html2canvas y exportaciones.
 */
export async function getLogoDataUrl(logoUrl: string | null | undefined): Promise<string | null> {
  if (!logoUrl) return null
  const mediaUrl = resolveMediaUrl(logoUrl)
  try {
    const res = await fetch(mediaUrl, { mode: 'cors' })
    if (!res.ok) return null
    const blob = await res.blob()
    return new Promise((resolve) => {
      const reader = new FileReader()
      reader.onloadend = () => resolve(reader.result as string)
      reader.onerror = () => resolve(null)
      reader.readAsDataURL(blob)
    })
  } catch (e) {
    console.warn('No se pudo convertir el logotipo a Data URL:', e)
    return null
  }
}

// ── React component (for in-page use) ──────────────────────────────
export const ExportSheet: React.FC<ExportSheetProps> = ({
  title,
  subtitle,
  empresaNombre = 'EMPRESA REGISTRADA',
  empresaNit,
  logoUrl,
  primaryColor = '#002D62',
  secondaryColor = '#0284C7',
  accentColor = '#F5A800',
  children,
}) => {
  const [dataUrlLogo, setDataUrlLogo] = useState<string | null>(null)
  const headerTextColor = contrastText(primaryColor)

  useEffect(() => {
    let isMounted = true
    getLogoDataUrl(logoUrl).then((base64) => {
      if (isMounted) setDataUrlLogo(base64)
    })
    return () => {
      isMounted = false
    }
  }, [logoUrl])

  const fechaImpresion = new Date().toLocaleDateString('es-CO', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  return (
    <div className="w-full bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-lg font-sans">
      {/* Encabezado Corporativo de Marca */}
      <div
        className="p-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 transition-all"
        style={{ backgroundColor: primaryColor, color: headerTextColor }}
      >
        <div className="flex items-center gap-4">
          {/* Logo sobre Placa Blanca Redondeada si existe */}
          {dataUrlLogo ? (
            <div className="w-14 h-14 rounded-2xl bg-white p-2 flex items-center justify-center shadow-md flex-shrink-0">
              <img
                src={dataUrlLogo}
                alt={`Logo ${empresaNombre}`}
                className="w-full h-full object-contain"
              />
            </div>
          ) : (
            <div className="w-12 h-12 rounded-2xl bg-white/15 border border-white/20 p-2 flex items-center justify-center flex-shrink-0 text-white">
              <ShieldCheck className="w-7 h-7" />
            </div>
          )}

          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <span className="text-xs font-black uppercase tracking-widest opacity-90">
                {empresaNombre}
              </span>
              {empresaNit && (
                <span className="text-[11px] font-medium opacity-80 font-mono">
                  • NIT: {empresaNit}
                </span>
              )}
            </div>
            <h2 className="text-xl font-black tracking-tight">{title}</h2>
            {subtitle && (
              <p className="text-xs opacity-85 font-medium">{subtitle}</p>
            )}
          </div>
        </div>

        {/* Bloque Fecha y Marca FOSST */}
        <div className="text-right space-y-1 flex-shrink-0 self-end sm:self-auto">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-extrabold shadow-xs bg-white/15 border border-white/20">
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: accentColor }}
            />
            <span>Documento Oficial SG-SST</span>
          </div>
          <p className="text-[11px] opacity-80 font-mono">
            Fecha: {fechaImpresion}
          </p>
        </div>
      </div>

      {/* Contenido Principal */}
      <div className="p-6 bg-slate-50">{children}</div>

      {/* Pie de Página FOSST V.I.D.A. */}
      <div className="px-6 py-3 bg-slate-100 border-t border-slate-200 flex justify-between items-center text-[11px] text-slate-500 font-semibold">
        <span>
          FOSST V.I.D.A. — Sistema Integrado de Gestión de Seguridad y Salud en el Trabajo
        </span>
        <span className="font-mono text-[10px]">ISO 45001 / Decreto 1072 de 2015</span>
      </div>
    </div>
  )
}

// ── Utilidades para impresión y exportación aislada ─────────────────

export interface ExportSheetConfig {
  title: string
  subtitle?: string
  empresaNombre: string
  empresaNit?: string
  logoDataUrl?: string | null
  primaryColor: string
  secondaryColor: string
  accentColor: string
  /** HTML del contenido del mapa (se inyecta dentro del body) */
  mapInnerHTML: string
}

/**
 * Genera la cadena HTML auto-contenida del ExportSheet con encabezado de marca,
 * contenido del mapa y pie de página. Incluye estilos inline y @media print.
 */
export function renderExportSheetHTML(cfg: ExportSheetConfig): string {
  const headerText = contrastText(cfg.primaryColor)
  const fecha = new Date().toLocaleDateString('es-CO', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  const logoBlock = cfg.logoDataUrl
    ? `<div style="width:52px;height:52px;border-radius:14px;background:#fff;padding:6px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,.12);flex-shrink:0">
         <img src="${cfg.logoDataUrl}" alt="Logo" style="max-width:100%;max-height:100%;object-fit:contain"/>
       </div>`
    : ''

  const nitBlock = cfg.empresaNit
    ? `<span style="font-size:11px;font-weight:500;opacity:.8;font-family:monospace"> · NIT: ${cfg.empresaNit}</span>`
    : ''

  const subtitleBlock = cfg.subtitle
    ? `<p style="font-size:11px;opacity:.85;margin:2px 0 0">${cfg.subtitle}</p>`
    : ''

  return `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<title>${cfg.title}</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html, body {
    width: 100%; height: 100%;
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    color-adjust: exact !important;
    background: #fff;
  }
  @page {
    size: A3 landscape;
    margin: 10mm;
  }
  @media print {
    html, body { width: 100%; height: auto; }
    .export-sheet { break-inside: avoid; page-break-inside: avoid; }
    .map-content { break-inside: avoid; page-break-inside: avoid; }
    .map-content * { break-inside: avoid; page-break-inside: avoid; }
  }
  .export-sheet {
    width: 100%;
    background: #fff;
    border-radius: 0;
    overflow: hidden;
  }
  .header {
    padding: 20px 28px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    background-color: ${cfg.primaryColor};
    color: ${headerText};
  }
  .header-left {
    display: flex;
    align-items: center;
    gap: 14px;
  }
  .header-info { line-height: 1.3; }
  .header-empresa {
    font-size: 11px;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: .08em;
    opacity: .92;
  }
  .header-title {
    font-size: 18px;
    font-weight: 900;
    letter-spacing: -.01em;
    margin: 2px 0 0;
  }
  .header-right {
    text-align: right;
    flex-shrink: 0;
  }
  .badge-oficial {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 800;
    background: rgba(255,255,255,.15);
    border: 1px solid rgba(255,255,255,.2);
  }
  .badge-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background-color: ${cfg.accentColor};
  }
  .header-fecha {
    font-size: 11px;
    opacity: .8;
    font-family: monospace;
    margin-top: 4px;
  }
  .map-content {
    padding: 24px;
    background: #f8fafc;
  }
  .map-content > div {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
  }
  .footer {
    padding: 10px 28px;
    background: #f1f5f9;
    border-top: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
    color: #64748b;
    font-weight: 600;
  }
  .footer-mono {
    font-family: monospace;
    font-size: 10px;
  }
</style>
</head>
<body>
<div class="export-sheet">
  <!-- Encabezado -->
  <div class="header">
    <div class="header-left">
      ${logoBlock}
      <div class="header-info">
        <div>
          <span class="header-empresa">${cfg.empresaNombre}</span>
          ${nitBlock}
        </div>
        <div class="header-title">${cfg.title}</div>
        ${subtitleBlock}
      </div>
    </div>
    <div class="header-right">
      <div class="badge-oficial">
        <span class="badge-dot"></span>
        <span>Documento Oficial SG-SST</span>
      </div>
      <div class="header-fecha">Fecha: ${fecha}</div>
    </div>
  </div>

  <!-- Contenido del Mapa -->
  <div class="map-content">
    ${cfg.mapInnerHTML}
  </div>

  <!-- Pie de página -->
  <div class="footer">
    <span>FOSST V.I.D.A. — Sistema Integrado de Gestión de Seguridad y Salud en el Trabajo</span>
    <span class="footer-mono">ISO 45001 / Decreto 1072 de 2015</span>
  </div>
</div>
</body>
</html>`
}

/**
 * Espera a que todas las imágenes dentro de un document estén cargadas.
 */
function waitForImages(doc: Document): Promise<void> {
  const imgs = Array.from(doc.querySelectorAll('img'))
  if (imgs.length === 0) return Promise.resolve()
  return Promise.all(
    imgs.map(
      (img) =>
        new Promise<void>((resolve) => {
          if (img.complete && img.naturalWidth > 0) {
            resolve()
          } else {
            img.onload = () => resolve()
            img.onerror = () => resolve()
          }
        })
    )
  ).then(() => {})
}

/**
 * Imprime el ExportSheet en un iframe aislado (no afecta la página principal).
 * Crea un iframe oculto, inyecta el HTML con estilos de impresión,
 * espera a las imágenes, dispara print y limpia.
 */
export async function printExportSheet(cfg: ExportSheetConfig): Promise<void> {
  const html = renderExportSheetHTML(cfg)

  // Crear iframe oculto
  const iframe = document.createElement('iframe')
  iframe.style.position = 'fixed'
  iframe.style.top = '-10000px'
  iframe.style.left = '-10000px'
  iframe.style.width = '1400px'
  iframe.style.height = '1000px'
  iframe.style.border = 'none'
  iframe.style.opacity = '0'
  iframe.style.pointerEvents = 'none'
  document.body.appendChild(iframe)

  try {
    const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document
    if (!iframeDoc) throw new Error('No se pudo acceder al documento del iframe')

    iframeDoc.open()
    iframeDoc.write(html)
    iframeDoc.close()

    // Esperar imágenes + breve pausa para render
    await waitForImages(iframeDoc)
    await new Promise((r) => setTimeout(r, 300))

    iframe.contentWindow?.focus()
    iframe.contentWindow?.print()

    // Limpiar después de un delay para que el diálogo de impresión se cierre
    setTimeout(() => {
      try { document.body.removeChild(iframe) } catch (_) {}
    }, 2000)
  } catch (err) {
    console.error('Error al imprimir el mapa:', err)
    try { document.body.removeChild(iframe) } catch (_) {}
    throw err
  }
}

/**
 * Exporta el ExportSheet como PNG usando html2canvas.
 * Renderiza en un contenedor off-screen temporal, captura y descarga.
 */
export async function exportSheetToPNG(
  cfg: ExportSheetConfig,
  filename?: string
): Promise<void> {
  const { default: html2canvas } = await import('html2canvas')

  const html = renderExportSheetHTML(cfg)

  // Crear contenedor off-screen
  const container = document.createElement('div')
  container.style.position = 'fixed'
  container.style.top = '-20000px'
  container.style.left = '-20000px'
  container.style.width = '1400px'
  container.style.zIndex = '-9999'
  container.style.opacity = '1' // html2canvas necesita opacidad 1
  container.style.background = '#fff'
  document.body.appendChild(container)

  try {
    // Crear un iframe para aislar los estilos
    const iframe = document.createElement('iframe')
    iframe.style.width = '1400px'
    iframe.style.height = '2000px'
    iframe.style.border = 'none'
    container.appendChild(iframe)

    const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document
    if (!iframeDoc) throw new Error('No se pudo acceder al documento del iframe')

    iframeDoc.open()
    iframeDoc.write(html)
    iframeDoc.close()

    await waitForImages(iframeDoc)
    await new Promise((r) => setTimeout(r, 400))

    // Capturar el contenido del body del iframe
    const target = iframeDoc.querySelector('.export-sheet') as HTMLElement
    if (!target) throw new Error('No se encontró el .export-sheet en el iframe')

    const canvas = await html2canvas(target, {
      scale: 2.5,
      useCORS: true,
      backgroundColor: '#ffffff',
      logging: false,
      // html2canvas with iframe context
      windowWidth: 1400,
      windowHeight: target.scrollHeight + 100,
    })

    const link = document.createElement('a')
    link.download = filename || `Mapa_Procesos_${new Date().toISOString().slice(0, 10)}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
  } catch (err) {
    console.error('Error exportando PNG:', err)
    alert('Hubo un error al exportar el mapa de procesos.')
  } finally {
    try { document.body.removeChild(container) } catch (_) {}
  }
}
