<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import SiteHeader from '../components/SiteHeader.vue'
import ItemCard from '../components/ItemCard.vue'
import { cacheItemForNavigation } from '../stores/itemNavigation'
import type { ItemStatus, LostFoundItem, RecordType } from '../types/item'

const PAGE_SIZE = 6
const router = useRouter()
const selectedType = ref<RecordType>('lost')
const status = ref<'all' | ItemStatus>('all')
const currentPage = ref(1)
const demoItems = ref<LostFoundItem[]>([])
const showDemoRecords = ref(false)

const statusLabels: Record<ItemStatus, string> = {
  active: '进行中',
  recovered: '已找回',
  returned: '已归还',
  closed: '已关闭',
}

// 演示数据仅在开发预览中加载，不能作为当前用户的记录或权限依据。
onMounted(async () => {
  if (import.meta.env.DEV) {
    const { profileDemoItems } = await import('../dev/profileDemo')
    demoItems.value = profileDemoItems
  }
})

const filteredDemoItems = computed(() => demoItems.value.filter(item =>
  item.type === selectedType.value && (status.value === 'all' || item.status === status.value),
))
const totalPages = computed(() => Math.max(1, Math.ceil(filteredDemoItems.value.length / PAGE_SIZE)))
const visibleItems = computed(() => filteredDemoItems.value.slice(
  (currentPage.value - 1) * PAGE_SIZE,
  currentPage.value * PAGE_SIZE,
))

watch([selectedType, status, showDemoRecords], () => {
  currentPage.value = 1
})

function changePage(nextPage: number) {
  if (nextPage < 1 || nextPage > totalPages.value) return
  currentPage.value = nextPage
}

/** 个人页演示记录沿用独立详情页，不再维护第二套详情弹窗。 */
function openItem(item: LostFoundItem) {
  cacheItemForNavigation(item)
  void router.push({ name: 'item-detail', params: { id: item.id } })
}
</script>

<template>
  <div class="app-shell">
    <SiteHeader active-nav="我的" />
    <main class="profile-main">
      <section class="intro-section" aria-labelledby="profile-title">
        <div>
          <p class="eyebrow">MY LOSTLINK</p>
          <h1 id="profile-title" tabindex="-1">我的</h1>
          <p class="intro-copy">集中查看你的失物与拾物记录。</p>
        </div>
      </section>

      <aside class="profile-preview-note" aria-label="开发预览说明">
        <strong>开发预览 · 相关服务暂未接入</strong>
        <p>此页面仅预览布局和交互，不代表登录成功。用户信息与个人记录尚不可用。</p>
        <RouterLink :to="{ name: 'login' }">返回登录</RouterLink>
      </aside>

      <section class="profile-summary" aria-labelledby="profile-summary-title">
        <div>
          <p class="section-kicker">个人信息</p>
          <h2 id="profile-summary-title">用户信息摘要</h2>
          <p>个人信息服务暂未接入，无法展示账号、显示名称或校园身份。</p>
          <p class="profile-hint">校园身份核验状态需由服务端提供。</p>
        </div>
        <div class="profile-logout">
          <button class="secondary-button" type="button" disabled aria-describedby="logout-note">退出登录</button>
          <p id="logout-note" class="profile-hint">退出登录服务暂未接入</p>
        </div>
      </section>

      <section class="profile-records" aria-labelledby="profile-records-title">
        <div class="results-header">
          <div>
            <p class="section-kicker">个人记录</p>
            <h2 id="profile-records-title">我的物品记录</h2>
          </div>
          <div class="type-tabs" role="group" aria-label="我的记录类型">
            <button type="button" :class="{ active: selectedType === 'lost' }" :aria-pressed="selectedType === 'lost'" @click="selectedType = 'lost'">我的失物</button>
            <button type="button" :class="{ active: selectedType === 'found' }" :aria-pressed="selectedType === 'found'" @click="selectedType = 'found'">我的拾物</button>
          </div>
        </div>

        <div class="profile-controls">
          <div class="filter-group">
            <label for="my-status">记录状态</label>
            <select id="my-status" v-model="status">
              <option value="all">全部状态</option>
              <option v-for="(label, value) in statusLabels" :key="value" :value="value">{{ label }}</option>
            </select>
          </div>
          <button class="secondary-button" type="button" :disabled="!demoItems.length" :aria-pressed="showDemoRecords" @click="showDemoRecords = !showDemoRecords">
            {{ showDemoRecords ? '收起演示记录' : '查看演示记录（非个人数据）' }}
          </button>
        </div>

        <p class="profile-hint">记录管理服务与编辑表单暂未接入，编辑、关闭和归还操作暂不可用。</p>

        <template v-if="showDemoRecords">
          <p class="profile-demo-note" role="status">开发演示：以下为虚构物品，仅用于预览，非个人数据。筛选后共 {{ filteredDemoItems.length }} 条演示记录。</p>
          <div v-if="visibleItems.length" class="item-grid">
            <div v-for="item in visibleItems" :key="item.id" class="profile-record">
              <ItemCard :item="item" @open="openItem" />
              <p class="profile-record-status">状态：{{ statusLabels[item.status] }}</p>
            </div>
          </div>
          <div v-else class="empty-state" role="status">
            <h3>演示数据中没有符合条件的记录</h3>
            <p>可切换状态查看其他演示记录。</p>
            <button class="secondary-button" type="button" @click="status = 'all'">清除状态筛选</button>
          </div>
          <nav v-if="totalPages > 1" class="pagination" aria-label="演示记录分页">
            <button type="button" :disabled="currentPage === 1" @click="changePage(currentPage - 1)">上一页</button>
            <span aria-live="polite">第 {{ currentPage }} / {{ totalPages }} 页</span>
            <button type="button" :disabled="currentPage === totalPages" @click="changePage(currentPage + 1)">下一页</button>
          </nav>
        </template>
        <template v-else>
          <div class="empty-state profile-unavailable" role="status">
            <h3>个人记录服务暂未接入</h3>
            <p>当前无法读取{{ selectedType === 'lost' ? '我的失物' : '我的拾物' }}，也无法确认记录总量。</p>
            <RouterLink class="secondary-button auth-link-button" :to="{ name: 'login' }">返回登录</RouterLink>
          </div>
          <nav class="pagination" aria-label="个人记录分页">
            <button type="button" disabled>上一页</button>
            <span>分页服务暂未接入</span>
            <button type="button" disabled>下一页</button>
          </nav>
        </template>
      </section>
    </main>
  </div>
