export const adminSections = [
  { id: 'overview', label: '数据概览' },
  { id: 'reports', label: '举报审核' },
  { id: 'users', label: '用户管理' },
  { id: 'audit', label: '审计日志' },
  { id: 'calibration', label: '匹配校准' },
] as const

export type AdminSection = typeof adminSections[number]['id']

/** 将 URL 参数限制为已知管理栏目，未知值安全回退到概览页。 */
export function readAdminSection(value: unknown): AdminSection {
  const sectionValue = Array.isArray(value) ? value[0] : value
  return adminSections.find(section => section.id === sectionValue)?.id ?? 'overview'
}
