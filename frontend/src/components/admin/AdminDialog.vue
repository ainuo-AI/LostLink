<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, useId } from 'vue'
defineProps<{ title: string }>()
const emit = defineEmits<{ close: [] }>()
const dialog = ref<HTMLDialogElement | null>(null)
const titleId = useId()
let previousFocus: HTMLElement | null = null
function keepFocus(event: KeyboardEvent) {
  if (event.key !== 'Tab') return
  const controls = dialog.value?.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), a[href]')
  if (!controls?.length) return
  const first = controls[0]
  const last = controls[controls.length - 1]
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last?.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first?.focus()
  }
}
onMounted(() => {
  previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null
  dialog.value?.showModal()
})
onBeforeUnmount(() => {
  dialog.value?.close()
  if (previousFocus?.isConnected) previousFocus.focus()
})
</script>

<template>
  <dialog ref="dialog" class="admin-dialog" :aria-labelledby="titleId" @cancel.prevent="emit('close')" @keydown="keepFocus">
    <div class="admin-dialog-heading">
      <h2 :id="titleId">{{ title }}</h2>
      <button class="admin-inline-button" type="button" autofocus aria-label="关闭管理弹窗" @click="emit('close')">关闭</button>
    </div>
    <p class="admin-demo-caption">开发演示 · 非真实管理数据，所有写操作未接入</p>
    <slot />
  </dialog>
</template>
