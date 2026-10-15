/**
 * Utilidades de Colorimetría y Cálculo de Contraste WCAG 2.1
 * FOSST V.I.D.A. — Fase 1: Identidad Visual
 */

export interface RGB {
  r: number
  g: number
  b: number
}

export interface HSL {
  h: number
  s: number
  l: number
}

export interface ColorScaleItem {
  hex: string
  rgb: string // "R G B"
}

export type ColorScale = Record<50 | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900, ColorScaleItem>

/** Convierte una cadena Hex (#RGB o #RRGGBB) a un objeto RGB */
export function hexToRgb(hex: string): RGB {
  let clean = hex.trim().replace(/^#/, '')
  if (clean.length === 3) {
    clean = clean.split('').map((c) => c + c).join('')
  }
  if (clean.length !== 6) {
    return { r: 0, g: 45, b: 98 } // Default #002D62
  }
  const num = parseInt(clean, 16)
  return {
    r: (num >> 16) & 255,
    g: (num >> 8) & 255,
    b: num & 255,
  }
}

/** Convierte RGB a Hex (#RRGGBB) */
export function rgbToHex(r: number, g: number, b: number): string {
  const toHex = (c: number) => {
    const clamped = Math.max(0, Math.min(255, Math.round(c)))
    return clamped.toString(16).padStart(2, '0')
  }
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`.toUpperCase()
}

/** Convierte Hex a HSL */
export function hexToHsl(hex: string): HSL {
  const { r, g, b } = hexToRgb(hex)
  const rNorm = r / 255
  const gNorm = g / 255
  const bNorm = b / 255

  const max = Math.max(rNorm, gNorm, bNorm)
  const min = Math.min(rNorm, gNorm, bNorm)
  let h = 0
  let s = 0
  const l = (max + min) / 2

  if (max !== min) {
    const d = max - min
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min)
    switch (max) {
      case rNorm:
        h = (gNorm - bNorm) / d + (gNorm < bNorm ? 6 : 0)
        break
      case gNorm:
        h = (bNorm - rNorm) / d + 2
        break
      case bNorm:
        h = (rNorm - gNorm) / d + 4
        break
    }
    h /= 6
  }

  return {
    h: Math.round(h * 360),
    s: Math.round(s * 100),
    l: Math.round(l * 100),
  }
}

/** Convierte HSL a RGB */
export function hslToRgb(h: number, s: number, l: number): RGB {
  const hNorm = (h % 360) / 360
  const sNorm = Math.max(0, Math.min(100, s)) / 100
  const lNorm = Math.max(0, Math.min(100, l)) / 100

  if (sNorm === 0) {
    const val = Math.round(lNorm * 255)
    return { r: val, g: val, b: val }
  }

  const hue2rgb = (p: number, q: number, t: number) => {
    let tAdj = t
    if (tAdj < 0) tAdj += 1
    if (tAdj > 1) tAdj -= 1
    if (tAdj < 1 / 6) return p + (q - p) * 6 * tAdj
    if (tAdj < 1 / 2) return q
    if (tAdj < 2 / 3) return p + (q - p) * (2 / 3 - tAdj) * 6
    return p
  }

  const q = lNorm < 0.5 ? lNorm * (1 + sNorm) : lNorm + sNorm - lNorm * sNorm
  const p = 2 * lNorm - q

  const r = hue2rgb(p, q, hNorm + 1 / 3)
  const g = hue2rgb(p, q, hNorm)
  const b = hue2rgb(p, q, hNorm - 1 / 3)

  return {
    r: Math.round(r * 255),
    g: Math.round(g * 255),
    b: Math.round(b * 255),
  }
}

/**
 * Genera una escala armónica de sombras de 50 a 900 a partir de un Hex base.
 * Mantiene la luminosidad calibrada para mantener la cohesión del diseño Tailwind.
 */
export function generatePaletteScale(baseHex: string): ColorScale {
  const { h, s, l: baseL } = hexToHsl(baseHex)

  // Calibración de luminosidad según escala Tailwind
  const targetLightness: Record<50 | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900, number> = {
    50: 96,
    100: 91,
    200: 82,
    300: 71,
    400: 60,
    500: baseL, // Mantiene el tono exacto seleccionado
    600: Math.max(10, baseL * 0.8),
    700: Math.max(8, baseL * 0.65),
    800: Math.max(6, baseL * 0.45),
    900: Math.max(4, baseL * 0.3),
  }

  const keys: (50 | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900)[] = [
    50, 100, 200, 300, 400, 500, 600, 700, 800, 900,
  ]

  const result = {} as ColorScale

  keys.forEach((key) => {
    let targetL = targetLightness[key]
    if (key === 500) {
      targetL = baseL
    } else if (key < 500) {
      // Interpolar entre 96 y baseL
      const factor = (500 - key) / 450
      targetL = baseL + (96 - baseL) * factor
    }

    // Ajuste leve de saturación para los tonos muy claros o oscuros
    let satAdj = s
    if (key <= 100) satAdj = Math.min(100, s * 0.85)
    if (key >= 800) satAdj = Math.min(100, s * 0.9)

    const rgbObj = hslToRgb(h, satAdj, targetL)
    const hexVal = rgbToHex(rgbObj.r, rgbObj.g, rgbObj.b)

    result[key] = {
      hex: hexVal,
      rgb: `${rgbObj.r} ${rgbObj.g} ${rgbObj.b}`,
    }
  })

  // Asegurar que 500 tenga el valor hex exacto ingresado
  const baseRgb = hexToRgb(baseHex)
  result[500] = {
    hex: baseHex.toUpperCase(),
    rgb: `${baseRgb.r} ${baseRgb.g} ${baseRgb.b}`,
  }

  return result
}

/**
 * Calcula la luminancia relativa según especificación WCAG 2.1
 */
export function getLuminance(hex: string): number {
  const { r, g, b } = hexToRgb(hex)
  const a = [r, g, b].map((v) => {
    const val = v / 255
    return val <= 0.04045 ? val / 12.92 : Math.pow((val + 0.055) / 1.055, 2.4)
  })
  return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722
}

/**
 * Calcula la relación de contraste WCAG entre dos colores Hex (ej: 4.5 para AA)
 */
export function getContrastRatio(hex1: string, hex2: string): number {
  const lum1 = getLuminance(hex1)
  const lum2 = getLuminance(hex2)
  const brightest = Math.max(lum1, lum2)
  const darkest = Math.min(lum1, lum2)
  return (brightest + 0.05) / (darkest + 0.05)
}

/**
 * Devuelve el color de texto con mejor contraste sobre un fondo (#FFFFFF o #0F172A)
 * Garantiza una relación mínima de 4.5:1 (WCAG AA).
 */
export function contrastText(bgHex: string): string {
  const whiteRatio = getContrastRatio('#FFFFFF', bgHex)
  if (whiteRatio >= 4.5) {
    return '#FFFFFF'
  }
  const darkRatio = getContrastRatio('#0F172A', bgHex)
  if (darkRatio >= whiteRatio) {
    return '#0F172A'
  }
  return '#FFFFFF'
}

/**
 * Asegura que el color de texto tenga un contraste suficiente sobre el fondo.
 * Si no cumple con minRatio (default 4.5), retorna un texto seguro (blanco u oscuro).
 */
export function ensureContrast(fgHex: string, bgHex: string, minRatio = 4.5): string {
  const ratio = getContrastRatio(fgHex, bgHex)
  if (ratio >= minRatio) {
    return fgHex
  }
  return contrastText(bgHex)
}

// ── Colorimetría CIE L*a*b* y Distancia Perceptual ΔE ───────────────

export interface LabColor {
  L: number
  a: number
  b: number
}

/** Convierte RGB (0-255) a CIE L*a*b* con iluminante D65 */
export function rgbToLab(r: number, g: number, b: number): LabColor {
  // 1. Linealización sRGB
  const rL = r / 255 > 0.04045 ? Math.pow((r / 255 + 0.055) / 1.055, 2.4) : (r / 255) / 12.92
  const gL = g / 255 > 0.04045 ? Math.pow((g / 255 + 0.055) / 1.055, 2.4) : (g / 255) / 12.92
  const bL = b / 255 > 0.04045 ? Math.pow((b / 255 + 0.055) / 1.055, 2.4) : (b / 255) / 12.92

  // 2. Transformación a CIE XYZ (D65)
  const x = (rL * 0.4124 + gL * 0.3576 + bL * 0.1805) / 0.95047
  const y = (rL * 0.2126 + gL * 0.7152 + bL * 0.0722) / 1.00000
  const z = (rL * 0.0193 + gL * 0.1192 + bL * 0.9505) / 1.08883

  // 3. Conversión XYZ a Lab
  const f = (t: number) => (t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116)
  const fX = f(x)
  const fY = f(y)
  const fZ = f(z)

  return {
    L: 116 * fY - 16,
    a: 500 * (fX - fY),
    b: 200 * (fY - fZ),
  }
}

/** Convierte Hex (#RRGGBB) a Lab */
export function hexToLab(hex: string): LabColor {
  const { r, g, b } = hexToRgb(hex)
  return rgbToLab(r, g, b)
}

/** Calcula la distancia perceptual Delta E (CIE76) entre dos colores Lab */
export function deltaE(c1: LabColor, c2: LabColor): number {
  const dL = c1.L - c2.L
  const da = c1.a - c2.a
  const db = c1.b - c2.b
  return Math.sqrt(dL * dL + da * da + db * db)
}

/**
 * Parsea una lista de colores HEX pegados como texto (separados por comas, espacios o saltos de línea).
 */
export function parseHexList(input: string): string[] {
  if (!input || !input.trim()) return []
  const matches = input.match(/#?([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b/g) || []
  const seen = new Set<string>()
  const result: string[] = []

  for (const m of matches) {
    let clean = m.replace(/^#/, '').toUpperCase()
    if (clean.length === 3) {
      clean = clean.split('').map((c) => c + c).join('')
    }
    const hex = `#${clean}`
    if (!seen.has(hex)) {
      seen.add(hex)
      result.push(hex)
    }
  }

  return result
}

