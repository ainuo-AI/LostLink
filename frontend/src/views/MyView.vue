<script setup lang="ts">
/** 当前用户资料与物品管理页，所有数据均来自受保护的后端接口。 */
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import SiteHeader from '../components/SiteHeader.vue'
import ItemCard from '../components/ItemCard.vue'
import { ApiError } from '../api/client'
import { fetchMyItems, toLostFoundItem, updateItem, updateItemStatus } from '../api/items'
import { ITEM_CATEGORIES } from '../types/demo'
import type { ApiOwnerItem, ItemStatus, RecordType, UpdateItemPayload } from '../types/item'
import { useAuth } from '../stores/auth'
import { locationOptions, isLocationSelection, useCampusLocations } from '../services/campusLocations'

const PAGE_SIZE = 6
const router = useRouter()
const auth = useAuth()
const selectedType = ref<RecordType>('lost')
const status = ref<'all' | ItemStatus>('all')
const currentPage = ref(1)
const records = ref<ApiOwnerItem[]>([])
const total = ref(0)
const loading = ref(false)
const pageError = ref('')
const actionError = ref('')
const actionId = ref<number | null>(null)
const editing = ref<ApiOwnerItem | null>(null)
const editForm = reactive({ title: '', category: '', description: '', location: '', contact: '', contactNote: '' })
const { choices: locations, loading: locationsLoading, error: locationsError, load: loadLocations } = useCampusLocations()
const editLocations = computed(() => editing.value ? locationOptions(locations.value, editing.value.campus, editing.value.area) : [])

const statusLabels: Record<ItemStatus, string> = {
  active: '进行中', recovered: '已找回', returned: '已归还', closed: '已关闭',
}
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

function handleRequestError(error: unknown, fallback: string): string {
  if (error instanceof ApiError && error.status === 401) {
    auth.clearSession()
    void router.replace({ name: 'login', query: { redirect: '/my' } })
    return '登录状态已失效，请重新登录。'
  }
  return error instanceof ApiError ? error.message : fallback
}

/** 根据当前类型、状态和页码加载当前用户自己的记录。 */
async function loadRecords() {
  loading.value = true
  pageError.value = ''
  try {
    const response = await fetchMyItems({
      type: selectedType.value,
      status: status.value === 'all' ? undefined : status.value,
      page: currentPage.value,
      pageSize: PAGE_SIZE,
    })
    records.value = response.items
    total.value = response.total
  } catch (error) {
    records.value = []
    total.value = 0
    pageError.value = handleRequestError(error, '无法读取个人记录，请确认后端已启动后重试。')
  } finally {
    loading.value = false
  }
}

watch([selectedType, status], () => {
  currentPage.value = 1
  void loadRecords()
})

onMounted(async () => {
  void loadLocations()
  await auth.restore()
  await loadRecords()
})

function openItem(item: ApiOwnerItem) {
  void router.push({ name: 'item-detail', params: { id: item.id } })
}

function changePage(nextPage: number) {
  if (nextPage < 1 || nextPage > totalPages.value || loading.value) return
  currentPage.value = nextPage
  void loadRecords()
}

/** 打开轻量编辑区；只提交用户实际可修改的常用字段。 */
function startEdit(item: ApiOwnerItem) {
  editing.value = item
  Object.assign(editForm, {
    title: item.title,
    category: item.category,
    description: item.description,
    location: item.location,
    contact: item.contact,
    contactNote: item.contact_note ?? '',
  })
  actionError.value = ''
}

async function saveEdit() {
  if (!editing.value || actionId.value !== null) return
  if (editForm.title.trim().length < 2 || editForm.description.trim().length < 10) {
    actionError.value = '请检查名称和描述的最小长度。'
    return
  }
  if (!isLocationSelection(locations.value, editing.value.campus, editing.value.area, editForm.location)) {
    actionError.value = '请选择当前校区和区域的地点。'
    return
  }
  const payload: UpdateItemPayload = {
    title: editForm.title.trim(),
    category: editForm.category,
    description: editForm.description.trim(),
    location: editForm.location.trim(),
    contact: editForm.contact.trim(),
    contact_note: editForm.contactNote.trim() || null,
  }
  actionId.value = editing.value.id
  actionError.value = ''
  try {
    const updated = await updateItem(editing.value.id, payload)
    const index = records.value.findIndex((item) => item.id === updated.id)
    if (index >= 0) records.value[index] = updated
    editing.value = null
  } catch (error) {
    actionError.value = handleRequestError(error, '保存失败，请稍后重试。')
  } finally {
    actionId.value = null
  }
}

