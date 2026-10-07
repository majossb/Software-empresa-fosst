import { Card, PageHeader, Badge } from '@/components/ui'
import { LoadingSpinner, ErrorDisplay } from '@/components/ui/forms'
import { useDashboardAD } from '@/hooks/useApi'
import { ShieldAlert, AlertTriangle, Scale, CheckCircle2 } from 'lucide-react'

function formatCOP(n: number) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(n)
}

export default function SancionesView() {
  const { data, isLoading, error, refetch } = useDashboardAD()

  if (isLoading) return <LoadingSpinner text="Analizando exposición legal..." />
  if (error || !data) return <ErrorDisplay message={(error as Error)?.message ?? 'Error'} onRetry={refetch} />

  const { sancion, estandares_criticos, cumplimiento } = data

  const articulos = [
    { art: 'Art. 13 Ley 1562/2012', desc: 'Multa por incumplimiento de normas SST', rango: 'Hasta 500 SMMLV', aplica: cumplimiento.no_cumple > 0 },
    { art: 'Art. 30 Ley 1562/2012', desc: 'Multas sucesivas por incumplimiento reiterado', rango: 'Hasta 1000 SMMLV', aplica: cumplimiento.no_cumple > 3 },
    { art: 'Art. 12 Decreto 1072/2015', desc: 'Clausura temporal del lugar de trabajo', rango: 'Hasta 120 días', aplica: cumplimiento.global < 40 },
    { art: 'Art. 28 Decreto 472/2015', desc: 'Graduación de sanciones según empresa', rango: 'Variable', aplica: true },
  ]

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader title="Riesgos y Sanciones" subtitle="Exposición legal por incumplimiento SG-SST · Decreto 1072/2015" />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="border-red-200">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-red-100 flex items-center justify-center">
              <ShieldAlert className="w-5 h-5 text-red-600" />
            </div>
            <div className="text-xs text-slate-500 uppercase font-bold">Sanción potencial</div>
          </div>
          <div className="text-2xl font-black text-red-700">{formatCOP(sancion.potencial)}</div>
          <div className="text-xs text-slate-500 mt-1">{sancion.factor}% de exposición sobre {formatCOP(500 * sancion.smmlv)}</div>
        </Card>

        <Card className="border-green-200">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-green-100 flex items-center justify-center">
              <Scale className="w-5 h-5 text-green-600" />
            </div>
            <div className="text-xs text-slate-500 uppercase font-bold">Multas evitadas</div>
          </div>
          <div className="text-2xl font-black text-green-700">{formatCOP(sancion.evitada)}</div>
          <div className="text-xs text-slate-500 mt-1">Gracias al {cumplimiento.global}% de cumplimiento</div>
        </Card>

        <Card className="border-brand-200">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-brand-50 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-brand-700" />
            </div>
            <div className="text-xs text-slate-500 uppercase font-bold">SMMLV 2025</div>
          </div>
          <div className="text-2xl font-black text-brand-700">{formatCOP(sancion.smmlv)}</div>
          <div className="text-xs text-slate-500 mt-1">Base de cálculo para sanciones</div>
        </Card>
      </div>

      <Card title="Marco Legal Aplicable" subtitle="Artículos que generan riesgo de sanción">
        <div className="space-y-3">
          {articulos.map((a) => (
            <div key={a.art} className={`flex items-start gap-3 p-3 rounded-xl border ${a.aplica ? 'bg-red-50 border-red-200' : 'bg-surface border-surface-2'}`}>
              <Badge variant={a.aplica ? 'red' : 'gray'}>{a.aplica ? 'APLICA' : 'N/A'}</Badge>
              <div className="flex-1">
                <div className="text-sm font-bold text-primary-500">{a.art}</div>
                <div className="text-xs text-slate-500 mt-0.5">{a.desc}</div>
              </div>
              <div className="text-xs text-slate-500 font-medium">{a.rango}</div>
            </div>
          ))}
        </div>
      </Card>

      <Card title={`${estandares_criticos.length} Estándares con Riesgo Legal`} subtitle="Incumplimientos que elevan la sanción potencial">
        {estandares_criticos.length === 0 ? (
          <div className="text-center py-8 text-green-700 text-sm font-bold flex items-center justify-center gap-1.5">
            <CheckCircle2 className="w-4 h-4" /> Sin estándares de riesgo
          </div>
        ) : (
          <div className="space-y-2">
            {estandares_criticos.map((e) => (
              <div key={e.codigo} className="flex items-center gap-3 p-3 bg-surface rounded-xl">
                <span className="text-xs font-bold text-slate-500 w-14">{e.codigo}</span>
                <span className="text-xs text-slate-700 flex-1 truncate">{e.nombre}</span>
                <Badge variant={e.estado === 'no_cumple' ? 'red' : 'orange'}>{e.porcentaje}%</Badge>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
