<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ApiError } from '../api/client'
import { fetchItems, toLostFoundItem } from '../api/items'
import ItemCard from '../components/ItemCard.vue'
import ItemDetailDialog from '../components/ItemDetailDialog.vue'
import SiteHeader from '../components/SiteHeader.vue'
import type { Campus, CampusArea, LostFoundItem, RecordType } from '../types/item'

const emit = defineEmits<{
  login: []
  profile: []
}>()

const PAGE_SIZE = 6

// 首页状态由真实 API 响应驱动，不再保存与后端重复的本地记录数组。
const items = ref<LostFoundItem[]>([])
const total = ref(0)
const loading = ref(false)
const errorMessage = ref('')
const currentPage = ref(1)
const keywordInput = ref('')
const keyword = ref('')
const selectedType = ref<'all' | RecordType>('all')
const category = ref('all')
const campus = ref<'all' | Campus>('all')
const area = ref<'all' | CampusArea>('all')
const timeRange = ref('30')
const selectedItem = ref<LostFoundItem | null>(null)
const filtersOpen = ref(false)
const notice = ref('')

// 类别属于当前产品枚举；不从筛选后的结果临时推导，避免选项随查询结果消失。
const categories = ['箱包', '卡证', '数码', '文具', '服饰', '书籍', '其他']
const campuses: Campus[] = ['东丽校区', '宁河校区']
const dongliAreas: CampusArea[] = ['北区', '南区']

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

// 筛选签名用于监听查询变化；Vue 会合并同一轮中的多项重置操作。
const filterSignature = computed(() => JSON.stringify({
  keyword: keyword.value,
  type: selectedType.value,
  category: category.value,
  campus: campus.value,
  area: area.value,
  days: timeRange.value,
}))

let activeRequest: AbortController | null = null

/** 从 FastAPI 加载当前页，并忽略已经被新查询取代的旧请求。 */
async function loadItems() {
  activeRequest?.abort()
  const controller = new AbortController()
  activeRequest = controller
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await fetchItems({
      keyword: keyword.value || undefined,
      type: selectedType.value === 'all' ? undefined : selectedType.value,
      category: category.value === 'all' ? undefined : category.value,
      campus: campus.value === 'all' ? undefined : campus.value,
      area: area.value === 'all' ? undefined : area.value,
      days: Number(timeRange.value),
      page: currentPage.value,
      pageSize: PAGE_SIZE,
    }, controller.signal)

    if (controller.signal.aborted) return
    items.value = response.items.map(toLostFoundItem)
    total.value = response.total
    selectedItem.value = null
  } catch (error) {
    if (controller.signal.aborted || (error instanceof Error && error.name === 'AbortError')) return

    // 对业务错误展示后端安全文案；网络失败使用对用户更明确的连接提示。
    errorMessage.value = error instanceof ApiError
      ? error.message
      : '无法连接数据服务，请确认后端已经启动后重试。'
    items.value = []
    total.value = 0
  } finally {
    if (activeRequest === controller) {
      loading.value = false
      activeRequest = null
    }
  }
}

// 离开东丽校区后清空二级区域，避免向后端发送隐藏筛选条件。
watch(campus, (currentCampus) => {
  if (currentCampus !== '东丽校区') area.value = 'all'
})

watch(filterSignature, () => {
  // 新筛选总是从第一页开始；已经在第一页时直接重新请求。
  if (currentPage.value === 1) void loadItems()
  else currentPage.value = 1
})

watch(currentPage, () => {
  void loadItems()
})

onMounted(() => {
  void loadItems()
})

onBeforeUnmount(() => {
  activeRequest?.abort()
})

/** 搜索按钮提交后才更新真正生效的关键词。 */
function submitSearch() {
  const nextKeyword = keywordInput.value.trim()
  currentPage.value = 1
  if (keyword.value === nextKeyword) {
    void loadItems()
  } else {
    keyword.value = nextKeyword
  }
}

/** 恢复首页默认筛选，并让监听器重新请求第一页。 */
function resetFilters() {
  keywordInput.value = ''
  keyword.value = ''
  selectedType.value = 'all'
  category.value = 'all'
  campus.value = 'all'
  area.value = 'all'
  timeRange.value = '30'
  currentPage.value = 1
}

/** 切换分页时保留筛选条件，并把结果区滚回用户容易看到的位置。 */
function changePage(page: number) {
  if (page < 1 || page > totalPages.value || page === currentPage.value) return
  currentPage.value = page
  document.querySelector('.results-section')?.scrollIntoView({ behavior: 'smooth' })
}

// 其他页面尚未实现，点击后使用轻提示告知用户，而不是出现无反应的按钮。
function navigate(label: string) {
  if (label === '首页') return
  if (label === '我的') {
    emit('profile')
    return
  }
  if (label === '登录') {
    emit('login')
    return
  }
  notice.value = `「${label}」将在后续迭代中开放`
  window.setTimeout(() => {
    notice.value = ''
  }, 2200)
}
</script>

