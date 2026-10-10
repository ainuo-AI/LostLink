<script setup lang="ts">
/**
 * 匹配通知列表页
 *
 * 页面负责加载状态、双条件筛选、未读计数和分页式“加载更多”；
 * 具体持久化交给 matches API 服务，避免组件直接操作 HTTP 或会话令牌。
 */
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import SiteHeader from '../components/SiteHeader.vue'
import { listMatchNotifications, markAllMatchesRead, markMatchRead, resetMatchDemo } from '../services/matches'
import type { MatchNotification, MatchStatus } from '../types/demo'

const router = useRouter()
const notifications = ref<MatchNotification[]>([])
const loading = ref(true)
const errorMessage = ref('')
const actionError = ref('')
const readFilter = ref<'all' | 'unread' | 'read'>('all')
const statusFilter = ref<'all' | MatchStatus>('all')
const visibleCount = ref(4)

// 未读状态和业务处理状态是两组独立条件，用户可以组合筛选。
const unreadCount = computed(() => notifications.value.filter((item) => !item.read).length)
const filtered = computed(() => notifications.value.filter((item) => {
  const matchesRead = readFilter.value === 'all' || (readFilter.value === 'read' ? item.read : !item.read)
  return matchesRead && (statusFilter.value === 'all' || item.status === statusFilter.value)
}))
const visible = computed(() => filtered.value.slice(0, visibleCount.value))

function formatTime(value: string) { return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) }
function statusText(status: MatchStatus) { return status === 'pending' ? '候选线索' : status === 'confirmed' ? '已处理' : '已拒绝' }

async function load() {
  loading.value = true
  errorMessage.value = ''
  try { notifications.value = await listMatchNotifications() }
  catch (error) { errorMessage.value = error instanceof Error ? error.message : '通知读取失败。' }
  finally { loading.value = false }
}

/** 读取失败时重新请求服务端通知。 */
async function resetDemo() {
  actionError.value = ''
  try { notifications.value = await resetMatchDemo(); errorMessage.value = ''; visibleCount.value = 4 }
  catch (error) { actionError.value = error instanceof Error ? error.message : '重置失败。' }
}

/** 标记后重新加载服务数据，让列表卡片和顶部未读数量同步更新。 */
async function readOne(id: string) {
  actionError.value = ''
  try { await markMatchRead(id); await load() }
  catch (error) { actionError.value = error instanceof Error ? error.message : '标记失败。' }
}

async function readAll() {
  actionError.value = ''
  try { await markAllMatchesRead(); await load() }
  catch (error) { actionError.value = error instanceof Error ? error.message : '标记失败。' }
}

/** 使用带 id 的子路由打开详情，刷新和浏览器前进后退都能恢复页面。 */
function openDetail(id: string) { void router.push({ name: 'match-detail', params: { id } }) }
function navigate(label: string) { if (label === '我的') window.alert('「我的」将在后续迭代中开放。') }
onMounted(() => { void load() })
</script>

<template>
  <div class="app-shell">
    <SiteHeader active-nav="匹配通知" @navigate="navigate" />
    <main class="notification-main">
      <header class="notification-heading"><div><p class="section-kicker">MATCH UPDATES</p><h1>匹配通知</h1><p>查看服务端生成的候选线索，直接联系对方或拒绝不符的匹配建议。分数只用于排序，不代表找回概率。</p></div><div class="unread-counter"><strong>{{ unreadCount }}</strong><span>条未读</span></div></header>
      <!-- 列表面板依次处理：加载、读取失败、空数据、筛选无结果、正常列表。 -->
      <section class="notification-panel" aria-labelledby="notification-list-title">
        <div class="notification-toolbar"><div><h2 id="notification-list-title">通知列表</h2><p>已读与匹配处理状态分别记录。</p></div><button class="secondary-button" type="button" :disabled="loading || unreadCount === 0" @click="readAll">全部标为已读</button></div>
        <div class="notification-filters"><div class="type-tabs" role="group" aria-label="已读状态"><button v-for="filter in [{ value: 'all', label: '全部' }, { value: 'unread', label: '未读' }, { value: 'read', label: '已读' }]" :key="filter.value" type="button" :class="{ active: readFilter === filter.value }" @click="readFilter = filter.value as typeof readFilter; visibleCount = 4">{{ filter.label }}</button></div><label for="match-status-filter">处理状态</label><select id="match-status-filter" v-model="statusFilter" @change="visibleCount = 4"><option value="all">全部状态</option><option value="pending">候选线索</option><option v-if="notifications.some(item => item.status === 'confirmed')" value="confirmed">已处理</option><option value="rejected">已拒绝</option></select></div>
        <p v-if="actionError" class="form-alert" role="alert">{{ actionError }}</p>
        <div v-if="loading" class="page-state notification-state" role="status"><span class="loading-spinner" aria-hidden="true"></span><p>正在读取通知…</p></div>
        <div v-else-if="errorMessage" class="page-state notification-state error-state" role="alert"><span class="state-icon" aria-hidden="true">!</span><h3>通知读取失败</h3><p>{{ errorMessage }}</p><div class="state-actions"><button class="secondary-button" type="button" @click="resetDemo">重新加载</button></div></div>
        <div v-else-if="notifications.length === 0" class="page-state notification-state"><h3>暂无通知</h3><p>有新的匹配线索时会显示在这里。</p></div>
        <div v-else-if="filtered.length === 0" class="page-state notification-state"><h3>当前筛选没有结果</h3><p>试试切换已读或处理状态。</p><button class="secondary-button" type="button" @click="readFilter = 'all'; statusFilter = 'all'">清除筛选</button></div>
        <template v-else><div class="notification-list"><article v-for="item in visible" :key="item.id" :class="['notification-card', { unread: !item.read }]"><div class="notification-thumb"><span aria-hidden="true">{{ item.candidate.icon }}</span><small>图片示意</small></div><div class="notification-content"><div class="notification-meta"><span v-if="!item.read" class="unread-dot">未读</span><span :class="['match-status', item.status]">{{ statusText(item.status) }}</span><time :datetime="item.createdAt">{{ formatTime(item.createdAt) }}</time></div><h3>{{ item.title }}</h3><p>{{ item.summary }}</p><p class="associated-item">关联物品：{{ item.mine.title }} ↔ {{ item.candidate.title }}</p><div class="notification-actions"><button class="primary-button" type="button" @click="openDetail(item.id)">查看匹配详情</button><button v-if="!item.read" class="text-button" type="button" @click="readOne(item.id)">标为已读</button></div></div></article></div><div v-if="visibleCount < filtered.length" class="load-more"><button class="secondary-button" type="button" @click="visibleCount += 4">加载更多（剩余 {{ filtered.length - visibleCount }} 条）</button></div></template>
      </section>
    </main>
  </div>
</template>
