// 用联合类型限制记录只能是“失物”或“拾物”，避免拼写错误。
export type RecordType = 'lost' | 'found'

// 校区使用固定枚举值，便于前后端统一地点字段。
export type Campus = '东丽校区' | '宁河校区'
export type CampusArea = '北区' | '南区' | ''

// 失物/拾物卡片的统一数据结构。
// 后续接入 FastAPI 时，后端响应可直接转换为该类型。
export interface LostFoundItem {
  id: number
  type: RecordType
  category: string
  title: string
  description: string
  location: string
  campus: Campus
  // 只有东丽校区继续区分北区和南区；宁河校区使用空字符串。
  area: CampusArea
  displayTime: string
  daysAgo: number
  icon: string
  color: string
  contactHint: string
}