<template>
  <div class="app-shell">
    <SiteHeader active-nav="首页" @navigate="navigate" />

    <main>
      <section class="intro-section" aria-labelledby="page-title">
        <div>
          <p class="eyebrow">CAMPUS LOST &amp; FOUND</p>
          <h1 id="page-title" tabindex="-1">找回遗失，连接线索</h1>
          <p class="intro-copy">搜索校园失物与拾物记录，让每一件物品都有回家的可能。</p>
        </div>
        <div class="intro-stat" aria-label="当前有效线索">
          <span class="stat-number">{{ total }}</span>
          <span class="stat-label">条有效线索</span>
        </div>
      </section>

      <!-- 表单只在提交时应用关键词，避免每输入一个字就请求一次后端。 -->
      <form class="search-panel" role="search" @submit.prevent="submitSearch">
        <span class="search-icon" aria-hidden="true"></span>
        <label class="sr-only" for="main-search">搜索物品</label>
        <input
          id="main-search"
          v-model="keywordInput"
          type="search"
          placeholder="输入物品名称、地点或特征"
          autocomplete="off"
        />
        <button class="primary-button search-button" type="submit" :disabled="loading">
          搜索
        </button>
      </form>

      <div class="mobile-toolbar">
        <button class="filter-toggle" type="button" :aria-expanded="filtersOpen" @click="filtersOpen = !filtersOpen">
          <span aria-hidden="true">☷</span> 筛选条件
        </button>
        <span>共 {{ total }} 条记录</span>
      </div>

      <div class="content-grid">
        <aside :class="['filter-panel', { open: filtersOpen }]" aria-label="筛选条件">
          <div class="filter-heading">
            <div>
              <span class="filter-kicker">FILTER</span>
              <h2>筛选条件</h2>
            </div>
            <button class="reset-button" type="button" @click="resetFilters">重置</button>
          </div>

          <div class="filter-group">
            <label for="category">物品类别</label>
            <select id="category" v-model="category">
              <option value="all">全部类别</option>
              <option v-for="value in categories" :key="value" :value="value">{{ value }}</option>
            </select>
          </div>

          <div class="filter-group">
            <label for="campus">校园地点</label>
            <select id="campus" v-model="campus">
              <option value="all">全部校区</option>
              <option v-for="value in campuses" :key="value" :value="value">{{ value }}</option>
            </select>
          </div>

          <div v-if="campus === '东丽校区'" class="filter-group">
            <label for="campus-area">东丽区域</label>
            <select id="campus-area" v-model="area">
              <option value="all">全部区域</option>
              <option v-for="value in dongliAreas" :key="value" :value="value">{{ value }}</option>
            </select>
          </div>

          <div class="filter-group">
            <label for="time-range">时间范围</label>
            <select id="time-range" v-model="timeRange">
              <option value="7">近 7 天</option>
              <option value="30">近一个月</option>
              <option value="90">近三个月</option>
            </select>
          </div>

          <div class="filter-note">
            <span aria-hidden="true">✦</span>
            <p>小提示：添加颜色、品牌等特征，能更快找到匹配记录。</p>
          </div>
        </aside>

        <section class="results-section" aria-labelledby="results-title" :aria-busy="loading">
          <div class="results-header">
            <div>
              <p class="section-kicker">最新动态</p>
              <h2 id="results-title">最新记录</h2>
              <p class="results-status" aria-live="polite">
                {{ loading ? '正在从数据服务更新…' : `共 ${total} 条记录` }}
              </p>
            </div>

            <div class="type-tabs" role="group" aria-label="记录类型">
              <button type="button" :class="{ active: selectedType === 'all' }" @click="selectedType = 'all'; currentPage = 1">全部</button>
              <button type="button" :class="{ active: selectedType === 'lost' }" @click="selectedType = 'lost'; currentPage = 1">失物</button>
              <button type="button" :class="{ active: selectedType === 'found' }" @click="selectedType = 'found'; currentPage = 1">拾物</button>
            </div>
          </div>

          <!-- 首次加载、服务错误、正常结果和空结果分别给出明确反馈。 -->
          <div v-if="loading && !items.length" class="empty-state loading-state" role="status">
            <span class="loading-spinner" aria-hidden="true"></span>
            <h3>正在加载记录</h3>
            <p>正在连接校园失物招领数据服务。</p>
          </div>

          <div v-else-if="errorMessage" class="empty-state error-state" role="alert">
            <span aria-hidden="true">!</span>
            <h3>暂时无法加载记录</h3>
            <p>{{ errorMessage }}</p>
            <button class="secondary-button" type="button" @click="loadItems">重新加载</button>
          </div>

          <template v-else-if="items.length">
            <div class="item-grid" aria-live="polite">
              <ItemCard v-for="item in items" :key="item.id" :item="item" @open="selectedItem = $event" />
            </div>

            <nav v-if="totalPages > 1" class="pagination" aria-label="记录分页">
              <button type="button" :disabled="currentPage === 1 || loading" @click="changePage(currentPage - 1)">
                上一页
              </button>
              <span>第 {{ currentPage }} / {{ totalPages }} 页</span>
              <button type="button" :disabled="currentPage === totalPages || loading" @click="changePage(currentPage + 1)">
                下一页
              </button>
            </nav>
          </template>

          <div v-else class="empty-state" role="status">
            <span aria-hidden="true">🔎</span>
            <h3>没有找到相关记录</h3>
            <p>换个关键词，或者放宽筛选条件试试。</p>
            <button class="secondary-button" type="button" @click="resetFilters">清除筛选</button>
          </div>
        </section>
      </div>
    </main>

    <transition name="toast">
      <div v-if="notice" class="toast" role="status">{{ notice }}</div>
    </transition>

    <ItemDetailDialog v-if="selectedItem" :item="selectedItem" @close="selectedItem = null" />
  </div>
</template>
