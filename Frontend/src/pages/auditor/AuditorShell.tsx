import { Outlet, useNavigate } from 'react-router-dom'
import { AppShell, NavSection } from '@/components/layout/AppShell'
import { Button } from '@/components/ui'
import { Eye, FileText, ClipboardCheck, AlertCircle, History, Pencil } from 'lucide-react'

// ── Navegación declarativa ──────────────────────────────────────
const NAV_SECTIONS: NavSection[] = [
  {
    title: 'Verificación',
    items: [
      { label: 'Verificación Cumplimiento', to: '/app/auditor',               icon: Eye           },
      { label: 'Ver Evidencias Cargadas',   to: '/app/auditor/evidencias',     icon: FileText      },
      { label: 'Ver Autoevaluación',        to: '/app/auditor/autoevaluacion', icon: ClipboardCheck},
    ],
  },
  {
    title: 'Mi Auditoría',
    items: [
      { label: 'Mis Hallazgos',    to: '/app/auditor/hallazgos',   icon: AlertCircle },
      { label: 'Apelaciones',      to: '/app/auditor/apelaciones', icon: ClipboardCheck },
      { label: 'Informe Final',    to: '/app/auditor/informe',     icon: FileText    },
      { label: 'Historial',        to: '/app/auditor/historial',   icon: History     },
    ],
  },
]

// ── Shell (layout route — renderiza Outlet para los hijos) ──────
export default function AuditorShell() {
  const navigate = useNavigate()

  return (
    <AppShell
      sections={NAV_SECTIONS}
      topbarRight={
        <>
          <span className="inline-flex items-center gap-1.5 text-xs font-bold bg-slate-100 text-primary-500 border border-slate-200 px-2.5 py-1 rounded-lg">
            <Eye className="w-3.5 h-3.5 text-primary-500" />
            SOLO LECTURA
          </span>
          <Button
            variant="ghost"
            icon={Pencil}
            className="text-xs py-1.5"
            onClick={() => navigate('/app/auditor/hallazgos')}
          >
            Nuevo hallazgo
          </Button>
          <Button
            variant="primary"
            icon={FileText}
            className="text-xs py-1.5"
            onClick={() => navigate('/app/auditor/informe')}
          >
            Informe final
          </Button>
        </>
      }
    >
      <Outlet />
    </AppShell>
  )
}
