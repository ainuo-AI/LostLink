<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import type { DemoAudit } from '../../dev/adminDemo'
import AdminServiceNotice from '../../components/admin/AdminServiceNotice.vue'
import AdminPagination from '../../components/admin/AdminPagination.vue'
import AdminDialog from '../../components/admin/AdminDialog.vue'

const props = defineProps<{ rows?: DemoAudit[] }>()
const emptyFilters = () => ({ operator: '', action: '', object: '', start: '', end: '' })
const filters = reactive(emptyFilters())
const applied = ref(emptyFilters())
const error = ref('')
const page = ref(1)
const selected = ref<DemoAudit | null>(null)
const actions = computed(() => [...new Set(props.rows?.map(row => row.action))])
const filtered = computed(() => props.rows?.filter(row => {
  const value = applied.value
  const date = row.time.slice(0, 10)
  return row.operator.includes(value.operator) && row.object.includes(value.object)
    && (!value.action || row.action === value.action)
    && (!value.start || date >= value.start) && (!value.end || date <= value.end)
}) ?? [])
const visibleRows = computed(() => filtered.value.slice((page.value - 1) * 5, page.value * 5))

function search() {
  error.value = filters.start && filters.end && filters.start > filters.end ? '开始日期不能晚于结束日期。' : ''
  if (error.value) return
  applied.value = { ...filters, operator: filters.operator.trim(), object: filters.object.trim() }
  page.value = 1
}
function reset() {
  Object.assign(filters, emptyFilters())
  applied.value = emptyFilters()
  error.value = ''
  page.value = 1
  selected.value = null
}
watch(() => props.rows, reset)
</script>

<template>
  <section aria-labelledby="admin-audit-title">
    <div class="admin-page-heading"><p class="eyebrow">AUDIT</p><h1 id="admin-audit-title" tabindex="-1">审计日志</h1><p>只读查看管理操作、处理理由及允许公开的状态变化。</p></div>
    <form class="admin-panel admin-filters" @submit.prevent="search">
      <div class="filter-group"><label for="audit-operator">操作者</label><input id="audit-operator" v-model="filters.operator" placeholder="搜索操作者" /></div>
      <div class="filter-group"><label for="audit-action">操作类型</label><select id="audit-action" v-model="filters.action" :disabled="!rows"><option value="">全部类型</option><option v-for="value in actions" :key="value">{{ value }}</option></select></div>
      <div class="filter-group"><label for="audit-object">操作对象</label><input id="audit-object" v-model="filters.object" placeholder="搜索操作对象" /></div>
      <div class="filter-group"><label for="audit-start">开始日期</label><input id="audit-start" v-model="filters.start" type="date" :aria-invalid="Boolean(error)" aria-describedby="audit-date-error" /></div>
      <div class="filter-group"><label for="audit-end">结束日期</label><input id="audit-end" v-model="filters.end" type="date" :aria-invalid="Boolean(error)" aria-describedby="audit-date-error" /></div>
      <button class="primary-button admin-filter-button" type="submit">筛选</button><button class="secondary-button" type="button" @click="reset">清除筛选</button>
      <p id="audit-date-error" class="admin-field-error" role="alert">{{ error }}</p>
    </form>
    <p class="admin-write-note">日志保持只读。时间范围、操作枚举和可查看字段以服务端契约为准。</p>
    <AdminServiceNotice v-if="!rows" title="审计查询服务" description="无法读取真实审计日志；筛选不会发送未经确认的请求。" />
    <template v-else>
      <p class="admin-demo-caption">开发演示：筛选后共 {{ filtered.length }} 条虚构日志，日期按样例文字筛选。</p>
      <div v-if="visibleRows.length" class="admin-table-wrap" tabindex="0" aria-label="演示审计表格，可横向滚动">
        <table class="admin-table"><caption class="sr-only">开发演示审计日志</caption><thead><tr><th scope="col">时间</th><th scope="col">操作者</th><th scope="col">操作类型</th><th scope="col">对象</th><th scope="col">结果</th><th scope="col">查看</th></tr></thead>
          <tbody><tr v-for="row in visibleRows" :key="row.id"><td>{{ row.time }}</td><td>{{ row.operator }}</td><td>{{ row.action }}</td><td>{{ row.object }}</td><td>{{ row.result }}</td><td><button class="admin-inline-button" type="button" :aria-label="`查看日志 ${row.id} 详情`" @click="selected = row">查看详情</button></td></tr></tbody>
        </table>
      </div>
      <div v-else class="admin-empty" role="status"><h2>没有符合条件的演示日志</h2><button class="secondary-button" type="button" @click="reset">清除筛选</button></div>
    </template>
    <AdminPagination :page="page" :total="rows ? filtered.length : undefined" @change="page = $event" />
  </section>
  <AdminDialog v-if="selected" title="审计详情（演示，只读）" @close="selected = null">
    <dl class="admin-detail-list"><div><dt>日志编号</dt><dd>{{ selected.id }}</dd></div><div><dt>操作时间</dt><dd>{{ selected.time }}</dd></div><div><dt>操作者</dt><dd>{{ selected.operator }}</dd></div><div><dt>操作类型</dt><dd>{{ selected.action }}</dd></div><div><dt>操作对象</dt><dd>{{ selected.object }}</dd></div><div><dt>处理理由</dt><dd>{{ selected.reason }}</dd></div><div><dt>结果</dt><dd>{{ selected.result }}</dd></div><div><dt>操作前</dt><dd>{{ selected.before }}</dd></div><div><dt>操作后</dt><dd>{{ selected.after }}</dd></div></dl>
  </AdminDialog>
</template>
