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
  image_urls?: string[]
}

/** FastAPI 列表接口的分页响应。 */
export interface ApiItemListResponse {
  items: ApiItem[]
  page: number
  page_size: number
  total: number
}

export type StorageMethod = 'self' | 'office'

/** 发布者视图包含管理所需的私密字段，只能由受保护接口返回。 */
export interface ApiOwnerItem extends ApiItem {
  owner_id: number
  contact: string
  contact_note: string | null
  storage_method: StorageMethod | null
  storage_location: string | null
  contact_window: string | null
  closure_reason: string | null
  closed_at: string | null
  created_at: string
  updated_at: string
}

export interface ApiOwnerItemListResponse {
  items: ApiOwnerItem[]
  page: number
  page_size: number
  total: number
}

/** 创建接口字段；owner_id 和状态始终由服务端决定。 */
export interface CreateItemPayload {
  type: RecordType
  category: string
  title: string
  description: string
  location: string
  campus: Campus
  area: CampusArea | null
  occurred_at: string
  contact: string
  contact_note: string | null
  storage_method: StorageMethod | null
  storage_location: string | null
  contact_window: string | null
  image_ids: string[]
}

export type UpdateItemPayload = Partial<Omit<CreateItemPayload, 'type'>>

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
  imageUrls: string[]
}