/** 终态变更先由用户确认，再交由后端执行类型和状态转换校验。 */
async function finishItem(item: ApiOwnerItem, nextStatus: ItemStatus) {
  if (actionId.value !== null) return
  const label = statusLabels[nextStatus]
  if (!window.confirm(`确定将“${item.title}”标记为${label}吗？该操作完成后不能继续编辑。`)) return
  const reasonInput = window.prompt('可填写处理说明（选填，最多 255 个字）：', '')
  if (reasonInput === null) return
  const reason = reasonInput || undefined
  if (reason && reason.length > 255) {
    actionError.value = '处理说明不能超过 255 个字。'
    return
  }
  actionId.value = item.id
  actionError.value = ''
  try {
    await updateItemStatus(item.id, nextStatus, reason)
    await loadRecords()
  } catch (error) {
    actionError.value = handleRequestError(error, '状态更新失败，请稍后重试。')
  } finally {
    actionId.value = null
  }
}

async function logout() {
  actionError.value = ''
  try {
    await auth.logout()
    await router.replace({ name: 'home' })
  } catch (error) {
    actionError.value = handleRequestError(error, '退出失败，请重试。')
  }
}
</script>

<template>
  <div class="app-shell">
    <SiteHeader active-nav="我的" />
    <main class="profile-main">
      <section class="intro-section" aria-labelledby="profile-title">
        <div><p class="eyebrow">MY LOSTLINK</p><h1 id="profile-title">我的</h1><p class="intro-copy">查看和管理你发布的失物与拾物记录。</p></div>
      </section>

      <section class="profile-summary" aria-labelledby="profile-summary-title">
        <div>
          <p class="section-kicker">个人信息</p>
          <h2 id="profile-summary-title">{{ auth.user.value?.display_name || auth.user.value?.account }}</h2>
          <p>账号：{{ auth.user.value?.account }} · 角色：{{ auth.user.value?.role === 'admin' ? '管理员' : '普通用户' }}</p>
          <p class="profile-hint">校园身份：{{ auth.user.value?.campus_verified ? '已验证' : '尚未验证' }}</p>
        </div>
        <button class="secondary-button" type="button" @click="logout">退出登录</button>
      </section>

      <section class="profile-records" aria-labelledby="profile-records-title">
        <div class="results-header">
          <div><p class="section-kicker">个人记录</p><h2 id="profile-records-title">我的物品记录</h2></div>
          <div class="type-tabs" role="group" aria-label="我的记录类型">
            <button type="button" :class="{ active: selectedType === 'lost' }" @click="selectedType = 'lost'">我的失物</button>
            <button type="button" :class="{ active: selectedType === 'found' }" @click="selectedType = 'found'">我的拾物</button>
          </div>
        </div>
        <div class="profile-controls">
          <div class="filter-group"><label for="my-status">记录状态</label><select id="my-status" v-model="status"><option value="all">全部状态</option><option v-for="(label, value) in statusLabels" :key="value" :value="value">{{ label }}</option></select></div>
          <RouterLink class="primary-button profile-publish-link" :to="{ name: selectedType === 'lost' ? 'publish-lost' : 'register-found' }">{{ selectedType === 'lost' ? '发布失物' : '登记拾物' }}</RouterLink>
        </div>

        <p v-if="pageError || actionError" class="form-alert" role="alert">{{ pageError || actionError }}</p>
        <div v-if="loading" class="page-state" role="status"><span class="loading-spinner" aria-hidden="true"></span><p>正在加载个人记录…</p></div>
        <div v-else-if="records.length" class="item-grid">
          <article v-for="item in records" :key="item.id" class="profile-record">
            <ItemCard :item="toLostFoundItem(item)" @open="openItem(item)" />
            <p class="profile-record-status">状态：{{ statusLabels[item.status] }}</p>
            <div v-if="item.status === 'active'" class="record-actions">
              <button class="secondary-button" type="button" :disabled="actionId === item.id" @click="startEdit(item)">编辑</button>
              <button class="secondary-button" type="button" :disabled="actionId === item.id" @click="finishItem(item, item.type === 'lost' ? 'recovered' : 'returned')">{{ item.type === 'lost' ? '标记找回' : '标记归还' }}</button>
              <button class="text-button" type="button" :disabled="actionId === item.id" @click="finishItem(item, 'closed')">关闭记录</button>
            </div>
          </article>
        </div>
        <div v-else-if="!pageError" class="empty-state" role="status"><h3>没有符合条件的记录</h3><p>可以切换筛选条件，或者发布一条新记录。</p></div>

        <nav v-if="totalPages > 1" class="pagination" aria-label="个人记录分页"><button type="button" :disabled="currentPage === 1" @click="changePage(currentPage - 1)">上一页</button><span>第 {{ currentPage }} / {{ totalPages }} 页，共 {{ total }} 条</span><button type="button" :disabled="currentPage === totalPages" @click="changePage(currentPage + 1)">下一页</button></nav>
      </section>

      <div v-if="editing" class="edit-overlay" role="presentation" @click.self="editing = null">
        <section class="edit-dialog" role="dialog" aria-modal="true" aria-labelledby="edit-title">
          <h2 id="edit-title">编辑记录</h2>
          <div class="edit-fields">
            <label>名称<input v-model="editForm.title" maxlength="60" /></label>
            <label>类别<select v-model="editForm.category"><option v-for="category in ITEM_CATEGORIES" :key="category">{{ category }}</option></select></label>
            <label class="full">特征描述<textarea v-model="editForm.description" rows="4" maxlength="500"></textarea></label>
            <label>地点<select v-model="editForm.location" :disabled="locationsLoading || Boolean(locationsError)"><option value="">请选择地点</option><option v-for="place in editLocations" :key="place.id" :value="place.name">{{ place.name }}{{ place.simulated ? '（模拟地点）' : '' }}</option></select></label>
            <label>联系方式<input v-model="editForm.contact" /></label>
            <label class="full">联系说明<textarea v-model="editForm.contactNote" rows="2" maxlength="200"></textarea></label>
          </div>
          <p v-if="locationsLoading" class="profile-hint" role="status">正在加载地点选项…</p>
          <div v-if="locationsError" class="form-alert" role="alert"><p>{{ locationsError }}</p><button class="secondary-button" type="button" @click="loadLocations">重新加载地点</button></div>
          <p v-if="actionError" class="form-alert" role="alert">{{ actionError }}</p>
          <div class="record-actions"><button class="primary-button" type="button" :disabled="actionId !== null || locationsLoading || Boolean(locationsError)" @click="saveEdit">保存</button><button class="secondary-button" type="button" :disabled="actionId !== null" @click="editing = null">取消</button></div>
        </section>
      </div>
    </main>
  </div>
