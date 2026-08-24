import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { UNAUTHORIZED_EVENT, getToken, setToken } from '../api/client'
import * as resources from '../api/resources'
import type { UserOut } from '../api/types'
import { AuthProvider, useAuth } from './AuthContext'

vi.mock('../api/resources')

const ME: UserOut = { user_id: 1, first_name: 'Ana', username: 'ana', notifications_enabled: true, notification_hour: 9 }

function Consumer() {
  const { user, loading, login, logout } = useAuth()
  return (
    <div>
      <span data-testid="loading">{String(loading)}</span>
      <span data-testid="user">{user ? user.first_name : 'none'}</span>
      <button onClick={() => login({ id: 1, first_name: 'Ana', auth_date: 0, hash: 'x' })}>entrar</button>
      <button onClick={logout}>sair</button>
    </div>
  )
}

function renderConsumer() {
  return render(
    <AuthProvider>
      <Consumer />
    </AuthProvider>,
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.mocked(resources.getMe).mockReset()
    vi.mocked(resources.loginWithTelegram).mockReset()
  })

  it('starts with no user and stops loading when there is no stored token', async () => {
    renderConsumer()

    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('false'))
    expect(screen.getByTestId('user')).toHaveTextContent('none')
    expect(resources.getMe).not.toHaveBeenCalled()
  })

  it('fetches the user on mount when a token is already stored', async () => {
    setToken('existing-token')
    vi.mocked(resources.getMe).mockResolvedValue(ME)

    renderConsumer()

    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('Ana'))
    expect(resources.getMe).toHaveBeenCalledTimes(1)
  })

  it('clears the session when the stored token turns out to be invalid', async () => {
    setToken('stale-token')
    vi.mocked(resources.getMe).mockRejectedValue(new Error('401'))

    renderConsumer()

    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('false'))
    expect(screen.getByTestId('user')).toHaveTextContent('none')
  })

  it('login() stores the token from the Telegram payload and populates the user', async () => {
    const user = userEvent.setup()
    vi.mocked(resources.loginWithTelegram).mockResolvedValue({ access_token: 'new-token', token_type: 'bearer' })
    vi.mocked(resources.getMe).mockResolvedValue(ME)

    renderConsumer()
    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('false'))

    await user.click(screen.getByText('entrar'))

    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('Ana'))
    expect(getToken()).toBe('new-token')
  })

  it('logout() clears the token and the user', async () => {
    const user = userEvent.setup()
    setToken('existing-token')
    vi.mocked(resources.getMe).mockResolvedValue(ME)

    renderConsumer()
    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('Ana'))

    await user.click(screen.getByText('sair'))

    expect(getToken()).toBeNull()
    expect(screen.getByTestId('user')).toHaveTextContent('none')
  })

  it('clears the user when the API dispatches an unauthorized event', async () => {
    setToken('existing-token')
    vi.mocked(resources.getMe).mockResolvedValue(ME)

    renderConsumer()
    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('Ana'))

    window.dispatchEvent(new Event(UNAUTHORIZED_EVENT))

    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('none'))
  })
})
