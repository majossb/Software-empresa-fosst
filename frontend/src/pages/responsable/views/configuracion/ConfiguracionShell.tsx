import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { modulo0Service } from '@/services/modulo0.service'
import { PageHeader } from '@/components/ui'
import { Building2, MapPin, GitBranch, Workflow, Sparkles, ArrowRight, ArrowLeft, CheckCircle2 } from 'lucide-react'

const TABS = [
  { step: 1, label: 'Información Empresa', to: '',             pathName: '/app/responsable/configuracion', icon: Building2, end: true  },
  { step: 2, label: 'Sedes Operativas',   to: 'sedes',        pathName: '/app/responsable/configuracion/sedes', icon: MapPin, end: false },
  { step: 3, label: 'Organigrama',       to: 'organigrama',  pathName: '/app/responsable/configuracion/organigrama', icon: GitBranch, end: false },
  { step: 4, label: 'Procesos',          to: 'procesos',     pathName: '/app/responsable/configuracion/procesos', icon: Workflow, end: false },
  { step: 5, label: 'Identidad Estratégica', to: 'identidad', pathName: '/app/responsable/configuracion/identidad', icon: Sparkles, end: false },
]

export default function ConfiguracionShell() {
  const navigate = useNavigate()
  const location = useLocation()

  const { data: completitud } = useQuery({
    queryKey: ['modulo0', 'completitud'],
    queryFn: modulo0Service.getCompletitud,
    staleTime: 30_000,
  })

  // Identificar paso activo
  const currentPath = location.pathname
  const currentTabIndex = TABS.findIndex(t => {
    if (t.to === '') {
      return currentPath === '/app/responsable/configuracion' || currentPath === '/app/responsable/configuracion/'
    }
    return currentPath.includes(t.to)
  })

  const activeIndex = currentTabIndex >= 0 ? currentTabIndex : 0

  const handlePrevStep = () => {
    if (activeIndex > 0) {
      const prevTab = TABS[activeIndex - 1]
      navigate(prevTab.to ? `/app/responsable/configuracion/${prevTab.to}` : '/app/responsable/configuracion')
    }
  }

  const handleNextStep = () => {
    if (activeIndex < TABS.length - 1) {
      const nextTab = TABS[activeIndex + 1]
      navigate(`/app/responsable/configuracion/${nextTab.to}`)
    } else {
      // Finalizar Wizard → Dashboard
      navigate('/app/responsable')
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Asistente de Configuración Inicial (Módulo 0)"
        subtitle="Contexto de la Organización — Completa los 5 pasos para desbloquear tu diagnóstico SG-SST"
      />

      {/* Barra de progreso de completitud */}
      <div className="bg-surface-1 p-4 rounded-xl border border-surface-2 shadow-sm space-y-2">
        <div className="flex items-center justify-between text-xs font-bold">
          <span className="text-slate-600 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-brand-500" />
            Progreso general de configuración del SG-SST
          </span>
          <span className="text-brand-600 font-extrabold text-sm">
            {completitud?.porcentaje ?? 0}% completado
          </span>
        </div>

        <div className="h-2.5 bg-surface-2 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-brand-500 to-primary-500 transition-all duration-700"
            style={{ width: `${completitud?.porcentaje ?? 0}%` }}
          />
        </div>
      </div>

      {/* Tabs / Wizard Steps */}
      <div className="border-b border-surface-2">
        <nav className="flex gap-2 overflow-x-auto scrollbar-hide pb-1">
          {TABS.map((tab, idx) => (
            <NavLink
              key={tab.label}
              to={tab.to}
              end={tab.end}
              className={({ isActive }) => `
                relative flex items-center gap-2.5 px-4 py-3 text-sm font-semibold
                transition-all duration-200 whitespace-nowrap rounded-t-lg group
                ${isActive
                  ? 'bg-surface-1 text-primary-600 border-b-2 border-brand-500 shadow-sm'
                  : 'text-slate-400 hover:text-slate-600 hover:bg-surface-1/50'
                }
              `}
            >
              {({ isActive }) => (
                <>
                  <span className={`
                    w-6 h-6 rounded-full text-xs font-extrabold flex items-center justify-center transition-colors
                    ${isActive
                      ? 'bg-brand-500 text-white'
                      : idx < activeIndex
                      ? 'bg-emerald-500 text-white'
                      : 'bg-surface-2 text-slate-500'
                    }
                  `}>
                    {idx < activeIndex ? <CheckCircle2 className="w-3.5 h-3.5" /> : tab.step}
                  </span>

                  <tab.icon className={`w-4 h-4 transition-colors ${isActive ? 'text-brand-500' : 'text-slate-400'}`} />

                  <span>{tab.label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Vista del paso activo */}
      <div className="min-h-[400px]">
        <Outlet />
      </div>

      {/* Controles de Navegación del Asistente */}
      <div className="flex items-center justify-between pt-6 border-t border-surface-2">
        <button
          type="button"
          onClick={handlePrevStep}
          disabled={activeIndex === 0}
          className={`
            inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm transition-all
            ${activeIndex === 0
              ? 'opacity-40 cursor-not-allowed text-slate-400 bg-surface-2'
              : 'text-slate-700 bg-surface-1 hover:bg-surface-2 border border-surface-2 shadow-sm'
            }
          `}
        >
          <ArrowLeft className="w-4 h-4" />
          Paso anterior
        </button>

        <button
          type="button"
          onClick={handleNextStep}
          className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl font-bold text-sm text-white bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-700 shadow-md hover:shadow-lg transition-all"
        >
          {activeIndex === TABS.length - 1 ? (
            <>
              Finalizar configuración e ir al Dashboard
              <CheckCircle2 className="w-4 h-4" />
            </>
          ) : (
            <>
              Siguiente paso ({TABS[activeIndex + 1]?.label})
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </div>
  )
}
