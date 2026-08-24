import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { TelegramLoginButton } from '../auth/TelegramLoginButton'
import { ErrorBanner } from '../components/ui'
import type { TelegramLoginPayload } from '../api/types'

export function Login() {
  const { user, loading, login } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<unknown>(null)

  if (loading) return null
  if (user) return <Navigate to="/" replace />

  async function handleAuth(payload: TelegramLoginPayload) {
    setError(null)
    try {
      await login(payload)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <span className="login-mark" />
        <h1>Jovis</h1>
        <p>Entre com sua conta do Telegram pra ver sua grade, atividades, faltas e notas.</p>
        <TelegramLoginButton onAuth={handleAuth} />
        <ErrorBanner error={error} />
      </div>
    </div>
  )
}
