import React, { createContext, useContext, useEffect, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { modulo0Service, BrandingConfig } from '@/services/modulo0.service'
import {
  generatePaletteScale,
  contrastText,
  ensureContrast,
  getContrastRatio,
  hexToRgb,
} from '@/utils/color.utils'

export const DEFAULT_FOSST_BRANDING: BrandingConfig = {
  preset: 'azul_fosst',
  primario: '#002D62',
  secundario: '#0284C7',
  acento: '#F5A800',
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
      'Requisitos Legales y Normativos',
      'Partes Interesadas',
      'Directrices de la Dirección',
      'Diagnóstico de Condiciones de Trabajo',
    ],
    salidas_items: [
      'Ambientes de Trabajo Seguros y Saludables',
      'Control de Riesgos y Peligros',
      'Cumplimiento Legal Integral',
      'Mejora Continua del Desempeño',
    ],
  },
}

export interface ResolvedMapColors {
  estrategico: string
  misional: string
  apoyo: string
  entradas: string
  salidas: string
  fondo: string
  texto_entradas: string
  texto_salidas: string
  entradas_items: string[]
  salidas_items: string[]
  isCustom: {
    estrategico: boolean
    misional: boolean
    apoyo: boolean
    entradas: boolean
    salidas: boolean
    fondo: boolean
  }
}

/**
 * Resuelve los colores del mapa de procesos:
 * Si una clave es null o no existe, deriva dinámicamente de la paleta corporativa de la empresa.
 * Si el usuario la sobrescribió explícitamente, respeta el color personalizado.
 */
export function resolveMapColors(
  branding: BrandingConfig,
  overrides?: Partial<BrandingConfig['mapa_procesos']> | null
): ResolvedMapColors {
  const mp = overrides || branding?.mapa_procesos || {}

  const defaultEstrategico = branding?.primario || '#002D62'
  const defaultMisional = branding?.secundario || '#0284C7'
  const defaultApoyo = '#64748B'
  const defaultEntradas = branding?.acento || '#F5A800'
  const defaultSalidas = '#059669'
  const defaultFondo = '#F8FAFC'

  const hasCustom = (val: string | null | undefined, def: string) => {
    return Boolean(val && val.trim() !== '' && val.toUpperCase() !== def.toUpperCase())
  }

  return {
    estrategico: (mp.estrategico && mp.estrategico.trim()) ? mp.estrategico : defaultEstrategico,
    misional: (mp.misional && mp.misional.trim()) ? mp.misional : defaultMisional,
    apoyo: (mp.apoyo && mp.apoyo.trim()) ? mp.apoyo : defaultApoyo,
    entradas: (mp.entradas && mp.entradas.trim()) ? mp.entradas : defaultEntradas,
    salidas: (mp.salidas && mp.salidas.trim()) ? mp.salidas : defaultSalidas,
    fondo: (mp.fondo && mp.fondo.trim()) ? mp.fondo : defaultFondo,
    texto_entradas: mp.texto_entradas || 'Requisitos Legales y de Partes Interesadas (Dec. 1072 / Res. 0312 de 2019)',
    texto_salidas: mp.texto_salidas || 'Lugares de Trabajo Seguros, Saludables y Sostenibles',
    entradas_items: mp.entradas_items || [
      'Requisitos Legales y Normativos',
      'Partes Interesadas',
      'Directrices de la Dirección',
      'Diagnóstico de Condiciones de Trabajo',
    ],
    salidas_items: mp.salidas_items || [
      'Ambientes de Trabajo Seguros y Saludables',
      'Control de Riesgos y Peligros',
      'Cumplimiento Legal Integral',
      'Mejora Continua del Desempeño',
    ],
    isCustom: {
      estrategico: hasCustom(mp.estrategico, defaultEstrategico),
      misional: hasCustom(mp.misional, defaultMisional),
      apoyo: hasCustom(mp.apoyo, defaultApoyo),
      entradas: hasCustom(mp.entradas, defaultEntradas),
      salidas: hasCustom(mp.salidas, defaultSalidas),
      fondo: hasCustom(mp.fondo, defaultFondo),
    },
  }
}

interface BrandingContextType {
  branding: BrandingConfig
  isLoading: boolean
  updateBranding: (newBranding: Partial<BrandingConfig>) => Promise<void>
  isUpdating: boolean
  contrastText: (bgHex: string) => string
  ensureContrast: (fgHex: string, bgHex: string, minRatio?: number) => string
  getContrastRatio: (hex1: string, hex2: string) => number
}

