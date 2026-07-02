<script setup lang="ts">
import { nextTick, ref, watch } from "vue";
import type { ModelQuery, ModelQueryStationRequirement, StationCapacity, StockStatus } from "@/types";
import { stockStatusLabel } from "@/utils/display";
import UiStatusPill from "@/components/UiStatusPill.vue";

const props = defineProps<{
  loading: boolean;
  selectedModelCode: string;
  selectedStationCode: string;
  selectedStationId: number | null;
  stationCapacity: StationCapacity | null;
  modelQuery: ModelQuery | null;
  selectedStationQueryRows: ModelQueryStationRequirement[];
  highlightFixtureCode?: string;
  highlightTrigger?: number;
}>();

const emit = defineEmits<{
  refreshCapacity: [];
  refreshModelQuery: [];
  "update:selectedStationId": [stationId: number | null];
}>();

function stockStatusNote(status: StockStatus): string {
  return status === "normal" ? "-" : "庫存不足";
}

function overviewCapacityClass(value: number): string {
  if (value <= 0) return "zero";
  if (value <= 1) return "low";
  if (value <= 3) return "medium";
  return "healthy";
}

function detailBottleneckClass(status: StockStatus): string {
  return status === "normal" ? "normal" : "blocked";
}

const highlightedFixtureCode = ref("");
const detailRowRefs = new Map<string, HTMLTableRowElement>();

function setDetailRowRef(fixtureCode: string, element: HTMLTableRowElement | null): void {
  if (element) {
    detailRowRefs.set(fixtureCode, element);
    return;
  }
  detailRowRefs.delete(fixtureCode);
}

async function focusBottleneckRow(): Promise<void> {
  const targetCode = props.highlightFixtureCode?.trim();
  if (!targetCode) {
    return;
  }
  await nextTick();
  const row = detailRowRefs.get(targetCode);
  if (!row) {
    return;
  }
  highlightedFixtureCode.value = targetCode;
  row.scrollIntoView({ behavior: "smooth", block: "center" });
  window.setTimeout(() => {
    if (highlightedFixtureCode.value === targetCode) {
      highlightedFixtureCode.value = "";
    }
  }, 2200);
}

watch(
  () => props.highlightTrigger,
  async () => {
    await focusBottleneckRow();
  }
);
</script>

<template>
  <article class="panel">
    <div v-if="loading" class="loading-banner">資料載入中，請稍候...</div>

    <section class="station-overview">
      <div class="head-row compact-head">
        <div>
          <h2>站點總覽</h2>
          <p class="overview-story">先掃描整個機種的站點開站能力，再點一個站看瓶頸明細。</p>
        </div>
        <span class="overview-count">{{ modelQuery?.stations?.length || 0 }} 站</span>
      </div>
      <table class="query-table compact-query-table">
        <thead>
          <tr>
            <th>站點</th>
            <th>站點名稱</th>
            <th>最大開站數</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="stationRow in modelQuery?.stations || []"
            :key="stationRow.station_id"
            class="overview-row"
            :class="[
              `capacity-${overviewCapacityClass(stationRow.max_open_station_count)}`,
              { selected: stationRow.station_id === selectedStationId }
            ]"
            @click="emit('update:selectedStationId', stationRow.station_id)"
          >
            <td>{{ stationRow.station_code }}</td>
            <td>{{ stationRow.station_name || "-" }}</td>
            <td>
              <span class="capacity-badge" :class="overviewCapacityClass(stationRow.max_open_station_count)">
                {{ stationRow.max_open_station_count }}
              </span>
            </td>
          </tr>
          <tr v-if="!loading && (modelQuery?.stations || []).length === 0">
            <td colspan="3" class="empty-cell">目前沒有可顯示的站點開站資料</td>
          </tr>
        </tbody>
      </table>
    </section>

    <div class="drilldown-bridge">
      <span class="drilldown-pill">總覽 -> 明細</span>
      <p>已選站點 {{ selectedStationCode || stationCapacity?.station_code || "-" }}，往下查看是哪支治具限制開站。</p>
    </div>

    <div class="query-inline drilldown-panel">
      <div class="head-row compact-head">
        <div>
          <h2>站點瓶頸明細</h2>
          <p class="meta">機種：{{ modelQuery?.model_code || selectedModelCode || "-" }}　站點：{{ selectedStationCode || stationCapacity?.station_code || "-" }}</p>
        </div>
        <button class="ghost-btn" :disabled="loading" @click="$emit('refreshModelQuery')">刷新</button>
      </div>
      <table class="query-table compact-query-table">
        <thead>
          <tr>
            <th>Fixture</th>
            <th>需求數 (Req)</th>
            <th>可開站數 (Cap)</th>
            <th>瓶頸狀態</th>
            <th>備註</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="fixtureRow in selectedStationQueryRows"
            :key="`${fixtureRow.station_id}-${fixtureRow.fixture_id}`"
            class="detail-row"
            :class="[
              detailBottleneckClass(fixtureRow.stock_status),
              { highlighted: highlightedFixtureCode === fixtureRow.fixture_code }
            ]"
            :ref="(element) => setDetailRowRef(fixtureRow.fixture_code, element as HTMLTableRowElement | null)"
          >
            <td>{{ fixtureRow.fixture_code }}</td>
            <td>{{ fixtureRow.required_qty }}</td>
            <td>{{ fixtureRow.max_open_station_count }}</td>
            <td>
              <UiStatusPill :label="stockStatusLabel(fixtureRow.stock_status)" :tone="fixtureRow.stock_status === 'normal' ? 'normal' : 'danger'" />
            </td>
            <td>{{ stockStatusNote(fixtureRow.stock_status) }}</td>
          </tr>
          <tr v-if="!loading && selectedStationQueryRows.length === 0">
            <td colspan="5" class="empty-cell">目前沒有可顯示的站點治具資料</td>
          </tr>
        </tbody>
      </table>
    </div>
  </article>
