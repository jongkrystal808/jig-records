<script setup lang="ts">
import { computed } from "vue";

import UiSplitDetailLayout from "@/components/UiSplitDetailLayout.vue";
import UiStatusPill from "@/components/UiStatusPill.vue";
import type { Fixture, MachineModel, MaterialTransaction, StockStatus, StockSummary } from "@/types";
import { fallbackText, stockStatusLabel, type IdentifierStockOwnershipGroup } from "@/utils/display";

const TRANSACTION_PREVIEW_COUNT = 8;

const props = defineProps<{
  fixture: Fixture | null;
  canOperateInventory: boolean;
  stock: StockSummary | null;
  imageUrl: string;
  imageLoadFailed: boolean;
  identifierGroups: IdentifierStockOwnershipGroup[];
  identifierTotalQty: number;
  relatedModels: MachineModel[];
  stationRows: Array<{ model_code: string; station_code: string; station_name: string; required_qty: number }>;
  transactions: MaterialTransaction[];
  matchedIdentifier: string;
  visibleSections: Record<string, boolean>;
  formatCount: (value: number) => string;
  formatDate: (value: string | null | undefined) => string;
  stockTone: (status: StockStatus | undefined) => "normal" | "warn" | "danger" | "muted";
}>();

const emit = defineEmits<{
  openTransactionOverview: [];
  openBatchImport: [];
}>();

function transactionTypeLabel(value: MaterialTransaction["transaction_type"]): string {
  return value === "receipt" ? "收料" : "退料";
}

function displayTransactionNo(value: string | null): string {
  return value?.trim() || "（無單號）";
}

const visibleTransactions = computed(() => props.transactions.slice(0, TRANSACTION_PREVIEW_COUNT));
const shouldShowTransactionOverviewAction = computed(() => props.transactions.length > 0);
</script>

