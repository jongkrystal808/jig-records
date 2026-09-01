<script setup lang="ts">
import { computed, defineAsyncComponent } from "vue";
import { RouterView, useRoute } from "vue-router";

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

const isQuickOperationRoute = computed(() => route.path === "/search" || route.path === "/inventory");
const isTransactionOverviewRoute = computed(() => route.path === "/inventory/overview");
</script>

<template>
  <section class="workspace-system-surface" data-system-ui="workspace" aria-label="Workspace UI 系統介面">
    <WorkbenchUiSurface
      v-if="isQuickOperationRoute"
      surface="workspace"
      :show-header="false"
      @update:selected-customer-id="emit('update:selectedCustomerId', $event)"
      @open-export="emit('openExport')"
    >
      <template #ui-switcher><slot name="ui-switcher" /></template>
      <template #heading-actions><slot name="heading-actions" /></template>
      <template #account-action><slot name="account-action" /></template>
    </WorkbenchUiSurface>
    <WorkbenchManagementSurface
      v-else-if="isTransactionOverviewRoute"
      surface="workspace"
      :show-header="false"
      transactions-only
      @update:selected-customer-id="emit('update:selectedCustomerId', $event)"
    />
    <RouterView v-else />
  </section>
</template>

<style scoped>
.workspace-system-surface {
  min-height: 100%;
}
</style>
