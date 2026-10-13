<script setup lang="ts">
// 文档对照：03_LostLink软件需求规格说明书.docx；图表编号以当前文档为准。
// 文档对应：图2-1 登记拾物信息；图2-2-3 登记拾物；图2-3 物品管理界面，使用found表单。
/** 登记拾物页面只负责选择 found 配置，共用表单会显示拾物专属字段。 */
import ItemEntryForm from '../components/ItemEntryForm.vue'
</script>

<template><ItemEntryForm type="found" /></template>
