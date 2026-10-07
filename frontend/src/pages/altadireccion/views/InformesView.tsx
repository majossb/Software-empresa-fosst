import { useState } from 'react'
import { Card, PageHeader, Badge, Button, EmptyState } from '@/components/ui'
import { LoadingSpinner, ErrorDisplay } from '@/components/ui/forms'
import { useInformes, useGenerarInforme, useDashboardAD } from '@/hooks/useApi'
import { FileText, Download, Plus } from 'lucide-react'

export default function InformesView() {
  const { data, isLoading, error, refetch } = useInformes()
  const dashboard = useDashboardAD()
  const generarMut = useGenerarInforme()
  const [generando, setGenerando] = useState(false)

  if (isLoading) return <LoadingSpinner text="Cargando informes..." />
  if (error || !data) return <ErrorDisplay message={(error as Error)?.message ?? 'Error'} onRetry={refetch} />

  const handleGenerar = async (tipo: 'ejecutivo' | 'revision_alta_direccion') => {
    if (!dashboard.data?.evaluacion_id) return
    setGenerando(true)
    try {
      await generarMut.mutateAsync({ evaluacion_id: dashboard.data.evaluacion_id, tipo })
    } finally { setGenerando(false) }
  }

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader title="Informes Ejecutivos" subtitle="Generación y consulta de informes del SG-SST"
        actions={
          <div className="flex gap-2">
            <Button variant="ghost" className="text-xs" onClick={() => handleGenerar('ejecutivo')} disabled={generando}>
              <Plus className="w-3 h-3" /> Informe ejecutivo
            </Button>
            <Button variant="primary" className="text-xs" onClick={() => handleGenerar('revision_alta_direccion')} disabled={generando}>
              <Plus className="w-3 h-3" /> Revisión alta dirección
            </Button>
          </div>
        }
      />

      {data.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="Sin informes generados"
          description="Genere su primer informe ejecutivo usando los botones superiores"
        />
      ) : (
        <div className="space-y-3">
          {data.map((inf) => {
            const contenido = inf.contenido_json as any
            return (
              <Card key={inf.id}>
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center flex-shrink-0">
                    <FileText className="w-5 h-5 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-bold text-primary-500 capitalize">{inf.tipo.replace(/_/g, ' ')}</span>
                      <Badge variant="blue">{inf.evaluacion?.anio ?? ''}</Badge>
                      {contenido?.clasificacion && (
                        <Badge variant={contenido.clasificacion === 'ACEPTABLE' ? 'green' : contenido.clasificacion === 'CRÍTICO' ? 'red' : 'orange'}>
                          {contenido.clasificacion}
                        </Badge>
                      )}
                    </div>
                    <div className="text-xs text-slate-500">
                      Generado: {new Date(inf.fecha_elaboracion).toLocaleString('es-CO')}
                      {contenido?.resumen_ejecutivo && (
                        <span> · Cumplimiento: <strong className="text-primary-500">{contenido.resumen_ejecutivo.cumplimiento_global}%</strong></span>
                      )}
                    </div>
                    {contenido?.recomendaciones && contenido.recomendaciones.length > 0 && (
                      <div className="mt-2 p-3 bg-surface rounded-xl">
                        <div className="text-[10px] font-bold text-slate-500 uppercase mb-1">Recomendaciones</div>
                        {contenido.recomendaciones.slice(0, 3).map((rec: string, i: number) => (
                          <div key={i} className="text-xs text-slate-600 mb-0.5">• {rec}</div>
                        ))}
                      </div>
                    )}
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
