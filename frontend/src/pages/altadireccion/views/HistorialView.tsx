import { Card, PageHeader, Badge, EmptyState } from '@/components/ui'
import { LoadingSpinner, ErrorDisplay } from '@/components/ui/forms'
import { useDashboardAD } from '@/hooks/useApi'
import { History } from 'lucide-react'

export default function HistorialView() {
  const { data, isLoading, error, refetch } = useDashboardAD()

  if (isLoading) return <LoadingSpinner text="Cargando historial..." />
  if (error || !data) return <ErrorDisplay message={(error as Error)?.message ?? 'Error'} onRetry={refetch} />

  const { historial } = data

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader title="Historial Anual" subtitle="Evolución del cumplimiento SG-SST por vigencia" />

      {historial.length === 0 ? (
        <EmptyState
          icon={History}
          title="Sin historial"
          description="El historial se generará con la primera evaluación completada"
        />
      ) : (
        <div className="space-y-4">
          {historial.map((ev, i) => {
            const pct = Number(ev.puntaje_total ?? 0)
            const nivel = pct >= 86 ? 'Aceptable' : pct >= 61 ? 'Moderado' : 'Crítico'
            const variant = pct >= 86 ? 'green' as const : pct >= 61 ? 'orange' as const : 'red' as const
            const barColorMap = { green: 'bg-green-500', orange: 'bg-amber-500', red: 'bg-red-500' }
            const textColorMap = { green: 'text-green-700', orange: 'text-amber-700', red: 'text-red-700' }
            return (
              <Card key={ev.anio}>
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 rounded-2xl bg-surface flex items-center justify-center flex-shrink-0">
                    <span className="text-xl font-black text-primary-500">{ev.anio}</span>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-bold text-primary-500">Vigencia {ev.anio}</span>
                      <Badge variant={variant}>{nivel}</Badge>
                      <Badge variant={ev.estado === 'completada' ? 'green' : 'gray'}>{ev.estado}</Badge>
                    </div>
                    <div className="h-2 bg-surface-2 rounded-full overflow-hidden mt-2">
                      <div className={`h-full rounded-full ${barColorMap[variant]}`} style={{ width: `${pct}%`, transition: 'width 0.8s ease' }} />
                    </div>
                    <div className="text-xs text-slate-500 mt-1">Puntaje: {pct}%</div>
                  </div>
                  <div className={`text-3xl font-black ${textColorMap[variant]}`}>{pct}%</div>
                </div>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
