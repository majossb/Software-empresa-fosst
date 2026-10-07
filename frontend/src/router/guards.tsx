import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '@/store/auth.context'
import { UserRole, ROLE_ROUTES } from '@/types'

// ── Guard genérico: requiere autenticación ──────────────────────
export function RequireAuth() {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()

  if (loading) return <FullScreenSpinner />

  return isAuthenticated
    ? <Outlet />
    : <Navigate to="/login" state={{ from: location }} replace />
}

// ── Guard de rol: redirige si el rol no coincide ────────────────
export function RequireRole({ roles }: { roles: UserRole[] }) {
  const { user } = useAuth()

  if (!user) return <Navigate to="/login" replace />

  return roles.includes(user.rol)
    ? <Outlet />
    : <Navigate to={ROLE_ROUTES[user.rol]} replace />
}

// ── Redirect desde / según rol autenticado ──────────────────────
export function RoleRedirect() {
  const { user, isAuthenticated, loading } = useAuth()

  if (loading) return <FullScreenSpinner />
  if (!isAuthenticated) return <Navigate to="/login" replace />

  if (user?.rol === 'responsable') {
    return <Navigate to="/app/responsable/configuracion" replace />
  }

  return <Navigate to={ROLE_ROUTES[user!.rol]} replace />
}

// ── Spinner de pantalla completa (inline styles para evitar
//    dependencia de Tailwind durante carga inicial) ──────────────
function FullScreenSpinner() {
  return (
    <div style={{
      minHeight: '100vh',
      background: '#0f172a',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 12,
    }}>
      <div style={{
        width: 40,
        height: 40,
        border: '2px solid #f97316',
        borderTopColor: 'transparent',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite',
      }} />
      <span style={{ color: '#94a3b8', fontSize: 14, fontFamily: 'Nunito, sans-serif' }}>
        Cargando...
      </span>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
