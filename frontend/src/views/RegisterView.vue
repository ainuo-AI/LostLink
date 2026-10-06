<script setup lang="ts">
import { nextTick, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AuthLayout from '../components/AuthLayout.vue'
import { registerAccount } from '../api/auth'
import { ApiError } from '../api/client'

const account = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const errors = reactive({ account: '', password: '', confirmPassword: '' })
const submissionMessage = ref('')
const submitting = ref(false)
const router = useRouter()

function clearError(field: keyof typeof errors) {
  errors[field] = ''
  submissionMessage.value = ''
}

async function submitRegistration() {
  if (submitting.value) return
  submissionMessage.value = ''
  errors.account = account.value.trim() ? '' : '请输入校园账号'
  errors.password = !password.value ? '请输入密码' : password.value.length < 8 ? '密码至少需要 8 位' : ''
  errors.confirmPassword = !confirmPassword.value
    ? '请再次输入密码'
    : password.value !== confirmPassword.value ? '两次输入的密码不一致' : ''

  const invalidField = errors.account ? 'register-account'
    : errors.password ? 'register-password'
      : errors.confirmPassword ? 'register-confirm-password' : null

  if (invalidField) {
    await nextTick()
    document.getElementById(invalidField)?.focus()
    return
  }

  submitting.value = true
  try {
    await registerAccount({ account: account.value.trim(), password: password.value })
    password.value = ''
    confirmPassword.value = ''
    await router.replace({ name: 'login', query: { registered: '1', account: account.value.trim() } })
  } catch (error) {
    if (error instanceof ApiError && error.code === 'ACCOUNT_EXISTS') {
      errors.account = '该校园账号已经注册'
      await nextTick()
      document.getElementById('register-account')?.focus()
    } else {
      submissionMessage.value = error instanceof ApiError
        ? error.message
        : '无法连接注册服务，请确认后端已启动后重试。'
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AuthLayout title="注册账号" description="使用校园账号，开启你的 LostLink 之旅。">
    <form class="auth-form" novalidate @submit.prevent="submitRegistration">
      <div class="auth-field">
        <label for="register-account">校园账号</label>
        <input
          id="register-account"
          v-model="account"
          name="account"
          type="text"
          autocomplete="username"
          autocapitalize="none"
          :spellcheck="false"
          required
          :aria-invalid="Boolean(errors.account)"
          :aria-describedby="errors.account ? 'account-error' : undefined"
          @input="clearError('account')"
        />
        <p v-if="errors.account" id="account-error" class="auth-field-error">{{ errors.account }}</p>
      </div>

      <div class="auth-field">
        <label for="register-password">密码</label>
        <div class="auth-password-control">
          <input
            id="register-password"
            v-model="password"
            name="password"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="new-password"
            required
            :aria-invalid="Boolean(errors.password)"
            :aria-describedby="errors.password ? 'password-error' : undefined"
            @input="clearError('password')"
          />
          <button
            type="button"
            :aria-label="showPassword ? '隐藏密码' : '显示密码'"
            :aria-pressed="showPassword"
            aria-controls="register-password"
            @click="showPassword = !showPassword"
          >{{ showPassword ? '隐藏' : '显示' }}</button>
        </div>
        <p v-if="errors.password" id="password-error" class="auth-field-error">{{ errors.password }}</p>
      </div>

      <div class="auth-field">
        <label for="register-confirm-password">确认密码</label>
        <div class="auth-password-control">
          <input
            id="register-confirm-password"
            v-model="confirmPassword"
            name="confirmPassword"
            :type="showConfirmPassword ? 'text' : 'password'"
            autocomplete="new-password"
            required
            :aria-invalid="Boolean(errors.confirmPassword)"
            :aria-describedby="errors.confirmPassword ? 'confirm-password-error' : undefined"
            @input="clearError('confirmPassword')"
          />
          <button
            type="button"
            :aria-label="showConfirmPassword ? '隐藏确认密码' : '显示确认密码'"
            :aria-pressed="showConfirmPassword"
            aria-controls="register-confirm-password"
            @click="showConfirmPassword = !showConfirmPassword"
          >{{ showConfirmPassword ? '隐藏' : '显示' }}</button>
        </div>
        <p v-if="errors.confirmPassword" id="confirm-password-error" class="auth-field-error">{{ errors.confirmPassword }}</p>
      </div>

      <p v-if="submissionMessage" class="auth-submit-error" role="alert">{{ submissionMessage }}</p>
      <button class="primary-button wide" type="submit" :disabled="submitting">{{ submitting ? '正在注册…' : '注册账号' }}</button>
    </form>

    <p class="auth-switch">已有账号，<RouterLink :to="{ name: 'login' }">返回登录</RouterLink></p>
  </AuthLayout>
</template>
