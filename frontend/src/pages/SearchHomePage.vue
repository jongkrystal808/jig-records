<script setup lang="ts">
import { searchWorkspaceHandoffState } from "@/appState";
import ModernUiSurface from "@/components/home/ModernUiSurface.vue";
import type { SearchWorkspaceHandoffState } from "@/utils/searchHomeModeState";

function rememberSearchWorkspaceState(state: SearchWorkspaceHandoffState): void {
  searchWorkspaceHandoffState.value = state;
}
</script>

<template>
  <ModernUiSurface @report-context-change="rememberSearchWorkspaceState" />
</template>
