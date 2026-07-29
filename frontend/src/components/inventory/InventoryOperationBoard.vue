<script setup lang="ts">
import { computed, ref } from "vue";

import UiSummaryCards from "@/components/UiSummaryCards.vue";
import UiStatusPill from "@/components/UiStatusPill.vue";
import BatchImportPanel from "@/components/inventory/BatchImportPanel.vue";
import type { StockSummary } from "@/types";
import { stockStatusLabel } from "@/utils/display";

type SummaryCard = {
  label: string;
  value: number;
  tone: string;
  emphasis: boolean;
};

type RecentRow = {
  id: string;
  transaction_no: string | null;
  fixture_id: number | null;
  fixture_code: string;
  identifier: string | null;
  quantity: number;
};

type AlertRow = {
  fixture_id: number;
  fixture_code: string;
  fixture_name: string;
  stock_qty: number;
  min_stock_qty: number;
  stock_status: "low_stock" | "out_of_stock";
};

const props = defineProps<{
  customerId: number | undefined;
  tutorialMode: boolean;
  summaryCards: SummaryCard[];
  receiptRows: RecentRow[];
  returnRows: RecentRow[];
  stockRows: StockSummary[];
  alertRows: AlertRow[];
}>();

const emit = defineEmits<{
  refreshed: [];
}>();

const mode = ref<"receipt" | "return">("receipt");
const showStockPanel = ref(false);
const showAlertPanel = ref(false);

const operationBoardClass = computed(() => ({
  "layout-all-expanded": showStockPanel.value && showAlertPanel.value,
  "layout-stock-only": showStockPanel.value && !showAlertPanel.value,
  "layout-alert-only": !showStockPanel.value && showAlertPanel.value,
  "layout-all-collapsed": !showStockPanel.value && !showAlertPanel.value
}));

const currentRecentRows = computed(() => (mode.value === "receipt" ? props.receiptRows : props.returnRows));
const currentRecentTitle = computed(() => (mode.value === "receipt" ? "最近收料" : "最近退料"));
const currentRecentEmptyText = computed(() => (mode.value === "receipt" ? "尚無收料資料" : "尚無退料資料"));
const secondaryRecentSummary = computed(() =>
  mode.value === "receipt"
    ? `最近退料 ${props.returnRows.length} 筆`
    : `最近收料 ${props.receiptRows.length} 筆`
);

function stockWaterLevelPercent(row: StockSummary): number {
  const minStock = row.min_stock_qty ?? 0;
  if (minStock <= 0) {
    return row.stock_qty > 0 ? 100 : 0;
  }
  return Math.max(0, Math.min(100, Math.round((row.stock_qty / minStock) * 100)));
}

function displayTransactionNo(value: string | null): string {
  return value?.trim() || "（無單號）";
}
</script>

