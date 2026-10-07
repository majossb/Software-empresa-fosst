import { ReactNode } from 'react'
import {
  TrendingUp, TrendingDown, Minus, LucideIcon,
  AlertCircle, AlertTriangle, CheckCircle2, Info, FolderOpen
} from 'lucide-react'

export { FOSST_ICONS } from './icons'
export type { FosstIconName } from './icons'

// ── KpiCard (Estructura Unificada FOSST) ──────────────────────────
const KPI_COLORS = {
  blue:   { bg: 'bg-white', border: 'border-slate-200', val: 'text-primary-500' },
  green:  { bg: 'bg-white', border: 'border-slate-200', val: 'text-emerald-700' },
  red:    { bg: 'bg-white', border: 'border-slate-200', val: 'text-rose-600' },
  orange: { bg: 'bg-white', border: 'border-slate-200', val: 'text-brand-700' },
  purple: { bg: 'bg-white', border: 'border-slate-200', val: 'text-primary-500' },
}

interface KpiCardProps {
  label: string
  valor: string | number
  desc:  string
  trend?: 'up' | 'down' | 'neutral'
  color?: keyof typeof KPI_COLORS
  icon?: LucideIcon
}

export function KpiCard({ label, valor, desc, trend = 'neutral', color = 'blue', icon: Icon }: KpiCardProps) {
  const c = KPI_COLORS[color] ?? KPI_COLORS.blue
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus
  const trendColor = trend === 'up' ? 'text-emerald-700 font-semibold' : trend === 'down' ? 'text-rose-600 font-semibold' : 'text-slate-500 font-medium'

  return (
    <div className={`relative rounded-2xl border p-5 bg-white shadow-sm hover:shadow-md transition-shadow ${c.border}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">{label}</div>
        {Icon && (
          <div className="p-2 rounded-xl bg-slate-50 text-primary-500 flex-shrink-0">
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>
      <div className={`text-3xl font-black mb-1 font-mono tracking-tight ${c.val}`}>{valor}</div>
      <div className={`flex items-center gap-1 text-xs ${trendColor}`}>
        <TrendIcon className="w-3.5 h-3.5" />
        <span>{desc}</span>
      </div>
    </div>
  )
}

// ── Card ────────────────────────────────────────────────────────
interface CardProps {
  title?:    string
  subtitle?: string
  action?:   ReactNode
  children:  ReactNode
  className?: string
}

export function Card({ title, subtitle, action, children, className = '' }: CardProps) {
  return (
    <div className={`bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm ${className}`}>
      {(title || action) && (
        <div className="flex items-start justify-between p-5 pb-0">
          {title && (
            <div>
              <div className="text-primary-500 text-sm font-extrabold tracking-tight">{title}</div>
              {subtitle && <div className="text-slate-500 text-xs mt-0.5 font-medium">{subtitle}</div>}
            </div>
          )}
          {action && <div className="flex-shrink-0 ml-4">{action}</div>}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  )
}

// ── Badge (Estilo Unificado en todo el sistema) ────────────────────
export type BadgeVariant = 'green' | 'red' | 'orange' | 'blue' | 'purple' | 'gray'

const BADGE_STYLES: Record<BadgeVariant, string> = {
  green:  'bg-emerald-50 text-emerald-800 border-emerald-200',
  red:    'bg-rose-50 text-rose-800 border-rose-200',
  orange: 'bg-amber-50 text-amber-900 border-amber-200',
  blue:   'bg-blue-50 text-primary-500 border-blue-200',
  purple: 'bg-slate-100 text-primary-500 border-slate-200',
  gray:   'bg-slate-100 text-slate-700 border-slate-200',
}

function renderIcon(icon: ReactNode | LucideIcon | undefined, defaultClass: string) {
  if (!icon) return null
  if (typeof icon === 'function' || (typeof icon === 'object' && icon !== null && 'render' in (icon as any))) {
    const IconComponent = icon as LucideIcon
    return <IconComponent className={defaultClass} />
  }
  return <>{icon}</>
}

export function Badge({ children, variant = 'gray', icon, className = '' }: {
  children: ReactNode
  variant?: BadgeVariant
  icon?: ReactNode | LucideIcon
  className?: string
}) {
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-0.5 rounded-md border ${BADGE_STYLES[variant]} ${className}`}>
      {renderIcon(icon, "w-3.5 h-3.5 flex-shrink-0")}
      <span>{children}</span>
    </span>
  )
}

// ── PageHeader ──────────────────────────────────────────────────
export function PageHeader({ title, subtitle, actions }: {
  title:     string
  subtitle?: string
  actions?:  ReactNode
}) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4 border-b border-slate-200 pb-4">
      <div>
        <h1 className="text-2xl font-black text-primary-500 tracking-tight font-sans">{title}</h1>
        {subtitle && <p className="text-slate-500 text-xs font-medium mt-1">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2.5 flex-shrink-0">{actions}</div>}
    </div>
  )
}

