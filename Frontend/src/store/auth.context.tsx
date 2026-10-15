import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import type { AuthUser, LoginPayload, OTPRequiredResponse } from '@/types'
import { authService } from '@/services/auth.service'

interface AuthContextValue {
  user: AuthUser | null
  loading: boolean
  isAuthenticated: boolean
  login: (payload: LoginPayload) => Promise<OTPRequiredResponse>
  verifyOTP: (usuarioId: string, codigo: string) => Promise<AuthUser>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  // Al iniciar la app, intentamos restaurar la sesión desde localStorage
  useEffect(() => {
    let mounted = true
    const restoreSession = async () => {
      try {
        const cached = authService.getCurrentUser()
        if (cached) {
          if (mounted) {
            setUser(cached)
            setLoading(false)
          }
          authService.me().then(fresh => {
            if (mounted) {
              if (fresh) setUser(fresh)
              else {
                authService.logout()
                setUser(null)
              }
            }
          }).catch(() => {})
          return
        }
        const currentUser = await authService.me()
        if (mounted) setUser(currentUser)
      } catch {
        authService.logout()
        if (mounted) setUser(null)
      } finally {
        if (mounted) setLoading(false)
      }
    }

    restoreSession()
    return () => {
      mounted = false
    }
  }, [])

  const login = useCallback(async (payload: LoginPayload): Promise<OTPRequiredResponse> => {
    return authService.login(payload)
  }, [])

  const verifyOTP = useCallback(async (usuarioId: string, codigo: string): Promise<AuthUser> => {
    const user = await authService.verifyOTP(usuarioId, codigo)
    const freshUser = await authService.me()
    const finalUser = freshUser ?? user
    setUser(finalUser)
    return finalUser
  }, [])

  const logout = useCallback(() => {
    authService.logout()
    setUser(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      isAuthenticated: !!user,
      login,
      verifyOTP,
      logout,
    }),
    [user, loading, login, verifyOTP, logout]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth debe usarse dentro de AuthProvider')
  }

  return context
}