<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import type { LostFoundItem } from '../types/item'

const props = defineProps<{
  item: LostFoundItem
}>()

const emit = defineEmits<{
  close: []
}>()

// 支持按 Esc 键关闭弹窗，让键盘用户也能完成操作。
function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') emit('close')
}

onMounted(() => {
  // 弹窗打开时禁止背景页面滚动。
  document.body.classList.add('modal-open')
  window.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  // 组件销毁时清理全局样式和事件，避免内存泄漏。
  document.body.classList.remove('modal-open')
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <!-- @mousedown.self 表示只有点击遮罩本身才关闭，点击内容区不会误关闭。 -->
  <div class="dialog-backdrop" role="presentation" @mousedown.self="$emit('close')">
    <section class="detail-dialog" role="dialog" aria-modal="true" :aria-labelledby="`item-title-${props.item.id}`">
      <button class="dialog-close" type="button" aria-label="关闭详情" @click="$emit('close')">×</button>
      <div class="dialog-visual" :style="{ '--item-color': props.item.color }">
        <span aria-hidden="true">{{ props.item.icon }}</span>
      </div>
      <div class="dialog-content">
        <span :class="['type-label', props.item.type]">{{ props.item.type === 'lost' ? '寻物启事' : '拾物信息' }}</span>
        <h2 :id="`item-title-${props.item.id}`">{{ props.item.title }}</h2>
        <p class="dialog-description">{{ props.item.description }}</p>
        <dl class="detail-list">
          <div>
            <dt>物品类别</dt>
            <dd>{{ props.item.category }}</dd>
          </div>
          <div>
            <dt>地点</dt>
            <dd>
              {{ props.item.area ? `${props.item.campus} · ${props.item.area}` : props.item.campus }}
              · {{ props.item.location }}
            </dd>
          </div>
          <div>
            <dt>时间</dt>
            <dd>{{ props.item.displayTime }}</dd>
          </div>
          <div>
            <dt>联系提示</dt>
            <dd>{{ props.item.contactHint }}</dd>
          </div>
        </dl>
        <button class="primary-button wide" type="button">
          {{ props.item.type === 'lost' ? '我可能找到了' : '这可能是我的' }}
        </button>
      </div>
    </section>
  </div>
</template>