// ── Button ───────────────────────────────────────────────────────
export type ButtonVariant = 'primary' | 'ghost' | 'danger' | 'secondary'

const BTN_STYLES: Record<ButtonVariant, string> = {
  primary:   'bg-brand-500 hover:bg-brand-600 text-slate-950 font-bold shadow-sm shadow-amber-500/20',
  secondary: 'bg-primary-500 hover:bg-primary-600 text-white font-bold shadow-sm',
  ghost:     'bg-white hover:bg-slate-100 text-primary-500 border border-slate-200 font-semibold',
  danger:    'bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-semibold',
}

export function Button({
  children, variant = 'ghost', onClick, disabled, className = '', type = 'button', title, icon,
}: {
  children:  ReactNode
  variant?:  ButtonVariant
  onClick?:  (e?: any) => void
  disabled?: boolean
  className?: string
  type?:      'button' | 'submit' | 'reset'
  title?:     string
  icon?:      ReactNode | LucideIcon
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={`
        inline-flex items-center justify-center gap-2 text-xs font-bold px-4 py-2.5 rounded-xl
        transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed
        ${BTN_STYLES[variant]} ${className}
      `}
    >
      {renderIcon(icon, "w-4 h-4 flex-shrink-0")}
      <span>{children}</span>
    </button>
  )
}

// ── Alert (Banners Semánticos Centralizados) ────────────────────────
export type AlertVariant = 'info' | 'success' | 'warning' | 'danger'

const ALERT_CONFIG: Record<AlertVariant, { container: string; text: string; icon: LucideIcon }> = {
  info:    { container: 'bg-primary-50/70 border-primary-200', text: 'text-primary-800', icon: Info },
  success: { container: 'bg-emerald-50/70 border-emerald-200', text: 'text-emerald-800', icon: CheckCircle2 },
  warning: { container: 'bg-amber-50/70 border-amber-200',     text: 'text-amber-900',   icon: AlertTriangle },
  danger:  { container: 'bg-rose-50/70 border-rose-200',       text: 'text-rose-800',    icon: AlertCircle },
}

export function Alert({
  variant = 'info',
  title,
  children,
  className = '',
  action,
}: {
  variant?: AlertVariant
  title?: string
  children: ReactNode
  className?: string
  action?: ReactNode
}) {
  const cfg = ALERT_CONFIG[variant]
  const Icon = cfg.icon

  return (
    <div className={`p-4 rounded-xl border flex items-start gap-3.5 ${cfg.container} ${className}`}>
      <Icon className={`w-5 h-5 flex-shrink-0 mt-0.5 ${cfg.text}`} />
      <div className="flex-1 min-w-0 text-xs leading-relaxed space-y-0.5">
        {title && <div className={`font-bold ${cfg.text}`}>{title}</div>}
        <div className="text-slate-700">{children}</div>
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  )
}

// ── EmptyState (Estado Vacío Centralizado) ──────────────────────────
export function EmptyState({
  icon = FolderOpen,
  title,
  description,
  action,
  className = '',
}: {
  icon?: ReactNode | LucideIcon
  title: string
  description?: string
  action?: ReactNode
  className?: string
}) {
  return (
    <div className={`p-8 text-center flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50/60 my-4 ${className}`}>
      <div className="w-12 h-12 rounded-2xl bg-white border border-slate-200 flex items-center justify-center mb-3 shadow-sm text-slate-400">
        {renderIcon(icon, "w-6 h-6")}
      </div>
      <h3 className="text-sm font-bold text-primary-500 mb-1">{title}</h3>
      {description && <p className="text-xs text-slate-500 max-w-sm mb-4 leading-relaxed">{description}</p>}
      {action && <div>{action}</div>}
    </div>
  )
}

// ── Table (Componentes Unificados para Tablas) ──────────────────────
export function Table({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className="w-full overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
      <table className={`w-full text-left border-collapse text-xs ${className}`}>
        {children}
      </table>
    </div>
  )
}

export function TableHeader({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <thead className={`bg-slate-50 border-b border-slate-200 text-slate-600 uppercase text-[10px] font-black tracking-wider ${className}`}>
      {children}
    </thead>
  )
}

export function TableBody({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <tbody className={`divide-y divide-slate-100 ${className}`}>{children}</tbody>
}

export function TableRow({ children, className = '', onClick }: { children: ReactNode; className?: string; onClick?: () => void }) {
  return (
    <tr
      onClick={onClick}
      className={`transition-colors hover:bg-slate-50/80 ${onClick ? 'cursor-pointer' : ''} ${className}`}
    >
      {children}
    </tr>
  )
}

export function TableHead({ children, className = '' }: { children?: ReactNode; className?: string }) {
  return <th className={`px-4 py-3.5 font-bold ${className}`}>{children}</th>
}

export function TableCell({ children, className = '' }: { children?: ReactNode; className?: string }) {
  return <td className={`px-4 py-3.5 text-slate-700 font-medium ${className}`}>{children}</td>
}