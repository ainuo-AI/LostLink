<script setup lang="ts">
/**
 * 图片选择与预览组件
 *
 * 作用：统一完成图片格式和大小校验、IndexedDB 保存、缩略图展示、
 * 大图预览及删除。父表单只保存图片编号，不直接保存体积较大的二进制内容。
 */
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { readImage, removeImage, saveImage } from '../services/imageStore'
import { MAX_IMAGES, validateImages } from '../services/itemValidation'

const props = defineProps<{ imageIds: string[] }>()
const emit = defineEmits<{ 'update:imageIds': [ids: string[]]; error: [message: string] }>()
const input = ref<HTMLInputElement | null>(null)
const dialog = ref<HTMLDialogElement | null>(null)
const closeButton = ref<HTMLButtonElement | null>(null)
const previews = ref<Array<{ id: string; url: string }>>([])
const largeUrl = ref('')
let opener: HTMLElement | null = null
let loadSequence = 0

/**
 * 根据父组件传入的图片编号重新生成浏览器临时 URL。
 * loadSequence 用来忽略较早的异步结果，防止快速增删图片时旧结果覆盖新列表。
 */
async function refreshPreviews(ids: string[]) {
  const sequence = ++loadSequence
  const next: Array<{ id: string; url: string }> = []
  let committed = false
  try {
    for (const id of ids) {
      const blob = await readImage(id)
      if (!blob) throw new Error('有图片无法读取，请移除后重新选择。')
      next.push({ id, url: URL.createObjectURL(blob) })
    }
    if (sequence !== loadSequence) return
    previews.value.forEach((item) => URL.revokeObjectURL(item.url))
    previews.value = next
    committed = true
  } catch (error) {
    if (sequence === loadSequence) emit('error', error instanceof Error ? error.message : '图片读取失败。')
  } finally {
    // 加载失败或图片列表已变化时，释放尚未展示的临时 URL。
    if (!committed) next.forEach((item) => URL.revokeObjectURL(item.url))
  }
}

watch(() => props.imageIds, (ids) => { void refreshPreviews(ids) }, { immediate: true, deep: true })
onBeforeUnmount(() => {
  // Object URL 由浏览器占用内存，组件销毁时必须主动释放。
  ++loadSequence
  previews.value.forEach((item) => URL.revokeObjectURL(item.url))
})

/** 用户选择文件后先做前端规则校验，全部保存成功后才把编号交给父表单。 */
async function selectFiles(event: Event) {
  const files = Array.from((event.target as HTMLInputElement).files ?? [])
  if (input.value) input.value.value = '' // 允许重新选择同一个文件。
  if (!files.length) return
  const error = validateImages(files, props.imageIds.length)
  if (error) { emit('error', error); return }
  const savedIds: string[] = []
  try {
    for (const file of files) savedIds.push(await saveImage(file))
    emit('update:imageIds', [...props.imageIds, ...savedIds])
  } catch (cause) {
    await Promise.allSettled(savedIds.map(removeImage))
    emit('error', cause instanceof Error ? cause.message : '图片保存失败。')
  }
}

/** 同时删除 IndexedDB 中的图片和父表单里的图片编号。 */
async function remove(id: string) {
  try {
    await removeImage(id)
    emit('update:imageIds', props.imageIds.filter((value) => value !== id))
  } catch (error) {
    emit('error', error instanceof Error ? error.message : '图片移除失败。')
  }
}

/** 打开原生 dialog 查看大图，并记录打开按钮，以便关闭后恢复键盘焦点。 */
async function openLarge(url: string, event: Event) {
  opener = event.currentTarget as HTMLElement
  largeUrl.value = url
  dialog.value?.showModal()
  await nextTick()
  closeButton.value?.focus()
}

function closeLarge() { dialog.value?.close() }
function restoreFocus() { opener?.focus(); opener = null }
</script>

<template>
  <!-- 该组件通过 update:imageIds 与父表单双向同步，不直接提交整张表单。 -->
  <div class="image-picker">
    <label for="demo-images">物品图片 <span class="optional">选填</span></label>
    <p id="image-rules" class="form-help">仅支持 JPG、PNG、WebP；每张不超过 5MB，最多 3 张。图片只保存在本地浏览器。</p>
    <input id="demo-images" ref="input" type="file" accept="image/jpeg,image/png,image/webp" multiple :disabled="imageIds.length >= MAX_IMAGES" aria-describedby="image-rules" @change="selectFiles" />
    <div v-if="previews.length" class="image-preview-grid">
      <div v-for="preview in previews" :key="preview.id" class="image-preview">
        <button type="button" :aria-label="'查看图片大图'" @click="openLarge(preview.url, $event)"><img :src="preview.url" alt="所选物品图片预览" /></button>
        <button type="button" class="image-remove" aria-label="移除图片" @click="remove(preview.id)">移除</button>
      </div>
    </div>
    <dialog ref="dialog" class="image-dialog" aria-label="图片大图预览" @close="restoreFocus">
      <button ref="closeButton" type="button" class="image-dialog-close" @click="closeLarge">关闭预览</button>
      <img :src="largeUrl" alt="所选物品图片大图" />
    </dialog>
  </div>
</template>