<template>
  <UiSplitDetailLayout>
    <template #summary>
      <section v-if="visibleSections.summary" class="ui-panel-card ui-panel-card--summary">
        <div class="ui-section-head">
          <div>
            <span class="ui-eyebrow">Fixture</span>
            <h2>{{ fixture?.code || "尚未選擇治具" }}</h2>
            <p>{{ fixture?.name || "請先從查詢結果選擇治具" }}</p>
          </div>
          <UiStatusPill :label="stockStatusLabel(stock?.stock_status ?? 'normal')" :tone="stockTone(stock?.stock_status)" />
        </div>

        <dl class="ui-summary-grid">
          <div>
            <dt>庫存總量</dt>
            <dd>{{ formatCount(stock?.stock_qty ?? 0) }} pcs</dd>
          </div>
          <div>
            <dt>客供庫存</dt>
            <dd>{{ formatCount(stock?.customer_supplied_qty ?? 0) }} pcs</dd>
          </div>
          <div>
            <dt>自購庫存</dt>
            <dd>{{ formatCount(stock?.self_purchased_qty ?? 0) }} pcs</dd>
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

        <div v-if="visibleSections.image" class="ui-image-box">
          <img v-if="imageUrl && !imageLoadFailed" :src="imageUrl" :alt="fixture?.code || 'fixture image'" />
          <div v-else class="ui-image-placeholder">目前沒有可顯示的圖片</div>
        </div>

        <div v-if="fixture && canOperateInventory" class="section-actions section-actions-left">
          <button class="section-toggle-btn" type="button" @click="emit('openBatchImport')">以此治具收 / 退料</button>
        </div>
      </section>
    </template>

      <section v-if="visibleSections.identifier" class="ui-panel-card">
        <div class="ui-section-head">
          <h3>datecode/編號庫存</h3>
          <span class="section-meta">總數 {{ formatCount(identifierTotalQty) }} pcs</span>
        </div>
        <div v-if="identifierGroups.length > 0" class="identifier-stock-groups">
          <section
            v-for="group in identifierGroups"
            :key="group.ownershipType"
            class="identifier-stock-group"
            :class="`identifier-stock-group--${group.ownershipType}`"
          >
            <div class="identifier-stock-group-head">
              <strong>{{ group.label }}</strong>
              <span>{{ formatCount(group.totalQty) }} pcs</span>
            </div>
            <div class="ui-chip-list">
              <span v-for="entry in group.entries" :key="entry.identifier" class="ui-chip">
                {{ entry.identifier }}: {{ formatCount(entry.quantity) }} pcs
              </span>
            </div>
          </section>
        </div>
        <div v-else class="ui-empty-text">目前沒有 datecode/編號庫存摘要</div>
      </section>

      <section v-if="visibleSections.transactions" class="ui-panel-card">
        <div class="ui-section-head">
          <h3>{{ matchedIdentifier ? `${matchedIdentifier} 收退料記錄` : "收退料記錄" }}</h3>
          <span class="section-meta">近期 {{ visibleTransactions.length }} 筆</span>
        </div>
        <table v-if="transactions.length > 0" class="ui-info-table">
          <thead>
            <tr><th>類型</th><th>日期</th><th>單號</th><th>datecode/編號</th><th>數量</th></tr>
          </thead>
          <tbody>
            <tr v-for="tx in visibleTransactions" :key="tx.id">
              <td><span class="status-pill" :class="tx.transaction_type">{{ transactionTypeLabel(tx.transaction_type) }}</span></td>
              <td>{{ formatDate(tx.occurred_at) }}</td>
              <td>{{ displayTransactionNo(tx.transaction_no) }}</td>
              <td>{{ tx.items[0]?.identifier || "-" }}</td>
              <td>{{ formatCount(tx.items.reduce((sum, item) => sum + item.quantity, 0)) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="shouldShowTransactionOverviewAction" class="section-actions">
          <button class="section-toggle-btn" type="button" @click="emit('openTransactionOverview')">
            到總檢視看完整歷史
          </button>
        </div>
        <div v-else class="ui-empty-text">尚無相關收退料資料</div>
      </section>

      <section v-if="visibleSections.models" class="ui-panel-card">
        <div class="ui-section-head"><h3>相關機種</h3><span class="section-meta">{{ relatedModels.length }} 種</span></div>
        <div v-if="relatedModels.length > 0" class="ui-chip-list">
          <span v-for="model in relatedModels" :key="model.id" class="ui-chip">{{ model.code }}</span>
        </div>
        <div v-else class="ui-empty-text">尚無關聯機種</div>
      </section>

      <section v-if="visibleSections.stations" class="ui-panel-card">
        <div class="ui-section-head"><h3>站點詳細</h3><span class="section-meta">{{ stationRows.length }} 筆</span></div>
        <table v-if="stationRows.length > 0" class="ui-info-table">
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
        <div v-else class="ui-empty-text">尚無站點資料</div>
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
dt {
  color: #5d6d89;
  font-size: 12px;
}

p {
  margin: 4px 0 0;
}

.section-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}

.section-actions-left {
  justify-content: flex-start;
}

.identifier-stock-groups {
  display: grid;
  gap: 12px;
}

.identifier-stock-group {
  display: grid;
  gap: 8px;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #f8faff;
}

.identifier-stock-group--self_purchased {
  background: #fffaf2;
}

.identifier-stock-group-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #40516d;
  font-size: 12px;
}

.identifier-stock-group-head strong {
  color: #22314a;
  font-size: 13px;
}

.section-toggle-btn {
  border: 1px solid color-mix(in srgb, var(--blue) 18%, var(--line));
  border-radius: 999px;
  background: color-mix(in srgb, var(--blue-soft) 72%, white);
  color: var(--tone-info);
  min-height: 34px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 800;
}

.section-toggle-btn:disabled {
  opacity: 0.72;
  cursor: wait;
}

@media (max-width: 960px) {
  .ui-section-head {
    flex-direction: column;
  }
}
</style>
