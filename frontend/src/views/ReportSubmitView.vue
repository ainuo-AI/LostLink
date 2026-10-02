<script setup lang="ts">
/**
 * 举报提交页面
 *
 * 先加载被举报物品摘要，再校验举报原因、说明和真实性确认；
 * 当前结果只写入浏览器本地存储，不调用后端，也不代表管理员已经收到。
 */
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError } from '../api/client'
import SiteHeader from '../components/SiteHeader.vue'
import { loadItemForPage } from '../stores/itemNavigation'
import { createLocalReport } from '../stores/reports'
import type { LostFoundItem } from '../types/item'
import type { ReportReason } from '../types/report'

const route = useRoute()
const router = useRouter()
const itemId = computed(() => Number(route.params.id))

const item = ref<LostFoundItem | null>(null)
const loading = ref(true)
const loadError = ref('')
const reason = ref<ReportReason | ''>('')
const description = ref('')
const confirmed = ref(false)
const submitted = ref(false)
const submitting = ref(false)
const submitError = ref('')
const createdReportId = ref<number | null>(null)
let activeRequest: AbortController | null = null

const reasonOptions: Array<{ value: ReportReason; label: string }> = [
  { value: 'inaccurate', label: '信息不准确' },
  { value: 'duplicate', label: '重复发布' },
  { value: 'spam', label: '广告或垃圾信息' },
  { value: 'inappropriate', label: '不当或敏感内容' },
  { value: 'fraud', label: '疑似冒领或欺诈' },
  { value: 'other', label: '其他问题' },
]

const descriptionLength = computed(() => description.value.trim().length)
// 表单有效条件集中计算，模板可以同时用它控制错误和提交逻辑。
const formValid = computed(() => (
  Boolean(reason.value)
  && descriptionLength.value >= 10
  && descriptionLength.value <= 500
  && confirmed.value
))

/** 功能对应：举报页先读取物品摘要，用户能确认自己举报的是哪条记录。 */
async function loadItem() {
  if (!Number.isSafeInteger(itemId.value) || itemId.value < 1) {
    loading.value = false
    loadError.value = '物品编号无效，请返回首页重新选择。'
    return
  }

  const controller = new AbortController()
  activeRequest = controller
  try {
    item.value = await loadItemForPage(itemId.value, controller.signal)
    if (!item.value) loadError.value = '未找到指定物品，请返回首页重新选择。'
  } catch (error) {
    if (controller.signal.aborted || (error instanceof Error && error.name === 'AbortError')) return
    loadError.value = error instanceof ApiError
      ? error.message
      : '无法连接数据服务，请确认后端已经启动后重试。'
  } finally {
    if (activeRequest === controller) {
      loading.value = false
      activeRequest = null
    }
  }
}

/** 功能对应：校验表单后保存为浏览器本地演示记录，不修改后端。 */
async function submitReport() {
  submitted.value = true
  submitError.value = ''
  if (!formValid.value || !item.value || !reason.value) return

  submitting.value = true
  try {
    const report = await createLocalReport({
      item_id: item.value.id,
      reason: reason.value,
      description: description.value.trim(),
    })
    createdReportId.value = report.id
  } catch (error) {
    submitError.value = error instanceof ApiError
      ? error.message
      : '举报提交失败，请检查网络连接后重试。'
  } finally {
    submitting.value = false
  }
}

function navigate(label: string) {
  if (label === '首页') void router.push({ name: 'home' })
  if (label === '我的') window.alert('「我的」将在后续迭代中开放。')
}

onMounted(() => { void loadItem() })
onBeforeUnmount(() => { activeRequest?.abort() })
</script>

