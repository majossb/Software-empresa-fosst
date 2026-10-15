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

// ── Helpers internos ────────────────────────────────────────────────

/**
 * Recoge todas las hojas de estilo del documento principal (<style> y <link rel="stylesheet">)
 * para inyectarlas en el <head> de iframes aislados.
 */
function collectParentStyles(): string {
  const parts: string[] = []
  document.querySelectorAll('style').forEach((el) => {
    parts.push(`<style>${el.textContent || ''}</style>`)
  })
  document.querySelectorAll('link[rel="stylesheet"]').forEach((el) => {
    const href = (el as HTMLLinkElement).href
    if (href) parts.push(`<link rel="stylesheet" href="${href}"/>`)
  })
  return parts.join('\n')
}

/**
 * Espera a que todas las <link rel="stylesheet"> carguen en un document.
 */
function waitForStylesheets(doc: Document): Promise<void> {
  const links = Array.from(doc.querySelectorAll('link[rel="stylesheet"]')) as HTMLLinkElement[]
  if (links.length === 0) return Promise.resolve()
  return Promise.all(
    links.map(
      (link) =>
        new Promise<void>((resolve) => {
          try {
            if (link.sheet) { resolve(); return }
          } catch (_) { /* cross-origin sheet, esperamos onload */ }
          link.onload = () => resolve()
          link.onerror = () => resolve()
        })
    )
  ).then(() => {})
}

/**
 * Espera a que todas las imágenes dentro de un root estén cargadas.
 * Acepta tanto Document como HTMLElement.
 */
