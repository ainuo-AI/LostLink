<script setup lang="ts">
// 文档对照：03_LostLink软件需求规格说明书.docx；图表编号以当前文档为准。
// 文档对应：图2-3 界面：共享页面入口，具体业务界面由路由呈现。
// 登录与注册页面共用的样式在根组件加载，路由切换时无需重复加载。
import './styles/auth.css'
</script>

<template>
  <!-- 所有页面统一交给 Vue Router 管理，保证刷新、前进和后退行为一致。 -->
  <RouterView />
</template>
