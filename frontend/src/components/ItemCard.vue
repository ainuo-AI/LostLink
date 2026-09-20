<script setup lang="ts">
import type { LostFoundItem } from '../types/item'

defineProps<{
  item: LostFoundItem
}>()

// 卡片只负责展示数据；点击时将完整 item 传给父组件。
defineEmits<{
  open: [item: LostFoundItem]
}>()
</script>

<template>
  <article class="item-card" tabindex="0" @keyup.enter="$emit('open', item)">
    <button class="card-main" type="button" :aria-label="`查看 ${item.title} 详情`" @click="$emit('open', item)">
      <!-- CSS 变量 --item-color 让卡片共用布局，同时保留不同的主题色。 -->
      <div class="item-visual" :style="{ '--item-color': item.color }">
        <span class="item-icon" aria-hidden="true">{{ item.icon }}</span>
        <span class="visual-location">{{ item.area ? `${item.campus} · ${item.area}` : item.campus }}</span>
      </div>

      <div class="card-content">
        <div class="card-label-row">
          <!-- 根据记录类型动态设置文案和 CSS 类名。 -->
          <span :class="['type-label', item.type]">{{ item.type === 'lost' ? '失物' : '拾物' }}</span>
          <span class="category-label">{{ item.category }}</span>
        </div>
        <h3>{{ item.title }}</h3>
        <p class="description">{{ item.description }}</p>
        <div class="card-meta">
          <span><span aria-hidden="true">⌖</span> {{ item.location }}</span>
          <span>{{ item.displayTime }}</span>
        </div>
      </div>
    </button>
    <button class="detail-link" type="button" @click="$emit('open', item)">
      查看详情 <span aria-hidden="true">↗</span>
    </button>
  </article>
</template>
