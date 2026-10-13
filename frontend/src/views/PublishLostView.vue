<script setup lang="ts">
// 文档对照：03_LostLink软件需求规格说明书.docx；图表编号以当前文档为准。
// 文档对应：图2-1 发布失物信息；图2-2-2 发布失物；图2-3 物品管理界面，使用lost表单。
/** 发布失物页面只负责选择 lost 配置，具体表单逻辑由共用组件承担。 */
import ItemEntryForm from '../components/ItemEntryForm.vue'
</script>

<template><ItemEntryForm type="lost" /></template>
