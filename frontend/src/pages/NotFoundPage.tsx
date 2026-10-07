import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/store/auth.context'
import { ROLE_ROUTES } from '@/types'
import { Home } from 'lucide-react'

export default function NotFoundPage() {
  const { user } = useAuth()
  const navigate  = useNavigate()

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center">
      <div className="text-center">
        <div className="text-8xl font-black text-brand-500/30 mb-4">404</div>
        <h1 className="text-2xl font-black text-primary-500 mb-2">Página no encontrada</h1>
        <p className="text-slate-500 text-sm mb-8">La ruta que buscas no existe en DiagnostiSST.</p>
        <button
          onClick={() => navigate(user ? ROLE_ROUTES[user.rol] : '/login')}
          className="inline-flex items-center gap-2 bg-brand-500 hover:bg-brand-600 text-white font-bold px-6 py-3 rounded-xl transition-colors"
        >
          <Home className="w-4 h-4" />
          Volver al inicio
        </button>
      </div>
    </div>
  )
}
