<script setup lang="ts">
/** 真实管理控制台。
 *
 * 该页面按当前栏目加载服务端数据，并提供举报结案、用户限制/恢复、校准任务和
 * 版本状态操作。每次写操作完成后重新读取对应列表，服务端始终是最终状态来源。
 */
import { ref, watch } from 'vue'
import AdminLayout from '../../layouts/AdminLayout.vue'
import { ApiError } from '../../api/client'
import {
  changeCalibrationVersion,
  createCalibrationTask,
  fetchAdminOverview,
  fetchAdminReports,
  fetchAdminUsers,
  fetchAuditLogs,
  fetchCalibrationTasks,
  fetchCalibrationVersions,
  resolveAdminReport,
  updateAdminUserStatus,
  type AdminOverview,
  type AdminReport,
  type AuditLog,
  type CalibrationTask,
  type CalibrationVersion,
  type ReportStatus,
} from '../../api/admin'
import type { AuthUser, UserStatus } from '../../types/auth'
import type { AdminSection } from '../../router/admin'
import '../../styles/admin.css'

const props = defineProps<{ section: AdminSection }>()
const loading = ref(false)
const errorMessage = ref('')
const overview = ref<AdminOverview | null>(null)
const reports = ref<AdminReport[]>([])
const users = ref<AuthUser[]>([])
const audits = ref<AuditLog[]>([])
const tasks = ref<CalibrationTask[]>([])
const versions = ref<CalibrationVersion[]>([])
const reportStatus = ref<'all' | ReportStatus>('all')
const userKeyword = ref('')
const userStatus = ref<'all' | UserStatus>('all')
const calibrationCategory = ref('')
const rangeStart = ref('')
const rangeEnd = ref('')

function message(error: unknown): string {
  return error instanceof ApiError ? error.message : '管理服务请求失败，请稍后重试。'
}

/** 根据导航栏目只请求当前页面需要的数据。 */
async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    if (props.section === 'overview') overview.value = await fetchAdminOverview()
    if (props.section === 'reports') {
      reports.value = (await fetchAdminReports(
        reportStatus.value === 'all' ? undefined : reportStatus.value,
      )).items
    }
    if (props.section === 'users') {
      users.value = (await fetchAdminUsers(
        userKeyword.value,
        userStatus.value === 'all' ? undefined : userStatus.value,
      )).items
    }
    if (props.section === 'audit') audits.value = (await fetchAuditLogs()).items
    if (props.section === 'calibration') {
      [tasks.value, versions.value] = await Promise.all([
        fetchCalibrationTasks(), fetchCalibrationVersions(),
      ])
    }
  } catch (error) {
    errorMessage.value = message(error)
  } finally {
    loading.value = false
  }
}

/** 要求管理员明确输入理由后处理举报。 */
async function handleReport(report: AdminReport, status: Exclude<ReportStatus, 'pending'>) {
  const reason = window.prompt('请输入处理理由（至少 2 个字）：')?.trim()
  if (!reason || reason.length < 2) return
  try {
    await resolveAdminReport(report.id, status, reason)
    await load()
  } catch (error) { errorMessage.value = message(error) }
}

/** 限制或恢复普通用户；后端会阻止修改管理员和自己的状态。 */
async function toggleUser(user: AuthUser) {
  const next: UserStatus = user.status === 'active' ? 'restricted' : 'active'
  const reason = window.prompt(`请输入${next === 'restricted' ? '限制' : '恢复'}理由：`)?.trim()
  if (!reason || reason.length < 2) return
  try {
    await updateAdminUserStatus(user.id, next, reason)
    await load()
  } catch (error) { errorMessage.value = message(error) }
}

/** 创建校准任务；当前后端同步完成评估并生成 draft 候选版本。 */
async function startCalibration() {
  if (!rangeStart.value || !rangeEnd.value) {
    errorMessage.value = '请选择完整的评估日期范围。'
    return
  }
  try {
    await createCalibrationTask({
      category: calibrationCategory.value.trim() || null,
      range_start: rangeStart.value,
      range_end: rangeEnd.value,
    })
    await load()
  } catch (error) { errorMessage.value = message(error) }
}

/** 执行版本审批、拒绝、启用或回滚，并立即刷新版本列表。 */
async function changeVersion(
  version: CalibrationVersion,
  action: 'approve' | 'reject' | 'activate' | 'rollback',
) {
  const reason = window.prompt('请输入操作理由：')?.trim()
  if (!reason || reason.length < 2) return
  try {
    await changeCalibrationVersion(version.id, action, reason)
    await load()
  } catch (error) { errorMessage.value = message(error) }
}

function formatTime(value: string | null): string {
  return value ? new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium', timeStyle: 'short',
  }).format(new Date(value)) : '—'
}

watch(() => props.section, () => { void load() }, { immediate: true })
</script>

