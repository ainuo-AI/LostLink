/**
 * 全站认证状态。
 *
 * 本模块统一负责登录、会话恢复和注销，页面只消费状态与动作，避免各页面分别
 * 操作令牌。服务端仍是权限真相来源，前端路由守卫只改善交互体验。
 */
import { computed, ref } from 'vue'
import { fetchCurrentUser, loginAccount, logoutAccount } from '../api/auth'
import type { AuthUser, LoginPayload } from '../types/auth'
import { clearStoredSession, readStoredSession, writeStoredSession } from './authToken'

const initialSession = readStoredSession()
const user = ref<AuthUser | null>(initialSession?.user ?? null)
const initialized = ref(false)
let restorePromise: Promise<AuthUser | null> | null = null

function clearSession(): void {
  clearStoredSession()
  user.value = null
}

/** 登录并保存带绝对过期时间的会话；密码只存在于本次请求内。 */
async function login(payload: LoginPayload): Promise<AuthUser> {
  const response = await loginAccount(payload)
  const expiresAt = Date.now() + response.expires_in * 1000
  writeStoredSession({ accessToken: response.access_token, expiresAt, user: response.user })
  user.value = response.user
  initialized.value = true
  return response.user
}

/** 应用首次导航时向服务端确认缓存会话，失效会话会被静默清理。 */
async function restore(): Promise<AuthUser | null> {
  if (initialized.value) return user.value
  if (!readStoredSession()) {
    initialized.value = true
    user.value = null
    return null
  }
  if (!restorePromise) {
    restorePromise = fetchCurrentUser()
      .then((current) => {
        const stored = readStoredSession()
        if (stored) writeStoredSession({ ...stored, user: current })
        user.value = current
        return current
      })
      .catch(() => {
        clearSession()
        return null
      })
      .finally(() => {
        initialized.value = true
        restorePromise = null
      })
  }
  return restorePromise
}

/** 无论服务端注销是否成功，都清除本地会话，避免用户继续误认为已登录。 */
async function logout(): Promise<void> {
  try {
    if (readStoredSession()) await logoutAccount()
  } catch {
    // 网络中断时服务端令牌会按过期时间失效；本地仍必须立即退出。
  } finally {
    clearSession()
    initialized.value = true
  }
}

export function useAuth() {
  return {
    user,
    initialized,
    isAuthenticated: computed(() => Boolean(user.value)),
    login,
    restore,
    logout,
    clearSession,
  }
}
