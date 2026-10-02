<script setup lang="ts">
import { ref } from 'vue'
import { adminSections, type AdminSection } from '../router/admin'

defineProps<{
  section: AdminSection
  demoEnabled: boolean
  demoReady: boolean
}>()
defineEmits<{ toggleDemo: [] }>()
const menuOpen = ref(false)
</script>

<template>
  <div class="admin-shell">
    <aside class="admin-sidebar">
      <div class="admin-brand-row">
        <RouterLink class="brand" :to="{ name: 'home' }" aria-label="返回 LostLink 校园首页">
          <span class="brand-mark" aria-hidden="true"><span class="brand-link brand-link-a"></span><span class="brand-link brand-link-b"></span></span>
          <span>LostLink</span>
        </RouterLink>
        <button class="admin-menu-toggle" type="button" :aria-expanded="menuOpen" aria-controls="admin-nav" @click="menuOpen = !menuOpen">管理菜单</button>
      </div>
      <p class="admin-sidebar-caption">管理控制台</p>
      <nav id="admin-nav" :class="['admin-nav', { open: menuOpen }]" aria-label="管理导航">
        <RouterLink v-for="(item, index) in adminSections" :key="item.id" :to="{ name: 'admin-preview', params: { section: item.id } }" :class="{ active: section === item.id }" :aria-current="section === item.id ? 'page' : undefined" @click="menuOpen = false">
          <span aria-hidden="true">0{{ index + 1 }}</span>{{ item.label }}
        </RouterLink>
      </nav>
      <RouterLink class="admin-campus-link" :to="{ name: 'home' }">返回校园首页</RouterLink>
    </aside>
    <div class="admin-body">
      <header class="admin-topbar">
        <span>校园管理工作区</span>
        <div><span class="admin-muted">身份与权限未确认</span><button class="secondary-button" type="button" disabled aria-describedby="admin-logout-note">退出登录</button></div>
      </header>
      <main class="admin-workspace">
        <aside class="admin-preview-banner" aria-label="管理端开发预览说明">
          <div>
            <strong>开发预览 · 非管理员会话</strong>
            <p>管理服务暂未接入，不能读取真实数据或执行操作。{{ demoEnabled ? '当前数据为虚构演示，字段与状态不代表接口契约。' : '默认展示服务未接入状态，可单独查看演示数据。' }}</p>
            <p id="admin-logout-note">退出登录服务暂未接入；演示开关不授予管理员权限。</p>
          </div>
          <button class="secondary-button" type="button" :disabled="!demoReady" :aria-pressed="demoEnabled" @click="$emit('toggleDemo')">{{ demoEnabled ? '收起演示数据' : '查看演示数据（非真实数据）' }}</button>
        </aside>
        <slot />
      </main>
    </div>
  </div>
</template>
