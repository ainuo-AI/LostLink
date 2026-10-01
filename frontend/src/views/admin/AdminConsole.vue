<script setup lang="ts">
import { onMounted, ref, shallowRef } from 'vue'
import AdminLayout from '../../layouts/AdminLayout.vue'
import type { AdminSection } from '../../router/admin'
import type { AdminDemoData } from '../../dev/adminDemo'
import OverviewView from './OverviewView.vue'
import ReportsView from './ReportsView.vue'
import UsersView from './UsersView.vue'
import AuditView from './AuditView.vue'
import CalibrationView from './CalibrationView.vue'
import '../../styles/admin.css'

defineProps<{ section: AdminSection }>()
const demoEnabled = ref(false)
const demoData = shallowRef<AdminDemoData>()
onMounted(async () => {
  if (import.meta.env.DEV) {
    const { adminDemoData } = await import('../../dev/adminDemo')
    demoData.value = adminDemoData
  }
})
</script>

<template>
  <AdminLayout :section="section" :demo-enabled="demoEnabled" :demo-ready="Boolean(demoData)" @toggle-demo="demoEnabled = !demoEnabled">
    <OverviewView v-if="section === 'overview'" :demo="demoEnabled ? demoData : undefined" />
    <ReportsView v-else-if="section === 'reports'" :rows="demoEnabled ? demoData?.reports : undefined" />
    <UsersView v-else-if="section === 'users'" :rows="demoEnabled ? demoData?.users : undefined" />
    <AuditView v-else-if="section === 'audit'" :rows="demoEnabled ? demoData?.audit : undefined" />
    <CalibrationView v-else :demo="demoEnabled ? demoData : undefined" />
  </AdminLayout>
</template>
