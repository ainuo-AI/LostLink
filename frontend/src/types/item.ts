/** 失物与拾物模块的 API 类型和页面展示类型。 */

export type RecordType = 'lost' | 'found'
export type Campus = '东丽校区' | '宁河校区'
export type CampusArea = '北区' | '南区'
export type ItemStatus = 'active' | 'recovered' | 'returned' | 'closed'

/** FastAPI 返回的原始记录，字段名与 OpenAPI 契约保持一致。 */
export interface ApiItem {
  id: number
  type: RecordType
  category: string
  title: string
  description: string
  location: string
  campus: Campus
  area: CampusArea | null
  occurred_at: string
  status: ItemStatus
  contact_hint: string
}

/** FastAPI 列表接口的分页响应。 */
export interface ApiItemListResponse {
  items: ApiItem[]
  page: number
  page_size: number
  total: number
}

/** 页面组件使用的驼峰命名和展示增强数据。 */
export interface LostFoundItem {
  id: number
  type: RecordType
  category: string
  title: string
  description: string
  location: string
  campus: Campus
  area: CampusArea | ''
  occurredAt: string
  displayTime: string
  status: ItemStatus
  icon: string
  color: string
  contactHint: string
}