<template>
  <section class="inventory-board" :class="operationBoardClass">
    <UiSummaryCards class="inventory-summary-row" :cards="summaryCards" variant="compact" :desktop-columns="6" :tablet-columns="3" :mobile-columns="2" />

    <article class="panel op-panel" :class="mode">
      <div class="panel-head">
        <div class="panel-actions">
          <div class="segmented-control" data-tour="inventory-mode-switch" role="tablist" aria-label="收退料切換">
            <button class="segmented-btn" :class="{ active: mode === 'receipt' }" type="button" @click="mode = 'receipt'">
              收料
            </button>
            <button class="segmented-btn" :class="{ active: mode === 'return' }" type="button" @click="mode = 'return'">
              退料
            </button>
          </div>
          <div class="collapsed-panel-actions">
            <button class="toggle-btn collapsed-panel-chip" :class="{ active: showStockPanel }" type="button" @click="showStockPanel = !showStockPanel">
              現有治具庫存
              <span>{{ stockRows.length }} 筆</span>
            </button>
            <button class="toggle-btn collapsed-panel-chip" :class="{ active: showAlertPanel }" type="button" @click="showAlertPanel = !showAlertPanel">
              低水位提醒
              <span>{{ alertRows.length }} 項</span>
            </button>
          </div>
        </div>
      </div>

      <section class="batch-inline-panel" data-tour="inventory-batch-panel">
        <BatchImportPanel
          :customer-id="customerId"
          :tutorial-mode="tutorialMode"
          :mode="mode"
          :show-mode-switch="false"
          title="批次貼上匯入"
          description="共用批次匯入元件，同時提供 /inventory 與全域 Modal 使用。"
          @update:mode="mode = $event"
          @success="emit('refreshed')"
        />
      </section>

      <div class="recent-block" :class="mode">
        <section class="recent-section">
          <div class="sub-head">
            <h3>{{ currentRecentTitle }}</h3>
            <div class="sub-head-inline recent-summary-inline">
              <span>{{ currentRecentRows.length }} 筆</span>
              <span class="recent-secondary-summary">{{ secondaryRecentSummary }}</span>
            </div>
          </div>
          <table class="grid-table compact-table">
            <thead>
              <tr>
                <th>治具ID</th>
                <th>治具</th>
                <th>datecode/編號</th>
                <th>數量</th>
                <th>單號</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in currentRecentRows" :key="`recent-${mode}-${row.id}`">
                <td>{{ row.fixture_id }}</td>
                <td>{{ row.fixture_code || "-" }}</td>
                <td>{{ row.identifier || "-" }}</td>
                <td>{{ row.quantity }}</td>
                <td>{{ displayTransactionNo(row.transaction_no) }}</td>
              </tr>
              <tr v-if="currentRecentRows.length === 0">
                <td colspan="5" class="empty-cell">{{ currentRecentEmptyText }}</td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>
    </article>

    <article v-if="showStockPanel" class="panel stock-panel">
      <div class="sub-head">
        <h2>現有治具庫存</h2>
        <div class="sub-head-inline">
          <span>{{ stockRows.length }} 筆</span>
          <button class="toggle-btn small-toggle" type="button" :class="{ active: showStockPanel }" @click="showStockPanel = !showStockPanel">
            {{ showStockPanel ? "收起" : "展開" }}
          </button>
        </div>
      </div>
      <div v-show="showStockPanel" class="panel-table-scroll">
        <table class="grid-table">
          <thead>
            <tr>
              <th>治具編號</th>
              <th>數量 (pcs)</th>
              <th>水位</th>
              <th>狀態</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in stockRows" :key="row.fixture_id">
              <td>{{ row.fixture_code }}</td>
              <td>{{ row.stock_qty }}</td>
              <td>
                <div class="stock-meter" :class="row.stock_status">
                  <div class="stock-meter-track">
                    <div class="stock-meter-fill" :style="{ width: `${stockWaterLevelPercent(row)}%` }"></div>
                  </div>
                  <span>{{ row.stock_qty }} / {{ row.min_stock_qty || 0 }}</span>
                </div>
              </td>
              <td>
                <UiStatusPill :label="stockStatusLabel(row.stock_status)" :tone="row.stock_status === 'normal' ? 'normal' : 'danger'" />
              </td>
            </tr>
            <tr v-if="stockRows.length === 0">
              <td colspan="4" class="empty-cell">目前沒有庫存資料</td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>

    <div v-if="showAlertPanel" class="side-stack">
      <article class="panel alert-panel">
        <div class="sub-head">
          <h2>低水位提醒</h2>
          <div class="sub-head-inline">
            <span>{{ alertRows.length }} 項</span>
            <button class="toggle-btn small-toggle" type="button" :class="{ active: showAlertPanel }" @click="showAlertPanel = !showAlertPanel">
              {{ showAlertPanel ? "收起" : "展開" }}
            </button>
          </div>
        </div>
        <div v-show="showAlertPanel" class="panel-table-scroll">
          <table class="grid-table compact-table">
            <thead>
              <tr>
                <th>治具編號</th>
                <th>目前數量</th>
                <th>設定水位</th>
                <th>狀態</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in alertRows" :key="`a-${row.fixture_id}`">
                <td>{{ row.fixture_code }}</td>
                <td>{{ row.stock_qty }}</td>
                <td>{{ row.min_stock_qty }}</td>
                <td><UiStatusPill :label="stockStatusLabel(row.stock_status)" tone="danger" /></td>
              </tr>
              <tr v-if="alertRows.length === 0">
                <td colspan="4" class="empty-cell">目前沒有低水位提醒</td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.inventory-board {
  display: grid;
  grid-template-columns: minmax(0, 1.18fr) minmax(0, 0.92fr) minmax(0, 0.84fr);
  grid-template-rows: auto minmax(0, 1fr);
  gap: 8px;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  align-items: stretch;
}

