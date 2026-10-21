// 文档对照：03_LostLink软件需求规格说明书.docx；图表编号以当前文档为准。
// 设计文档对照：04_LostLink软件设计规格说明书.docx；以下“设计文档对应”使用该文档图表编号。
/** 用户注册、登录和当前会话 API。 */
import type { AuthUser, LoginPayload, LoginResponse, RegisterPayload } from '../types/auth'
import { requestJson } from './client'

const jsonHeaders = { 'Content-Type': 'application/json' }

/** 创建本地校园账号；注册成功不会自动签发会话。 */
// 文档对应：图2-2-1a 注册请求的前端API适配；2.2.1节。
// 设计文档对应：图4-1-1 注册请求的 HTTP 适配。
export function registerAccount(payload: RegisterPayload): Promise<AuthUser> {
  return requestJson<AuthUser>('/api/v1/auth/register', {
    method: 'POST',
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  })
}

/** 验证账号密码并换取 Bearer 会话。 */
// 文档对应：图2-2-1 登录请求的前端API适配；2.2.1节。
// 设计文档对应：图4-1-2 登录凭据与会话响应的 HTTP 适配。
export function loginAccount(payload: LoginPayload): Promise<LoginResponse> {
  return requestJson<LoginResponse>('/api/v1/auth/login', {
    method: 'POST',
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  })
}

/** 使用当前会话读取用户摘要，也用于页面刷新后的会话有效性确认。 */
// 文档对应：图2-1 校园用户的身份恢复；表1-1 用户与会话。
// 设计文档对应：图3-3-1、图3-3-2 受保护页面恢复当前用户身份。
export function fetchCurrentUser(): Promise<AuthUser> {
  return requestJson<AuthUser>('/api/v1/users/me', {}, { authenticated: true })
}

/** 吊销当前标签页持有的服务端会话。 */
// 文档对应：图2-2-1b 退出请求的前端API适配；2.2.1节。
// 设计文档对应：图3-2-7 个人中心退出时吊销当前会话。
export function logoutAccount(): Promise<void> {
  return requestJson<void>('/api/v1/auth/logout', { method: 'POST' }, { authenticated: true })
}
