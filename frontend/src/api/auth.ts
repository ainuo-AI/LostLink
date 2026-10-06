/** 用户注册、登录和当前会话 API。 */
import type { AuthUser, LoginPayload, LoginResponse, RegisterPayload } from '../types/auth'
import { requestJson } from './client'

const jsonHeaders = { 'Content-Type': 'application/json' }

/** 创建本地校园账号；注册成功不会自动签发会话。 */
export function registerAccount(payload: RegisterPayload): Promise<AuthUser> {
  return requestJson<AuthUser>('/api/v1/auth/register', {
    method: 'POST',
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  })
}

/** 验证账号密码并换取 Bearer 会话。 */
export function loginAccount(payload: LoginPayload): Promise<LoginResponse> {
  return requestJson<LoginResponse>('/api/v1/auth/login', {
    method: 'POST',
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  })
}

/** 使用当前会话读取用户摘要，也用于页面刷新后的会话有效性确认。 */
export function fetchCurrentUser(): Promise<AuthUser> {
  return requestJson<AuthUser>('/api/v1/users/me', {}, { authenticated: true })
}

/** 吊销当前标签页持有的服务端会话。 */
export function logoutAccount(): Promise<void> {
  return requestJson<void>('/api/v1/auth/logout', { method: 'POST' }, { authenticated: true })
}
