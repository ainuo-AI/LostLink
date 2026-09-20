<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import ItemCard from '../components/ItemCard.vue'
import ItemDetailDialog from '../components/ItemDetailDialog.vue'
import SiteHeader from '../components/SiteHeader.vue'
import type { Campus, LostFoundItem, RecordType } from '../types/item'

// 首页暂时使用本地演示数据。
// 后续接入后端时，可将这个数组替换为 src/api/ 中的查询结果。
const items: LostFoundItem[] = [
  {
    id: 1,
    type: 'lost',
    category: '箱包',
    title: '黑色双肩包',
    description: '包上有一枚白色小熊徽章，内有专业课本和钥匙。',
    location: '图书馆二层',
    campus: '东丽校区',
    area: '北区',
    displayTime: '今天 15:20',
    daysAgo: 0,
    icon: '🎒',
    color: '#2878a9',
    contactHint: '请提供包内课本名称进行核验。',
  },
  {
    id: 2,
    type: 'found',
    category: '卡证',
    title: '蓝色校园卡套',
    description: '透明卡套配蓝色挂绳，已送到教学楼值班室。',
    location: '教学楼 A 座',
    campus: '东丽校区',
    area: '南区',
    displayTime: '昨天 18:05',
    daysAgo: 1,
    icon: '🪪',
    color: '#22a07a',
    contactHint: '请说明卡套内校园卡的姓名末字。',
  },
  {
    id: 3,
    type: 'found',
    category: '数码',
    title: '白色无线耳机',
    description: '白色充电仓，外壳有轻微划痕，耳机已妥善保管。',
    location: '操场南门',
    campus: '宁河校区',
    area: '',
    displayTime: '9 月 16 日',
    daysAgo: 4,
    icon: '🎧',
    color: '#e79338',
    contactHint: '请描述蓝牙名称或保护套特征。',
  },
  {
    id: 4,
    type: 'lost',
    category: '文具',
    title: '银色金属钢笔',
    description: '笔帽处刻有一行小字，可能遗落在自习室。',
    location: '博学楼 302',
    campus: '东丽校区',
    area: '北区',
    displayTime: '9 月 15 日',
    daysAgo: 5,
    icon: '🖊️',
    color: '#6c72b8',
    contactHint: '请联系发布者进一步核对。',
  },
  {
    id: 5,
    type: 'found',
    category: '服饰',
    title: '浅灰色防晒外套',
    description: '左侧口袋内有一包纸巾，现放在食堂服务台。',
    location: '第二食堂',
    campus: '宁河校区',
    area: '',
    displayTime: '9 月 14 日',
    daysAgo: 6,
    icon: '🧥',
    color: '#bf657b',
    contactHint: '请说明外套尺码和品牌。',
  },
  {
    id: 6,
    type: 'lost',
    category: '书籍',
    title: '《软件工程导论》',
    description: '书中夹有黄色便签，扉页写有姓名和班级。',
    location: '实验楼 4 楼',
    campus: '东丽校区',
    area: '南区',
    displayTime: '9 月 12 日',
    daysAgo: 8,
    icon: '📘',
    color: '#3e75ca',
    contactHint: '请联系发布者核对扉页信息。',
  },
]

// ref 创建响应式状态：值改变后，Vue 会自动更新页面。
// keywordInput 是输入框当前内容，keyword 是用户点击“搜索”后真正生效的关键词。
const keywordInput = ref('')
const keyword = ref('')
const selectedType = ref<'all' | RecordType>('all')
const category = ref('all')
const campus = ref<'all' | Campus>('all')
const area = ref<'all' | '北区' | '南区'>('all')
const timeRange = ref('30')
const selectedItem = ref<LostFoundItem | null>(null)
const filtersOpen = ref(false)
const notice = ref('')

// Set 自动去重，再转回数组，用于生成下拉选项。
const categories = [...new Set(items.map((item) => item.category))]
const campuses: Campus[] = ['东丽校区', '宁河校区']
const dongliAreas = ['北区', '南区'] as const

// 离开东丽校区后清空北区/南区条件，避免隐藏条件影响宁河结果。
watch(campus, (currentCampus) => {
  if (currentCampus !== '东丽校区') area.value = 'all'
})

