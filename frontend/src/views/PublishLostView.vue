<script setup lang="ts">
/** 发布失物页面只负责选择 lost 配置，具体表单逻辑由共用组件承担。 */
import ItemEntryForm from '../components/ItemEntryForm.vue'
</script>

<template><ItemEntryForm type="lost" /></template>
