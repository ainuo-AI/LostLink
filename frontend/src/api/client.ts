/** 通用 HTTP 客户端。
 *
 * 这个模块集中处理服务地址、JSON 解析和统一错误响应，页面组件不直接调用 fetch。
 */

import { getAccessToken } from '../stores/authToken'

interface ApiErrorPayload {
  code?: string
  message?: string
  details?: unknown
  request_id?: string
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details: unknown
  readonly requestId?: string

  constructor(status: number, payload: ApiErrorPayload = {}) {
    super(payload.message ?? '服务请求失败')
    this.name = 'ApiError'
    this.status = status
    this.code = payload.code ?? 'HTTP_ERROR'
    this.details = payload.details
    this.requestId = payload.request_id
  }
}

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
const apiBaseUrl = configuredBaseUrl.endsWith('/') ? configuredBaseUrl : `${configuredBaseUrl}/`

/** 把后端返回的相对资源路径转换为浏览器可直接使用的绝对地址。 */
export function resolveApiUrl(path: string): string {
  return new URL(path.replace(/^\//, ''), apiBaseUrl).toString()
}

export interface RequestOptions {
  /** 为受保护接口自动附加当前 Bearer 会话。 */
  authenticated?: boolean
}

/** 请求 JSON 接口，并把非成功响应转换为页面可识别的 ApiError。 */
export async function requestJson<T>(
  path: string,
  init: RequestInit = {},
  options: RequestOptions = {},
): Promise<T> {
  const url = new URL(path.replace(/^\//, ''), apiBaseUrl)
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')
  if (options.authenticated) {
    const token = getAccessToken()
    if (token) headers.set('Authorization', `Bearer ${token}`)
  }
  const response = await fetch(url, {
    ...init,
    headers,
  })

  if (!response.ok) {
    let payload: ApiErrorPayload = {}
    try {
      payload = await response.json() as ApiErrorPayload
    } catch {
      // 非 JSON 错误仍转换为统一异常，避免解析失败覆盖原始 HTTP 状态。
    }
    throw new ApiError(response.status, payload)
  }

  // 注销接口返回 204，没有 JSON 响应体。
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}
