<script setup lang="ts">
import UiSplitDetailLayout from "@/components/UiSplitDetailLayout.vue";
import UiStatusPill from "@/components/UiStatusPill.vue";
import type { ModelQuery, ModelQueryFixture } from "@/types";
import { fallbackText, stockStatusLabel } from "@/utils/display";

defineProps<{
  model: { id: number; code: string; name: string } | null;
  queryData: ModelQuery | null;
  fixtures: Array<ModelQueryFixture & { identifierTags: string[] }>;
  visibleSections: Record<string, boolean>;
  formatCount: (value: number) => string;
  canAccessProduction: boolean;
  goToProduction: () => void;
}>();

function stockTone(status: string): "normal" | "warn" | "danger" {
  if (status === "normal") return "normal";
  if (status === "low_stock") return "warn";
  return "danger";
}
</script>

<template>
  <UiSplitDetailLayout>
    <template #summary>
      <section v-if="visibleSections.summary" class="ui-panel-card ui-panel-card--summary">
        <div class="ui-section-head">
          <div>
            <span class="ui-eyebrow">Model</span>
            <h2>{{ model?.code || "尚未選擇機種" }}</h2>
            <p>{{ model?.name || "請先從查詢結果選擇機種" }}</p>
          </div>
          <button
            v-if="canAccessProduction"
            class="outline-btn"
            type="button"
            :disabled="!model"
            @click="goToProduction"
          >
            前往產能管理
          </button>
        </div>

        <dl class="ui-summary-grid ui-summary-grid--single">
          <div>
            <dt>站點數</dt>
            <dd>{{ formatCount(queryData?.station_count ?? 0) }}</dd>
          </div>
          <div>
            <dt>治具種類</dt>
            <dd>{{ formatCount(queryData?.fixture_type_count ?? 0) }}</dd>
          </div>
          <div>
            <dt>所需治具總庫存量</dt>
            <dd>{{ formatCount(queryData?.total_stock_qty ?? 0) }}</dd>
          </div>
          <div>
            <dt>代表性開站量</dt>
            <dd>{{ formatCount(queryData?.max_open_station_count ?? 0) }}</dd>
          </div>
        </dl>
      </section>
    </template>

      <section v-if="visibleSections.stations" class="ui-panel-card">
        <div class="ui-section-head"><h3>相關站點</h3><span class="section-meta">{{ queryData?.stations.length ?? 0 }} 站</span></div>
        <table v-if="(queryData?.stations.length ?? 0) > 0" class="ui-info-table">
          <thead>
            <tr><th>站點</th><th>名稱</th><th>最大開站量</th><th>瓶頸治具</th></tr>
          </thead>
          <tbody>
            <tr v-for="station in queryData?.stations ?? []" :key="station.station_id">
              <td>{{ station.station_code }}</td>
              <td>{{ station.station_name }}</td>
              <td>{{ formatCount(station.max_open_station_count) }}</td>
              <td>{{ fallbackText(station.bottleneck_fixture_code) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="ui-empty-text">尚無相關站點</div>
      </section>

      <section v-if="visibleSections.fixtures" class="ui-panel-card">
        <div class="ui-section-head"><h3>相關治具</h3><span class="section-meta">{{ fixtures.length }} 種</span></div>
        <table v-if="fixtures.length > 0" class="ui-info-table">
          <thead>
            <tr><th>治具</th><th>每站需求</th><th>庫存</th><th>狀態</th></tr>
          </thead>
          <tbody>
            <tr v-for="row in fixtures" :key="row.fixture_id">
              <td>
                <div class="ui-table-stack">
                  <strong>{{ row.fixture_code }}</strong>
                  <span>{{ row.fixture_name }}</span>
                </div>
              </td>
              <td>{{ formatCount(row.required_per_station) }}</td>
              <td>{{ formatCount(row.stock_qty) }}</td>
              <td><UiStatusPill :label="stockStatusLabel(row.stock_status)" :tone="stockTone(row.stock_status)" /></td>
            </tr>
          </tbody>
        </table>
        <div v-else class="ui-empty-text">尚無關聯治具</div>
      </section>

      <section v-if="visibleSections.requirements" class="ui-panel-card">
        <div class="ui-section-head"><h3>站點需求明細</h3><span class="section-meta">{{ queryData?.station_requirements.length ?? 0 }} 筆</span></div>
        <p v-if="queryData?.station_requirements.some((row) => row.designated_mode)" class="designated-mode-note">
          指定模式列的庫存與開站量只採計列出的 identifier。
        </p>
        <table v-if="(queryData?.station_requirements.length ?? 0) > 0" class="ui-info-table">
          <thead>
            <tr><th>站點</th><th>治具</th><th>需求</th><th>使用模式</th><th>庫存</th><th>開站量</th></tr>
          </thead>
          <tbody>
            <tr v-for="row in queryData?.station_requirements ?? []" :key="`${row.station_id}-${row.fixture_id}`">
              <td>{{ row.station_code }}</td>
              <td>{{ row.fixture_code }}</td>
              <td>{{ formatCount(row.required_qty) }}</td>
              <td>
                <div v-if="row.designated_mode" class="designated-mode-cell">
                  <span>指定模式</span>
                  <small>{{ row.designated_identifiers.join("、") }}</small>
                </div>
                <span v-else>不限 identifier</span>
              </td>
              <td>{{ formatCount(row.stock_qty) }}</td>
              <td>{{ formatCount(row.max_open_station_count) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="ui-empty-text">尚無站點需求資料</div>
      </section>
  </UiSplitDetailLayout>
</template>

<style scoped>
h2,
h3,
.section-meta {
  margin: 0;
  color: #22314a;
}

h2 {
  font-size: 22px;
}

h3 {
  font-size: 16px;
}

p,
dt,
.ui-table-stack span {
  color: #5d6d89;
  font-size: 12px;
}

p {
  margin: 4px 0 0;
}

.designated-mode-note {
  margin: 8px 0 10px;
  border: 1px solid #c9dbf7;
  border-radius: 10px;
  padding: 8px 10px;
  background: #f2f7ff;
  color: #315f9f;
}

.designated-mode-cell {
  display: grid;
  gap: 3px;
}

.designated-mode-cell span {
  width: fit-content;
  border-radius: 999px;
  padding: 2px 7px;
  background: #e8f1ff;
  color: #215fac;
  font-size: 11px;
  font-weight: 800;
}

.designated-mode-cell small {
  color: #53627b;
  overflow-wrap: anywhere;
}

@media (max-width: 960px) {
  .ui-section-head {
    flex-direction: column;
  }
}
</style>