<template>
  <div class="app-shell">
    <SiteHeader active-nav="" @navigate="navigate" />

    <main class="page-main report-page-main">
      <button
        class="back-link"
        type="button"
        @click="$router.push({ name: 'item-detail', params: { id: route.params.id } })"
      >
        <span aria-hidden="true">←</span> 返回物品详情
      </button>

      <div v-if="loading" class="page-state" role="status">
        <span class="loading-spinner" aria-hidden="true"></span>
        <h1>正在准备举报信息</h1>
      </div>

      <div v-else-if="loadError || !item" class="page-state error-state" role="alert">
        <span class="state-icon" aria-hidden="true">!</span>
        <h1>无法打开举报页面</h1>
        <p>{{ loadError }}</p>
        <button class="primary-button" type="button" @click="$router.push({ name: 'home' })">返回首页</button>
      </div>

      <section v-else-if="createdReportId" class="report-success" role="status">
        <span class="success-mark" aria-hidden="true">✓</span>
        <p class="section-kicker">REPORT RECEIVED</p>
        <h1>举报已提交</h1>
        <p>本地演示举报编号为 <strong>#{{ createdReportId }}</strong>，当前状态为“待处理”。记录已保存在当前浏览器中，未提交到后端。</p>
        <div class="state-actions">
          <button class="secondary-button" type="button" @click="$router.push({ name: 'item-detail', params: { id: item.id } })">
            返回物品详情
          </button>
          <button class="primary-button" type="button" @click="$router.push({ name: 'home' })">返回首页</button>
        </div>
      </section>

      <!-- 功能对应：举报提交页。物品摘要只读，原因和说明由用户填写。 -->
      <div v-else class="report-layout">
        <section class="report-form-panel" aria-labelledby="report-title">
          <p class="section-kicker">REPORT ITEM</p>
          <h1 id="report-title">提交举报</h1>
          <p class="report-intro">请如实说明问题。举报提交后进入待处理状态，由管理员依据物品内容和说明进行核查。</p>

          <form novalidate @submit.prevent="submitReport">
            <div class="form-field">
              <label for="report-reason">举报原因 <span aria-hidden="true">*</span></label>
              <select id="report-reason" v-model="reason" :aria-invalid="submitted && !reason">
                <option value="" disabled>请选择举报原因</option>
                <option v-for="option in reasonOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <p v-if="submitted && !reason" class="field-error">请选择举报原因。</p>
            </div>

            <div class="form-field">
              <div class="field-heading">
                <label for="report-description">问题说明 <span aria-hidden="true">*</span></label>
                <span>{{ descriptionLength }}/500</span>
              </div>
              <textarea
                id="report-description"
                v-model="description"
                rows="7"
                maxlength="500"
                placeholder="请描述发现的问题、判断依据及便于管理员核查的信息（至少 10 个字）"
                :aria-invalid="submitted && (descriptionLength < 10 || descriptionLength > 500)"
              ></textarea>
              <p v-if="submitted && descriptionLength < 10" class="field-error">问题说明至少需要 10 个字。</p>
            </div>

            <label class="confirm-row">
              <input v-model="confirmed" type="checkbox" />
              <span>我确认以上内容真实，不提交恶意或重复举报。</span>
            </label>
            <p v-if="submitted && !confirmed" class="field-error">请先确认举报内容真实。</p>

            <div v-if="submitError" class="form-alert" role="alert">{{ submitError }}</div>

            <button class="report-submit-button wide" type="submit" :disabled="submitting">
              {{ submitting ? '正在提交…' : '提交举报' }}
            </button>
          </form>
        </section>

        <aside class="report-item-summary" aria-label="被举报物品">
          <p class="summary-label">被举报物品</p>
          <div class="summary-visual" :style="{ '--item-color': item.color }">
            <span aria-hidden="true">{{ item.icon }}</span>
          </div>
          <span :class="['type-label', item.type]">{{ item.type === 'lost' ? '寻物启事' : '拾物信息' }}</span>
          <h2>{{ item.title }}</h2>
          <p>{{ item.description }}</p>
          <dl>
            <div><dt>地点</dt><dd>{{ item.location }}</dd></div>
            <div><dt>时间</dt><dd>{{ item.displayTime }}</dd></div>
            <div><dt>记录编号</dt><dd>#{{ item.id }}</dd></div>
          </dl>
        </aside>
      </div>
    </main>
  </div>
</template>
