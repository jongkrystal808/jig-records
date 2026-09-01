<script setup lang="ts">
import SearchWorkspacePage from "@/pages/SearchWorkspacePage.vue";
import type { SearchWorkspaceHandoffState } from "@/utils/searchHomeModeState";

const emit = defineEmits<{
  reportContextChange: [state: SearchWorkspaceHandoffState];
}>();
</script>

<template>
  <section class="modern-ui-surface" data-ui-surface="modern" aria-label="Modern UI">
    <SearchWorkspacePage @report-context-change="emit('reportContextChange', $event)" />
  </section>
</template>

<style src="../../styles/surfaces/modern.css"></style>
