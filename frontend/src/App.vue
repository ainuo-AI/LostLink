<script setup lang="ts">
// 登录与注册页面共用的样式在根组件加载，路由切换时无需重复加载。
import './styles/auth.css'
</script>

<template>
  <!-- 所有页面统一交给 Vue Router 管理，保证刷新、前进和后退行为一致。 -->
  <RouterView />
</template>
