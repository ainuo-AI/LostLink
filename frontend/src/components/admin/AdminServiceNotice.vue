<script setup lang="ts">
defineProps<{ title: string; description: string }>()
</script>

<template>
  <div class="admin-service-state" role="status">
    <span class="admin-service-mark" aria-hidden="true">—</span>
    <h2>{{ title }}暂未接入</h2>
    <p>{{ description }}</p>
    <RouterLink class="secondary-button auth-link-button" :to="{ name: 'login' }">返回登录</RouterLink>
  </div>
</template>
