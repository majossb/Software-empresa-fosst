import { useState } from 'react'
import { KpiCard, Card, PageHeader, Badge, Button } from '@/components/ui'
import { LoadingSpinner, ErrorDisplay } from '@/components/ui/forms'
import { AlertTriangle, ArrowRight, ChevronDown, CheckCircle2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useDashboardAD } from '@/hooks/useApi'

function EstadoBadge({ estado }: { estado: string }) {
  if (estado === 'no_cumple') return <Badge variant="red">No cumple</Badge>
  if (estado === 'parcial')   return <Badge variant="orange">Parcial</Badge>
  return <Badge variant="green">Cumple</Badge>
}

function formatCOP(n: number) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(n)
}

export default function AltaDireccionDashboard() {
  const navigate = useNavigate()
  const { data, isLoading, error, refetch } = useDashboardAD()
  const [activeCardId, setActiveCardId] = useState<string | null>('sg-sst')

  const toggleCard = (id: string) => {
    setActiveCardId((prev) => (prev === id ? null : id))
  }

  if (isLoading) return <LoadingSpinner text="Cargando panel ejecutivo..." />
  if (error || !data) return <ErrorDisplay message={(error as Error)?.message ?? 'Error cargando datos'} onRetry={refetch} />

  const { cumplimiento, phva, estandares_criticos, sancion, empresa } = data

  const KPI_DATA = [
    { id: 'sg-sst', label: 'Cumplimiento Global SG-SST', valor: `${cumplimiento.global}%`, desc: `${cumplimiento.cumplidos}/${cumplimiento.total_estandares} estándares`, trend: cumplimiento.global >= 60 ? 'up' as const : 'down' as const, color: 'orange' as const },
    { id: 'gestion-humana', label: 'Módulo de Gestión Humana', valor: '82%', desc: `4 secciones activas`, trend: 'neutral' as const, color: 'red' as const },
    { id: 'pesv', label: 'Plan Estratégico de Seguridad Vial (PESV)', valor: 'Diseño', desc: `Avance 30%`, trend: 'up' as const, color: 'green' as const },
    { id: 'participacion', label: 'Nivel de Participación de Trabajadores', valor: 'Alto', desc: `85% de asistencia`, trend: 'up' as const, color: 'blue' as const },
  ]

  const PHVA_DATA = [
    { ciclo: 'P · Planear',   pct: phva['Planear']?.porcentaje ?? 0,   color: 'bg-blue-500' },
    { ciclo: 'H · Hacer',     pct: phva['Hacer']?.porcentaje ?? 0,     color: 'bg-brand-500' },
    { ciclo: 'V · Verificar', pct: phva['Verificar']?.porcentaje ?? 0, color: 'bg-primary-500' },
    { ciclo: 'A · Actuar',    pct: phva['Actuar']?.porcentaje ?? 0,    color: 'bg-green-500' },
  ]

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        title="Panel Ejecutivo — Alta Dirección"
        subtitle={`Visión financiera, cumplimiento SG-SST y riesgo legal · ${empresa?.nombre ?? ''} · ${new Date().getFullYear()}`}
      />

      {/* Alerta crítica — solo si hay incumplimientos */}
      {cumplimiento.no_cumple > 0 && (
        <div style={{ display: 'none' }} className="flex items-start gap-4 bg-red-50 border border-red-200 rounded-2xl p-5">
          <div className="w-10 h-10 rounded-xl bg-red-100 flex items-center justify-center flex-shrink-0 mt-0.5">
            <AlertTriangle className="w-5 h-5 text-red-600" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-red-700 text-sm font-bold mb-1">
              RIESGO SANCIÓN ACTIVO — Incumplimiento en {cumplimiento.no_cumple} estándares (Art. 28 · Decreto 1072/2015)
            </div>
            <div className="text-slate-600 text-xs leading-relaxed">
              La empresa está expuesta a multas de hasta{' '}
              <span className="text-red-700 font-bold">{formatCOP(sancion.potencial)}</span>.
              Acción inmediata requerida para los estándares críticos.
            </div>
          </div>
          <Button
            variant="danger"
            className="flex-shrink-0 text-xs py-1.5"
            onClick={() => navigate('/app/alta-direccion/sanciones')}
          >
            Ver exposición <ArrowRight className="w-3 h-3" />
          </Button>
        </div>
      )}

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {KPI_DATA.map((kpi) => (
          <div
            key={kpi.id}
            onClick={() => toggleCard(kpi.id)}
            className={`cursor-pointer transition-all duration-300 rounded-2xl relative select-none ${
              activeCardId === kpi.id
                ? 'ring-2 ring-primary-500 ring-offset-2 scale-[1.02] shadow-lg'
                : 'hover:scale-[1.02]'
            }`}
          >
            <KpiCard label={kpi.label} valor={kpi.valor} desc={kpi.desc} trend={kpi.trend} color={kpi.color} />
            
            {/* Indicador visual Chevron */}
            <div
              className={`absolute -bottom-3 left-1/2 -translate-x-1/2 w-6 h-6 rounded-full bg-white shadow-md border border-surface-2 flex items-center justify-center transition-all duration-300 z-10 ${
                activeCardId === kpi.id ? 'opacity-100 text-primary-500 bg-primary-50 border-primary-200' : 'opacity-0 scale-50'
              }`}
            >
              <ChevronDown className={`w-4 h-4 transition-transform duration-300 ${activeCardId === kpi.id ? 'rotate-180' : ''}`} />
            </div>
          </div>
        ))}
      </div>

      {/* Contenido desplegable (Accordion) */}
      <div
        className={`grid grid-cols-1 overflow-hidden transition-all duration-500 ease-in-out ${
          activeCardId ? 'opacity-100 max-h-[3000px] mt-6' : 'opacity-0 max-h-0 mt-0'
        }`}
      >
        {/* Tarjeta 1 - Cumplimiento Global SG-SST */}
        {activeCardId === 'sg-sst' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 animate-fade-in">
            {/* Estándares críticos */}
            <div className="lg:col-span-2">
              <Card
                title="Estándares Críticos — Acción Inmediata"
                subtitle="Incumplimientos que generan exposición legal máxima"
                action={
                  <Button variant="ghost" className="text-xs py-1" onClick={() => navigate('/app/alta-direccion/cumplimiento')}>
                    Ver todos →
                  </Button>
                }
              >
                {estandares_criticos.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-green-600 text-sm font-bold flex items-center justify-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4" /> Sin estándares críticos
                    </div>
                    <div className="text-slate-500 text-xs mt-1">Todos los estándares tienen un nivel aceptable</div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {estandares_criticos.map((e) => (
                      <div key={e.codigo} className="flex items-center gap-3">
                        <div className="w-12 text-xs font-bold text-slate-500 flex-shrink-0">{e.codigo}</div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm text-slate-700 font-medium truncate">{e.nombre}</span>
                            <span className="text-xs text-slate-500 ml-2 flex-shrink-0">{e.porcentaje}%</span>
                          </div>
                          <div className="h-1.5 bg-surface-2 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${
                                e.porcentaje < 20 ? 'bg-red-500' : e.porcentaje < 50 ? 'bg-brand-500' : 'bg-green-500'
                              }`}
                              style={{ width: `${Math.max(e.porcentaje, 2)}%` }}
                            />
                          </div>
                        </div>
                        <div className="flex-shrink-0">
                          <EstadoBadge estado={e.estado} />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </div>

            {/* PHVA Breakdown */}
            <Card title="Ciclo PHVA" subtitle="Avance por fase — datos en tiempo real">
              <div className="space-y-4">
                {PHVA_DATA.map((p) => (
                  <div key={p.ciclo}>
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="text-xs font-semibold text-slate-600">{p.ciclo}</span>
                      <span className="text-xs font-bold text-primary-500">{p.pct}%</span>
                    </div>
                    <div className="h-2 bg-surface-2 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${p.color}`}
                        style={{ width: `${p.pct}%`, transition: 'width 1s ease-out' }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 pt-4 border-t border-surface-2">
                <div className="text-center">
                  <div className="text-3xl font-black text-brand-700 mb-1">{cumplimiento.global}%</div>
                  <div className="text-xs text-slate-500">Cumplimiento global</div>
                  <div className="text-xs text-slate-400 mt-0.5">Meta: 85%</div>
                </div>
                <div className="mt-4 h-2 bg-surface-2 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-red-500 via-brand-500 to-green-500 rounded-full" style={{ width: `${cumplimiento.global}%` }} />
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* Tarjeta 2 - Módulo de Gestión Humana */}
        {activeCardId === 'gestion-humana' && (
          <div className="animate-fade-in">
            <Card title="Módulo de Gestión Humana" subtitle="Indicadores principales de talento humano">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-2">
                <div className="p-5 bg-surface rounded-xl border border-surface-2 flex flex-col items-center justify-center text-center">
                  <div className="text-3xl font-black text-slate-700">124</div>
                  <div className="text-sm font-medium text-slate-500 mt-2">Colaboradores activos</div>
                </div>
                <div className="p-5 bg-surface rounded-xl border border-surface-2 flex flex-col items-center justify-center text-center">
                  <div className="text-3xl font-black text-brand-600">15</div>
                  <div className="text-sm font-medium text-slate-500 mt-2">Capacitaciones pendientes</div>
                </div>
                <div className="p-5 bg-surface rounded-xl border border-surface-2 flex flex-col items-center justify-center text-center">
                  <div className="text-3xl font-black text-green-600">89%</div>
                  <div className="text-sm font-medium text-slate-500 mt-2">Evaluaciones de desempeño</div>
                </div>
                <div className="p-5 bg-surface rounded-xl border border-surface-2 flex flex-col items-center justify-center text-center">
                  <div className="text-3xl font-black text-primary-500">3</div>
                  <div className="text-sm font-medium text-slate-500 mt-2">Novedades de nómina</div>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* Tarjeta 3 - PESV */}
        {activeCardId === 'pesv' && (
          <div className="animate-fade-in">
            <Card title="Plan Estratégico de Seguridad Vial (PESV)" subtitle="Avance e indicadores de accidentalidad">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-2">
                <div className="p-5 bg-surface rounded-xl border border-surface-2 flex flex-col items-center justify-center text-center">
                  <div className="text-3xl font-black text-slate-700">30%</div>
                  <div className="text-sm font-medium text-slate-500 mt-2">Avance del plan</div>
                </div>
                <div className="p-5 bg-surface rounded-xl border border-surface-2 flex flex-col items-center justify-center text-center">
                  <div className="text-3xl font-black text-red-600">5</div>
                  <div className="text-sm font-medium text-slate-500 mt-2">Acciones pendientes</div>
                </div>
                <div className="p-5 bg-surface rounded-xl border border-surface-2 flex flex-col items-center justify-center text-center">
                  <div className="text-3xl font-black text-green-600">0</div>
                  <div className="text-sm font-medium text-slate-500 mt-2">Indicadores de accidentalidad vial</div>
                </div>
                <div className="p-5 bg-surface rounded-xl border border-surface-2 flex flex-col items-center justify-center text-center">
                  <div className="text-3xl font-black text-blue-600">12 Nov</div>
                  <div className="text-sm font-medium text-slate-500 mt-2">Próximas auditorías PESV</div>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* Tarjeta 4 - Participación */}
        {activeCardId === 'participacion' && (
          <div className="animate-fade-in">
            <Card title="Nivel de Participación de Trabajadores" subtitle="Involucramiento y clima laboral">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-2">
                <div className="p-5 bg-surface rounded-xl border border-surface-2 flex flex-col items-center justify-center text-center">
                  <div className="text-3xl font-black text-slate-700">85%</div>
                  <div className="text-sm font-medium text-slate-500 mt-2">% participación en capacitaciones</div>
                </div>
                <div className="p-5 bg-surface rounded-xl border border-surface-2 flex flex-col items-center justify-center text-center">
                  <div className="text-3xl font-black text-brand-600">Activo</div>
                  <div className="text-sm font-medium text-slate-500 mt-2">Comité COPASST</div>
                </div>
                <div className="p-5 bg-surface rounded-xl border border-surface-2 flex flex-col items-center justify-center text-center">
                  <div className="text-3xl font-black text-green-600">4.2/5</div>
                  <div className="text-sm font-medium text-slate-500 mt-2">Encuestas de clima laboral</div>
                </div>
                <div className="p-5 bg-surface rounded-xl border border-surface-2 flex flex-col items-center justify-center text-center">
                  <div className="text-3xl font-black text-primary-500">2</div>
                  <div className="text-sm font-medium text-slate-500 mt-2">Actividades de bienestar</div>
                </div>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
