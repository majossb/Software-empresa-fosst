import { Card, PageHeader, Badge, Button, EmptyState } from '@/components/ui'
import { LoadingSpinner, ErrorDisplay } from '@/components/ui/forms'
import { useEvidencias } from '@/hooks/useApi'
import { Eye, FileText } from 'lucide-react'

export default function EvidenciasAuditorView() {
  const { data, isLoading, error, refetch } = useEvidencias()

  if (isLoading) return <LoadingSpinner text="Cargando evidencias..." />
  if (error || !data) return <ErrorDisplay message={(error as Error)?.message ?? 'Error'} onRetry={refetch} />

  const { evidencias, total } = data

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader title="Revisión de Evidencias" subtitle={`${total} evidencias documentales cargadas por el responsable`} />

      <div className="flex items-start gap-3 bg-slate-50 border border-slate-200 rounded-xl p-4">
        <Eye className="w-5 h-5 text-primary-500 flex-shrink-0" />
        <div className="text-xs text-slate-600">
          Vista de <strong className="text-primary-500">solo lectura</strong>. Las evidencias son cargadas por el Responsable SG-SST.
        </div>
      </div>

      {evidencias.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="Sin evidencias"
          description="El responsable no ha cargado evidencias aún"
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {evidencias.map(ev => (
            <Card key={ev.id}>
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <FileText className="w-5 h-5 text-blue-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-bold text-primary-500 truncate">{ev.archivo?.nombre ?? 'Sin nombre'}</div>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="blue">{ev.estandar_codigo}</Badge>
                    <span className="text-xs text-slate-500 truncate">{ev.estandar_nombre}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant={ev.estado_estandar === 'cumple' ? 'green' : ev.estado_estandar === 'parcial' ? 'orange' : 'red'}>
                      {ev.estado_estandar}
                    </Badge>
                    {ev.archivo?.url && (
                      <a href={ev.archivo.url} target="_blank" rel="noopener" className="text-brand-700 text-[10px] hover:underline">Ver archivo</a>
                    )}
                  </div>
                  {ev.descripcion && <div className="text-xs text-slate-500 mt-1">{ev.descripcion}</div>}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
