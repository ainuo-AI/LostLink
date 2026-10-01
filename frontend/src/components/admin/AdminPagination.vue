<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ page: number; total?: number }>()
defineEmits<{ change: [page: number] }>()
const totalPages = computed(() => props.total === undefined ? 0 : Math.max(1, Math.ceil(props.total / 5)))
</script>

<template>
  <nav class="pagination admin-pagination" aria-label="管理列表分页">
    <button type="button" :disabled="!totalPages || page === 1" @click="$emit('change', page - 1)">上一页</button>
    <span aria-live="polite">{{ total === undefined ? '分页服务暂未接入' : `演示数据：第 ${page} / ${totalPages} 页` }}</span>
    <button type="button" :disabled="!totalPages || page >= totalPages" @click="$emit('change', page + 1)">下一页</button>
  </nav>
</template>
