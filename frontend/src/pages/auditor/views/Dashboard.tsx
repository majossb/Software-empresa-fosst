import { KpiCard, Card, PageHeader, Badge, Button, Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui'
import { LoadingSpinner, ErrorDisplay } from '@/components/ui/forms'
import { Eye, Plus, Download } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useDashboardAud } from '@/hooks/useApi'

const CICLO_COLOR: Record<string, string> = {
  Planear:   'bg-blue-100 text-blue-700',
  Hacer:     'bg-brand-50 text-brand-800',
  Verificar: 'bg-primary-50 text-primary-500',
  Actuar:    'bg-green-100 text-green-700',
}

type BadgeVariant = 'green' | 'red' | 'orange' | 'gray' | 'blue'
const VERIF_BADGE: Record<string, { label: string; variant: BadgeVariant }> = {
  cumple:        { label: 'Cumple',       variant: 'green' },
  no_cumple:     { label: 'No cumple',    variant: 'red' },
  parcial:       { label: 'Parcial',      variant: 'orange' },
  sin_respuesta: { label: 'Pendiente',    variant: 'gray' },
  no_aplica:     { label: 'N/A',          variant: 'gray' },
}

export default function AuditorDashboard() {
  const navigate = useNavigate()
  const { data, isLoading, error, refetch } = useDashboardAud()

  if (isLoading) return <LoadingSpinner text="Cargando panel de auditoría..." />
  if (error || !data) return <ErrorDisplay message={(error as Error)?.message ?? 'Error cargando datos'} onRetry={refetch} />

  const { kpis, tabla_verificacion, empresa } = data

  const KPI_DATA = [
    { label: 'Cumplimiento general',  valor: `${kpis.cumplimiento_general}%`, desc: kpis.cumplimiento_general >= 86 ? '→ Aceptable' : kpis.cumplimiento_general >= 61 ? '→ Moderado' : '→ Crítico', trend: 'neutral' as const, color: 'blue' as const },
    { label: 'Evidencias revisadas',  valor: kpis.evidencias_revisadas, desc: '→ Docs cargados por resp.', trend: 'neutral' as const, color: 'blue' as const },
    { label: 'No conformidades',      valor: kpis.hallazgos.no_conformidad, desc: `De ${kpis.hallazgos.total} hallazgos`, trend: 'down' as const, color: 'red' as const },
    { label: 'Oportunidades',         valor: kpis.hallazgos.oportunidad, desc: '→ Áreas para fortalecer', trend: 'neutral' as const, color: 'orange' as const },
  ]

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        title="Verificación de Cumplimiento"
        subtitle={`Revisión independiente SG-SST · ${empresa?.nombre ?? ''} · ${new Date().getFullYear()}`}
        actions={
          <Button variant="ghost" className="text-xs py-1.5" icon={<Download className="w-3.5 h-3.5" />}>
            Exportar tabla
          </Button>
        }
      />

      <div className="flex items-start gap-3 bg-slate-50 border border-slate-200 rounded-xl p-4">
        <Eye className="w-5 h-5 text-primary-500 flex-shrink-0 mt-0.5" />
        <div>
          <div className="text-primary-500 text-sm font-bold mb-0.5">Vista de solo lectura — Auditor</div>
          <div className="text-slate-600 text-xs">
            Puede visualizar toda la información pero <strong className="text-primary-500">no puede editar documentos</strong>.
            Registre hallazgos en "Mis Hallazgos".
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {KPI_DATA.map((k) => <KpiCard key={k.label} {...k} />)}
      </div>

      <Card
        title="Tabla de Verificación por Estándar Mínimo"
        subtitle={`Estado declarado por empresa · Verificación auditor · Capítulo ${empresa?.capitulo_vigente}`}
        action={<Badge variant="blue" icon={<Eye className="w-3 h-3" />}>Solo lectura</Badge>}
      >
        <div className="overflow-x-auto -mx-5 px-5">
          <Table>
            <TableHeader>
              <TableRow>
                {['Est.', 'Ciclo', 'Estándar Mínimo', 'Pts', 'Estado', 'Docs', 'Hallazgo'].map((h) => (
                  <TableHead key={h} className={h === 'Est.' ? 'pl-0' : ''}>
                    {h}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {tabla_verificacion.map((row) => {
                const verifInfo = VERIF_BADGE[row.estado_empresa] ?? VERIF_BADGE['sin_respuesta']
                return (
                  <TableRow key={row.codigo}>
                    <TableCell className="pl-0 font-bold text-slate-400">{row.codigo}</TableCell>
                    <TableCell>
                      <span className={`px-1.5 py-0.5 rounded font-bold text-[10px] ${CICLO_COLOR[row.ciclo_phva] ?? ''}`}>
                        {row.ciclo_phva?.[0] ?? '?'}
                      </span>
                    </TableCell>
                    <TableCell className="text-slate-700 font-medium max-w-xs truncate">{row.nombre}</TableCell>
                    <TableCell className="text-slate-500 text-center">{row.puntaje_maximo}</TableCell>
                    <TableCell>
                      <Badge variant={verifInfo.variant}>{verifInfo.label}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="blue">{row.documentos} doc{row.documentos !== 1 ? 's' : ''}</Badge>
                    </TableCell>
                    <TableCell>
                      {row.hallazgo_id ? (
                        <button
                          className="text-brand-700 hover:text-brand-600 font-bold transition-colors text-xs"
                          onClick={() => navigate(`/app/auditor/hallazgos?estandar=${row.codigo}`)}
                        >
                          Ver
                        </button>
                      ) : (
                        <button
                          className="text-slate-400 hover:text-brand-700 transition-colors flex items-center gap-1 text-xs"
                          onClick={() => navigate(`/app/auditor/hallazgos?estandar=${row.codigo}`)}
                        >
                          <Plus className="w-3 h-3" /> Agregar
                        </button>
                      )}
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </div>
      </Card>
    </div>
  )
}
