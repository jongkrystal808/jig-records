<script setup lang="ts">
import type { ModelQuery, StationCapacity, StockStatus } from "@/types";
import { stockStatusLabel } from "@/utils/display";
import UiStatusPill from "@/components/UiStatusPill.vue";

defineProps<{
  loading: boolean;
  selectedModelCode: string;
  selectedStationCode: string;
  stationCapacity: StationCapacity | null;
  modelQuery: ModelQuery | null;
  capacityMaxOpen: number;
}>();

defineEmits<{
  refreshCapacity: [];
  refreshModelQuery: [];
}>();

function stockStatusNote(status: StockStatus): string {
  return status === "normal" ? "-" : "庫存不足";
}
</script>

<template>
  <article class="panel">
    <div class="section-head">
      <div>
        <h2>Station Capacity</h2>
      </div>
      <button class="ghost-btn" :disabled="loading" @click="$emit('refreshCapacity')">刷新</button>
    </div>
    <div v-if="loading" class="loading-banner">資料載入中，請稍候...</div>
    <div class="capacity-box">
      <div class="capacity-left">
        <div class="capacity-stat-grid">
          <article class="capacity-stat-card">
            <span>站點</span>
            <strong>{{ selectedStationCode || stationCapacity?.station_code || "-" }}</strong>
            <small>目前檢視站點</small>
          </article>
          <article class="capacity-stat-card">
            <span>最大開站數</span>
            <strong>{{ stationCapacity?.max_open_station_count ?? 0 }}</strong>
            <small>只開這一站時可支援的最大站數</small>
          </article>
          <article class="capacity-stat-card">
            <span>瓶頸治具</span>
            <strong>{{ stationCapacity?.bottleneck_fixture_code || "-" }}</strong>
            <small>限制治具</small>
          </article>
          <article class="capacity-stat-card">
            <span>計算模式</span>
            <strong>單站獨立</strong>
            <small>不扣其他站，不混算其他機種</small>
          </article>
        </div>
      </div>
      <div class="capacity-right">
        <div>
          <span>指定機種</span>
          <strong>{{ modelQuery?.model_code || selectedModelCode || "-" }}</strong>
        </div>
        <div>
          <span>指定站點</span>
          <strong>{{ selectedStationCode || stationCapacity?.station_code || "-" }}</strong>
        </div>
        <div>
          <span>狀態</span>
          <strong :class="capacityMaxOpen === 0 ? 'danger' : 'ok'">
            {{ capacityMaxOpen === 0 ? "無法開站" : "可開站" }}
          </strong>
        </div>
      </div>
    </div>

    <div class="query-inline">
      <div class="head-row compact-head">
        <div>
          <h2>Selected Station Query</h2>
          <p class="meta">機種：{{ modelQuery?.model_code || selectedModelCode || "-" }}　站點：{{ selectedStationCode || stationCapacity?.station_code || "-" }}</p>
        </div>
        <button class="ghost-btn" :disabled="loading" @click="$emit('refreshModelQuery')">刷新</button>
      </div>
      <table class="query-table compact-query-table">
        <thead>
          <tr>
            <th>Fixture</th>
            <th>目前庫存 (Stock)</th>
            <th>需求數 (Req)</th>
            <th>可開站數 (Cap)</th>
            <th>瓶頸狀態</th>
            <th>備註</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="fixtureRow in modelQuery?.fixtures || []" :key="fixtureRow.fixture_id">
            <td>{{ fixtureRow.fixture_code }}</td>
            <td>{{ fixtureRow.stock_qty }}</td>
            <td>{{ fixtureRow.required_per_station }}</td>
            <td>{{ fixtureRow.max_open_station_count }}</td>
            <td>
              <UiStatusPill :label="stockStatusLabel(fixtureRow.stock_status)" :tone="fixtureRow.stock_status === 'normal' ? 'normal' : 'danger'" />
            </td>
            <td>{{ stockStatusNote(fixtureRow.stock_status) }}</td>
          </tr>
          <tr v-if="!loading && (modelQuery?.fixtures || []).length === 0">
            <td colspan="6" class="empty-cell">目前沒有可顯示的 Model Query 資料</td>
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

.capacity-note {
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: #f8fbff;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
}

@media (max-width: 720px) {
  .capacity-stat-grid {
    grid-template-columns: 1fr;
  }
}
</style>
