<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { AdminDemoData, DemoVersion } from '../../dev/adminDemo'
import AdminServiceNotice from '../../components/admin/AdminServiceNotice.vue'
import AdminActionPreview from '../../components/admin/AdminActionPreview.vue'

const props = defineProps<{ demo?: AdminDemoData }>()
const category = ref('')
const start = ref('')
const end = ref('')
const error = ref('')
const showTask = ref(false)
const taskState = ref('等待（演示）')
const taskStates = ['等待（演示）', '执行中（演示）', '成功（演示）', '失败（演示）', '样本不足（演示）']
const selectedId = ref(props.demo?.versions[1]?.id ?? '')
const selected = computed(() => props.demo?.versions.find(version => version.id === selectedId.value))
const current = computed(() => props.demo?.versions[0])
const compared = computed(() => current.value?.id === selected.value?.id ? [current.value] : [current.value, selected.value])
const actionTarget = ref<DemoVersion | null>(null)

function previewTask() {
  error.value = !category.value || !start.value || !end.value ? '请选择演示类别并填写评估日期。'
    : start.value > end.value ? '开始日期不能晚于结束日期。' : ''
  if (error.value) return
  showTask.value = true
  taskState.value = taskStates[0]!
}
watch(() => props.demo, () => {
  category.value = ''; start.value = ''; end.value = ''; error.value = ''; showTask.value = false
  selectedId.value = props.demo?.versions[1]?.id ?? ''; actionTarget.value = null
})
</script>

<template>
  <section aria-labelledby="admin-calibration-title">
    <div class="admin-page-heading"><p class="eyebrow">CALIBRATION</p><h1 id="admin-calibration-title" tabindex="-1">匹配校准版本管理</h1><p>查看异步评估与版本指标；启用、回滚需要人工确认及服务端授权。</p></div>
    <form class="admin-panel admin-filters" novalidate @submit.prevent="previewTask">
      <div class="filter-group"><label for="calibration-category">物品类别</label><select id="calibration-category" v-model="category" :disabled="!demo"><option value="">{{ demo ? '选择演示类别' : '类别服务暂未接入' }}</option><option v-for="value in demo?.categories" :key="value">{{ value }}</option></select></div>
      <div class="filter-group"><label for="calibration-start">评估开始日期</label><input id="calibration-start" v-model="start" type="date" :disabled="!demo" aria-describedby="calibration-error" :aria-invalid="Boolean(error)" /></div>
      <div class="filter-group"><label for="calibration-end">评估结束日期</label><input id="calibration-end" v-model="end" type="date" :disabled="!demo" aria-describedby="calibration-error" :aria-invalid="Boolean(error)" /></div>
      <button class="primary-button admin-filter-button" type="button" disabled>发起评估（暂未接入）</button>
      <button v-if="demo" class="secondary-button" type="submit">预览任务状态（不执行）</button>
      <p id="calibration-error" class="admin-field-error" role="alert">{{ error }}</p>
    </form>
    <p class="admin-write-note">评估类别、时间口径、任务状态和版本权限尚未确定。浏览器不会训练参数、计算指标或启动评估任务。</p>
    <AdminServiceNotice v-if="!demo" title="校准评估与版本服务" description="无法读取活动版本、候选指标及异步任务。审核、保留、拒绝、启用和回滚均不可用。" />
    <template v-else>
      <div v-if="showTask" class="admin-panel">
        <h2>任务状态样例（非真实任务）</h2><p class="admin-muted">{{ category }} · {{ start }} 至 {{ end }}。手动选择固定样例，不轮询或发送请求。</p>
        <div class="filter-group"><label for="calibration-task-state">预览状态</label><select id="calibration-task-state" v-model="taskState"><option v-for="value in taskStates" :key="value">{{ value }}</option></select></div>
        <div class="admin-task-state" role="status"><h3>{{ taskState }}</h3><p>此状态只展示布局，不代表实际执行结果、失败原因或样本数量。</p></div>
      </div>
      <div class="admin-panel">
        <h2>版本指标对比（固定演示值）</h2>
        <p class="admin-demo-caption">指标名称与计算口径待确认。以下 A / B 数值来自固定样例，不能用于启用决策。</p>
        <div class="filter-group"><label for="calibration-version">对比版本</label><select id="calibration-version" v-model="selectedId"><option v-for="version in demo.versions" :key="version.id" :value="version.id">{{ version.id }} · {{ version.status }}</option></select></div>
        <div class="admin-table-wrap" tabindex="0" aria-label="演示版本对比，可横向滚动">
          <table class="admin-table"><caption class="sr-only">固定演示指标比较</caption><thead><tr><th scope="col">版本</th><th scope="col">状态样例</th><th scope="col">时间</th><th scope="col">演示指标 A（口径未定）</th><th scope="col">演示指标 B（口径未定）</th></tr></thead>
            <tbody><tr v-for="version in compared" :key="version?.id"><template v-if="version"><td>{{ version.id }}</td><td>{{ version.status }}</td><td>{{ version.time }}</td><td>{{ version.metricA }}</td><td>{{ version.metricB }}</td></template></tr></tbody>
          </table>
        </div>
        <p class="admin-write-note">真实版本操作未接入；演示不会改变活动版本。启用或回滚后必须从服务端重新读取活动版本。</p>
        <div class="admin-dialog-actions"><button v-for="action in ['审核', '保留', '拒绝', '启用', '回滚']" :key="action" class="secondary-button" type="button" disabled>{{ action }}（未接入）</button><button v-if="selected" class="secondary-button" type="button" @click="actionTarget = selected">预览版本确认（不执行）</button></div>
      </div>
    </template>
  </section>
  <AdminActionPreview v-if="actionTarget" :target="`${actionTarget.id} · ${actionTarget.status}`" :actions="['启用目标版本（演示）', '回滚至目标版本（演示）']" impact="目标版本不会在本预览中启用或回滚；真实影响和允许动作待服务端契约确定。" @close="actionTarget = null" />
</template>
