<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { adminSections, type AdminSection } from '../router/admin'
import { useAuth } from '../stores/auth'

defineProps<{ section: AdminSection }>()
const menuOpen = ref(false)
const router = useRouter()
const auth = useAuth()

/** 注销管理员会话并返回登录页。 */
async function logout() {
  await auth.logout()
  await router.replace({ name: 'login' })
}
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
        <RouterLink v-for="(item, index) in adminSections" :key="item.id" :to="{ name: 'admin', params: { section: item.id } }" :class="{ active: section === item.id }" :aria-current="section === item.id ? 'page' : undefined" @click="menuOpen = false">
          <span aria-hidden="true">0{{ index + 1 }}</span>{{ item.label }}
        </RouterLink>
      </nav>
      <RouterLink class="admin-campus-link" :to="{ name: 'home' }">返回校园首页</RouterLink>
    </aside>
    <div class="admin-body">
      <header class="admin-topbar">
        <span>校园管理工作区</span>
        <div><span class="admin-muted">{{ auth.user.value?.display_name || auth.user.value?.account }} · 管理员</span><button class="secondary-button" type="button" @click="logout">退出登录</button></div>
      </header>
      <main class="admin-workspace">
        <slot />
      </main>
    </div>
  </div>
</template>
