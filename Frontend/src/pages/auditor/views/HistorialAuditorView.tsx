import { Card, PageHeader, Badge, EmptyState } from '@/components/ui'
import { LoadingSpinner, ErrorDisplay } from '@/components/ui/forms'
import { useHistorialEvaluaciones } from '@/hooks/useApi'
import { History, Calendar, FileText, AlertTriangle } from 'lucide-react'

export default function HistorialAuditorView() {
  const { data: historial, isLoading, error, refetch } = useHistorialEvaluaciones()

  if (isLoading) return <LoadingSpinner text="Cargando historial de autoevaluaciones..." />
  if (error) return <ErrorDisplay message={(error as Error)?.message ?? 'Error al cargar historial'} onRetry={refetch} />

  const lista = Array.isArray(historial) ? historial : []

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        title="Historial de Evaluaciones"
        subtitle="Registro histórico de evaluaciones y autoevaluaciones SST de la empresa"
      />

      {lista.length === 0 ? (
        <EmptyState
          icon={History}
          title="Sin historial de evaluaciones"
          description="Aún no se han registrado evaluaciones en el sistema para esta empresa."
        />
      ) : (
        <div className="space-y-4">
          {lista.map((ev) => {
            const pct = ev.puntaje_total !== null && ev.puntaje_total !== undefined ? Number(ev.puntaje_total) : 0
            const nivel = pct >= 86 ? 'Aceptable' : pct >= 61 ? 'Moderado' : 'Crítico'
            const variant = pct >= 86 ? 'green' as const : pct >= 61 ? 'orange' as const : 'red' as const
            const barColorMap = { green: 'bg-green-500', orange: 'bg-amber-500', red: 'bg-red-500' }
            const textColorMap = { green: 'text-green-700', orange: 'text-amber-700', red: 'text-red-700' }

            return (
              <Card key={ev.id || ev.anio}>
                <div className="flex flex-col md:flex-row md:items-center gap-4">
                  <div className="w-16 h-16 rounded-2xl bg-surface flex items-center justify-center flex-shrink-0">
                    <span className="text-xl font-black text-primary-500">{ev.anio}</span>
                  </div>
                  <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <span className="text-base font-bold text-primary-500">
                        Vigencia {ev.anio} {ev.capitulo ? `- ${ev.capitulo}` : ''}
                      </span>
                      <Badge variant={variant}>{nivel}</Badge>
                      <Badge variant={ev.estado === 'completada' ? 'green' : 'gray'}>
                        {ev.estado === 'completada' ? 'Completada' : 'En Proceso'}
                      </Badge>
                    </div>

                    <div className="flex flex-wrap gap-4 text-xs text-slate-500 my-2">
                      <span className="flex items-center gap-1">
                        <FileText className="w-3.5 h-3.5 text-slate-400" />
                        {ev.respuestas_count ?? 0} respuestas registradas
                      </span>
                      <span className="flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                        {ev.hallazgos_count ?? 0} hallazgos
                      </span>
                      {ev.fecha_completado && (
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3.5 h-3.5 text-slate-400" />
                          Completado: {new Date(ev.fecha_completado).toLocaleDateString()}
                        </span>
                      )}
                    </div>

                    <div className="h-2 bg-surface-2 rounded-full overflow-hidden mt-1">
                      <div
                        className={`h-full rounded-full ${barColorMap[variant]}`}
                        style={{ width: `${pct}%`, transition: 'width 0.8s ease' }}
                      />
                    </div>
                  </div>
                  <div className={`text-3xl font-black ${textColorMap[variant]} text-right`}>
                    {pct.toFixed(1)}%
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
