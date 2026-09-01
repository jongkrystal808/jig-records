<script setup lang="ts">
import FormMasterDataOperations from "@/components/home/FormMasterDataOperations.vue";
import FormProductionOperations from "@/components/home/FormProductionOperations.vue";
import FormTransactionOperations from "@/components/home/FormTransactionOperations.vue";

export type FormOperationMode = "transactions" | "production" | "master";
export type FormProductionView = "requirements" | "mappings";
export type FormMasterView = "fixture" | "model" | "station" | "customer" | "user";

defineProps<{
  mode: FormOperationMode;
  requestedProductionView?: FormProductionView;
  requestedMasterView?: FormMasterView;
  workbenchLayout?: boolean;
}>();

defineEmits<{
  productionViewChange: [view: FormProductionView];
  masterViewChange: [view: FormMasterView];
}>();
</script>

<template>
  <FormTransactionOperations v-if="mode === 'transactions'" :workbench-layout="workbenchLayout">
    <template #between-filter-and-results><slot name="between-filter-and-results" /></template>
  </FormTransactionOperations>

  <FormProductionOperations
    v-else-if="mode === 'production'"
    :requested-view="requestedProductionView"
    :workbench-layout="workbenchLayout"
    @view-change="$emit('productionViewChange', $event)"
  >
    <template #between-filter-and-results><slot name="between-filter-and-results" /></template>
  </FormProductionOperations>

  <FormMasterDataOperations
    v-else
    :requested-view="requestedMasterView"
    :workbench-layout="workbenchLayout"
    @view-change="$emit('masterViewChange', $event)"
  >
    <template #between-filter-and-results><slot name="between-filter-and-results" /></template>
  </FormMasterDataOperations>
</template>

<style src="@/styles/form-report-operations.css"></style>