</template>

<style scoped>
.panel,
.capacity-left {
  display: grid;
  gap: 12px;
  align-content: start;
  position: relative;
}

.capacity-stat-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.capacity-stat-card {
  border: 1px solid var(--line);
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  padding: 12px 14px;
  display: grid;
  gap: 4px;
}

.capacity-stat-card span,
.capacity-stat-card small {
  color: var(--muted);
}

.capacity-stat-card strong {
  color: var(--text);
  font-size: 22px;
  line-height: 1.1;
}

.capacity-select {
  width: 100%;
  margin-top: 4px;
}

.capacity-note {
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: #f8fbff;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
}

.station-overview {
  display: grid;
  gap: 10px;
}

.overview-story {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.45;
}

.query-table {
  width: 100%;
  min-width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
  border: 1px solid var(--line);
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
}

.query-table th,
.query-table td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--line);
  text-align: left;
  vertical-align: middle;
  font-size: 12px;
}

.query-table th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: #f7f9fd;
  color: #52607b;
  font-weight: 700;
}

.query-table tbody tr:nth-child(even) {
  background: #fcfdff;
}

.query-table tbody tr:hover {
  background: #f3f7ff;
}

.overview-row {
  cursor: pointer;
  transition: background 0.15s ease, box-shadow 0.15s ease;
}

.overview-row.selected {
  background: linear-gradient(180deg, rgba(47, 110, 229, 0.1) 0%, rgba(47, 110, 229, 0.06) 100%);
  box-shadow: inset 4px 0 0 var(--tone-info);
}

.overview-row.capacity-zero {
  background: linear-gradient(180deg, #fff5f5 0%, #fff0f0 100%);
}

.overview-row.capacity-zero.selected {
  box-shadow: inset 4px 0 0 var(--tone-info);
}

.capacity-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 42px;
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 800;
}

.capacity-badge.zero {
  color: var(--tone-danger);
  background: var(--tone-danger-soft);
}

.capacity-badge.low {
  color: var(--tone-warn);
  background: var(--tone-warn-soft);
}

.capacity-badge.medium {
  color: var(--tone-info);
  background: var(--tone-info-soft);
}

.capacity-badge.healthy {
  color: var(--tone-success);
  background: var(--tone-success-soft);
}

.query-table tbody tr:last-child td {
  border-bottom: none;
}

.overview-count {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}

.drilldown-bridge {
  display: grid;
  gap: 4px;
  margin-top: -2px;
}

.drilldown-pill {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid rgba(47, 110, 229, 0.16);
  background: rgba(47, 110, 229, 0.08);
  color: var(--tone-info);
  font-size: 11px;
  font-weight: 800;
}

.drilldown-bridge p {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.45;
}

.drilldown-panel {
  position: relative;
  display: grid;
  gap: 10px;
  margin-left: 18px;
  padding: 14px 14px 0 18px;
  border-left: 2px solid rgba(47, 110, 229, 0.18);
}

.drilldown-panel::before {
  content: "";
  position: absolute;
  left: -8px;
  top: 18px;
  width: 12px;
  height: 12px;
  border-radius: 999px;
  background: var(--tone-info);
  box-shadow: 0 0 0 4px rgba(47, 110, 229, 0.12);
}

.note {
  margin-top: 4px;
}

.compact-query-table th,
.compact-query-table td {
  padding: 7px 10px;
}

.empty-cell {
  text-align: center;
  color: var(--muted);
}

.detail-row.blocked {
  background: linear-gradient(180deg, rgba(224, 142, 31, 0.14) 0%, rgba(224, 142, 31, 0.08) 100%);
  box-shadow: inset 4px 0 0 var(--tone-warn);
}

.detail-row.normal {
  background: #ffffff;
  color: #6f7f97;
}

.detail-row.normal td {
  color: #6f7f97;
}

.detail-row.highlighted {
  position: relative;
  background: linear-gradient(180deg, rgba(216, 71, 63, 0.14) 0%, rgba(216, 71, 63, 0.08) 100%);
  box-shadow: inset 4px 0 0 var(--tone-danger), 0 0 0 1px rgba(216, 71, 63, 0.08);
}

@media (max-width: 560px) {
  .capacity-stat-grid {
    grid-template-columns: 1fr;
  }
}
</style>