/**
 * Extrae de 5 a 8 colores dominantes en el navegador a partir de una imagen o canvas.
 * - Reduce imagen a máx 150 px.
 * - Ignora transparentes, casi blancos (L > 93) y casi negros (L < 12).
 * - Agrupa por cuantización y fusiona en espacio Lab si ΔE < 16.
 */
export function extractDominantColors(
  source: HTMLImageElement | HTMLCanvasElement,
  maxResults = 8
): string[] {
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d', { willReadFrequently: true })
  if (!ctx) return []

  const maxDim = 150
  const srcW = 'naturalWidth' in source ? (source.naturalWidth || source.width) : source.width
  const srcH = 'naturalHeight' in source ? (source.naturalHeight || source.height) : source.height

  if (!srcW || !srcH) return []

  const scale = Math.min(1, maxDim / Math.max(srcW, srcH))
  canvas.width = Math.max(1, Math.round(srcW * scale))
  canvas.height = Math.max(1, Math.round(srcH * scale))

  ctx.drawImage(source, 0, 0, canvas.width, canvas.height)
  const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height).data

  interface Bucket {
    r: number
    g: number
    b: number
    hex: string
    lab: LabColor
    count: number
  }

  const rawBuckets = new Map<string, { r: number; g: number; b: number; count: number }>()

  for (let i = 0; i < imgData.length; i += 4) {
    const a = imgData[i + 3]
    if (a < 128) continue // Ignorar transparentes

    const r = imgData[i]
    const g = imgData[i + 1]
    const b = imgData[i + 2]

    // Ignorar casi blancos y casi negros
    if (r > 240 && g > 240 && b > 240) continue
    if (r < 18 && g < 18 && b < 18) continue

    // Cuantización a bloques de 16
    const qr = Math.round(r / 16) * 16
    const qg = Math.round(g / 16) * 16
    const qb = Math.round(b / 16) * 16
    const key = `${qr}_${qg}_${qb}`

    const existing = rawBuckets.get(key)
    if (existing) {
      existing.count += 1
      existing.r += r
      existing.g += g
      existing.b += b
    } else {
      rawBuckets.set(key, { r, g, b, count: 1 })
    }
  }

  // Convertir a lista de buckets ordenados por frecuencia
  const initialList: Bucket[] = Array.from(rawBuckets.values())
    .map((b) => {
      const avgR = Math.round(b.r / b.count)
      const avgG = Math.round(b.g / b.count)
      const avgB = Math.round(b.b / b.count)
      const hex = rgbToHex(avgR, avgG, avgB)
      return {
        r: avgR,
        g: avgG,
        b: avgB,
        hex,
        lab: rgbToLab(avgR, avgG, avgB),
        count: b.count,
      }
    })
    .sort((a, b) => b.count - a.count)

  // Fusionar colores perceptualmente parecidos (ΔE < 16 en Lab)
  const merged: Bucket[] = []
  const MERGE_THRESHOLD = 16

  for (const item of initialList) {
    let matched = false
    for (const m of merged) {
      if (deltaE(item.lab, m.lab) < MERGE_THRESHOLD) {
        m.count += item.count
        matched = true
        break
      }
    }
    if (!matched) {
      merged.push({ ...item })
    }
  }

  // Filtrar colores resultantes con brillo demasiado extremo
  const filtered = merged
    .filter((b) => b.lab.L >= 12 && b.lab.L <= 94)
    .sort((a, b) => b.count - a.count)

  const count = Math.min(Math.max(5, maxResults), filtered.length)
  return filtered.slice(0, count).map((b) => b.hex)
}

