<script setup lang="ts">
/**
 * 发布失物与登记拾物共用表单
 *
 * 通过 type 区分 lost 和 found：两种业务共享物品、地点、图片和联系字段，
 * 拾物模式再条件展示保管方式等字段，避免复制两套几乎相同的页面代码。
 */
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRouter } from 'vue-router'
import ImagePicker from './ImagePicker.vue'
import SiteHeader from './SiteHeader.vue'
import { clearDraft, loadDraft, saveDraft } from '../services/localItems'
import { emptyDraft, validateDraft } from '../services/itemValidation'
import { readImage, removeImage } from '../services/imageStore'
import { ITEM_CATEGORIES, type DraftErrors, type DraftField, type ItemDraft } from '../types/demo'
import type { ApiOwnerItem, Campus, CreateItemPayload, RecordType } from '../types/item'
import { createItem } from '../api/items'
import { ApiError } from '../api/client'
import { deleteUploadedImage, uploadImage } from '../api/media'
import { useAuth } from '../stores/auth'
import { locationOptions, isLocationSelection, useCampusLocations } from '../services/campusLocations'

const props = defineProps<{ type: RecordType }>()
const router = useRouter()
const { clearSession } = useAuth()
const isFound = computed(() => props.type === 'found')
const draft = reactive<ItemDraft>(emptyDraft())
const { choices: locations, loading: locationsLoading, error: locationsError, load: loadLocations } = useCampusLocations()
const availableLocations = computed(() => locationOptions(locations.value, draft.campus, draft.area))
const storageLocations = computed(() => locationOptions(locations.value, draft.campus, null, true))
const errors = reactive<DraftErrors>({})
const loading = ref(true)
const submitting = ref(false)
const formError = ref('')
const storageWarning = ref('')
const success = ref<ApiOwnerItem | null>(null)
let hydrated = false
let suppressSave = false

// hasContent 同时服务于“重置确认”和“离开页面提醒”。
const hasContent = computed(() => Object.entries(draft).some(([key, value]) => key !== 'imageIds' ? Boolean(String(value).trim()) : (value as string[]).length > 0))
// 与页面的视觉顺序一致，提交失败时键盘焦点落到第一个错误字段。
const fieldOrder: DraftField[] = ['title', 'category', 'description', 'imageIds', 'campus', 'area', 'location', 'occurredAt', 'storageMethod', 'storageLocation', 'contact', 'contactWindow', 'contactNote']

/** 页面进入时读取对应业务类型的本地草稿，失物和拾物草稿不会串用。 */
async function hydrate() {
  loading.value = true
  storageWarning.value = ''
  await loadLocations()
  try {
    const saved = await loadDraft(props.type)
    if (saved) Object.assign(draft, emptyDraft(), saved)
    if (draft.campus !== '东丽校区') draft.area = ''
    clearInvalidLocations()
  } catch (error) {
    storageWarning.value = error instanceof Error ? error.message : '草稿读取失败。'
  } finally {
    hydrated = true
    loading.value = false
  }
}

watch(() => draft.campus, (campus) => {
  // 宁河校区不分南北区，切换校区时清除旧的东丽区域值。
  if (campus !== '东丽校区') draft.area = ''
})

function clearInvalidLocations() {
  if (!locations.value.length) return
  if (!isLocationSelection(locations.value, draft.campus, draft.area, draft.location)) draft.location = ''
  if (!isLocationSelection(locations.value, draft.campus, null, draft.storageLocation, true)) draft.storageLocation = ''
}
watch([locations, () => draft.campus, () => draft.area], clearInvalidLocations)

// 深度监听表单字段并自动保存草稿；重置和提交成功时暂时关闭自动保存。
watch(draft, () => {
  if (!hydrated || suppressSave || success.value) return
  void saveDraft(props.type, { ...draft, imageIds: [...draft.imageIds] }).then(() => { storageWarning.value = '' }).catch((error: unknown) => {
    storageWarning.value = error instanceof Error ? error.message : '草稿保存失败。'
  })
}, { deep: true })

