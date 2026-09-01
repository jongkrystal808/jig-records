<script setup lang="ts">
import { computed } from "vue";
import { RouterView, useRoute, useRouter } from "vue-router";

import FormUiSurface, { type FormWorkspace } from "@/components/home/FormUiSurface.vue";
import type { FormMasterView, FormProductionView } from "@/components/home/FormReportOperations.vue";

withDefaults(defineProps<{ surfaceLabel?: string }>(), { surfaceLabel: "Form UI" });

const route = useRoute();
const router = useRouter();
const emit = defineEmits<{
  "update:selectedCustomerId": [value: number | null];
}>();

const workspace = computed<FormWorkspace>(() => {
  if (route.path === "/inventory") return "import";
  if (route.path === "/inventory/overview") return "inventory-overview";
  if (route.path.startsWith("/production")) return "production";
  if (route.path === "/master/ledger") return "ledger";
  if (route.path === "/master/quality") return "quality";
  if (route.path === "/master/images") return "image";
  if (route.path.startsWith("/master")) return "master";
  return "report";
});

const productionView = computed<FormProductionView>(() =>
  route.path === "/production/mapping" ? "mappings" : "requirements"
);

const masterView = computed<FormMasterView>(() => {
  if (route.path === "/master/models") return "model";
  if (route.path === "/master/stations") return "station";
  if (route.path === "/master/customers") return "customer";
  if (route.path === "/master/users") return "user";
  return "fixture";
});

const workspacePaths: Record<FormWorkspace, string> = {
  report: "/search",
  import: "/inventory",
  "inventory-overview": "/inventory/overview",
  production: "/production/requirements",
  master: "/master/fixtures",
  image: "/master/images",
  ledger: "/master/ledger",
  quality: "/master/quality"
};

function openWorkspace(nextWorkspace: FormWorkspace): void {
  const path = workspacePaths[nextWorkspace];
  if (path !== route.path) void router.push(path);
}

function openProductionView(view: FormProductionView): void {
  const path = view === "mappings" ? "/production/mapping" : "/production/requirements";
  if (path !== route.path) void router.push(path);
}

function openMasterView(view: FormMasterView): void {
  const path = `/master/${view === "fixture" ? "fixtures" : `${view}s`}`;
  if (path !== route.path) void router.push(path);
}
</script>

<template>
  <section class="form-system-surface" data-system-ui="form" aria-label="Form UI 系統介面">
    <RouterView v-if="route.path === '/storage'" />
    <FormUiSurface
      v-else
      :surface-label="surfaceLabel"
      :workspace="workspace"
      :production-view="productionView"
      :master-view="masterView"
      @update:selected-customer-id="emit('update:selectedCustomerId', $event)"
      @workspace-change="openWorkspace"
      @production-view-change="openProductionView"
      @master-view-change="openMasterView"
    >
      <template #ui-switcher><slot name="ui-switcher" /></template>
      <template #heading-actions><slot name="heading-actions" /></template>
      <template #account-action><slot name="account-action" /></template>
    </FormUiSurface>
  </section>
</template>

<style scoped>
.form-system-surface {
  min-height: 100%;
}
</style>
