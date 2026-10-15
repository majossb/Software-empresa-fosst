import { Construction, Eye } from 'lucide-react'
import { ROLE_LABELS } from '@/types'
import type { UserRole } from '@/types'

interface Props {
  title:    string
  rol:      UserRole
  readOnly?: boolean
}

export default function PlaceholderView({ title, rol, readOnly }: Props) {
  return (
    <div className="animate-fade-in flex flex-col items-center justify-center min-h-[60vh] text-center">
      <div className="w-16 h-16 rounded-2xl bg-brand-50 border border-brand-200 flex items-center justify-center mb-5">
        <Construction className="w-7 h-7 text-brand-700" />
      </div>
      <h2 className="text-xl font-black text-primary-500 mb-2">{title}</h2>
      <p className="text-slate-500 text-sm max-w-sm leading-relaxed mb-4">
        Esta vista está en desarrollo. Será implementada como componente React
        conectado al backend Express.
      </p>
      <div className="flex items-center gap-2 flex-wrap justify-center">
        <span className="text-xs bg-surface text-slate-600 px-3 py-1.5 rounded-lg border border-surface-2">
          Rol: {ROLE_LABELS[rol]}
        </span>
        {readOnly && (
          <span className="text-xs bg-primary-50 text-primary-500 px-3 py-1.5 rounded-lg border border-primary-200 inline-flex items-center gap-1">
            <Eye className="w-3.5 h-3.5" /> Solo lectura
          </span>
        )}
      </div>
    </div>
  )
}
