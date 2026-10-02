/** 纯前端举报记录存储。
 *
 * 这里让课程演示可以完成“填写 -> 提交 -> 成功”的闭环，但不会请求或修改后端。
 * 后续后端提供举报接口后，可把本函数替换成 POST /api/v1/reports。
 */

import type { LocalReport, ReportCreate } from '../types/report'

const REPORTS_KEY = 'lostlink:reports'

/** 读取以前的本地举报；没有记录或 JSON 无法解析时返回空数组。 */
function readReports(): LocalReport[] {
  try {
    const raw = window.localStorage.getItem(REPORTS_KEY)
    return raw ? JSON.parse(raw) as LocalReport[] : []
  } catch {
    return []
  }
}

/** 功能对应：点击“提交举报”后把记录保存在当前浏览器。 */
export async function createLocalReport(payload: ReportCreate): Promise<LocalReport> {
  const reports = readReports()
  // 纯前端阶段用现有最大编号加一，正式后端应改为服务端生成不可冲突的 ID。
  const report: LocalReport = {
    id: reports.reduce((maxId, current) => Math.max(maxId, current.id), 0) + 1,
    item_id: payload.item_id,
    reason: payload.reason,
    description: payload.description,
    status: 'pending',
    created_at: new Date().toISOString(),
  }

  try {
    window.localStorage.setItem(REPORTS_KEY, JSON.stringify([...reports, report]))
  } catch {
    // 即使浏览器禁用存储，也返回本次演示结果，不让页面无响应。
  }
  return report
}
