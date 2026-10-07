import { Card, PageHeader, Badge, Table, TableHeader, TableBody, TableRow, TableHead, TableCell, EmptyState } from '@/components/ui'
import { LoadingSpinner, ErrorDisplay } from '@/components/ui/forms'
import { useEstandaresConRespuestas } from '@/hooks/useApi'

export default function AutoevaluacionView() {
  const { data, isLoading, error, refetch } = useEstandaresConRespuestas()

  if (isLoading) return <LoadingSpinner text="Cargando autoevaluación..." />
  if (error || !data) return <ErrorDisplay message={(error as Error)?.message ?? 'Error'} onRetry={refetch} />

  const { estandares, capitulo } = data
  const total = estandares.length
  const cumple = estandares.filter(e => e.estado === 'cumple').length
  const parcial = estandares.filter(e => e.estado === 'parcial').length
  const noCumple = estandares.filter(e => e.estado === 'no_cumple').length
  const puntajeMax = estandares.reduce((s, e) => s + e.puntaje_maximo, 0)
  const puntajeObt = estandares.reduce((s, e) => s + e.puntaje, 0)
  const porcentaje = puntajeMax > 0 ? Math.round((puntajeObt / puntajeMax) * 100) : 0
  const clasif = porcentaje >= 86 ? 'ACEPTABLE' : porcentaje >= 61 ? 'MODERADAMENTE ACEPTABLE' : 'CRÍTICO'

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader title="Autoevaluación Anual" subtitle={`Capítulo ${capitulo} · Res. 0312/2019 · ${new Date().getFullYear()}`} />

      <div className={`text-center p-8 rounded-2xl border ${porcentaje >= 86 ? 'bg-green-50 border-green-200' : porcentaje >= 61 ? 'bg-brand-50 border-brand-200' : 'bg-red-50 border-red-200'}`}>
        <div className="text-6xl font-black mb-2" style={{ color: porcentaje >= 86 ? '#15803d' : porcentaje >= 61 ? '#c28500' : '#dc2626' }}>
          {porcentaje}%
        </div>
        <div className="text-lg font-bold" style={{ color: porcentaje >= 86 ? '#15803d' : porcentaje >= 61 ? '#c28500' : '#dc2626' }}>{clasif}</div>
        <div className="text-xs text-slate-500 mt-2">{puntajeObt.toFixed(1)} / {puntajeMax.toFixed(1)} puntos</div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total estándares', val: total, color: 'text-primary-500' },
          { label: 'Cumplen', val: cumple, color: 'text-green-700' },
          { label: 'Parciales', val: parcial, color: 'text-brand-700' },
          { label: 'No cumplen', val: noCumple, color: 'text-red-700' },
        ].map(k => (
          <Card key={k.label}>
            <div className="text-center">
              <div className={`text-2xl font-black ${k.color}`}>{k.val}</div>
              <div className="text-xs text-slate-500 mt-1">{k.label}</div>
            </div>
          </Card>
        ))}
      </div>

      <Card title="Detalle por Estándar">
        {estandares.length === 0 ? (
          <EmptyState title="Sin estándares" description="No hay estándares disponibles para mostrar." />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Código</TableHead>
                <TableHead>Estándar</TableHead>
                <TableHead className="text-center">Ciclo</TableHead>
                <TableHead className="text-center">Pts Máx</TableHead>
                <TableHead className="text-center">Pts Obt</TableHead>
                <TableHead className="text-center">Estado</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {estandares.map(e => (
                <TableRow key={e.estandar_id}>
                  <TableCell className="font-bold text-slate-500">{e.codigo}</TableCell>
                  <TableCell className="truncate max-w-xs">{e.nombre}</TableCell>
                  <TableCell className="text-center"><Badge variant="blue">{e.ciclo_phva?.[0]}</Badge></TableCell>
                  <TableCell className="text-center text-slate-500">{e.puntaje_maximo}</TableCell>
                  <TableCell className="text-center text-primary-500 font-bold">{e.puntaje}</TableCell>
                  <TableCell className="text-center">
                    <Badge variant={e.estado === 'cumple' ? 'green' : e.estado === 'parcial' ? 'orange' : e.estado === 'no_cumple' ? 'red' : 'gray'}>
                      {e.estado === 'cumple' ? 'Cumple' : e.estado === 'parcial' ? 'Parcial' : e.estado === 'no_cumple' ? 'No cumple' : 'N/A'}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  )
}
