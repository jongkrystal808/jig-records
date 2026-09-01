<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  activeWorkspace: string;
  items: Array<{ key: string; label: string; shortLabel?: string }>;
  hint: string;
}>();

const emit = defineEmits<{
  select: [key: string];
}>();

const activeItem = computed(() =>
  props.items.find((item) => item.key === props.activeWorkspace) ?? props.items[0]
);

const groupDefinitions = [
  { key: "daily", label: "日常作業", workspaces: ["report", "import", "inventory-overview"] },
  { key: "maintenance", label: "設定維護", workspaces: ["production", "master", "image"] },
  { key: "system", label: "系統管理", workspaces: ["ledger", "quality"] }
] as const;

const workspaceGroups = computed(() =>
  groupDefinitions
    .map((group) => ({
      ...group,
      items: props.items.filter((item) => (group.workspaces as readonly string[]).includes(item.key))
    }))
    .filter((group) => group.items.length > 0)
);
</script>

<template>
  <nav class="form-workspace-selector" data-tour="form-workspace-switcher" aria-label="切換 Form UI 報表功能">
    <div class="form-workspace-context">
      <strong>目前模組</strong>
      <span class="form-workspace-current">{{ activeItem?.label }}</span>
      <span class="form-workspace-hint">{{ hint }}</span>
    </div>
    <div class="form-workspace-tabs" aria-label="切換報表資料表">
      <section v-for="group in workspaceGroups" :key="group.key" class="form-workspace-group">
        <span class="form-workspace-group-label">{{ group.label }}</span>
        <div class="form-workspace-group-tabs" role="tablist" :aria-label="group.label">
          <button
            v-for="item in group.items"
            :key="item.key"
            type="button"
            role="tab"
            class="form-workspace-tab"
            :class="{ active: activeWorkspace === item.key }"
            :aria-selected="activeWorkspace === item.key"
            :data-workspace="item.key"
            :data-tour="`form-workspace-${item.key}`"
            @click="emit('select', item.key)"
          >
            <span class="form-workspace-tab-label">{{ item.label }}</span>
          </button>
        </div>
      </section>
    </div>
  </nav>
</template>
