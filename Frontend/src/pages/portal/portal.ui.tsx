import { ReactNode, useEffect } from 'react'
import { X, CheckCircle2, AlertCircle } from 'lucide-react'

/**
 * Componentes de UI reutilizables para el Portal del Candidato (tema oscuro).
 * Evitan el uso de alert()/prompt() nativos para mantener el diseño consistente.
 */

export function PortalModal({
  open,
  onClose,
  title,
  children,
  maxWidth = '28rem',
}: {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
  maxWidth?: string
}) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="w-full rounded-2xl bg-slate-800 border border-slate-700 shadow-2xl" style={{ maxWidth }}>
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-700">
          <h3 className="text-sm font-bold text-white">{title}</h3>
          <button type="button" onClick={onClose} className="text-slate-400 hover:text-white transition" aria-label="Cerrar">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="p-5 text-xs">{children}</div>
      </div>
    </div>
  )
}

export type PortalFeedback = { type: 'success' | 'error'; text: string } | null

export function PortalToast({ feedback, onClose }: { feedback: PortalFeedback; onClose: () => void }) {
  useEffect(() => {
    if (!feedback) return
    const t = setTimeout(onClose, 4000)
    return () => clearTimeout(t)
  }, [feedback, onClose])

  if (!feedback) return null

  const isError = feedback.type === 'error'
  return (
    <div className="fixed top-4 left-1/2 -translate-x-1/2 z-[60] w-[calc(100%-2rem)] max-w-md">
      <div
        className={`flex items-start gap-3 px-4 py-3 rounded-xl border shadow-2xl backdrop-blur-sm ${
          isError
            ? 'bg-rose-950/80 border-rose-500/40 text-rose-200'
            : 'bg-emerald-950/80 border-emerald-500/40 text-emerald-200'
        }`}
      >
        {isError ? <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" /> : <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0" />}
        <span className="text-xs leading-relaxed flex-1">{feedback.text}</span>
        <button type="button" onClick={onClose} className="opacity-70 hover:opacity-100" aria-label="Cerrar">
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  )
}
