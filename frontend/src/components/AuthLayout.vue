<script setup lang="ts">
// 设计文档对照：04_LostLink软件设计规格说明书.docx；以下“设计文档对应”使用该文档图表编号。
defineProps<{
  title: string
  description: string
}>()
</script>

<!-- 设计文档对应：图3-1-1、图3-1-2、图3-2-1 登录与注册共用的品牌、标题、说明和表单容器。 -->
<template>
  <div class="app-shell">
    <header class="site-header">
      <div class="header-inner">
        <RouterLink class="brand auth-brand" :to="{ name: 'home' }" aria-label="返回 LostLink 首页">
          <span class="brand-mark" aria-hidden="true">
            <span class="brand-link brand-link-a"></span>
            <span class="brand-link brand-link-b"></span>
          </span>
          <span>LostLink</span>
        </RouterLink>
        <RouterLink class="auth-home-link" :to="{ name: 'home' }">返回首页</RouterLink>
      </div>
    </header>

    <main class="auth-main">
      <section class="auth-card" aria-labelledby="auth-title">
        <p class="eyebrow">CAMPUS LOST &amp; FOUND</p>
        <h1 id="auth-title" tabindex="-1">{{ title }}</h1>
        <p class="auth-description">{{ description }}</p>
        <slot />
      </section>
      <p class="auth-footer">找回遗失，连接线索</p>
    </main>
  </div>
</template>
