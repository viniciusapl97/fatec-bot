import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, UNAUTHORIZED_EVENT, api, clearToken, getToken, setToken } from './client'

function mockFetchOnce(init: { ok: boolean; status: number; jsonBody?: unknown }) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: init.ok,
    status: init.status,
    json: async () => init.jsonBody,
  } as Response)
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('api client', () => {
  beforeEach(() => {
    clearToken()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('sends no Authorization header when there is no token', async () => {
    const fetchMock = mockFetchOnce({ ok: true, status: 200, jsonBody: {} })

    await api.get('/me')

    const headers = fetchMock.mock.calls[0][1].headers as Headers
    expect(headers.has('Authorization')).toBe(false)
  })

  it('attaches Authorization: Bearer <token> once a token is set', async () => {
    setToken('abc123')
    const fetchMock = mockFetchOnce({ ok: true, status: 200, jsonBody: {} })

    await api.get('/me')

    const headers = fetchMock.mock.calls[0][1].headers as Headers
    expect(headers.get('Authorization')).toBe('Bearer abc123')
  })

  it('clears the token and dispatches UNAUTHORIZED_EVENT on a 401', async () => {
    setToken('expired-token')
    mockFetchOnce({ ok: false, status: 401, jsonBody: { detail: 'Token de acesso inválido ou revogado.' } })
    const listener = vi.fn()
    window.addEventListener(UNAUTHORIZED_EVENT, listener)

    await expect(api.get('/me')).rejects.toThrow(ApiError)

    expect(getToken()).toBeNull()
    expect(listener).toHaveBeenCalledOnce()
    window.removeEventListener(UNAUTHORIZED_EVENT, listener)
  })

  it('throws an ApiError carrying the backend detail on other error statuses', async () => {
    mockFetchOnce({ ok: false, status: 409, jsonBody: { detail: 'Conflito de horário.' } })

    await expect(api.post('/subjects', {})).rejects.toMatchObject({
      status: 409,
      message: 'Conflito de horário.',
    })
  })

  it('falls back to a generic message when the error body has no detail', async () => {
    mockFetchOnce({ ok: false, status: 500 })

    await expect(api.get('/subjects')).rejects.toMatchObject({ status: 500, message: 'Erro 500' })
  })

  it('resolves to undefined for a 204 response instead of parsing a body', async () => {
    const fetchMock = mockFetchOnce({ ok: true, status: 204 })

    const result = await api.delete('/subjects/1')

    expect(result).toBeUndefined()
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/subjects/1'), expect.objectContaining({ method: 'DELETE' }))
  })
})
