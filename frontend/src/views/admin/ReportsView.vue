<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { DemoReport } from '../../dev/adminDemo'
import AdminServiceNotice from '../../components/admin/AdminServiceNotice.vue'
import AdminPagination from '../../components/admin/AdminPagination.vue'
import AdminDialog from '../../components/admin/AdminDialog.vue'
import AdminActionPreview from '../../components/admin/AdminActionPreview.vue'
const props = defineProps<{ rows?: DemoReport[] }>()
const status = ref('all')
const page = ref(1)
const selected = ref<DemoReport | null>(null)
const actionTarget = ref<DemoReport | null>(null)
const statuses = computed(() => [...new Set(props.rows?.map(row => row.status))])
const filtered = computed(() => props.rows?.filter(row => status.value === 'all' || row.status === status.value) ?? [])
const visibleRows = computed(() => filtered.value.slice((page.value - 1) * 5, page.value * 5))
watch(status, () => { page.value = 1; selected.value = null; actionTarget.value = null })
watch(() => props.rows, () => { status.value = 'all'; page.value = 1; selected.value = null; actionTarget.value = null })
function previewAction(row: DemoReport) {
  selected.value = null
  actionTarget.value = row
}
</script>

<template>
  <section aria-labelledby="admin-reports-title">
    <div class="admin-page-heading"><p class="eyebrow">REPORTS</p><h1 id="admin-reports-title" tabindex="-1">举报审核</h1><p>核对举报原因、关联对象及处理历史。</p></div>
    <div class="admin-panel admin-filters">
      <div class="filter-group"><label for="report-status">举报状态{{ rows ? '（演示）' : '' }}</label><select id="report-status" v-model="status" :disabled="!rows"><option value="all">全部状态</option><option v-for="value in statuses" :key="value">{{ value }}</option></select></div>
      <p class="admin-muted">{{ rows ? '演示状态只用于筛选样例，不代表服务端状态枚举。' : '举报状态与权限契约尚未提供。' }}</p>
    </div>
    <p class="admin-write-note">举报处理服务与允许动作未接入，驳回、隐藏、恢复等真实操作不可用。用户限制需在用户管理中单独处理。</p>
    <AdminServiceNotice v-if="!rows" title="举报审核服务" description="无法查询举报及处理历史，不将接口缺失显示为暂无举报。" />
    <template v-else>
      <p class="admin-demo-caption" role="status">开发演示：筛选后共 {{ filtered.length }} 条虚构举报。</p>
      <div v-if="visibleRows.length" class="admin-table-wrap" tabindex="0" aria-label="演示举报表格，可横向滚动">
        <table class="admin-table"><caption class="sr-only">开发演示举报列表</caption><thead><tr><th scope="col">举报编号</th><th scope="col">关联对象</th><th scope="col">举报原因</th><th scope="col">状态</th><th scope="col">时间</th><th scope="col">查看</th></tr></thead>
          <tbody><tr v-for="row in visibleRows" :key="row.id"><td>{{ row.id }}</td><td>{{ row.object }}</td><td>{{ row.reason }}</td><td><span class="admin-status">{{ row.status }}</span></td><td>{{ row.time }}</td><td><button class="admin-inline-button" type="button" :aria-label="`查看举报 ${row.id} 详情`" @click="selected = row">详情与历史</button></td></tr></tbody>
        </table>
      </div>
      <div v-else class="admin-empty" role="status"><h2>没有符合条件的演示举报</h2><button class="secondary-button" type="button" @click="status = 'all'">清除状态筛选</button></div>
    </template>
    <AdminPagination :page="page" :total="rows ? filtered.length : undefined" @change="page = $event" />
  </section>
  <AdminDialog v-if="selected" title="举报详情与处理历史（演示）" @close="selected = null">
    <dl class="admin-detail-list"><div><dt>举报编号</dt><dd>{{ selected.id }}</dd></div><div><dt>关联对象</dt><dd>{{ selected.object }}</dd></div><div><dt>举报原因</dt><dd>{{ selected.reason }}</dd></div><div><dt>证据摘要</dt><dd>{{ selected.evidence }}</dd></div><div><dt>当前状态</dt><dd>{{ selected.status }}</dd></div></dl>
    <h3>处理历史（演示）</h3><ol v-if="selected.history.length" class="admin-history"><li v-for="entry in selected.history" :key="entry.time"><time>{{ entry.time }}</time><p>{{ entry.description }}</p></li></ol><p v-else>这条演示举报没有处理历史样例。</p>
    <p class="admin-write-note">服务与权限暂未接入；处理举报不会在本预览中限制用户。</p>
    <div class="admin-dialog-actions"><button class="secondary-button" type="button" disabled>处理举报（暂未接入）</button><button class="secondary-button" type="button" @click="previewAction(selected)">预览处理确认（不执行）</button></div>
  </AdminDialog>
  <AdminActionPreview v-if="actionTarget" :target="`${actionTarget.id} · ${actionTarget.object}`" :actions="['驳回举报（演示）', '隐藏内容（演示）', '恢复内容（演示）']" impact="举报处理与用户限制为独立操作。" @close="actionTarget = null" />
</template>