onMounted(() => {
  void hydrate()
  window.addEventListener('beforeunload', warnBeforeUnload)
})
onBeforeUnmount(() => window.removeEventListener('beforeunload', warnBeforeUnload))

function warnBeforeUnload(event: BeforeUnloadEvent) {
  // 浏览器刷新或关闭标签页时，交给浏览器显示标准离开提示。
  if (hasContent.value && !success.value) event.preventDefault()
}

onBeforeRouteLeave(() => {
  // Vue Router 页面切换时使用项目自己的中文确认文案。
  if (hasContent.value && !success.value && !window.confirm('表单尚未提交，确定离开当前页面吗？草稿会保留在本地。')) return false
})

function setError(field: DraftField, message: string) {
  errors[field] = message
}

async function focusFirstError() {
  const first = fieldOrder.find((field) => errors[field])
  await nextTick()
  document.getElementById(first === 'imageIds' ? 'demo-images' : `entry-${first}`)?.focus()
}

/**
 * 提交流程：字段校验 → 上传暂存图片 → 调用发布接口关联图片 → 清空本地草稿。
 * 任一步失败都会保留用户已填写内容，并显示可重试的错误信息。
 */
async function submit() {
  if (submitting.value) return
  Object.keys(errors).forEach((key) => delete errors[key as DraftField])
  Object.assign(errors, validateDraft(draft, props.type, new Date(), locations.value))
  if (Object.keys(errors).length) { await focusFirstError(); return }
  const localImages: Array<{ id: string; blob: Blob }> = []
  try {
    // 草稿恢复后再次核对 IndexedDB；图片丢失或不可读时不能假装提交成功。
    for (const id of draft.imageIds) {
      const blob = await readImage(id)
      if (!blob) throw new Error('有图片无法读取，请移除后重新选择。')
      localImages.push({ id, blob })
    }
  } catch (error) {
    setError('imageIds', error instanceof Error ? error.message : '图片读取失败。')
    await focusFirstError()
    return
  }
  formError.value = ''
  submitting.value = true
  const uploadedIds: string[] = []
  try {
    for (const [index, image] of localImages.entries()) {
      const uploaded = await uploadImage(
        image.blob,
        `item-${index + 1}.${image.blob.type.split('/')[1] || 'jpg'}`,
      )
      uploadedIds.push(uploaded.id)
    }
    const payload: CreateItemPayload = {
      type: props.type,
      category: draft.category,
      title: draft.title.trim(),
      description: draft.description.trim(),
      location: draft.location.trim(),
      // 前面的 validateDraft 已确认该值是受支持的校区枚举。
      campus: draft.campus as Campus,
      area: draft.area || null,
      // datetime-local 按浏览器本地时区解析，再转为后端要求的带时区 ISO 时间。
      occurred_at: new Date(draft.occurredAt).toISOString(),
      contact: draft.contact.trim(),
      contact_note: draft.contactNote.trim() || null,
      storage_method: isFound.value ? draft.storageMethod || null : null,
      storage_location: isFound.value ? draft.storageLocation.trim() || null : null,
      contact_window: isFound.value ? draft.contactWindow.trim() || null : null,
      image_ids: uploadedIds,
    }
    const record = await createItem(payload)
    success.value = record
    suppressSave = true
    await Promise.allSettled(localImages.map(image => removeImage(image.id)))
    Object.assign(draft, emptyDraft())
    try { await clearDraft(props.type) } catch { storageWarning.value = '记录已保存，但旧草稿未能清除。' }
    await nextTick()
    document.getElementById('entry-success-title')?.focus()
  } catch (error) {
    // 物品未创建时，回收服务端临时上传；本地草稿和图片保留供用户重试。
    await Promise.allSettled(uploadedIds.map(deleteUploadedImage))
    if (error instanceof ApiError && error.status === 401) {
      clearSession()
      await router.replace({ name: 'login', query: { redirect: router.currentRoute.value.fullPath } })
      return
    }
    formError.value = error instanceof ApiError
      ? error.message
      : '无法连接发布服务，请确认后端已启动后重试。'
  } finally {
    submitting.value = false
    suppressSave = false
  }
}