.inventory-board.layout-stock-only,
.inventory-board.layout-alert-only {
  grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
}

.inventory-board.layout-all-collapsed {
  grid-template-columns: minmax(0, 1fr);
}

.inventory-summary-row {
  grid-column: 1 / -1;
}

.side-stack {
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 8px;
  min-height: 0;
  overflow: hidden;
}

.panel {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
  padding: 10px;
  min-width: 0;
  min-height: 0;
  overflow: auto;
}

.panel h2,
.sub-head h2 {
  margin: 0;
  color: #22314a;
  font-size: 16px;
}

.panel-head,
.sub-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.sub-head {
  align-items: center;
  margin-bottom: 8px;
}

.sub-head-inline {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sub-head span {
  color: var(--muted);
  font-size: 12px;
}

.segmented-control {
  display: inline-flex;
  gap: 4px;
  padding: 4px;
  border: 1px solid var(--op-input-border, var(--line-strong));
  border-radius: 999px;
  background: color-mix(in srgb, var(--op-accent-soft, rgba(47, 125, 224, 0.1)) 64%, white);
}

.segmented-btn {
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: #5b677d;
  padding: 8px 14px;
  min-height: 34px;
  font-weight: 800;
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
}

.segmented-btn.active {
  background: linear-gradient(180deg, color-mix(in srgb, var(--op-accent-soft, rgba(47, 125, 224, 0.1)) 70%, white) 0%, color-mix(in srgb, var(--op-accent-soft, rgba(47, 125, 224, 0.1)) 92%, white) 100%);
  color: var(--op-accent-strong, var(--blue));
  box-shadow: 0 6px 14px color-mix(in srgb, var(--op-accent, var(--blue)) 18%, transparent);
}

.panel-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
}

.batch-inline-panel {
  display: grid;
  gap: 10px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: #fbfdff;
  padding: 12px;
}

