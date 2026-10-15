import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { modulo0Service } from '@/services/modulo0.service'
import { X, CheckCircle2, Circle, Sparkles } from 'lucide-react'

export default function CompletitudBanner() {
  const [dismissed, setDismissed] = useState(
    () => sessionStorage.getItem('modulo0_banner_dismissed') === 'true'
  )

  const { data } = useQuery({
    queryKey: ['modulo0', 'completitud'],
    queryFn: modulo0Service.getCompletitud,
    staleTime: 30_000,
  })

  if (dismissed || !data || data.porcentaje >= 100) return null

  const handleDismiss = () => {
    sessionStorage.setItem('modulo0_banner_dismissed', 'true')
    setDismissed(true)
  }

  const pendientes = data.hitos.filter((h) => !h.completado)

  return (
    <div className="relative mb-6 rounded-2xl overflow-hidden border border-brand-200/50 shadow-lg">
      {/* Fondo con gradiente y glassmorphism */}
      <div className="absolute inset-0 bg-gradient-to-r from-brand-500/10 via-primary-500/5 to-brand-500/10 backdrop-blur-sm" />
      <div className="absolute inset-0 bg-white/70" />

      <div className="relative p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-primary-500 flex items-center justify-center shadow-md shadow-brand-500/20">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-primary-500">
                Configuración de la Organización
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Completa todos los datos para habilitar el diagnóstico
              </p>
            </div>
          </div>
          <button
            onClick={handleDismiss}
            className="text-slate-400 hover:text-primary-500 transition-colors p-1 rounded-lg hover:bg-surface"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Barra de progreso */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-semibold text-slate-600">Progreso general</span>
            <span className="text-xs font-black text-brand-700">{data.porcentaje}%</span>
          </div>
          <div className="h-2.5 bg-surface-2 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-brand-500 to-primary-500 transition-all duration-1000 ease-out shadow-sm"
              style={{ width: `${data.porcentaje}%` }}
            />
          </div>
        </div>

        {/* Hitos pendientes */}
        {pendientes.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {data.hitos.map((hito) => (
              <div
                key={hito.nombre}
                className={`
                  inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg
                  transition-all duration-200
                  ${hito.completado
                    ? 'bg-green-50 text-green-700 border border-green-200'
                    : 'bg-brand-50 text-brand-800 border border-brand-200 animate-pulse'
                  }
                `}
              >
                {hito.completado
                  ? <CheckCircle2 className="w-3.5 h-3.5" />
                  : <Circle className="w-3.5 h-3.5" />
                }
                {hito.nombre}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
