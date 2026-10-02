<script setup lang="ts">
import AuthLayout from '../components/AuthLayout.vue'

defineProps<{
  profileRequested?: boolean
  adminRequested?: boolean
}>()

const isDevelopment = import.meta.env.DEV
</script>

<template>
  <AuthLayout title="登录 LostLink" description="欢迎回来，让校园里的线索再次相连。">
    <p class="auth-service-note">登录服务暂未接入，你仍可以浏览首页的失物与拾物记录。</p>
    <p v-if="profileRequested" class="auth-service-note" role="status">查看“我的”需要登录。认证服务暂未接入，当前无法确认会话或加载个人数据。</p>
    <p v-if="adminRequested" class="auth-service-note" role="status">管理控制台需要管理员权限。认证与权限服务暂未接入，当前无法确认会话或访问管理数据。</p>
    <button class="primary-button wide" type="button" disabled>登录（暂未开放）</button>
    <div class="auth-register-entry">
      <p>还没有账号？</p>
      <RouterLink class="secondary-button auth-link-button" :to="{ name: 'register' }">注册账号</RouterLink>
    </div>
    <p v-if="isDevelopment" class="auth-switch"><RouterLink :to="{ name: 'my-preview' }">开发预览：我的页面（非登录状态）</RouterLink></p>
    <p v-if="isDevelopment" class="auth-switch"><RouterLink :to="{ name: 'admin-preview', params: { section: 'overview' } }">开发预览：管理控制台（非管理员会话）</RouterLink></p>
  </AuthLayout>
</template>