// computed 是计算属性：只要关键词或任意筛选条件改变，结果就会自动重新计算。
const filteredItems = computed(() => {
  const query = keyword.value.trim().toLocaleLowerCase('zh-CN')
  const maxDays = Number(timeRange.value)

  return items.filter((item) => {
    // 关键词会同时检索标题、描述、地点和类别。
    const matchesKeyword = !query || [item.title, item.description, item.location, item.category, item.campus, item.area]
      .some((field) => field.toLocaleLowerCase('zh-CN').includes(query))

    // 每个布尔值代表一组筛选条件，只有全部为 true 时才保留该记录。
    const matchesType = selectedType.value === 'all' || item.type === selectedType.value
    const matchesCategory = category.value === 'all' || item.category === category.value
    const matchesCampus = campus.value === 'all' || item.campus === campus.value
    const matchesArea = campus.value !== '东丽校区' || area.value === 'all' || item.area === area.value
    const matchesTime = item.daysAgo <= maxDays

    return matchesKeyword && matchesType && matchesCategory && matchesCampus && matchesArea && matchesTime
  })
})

// 提交搜索时才把输入值写入 keyword，避免用户每输入一个字都立即刷新。
function submitSearch() {
  keyword.value = keywordInput.value
}

// 将所有条件恢复为页面初始状态。
function resetFilters() {
  keywordInput.value = ''
  keyword.value = ''
  selectedType.value = 'all'
  category.value = 'all'
  campus.value = 'all'
  area.value = 'all'
  timeRange.value = '30'
}

// 其他页面尚未实现，点击后使用轻提示告知用户，而不是出现无反应的按钮。
function navigate(label: string) {
  if (label === '首页') return
  notice.value = `「${label}」将在后续迭代中开放`
  window.setTimeout(() => {
    notice.value = ''
  }, 2200)
}
</script>

<template>
  <div class="app-shell">
    <!-- 父组件通过 @navigate 监听子组件发出的导航事件。 -->
    <SiteHeader active-nav="首页" @navigate="navigate" />

    <main>
      <!-- 首屏文案区：说明页面的核心用途。 -->
      <section class="intro-section" aria-labelledby="page-title">
        <div>
          <p class="eyebrow">CAMPUS LOST &amp; FOUND</p>
          <h1 id="page-title">找回遗失，连接线索</h1>
          <p class="intro-copy">搜索校园失物与拾物记录，让每一件物品都有回家的可能。</p>
        </div>
        <div class="intro-stat" aria-label="今日数据">
          <span class="stat-number">12</span>
          <span class="stat-label">今日新线索</span>
        </div>
      </section>

      <!-- .prevent 阻止表单默认刷新页面，改由 Vue 在前端完成搜索。 -->
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
        <button class="primary-button search-button" type="submit">搜索</button>
      </form>

      <div class="mobile-toolbar">
        <button class="filter-toggle" type="button" :aria-expanded="filtersOpen" @click="filtersOpen = !filtersOpen">
          <span aria-hidden="true">☷</span> 筛选条件
        </button>
        <span>共 {{ filteredItems.length }} 条记录</span>
      </div>

      <div class="content-grid">
        <!-- 在手机端通过 open 类控制筛选面板展开/收起。 -->
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

          <!-- 东丽校区才需要第二级区域筛选，宁河校区作为一个整体。 -->
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

        <section class="results-section" aria-labelledby="results-title">
          <div class="results-header">
            <div>
              <p class="section-kicker">最新动态</p>
              <h2 id="results-title">最新记录</h2>
            </div>

            <div class="type-tabs" role="group" aria-label="记录类型">
              <button type="button" :class="{ active: selectedType === 'all' }" @click="selectedType = 'all'">全部</button>
              <button type="button" :class="{ active: selectedType === 'lost' }" @click="selectedType = 'lost'">失物</button>
              <button type="button" :class="{ active: selectedType === 'found' }" @click="selectedType = 'found'">拾物</button>
            </div>
          </div>

          <!-- v-if/v-else 分别处理“有结果”和“空结果”两种状态。 -->
          <div v-if="filteredItems.length" class="item-grid" aria-live="polite">
            <!-- v-for 循环生成卡片；点击后将当前物品赋给 selectedItem。 -->
            <ItemCard v-for="item in filteredItems" :key="item.id" :item="item" @open="selectedItem = $event" />
          </div>

          <div v-else class="empty-state" role="status">
            <span aria-hidden="true">🔎</span>
            <h3>没有找到相关记录</h3>
            <p>换个关键词，或者放宽筛选条件试试。</p>
            <button class="secondary-button" type="button" @click="resetFilters">清除筛选</button>
          </div>
        </section>
      </div>
    </main>

    <!-- transition 为提示消息添加淡入淡出效果。 -->
    <transition name="toast">
      <div v-if="notice" class="toast" role="status">{{ notice }}</div>
    </transition>

    <!-- selectedItem 有值时打开详情，子组件发出 close 后恢复为 null。 -->
    <ItemDetailDialog v-if="selectedItem" :item="selectedItem" @close="selectedItem = null" />
  </div>
</template>
