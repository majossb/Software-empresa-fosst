import { Outlet } from 'react-router-dom'
import { AppShell, NavSection } from '@/components/layout/AppShell'
import { Button } from '@/components/ui'
import {
  LayoutDashboard, ClipboardCheck, FileText,
  Upload, Calendar, BookOpen, Building2, Briefcase,
  ShieldCheck, AlertCircle, Users, GraduationCap, Bell, UserCheck,
  Layers, History, FileBarChart, Settings,
} from 'lucide-react'
import CompletitudBanner from './views/configuracion/CompletitudBanner'

// ── Navegación jerárquica por categorías funcionales ─────────────
const NAV_SECTIONS: NavSection[] = [
  {
    title: 'Mi Trabajo',
    items: [
      { label: 'Mi Panel', to: '/app/responsable', icon: LayoutDashboard },
    ],
  },
  {
    title: 'Organización',
    items: [
      { label: 'Configuración de Organización', to: '/app/responsable/configuracion', icon: Building2 },
      { label: 'Perfiles de Cargo', to: '/app/responsable/perfiles-cargo', icon: Briefcase },
    ],
  },
  {
    title: 'SG-SST',
    items: [
      { label: 'Estándares Mínimos', to: '/app/responsable/estandares', icon: ClipboardCheck, badge: 5, badgeColor: 'orange' },
      { label: 'Autoevaluación Anual', to: '/app/responsable/autoevaluacion', icon: FileText },
      { label: 'Cargar Evidencias', to: '/app/responsable/evidencias', icon: Upload, badge: 3, badgeColor: 'red' },
    ],
  },
  {
    title: 'Gestión Humana',
    items: [
      { label: 'Reclutamiento & Selección', to: '/app/responsable/reclutamiento', icon: UserCheck },
      { label: 'Gestión Humana & Expedientes', to: '/app/responsable/gestion-humana', icon: Users },
      { label: 'Formación & Competencias', to: '/app/responsable/formacion', icon: GraduationCap },
      { label: 'Alertas & Vencimientos', to: '/app/responsable/alertas', icon: Bell },
    ],
  },
  {
    title: 'Gestión Integral',
    items: [
      { label: 'Matriz MICHC', to: '/app/responsable/michc', icon: ShieldCheck },
      { label: 'Historial de Brechas', to: '/app/responsable/hbseo', icon: AlertCircle },
    ],
  },
  {
    title: 'Planificación',
    items: [
      { label: 'Plan de Trabajo', to: '/app/responsable/plan', icon: Calendar },
      { label: 'Capacitaciones', to: '/app/responsable/capacitaciones', icon: BookOpen, badge: 16, badgeColor: 'blue' },
    ],
  },
]

// ── Shell (layout route — renderiza Outlet para los hijos) ──────
export default function ResponsableShell() {
  return (
    <AppShell
      sections={NAV_SECTIONS}
      topbarRight={
        <Button variant="primary" className="text-xs py-1.5">
          + Cargar evidencia
        </Button>
      }
    >
      <div className="space-y-6">
        <CompletitudBanner />
        <Outlet />
      </div>
    </AppShell>
  )
}
