<script setup lang="ts">
/**
 * 全站顶部导航组件
 *
 * RouterLink 负责真实页面跳转，activeLabel 根据当前路由计算高亮项。
 * 六个入口同时覆盖现有业务页和同学新增的普通用户入口。
 */
import { computed } from 'vue'
import { useRoute } from 'vue-router'

// activeNav 保持兼容旧页面；实际高亮以当前 URL 为准，刷新和后退也会正确显示。
defineProps<{ activeNav?: string }>()
const route = useRoute()
const activeLabel = computed(() => {
  if (route.name === 'publish-lost') return '发布失物'
  if (route.name === 'register-found') return '登记拾物'
  if (route.name === 'notifications' || route.name === 'match-detail') return '匹配通知'
  if (route.name === 'my' || route.name === 'my-preview') return '我的'
  if (route.name === 'login' || route.name === 'register') return '登录'
  if (route.name === 'home') return '首页'
  return ''
})

// 子组件不直接处理跳转，而是向父组件发出 navigate 事件。
// 这样导航栏可以在不同页面中复用。
defineEmits<{
  navigate: [label: string]
}>()

// 导航数据统一放在数组中，避免在模板里重复写按钮。
const navItems = [
  { label: '首页', name: 'home' },
  { label: '发布失物', name: 'publish-lost' },
  { label: '登记拾物', name: 'register-found' },
  { label: '匹配通知', name: 'notifications' },
  { label: '我的', name: 'my' },
  { label: '登录', name: 'login' },
] as const
</script>

<template>
  <header class="site-header">
    <div class="header-inner">
      <RouterLink class="brand" :to="{ name: 'home' }" aria-label="返回 LostLink 首页">
        <span class="brand-mark" aria-hidden="true">
          <span class="brand-link brand-link-a"></span>
          <span class="brand-link brand-link-b"></span>
        </span>
        <span>LostLink</span>
      </RouterLink>

      <nav class="desktop-nav" aria-label="主导航">
        <!-- v-for 根据数组生成导航项，active 类用于标记当前页面。 -->
        <RouterLink
          v-for="item in navItems"
          :key="item.name"
          :to="{ name: item.name }"
          :class="['nav-item', { active: activeLabel === item.label }]"
          :aria-current="activeLabel === item.label ? 'page' : undefined"
        >
          {{ item.label }}
        </RouterLink>
      </nav>
    </div>
    <!-- 手机端同样保留六个入口，普通用户和新增业务都可直接访问。 -->
    <nav class="mobile-nav" aria-label="手机主导航">
      <RouterLink
        v-for="item in navItems"
        :key="item.name"
        :to="{ name: item.name }"
        :class="{ active: activeLabel === item.label }"
        :aria-current="activeLabel === item.label ? 'page' : undefined"
      >{{ item.label }}</RouterLink>
    </nav>
  </header>
</template>
