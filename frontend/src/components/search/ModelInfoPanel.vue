<script setup lang="ts">
import type { ModelQuery, ModelQueryFixture } from "@/types";
import { fallbackText, stockStatusLabel } from "@/utils/display";

defineProps<{
  model: { id: number; code: string; name: string } | null;
  queryData: ModelQuery | null;
  fixtures: Array<ModelQueryFixture & { identifierTags: string[] }>;
  visibleSections: Record<string, boolean>;
  formatCount: (value: number) => string;
  goToProduction: () => void;
}>();
</script>

<template>
  <div class="info-layout">
    <aside class="summary-rail">
      <section v-if="visibleSections.summary" class="info-card summary-card">
        <div class="summary-head">
          <div>
            <span class="eyebrow">Model</span>
            <h2>{{ model?.code || "尚未選擇機種" }}</h2>
            <p>{{ model?.name || "請先從查詢結果選擇機種" }}</p>
          </div>
          <button class="outline-btn" type="button" :disabled="!model" @click="goToProduction">前往產能管理</button>
        </div>

        <dl class="summary-grid">
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
    </aside>

    <div class="detail-scroll">
      <section v-if="visibleSections.stations" class="info-card">
        <div class="section-head"><h3>相關站點</h3><span>{{ queryData?.stations.length ?? 0 }} 站</span></div>
        <table v-if="(queryData?.stations.length ?? 0) > 0" class="info-table">
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
        <div v-else class="empty-text">尚無相關站點</div>
      </section>

      <section v-if="visibleSections.fixtures" class="info-card">
        <div class="section-head"><h3>相關治具</h3><span>{{ fixtures.length }} 種</span></div>
        <table v-if="fixtures.length > 0" class="info-table">
          <thead>
            <tr><th>治具</th><th>每站需求</th><th>庫存</th><th>狀態</th></tr>
          </thead>
          <tbody>
            <tr v-for="row in fixtures" :key="row.fixture_id">
              <td>
                <div class="table-stack">
                  <strong>{{ row.fixture_code }}</strong>
                  <span>{{ row.fixture_name }}</span>
                </div>
              </td>
              <td>{{ formatCount(row.required_per_station) }}</td>
              <td>{{ formatCount(row.stock_qty) }}</td>
              <td>{{ stockStatusLabel(row.stock_status) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-text">尚無關聯治具</div>
      </section>

      <section v-if="visibleSections.requirements" class="info-card">
        <div class="section-head"><h3>站點需求明細</h3><span>{{ queryData?.station_requirements.length ?? 0 }} 筆</span></div>
        <table v-if="(queryData?.station_requirements.length ?? 0) > 0" class="info-table">
          <thead>
            <tr><th>站點</th><th>治具</th><th>需求</th><th>庫存</th><th>開站量</th></tr>
          </thead>
          <tbody>
            <tr v-for="row in queryData?.station_requirements ?? []" :key="`${row.station_id}-${row.fixture_id}`">
              <td>{{ row.station_code }}</td>
              <td>{{ row.fixture_code }}</td>
              <td>{{ formatCount(row.required_qty) }}</td>
              <td>{{ formatCount(row.stock_qty) }}</td>
              <td>{{ formatCount(row.max_open_station_count) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-text">尚無站點需求資料</div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.info-layout {
  display: grid;
  grid-template-columns: minmax(260px, 1fr) minmax(0, 2fr);
  gap: 12px;
  min-height: min(72vh, 720px);
}

.summary-rail {
  min-height: 0;
}

.summary-card,
.info-card {
  border: 1px solid var(--line);
  border-radius: 18px;
  background: #fff;
  padding: 14px;
}

.summary-card {
  display: grid;
  gap: 14px;
  background: linear-gradient(180deg, #ffffff 0%, #f7faff 100%);
}

.summary-head,
.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}

.eyebrow {
  color: #2f6ee5;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h2,
h3 {
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
.section-head span,
.empty-text,
dt,
.table-stack span {
  color: #5d6d89;
  font-size: 12px;
}

p {
  margin: 4px 0 0;
}

.summary-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
  margin: 0;
}

dd {
  margin: 4px 0 0;
  color: #22314a;
  font-size: 16px;
  font-weight: 800;
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

.detail-scroll {
  min-height: 0;
  overflow: auto;
  display: grid;
  align-content: start;
  gap: 12px;
  padding-right: 4px;
}

.info-table {
  width: 100%;
  border-collapse: collapse;
}

.info-table th,
.info-table td {
  padding: 7px 8px;
  border-bottom: 1px solid var(--line);
  text-align: left;
  font-size: 12px;
}

.info-table thead th {
  background: var(--surface-secondary);
  color: #52607b;
  font-weight: 700;
}

.info-table tbody tr:last-child td {
  border-bottom: none;
}

.table-stack {
  display: grid;
  gap: 2px;
}

.table-stack strong {
  color: #22314a;
}

@media (max-width: 960px) {
  .info-layout {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .detail-scroll {
    overflow: visible;
    padding-right: 0;
  }

  .summary-head,
  .section-head {
    flex-direction: column;
  }
}
</style>
