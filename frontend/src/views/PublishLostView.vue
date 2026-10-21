<script setup lang="ts">
// 设计文档对照：04_LostLink软件设计规格说明书.docx；以下“设计文档对应”使用该文档图表编号。
// 文档对照：03_LostLink软件需求规格说明书.docx；图表编号以当前文档为准。
// 文档对应：图2-1 发布失物信息；图2-2-2 发布失物；图2-3 物品管理界面，使用lost表单。
/** 发布失物页面只负责选择 lost 配置，具体表单逻辑由共用组件承担。 */
import ItemEntryForm from '../components/ItemEntryForm.vue'
</script>

<!-- 设计文档对应：图3-1-5、图3-2-4、图4-1-3 失物入口传入 lost，复用 ItemEntryForm。 -->
<template><ItemEntryForm type="lost" /></template>
