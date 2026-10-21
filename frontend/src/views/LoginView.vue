<script setup lang="ts">
// 设计文档对照：04_LostLink软件设计规格说明书.docx；以下“设计文档对应”使用该文档图表编号。
// 文档对照：03_LostLink软件需求规格说明书.docx；图表编号以当前文档为准。
/** 登录页负责收集凭据并把成功会话交给全站认证 Store。 */
import { computed, nextTick, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AuthLayout from '../components/AuthLayout.vue'
import { ApiError } from '../api/client'
import { useAuth } from '../stores/auth'

defineProps<{
  profileRequested?: boolean
  protectedRequested?: boolean
  adminRequested?: boolean
}>()

const route = useRoute()
const router = useRouter()
const { login } = useAuth()
// 设计文档对应：图3-2-1、图4-2 登录界面的账号、密码及提交状态。
const account = ref(typeof route.query.account === 'string' ? route.query.account : '')
const password = ref('')
const showPassword = ref(false)
const accountError = ref('')
const passwordError = ref('')
const submitError = ref('')
const submitting = ref(false)
const registered = computed(() => route.query.registered === '1')

function readableError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === 'AUTHENTICATION_FAILED') return '账号或密码错误，或账号暂时无法登录。'
    if (error.code === 'ACCOUNT_RESTRICTED') return '账号当前受限，无法登录。'
    return error.message
  }
  return '无法连接登录服务，请确认后端已启动后重试。'
}

// 文档对应：图2-2-1 用户登录；图2-3 用户认证界面；2.2.1节。
// 设计文档对应：图4-1-2、图3-3-1 提交凭据，成功后恢复 redirect 或进入个人中心。
async function submitLogin() {
  if (submitting.value) return
  accountError.value = account.value.trim() ? '' : '请输入校园账号'
  passwordError.value = password.value ? '' : '请输入密码'
  submitError.value = ''
  const invalidId = accountError.value ? 'login-account' : passwordError.value ? 'login-password' : ''
  if (invalidId) {
    await nextTick()
    document.getElementById(invalidId)?.focus()
    return
  }

  submitting.value = true
  try {
    await login({ account: account.value.trim(), password: password.value })
    password.value = ''
    const redirect = typeof route.query.redirect === 'string' && route.query.redirect.startsWith('/')
      ? route.query.redirect
      : '/my'
    await router.replace(redirect)
  } catch (error) {
    submitError.value = readableError(error)
    password.value = ''
    await nextTick()
    document.getElementById('login-password')?.focus()
  } finally {
    submitting.value = false
  }
}
</script>

<!-- 设计文档对应：图3-1-1、图3-2-1 登录外观；密码切换与导航命令由模板事件和 RouterLink 实现。 -->
<template>
  <AuthLayout title="登录 LostLink" description="欢迎回来，让校园里的线索再次相连。">
    <p v-if="registered" class="auth-success-note" role="status">账号注册成功，请使用新账号登录。</p>
    <p v-if="profileRequested" class="auth-service-note" role="status">查看“我的”需要先登录。</p>
    <p v-if="protectedRequested" class="auth-service-note" role="status">发布和管理物品需要先登录，登录后会返回刚才的页面。</p>
    <p v-if="adminRequested" class="auth-service-note" role="status">管理控制台需要管理员账号；登录后将由服务端验证权限。</p>

    <form class="auth-form" novalidate @submit.prevent="submitLogin">
      <div class="auth-field">
        <label for="login-account">校园账号</label>
        <input id="login-account" v-model="account" autocomplete="username" autocapitalize="none" :spellcheck="false" :aria-invalid="Boolean(accountError)" @input="accountError = ''; submitError = ''" />
        <p v-if="accountError" class="auth-field-error" role="alert">{{ accountError }}</p>
      </div>
      <div class="auth-field">
        <label for="login-password">密码</label>
        <div class="auth-password-control">
          <input id="login-password" v-model="password" :type="showPassword ? 'text' : 'password'" autocomplete="current-password" :aria-invalid="Boolean(passwordError)" @input="passwordError = ''; submitError = ''" />
          <button type="button" :aria-label="showPassword ? '隐藏密码' : '显示密码'" :aria-pressed="showPassword" @click="showPassword = !showPassword">{{ showPassword ? '隐藏' : '显示' }}</button>
        </div>
        <p v-if="passwordError" class="auth-field-error" role="alert">{{ passwordError }}</p>
      </div>
      <p v-if="submitError" class="auth-submit-error" role="alert">{{ submitError }}</p>
      <button class="primary-button wide" type="submit" :disabled="submitting">{{ submitting ? '正在登录…' : '登录' }}</button>
    </form>

    <div class="auth-register-entry">
      <p>还没有账号？</p>
      <RouterLink class="secondary-button auth-link-button" :to="{ name: 'register' }">注册账号</RouterLink>
    </div>
  </AuthLayout>
</template>
