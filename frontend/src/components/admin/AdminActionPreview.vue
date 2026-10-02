<script setup lang="ts">
import { nextTick, ref, useId } from 'vue'
import AdminDialog from './AdminDialog.vue'
const props = defineProps<{ target: string; actions: string[]; impact: string }>()
defineEmits<{ close: [] }>()
const action = ref(props.actions[0])
const reason = ref('')
const error = ref('')
const reviewing = ref(false)
const reasonId = useId()
const actionId = useId()
const reasonInput = ref<HTMLTextAreaElement | null>(null)
const backButton = ref<HTMLButtonElement | null>(null)
async function review() {
  error.value = reason.value.trim() ? '' : '请填写理由以预览确认摘要'
  if (error.value) { reasonInput.value?.focus(); return }
  reviewing.value = true
  await nextTick()
  backButton.value?.focus()
}
async function edit() {
  reviewing.value = false
  await nextTick()
  reasonInput.value?.focus()
}
</script>

<template>
  <AdminDialog :title="reviewing ? '操作确认摘要（演示）' : '预览操作确认（不执行）'" @close="$emit('close')">
    <p class="admin-write-note">{{ impact }}真实允许动作、影响范围和权限需由后端确认。</p>
    <form v-if="!reviewing" class="admin-action-form" novalidate @submit.prevent="review">
      <p><strong>操作对象：</strong>{{ target }}</p>
      <label :for="actionId">处理决定（示例）</label><select :id="actionId" v-model="action"><option v-for="option in actions" :key="option">{{ option }}</option></select>
      <label :for="reasonId">处理理由<textarea :id="reasonId" ref="reasonInput" v-model="reason" rows="3" required :aria-invalid="Boolean(error)" :aria-describedby="error ? `${reasonId}-error` : undefined" @input="error = ''"></textarea></label>
      <p v-if="error" :id="`${reasonId}-error`" class="admin-field-error" role="alert">{{ error }}</p>
      <button class="primary-button wide" type="submit">查看确认摘要（演示）</button>
    </form>
    <template v-else>
      <dl class="admin-detail-list"><div><dt>操作对象</dt><dd>{{ target }}</dd></div><div><dt>处理决定</dt><dd>{{ action }}</dd></div><div><dt>处理理由</dt><dd>{{ reason.trim() }}</dd></div></dl>
      <p class="admin-write-note">服务暂未接入：不能执行此操作，不会提交请求或改变任何记录。</p>
      <div class="admin-dialog-actions"><button ref="backButton" class="secondary-button" type="button" @click="edit">返回修改</button><button class="primary-button" type="button" disabled>确认执行（暂未接入）</button></div>
    </template>
  </AdminDialog>
</template>
