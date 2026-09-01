<script setup lang="ts">
import type { MachineModel, StationCapacity } from "@/types";

const props = defineProps<{
  models: MachineModel[];
  modelId: number | null;
  loading: boolean;
  savingMapping: boolean;
  loadedAt: string;
  updatedAt: string;
  stationCapacity: StationCapacity | null;
  currentStationHasBottleneck: boolean;
  stationConstraintTitle: string;
  stationConstraintHint: string;
  isMainOverview: boolean;
  detailMode: "overview" | "configure";
  backLabel?: string;
}>();

const emit = defineEmits<{
  back: [];
  openOverview: [];
  openConfigure: [];
  focusBottleneck: [];
  "update:modelId": [value: number | null];
}>();

function onModelChange(event: Event): void {
  const value = Number.parseInt((event.target as HTMLSelectElement).value, 10);
  emit("update:modelId", Number.isFinite(value) ? value : null);
}
</script>

<template>
  <div class="production-header-section">
    <div class="page-head-actions">
      <button class="outline-btn" type="button" @click="emit('back')">{{ backLabel || "返回搜尋" }}</button>
    </div>
    <nav class="page-tabs" data-tour="production-tabs" aria-label="生產管理檢視切換">
      <button class="page-tab" type="button" :class="{ active: isMainOverview }" @click="emit('openOverview')">
        總覽
      </button>
      <button class="page-tab" type="button" :class="{ active: detailMode === 'configure' }" @click="emit('openConfigure')">
        產能設定
      </button>
    </nav>

    <section class="filter-row" :class="{ configure: !isMainOverview }" data-tour="production-filter-row">
      <div class="filter-group">
        <span class="filter-row-label">目前篩選條件</span>
        <div class="filter-fields">
          <label class="filter-field">
            <span>機種</span>
            <select :value="modelId ?? undefined" :disabled="loading || savingMapping" @change="onModelChange">
              <option v-for="model in models" :key="`summary-model-${model.id}`" :value="model.id">{{ model.code }}</option>
            </select>
          </label>
        </div>
        <p class="filter-row-meta">站點請直接從下方總覽表點選。建立日期 {{ loadedAt || "-" }}　更新日期 {{ updatedAt || "-" }}</p>
      </div>

      <div v-if="isMainOverview" class="result-group">
        <span class="filter-row-label">目前站點結果</span>
        <div class="result-fields">
          <div class="result-stat" :class="{ alert: (stationCapacity?.max_open_station_count ?? 0) <= 0 }">
            <span>最大開站數</span>
            <strong>{{ stationCapacity?.max_open_station_count ?? 0 }}</strong>
            <small>只開這一站時可支援的最大站數</small>
          </div>
          <button class="result-stat result-stat-action" type="button" :disabled="!stationCapacity?.bottleneck_fixture_code || !currentStationHasBottleneck" @click="emit('focusBottleneck')">
            <span>{{ stationConstraintTitle }}</span>
            <strong>{{ stationCapacity?.bottleneck_fixture_code || "-" }}</strong>
            <small>{{ stationConstraintHint }}</small>
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.production-header-section {
  display: grid;
  gap: 8px;
}

.page-head-actions {
  display: flex;
  justify-content: flex-end;
}

.page-tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--line);
  padding-bottom: 0;
}

.page-tab {
  border: none;
  background: transparent;
  padding: 9px 14px;
  font-size: 13px;
  font-weight: 700;
  color: var(--muted);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 0.15s ease, border-color 0.15s ease;
}

.page-tab:hover {
  color: #344563;
}

.page-tab.active {
  color: var(--blue);
  border-bottom-color: var(--blue);
}

.filter-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.filter-row.configure {
  grid-template-columns: 1fr;
}

.filter-group,
.result-group {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
  padding: 10px 12px;
  display: grid;
  gap: 8px;
  align-content: start;
}

.result-group {
  background: linear-gradient(180deg, #f8fbff 0%, #f2f7ff 100%);
}

.filter-row-label {
  color: var(--muted);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.filter-fields,
.result-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.filter-fields {
  grid-template-columns: minmax(0, 280px);
}

.filter-field {
  display: grid;
  gap: 4px;
}

.filter-field span {
  color: var(--muted);
  font-size: 11px;
}

.filter-field select {
  min-height: 34px;
  padding-block: 5px;
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  padding-inline: 10px;
  background: #fff;
  font: inherit;
}

.filter-row-meta {
  margin: 0;
  color: #5d6d89;
  font-size: 11px;
  line-height: 1.25;
}

.result-stat {
  display: grid;
  gap: 2px;
}

.result-stat-action {
  border: 1px solid #d7e2f5;
  border-radius: 12px;
  background: #fff;
  padding: 10px 12px;
  text-align: left;
  cursor: pointer;
  transition: transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
}

.result-stat-action:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: #bfd0ef;
  box-shadow: 0 8px 18px rgba(47, 110, 229, 0.1);
}

.result-stat-action:disabled {
  cursor: default;
  opacity: 0.7;
}

.result-stat span {
  color: var(--muted);
  font-size: 11px;
  line-height: 1.2;
}

.result-stat strong {
  color: #22314a;
  font-size: 18px;
  line-height: 1.15;
}

.result-stat.alert strong {
  color: #c24b4b;
}

.result-stat small {
  color: #5d6d89;
  font-size: 11px;
  line-height: 1.25;
}

@media (max-width: 1200px) {
  .filter-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .filter-fields,
  .result-fields {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .page-tabs {
    overflow-x: auto;
  }
}
</style>
