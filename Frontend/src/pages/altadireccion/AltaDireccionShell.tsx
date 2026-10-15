import { Outlet } from 'react-router-dom'
import { AppShell, NavSection } from '@/components/layout/AppShell'
import { Button } from '@/components/ui'
import {
  LayoutDashboard, TrendingUp, ShieldAlert,
  ClipboardCheck, FileText, History, Settings,
} from 'lucide-react'

// ── Navegación declarativa ──────────────────────────────────────
const NAV_SECTIONS: NavSection[] = [
  {
    title: 'Panel Ejecutivo',
    items: [
      { label: 'Dashboard General',  to: '/app/alta-direccion',             icon: LayoutDashboard },
      { label: 'Cumplimiento SG-SST',to: '/app/alta-direccion/cumplimiento', icon: TrendingUp      },
      { label: 'Riesgos y Sanciones',to: '/app/alta-direccion/sanciones',    icon: ShieldAlert, badge: '!', badgeColor: 'red' },
      { label: 'Plan de Mejora',     to: '/app/alta-direccion/plan',         icon: ClipboardCheck, badge: 3, badgeColor: 'orange' },
    ],
  },
  {
    title: 'Reportes',
    items: [
      { label: 'Informes Ejecutivos',to: '/app/alta-direccion/informes',  icon: FileText },
      { label: 'Historial Anual',    to: '/app/alta-direccion/historial', icon: History  },
    ],
  },
  {
    title: 'Configuración',
    items: [
      { label: 'Config. empresa',    to: '/app/alta-direccion/config',    icon: Settings },
    ],
  },
]

// ── Shell (layout route — renderiza Outlet para los hijos) ──────
export default function AltaDireccionShell() {
  return (
    <AppShell
      sections={NAV_SECTIONS}
      topbarRight={
        <>
          <Button variant="ghost" className="text-xs py-1.5">Exportar</Button>
          <Button variant="primary" className="text-xs py-1.5">Ver plan de mejora →</Button>
        </>
      }
    >
      <Outlet />
    </AppShell>
  )
}
