/**
 * 举报模块的前后端接口类型
 *
 * 类型文件只描述数据形状，不负责校验、界面或存储，供页面和 store 共同引用。
 */

export type ReportReason =
  | 'inaccurate'
  | 'duplicate'
  | 'spam'
  | 'inappropriate'
  | 'fraud'
  | 'other'

export type ReportStatus = 'pending' | 'resolved' | 'rejected'

/** 举报提交页整理出的表单结构。 */
export interface ReportCreate {
  item_id: number
  reason: ReportReason
  description: string
}

/** 服务端创建后返回的举报记录摘要。 */
export interface LocalReport {
  id: number
  item_id: number
  reason: ReportReason
  description: string
  status: ReportStatus
  created_at: string
}
