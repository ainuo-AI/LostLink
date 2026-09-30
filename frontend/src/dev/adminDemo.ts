// 只用于管理端开发预览，不是 API 类型、权限或业务状态契约。
export interface DemoReport {
  id: string; object: string; reason: string; evidence: string; status: string; time: string
  history: { time: string; description: string }[]
}
export interface DemoUser { account: string; name: string; status: string; note: string }
export interface DemoAudit { id: string; operator: string; action: string; object: string; time: string; reason: string; result: string; before: string; after: string }
export interface DemoVersion { id: string; status: string; time: string; metricA: string; metricB: string }
export interface AdminDemoData {
  reports: DemoReport[]
  users: DemoUser[]
  audit: DemoAudit[]
  versions: DemoVersion[]
  statistics: { label: string; value: string }[]
  categories: string[]
}

export const adminDemoData: AdminDemoData = {
  statistics: [
    { label: '待处理举报', value: '12（演示）' }, { label: '已处理举报', value: '28（演示）' },
    { label: '受限用户', value: '3（演示）' }, { label: '评估任务', value: '2（演示）' },
  ],
  reports: Array.from({ length: 12 }, (_, index) => ({
    id: `DEMO-R-${index + 1}`, object: `【开发演示】物品 ${index + 1}`,
    reason: '演示举报原因：物品描述可能不准确。', evidence: '演示文字证据，不涉及真实用户材料。',
    status: index % 3 === 0 ? '已处理（演示）' : '待处理（演示）', time: '2026-09-30 09:00',
    history: index % 3 === 0 ? [{ time: '2026-09-30 10:00', description: '演示处理历史，仅用于查看布局，不代表执行过操作。' }] : [],
  })),
  users: Array.from({ length: 12 }, (_, index) => ({
    account: `demo-student-${String(index + 1).padStart(2, '0')}`, name: `演示用户 ${index + 1}`,
    status: index % 4 === 0 ? '受限（演示）' : '正常（演示）', note: '虚构账户，不对应真实身份或管理权限。',
  })),
  audit: Array.from({ length: 12 }, (_, index) => ({
    id: `DEMO-A-${index + 1}`, operator: `演示操作者 ${index % 2 + 1}`,
    action: index % 2 ? '举报处理（演示）' : '用户状态操作（演示）', object: `演示对象 ${index + 1}`,
    time: `2026-09-${index % 2 ? '30' : '29'} 10:00`, reason: '演示处理理由。', result: '演示结果，未执行真实操作',
    before: '演示前状态', after: '演示后状态',
  })),
  versions: [
    { id: 'DEMO-V-CURRENT', status: '当前版本样例', time: '2026-09-29 10:00', metricA: '0.80（演示）', metricB: '0.75（演示）' },
    { id: 'DEMO-V-CANDIDATE', status: '候选版本样例', time: '2026-09-30 10:00', metricA: '0.82（演示）', metricB: '0.78（演示）' },
    { id: 'DEMO-V-HISTORY', status: '历史版本样例', time: '2026-09-28 10:00', metricA: '0.76（演示）', metricB: '0.72（演示）' },
  ],
  categories: ['箱包（演示）', '数码（演示）'],
}
