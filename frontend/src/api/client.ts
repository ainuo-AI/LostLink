/** 通用 HTTP 客户端。
 *
 * 这个模块集中处理服务地址、JSON 解析和统一错误响应，页面组件不直接调用 fetch。
 */

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

/** 请求 JSON 接口，并把非成功响应转换为页面可识别的 ApiError。 */
export async function requestJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const url = new URL(path.replace(/^\//, ''), apiBaseUrl)
  const response = await fetch(url, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...init.headers,
    },
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

  return response.json() as Promise<T>
}