const BrandingContext = createContext<BrandingContextType | undefined>(undefined)

export function BrandingProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient()
  const token = localStorage.getItem('token')

  const { data: brandingData, isLoading } = useQuery({
    queryKey: ['modulo0', 'branding'],
    queryFn: modulo0Service.getBranding,
    enabled: !!token,
    staleTime: 60_000,
  })

  const branding = useMemo(() => {
    if (!brandingData) return DEFAULT_FOSST_BRANDING
    return {
      ...DEFAULT_FOSST_BRANDING,
      ...brandingData,
      mapa_procesos: {
        ...DEFAULT_FOSST_BRANDING.mapa_procesos,
        ...(brandingData.mapa_procesos || {}),
      },
    }
  }, [brandingData])

  const mutation = useMutation({
    mutationFn: (data: Partial<BrandingConfig>) => modulo0Service.updateBranding(data),
    onSuccess: (updated) => {
      queryClient.setQueryData(['modulo0', 'branding'], updated)
      queryClient.invalidateQueries({ queryKey: ['modulo0'] })
    },
  })

  // Escribir variables CSS dinámicas en :root cada vez que cambia el branding
  useEffect(() => {
    const root = document.documentElement

    // Primary palette
    const primaryScale = generatePaletteScale(branding.primario || '#002D62')
    Object.entries(primaryScale).forEach(([shade, item]) => {
      root.style.setProperty(`--color-primary-${shade}`, item.rgb)
    })
    root.style.setProperty('--color-primary-hex', branding.primario || '#002D62')

    // Secondary / Brand palette (brand en tailwind mapea a secundario o acento)
    const brandScale = generatePaletteScale(branding.acento || '#F5A800')
    Object.entries(brandScale).forEach(([shade, item]) => {
      root.style.setProperty(`--color-brand-${shade}`, item.rgb)
    })
    root.style.setProperty('--color-brand-hex', branding.acento || '#F5A800')

    // Secondary palette explícita
    const secondaryScale = generatePaletteScale(branding.secundario || '#0284C7')
    Object.entries(secondaryScale).forEach(([shade, item]) => {
      root.style.setProperty(`--color-secondary-${shade}`, item.rgb)
    })
    root.style.setProperty('--color-secondary-hex', branding.secundario || '#0284C7')

    // Mapa de procesos variables dinámicas
    const resolvedMap = resolveMapColors(branding)
    root.style.setProperty('--mapa-estrategico-hex', resolvedMap.estrategico)
    root.style.setProperty('--mapa-misional-hex', resolvedMap.misional)
    root.style.setProperty('--mapa-apoyo-hex', resolvedMap.apoyo)
    root.style.setProperty('--mapa-entradas-hex', resolvedMap.entradas)
    root.style.setProperty('--mapa-salidas-hex', resolvedMap.salidas)
    root.style.setProperty('--mapa-fondo-hex', resolvedMap.fondo)

    // RGB channels de mapa de procesos para transparencias
    const estRgb = hexToRgb(resolvedMap.estrategico)
    const misRgb = hexToRgb(resolvedMap.misional)
    const apoRgb = hexToRgb(resolvedMap.apoyo)
    root.style.setProperty('--mapa-estrategico-rgb', `${estRgb.r} ${estRgb.g} ${estRgb.b}`)
    root.style.setProperty('--mapa-misional-rgb', `${misRgb.r} ${misRgb.g} ${misRgb.b}`)
    root.style.setProperty('--mapa-apoyo-rgb', `${apoRgb.r} ${apoRgb.g} ${apoRgb.b}`)
  }, [branding])

  const updateBranding = async (newBranding: Partial<BrandingConfig>) => {
    await mutation.mutateAsync(newBranding)
  }

  return (
    <BrandingContext.Provider
      value={{
        branding,
        isLoading,
        updateBranding,
        isUpdating: mutation.isPending,
        contrastText,
        ensureContrast,
        getContrastRatio,
      }}
    >
      {children}
    </BrandingContext.Provider>
  )
}

export function useBranding() {
  const context = useContext(BrandingContext)
  if (!context) {
    throw new Error('useBranding debe usarse dentro de un BrandingProvider')
  }
  return context
}
