<script setup lang="ts">
import UiStatusPill from "@/components/UiStatusPill.vue";
import type { Fixture, MachineModel, MaterialTransaction, StockStatus, StockSummary } from "@/types";
import { fallbackText, stockStatusLabel } from "@/utils/display";

defineProps<{
  fixture: Fixture | null;
  stock: StockSummary | null;
  imageUrl: string;
  imageLoadFailed: boolean;
  identifierTags: string[];
  relatedModels: MachineModel[];
  stationRows: Array<{ model_code: string; station_code: string; station_name: string; required_qty: number }>;
  transactions: MaterialTransaction[];
  visibleSections: Record<string, boolean>;
  formatCount: (value: number) => string;
  formatDate: (value: string | null | undefined) => string;
  stockTone: (status: StockStatus | undefined) => "normal" | "warn" | "danger" | "muted";
}>();

function transactionTypeLabel(value: MaterialTransaction["transaction_type"]): string {
  return value === "receipt" ? "收料" : "退料";
}
</script>

<template>
  <div class="info-layout">
    <aside class="summary-rail">
      <section v-if="visibleSections.summary" class="info-card summary-card">
        <div class="summary-head">
          <div>
            <span class="eyebrow">Fixture</span>
            <h2>{{ fixture?.code || "尚未選擇治具" }}</h2>
            <p>{{ fixture?.name || "請先從查詢結果選擇治具" }}</p>
          </div>
          <UiStatusPill :label="stockStatusLabel(stock?.stock_status ?? 'normal')" :tone="stockTone(stock?.stock_status)" />
        </div>

        <dl class="summary-grid">
          <div>
            <dt>庫存總量</dt>
            <dd>{{ formatCount(stock?.stock_qty ?? 0) }} pcs</dd>
          </div>
          <div>
            <dt>最低水位</dt>
            <dd>{{ formatCount(stock?.min_stock_qty ?? 0) }}</dd>
          </div>
          <div>
            <dt>產線儲位</dt>
            <dd>{{ fallbackText(fixture?.line_storage_location) }}</dd>
          </div>
          <div>
            <dt>部門儲位</dt>
            <dd>{{ fallbackText(fixture?.department_storage_location) }}</dd>
          </div>
        </dl>

        <div v-if="visibleSections.image" class="image-box">
          <img v-if="imageUrl && !imageLoadFailed" :src="imageUrl" :alt="fixture?.code || 'fixture image'" />
          <div v-else class="placeholder">目前沒有可顯示的圖片</div>
        </div>
      </section>
    </aside>

    <div class="detail-scroll">
      <section v-if="visibleSections.identifier" class="info-card">
        <div class="section-head"><h3>識別碼庫存</h3></div>
        <div v-if="identifierTags.length > 0" class="chip-list">
          <span v-for="tag in identifierTags" :key="tag" class="chip">{{ tag }}</span>
        </div>
        <div v-else class="empty-text">目前沒有識別碼庫存摘要</div>
      </section>

      <section v-if="visibleSections.transactions" class="info-card">
        <div class="section-head"><h3>最近收退料</h3><span>{{ transactions.length }} 筆</span></div>
        <table v-if="transactions.length > 0" class="info-table">
          <thead>
            <tr><th>類型</th><th>日期</th><th>單號</th><th>識別碼</th><th>數量</th></tr>
          </thead>
          <tbody>
            <tr v-for="tx in transactions" :key="tx.id">
              <td>{{ transactionTypeLabel(tx.transaction_type) }}</td>
              <td>{{ formatDate(tx.occurred_at) }}</td>
              <td>{{ tx.transaction_no }}</td>
              <td>{{ tx.items[0]?.identifier || "-" }}</td>
              <td>{{ formatCount(tx.items.reduce((sum, item) => sum + item.quantity, 0)) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-text">尚無相關收退料資料</div>
      </section>

      <section v-if="visibleSections.models" class="info-card">
        <div class="section-head"><h3>相關機種</h3><span>{{ relatedModels.length }} 種</span></div>
        <div v-if="relatedModels.length > 0" class="chip-list">
          <span v-for="model in relatedModels" :key="model.id" class="chip">{{ model.code }}</span>
        </div>
        <div v-else class="empty-text">尚無關聯機種</div>
      </section>

      <section v-if="visibleSections.stations" class="info-card">
        <div class="section-head"><h3>站點詳細</h3><span>{{ stationRows.length }} 筆</span></div>
        <table v-if="stationRows.length > 0" class="info-table">
          <thead>
            <tr><th>機種</th><th>站點</th><th>站點名稱</th><th>需求數量</th></tr>
          </thead>
          <tbody>
            <tr v-for="row in stationRows" :key="`${row.model_code}-${row.station_code}`">
              <td>{{ row.model_code }}</td>
              <td>{{ row.station_code }}</td>
              <td>{{ row.station_name }}</td>
              <td>{{ formatCount(row.required_qty) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-text">尚無站點資料</div>
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
dt {
  color: #5d6d89;
  font-size: 12px;
}

p {
  margin: 4px 0 0;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin: 0;
}

.summary-grid .wide {
  grid-column: auto;
}

dd {
  margin: 4px 0 0;
  color: #22314a;
  font-size: 16px;
  font-weight: 800;
}

.image-box {
  min-height: 240px;
  border: 1px solid #d9e3f2;
  border-radius: 14px;
  background: #f8fbff;
  overflow: hidden;
  display: grid;
  place-items: center;
}

.image-box img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.placeholder {
  color: #72829d;
  font-size: 12px;
  text-align: center;
  padding: 16px;
}

.detail-scroll {
  min-height: 0;
  overflow: auto;
  display: grid;
  align-content: start;
  gap: 12px;
  padding-right: 4px;
}

.chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border: 1px solid #d7e2f5;
  border-radius: 999px;
  background: #f7faff;
  color: #35527d;
  font-size: 12px;
  font-weight: 700;
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

@media (max-width: 960px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .info-layout {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .detail-scroll {
    overflow: visible;
    padding-right: 0;
  }
}
</style>