function waitForImages(root: Document | HTMLElement): Promise<void> {
  const imgs = Array.from(root.querySelectorAll('img'))
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
 * Construye el HTML del cuerpo del ExportSheet (encabezado + mapa + pie)
 * usando SOLO estilos inline para encabezado y pie, de modo que no dependa
 * de ningún CSS externo. El mapInnerHTML ya debe venir con estilos inline
 * aplicados (ver applyComputedInlineStyles en ProcesosView).
 */
function buildExportSheetBody(cfg: ExportSheetConfig): string {
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

  return `
<div class="export-sheet" style="width:100%;background:#fff;overflow:hidden;font-family:Inter,'Segoe UI',system-ui,-apple-system,sans-serif;border-radius:0">
  <!-- Encabezado -->
  <div style="padding:20px 28px;display:flex;justify-content:space-between;align-items:center;gap:16px;background-color:${cfg.primaryColor};color:${headerText}">
    <div style="display:flex;align-items:center;gap:14px">
      ${logoBlock}
      <div style="line-height:1.3">
        <div>
          <span style="font-size:11px;font-weight:900;text-transform:uppercase;letter-spacing:.08em;opacity:.92">${cfg.empresaNombre}</span>
          ${nitBlock}
        </div>
        <div style="font-size:18px;font-weight:900;letter-spacing:-.01em;margin:2px 0 0">${cfg.title}</div>
        ${subtitleBlock}
      </div>
    </div>
    <div style="text-align:right;flex-shrink:0">
      <div style="display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:999px;font-size:11px;font-weight:800;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.2)">
        <span style="width:8px;height:8px;border-radius:50%;display:inline-block;background-color:${cfg.accentColor}"></span>
        <span>Documento Oficial SG-SST</span>
      </div>
      <div style="font-size:11px;opacity:.8;font-family:monospace;margin-top:4px">Fecha: ${fecha}</div>
    </div>
  </div>

  <!-- Contenido del Mapa -->
  <div style="padding:24px;background:#f8fafc">
    ${cfg.mapInnerHTML}
  </div>

  <!-- Pie de página -->
  <div style="padding:10px 28px;background:#f1f5f9;border-top:1px solid #e2e8f0;display:flex;justify-content:space-between;align-items:center;font-size:11px;color:#64748b;font-weight:600">
    <span>FOSST V.I.D.A. — Sistema Integrado de Gestión de Seguridad y Salud en el Trabajo</span>
    <span style="font-family:monospace;font-size:10px">ISO 45001 / Decreto 1072 de 2015</span>
  </div>
</div>`
}

/**
 * Genera un documento HTML auto-contenido con TODAS las hojas de estilo del
 * documento principal copiadas en el <head>. Se usa como fallback y para
 * renderizar en iframes donde el CSS de la app no está disponible.
 */
export function renderExportSheetHTML(cfg: ExportSheetConfig): string {
  const parentStyles = collectParentStyles()
  const body = buildExportSheetBody(cfg)

  return `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<title>${cfg.title}</title>
${parentStyles}
<style>
  *, *::before, *::after { box-sizing: border-box; }
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
    .export-sheet * { break-inside: avoid; page-break-inside: avoid; }
  }
</style>
</head>
<body style="margin:0;padding:0">
${body}
</body>
</html>`
}

// ── Función principal: IMPRESIÓN como imagen ────────────────────────
//
// Estrategia: renderiza el ExportSheet completo dentro del documento
// principal (donde Tailwind y todos los CSS de la app YA están cargados),
// captura con html2canvas a @2.5x, y envía esa imagen a un iframe limpio
// para imprimir. Esto garantiza que el mapa se ve EXACTAMENTE igual a la
// vista en pantalla: franjas, tarjetas, flechas, colores de paleta, logo.

/**
 * Imprime el mapa de procesos como imagen de alta resolución en hoja horizontal.
 */
export async function printExportSheet(cfg: ExportSheetConfig): Promise<void> {
  const { default: html2canvas } = await import('html2canvas')

  // 1. Montar el ExportSheet en el documento principal (off-screen)
  //    para que TODAS las clases Tailwind se resuelvan correctamente.
  const container = document.createElement('div')
  container.style.position = 'fixed'
  container.style.top = '-30000px'
  container.style.left = '-30000px'
  container.style.width = '1400px'
  container.style.zIndex = '-9999'
  container.style.opacity = '1' // html2canvas necesita opacidad 1
  container.style.background = '#fff'
  container.style.pointerEvents = 'none'
  container.innerHTML = buildExportSheetBody(cfg)
  document.body.appendChild(container)

  try {
    // 2. Esperar imágenes (logo) + render
    await waitForImages(container)
    await new Promise((r) => setTimeout(r, 500))

    // 3. Capturar con html2canvas a escala alta
    const target = container.querySelector('.export-sheet') as HTMLElement
    if (!target) throw new Error('No se encontró .export-sheet para capturar')

    const canvas = await html2canvas(target, {
      scale: 2.5,
      useCORS: true,
      backgroundColor: '#ffffff',
      logging: false,
      windowWidth: 1400,
      windowHeight: target.scrollHeight + 100,
    })

    const imgDataUrl = canvas.toDataURL('image/png')

    // 4. Crear iframe de impresión con solo la imagen, centrada, hoja horizontal
    const iframe = document.createElement('iframe')
    iframe.style.position = 'fixed'
    iframe.style.top = '-10000px'
    iframe.style.left = '-10000px'
    iframe.style.width = '1px'
    iframe.style.height = '1px'
    iframe.style.border = 'none'
    iframe.style.opacity = '0'
    document.body.appendChild(iframe)

    const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document
    if (!iframeDoc) throw new Error('No se pudo acceder al iframe de impresión')

    iframeDoc.open()
    iframeDoc.write(`<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<title>${cfg.title}</title>
<style>
  @page {
    size: A3 landscape;
    margin: 8mm;
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html, body {
    width: 100%; height: 100%;
    background: #fff;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    color-adjust: exact !important;
  }
  body {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
  }
  img {
    width: 100%;
    height: auto;
    max-height: 100vh;
    object-fit: contain;
    display: block;
  }
</style>
</head>
<body>
<img src="${imgDataUrl}" alt="Mapa de Procesos Organizacional"/>
</body>
</html>`)
    iframeDoc.close()

    // 5. Esperar carga de la imagen en el iframe
    await waitForImages(iframeDoc)
    await new Promise((r) => setTimeout(r, 300))

    // 6. Imprimir
    iframe.contentWindow?.focus()
    iframe.contentWindow?.print()

    // Limpiar iframe después de que el usuario cierre el diálogo
    setTimeout(() => {
      try { document.body.removeChild(iframe) } catch (_) {}
    }, 3000)
  } catch (err) {
    console.error('Error al imprimir el mapa:', err)
    alert('Hubo un error al preparar la impresión del mapa.')
  } finally {
    try { document.body.removeChild(container) } catch (_) {}
  }
}

// ── Exportar PNG ────────────────────────────────────────────────────
//
// Misma estrategia: renderiza en el documento principal donde Tailwind
// está cargado, captura con html2canvas, y descarga como PNG.

/**
 * Exporta el ExportSheet como PNG de alta resolución (@2.5x).
 */
export async function exportSheetToPNG(
  cfg: ExportSheetConfig,
  filename?: string
): Promise<void> {
  const { default: html2canvas } = await import('html2canvas')

  // Montar en el documento principal para que Tailwind aplique
  const container = document.createElement('div')
  container.style.position = 'fixed'
  container.style.top = '-30000px'
  container.style.left = '-30000px'
  container.style.width = '1400px'
  container.style.zIndex = '-9999'
  container.style.opacity = '1'
  container.style.background = '#fff'
  container.style.pointerEvents = 'none'
  container.innerHTML = buildExportSheetBody(cfg)
  document.body.appendChild(container)

  try {
    await waitForImages(container)
    await new Promise((r) => setTimeout(r, 500))

    const target = container.querySelector('.export-sheet') as HTMLElement
    if (!target) throw new Error('No se encontró .export-sheet para capturar')

    const canvas = await html2canvas(target, {
      scale: 2.5,
      useCORS: true,
      backgroundColor: '#ffffff',
      logging: false,
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
