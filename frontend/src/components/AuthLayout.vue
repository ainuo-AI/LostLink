<script setup lang="ts">
defineProps<{
  title: string
  description: string
}>()
</script>

<template>
  <div class="app-shell">
    <header class="site-header">
      <div class="header-inner">
        <a class="brand auth-brand" href="#/" aria-label="返回 LostLink 首页">
          <span class="brand-mark" aria-hidden="true">
            <span class="brand-link brand-link-a"></span>
            <span class="brand-link brand-link-b"></span>
          </span>
          <span>LostLink</span>
        </a>
        <a class="auth-home-link" href="#/">返回首页</a>
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
