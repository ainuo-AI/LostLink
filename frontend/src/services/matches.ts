// 文档对照：03_LostLink软件需求规格说明书.docx；图表编号以当前文档为准。
// 设计文档对照：04_LostLink软件设计规格说明书.docx；以下“设计文档对应”使用该文档图表编号。
/** 匹配通知 API 适配模块。
 *
 * 后端保存通知、已读和反馈状态；本模块把 snake_case 响应转换为现有页面使用的
 * 驼峰展示模型，使通知页无需了解 HTTP 或数据库字段。
 */

import { requestJson, resolveApiUrl } from '../api/client'
import type { ApiItem } from '../types/item'
import type { MatchDimension, MatchItem, MatchNotification, MatchStatus } from '../types/demo'

interface ApiMatchNotification {
  id: number
  title: string
  summary: string
  created_at: string
  is_read: boolean
  status: MatchStatus
  mine: ApiItem
  candidate: ApiItem
  score: number
  dimensions: MatchDimension[]
  rejection_reason: string | null
  rejection_note: string | null
}

interface ApiMatchList {
  items: ApiMatchNotification[]
  page: number
  page_size: number
  total: number
  unread: number
}

const categoryIcons: Record<string, string> = {
  箱包: '🎒', 卡证: '🪪', 数码: '🎧', 文具: '🖊️', 服饰: '🧥', 书籍: '📘',
}

/** 把公开物品响应转换为通知详情已有的对比卡片结构。 */
function toMatchItem(item: ApiItem): MatchItem {
  return {
    title: item.title,
    category: item.category,
    description: item.description,
    campus: item.campus,
    location: item.location,
    occurredAt: item.occurred_at,
    icon: categoryIcons[item.category] ?? '📦',
    imageId: item.image_urls?.[0] ? resolveApiUrl(item.image_urls[0]) : undefined,
  }
}

/** 转换通知字段名，同时保留后端给出的解释维度。 */
function toNotification(item: ApiMatchNotification): MatchNotification {
  return {
    id: String(item.id),
    title: item.title,
    summary: item.summary,
    createdAt: item.created_at,
    read: item.is_read,
    status: item.status,
    mine: toMatchItem(item.mine),
    candidate: toMatchItem(item.candidate),
    score: item.score,
    dimensions: item.dimensions,
    rejectionReason: item.rejection_reason ?? undefined,
    rejectionNote: item.rejection_note ?? undefined,
  }
}

/** 按后端时间顺序读取当前用户的全部匹配通知。 */
// 文档对应：图2-2-6 通知列表的前端API适配；2.2.6、2.2.7节。
// 设计文档对应：图3-2-5 读取通知列表并转换为界面展示模型。
export async function listMatchNotifications(): Promise<MatchNotification[]> {
  const response = await requestJson<ApiMatchList>(
    '/api/v1/notifications?page=1&page_size=100',
    {},
    { authenticated: true },
  )
  return response.items.map(toNotification)
}

/** 读取一条属于当前用户的匹配通知。 */
// 文档对应：图2-2-6、图2-2-7 候选详情的前端API适配；2.2.6、2.2.7节。
// 设计文档对应：图3-2-6 读取候选双方物品、分数和维度解释。
export async function getMatchNotification(id: string): Promise<MatchNotification | null> {
  const numericId = Number(id)
  if (!Number.isSafeInteger(numericId) || numericId < 1) return null
  return toNotification(await requestJson<ApiMatchNotification>(
    `/api/v1/matches/${numericId}`,
    {},
    { authenticated: true },
  ))
}

/** 标记一条通知已读，不改变反馈状态。 */
// 文档对应：图2-2-6 标记已读的前端API适配；2.2.6、2.2.7节。
// 设计文档对应：图3-2-5、图3-2-6 只更新已读状态，不改变确认或拒绝结论。
export async function markMatchRead(id: string): Promise<MatchNotification> {
  const response = await requestJson<ApiMatchNotification>(
    `/api/v1/notifications/${Number(id)}/read`,
    { method: 'PATCH' },
    { authenticated: true },
  )
  return toNotification(response)
}

/** 后端当前提供单条已读接口，因此批量操作会并发更新未读通知。 */
// 设计文档对应：图3-2-5 全部已读由多个单条请求组成。
export async function markAllMatchesRead(): Promise<void> {
  const matches = await listMatchNotifications()
  await Promise.all(matches.filter(item => !item.read).map(item => markMatchRead(item.id)))
}

/** 保存确认或拒绝反馈；重复处理由后端状态机拒绝。 */
// 文档对应：图2-2-7 确认或拒绝的前端API适配；2.2.6、2.2.7节。
// 设计文档对应：图4-1-8 提交接收者对候选的确认或拒绝。
export async function decideMatch(
  id: string,
  decision: Exclude<MatchStatus, 'pending'>,
  reason = '',
  note = '',
): Promise<MatchNotification> {
  const response = await requestJson<ApiMatchNotification>(
    `/api/v1/matches/${Number(id)}/feedback`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        status: decision,
        reason: reason.trim() || null,
        note: note.trim() || null,
      }),
    },
    { authenticated: true },
  )
  return toNotification(response)
}

/** 兼容旧页面导出；真实通知不能由客户端重置。 */
export async function resetMatchDemo(): Promise<MatchNotification[]> {
  return listMatchNotifications()
}
