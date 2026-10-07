import { Card, PageHeader, Badge, Button } from '@/components/ui'
import { LoadingSpinner, ErrorDisplay } from '@/components/ui/forms'
import { useDashboardAD } from '@/hooks/useApi'

export default function CumplimientoView() {
  const { data, isLoading, error, refetch } = useDashboardAD()

  if (isLoading) return <LoadingSpinner text="Cargando cumplimiento..." />
  if (error || !data) return <ErrorDisplay message={(error as Error)?.message ?? 'Error'} onRetry={refetch} />

  const { cumplimiento, phva, empresa } = data

  const nivel = cumplimiento.global >= 86 ? 'ACEPTABLE' : cumplimiento.global >= 61 ? 'MODERADAMENTE ACEPTABLE' : 'CRÍTICO'
  const nivelColor = cumplimiento.global >= 86 ? 'text-green-700' : cumplimiento.global >= 61 ? 'text-brand-700' : 'text-red-700'

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader title="Cumplimiento SG-SST" subtitle={`Desglose completo · ${empresa?.nombre} · Capítulo ${empresa?.capitulo_vigente}`} />

      {/* Clasificación */}
      <div className={`text-center p-6 rounded-2xl border ${
        cumplimiento.global >= 86 ? 'bg-green-50 border-green-200' :
        cumplimiento.global >= 61 ? 'bg-brand-50 border-brand-200' :
        'bg-red-50 border-red-200'
      }`}>
        <div className="text-5xl font-black mb-2" style={{ color: cumplimiento.global >= 86 ? '#15803d' : cumplimiento.global >= 61 ? '#c28500' : '#dc2626' }}>
          {cumplimiento.global}%
        </div>
        <div className={`text-sm font-bold ${nivelColor}`}>{nivel}</div>
        <div className="text-xs text-slate-500 mt-1">
          {cumplimiento.puntaje_obtenido} / {cumplimiento.puntaje_maximo} puntos · Res. 0312/2019
        </div>
      </div>

      {/* PHVA detallado */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {Object.entries(phva).map(([ciclo, d]) => {
          const colorMap: Record<string, { border: string; text: string; bar: string }> = {
            Planear:   { border: 'border-blue-200',   text: 'text-blue-700',   bar: 'bg-blue-500'   },
            Hacer:     { border: 'border-amber-200',  text: 'text-amber-700',  bar: 'bg-amber-500'  },
            Verificar: { border: 'border-blue-200',   text: 'text-blue-700',   bar: 'bg-blue-500'   },
            Actuar:    { border: 'border-green-200',  text: 'text-green-700',  bar: 'bg-green-500'  },
          }
          const c = colorMap[ciclo] ?? colorMap.Planear
          return (
            <Card key={ciclo} className={c.border}>
              <div className="text-center">
                <div className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">{ciclo}</div>
                <div className={`text-2xl font-black ${c.text} mb-1`}>{d.porcentaje}%</div>
                <div className="text-xs text-slate-500">{d.obtenido} / {d.maximo} pts</div>
                <div className="mt-3 h-2 bg-surface-2 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${c.bar}`} style={{ width: `${d.porcentaje}%`, transition: 'width 0.8s ease' }} />
                </div>
              </div>
            </Card>
          )
        })}
      </div>

      {/* Resumen numérico */}
      <Card title="Resumen por Estado">
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: 'Cumple', count: cumplimiento.cumplidos, color: 'green' as const, textClass: 'text-green-700' },
            { label: 'Parcial', count: cumplimiento.parciales, color: 'orange' as const, textClass: 'text-amber-700' },
            { label: 'No Cumple', count: cumplimiento.no_cumple, color: 'red' as const, textClass: 'text-red-700' },
          ].map((item) => (
            <div key={item.label} className="text-center p-4 bg-surface rounded-xl">
              <div className={`text-2xl font-black ${item.textClass}`}>{item.count}</div>
              <div className="text-xs text-slate-500 mt-1">{item.label}</div>
              <Badge variant={item.color} >{Math.round((item.count / cumplimiento.total_estandares) * 100)}%</Badge>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
