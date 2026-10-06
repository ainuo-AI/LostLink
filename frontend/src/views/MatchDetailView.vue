<script setup lang="ts">
/**
 * 匹配详情与反馈页面
 *
 * 根据 URL 中的通知 id 读取候选，展示双方字段和可解释维度分数；
 * 用户可确认或拒绝，结果通过 matches API 同步回通知列表。
 */
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SiteHeader from '../components/SiteHeader.vue'
import { decideMatch, getMatchNotification, markMatchRead } from '../services/matches'
import type { MatchItem, MatchNotification, MatchStatus } from '../types/demo'

const route = useRoute()
const router = useRouter()
const match = ref<MatchNotification | null>(null)
const loading = ref(true)
const busy = ref(false)
const errorMessage = ref('')
const actionError = ref('')
const rejectionReason = ref('')
const rejectionNote = ref('')
const id = computed(() => String(route.params.id))
const reasonOptions = ['特征不符', '时间地点不符', '已经找到物品', '其他原因']

function formatTime(value: string) { return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) }
function statusText(status: MatchStatus) { return status === 'pending' ? '待处理' : status === 'confirmed' ? '已确认' : '已拒绝' }

/** 读取详情时同时标记为已读，但不改变候选的处理状态。 */
async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    const current = await getMatchNotification(id.value)
    if (!current) { errorMessage.value = '找不到这条匹配通知。'; match.value = null; return }
    // 打开详情立即同步已读状态；该写入与确认/拒绝处理互不影响。
    match.value = await markMatchRead(id.value)
  } catch (error) { errorMessage.value = error instanceof Error ? error.message : '匹配详情读取失败。'; match.value = null }
  finally { loading.value = false }
}

/**
 * 处理候选前检查拒绝原因和说明长度，再通过确认框避免误操作。
 * busy 防止连续点击产生重复处理，服务层还会做第二次状态保护。
 */
async function decide(decision: 'confirmed' | 'rejected') {
  if (busy.value || !match.value || match.value.status !== 'pending') return
  actionError.value = ''
  if (decision === 'rejected' && !rejectionReason.value) { actionError.value = '请选择拒绝原因。'; document.getElementById('rejection-reason')?.focus(); return }
  if (rejectionNote.value.trim().length > 200) { actionError.value = '补充说明不能超过 200 个字。'; document.getElementById('rejection-note')?.focus(); return }
  const prompt = decision === 'confirmed' ? '确认接受这条候选匹配？这不代表完成认领或归还。' : '确认拒绝这条候选匹配？'
  if (!window.confirm(prompt)) return
  busy.value = true
  try {
    match.value = await decideMatch(id.value, decision, rejectionReason.value, rejectionNote.value.trim())
  } catch (error) { actionError.value = error instanceof Error ? error.message : '操作失败，请重试。' }
  finally { busy.value = false }
}

function navigate(label: string) { if (label === '我的') window.alert('「我的」将在后续迭代中开放。') }
onMounted(() => { void load() })
watch(id, () => { void load() })
</script>

<template>
  <div class="app-shell">
    <SiteHeader active-nav="匹配通知" @navigate="navigate" />
    <main class="match-main">
      <button class="back-link" type="button" @click="router.push({ name: 'notifications' })">← 返回匹配通知</button>
      <div v-if="loading" class="page-state" role="status"><span class="loading-spinner" aria-hidden="true"></span><p>正在读取匹配详情…</p></div>
      <div v-else-if="errorMessage" class="page-state error-state" role="alert"><span class="state-icon" aria-hidden="true">!</span><h1>无法打开匹配详情</h1><p>{{ errorMessage }}</p><div class="state-actions"><button class="secondary-button" type="button" @click="load">重试</button><button class="primary-button" type="button" @click="router.push({ name: 'notifications' })">返回通知</button></div></div>
      <!-- 正常详情分为：页面标题、双方物品对比、模拟得分解释、处理反馈四部分。 -->
      <template v-else-if="match"><header class="match-heading"><div><p class="section-kicker">MATCH DETAIL</p><h1>{{ match.title }}</h1><p class="demo-notice">匹配分数用于比较候选线索，不是找回概率，请继续核验物品特征。</p></div><span :class="['match-status', match.status]">{{ statusText(match.status) }}</span></header>
        <section class="match-compare" aria-label="双方物品对比"><article v-for="(item, index) in [match.mine, match.candidate]" :key="index" class="match-item"><p class="match-item-label">{{ index === 0 ? '我的物品' : '候选物品' }}</p><div class="match-item-visual"><img v-if="(item as MatchItem).imageId" :src="(item as MatchItem).imageId" alt="物品图片" /><span v-else aria-hidden="true">{{ (item as MatchItem).icon }}</span><small>{{ (item as MatchItem).imageId ? '物品图片' : '暂无实物照片' }}</small></div><h2>{{ (item as MatchItem).title }}</h2><dl><div><dt>类别</dt><dd>{{ (item as MatchItem).category }}</dd></div><div><dt>描述</dt><dd>{{ (item as MatchItem).description }}</dd></div><div><dt>地点</dt><dd>{{ (item as MatchItem).campus }} · {{ (item as MatchItem).location }}</dd></div><div><dt>时间</dt><dd>{{ formatTime((item as MatchItem).occurredAt) }}</dd></div></dl></article></section>
        <section class="match-score-panel"><div class="match-score-heading"><div><h2>匹配依据</h2><p>生成候选时的得分和依据不会随确认或拒绝而变化。</p></div><div class="score-total"><strong>{{ match.score }}</strong><span>/ 100</span></div></div><div class="dimension-list"><div v-for="dimension in match.dimensions" :key="dimension.label" class="dimension-row"><div class="dimension-title"><strong>{{ dimension.label }}</strong><span>{{ dimension.score === null ? '未评估' : `${dimension.score} / 100` }}</span></div><div v-if="dimension.score !== null" class="score-track"><span :style="{ width: `${dimension.score}%` }"></span></div><p>{{ dimension.explanation }}</p></div></div></section>
        <!-- 已处理记录只展示结果；只有 pending 状态才显示确认和拒绝按钮。 -->
        <section class="match-feedback"><h2>处理这条候选</h2><p v-if="match.status === 'confirmed'">已确认接受候选。后续仍需联系对方核验身份和物品特征；认领与归还尚未实现。</p><p v-else-if="match.status === 'rejected'">已拒绝候选。原因：{{ match.rejectionReason || '未填写' }}{{ match.rejectionNote ? `；${match.rejectionNote}` : '' }}</p><template v-else><p>确认仅表示接受这条线索，不能代替认领与归还。</p><div class="rejection-fields"><label for="rejection-reason">拒绝原因</label><select id="rejection-reason" v-model="rejectionReason"><option value="">请选择原因</option><option v-for="reason in reasonOptions" :key="reason" :value="reason">{{ reason }}</option></select><label for="rejection-note">补充说明（选填）</label><textarea id="rejection-note" v-model="rejectionNote" rows="3" maxlength="200" placeholder="可补充不符之处"></textarea></div><p v-if="actionError" class="field-error" role="alert">{{ actionError }}</p><div class="entry-actions"><button class="primary-button" type="button" :disabled="busy" @click="decide('confirmed')">{{ busy ? '处理中…' : '确认匹配' }}</button><button class="report-button" type="button" :disabled="busy" @click="decide('rejected')">拒绝匹配</button></div></template></section>
      </template>
    </main>
  </div>
</template>
