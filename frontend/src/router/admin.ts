export const adminSections = [
  { id: 'overview', label: '数据概览' },
  { id: 'reports', label: '举报审核' },
  { id: 'users', label: '用户管理' },
  { id: 'audit', label: '审计日志' },
  { id: 'calibration', label: '匹配校准' },
] as const

export type AdminSection = typeof adminSections[number]['id']

export function isAdminPath(hash: string) {
  return hash === '#/admin' || hash.startsWith('#/admin/')
}

export function isAdminPreviewPath(hash: string) {
  return hash === '#/admin-preview' || hash.startsWith('#/admin-preview/')
}

export function readAdminSection(hash: string): AdminSection {
  return adminSections.find(section => section.id === hash.split('/')[2])?.id ?? 'overview'
}
