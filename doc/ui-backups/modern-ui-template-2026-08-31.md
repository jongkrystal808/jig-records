# Modern UI Template Backup

Archived on 2026-08-31 before Modern UI was removed as an independently selectable system surface.

Workspace UI still reuses the canonical Modern route pages for production and master-data maintenance. This backup preserves the former Modern shell and `/search` composition so the standalone surface can be restored without reconstructing its template.

## `frontend/src/components/app/ModernSystemSurface.vue`

```vue
<script setup lang="ts">
import { RouterView } from "vue-router";
</script>

<template>
  <section class="modern-system-surface" data-system-ui="modern" aria-label="Modern UI 系統介面">
    <RouterView />
  </section>
</template>

<style scoped>
.modern-system-surface {
  min-height: 100%;
}
</style>
```

## `frontend/src/components/home/ModernUiSurface.vue`

```vue
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
```

## `frontend/src/pages/SearchHomePage.vue`

```vue
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
```

## Restore notes

1. Add `modern` back to the application surface type and the global surface switcher.
2. Mount `ModernSystemSurface.vue` as a root system-surface branch in `App.vue`.
3. Restore `ui_surface=modern` routing and preference handling instead of migrating it to `workspace`.
4. Keep the Modern top bar enabled for that branch.
