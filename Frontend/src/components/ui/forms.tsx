import { ReactNode, useEffect, useRef } from 'react'
import { X, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui'

interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
  footer?: ReactNode
  maxWidth?: string
}

export function Modal({ open, onClose, title, children, footer, maxWidth = '540px' }: ModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [open])

  if (!open) return null

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in"
      onClick={(e) => { if (e.target === overlayRef.current) onClose() }}
    >
      <div
        className="relative bg-white border border-slate-200 rounded-2xl shadow-2xl w-full flex flex-col max-h-[90vh] overflow-hidden"
        style={{ maxWidth }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <h3 className="text-primary-500 text-sm font-extrabold tracking-tight">{title}</h3>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-primary-500 hover:bg-slate-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto space-y-4">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-100 bg-slate-50/50">
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}

// ── FormField ─────────────────────────────────────────────────────
interface FormFieldProps {
  label: string
  error?: string
  children: ReactNode
  required?: boolean
  helperText?: string
  className?: string
}

export function FormField({ label, error, children, required, helperText, className = 'mb-4' }: FormFieldProps) {
  return (
    <div className={className}>
      <label className="flex items-center justify-between text-xs font-semibold text-slate-700 mb-1.5">
        <span>
          {label} {required && <span className="text-rose-600 font-bold">*</span>}
        </span>
      </label>
      {children}
      {error ? (
        <p className="flex items-center gap-1 text-rose-600 text-[11px] font-semibold mt-1 animate-in fade-in duration-150">
          <AlertCircle className="w-3 h-3 flex-shrink-0" />
          <span>{error}</span>
        </p>
      ) : helperText ? (
        <p className="text-slate-400 text-[11px] font-medium mt-1 leading-tight">
          {helperText}
        </p>
      ) : null}
    </div>
  )
}

// ── Input ─────────────────────────────────────────────────────────
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean
}

export function Input({ error, className = '', ...props }: InputProps) {
  return (
    <input
      className={`
        w-full bg-white border rounded-xl px-3.5 py-2.5 text-sm text-slate-900
        placeholder:text-slate-400 outline-none transition-all
        focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20
        disabled:bg-slate-50 disabled:text-slate-400 disabled:cursor-not-allowed
        ${error ? 'border-rose-400 focus:border-rose-500 focus:ring-rose-500/20' : 'border-slate-200'}
        ${className}
      `}
      {...props}
    />
  )
}

// ── Select ────────────────────────────────────────────────────────
interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  options: { value: string | number; label: string }[]
  error?: boolean
}

export function Select({ options, error, className = '', ...props }: SelectProps) {
  return (
    <select
      className={`
        w-full bg-white border rounded-xl px-3.5 py-2.5 text-sm text-slate-900
        outline-none transition-all cursor-pointer
        focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20
        disabled:bg-slate-50 disabled:text-slate-400 disabled:cursor-not-allowed
        ${error ? 'border-rose-400 focus:border-rose-500 focus:ring-rose-500/20' : 'border-slate-200'}
        ${className}
      `}
      {...props}
    >
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>{opt.label}</option>
      ))}
    </select>
  )
}

// ── Textarea ──────────────────────────────────────────────────────
interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean
}

export function Textarea({ error, className = '', rows = 3, ...props }: TextareaProps) {
  return (
    <textarea
      rows={rows}
      className={`
        w-full bg-white border rounded-xl px-3.5 py-2.5 text-sm text-slate-900
        placeholder:text-slate-400 outline-none transition-all resize-none
        focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20
        disabled:bg-slate-50 disabled:text-slate-400 disabled:cursor-not-allowed
        ${error ? 'border-rose-400 focus:border-rose-500 focus:ring-rose-500/20' : 'border-slate-200'}
        ${className}
      `}
      {...props}
    />
  )
}

// ── LoadingSpinner ────────────────────────────────────────────────
export function LoadingSpinner({ text = 'Cargando información…' }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3">
      <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      <span className="text-slate-500 text-xs font-semibold">{text}</span>
    </div>
  )
}

// ── ErrorDisplay ──────────────────────────────────────────────────
export function ErrorDisplay({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center max-w-md mx-auto p-6">
      <div className="w-12 h-12 rounded-2xl bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600 mb-3 shadow-sm">
        <AlertCircle className="w-6 h-6" />
      </div>
      <h3 className="text-primary-500 text-sm font-bold mb-1">No se pudo cargar la información</h3>
      <p className="text-slate-500 text-xs mb-4 leading-relaxed">{message}</p>
      {onRetry && (
        <Button variant="ghost" onClick={onRetry}>Reintentar consulta</Button>
      )}
    </div>
  )
}
