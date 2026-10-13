<script setup lang="ts">
// 设计文档对照：04_LostLink软件设计规格说明书.docx；以下“设计文档对应”使用该文档图表编号。
// 文档对照：03_LostLink软件需求规格说明书.docx；图表编号以当前文档为准。
// 文档对应：图2-1 登记拾物信息；图2-2-3 登记拾物；图2-3 物品管理界面，使用found表单。
/** 登记拾物页面只负责选择 found 配置，共用表单会显示拾物专属字段。 */
import ItemEntryForm from '../components/ItemEntryForm.vue'
</script>

<!-- 设计文档对应：图3-1-6、图3-2-4、图4-1-4 拾物入口传入 found，复用 ItemEntryForm。 -->
<template><ItemEntryForm type="found" /></template>
