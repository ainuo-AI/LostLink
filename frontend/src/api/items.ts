/** 失物与拾物 API 访问及数据转换模块。 */

import type {
  ApiItem,
  ApiItemListResponse,
  ApiOwnerItem,
  ApiOwnerItemListResponse,
  Campus,
  CampusArea,
  ItemStatus,
  LostFoundItem,
  RecordType,
  CreateItemPayload,
  UpdateItemPayload,
} from '../types/item'
import { requestJson, resolveApiUrl } from './client'

export interface ItemListQuery {
  keyword?: string
  type?: RecordType
  category?: string
  campus?: Campus
  area?: CampusArea
  status?: ItemStatus
  days?: number
  page: number
  pageSize: number
}

const categoryVisuals: Record<string, { icon: string; color: string }> = {
  箱包: { icon: '🎒', color: '#2878a9' },
  卡证: { icon: '🪪', color: '#22a07a' },
  数码: { icon: '🎧', color: '#e79338' },
  文具: { icon: '🖊️', color: '#6c72b8' },
  服饰: { icon: '🧥', color: '#bf657b' },
  书籍: { icon: '📘', color: '#3e75ca' },
}

const fallbackVisual = { icon: '📦', color: '#5d8299' }

/** 把页面筛选条件转换为后端约定的查询参数。 */
export async function fetchItems(
  query: ItemListQuery,
  signal?: AbortSignal,
): Promise<ApiItemListResponse> {
  const params = new URLSearchParams({
    page: String(query.page),
    page_size: String(query.pageSize),
  })

  if (query.keyword) params.set('keyword', query.keyword)
  if (query.type) params.set('type', query.type)
  if (query.category) params.set('category', query.category)
  if (query.campus) params.set('campus', query.campus)
  if (query.area) params.set('area', query.area)
  if (query.status) params.set('status', query.status)
  if (query.days) params.set('days', String(query.days))

  return requestJson<ApiItemListResponse>(`/api/v1/items?${params.toString()}`, { signal })
}

const jsonHeaders = { 'Content-Type': 'application/json' }

/** 发布一条真实记录；所有者和初始状态由后端根据当前会话设置。 */
export function createItem(payload: CreateItemPayload): Promise<ApiOwnerItem> {
  return requestJson<ApiOwnerItem>('/api/v1/items', {
    method: 'POST',
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  }, { authenticated: true })
}

export interface MyItemQuery {
  type?: RecordType
  status?: ItemStatus
  page: number
  pageSize: number
}

/** 分页读取当前登录用户自己的记录和管理字段。 */
export function fetchMyItems(query: MyItemQuery): Promise<ApiOwnerItemListResponse> {
  const params = new URLSearchParams({
    page: String(query.page),
    page_size: String(query.pageSize),
  })
  if (query.type) params.set('type', query.type)
  if (query.status) params.set('status', query.status)
  return requestJson<ApiOwnerItemListResponse>(
    `/api/v1/users/me/items?${params.toString()}`,
    {},
    { authenticated: true },
  )
}

/** 编辑仍处于 active 状态的自有记录。 */
export function updateItem(itemId: number, payload: UpdateItemPayload): Promise<ApiOwnerItem> {
  return requestJson<ApiOwnerItem>(`/api/v1/items/${itemId}`, {
    method: 'PATCH',
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  }, { authenticated: true })
}

/** 将记录变更为与类型匹配的终态并附带可选原因。 */
export function updateItemStatus(
  itemId: number,
  status: ItemStatus,
  reason?: string,
): Promise<ApiOwnerItem> {
  return requestJson<ApiOwnerItem>(`/api/v1/items/${itemId}/status`, {
    method: 'PATCH',
    headers: jsonHeaders,
    body: JSON.stringify({ status, reason: reason?.trim() || null }),
  }, { authenticated: true })
}

/** 将带时区的 API 时间转换为适合首页阅读的中文时间。 */
export function formatDisplayTime(value: string, now = new Date()): string {
  const occurredAt = new Date(value)
  if (Number.isNaN(occurredAt.getTime())) return '时间未知'

  const currentDay = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const occurredDay = new Date(
    occurredAt.getFullYear(),
    occurredAt.getMonth(),
    occurredAt.getDate(),
  )
  const daysAgo = Math.round((currentDay.getTime() - occurredDay.getTime()) / 86_400_000)
  const time = new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(occurredAt)

  if (daysAgo === 0) return `今天 ${time}`
  if (daysAgo === 1) return `昨天 ${time}`

  return new Intl.DateTimeFormat('zh-CN', {
    month: 'long',
    day: 'numeric',
  }).format(occurredAt)
}

/** 把后端 snake_case 数据转换为组件使用的展示模型。 */
export function toLostFoundItem(item: ApiItem): LostFoundItem {
  const visual = categoryVisuals[item.category] ?? fallbackVisual
  return {
    id: item.id,
    type: item.type,
    category: item.category,
    title: item.title,
    description: item.description,
    location: item.location,
    campus: item.campus,
    area: item.area ?? '',
    occurredAt: item.occurred_at,
    displayTime: formatDisplayTime(item.occurred_at),
    status: item.status,
    icon: visual.icon,
    color: visual.color,
    contactHint: item.contact_hint,
    imageUrls: (item.image_urls ?? []).map(resolveApiUrl),
  }
}
