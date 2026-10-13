// 文档对照：03_LostLink软件需求规格说明书.docx；图表编号以当前文档为准。
/** 举报 API 适配模块。
 *
 * 页面仍使用原有 ReportCreate/LocalReport 类型，本模块负责把 item_id 放进资源路径，
 * 并通过统一 HTTP 客户端附加当前登录会话。
 */

import { requestJson } from '../api/client'
import type { LocalReport, ReportCreate } from '../types/report'

/** 向服务端提交举报，返回可用于成功页展示的举报记录。 */
// 文档对应：图2-2-8 举报请求适配；函数保留旧名称，实际提交至后端；2.2.8节。
export function createLocalReport(payload: ReportCreate): Promise<LocalReport> {
  return requestJson<LocalReport>(`/api/v1/items/${payload.item_id}/reports`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason: payload.reason, description: payload.description }),
  }, { authenticated: true })
}