.toggle-btn {
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  background: linear-gradient(180deg, #ffffff 0%, #f7f9fd 100%);
  color: #5b677d;
  padding: 8px 12px;
  font-weight: 700;
  cursor: pointer;
  min-height: 36px;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease, filter 0.15s ease;
}

.small-toggle {
  width: auto;
  min-height: 32px;
  padding: 6px 10px;
}

.toggle-btn.active {
  border-color: #a9c3f9;
  background: linear-gradient(180deg, #eff5ff 0%, #e3eeff 100%);
  color: var(--blue);
  box-shadow: 0 6px 16px rgba(47, 110, 229, 0.12);
}

.op-panel {
  --op-accent: var(--action-in);
  --op-accent-strong: var(--action-in-strong);
  --op-accent-soft: var(--action-in-soft);
  --op-panel-wash: linear-gradient(180deg, rgba(47, 125, 224, 0.08) 0%, rgba(47, 125, 224, 0.02) 100%);
  --op-input-border: rgba(47, 125, 224, 0.34);
  display: grid;
  grid-template-rows: auto auto minmax(260px, 1fr);
  gap: 12px;
  position: relative;
  background: var(--op-panel-wash), #fff;
}

.op-panel::before {
  content: "";
  position: absolute;
  inset: 0 0 auto 0;
  height: 4px;
  background: linear-gradient(90deg, var(--op-accent) 0%, var(--op-accent-strong) 100%);
}

.op-panel > * {
  position: relative;
  z-index: 1;
}

.op-panel.receipt {
  --op-accent: var(--action-in);
  --op-accent-strong: var(--action-in-strong);
  --op-accent-soft: var(--action-in-soft);
  --op-panel-wash: linear-gradient(180deg, rgba(47, 125, 224, 0.08) 0%, rgba(47, 125, 224, 0.02) 100%);
  --op-input-border: rgba(47, 125, 224, 0.34);
}

.op-panel.return {
  --op-accent: var(--action-out);
  --op-accent-strong: var(--action-out-strong);
  --op-accent-soft: var(--action-out-soft);
  --op-panel-wash: linear-gradient(180deg, rgba(106, 95, 196, 0.08) 0%, rgba(106, 95, 196, 0.02) 100%);
  --op-input-border: rgba(106, 95, 196, 0.34);
}

.inventory-board.layout-stock-only .op-panel,
.inventory-board.layout-alert-only .op-panel,
.inventory-board.layout-all-collapsed .op-panel {
  grid-column: 1;
}

.inventory-board.layout-stock-only .stock-panel,
.inventory-board.layout-alert-only .side-stack {
  grid-column: 2;
}

.collapsed-panel-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.collapsed-panel-chip {
  width: auto;
  min-width: 0;
  min-height: 34px;
  padding: 7px 12px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.collapsed-panel-chip span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}

.primary-btn,
.outline-btn {
  width: 100%;
  border-radius: 10px;
  font: inherit;
}

.primary-btn {
  border: 1px solid var(--green);
  background: linear-gradient(180deg, color-mix(in srgb, var(--green) 80%, white) 0%, var(--green) 100%);
  color: #fff;
  font-weight: 700;
  padding: 8px 14px;
  min-height: 36px;
  box-shadow: 0 8px 18px rgba(34, 169, 110, 0.18);
  cursor: pointer;
}

.outline-btn {
  border: 1px solid var(--line-strong);
  background: linear-gradient(180deg, #ffffff 0%, #f7f9fd 100%);
  color: #5b677d;
  font-weight: 700;
  padding: 8px 14px;
  min-height: 36px;
  cursor: pointer;
}

.primary-btn:hover,
.outline-btn:hover,
.toggle-btn:hover {
  transform: translateY(-1px);
}

.primary-btn:hover {
  box-shadow: 0 10px 22px rgba(34, 169, 110, 0.24);
  filter: brightness(1.02);
}

.outline-btn:hover,
.toggle-btn:hover {
  border-color: #c0cad9;
  box-shadow: 0 4px 12px rgba(28, 47, 84, 0.08);
}

.primary-btn:active,
.outline-btn:active,
.toggle-btn:active {
  transform: translateY(0);
}

.recent-block,
.stock-panel,
.alert-panel {
  min-height: 0;
  overflow-x: auto;
}

.recent-block {
  --recent-accent: var(--action-in);
  --recent-accent-strong: var(--action-in-strong);
  --recent-accent-soft: var(--action-in-soft);
  min-height: 300px;
  border-top: 1px solid color-mix(in srgb, var(--recent-accent) 16%, white);
  padding-top: 4px;
}

.recent-block.receipt {
  --recent-accent: var(--action-in);
  --recent-accent-strong: var(--action-in-strong);
  --recent-accent-soft: var(--action-in-soft);
}

.recent-block.return {
  --recent-accent: var(--action-out);
  --recent-accent-strong: var(--action-out-strong);
  --recent-accent-soft: var(--action-out-soft);
}

.recent-section {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.recent-summary-inline {
  flex-wrap: wrap;
  justify-content: flex-end;
}

.recent-secondary-summary {
  color: var(--recent-accent-strong);
  font-size: 12px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 999px;
  background: var(--recent-accent-soft);
}

.stock-panel,
.alert-panel {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
}

.panel-table-scroll {
  min-height: 0;
  overflow: auto;
  height: 100%;
}

.stock-meter {
  display: grid;
  gap: 4px;
}

.stock-meter-track {
  height: 8px;
  border-radius: 999px;
  background: #e6ebf4;
  overflow: hidden;
}

.stock-meter-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, color-mix(in srgb, var(--green) 76%, white) 0%, var(--green) 100%);
}

.stock-meter.low_stock .stock-meter-fill {
  background: linear-gradient(90deg, color-mix(in srgb, var(--orange) 72%, white) 0%, var(--orange) 100%);
}

.stock-meter.out_of_stock .stock-meter-fill {
  background: linear-gradient(90deg, color-mix(in srgb, var(--red) 72%, white) 0%, var(--red) 100%);
}

.stock-meter span {
  color: #66748d;
  font-size: 11px;
  font-weight: 700;
}

.grid-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border: 1px solid var(--line);
  border-radius: 10px;
  overflow: hidden;
  min-width: 100%;
}

.grid-table th,
.grid-table td {
  border-bottom: 1px solid var(--line);
  padding: 4px 8px;
  text-align: left;
  font-size: 12px;
}

.grid-table th {
  background: #f7f9fd;
  color: #52607b;
  font-weight: 700;
}

.recent-block .sub-head h3 {
  color: var(--recent-accent-strong);
}

.recent-block .grid-table thead th {
  background: color-mix(in srgb, var(--recent-accent-soft) 70%, white);
}

.recent-block .empty-cell {
  background: color-mix(in srgb, var(--recent-accent-soft) 38%, white);
}

.grid-table tbody tr:last-child td {
  border-bottom: none;
}

.compact-table th,
.compact-table td {
  padding-top: 4px;
  padding-bottom: 4px;
}

.stock-panel table,
.alert-panel table,
.recent-block table {
  table-layout: fixed;
}

.stock-panel .grid-table,
.alert-panel .grid-table {
  min-width: 100%;
}

.stock-panel thead th,
.alert-panel thead th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: #f7f9fd;
}

