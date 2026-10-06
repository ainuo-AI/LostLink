/** 用户认证模块的前端类型，与 FastAPI 的公开响应契约保持一致。 */

export type UserRole = 'user' | 'admin'
export type UserStatus = 'active' | 'restricted'

/** 已登录用户的安全摘要；响应中不会包含密码或会话摘要。 */
export interface AuthUser {
  id: number
  account: string
  display_name: string | null
  role: UserRole
  status: UserStatus
  campus_verified: boolean
  created_at: string
}

/** 登录成功后由后端签发的 Bearer 会话。 */
export interface LoginResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  user: AuthUser
}

export interface RegisterPayload {
  account: string
  password: string
  display_name?: string
}

export interface LoginPayload {
  account: string
  password: string
}
