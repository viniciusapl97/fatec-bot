import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { UNAUTHORIZED_EVENT, clearToken, getToken, setToken } from '../api/client'
import { getMe, loginWithTelegram } from '../api/resources'
import type { TelegramLoginPayload, UserOut } from '../api/types'

interface AuthContextValue {
  user: UserOut | null
  loading: boolean
  login: (payload: TelegramLoginPayload) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    if (!getToken()) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      setUser(await getMe())
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshUser()
    const handleUnauthorized = () => setUser(null)
    window.addEventListener(UNAUTHORIZED_EVENT, handleUnauthorized)
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, handleUnauthorized)
  }, [refreshUser])

  const login = useCallback(
    async (payload: TelegramLoginPayload) => {
      const { access_token } = await loginWithTelegram(payload)
      setToken(access_token)
      await refreshUser()
    },
    [refreshUser],
  )

  const logout = useCallback(() => {
    clearToken()
    setUser(null)
  }, [])

  return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth deve ser usado dentro de <AuthProvider>')
  return ctx
}
