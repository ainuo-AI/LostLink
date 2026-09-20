<script setup lang="ts">
defineProps<{
  activeNav: string
}>()

// 子组件不直接处理跳转，而是向父组件发出 navigate 事件。
// 这样导航栏可以在不同页面中复用。
defineEmits<{
  navigate: [label: string]
}>()

// 导航数据统一放在数组中，避免在模板里重复写按钮。
const navItems = ['首页', '发布失物', '登记拾物', '匹配通知', '我的']
</script>

<template>
  <header class="site-header">
    <div class="header-inner">
      <button class="brand" type="button" aria-label="返回 LostLink 首页" @click="$emit('navigate', '首页')">
        <span class="brand-mark" aria-hidden="true">
          <span class="brand-link brand-link-a"></span>
          <span class="brand-link brand-link-b"></span>
        </span>
        <span>LostLink</span>
      </button>

      <nav class="desktop-nav" aria-label="主导航">
        <!-- v-for 根据数组生成导航项，active 类用于标记当前页面。 -->
        <button
          v-for="item in navItems"
          :key="item"
          type="button"
          :class="['nav-item', { active: activeNav === item }]"
          @click="$emit('navigate', item)"
        >
          {{ item }}
        </button>
      </nav>

      <button class="mobile-profile" type="button" aria-label="打开我的页面" @click="$emit('navigate', '我的')">
        <span aria-hidden="true">👤</span>
      </button>
    </div>
  </header>
</template>
