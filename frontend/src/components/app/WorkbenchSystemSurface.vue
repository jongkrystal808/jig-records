<script setup lang="ts">
import { computed, defineAsyncComponent } from "vue";
import { useRoute } from "vue-router";

import FormSystemSurface from "@/components/app/FormSystemSurface.vue";
import WorkbenchDailyLoading from "@/components/home/WorkbenchDailyLoading.vue";
import WorkbenchManagementLoading from "@/components/home/WorkbenchManagementLoading.vue";

const WorkbenchUiSurface = defineAsyncComponent({
  loader: () => import("@/components/home/WorkbenchUiSurface.vue"),
  loadingComponent: WorkbenchDailyLoading,
  delay: 120
});

const WorkbenchManagementSurface = defineAsyncComponent({
  loader: () => import("@/components/home/WorkbenchManagementSurface.vue"),
  loadingComponent: WorkbenchManagementLoading,
  delay: 120
});

const route = useRoute();
const emit = defineEmits<{
  "update:selectedCustomerId": [value: number | null];
  openExport: [];
}>();

const isDailyWorkbenchRoute = computed(() => route.path === "/search" || route.path === "/inventory");
const isWorkbenchManagementRoute = computed(() =>
  route.path === "/inventory/overview" ||
  route.path.startsWith("/production") ||
  [
    "/master/fixtures",
    "/master/models",
    "/master/stations",
    "/master/customers",
    "/master/users",
    "/master/images",
    "/master/ledger",
    "/master/quality"
  ].includes(route.path)
);

</script>

<template>
  <section class="workbench-system-surface" data-system-ui="workbench" aria-label="工作台 UI 系統介面">
    <WorkbenchUiSurface
      v-if="isDailyWorkbenchRoute"
      @update:selected-customer-id="emit('update:selectedCustomerId', $event)"
      @open-export="emit('openExport')"
    >
      <template #ui-switcher><slot name="ui-switcher" /></template>
      <template #heading-actions><slot name="heading-actions" /></template>
      <template #account-action><slot name="account-action" /></template>
    </WorkbenchUiSurface>
    <WorkbenchManagementSurface
      v-else-if="isWorkbenchManagementRoute"
      @update:selected-customer-id="emit('update:selectedCustomerId', $event)"
    >
      <template #ui-switcher><slot name="ui-switcher" /></template>
      <template #heading-actions><slot name="heading-actions" /></template>
      <template #account-action><slot name="account-action" /></template>
    </WorkbenchManagementSurface>
    <FormSystemSurface
      v-else
      surface-label="工作台 UI · 管理後臺"
      @update:selected-customer-id="emit('update:selectedCustomerId', $event)"
    >
      <template #ui-switcher><slot name="ui-switcher" /></template>
      <template #heading-actions><slot name="heading-actions" /></template>
      <template #account-action><slot name="account-action" /></template>
    </FormSystemSurface>
  </section>
</template>

<style scoped>
.workbench-system-surface {
  min-height: 100%;
}
</style>
