<script setup lang="ts">
import type { ModelQuery, StationCapacity, StockStatus } from "@/types";
import { capacityStateLabel, stockStatusLabel } from "@/utils/display";
import UiStatusPill from "@/components/UiStatusPill.vue";

defineProps<{
  loading: boolean;
  selectedModelCode: string;
  selectedStationCode: string;
  stationCapacity: StationCapacity | null;
  modelQuery: ModelQuery | null;
  capacityCurrentOpen: number;
  capacityMaxOpen: number;
  capacityRemaining: number;
  capacityUsagePercent: number;
  capacityState: "idle" | "good" | "warn" | "danger";
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
        <p>站點產能與瓶頸治具摘要。</p>
      </div>
      <button class="ghost-btn" :disabled="loading" @click="$emit('refreshCapacity')">刷新</button>
    </div>
    <div v-if="loading" class="loading-banner">資料載入中，請稍候...</div>
    <div class="capacity-box">
      <div class="capacity-left">
        <p>站點：{{ selectedStationCode || stationCapacity?.station_code || "-" }}</p>
        <p>最大開站數：{{ stationCapacity?.max_open_station_count ?? 0 }}</p>
        <p>瓶頸治具：{{ stationCapacity?.bottleneck_fixture_code || "-" }}</p>
        <div class="capacity-meter">
          <div class="capacity-meter-track">
            <div class="capacity-meter-fill" :class="capacityState" :style="{ width: `${capacityUsagePercent}%` }"></div>
          </div>
          <div class="capacity-meter-meta">
            <span>目前 {{ capacityCurrentOpen }} / {{ capacityMaxOpen }} 開站</span>
            <span>剩餘 {{ capacityRemaining }} 開站</span>
          </div>
        </div>
      </div>
      <div class="capacity-right">
        <div>
          <span>目前開站數</span>
          <strong>{{ capacityCurrentOpen }}</strong>
        </div>
        <div>
          <span>可開站數</span>
          <strong>{{ capacityMaxOpen }}</strong>
        </div>
        <div>
          <span>狀態</span>
          <strong :class="capacityState === 'danger' ? 'danger' : capacityState === 'warn' ? 'warn' : 'ok'">
            {{ capacityStateLabel(capacityState) }}
          </strong>
        </div>
      </div>
    </div>

    <div class="query-inline">
      <div class="head-row compact-head">
        <div>
          <h2>Model Query</h2>
          <p class="meta">機種：{{ modelQuery?.model_code || selectedModelCode || "-" }}　最大開站數：{{ modelQuery?.max_open_station_count ?? 0 }}</p>
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
