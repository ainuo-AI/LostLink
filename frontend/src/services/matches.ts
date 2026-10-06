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
export async function listMatchNotifications(): Promise<MatchNotification[]> {
  const response = await requestJson<ApiMatchList>(
    '/api/v1/notifications?page=1&page_size=100',
    {},
    { authenticated: true },
  )
  return response.items.map(toNotification)
}

/** 读取一条属于当前用户的匹配通知。 */
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
export async function markMatchRead(id: string): Promise<MatchNotification> {
  const response = await requestJson<ApiMatchNotification>(
    `/api/v1/notifications/${Number(id)}/read`,
    { method: 'PATCH' },
    { authenticated: true },
  )
  return toNotification(response)
}

/** 后端当前提供单条已读接口，因此批量操作会并发更新未读通知。 */
export async function markAllMatchesRead(): Promise<void> {
  const matches = await listMatchNotifications()
  await Promise.all(matches.filter(item => !item.read).map(item => markMatchRead(item.id)))
}

/** 保存确认或拒绝反馈；重复处理由后端状态机拒绝。 */
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
