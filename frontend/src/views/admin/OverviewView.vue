<script setup lang="ts">
import type { AdminDemoData } from '../../dev/adminDemo'
import AdminServiceNotice from '../../components/admin/AdminServiceNotice.vue'
defineProps<{ demo?: AdminDemoData }>()
const metrics = ['待处理举报', '已处理举报', '受限用户', '评估任务']
</script>

<template>
  <section aria-labelledby="admin-overview-title">
    <div class="admin-page-heading"><p class="eyebrow">OVERVIEW</p><h1 id="admin-overview-title" tabindex="-1">数据概览</h1><p>查看校园管理工作与待处理事项。</p></div>
    <p class="admin-scope-note">{{ demo ? '开发演示统计范围：2026-09-01 至 2026-09-30；以下为固定样例，不是列表条数或真实统计。' : '统计时间范围与总量服务暂未接入，当前无法确认统计口径。' }}</p>
    <div class="admin-metrics">
      <article v-for="(label, index) in metrics" :key="label" class="admin-metric-card"><h2>{{ label }}</h2><strong>{{ demo?.statistics[index].value ?? '—' }}</strong><p>{{ demo ? '固定演示数值' : '统计服务暂未接入' }}</p></article>
    </div>
    <div class="admin-panel">
      <h2>工作入口</h2>
      <div class="admin-shortcuts">
        <a href="#/admin-preview/reports"><strong>举报审核 →</strong><span>查看举报、关联对象与处理历史</span></a>
        <a href="#/admin-preview/users"><strong>用户管理 →</strong><span>搜索账号与查看状态</span></a>
        <a href="#/admin-preview/audit"><strong>审计日志 →</strong><span>按操作对象和时间追溯记录</span></a>
        <a href="#/admin-preview/calibration"><strong>匹配校准 →</strong><span>查看任务状态与版本对比</span></a>
      </div>
    </div>
    <AdminServiceNotice v-if="!demo" title="管理概览服务" description="无法加载真实管理统计；服务缺失不代表待处理数量为零。" />
  </section>
</template>
