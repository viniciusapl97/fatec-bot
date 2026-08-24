import { useEffect, useRef } from 'react'
import type { TelegramLoginPayload } from '../api/types'

declare global {
  interface Window {
    onTelegramAuth?: (user: TelegramLoginPayload) => void
  }
}

interface Props {
  onAuth: (payload: TelegramLoginPayload) => void
}

// Injeta o widget oficial do Telegram (https://core.telegram.org/widgets/login).
// O widget chama window.onTelegramAuth com o payload assinado, que é
// repassado pro backend em POST /auth/telegram (ver api/routers/auth.py).
export function TelegramLoginButton({ onAuth }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const botUsername = import.meta.env.VITE_TELEGRAM_BOT_USERNAME
    window.onTelegramAuth = onAuth

    const container = containerRef.current
    if (container) container.innerHTML = ''

    const script = document.createElement('script')
    script.src = 'https://telegram.org/js/telegram-widget.js?22'
    script.async = true
    script.setAttribute('data-telegram-login', botUsername)
    script.setAttribute('data-size', 'large')
    script.setAttribute('data-onauth', 'onTelegramAuth(user)')
    script.setAttribute('data-request-access', 'write')
    container?.appendChild(script)

    return () => {
      delete window.onTelegramAuth
    }
  }, [onAuth])

  return <div ref={containerRef} />
}