</template>

<style scoped>
.profile-preview-note {
  margin: 28px 0;
  padding: 20px 24px;
  background: var(--sky);
  border: 1px solid var(--line);
  border-radius: 14px;
  color: var(--blue-dark);
  line-height: 1.7;
}

.profile-preview-note p {
  margin: 6px 0 10px;
}

.profile-preview-note a {
  color: var(--blue);
  font-weight: 700;
}

.profile-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
  padding: 28px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 16px;
  box-shadow: var(--shadow);
}

.profile-summary h2 {
  color: var(--navy);
  font-size: 1.45rem;
}

.profile-summary p:not(.section-kicker) {
  margin-bottom: 8px;
  line-height: 1.7;
}

.profile-hint {
  color: var(--muted);
  font-size: 0.85rem;
  line-height: 1.7;
}

.profile-logout {
  flex-shrink: 0;
}

.profile-logout p {
  margin-top: 10px;
}

.profile-records {
  margin-top: 36px;
}

.profile-controls {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 18px;
}

.profile-controls .filter-group {
  width: 200px;
  margin: 0;
}

.profile-demo-note {
  margin: 20px 0;
  padding: 12px 16px;
  color: var(--blue-dark);
  background: var(--sky);
  border-radius: 9px;
  line-height: 1.7;
}

.profile-record {
  min-width: 0;
}

.profile-record-status {
  margin: 10px 4px 0;
  color: var(--muted);
  font-size: 0.85rem;
}

.profile-unavailable {
  min-height: 240px;
  padding: 24px;
}

.profile-main a:focus-visible {
  outline: 3px solid rgba(49, 145, 202, 0.5);
  outline-offset: 3px;
}

@media (max-width: 560px) {
  .profile-summary {
    align-items: flex-start;
    flex-direction: column;
    padding: 24px 20px;
  }

  .profile-preview-note {
    padding: 18px 20px;
  }

  .profile-controls .filter-group {
    width: 100%;
  }

  .profile-controls > button {
    width: 100%;
  }

  .profile-records > .pagination {
    gap: 8px;
    font-size: 0.75rem;
  }
}
</style>