</template>

<style scoped>
.profile-summary { display:flex; justify-content:space-between; align-items:center; gap:24px; margin:28px 0 36px; padding:28px; background:var(--surface); border:1px solid var(--line); border-radius:16px; box-shadow:var(--shadow); }
.profile-summary h2 { margin:6px 0 10px; color:var(--navy); }
.profile-summary p { line-height:1.7; }
.profile-hint { color:var(--muted); font-size:.86rem; }
.profile-controls { display:flex; align-items:flex-end; justify-content:space-between; flex-wrap:wrap; gap:16px; margin:20px 0; }
.profile-controls .filter-group { width:200px; }
.profile-publish-link { text-decoration:none; }
.profile-record { padding-bottom:16px; overflow:hidden; background:var(--surface); border:1px solid var(--line); border-radius:14px; }
.profile-record :deep(.item-card) { border:0; box-shadow:none; }
.profile-record-status { padding:0 16px 12px; color:var(--muted); font-weight:700; }
.record-actions { display:flex; flex-wrap:wrap; gap:10px; padding:0 16px; }
.edit-overlay { position:fixed; inset:0; z-index:50; display:grid; place-items:center; padding:20px; background:rgba(8,35,54,.58); }
.edit-dialog { width:min(700px, 100%); max-height:90vh; overflow:auto; padding:28px; background:var(--surface); border-radius:16px; box-shadow:0 24px 70px rgba(0,0,0,.25); }
.edit-dialog h2 { margin-bottom:20px; }
.edit-fields { display:grid; grid-template-columns:1fr 1fr; gap:18px; margin-bottom:20px; }
.edit-fields label { display:grid; gap:8px; color:var(--navy); font-weight:700; }
.edit-fields input, .edit-fields select, .edit-fields textarea { width:100%; padding:11px 12px; border:1px solid #c7dae6; border-radius:8px; font:inherit; }
.edit-fields .full { grid-column:1 / -1; }
@media (max-width:640px) { .profile-summary { align-items:flex-start; flex-direction:column; } .edit-fields { grid-template-columns:1fr; } .edit-fields .full { grid-column:auto; } }
</style>
