<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import HomeView from './views/HomeView.vue'
import LoginView from './views/LoginView.vue'
import RegisterView from './views/RegisterView.vue'
import MyView from './views/MyView.vue'
import AdminConsole from './views/admin/AdminConsole.vue'
import { isAdminPath, isAdminPreviewPath, readAdminSection } from './router/admin'
import './styles/auth.css'

function readPage() {
  if (isAdminPath(window.location.hash)) return 'admin'
  if (import.meta.env.DEV && isAdminPreviewPath(window.location.hash)) return 'admin-preview'
  if (window.location.hash === '#/my') return 'my'
  if (import.meta.env.DEV && window.location.hash === '#/my-preview') return 'my-preview'
  if (window.location.hash === '#/login') return 'login'
  if (window.location.hash === '#/register') return 'register'
  return 'home'
}

const page = ref(readPage())
const profileRequested = ref(false)
const adminRequested = ref(false)
const adminSection = ref(readAdminSection(window.location.hash))

function updatePage() {
  const nextPage = readPage()
  if (nextPage === 'admin') {
    // 管理端认证与会话确认接口缺失，不依据前端角色或演示模式授予访问资格。
    adminRequested.value = true
    profileRequested.value = false
    page.value = 'login'
    window.location.replace('#/login')
    return
  }
  if (nextPage === 'my') {
    // 当前没有会话确认接口，不能将访问个人页视为已登录。
    profileRequested.value = true
    adminRequested.value = false
    page.value = 'login'
    window.location.replace('#/login')
    return
  }
  page.value = nextPage
  adminSection.value = readAdminSection(window.location.hash)
  if (nextPage !== 'login') {
    profileRequested.value = false
    adminRequested.value = false
  }
}

updatePage()

function openLogin() {
  profileRequested.value = false
  adminRequested.value = false
  window.location.hash = '/login'
}

function openProfile() {
  window.location.hash = '/my'
}

watch([page, adminSection], async () => {
  await nextTick()
  document.querySelector<HTMLElement>('main h1')?.focus({ preventScroll: true })
  window.scrollTo(0, 0)
})

onMounted(() => window.addEventListener('hashchange', updatePage))
onBeforeUnmount(() => window.removeEventListener('hashchange', updatePage))
</script>

<template>
  <HomeView v-if="page === 'home'" @login="openLogin" @profile="openProfile" />
  <LoginView v-else-if="page === 'login'" :profile-requested="profileRequested" :admin-requested="adminRequested" />
  <RegisterView v-else-if="page === 'register'" />
  <MyView v-else-if="page === 'my-preview'" />
  <AdminConsole v-else-if="page === 'admin-preview'" :section="adminSection" />
</template>