.empty-cell {
  text-align: center;
  color: var(--muted);
}

@media (max-width: 1500px) {
  .inventory-board,
  .inventory-board.layout-stock-only,
  .inventory-board.layout-alert-only,
  .inventory-board.layout-all-collapsed {
    grid-template-columns: 1fr;
  }

  .side-stack {
    grid-template-rows: auto;
  }

  .panel-head {
    flex-direction: column;
  }
}

@media (max-width: 900px) {
  .panel {
    padding: 12px;
  }

  .collapsed-panel-actions {
    width: 100%;
    display: grid;
    grid-template-columns: 1fr 1fr;
  }

  .collapsed-panel-chip {
    width: 100%;
  }
}

@media (max-width: 640px) {
  .inventory-board {
    gap: 10px;
  }

  .panel-head h2,
  .sub-head h2 {
    font-size: 16px;
  }

  .segmented-control {
    width: 100%;
    padding: 3px;
  }

  .segmented-btn {
    flex: 1 1 0;
    min-height: 32px;
    padding: 7px 8px;
    font-size: 12px;
  }

  .panel-actions {
    width: 100%;
    display: grid;
    gap: 8px;
    justify-content: stretch;
  }

  .toggle-btn {
    flex: 1 1 0;
  }

  .collapsed-panel-actions {
    grid-template-columns: 1fr;
  }

  .collapsed-panel-chip {
    min-height: 42px;
    padding: 8px 10px;
    justify-content: space-between;
    font-size: 12px;
  }

  .collapsed-panel-chip span {
    font-size: 11px;
  }

  .grid-table th,
  .grid-table td,
  .stock-meter span {
    white-space: nowrap;
  }
}
</style>
