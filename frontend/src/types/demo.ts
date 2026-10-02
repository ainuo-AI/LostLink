import type { Campus, CampusArea, RecordType } from './item'

/** 前端演示统一使用首页已有的物品分类，避免各页面出现不同枚举。 */
export const ITEM_CATEGORIES = ['箱包', '卡证', '数码', '文具', '服饰', '书籍', '其他'] as const
export type ItemCategory = typeof ITEM_CATEGORIES[number]
export type StorageMethod = 'self' | 'office'

/** 两个发布页面共用结构，但每种类型分别使用自己的草稿键。 */
export interface ItemDraft {
  title: string
  category: ItemCategory | ''
  campus: Campus | ''
  area: CampusArea | ''
  location: string
  occurredAt: string
  description: string
  contact: string
  contactNote: string
  storageMethod: StorageMethod | ''
  storageLocation: string
  contactWindow: string
  imageIds: string[]
}

export type DraftField = keyof ItemDraft
export type DraftErrors = Partial<Record<DraftField, string>>

/** 提交后写入 localStorage 的公开演示摘要，不保存完整联系方式。 */
export interface LocalItemRecord {
  id: string
  type: RecordType
  title: string
  category: ItemCategory
  campus: Campus
  area: CampusArea | ''
  location: string
  occurredAt: string
  description: string
  contactMasked: string
  contactNote: string
  storageMethod?: StorageMethod
  storageLocation?: string
  contactWindow?: string
  imageIds: string[]
  status: 'pending-match'
  createdAt: string
}

/** 匹配详情左右两侧共用的物品展示结构。 */
export interface MatchItem {
  title: string
  category: string
  description: string
  campus: string
  location: string
  occurredAt: string
  icon: string
  imageId?: string
}

export type MatchStatus = 'pending' | 'confirmed' | 'rejected'

/** 每个维度保存模拟分数和解释；null 表示该维度因缺少数据未评估。 */
export interface MatchDimension {
  label: string
  score: number | null
  explanation: string
}

/** 通知的已读状态 read 与业务处理状态 status 分开维护。 */
export interface MatchNotification {
  id: string
  title: string
  summary: string
  createdAt: string
  read: boolean
  status: MatchStatus
  mine: MatchItem
  candidate: MatchItem
  score: number
  dimensions: MatchDimension[]
  rejectionReason?: string
  rejectionNote?: string
}
