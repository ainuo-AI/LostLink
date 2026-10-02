<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { DemoUser } from '../../dev/adminDemo'
import AdminServiceNotice from '../../components/admin/AdminServiceNotice.vue'
import AdminPagination from '../../components/admin/AdminPagination.vue'
import AdminDialog from '../../components/admin/AdminDialog.vue'
import AdminActionPreview from '../../components/admin/AdminActionPreview.vue'
const props = defineProps<{ rows?: DemoUser[] }>()
const searchInput = ref('')
const keyword = ref('')
const status = ref('all')
const page = ref(1)
const selected = ref<DemoUser | null>(null)
const actionTarget = ref<DemoUser | null>(null)
const statuses = computed(() => [...new Set(props.rows?.map(row => row.status))])
const filtered = computed(() => props.rows?.filter(row => row.account.includes(keyword.value) && (status.value === 'all' || row.status === status.value)) ?? [])
const visibleRows = computed(() => filtered.value.slice((page.value - 1) * 5, page.value * 5))
watch([keyword, status], () => { page.value = 1; selected.value = null; actionTarget.value = null })
watch(() => props.rows, () => { searchInput.value = ''; keyword.value = ''; status.value = 'all'; page.value = 1; selected.value = null; actionTarget.value = null })
function search() { keyword.value = searchInput.value.trim(); page.value = 1 }
function resetFilters() { searchInput.value = ''; keyword.value = ''; status.value = 'all'; page.value = 1 }
function previewAction(row: DemoUser) { selected.value = null; actionTarget.value = row }
</script>

<template>
  <section aria-labelledby="admin-users-title">
    <div class="admin-page-heading"><p class="eyebrow">USERS</p><h1 id="admin-users-title" tabindex="-1">用户管理</h1><p>查询账号信息，并核对用户状态。</p></div>
    <form class="admin-panel admin-filters" role="search" @submit.prevent="search">
      <div class="filter-group"><label for="admin-account-search">账号搜索</label><input id="admin-account-search" v-model="searchInput" type="search" autocomplete="off" placeholder="输入账号" /></div>
      <div class="filter-group"><label for="admin-user-status">用户状态{{ rows ? '（演示）' : '' }}</label><select id="admin-user-status" v-model="status" :disabled="!rows"><option value="all">全部状态</option><option v-for="value in statuses" :key="value">{{ value }}</option></select></div>
      <button class="primary-button admin-filter-button" type="submit">搜索{{ rows ? '演示数据' : '' }}</button><button class="secondary-button" type="button" @click="resetFilters">重置</button>
    </form>
    <p class="admin-write-note">用户限制及恢复服务未接入。影响范围、对自身或其他管理员的操作限制尚未确定，不能执行处罚、删除或角色提升。</p>
    <AdminServiceNotice v-if="!rows" title="用户管理服务" description="当前无法查询真实账号、状态或允许操作；搜索不会发送未确定的请求。" />
    <template v-else>
      <p class="admin-demo-caption" role="status">开发演示：筛选后共 {{ filtered.length }} 个虚构账号。</p>
      <div v-if="visibleRows.length" class="admin-table-wrap" tabindex="0" aria-label="演示用户表格，可横向滚动">
        <table class="admin-table"><caption class="sr-only">开发演示用户列表</caption><thead><tr><th scope="col">账号</th><th scope="col">显示名称</th><th scope="col">状态</th><th scope="col">权限</th><th scope="col">查看</th></tr></thead><tbody><tr v-for="row in visibleRows" :key="row.account"><td>{{ row.account }}</td><td>{{ row.name }}</td><td><span class="admin-status">{{ row.status }}</span></td><td>权限服务暂未接入</td><td><button class="admin-inline-button" type="button" :aria-label="`查看用户 ${row.account} 详情`" @click="selected = row">查看详情</button></td></tr></tbody></table>
      </div>
      <div v-else class="admin-empty" role="status"><h2>没有符合条件的演示账号</h2><button class="secondary-button" type="button" @click="resetFilters">清除筛选</button></div>
    </template>
    <AdminPagination :page="page" :total="rows ? filtered.length : undefined" @change="page = $event" />
  </section>
  <AdminDialog v-if="selected" title="用户详情（演示）" @close="selected = null">
    <dl class="admin-detail-list"><div><dt>账号</dt><dd>{{ selected.account }}</dd></div><div><dt>显示名称</dt><dd>{{ selected.name }}</dd></div><div><dt>状态</dt><dd>{{ selected.status }}</dd></div><div><dt>说明</dt><dd>{{ selected.note }}</dd></div></dl>
    <p class="admin-write-note">身份、权限与处罚范围尚未接入；不依据本地账号判断是否允许管理。</p>
    <div class="admin-dialog-actions"><button class="secondary-button" type="button" disabled>限制用户</button><button class="secondary-button" type="button" disabled>恢复用户</button><button class="secondary-button" type="button" @click="previewAction(selected)">预览用户操作确认（不执行）</button></div>
  </AdminDialog>
  <AdminActionPreview v-if="actionTarget" :target="actionTarget.account" :actions="['限制用户（演示）', '恢复用户（演示）']" impact="用户限制影响范围尚未确定，此预览不执行任何处罚。" @close="actionTarget = null" />
</template>