<template>
  <AdminLayout :section="section">
    <div class="admin-page-heading">
      <p class="eyebrow">ADMIN</p>
      <h1 tabindex="-1">{{ section === 'overview' ? '数据概览' : section === 'reports' ? '举报审核' : section === 'users' ? '用户管理' : section === 'audit' ? '审计日志' : '匹配校准' }}</h1>
      <p>以下数据来自服务端，所有管理写操作都会记录操作人和理由。</p>
    </div>
    <p v-if="errorMessage" class="form-alert" role="alert">{{ errorMessage }}</p>
    <div v-if="loading" class="page-state" role="status"><span class="loading-spinner" aria-hidden="true"></span><p>正在加载管理数据…</p></div>

    <section v-else-if="section === 'overview' && overview" class="admin-metrics" aria-label="管理概览">
      <article v-for="metric in [
        ['用户总数', overview.users_total], ['受限用户', overview.users_restricted],
        ['物品总数', overview.items_total], ['进行中物品', overview.items_active],
        ['待处理举报', overview.reports_pending], ['未读匹配通知', overview.notifications_unread],
      ]" :key="String(metric[0])" class="admin-metric-card"><h2>{{ metric[0] }}</h2><strong>{{ metric[1] }}</strong><p>实时服务端统计</p></article>
    </section>

    <section v-else-if="section === 'reports'">
      <form class="admin-panel admin-filters" @submit.prevent="load">
        <div class="filter-group"><label for="report-status">处理状态</label><select id="report-status" v-model="reportStatus"><option value="all">全部</option><option value="pending">待处理</option><option value="dismissed">已驳回</option><option value="resolved">已解决</option><option value="content_hidden">内容已隐藏</option></select></div>
        <button class="primary-button" type="submit">筛选</button>
      </form>
      <div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>编号</th><th>物品</th><th>原因</th><th>说明</th><th>状态</th><th>提交时间</th><th>操作</th></tr></thead><tbody><tr v-for="report in reports" :key="report.id"><td>#{{ report.id }}</td><td>#{{ report.item_id }}</td><td>{{ report.reason }}</td><td>{{ report.description || '—' }}</td><td>{{ report.status }}</td><td>{{ formatTime(report.created_at) }}</td><td><template v-if="report.status === 'pending'"><button class="admin-inline-button" type="button" @click="handleReport(report, 'dismissed')">驳回</button> <button class="admin-inline-button" type="button" @click="handleReport(report, 'resolved')">解决</button> <button class="admin-inline-button" type="button" @click="handleReport(report, 'content_hidden')">隐藏内容</button></template><span v-else>{{ report.resolution_note }}</span></td></tr></tbody></table></div>
      <div v-if="!reports.length" class="admin-empty">暂无符合条件的举报。</div>
    </section>

    <section v-else-if="section === 'users'">
      <form class="admin-panel admin-filters" @submit.prevent="load"><div class="filter-group"><label for="user-keyword">账号或名称</label><input id="user-keyword" v-model="userKeyword" /></div><div class="filter-group"><label for="user-status">状态</label><select id="user-status" v-model="userStatus"><option value="all">全部</option><option value="active">正常</option><option value="restricted">受限</option></select></div><button class="primary-button" type="submit">查询</button></form>
      <div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>账号</th><th>显示名称</th><th>角色</th><th>状态</th><th>创建时间</th><th>操作</th></tr></thead><tbody><tr v-for="user in users" :key="user.id"><td>{{ user.account }}</td><td>{{ user.display_name || '—' }}</td><td>{{ user.role }}</td><td>{{ user.status }}</td><td>{{ formatTime(user.created_at) }}</td><td><button v-if="user.role !== 'admin'" class="admin-inline-button" type="button" @click="toggleUser(user)">{{ user.status === 'active' ? '限制' : '恢复' }}</button><span v-else>受保护</span></td></tr></tbody></table></div>
    </section>

    <section v-else-if="section === 'audit'">
      <p class="admin-write-note">审计日志为只读记录。</p>
      <div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>时间</th><th>操作者</th><th>动作</th><th>对象</th><th>理由</th></tr></thead><tbody><tr v-for="audit in audits" :key="audit.id"><td>{{ formatTime(audit.created_at) }}</td><td>#{{ audit.actor_id }}</td><td>{{ audit.action }}</td><td>{{ audit.object_type }} #{{ audit.object_id }}</td><td>{{ audit.reason }}</td></tr></tbody></table></div>
    </section>

    <section v-else>
      <form class="admin-panel admin-filters" @submit.prevent="startCalibration"><div class="filter-group"><label for="cal-category">类别（选填）</label><input id="cal-category" v-model="calibrationCategory" /></div><div class="filter-group"><label for="cal-start">开始日期</label><input id="cal-start" v-model="rangeStart" type="date" /></div><div class="filter-group"><label for="cal-end">结束日期</label><input id="cal-end" v-model="rangeEnd" type="date" /></div><button class="primary-button" type="submit">发起评估</button></form>
      <div class="admin-panel"><h2>版本</h2><div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>版本</th><th>状态</th><th>指标</th><th>操作</th></tr></thead><tbody><tr v-for="version in versions" :key="version.id"><td>{{ version.version_key }}</td><td>{{ version.status }}</td><td>F1 {{ version.metrics.f1 ?? '—' }}</td><td><button v-if="version.status === 'draft'" class="admin-inline-button" type="button" @click="changeVersion(version, 'approve')">批准</button> <button v-if="version.status === 'draft'" class="admin-inline-button" type="button" @click="changeVersion(version, 'reject')">拒绝</button> <button v-if="version.status === 'approved'" class="admin-inline-button" type="button" @click="changeVersion(version, 'activate')">启用</button> <button v-if="version.status === 'active'" class="admin-inline-button" type="button" @click="changeVersion(version, 'rollback')">回滚</button></td></tr></tbody></table></div></div>
      <div class="admin-panel"><h2>最近任务</h2><p v-for="task in tasks" :key="task.id">#{{ task.id }} · {{ task.category || '全部类别' }} · {{ task.range_start }} 至 {{ task.range_end }} · {{ task.status }}</p></div>
    </section>
  </AdminLayout>
</template>
