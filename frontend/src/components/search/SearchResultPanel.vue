<script setup lang="ts">
import InlineSpinner from "@/components/common/InlineSpinner.vue";

type SearchMode = "fixture" | "model";
type DetailTab = "info" | "edit";

const props = defineProps<{
  canEdit: boolean;
  showMaintenanceTab: boolean;
  detailTab: DetailTab;
  loading: boolean;
  empty: boolean;
  mode: SearchMode;
}>();

const emit = defineEmits<{
  "update:detailTab": [value: DetailTab];
  create: [];
}>();

// Keep result-shell states centralized so the page only decides which content slot to render.
</script>

<template>
  <article class="detail-panel">
    <div v-if="showMaintenanceTab && canEdit" class="detail-panel-tabs">
      <button class="detail-panel-tab" :class="{ active: detailTab === 'info' }" type="button" @click="emit('update:detailTab', 'info')">資訊</button>
      <button class="detail-panel-tab" :class="{ active: detailTab === 'edit' }" type="button" @click="emit('update:detailTab', 'edit')">編輯</button>
    </div>

    <div v-if="loading" class="loading-panel">
      <InlineSpinner label="載入查詢資料..." />
    </div>

    <div v-else-if="empty" class="empty-state detail-empty-state">
      <strong>找不到符合條件的資料</strong>
      <span>請調整搜尋條件，或直接建立新的 {{ mode === "fixture" ? "治具" : "機種" }}。</span>
      <button v-if="canEdit" class="outline-btn empty-action" type="button" @click="emit('create')">找不到，新增一筆？</button>
    </div>

    <div v-else class="result-content">
      <slot />
    </div>
  </article>
</template>

<style scoped>
.detail-panel {
  min-height: 0;
  padding: 12px;
  display: grid;
  align-content: start;
  gap: 14px;
  position: sticky;
  top: 12px;
  border: 1px solid var(--line);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: var(--shadow);
}

.detail-panel-tabs {
  display: inline-flex;
  align-items: center;
  gap: 0;
  width: fit-content;
  border: 1px solid color-mix(in srgb, var(--blue) 18%, var(--line));
  border-radius: 12px;
  background: color-mix(in srgb, var(--blue-soft) 70%, white);
  overflow: hidden;
}

.detail-panel-tab {
  border: 0;
  background: transparent;
  color: #5c6a81;
  padding: 10px 18px;
  font-size: 13px;
  font-weight: 800;
}

.detail-panel-tab + .detail-panel-tab {
  border-left: 1px solid color-mix(in srgb, var(--blue) 18%, var(--line));
}

.detail-panel-tab.active {
  background: color-mix(in srgb, var(--blue-soft) 92%, white);
  color: var(--tone-info);
}

.empty-state {
  display: grid;
  gap: 10px;
  padding: 18px;
  border: 1px dashed var(--line-strong);
  border-radius: 14px;
  background: #fafcff;
  color: #5d6d89;
  font-size: 12px;
}

.empty-action {
  width: fit-content;
}

.detail-empty-state {
  min-height: 280px;
  place-content: center;
}

.loading-panel {
  min-height: 180px;
  display: grid;
  place-items: center;
}

.outline-btn {
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  background: linear-gradient(180deg, #ffffff 0%, #f7f9fd 100%);
  color: #5b677d;
  padding: 8px 14px;
  min-height: 36px;
  font-weight: 700;
}

.result-content {
  min-width: 0;
}

@media (max-width: 960px) {
  .detail-panel {
    position: static;
    top: auto;
  }
}
</style>
