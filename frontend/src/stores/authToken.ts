/**
 * Bearer 会话的浏览器存储边界。
 *
 * 使用 sessionStorage 让刷新后仍能恢复登录，同时在关闭标签页后自动清理；页面和
 * API 模块不直接拼接存储键，也不会把密码写入任何浏览器存储。
 */
import type { AuthUser } from '../types/auth'

const SESSION_KEY = 'lostlink.auth.session.v1'

export interface StoredAuthSession {
  accessToken: string
  expiresAt: number
  user: AuthUser
}

export function readStoredSession(): StoredAuthSession | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.sessionStorage.getItem(SESSION_KEY)
    if (!raw) return null
    const session = JSON.parse(raw) as StoredAuthSession
    if (!session.accessToken || !session.user || session.expiresAt <= Date.now()) {
      clearStoredSession()
      return null
    }
    return session
  } catch {
    clearStoredSession()
    return null
  }
}

export function writeStoredSession(session: StoredAuthSession): void {
  window.sessionStorage.setItem(SESSION_KEY, JSON.stringify(session))
}

export function clearStoredSession(): void {
  if (typeof window !== 'undefined') window.sessionStorage.removeItem(SESSION_KEY)
}

export function getAccessToken(): string | null {
  return readStoredSession()?.accessToken ?? null
}
