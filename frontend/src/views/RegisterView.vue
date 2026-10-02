<script setup lang="ts">
import { nextTick, reactive, ref } from 'vue'
import AuthLayout from '../components/AuthLayout.vue'

const account = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const errors = reactive({ account: '', password: '', confirmPassword: '' })
const submissionMessage = ref('')

function clearError(field: keyof typeof errors) {
  errors[field] = ''
  submissionMessage.value = ''
}

async function submitRegistration() {
  submissionMessage.value = ''
  errors.account = account.value.trim() ? '' : '请输入校园账号'
  errors.password = password.value ? '' : '请输入密码'
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

  // 注册接口及字段契约尚未提供；不发送密码，也不生成本地账户或成功状态。
  submissionMessage.value = '注册服务暂未接入，账号尚未创建，请稍后再试。'
}
</script>

<template>
  <AuthLayout title="注册账号" description="使用校园账号，开启你的 LostLink 之旅。">
    <p id="register-service-note" class="auth-service-note">注册服务暂未接入，当前无法创建账号。</p>

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
      <button class="primary-button wide" type="submit" aria-describedby="register-service-note">注册账号（服务暂未接入）</button>
    </form>

    <p class="auth-switch">已有账号，<RouterLink :to="{ name: 'login' }">返回登录</RouterLink></p>
  </AuthLayout>
</template>