/**
 * Asigna automáticamente Primario, Secundario y Acento a partir de una lista de muestras:
 * - Primario: color más oscuro y estructurado con buena saturación (L < 50).
 * - Secundario: segundo tono distinto con buen contraste cromático o balance.
 * - Acento: el más cálido (rango amarillo/ámbar/naranja 25-65°) o más vívido/luminoso.
 */
export function autoAssignBrandPalette(swatches: string[]): {
  primario: string
  secundario: string
  acento: string
} {
  if (!swatches || swatches.length === 0) {
    return { primario: '#002D62', secundario: '#0284C7', acento: '#F5A800' }
  }

  if (swatches.length === 1) {
    const p = swatches[0]
    const { h, s, l } = hexToHsl(p)
    const secRgb = hslToRgb((h + 30) % 360, Math.min(100, s + 10), Math.min(80, l + 15))
    const aceRgb = hslToRgb((h + 180) % 360, 85, 55)
    return {
      primario: p,
      secundario: rgbToHex(secRgb.r, secRgb.g, secRgb.b),
      acento: rgbToHex(aceRgb.r, aceRgb.g, aceRgb.b),
    }
  }

  // Analizar cada color
  const items = swatches.map((hex) => {
    const hsl = hexToHsl(hex)
    const lab = hexToLab(hex)
    return { hex, hsl, lab }
  })

  // 1. Primario: Busca el tono con mayor peso corporativo (oscuro, saturado)
  const scoredForPrimary = [...items].sort((a, b) => {
    // Premiar menor L (pero no negro, ej L entre 20 y 48) y buena saturación
    const scoreA = (a.hsl.s * 0.8) + (55 - Math.abs(a.hsl.l - 30)) * 1.5
    const scoreB = (b.hsl.s * 0.8) + (55 - Math.abs(b.hsl.l - 30)) * 1.5
    return scoreB - scoreA
  })
  const primarioItem = scoredForPrimary[0] || items[0]
  const primario = primarioItem.hex

  // 2. Acento: El más cálido (H entre 20 y 65) o más vibrante/luminoso
  const candidatesForAccent = items.filter((it) => it.hex !== primario)
  const scoredForAccent = [...candidatesForAccent].sort((a, b) => {
    const isWarmA = a.hsl.h >= 20 && a.hsl.h <= 65 ? 40 : 0
    const isWarmB = b.hsl.h >= 20 && b.hsl.h <= 65 ? 40 : 0
    const scoreA = isWarmA + a.hsl.s * 0.7 + a.hsl.l * 0.5
    const scoreB = isWarmB + b.hsl.s * 0.7 + b.hsl.l * 0.5
    return scoreB - scoreA
  })
  const acentoItem = scoredForAccent[0] || candidatesForAccent[0] || primarioItem
  const acento = acentoItem.hex

  // 3. Secundario: Un tono distinto a primario y acento con buena separación
  const candidatesForSecondary = items.filter(
    (it) => it.hex !== primario && it.hex !== acento
  )

  let secundario = ''
  if (candidatesForSecondary.length > 0) {
    // Buscar el que tenga mayor distancia perceptual con el primario
    const scoredSec = [...candidatesForSecondary].sort((a, b) => {
      const dA = deltaE(a.lab, primarioItem.lab)
      const dB = deltaE(b.lab, primarioItem.lab)
      return dB - dA
    })
    secundario = scoredSec[0].hex
  } else {
    // Derivar uno armónico si no hay más
    const secRgb = hslToRgb((primarioItem.hsl.h + 35) % 360, primarioItem.hsl.s, Math.min(75, primarioItem.hsl.l + 20))
    secundario = rgbToHex(secRgb.r, secRgb.g, secRgb.b)
  }

  return { primario, secundario, acento }
}
