<script setup lang="ts">
// 设计文档对照：04_LostLink软件设计规格说明书.docx；以下“设计文档对应”使用该文档图表编号。
// 文档对照：03_LostLink软件需求规格说明书.docx；图表编号以当前文档为准。
// 文档对应：图2-3 界面：共享页面入口，具体业务界面由路由呈现。
// 登录与注册页面共用的样式在根组件加载，路由切换时无需重复加载。
import './styles/auth.css'
</script>

<!-- 设计文档对应：图2-1、图3-3-1、图3-3-2 根界面通过 RouterView 承载业务页面流。 -->
<template>
  <!-- 所有页面统一交给 Vue Router 管理，保证刷新、前进和后退行为一致。 -->
  <RouterView />
</template>
