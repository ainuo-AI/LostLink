<script setup lang="ts">
// 设计文档对照：04_LostLink软件设计规格说明书.docx；以下“设计文档对应”使用该文档图表编号。
// 文档对照：03_LostLink软件需求规格说明书.docx；图表编号以当前文档为准。
/**
 * 物品详情页面
 *
 * 页面根据路由中的物品 id 读取公开数据，展示加载、错误和正常详情三种状态，
 * 并提供“举报”子流程入口。当前没有单条详情接口，因此读取逻辑集中在 itemNavigation。
 */
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError } from '../api/client'
import SiteHeader from '../components/SiteHeader.vue'
import { loadItemForPage } from '../stores/itemNavigation'
import type { LostFoundItem } from '../types/item'

const route = useRoute()
const router = useRouter()

const item = ref<LostFoundItem | null>(null)
const loading = ref(true)
const errorMessage = ref('')
const notice = ref('')
let activeRequest: AbortController | null = null

const itemId = computed(() => Number(route.params.id))

/** 功能对应：优先读取首页缓存，刷新页面时用现有列表接口兜底查找。 */
// 文档对应：图2-2-4 物品详情；图2-3 物品管理界面；2.2.4节。
// 设计文档对应：图3-2-3、图4-1-5、图4-2 按路由编号重新读取物品公开详情。
async function loadItem() {
  if (!Number.isSafeInteger(itemId.value) || itemId.value < 1) {
    item.value = null
    loading.value = false
    errorMessage.value = '物品编号无效，请返回首页重新选择。'
    return
  }

  activeRequest?.abort()
  const controller = new AbortController()
  activeRequest = controller
  loading.value = true
  errorMessage.value = ''

  try {
    item.value = await loadItemForPage(itemId.value, controller.signal)
    if (!item.value) errorMessage.value = '未找到指定物品，请返回首页重新选择。'
  } catch (error) {
    if (controller.signal.aborted || (error instanceof Error && error.name === 'AbortError')) return
    errorMessage.value = error instanceof ApiError
      ? error.message
      : '无法连接数据服务，请确认后端已经启动后重试。'
    item.value = null
  } finally {
    if (activeRequest === controller) {
      loading.value = false
      activeRequest = null
    }
  }
}

/** 功能对应：详情页下方“举报”按钮进入当前物品的举报提交页。 */
// 设计文档对应：图3-3-2 由物品详情进入举报提交路由。
function openReportPage() {
  if (!item.value) return
  void router.push({ name: 'report-submit', params: { id: item.value.id } })
}

function navigate(label: string) {
  if (label === '首页') {
    void router.push({ name: 'home' })
    return
  }
  notice.value = `「${label}」将在后续迭代中开放`
  window.setTimeout(() => { notice.value = '' }, 2200)
}

// 设计文档对应：图3-2-3 认领按钮仅展示待开放提示，没有认领申请业务。
function showClaimNotice() {
  notice.value = '认领功能将在后续迭代中开放'
  window.setTimeout(() => { notice.value = '' }, 2200)
}

onMounted(() => { void loadItem() })
watch(itemId, () => { void loadItem() })
onBeforeUnmount(() => { activeRequest?.abort() })
</script>

<!-- 设计文档对应：图3-1-4 物品详情外观，包含公开字段、类别图标与举报入口。 -->
<template>
  <div class="app-shell">
    <SiteHeader active-nav="" @navigate="navigate" />

    <main class="page-main">
      <button class="back-link" type="button" @click="$router.push({ name: 'home' })">
        <span aria-hidden="true">←</span> 返回首页
      </button>

      <div v-if="loading" class="page-state" role="status" aria-live="polite">
        <span class="loading-spinner" aria-hidden="true"></span>
        <h1>正在加载物品详情</h1>
        <p>正在读取该物品的最新公开信息。</p>
      </div>

      <div v-else-if="errorMessage" class="page-state error-state" role="alert">
        <span class="state-icon" aria-hidden="true">!</span>
        <h1>无法打开物品详情</h1>
        <p>{{ errorMessage }}</p>
        <div class="state-actions">
          <button class="secondary-button" type="button" @click="loadItem">重新加载</button>
          <button class="primary-button" type="button" @click="$router.push({ name: 'home' })">返回首页</button>
        </div>
      </div>

      <!-- 功能对应：原详情弹窗升级为独立详情页，保留全部公开字段。 -->
      <article v-else-if="item" class="item-detail-page">
        <div class="detail-page-visual" :style="{ '--item-color': item.color }">
          <span aria-hidden="true">{{ item.icon }}</span>
          <p>{{ item.area ? `${item.campus} · ${item.area}` : item.campus }}</p>
        </div>

        <div class="detail-page-content">
          <span :class="['type-label', item.type]">{{ item.type === 'lost' ? '寻物启事' : '拾物信息' }}</span>
          <h1>{{ item.title }}</h1>
          <p class="dialog-description">{{ item.description }}</p>

          <dl class="detail-list">
            <div>
              <dt>物品类别</dt>
              <dd>{{ item.category }}</dd>
            </div>
            <div>
              <dt>地点</dt>
              <dd>{{ item.location }}</dd>
            </div>
            <div>
              <dt>时间</dt>
              <dd>{{ item.displayTime }}</dd>
            </div>
            <div>
              <dt>联系提示</dt>
              <dd>{{ item.contactHint }}</dd>
            </div>
          </dl>

          <div class="detail-actions">
            <button class="primary-button wide" type="button" @click="showClaimNotice">
              {{ item.type === 'lost' ? '我可能找到了' : '这可能是我的' }}
            </button>
            <!-- 用户要求新增的入口：位于详情主要操作下方。 -->
            <button class="report-button wide" type="button" @click="openReportPage">
              举报
            </button>
          </div>
        </div>
      </article>
    </main>

    <transition name="toast">
      <div v-if="notice" class="toast" role="status">{{ notice }}</div>
    </transition>
  </div>
</template>