/** 重置前征求确认，并清理草稿字段及 IndexedDB 中对应的本地图片。 */
async function reset() {
  if (hasContent.value && !window.confirm('确定清空当前表单和已选图片吗？此操作不可恢复。')) return
  formError.value = ''
  try {
    await clearDraft(props.type)
    const ids = [...draft.imageIds]
    suppressSave = true
    Object.assign(draft, emptyDraft())
    Object.keys(errors).forEach((key) => delete errors[key as DraftField])
    const removal = await Promise.allSettled(ids.map(removeImage))
    storageWarning.value = removal.some((result) => result.status === 'rejected') ? '表单已重置，但部分本地图片未能清理。' : ''
  } catch (error) {
    formError.value = error instanceof Error ? error.message : '无法清除草稿。'
  } finally {
    suppressSave = false
  }
}

function continueEntry() { success.value = null }
function imageError(message: string) { setError('imageIds', message) }
function updateImages(ids: string[]) { draft.imageIds = ids; delete errors.imageIds }
</script>

<template>
  <div class="app-shell">
      <SiteHeader :active-nav="isFound ? '登记拾物' : '发布失物'" />
    <main class="entry-main">
      <div class="entry-heading">
        <p class="section-kicker">{{ isFound ? 'FOUND ITEM' : 'LOST ITEM' }}</p>
        <h1>{{ isFound ? '登记拾物' : '发布失物' }}</h1>
        <p>{{ isFound ? '记录拾获信息，帮助失主核验线索。' : '详细描述遗失物品，让其他同学更容易发现线索。' }}</p>
        <p class="demo-notice">提交后将写入服务器；所选图片会在发布时上传并关联到该记录。</p>
      </div>

      <div v-if="loading" class="page-state" role="status"><span class="loading-spinner" aria-hidden="true"></span><p>正在读取本地草稿…</p></div>

      <section v-else-if="success" class="entry-success" aria-labelledby="entry-success-title">
        <span class="success-mark" aria-hidden="true">✓</span>
        <h2 id="entry-success-title" tabindex="-1">{{ isFound ? '拾物登记成功' : '失物发布成功' }}</h2>
        <p>服务器记录编号：<strong>{{ success.id }}</strong></p>
        <p>{{ success.title }} · {{ success.campus }}{{ success.area ? ` ${success.area}` : '' }} · {{ success.location }}</p>
        <p>状态：进行中。你可以在“我的”页面查看和管理这条记录。</p>
        <div class="entry-actions"><button class="secondary-button" type="button" @click="continueEntry">{{ isFound ? '继续登记' : '继续发布' }}</button><RouterLink class="primary-button action-link" :to="{ name: 'home' }">返回首页</RouterLink></div>
      </section>

      <!-- success、loading 和 form 三种状态互斥，防止提交结果与编辑表单同时出现。 -->
      <form v-else class="entry-form" novalidate @submit.prevent="submit">
        <p v-if="storageWarning" class="form-alert" role="alert">{{ storageWarning }}</p>
        <section class="entry-section" aria-labelledby="entry-basic-title">
          <div class="entry-section-heading"><span>01</span><div><h2 id="entry-basic-title">物品信息</h2><p>名称、类别和外观特征有助于核对。</p></div></div>
          <div class="entry-fields">
            <div class="entry-field"><label for="entry-title">物品名称 <span>*</span></label><input id="entry-title" v-model="draft.title" maxlength="60" placeholder="例如：黑色双肩包" :aria-invalid="Boolean(errors.title)" :aria-describedby="errors.title ? 'entry-title-error' : undefined" /><p v-if="errors.title" id="entry-title-error" class="field-error" role="alert">{{ errors.title }}</p></div>
            <div class="entry-field"><label for="entry-category">物品类别 <span>*</span></label><select id="entry-category" v-model="draft.category" :aria-invalid="Boolean(errors.category)" :aria-describedby="errors.category ? 'entry-category-error' : undefined"><option value="">请选择类别</option><option v-for="category in ITEM_CATEGORIES" :key="category" :value="category">{{ category }}</option></select><p v-if="errors.category" id="entry-category-error" class="field-error" role="alert">{{ errors.category }}</p></div>
            <div class="entry-field full"><label for="entry-description">特征描述 <span>*</span></label><textarea id="entry-description" v-model="draft.description" rows="5" maxlength="500" placeholder="写明颜色、品牌、外观和独有标记（至少 10 个字）" :aria-invalid="Boolean(errors.description)" :aria-describedby="errors.description ? 'entry-description-error' : undefined"></textarea><p v-if="errors.description" id="entry-description-error" class="field-error" role="alert">{{ errors.description }}</p></div>
            <div class="entry-field full"><ImagePicker :image-ids="draft.imageIds" @update:image-ids="updateImages" @error="imageError" /><p class="profile-hint">图片仅供本地预览；服务端上传开放前，提交时必须移除所有图片。</p><p v-if="errors.imageIds" class="field-error" role="alert">{{ errors.imageIds }}</p></div>
          </div>
        </section>

        <!-- 地点和时间区根据业务类型自动切换“丢失”或“拾获”文案。 -->
        <section class="entry-section" aria-labelledby="entry-location-title">
          <div class="entry-section-heading"><span>02</span><div><h2 id="entry-location-title">{{ isFound ? '拾获信息' : '丢失信息' }}</h2><p>请填写尽可能准确的校区、地点和时间。</p></div></div>
          <p v-if="locationsLoading" class="profile-hint" role="status">正在加载地点选项…</p>
          <div v-if="locationsError" class="form-alert" role="alert"><p>{{ locationsError }}</p><button class="secondary-button" type="button" @click="loadLocations">重新加载地点</button></div>
          <div class="entry-fields">
            <div class="entry-field"><label for="entry-campus">{{ isFound ? '拾获校区' : '丢失校区' }} <span>*</span></label><select id="entry-campus" v-model="draft.campus" :aria-invalid="Boolean(errors.campus)"><option value="">请选择校区</option><option value="东丽校区">东丽校区</option><option value="宁河校区">宁河校区</option></select><p v-if="errors.campus" class="field-error" role="alert">{{ errors.campus }}</p></div>
            <div v-if="draft.campus === '东丽校区'" class="entry-field"><label for="entry-area">校区区域 <span>*</span></label><select id="entry-area" v-model="draft.area" :aria-invalid="Boolean(errors.area)"><option value="">请选择区域</option><option value="北区">北区</option><option value="南区">南区</option></select><p v-if="errors.area" class="field-error" role="alert">{{ errors.area }}</p></div>
            <div class="entry-field"><label for="entry-location">{{ isFound ? '具体拾获地点' : '具体丢失地点' }} <span>*</span></label><select id="entry-location" v-model="draft.location" :disabled="locationsLoading || Boolean(locationsError) || !draft.campus || (draft.campus === '东丽校区' && !draft.area)" :aria-invalid="Boolean(errors.location)"><option value="">{{ !draft.campus ? '请先选择校区' : draft.campus === '东丽校区' && !draft.area ? '请先选择区域' : '请选择地点' }}</option><option v-for="place in availableLocations" :key="place.id" :value="place.name">{{ place.name }}{{ place.simulated ? '（模拟地点）' : '' }}</option></select><p v-if="errors.location" class="field-error" role="alert">{{ errors.location }}</p></div>
            <div class="entry-field"><label for="entry-occurredAt">{{ isFound ? '拾获时间' : '丢失时间' }} <span>*</span></label><input id="entry-occurredAt" v-model="draft.occurredAt" type="datetime-local" :aria-invalid="Boolean(errors.occurredAt)" /><p v-if="errors.occurredAt" class="field-error" role="alert">{{ errors.occurredAt }}</p></div>
          </div>
        </section>

        <!-- 拾物模式比失物模式多出保管方式、保管地点和可联系时间。 -->
        <section class="entry-section" aria-labelledby="entry-contact-title">
          <div class="entry-section-heading"><span>03</span><div><h2 id="entry-contact-title">{{ isFound ? '保管与联系' : '联系方式' }}</h2><p>联系方式将在物品记录中直接展示，方便对方联系你。</p></div></div>
          <div class="entry-fields">
            <template v-if="isFound">
              <div class="entry-field"><label for="entry-storageMethod">保管方式 <span>*</span></label><select id="entry-storageMethod" v-model="draft.storageMethod" :aria-invalid="Boolean(errors.storageMethod)"><option value="">请选择方式</option><option value="self">本人暂存</option><option value="office">交至失物招领处</option></select><p v-if="errors.storageMethod" class="field-error" role="alert">{{ errors.storageMethod }}</p></div>
              <div v-if="draft.storageMethod" class="entry-field"><label for="entry-storageLocation">{{ draft.storageMethod === 'self' ? '暂存地点' : '交存地点' }} <span>*</span></label><select id="entry-storageLocation" v-model="draft.storageLocation" :disabled="locationsLoading || Boolean(locationsError) || !draft.campus" :aria-invalid="Boolean(errors.storageLocation)"><option value="">{{ draft.campus ? '请选择保管地点' : '请先选择校区' }}</option><option v-for="place in storageLocations" :key="place.id" :value="place.name">{{ place.area ? `${place.area} · ` : '' }}{{ place.name }}{{ place.simulated ? '（模拟地点）' : '' }}</option></select><p v-if="errors.storageLocation" class="field-error" role="alert">{{ errors.storageLocation }}</p></div>
            </template>
            <div class="entry-field"><label for="entry-contact">手机号或邮箱 <span>*</span></label><input id="entry-contact" v-model="draft.contact" autocomplete="off" placeholder="请输入手机号或邮箱" :aria-invalid="Boolean(errors.contact)" /><p v-if="errors.contact" class="field-error" role="alert">{{ errors.contact }}</p></div>
            <div v-if="isFound" class="entry-field"><label for="entry-contactWindow">可联系时间或范围 <span>*</span></label><input id="entry-contactWindow" v-model="draft.contactWindow" maxlength="100" placeholder="例如：工作日 12:00–18:00" :aria-invalid="Boolean(errors.contactWindow)" /><p v-if="errors.contactWindow" class="field-error" role="alert">{{ errors.contactWindow }}</p></div>
            <div class="entry-field full"><label for="entry-contactNote">联系说明 <span class="optional">选填</span></label><textarea id="entry-contactNote" v-model="draft.contactNote" rows="3" maxlength="200" placeholder="例如：请先说明物品上的独有标记" :aria-invalid="Boolean(errors.contactNote)"></textarea><p v-if="errors.contactNote" class="field-error" role="alert">{{ errors.contactNote }}</p></div>
          </div>
        </section>
        <p v-if="formError" class="form-alert" role="alert">{{ formError }}</p>
        <div class="entry-actions"><button class="primary-button" type="submit" :disabled="submitting || locationsLoading || Boolean(locationsError)">{{ submitting ? '正在保存…' : isFound ? '提交登记' : '提交发布' }}</button><button class="secondary-button" type="button" :disabled="submitting" @click="reset">重置</button><button class="text-button" type="button" :disabled="submitting" @click="router.push({ name: 'home' })">取消并返回</button></div>
      </form>
    </main>
  </div>
</template>
