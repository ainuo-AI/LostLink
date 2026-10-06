/** 举报 API 适配模块。
 *
 * 页面仍使用原有 ReportCreate/LocalReport 类型，本模块负责把 item_id 放进资源路径，
 * 并通过统一 HTTP 客户端附加当前登录会话。
 */

import { requestJson } from '../api/client'
import type { LocalReport, ReportCreate } from '../types/report'

/** 向服务端提交举报，返回可用于成功页展示的举报记录。 */
export function createLocalReport(payload: ReportCreate): Promise<LocalReport> {
  return requestJson<LocalReport>(`/api/v1/items/${payload.item_id}/reports`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason: payload.reason, description: payload.description }),
  }, { authenticated: true })
}
