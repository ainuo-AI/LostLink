// 文档对照：03_LostLink软件需求规格说明书.docx；图表编号以当前文档为准。
/** 管理控制台 API 契约与访问函数。
 *
 * 所有函数都使用管理员 Bearer 会话；后端仍会再次验证角色，前端路由守卫只用于
 * 改善导航体验，不能替代服务端授权。
 */

import { requestJson } from './client'
import type { AuthUser, UserStatus } from '../types/auth'

export type ReportStatus = 'pending' | 'dismissed' | 'resolved' | 'content_hidden'
export type CalibrationStatus = 'draft' | 'approved' | 'active' | 'rejected' | 'archived'

export interface AdminOverview {
  users_total: number
  users_restricted: number
  items_total: number
  items_active: number
  reports_pending: number
  notifications_unread: number
}

export interface AdminReport {
  id: number
  item_id: number
  reporter_id: number
  reason: string
  description: string | null
  status: ReportStatus
  resolution_note: string | null
  handled_by_id: number | null
  handled_at: string | null
  created_at: string
  updated_at: string
}

export interface AuditLog {
  id: number
  actor_id: number
  action: string
  object_type: string
  object_id: string
  reason: string
  details: Record<string, unknown> | null
  created_at: string
}

export interface CalibrationTask {
  id: number
  category: string | null
  range_start: string
  range_end: string
  status: string
  candidate_version_id: number | null
  result_metrics: Record<string, number> | null
}

export interface CalibrationVersion {
  id: number
  version_key: string
  status: CalibrationStatus
  weights: Record<string, number>
  metrics: Record<string, number>
  review_reason: string | null
  created_at: string
}

interface Page<T> { items: T[]; total: number; page: number; page_size: number }
const jsonHeaders = { 'Content-Type': 'application/json' }
const authenticated = { authenticated: true } as const

// 文档对应：图2-2-9b 管理概览请求的前端API适配；2.2.9节。
export function fetchAdminOverview(): Promise<AdminOverview> {
  return requestJson('/api/v1/admin/overview', {}, authenticated)
}

// 文档对应：图2-2-9 处理前读取举报列表；2.2.9节。
export function fetchAdminReports(status?: ReportStatus): Promise<Page<AdminReport>> {
  const query = status ? `?status=${status}` : ''
  return requestJson(`/api/v1/admin/reports${query}`, {}, authenticated)
}

// 文档对应：图2-2-9 举报结案请求的前端API适配；2.2.9节。
export function resolveAdminReport(
  id: number,
  status: Exclude<ReportStatus, 'pending'>,
  resolutionNote: string,
): Promise<AdminReport> {
  return requestJson(`/api/v1/admin/reports/${id}`, {
    method: 'PATCH', headers: jsonHeaders,
    body: JSON.stringify({ status, resolution_note: resolutionNote }),
  }, authenticated)
}

// 文档对应：图2-2-9a 管理前读取用户列表；2.2.9节。
export function fetchAdminUsers(keyword = '', status?: UserStatus): Promise<Page<AuthUser>> {
  const params = new URLSearchParams()
  if (keyword.trim()) params.set('keyword', keyword.trim())
  if (status) params.set('status', status)
  return requestJson(`/api/v1/admin/users?${params}`, {}, authenticated)
}

// 文档对应：图2-2-9a 用户状态请求的前端API适配；2.2.9节。
export function updateAdminUserStatus(
  id: number,
  status: UserStatus,
  reason: string,
): Promise<AuthUser> {
  return requestJson(`/api/v1/admin/users/${id}/status`, {
    method: 'PATCH', headers: jsonHeaders, body: JSON.stringify({ status, reason }),
  }, authenticated)
}

// 文档对应：图2-2-9c 审计请求的前端API适配；2.2.9节。
export function fetchAuditLogs(): Promise<Page<AuditLog>> {
  return requestJson('/api/v1/admin/audit', {}, authenticated)
}

// 文档范围：校准任务和版本管理未纳入当前需求规格说明书；此处保留已有实现，不关联当前图表。
export function fetchCalibrationTasks(): Promise<CalibrationTask[]> {
  return requestJson('/api/v1/admin/calibration/tasks', {}, authenticated)
}

// 文档范围：校准任务和版本管理未纳入当前需求规格说明书；此处保留已有实现，不关联当前图表。
export function createCalibrationTask(payload: {
  category: string | null
  range_start: string
  range_end: string
}): Promise<CalibrationTask> {
  return requestJson('/api/v1/admin/calibration/tasks', {
    method: 'POST', headers: jsonHeaders, body: JSON.stringify(payload),
  }, authenticated)
}

// 文档范围：校准任务和版本管理未纳入当前需求规格说明书；此处保留已有实现，不关联当前图表。
export function fetchCalibrationVersions(): Promise<CalibrationVersion[]> {
  return requestJson('/api/v1/admin/calibration/versions', {}, authenticated)
}

// 文档范围：校准任务和版本管理未纳入当前需求规格说明书；此处保留已有实现，不关联当前图表。
export function changeCalibrationVersion(
  id: number,
  action: 'approve' | 'reject' | 'activate' | 'rollback',
  reason: string,
): Promise<CalibrationVersion> {
  return requestJson(`/api/v1/admin/calibration/versions/${id}`, {
    method: 'PATCH', headers: jsonHeaders, body: JSON.stringify({ action, reason }),
  }, authenticated)
}
