/** 认证 API 客户端测试，确保敏感操作使用约定的方法、路径和 JSON 字段。 */
import { afterEach, describe, expect, it, vi } from 'vitest'
import { fetchCurrentUser, loginAccount, logoutAccount, registerAccount } from './auth'

afterEach(() => vi.unstubAllGlobals())

function jsonResponse(body: unknown, status = 200) {
  return new Response(status === 204 ? null : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('auth api', () => {
  it('注册和登录只发送公开契约字段', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ id: 1, account: '20260001' }, 201))
      .mockResolvedValueOnce(jsonResponse({ access_token: 'token', token_type: 'bearer', expires_in: 60, user: { id: 1 } }))
    vi.stubGlobal('fetch', fetchMock)

    await registerAccount({ account: '20260001', password: 'password-123' })
    await loginAccount({ account: '20260001', password: 'password-123' })

    expect(new URL(fetchMock.mock.calls[0][0]).pathname).toBe('/api/v1/auth/register')
    expect(fetchMock.mock.calls[0][1]).toMatchObject({ method: 'POST' })
    expect(JSON.parse(fetchMock.mock.calls[1][1].body)).toEqual({ account: '20260001', password: 'password-123' })
  })

  it('当前用户与注销请求携带 Bearer 会话', async () => {
    const storage = new Map<string, string>()
    storage.set('lostlink.auth.session.v1', JSON.stringify({
      accessToken: 'session-token', expiresAt: Date.now() + 60_000, user: { id: 1 },
    }))
    vi.stubGlobal('window', {
      sessionStorage: {
        getItem: (key: string) => storage.get(key) ?? null,
        setItem: (key: string, value: string) => storage.set(key, value),
        removeItem: (key: string) => storage.delete(key),
      },
    })
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ id: 1, account: '20260001' }))
      .mockResolvedValueOnce(jsonResponse(null, 204))
    vi.stubGlobal('fetch', fetchMock)

    await fetchCurrentUser()
    await logoutAccount()

    for (const call of fetchMock.mock.calls) {
      expect(new Headers(call[1].headers).get('Authorization')).toBe('Bearer session-token')
    }
    expect(fetchMock.mock.calls[1][1]).toMatchObject({ method: 'POST' })
  })
})
