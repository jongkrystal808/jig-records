<script setup lang="ts">
import InventoryReportMobileCards, {
  type InventoryReportMobileRow
} from "@/components/inventory/InventoryReportMobileCards.vue";
import FixtureReportRowActions from "@/components/inventory/FixtureReportRowActions.vue";
import type { TransactionOverviewRow } from "@/types";
import { normalizeReportFixtureCode } from "@/utils/reportTransactionDetails";
import type {
  ReportColumnKey,
  ReportColumnPresetKey
} from "@/utils/reportColumnPresets";

type FilterChip = { key: string; label: string; value: string };
type ColumnDefinition = { key: ReportColumnKey; label: string };
type ColumnPreset = {
  key: ReportColumnPresetKey;
  label: string;
  description: string;
  columns: ReportColumnKey[];
};

const props = defineProps<{
  rows: InventoryReportMobileRow[];
  reportTotal: number;
  fixtureCount: number;
  attentionFixtureCount: number;
  missingConfigurationCount: number;
  totalStockQty: number;
  customerSuppliedQty: number;
  selfPurchasedQty: number;
  page: number;
  pageSize: 20 | 50 | 100;
  pageSizeOptions: Array<20 | 50 | 100>;
  jumpPage: number;
  totalPages: number;
  pageStart: number;
  pageEnd: number;
  loading: boolean;
  loadError: string;
  customerSelected: boolean;
  transactionModeApplied: boolean;
  transactionFilterLoading: boolean;
  transactionDetailCount: number;
  transactionDetailsByFixtureCode: Map<string, TransactionOverviewRow[]>;
  showTransactionDetails: boolean;
  exportFormat: "csv" | "xlsx";
  exportLoading: boolean;
  exportFeedbackMessage: string;
  columnPickerOpen: boolean;
  columnDefinitions: ColumnDefinition[];
  columnPresets: ColumnPreset[];
  selectedColumnPreset: ReportColumnPresetKey | null;
  selectedColumnPresetLabel: string;
  visibleColumns: ReportColumnKey[];
  effectiveVisibleColumns: ReportColumnKey[];
  autoHiddenColumns: ReportColumnKey[];
  visibleColumnCount: number;
  tableMinWidth: string;
  appliedFilterChips: FilterChip[];
  hasPendingFilters: boolean;
  pendingFilterCount: number;
  canRunSearch: boolean;
  canOperateFixtures: boolean;
}>();

const emit = defineEmits<{
  "update:jumpPage": [value: number];
  "update:showTransactionDetails": [value: boolean];
  "update:exportFormat": [value: "csv" | "xlsx"];
  "update:columnPickerOpen": [value: boolean];
  showTransactionDetailsChange: [];
  exportRows: [];
  showAllColumns: [];
  applyColumnPreset: [key: ReportColumnPresetKey];
  toggleColumn: [key: ReportColumnKey, checked: boolean];
  runSearch: [];
  reload: [];
  openImage: [row: InventoryReportMobileRow];
  quickTransaction: [row: InventoryReportMobileRow, mode: "receipt" | "return"];
  editFixture: [row: InventoryReportMobileRow];
  viewProduction: [row: InventoryReportMobileRow];
  changePage: [page: number];
  changePageSize: [pageSize: number];
  jumpPage: [];
}>();

function isColumnVisible(key: ReportColumnKey): boolean {
  return props.effectiveVisibleColumns.includes(key);
}

function isColumnSelected(key: ReportColumnKey): boolean {
  return props.visibleColumns.includes(key);
}

function isColumnAutoHidden(key: ReportColumnKey): boolean {
  return props.autoHiddenColumns.includes(key);
}

function waterStatusLabel(status: InventoryReportMobileRow["waterStatus"]): string {
  if (status === "low") return "低水位";
  if (status === "empty") return "缺料";
  if (status === "na") return "—";
  return "正常";
}

function configurationStatusLabel(
  status: InventoryReportMobileRow["configurationStatus"]
): string {
  if (status === "unconfigured") return "未配置";
  if (status === "unbound") return "未綁定";
  return "已配置";
}

function transactionTypeLabel(value: TransactionOverviewRow["transaction_type"]): string {
  return value === "receipt" ? "收料" : "退料";
}

function transactionDateLabel(value: string): string {
  return value.split("T")[0]?.trim() || value || "—";
}

function transactionNoLabel(value: string | null): string {
  return value?.trim() || "（無單號）";
}

function transactionDetailsForRow(row: InventoryReportMobileRow): TransactionOverviewRow[] {
  return props.transactionDetailsByFixtureCode.get(normalizeReportFixtureCode(row.fixtureCode)) ?? [];
}

function shouldShowTransactionDetails(
  row: InventoryReportMobileRow,
  rowIndex: number
): boolean {
  if (!props.showTransactionDetails || !row.fixtureCode) return false;
  const fixtureCode = normalizeReportFixtureCode(row.fixtureCode);
  return (
    transactionDetailsForRow(row).length > 0 &&
    props.rows.findIndex(
      (candidate) => normalizeReportFixtureCode(candidate.fixtureCode) === fixtureCode
    ) === rowIndex
  );
}

function handleTransactionToggle(event: Event): void {
  emit("update:showTransactionDetails", (event.target as HTMLInputElement).checked);
  emit("showTransactionDetailsChange");
}

function handleColumnToggle(key: ReportColumnKey, event: Event): void {
  emit("toggleColumn", key, (event.target as HTMLInputElement).checked);
}
</script>

<template>
  <section class="report-section" aria-label="治具庫存與配置結果">
    <div class="report-sticky-toolbar">
      <div class="report-toolbar" data-tour="report-result-toolbar">
        <div class="report-summary" data-tour="report-result-summary">
          <strong>{{ reportTotal }}</strong><span>筆資料</span><i></i>
          <span><b>{{ fixtureCount }}</b> 支治具</span>
          <span class="attention"><b>{{ attentionFixtureCount }}</b> 支低水位／缺料</span>
          <span class="missing"><b>{{ missingConfigurationCount }}</b> 筆未配置</span>
          <span><b>{{ totalStockQty }}</b> 總庫存</span>
          <span><b>{{ customerSuppliedQty }}</b> 客供</span>
          <span><b>{{ selfPurchasedQty }}</b> 自購</span>
        </div>
        <div class="report-toolbar-actions">
          <div class="report-range">顯示 {{ pageStart }}–{{ pageEnd }} / 共 {{ reportTotal }} 筆</div>
          <label
            v-if="transactionModeApplied"
            class="transaction-detail-toggle"
            data-tour="report-transaction-details"
            :class="{ selected: showTransactionDetails }"
          >
            <input
              :checked="showTransactionDetails"
              type="checkbox"
              :disabled="transactionDetailCount === 0"
              @change="handleTransactionToggle"
            />
            <span class="transaction-detail-indicator" aria-hidden="true"></span>
            <span>展示收／退料明細</span>
            <b>{{ transactionDetailCount.toLocaleString("zh-TW") }}</b>
          </label>
          <select
            :value="exportFormat"
            class="report-export-format"
            aria-label="選擇匯出格式"
            :disabled="exportLoading"
            @change="emit('update:exportFormat', ($event.target as HTMLSelectElement).value as 'csv' | 'xlsx')"
          >
            <option value="xlsx">XLSX</option><option value="csv">CSV</option>
          </select>
          <button
            class="report-export-button"
            data-tour="report-export-trigger"
            type="button"
            :disabled="loading || exportLoading || reportTotal === 0"
            @click="emit('exportRows')"
          >
            {{ exportLoading ? "匯出中…" : "匯出篩選結果" }}
          </button>
          <div class="column-picker">
            <button
              class="column-picker-trigger"
              data-tour="report-column-trigger"
              type="button"
              :aria-expanded="columnPickerOpen"
              aria-haspopup="true"
              @click.stop="emit('update:columnPickerOpen', !columnPickerOpen)"
            >
              顯示欄位 <b>{{ visibleColumnCount }} / {{ columnDefinitions.length }}</b>
            </button>
            <div v-if="columnPickerOpen" class="column-picker-popover" role="group" aria-label="選擇報表顯示欄位">
              <div class="column-picker-heading">
                <div><strong>選擇顯示欄位</strong><span>{{ selectedColumnPresetLabel }}</span></div>
                <button type="button" :disabled="selectedColumnPreset === 'full'" @click="emit('showAllColumns')">全部顯示</button>
              </div>
              <div class="column-picker-presets" role="group" aria-label="欄位預設">
                <button
                  v-for="preset in columnPresets"
                  :key="preset.key"
                  type="button"
                  :class="{ selected: selectedColumnPreset === preset.key }"
                  :aria-pressed="selectedColumnPreset === preset.key"
                  @click="emit('applyColumnPreset', preset.key)"
                >
                  <strong>{{ preset.label }}</strong><span>{{ preset.description }}</span>
                </button>
              </div>
              <div class="column-picker-options">
                <label
                  v-for="column in columnDefinitions"
                  :key="column.key"
                  :class="{ selected: isColumnSelected(column.key), 'auto-hidden': isColumnAutoHidden(column.key) }"
                >
                  <input type="checkbox" :checked="isColumnSelected(column.key)" @change="handleColumnToggle(column.key, $event)" />
                  <span class="column-option-indicator" aria-hidden="true"></span>
                  <span class="column-option-label">{{ column.label }}</span>
                  <em v-if="isColumnAutoHidden(column.key)">無資料</em>
                </label>
              </div>
              <small v-if="autoHiddenColumns.length" class="auto-hidden-note">
                已自動收合 {{ autoHiddenColumns.length }} 個無資料欄位；條件改變後有資料時會自動恢復。
              </small>
              <small v-else>至少保留一個欄位；選擇會儲存在此瀏覽器。</small>
            </div>
          </div>
        </div>
      </div>
      <div class="applied-filter-strip" aria-label="目前實際套用的報表條件">
        <strong>已套用</strong>
        <span v-if="appliedFilterChips.length === 0" class="empty">全部資料</span>
        <span v-for="chip in appliedFilterChips" :key="chip.key">{{ chip.label }}：<b>{{ chip.value }}</b></span>
        <em>共 {{ reportTotal.toLocaleString("zh-TW") }} 筆</em>
      </div>
    </div>

    <div v-if="hasPendingFilters" class="pending-filter-notice" role="status">
      <div><strong>有 {{ pendingFilterCount }} 個條件尚未套用</strong><span>下方仍顯示上一次已套用的報表結果。</span></div>
      <button type="button" :disabled="!canRunSearch" @click="emit('runSearch')">
        {{ transactionFilterLoading ? "套用中…" : "套用條件" }}
      </button>
    </div>

    <p v-if="exportFeedbackMessage" class="export-feedback" role="status">{{ exportFeedbackMessage }}</p>
    <div v-if="!customerSelected" class="report-state"><strong>請先選擇客戶</strong><p>選擇客戶後即可載入治具庫存與配置報表。</p></div>
    <div v-else-if="loading" class="report-state"><strong>正在載入報表…</strong><p>正在整理治具、庫存、機種與站點資料。</p></div>
    <div v-else-if="loadError" class="report-state error">
      <strong>資料載入失敗</strong><p>{{ loadError }}</p><button type="button" @click="emit('reload')">重新載入</button>
    </div>

    <div v-else class="table-frame" data-tour="report-result-table">
      <div class="table-scroll desktop-report-table" tabindex="0" aria-label="報表可左右捲動">
        <table :style="{ minWidth: tableMinWidth }">
          <thead><tr>
            <th v-if="isColumnVisible('index')" class="index-column">序號</th><th v-if="isColumnVisible('customer')">客戶</th>
            <th v-if="isColumnVisible('fixtureCode')">治具代碼</th><th v-if="isColumnVisible('fixtureName')">治具名稱</th>
            <th v-if="isColumnVisible('stockQty')" class="number-column">總庫存</th><th v-if="isColumnVisible('customerSuppliedQty')" class="number-column">客供庫存</th>
            <th v-if="isColumnVisible('selfPurchasedQty')" class="number-column">自購庫存</th><th v-if="isColumnVisible('minStockQty')" class="number-column">最低水位</th>
            <th v-if="isColumnVisible('waterStatus')">水位狀態</th><th v-if="isColumnVisible('lineStorage')">產線儲位</th>
            <th v-if="isColumnVisible('departmentStorage')">部門儲位</th><th v-if="isColumnVisible('modelCode')">機種</th>
            <th v-if="isColumnVisible('station')">站點</th><th v-if="isColumnVisible('requiredQty')" class="number-column">需求數量</th>
            <th v-if="isColumnVisible('maxOpenStationCount')" class="number-column">此治具可支援站數</th><th v-if="isColumnVisible('configurationStatus')">配置狀態</th>
            <th v-if="canOperateFixtures" class="row-action-column">操作</th>
          </tr></thead>
          <tbody>
            <template v-for="(row, index) in rows" :key="row.key">
              <tr :class="[`water-${row.waterStatus}`, { 'configuration-missing': row.configurationStatus === 'unconfigured' }]">
                <td v-if="isColumnVisible('index')" class="index-column">{{ (page - 1) * pageSize + index + 1 }}</td>
                <td v-if="isColumnVisible('customer')">{{ row.customerCode || "—" }}</td>
                <td v-if="isColumnVisible('fixtureCode')" class="code-cell">
                  <button v-if="row.fixtureCode" class="fixture-image-trigger" type="button" :aria-label="`查看治具 ${row.fixtureCode} 圖片`" @click="emit('openImage', row)">{{ row.fixtureCode }}</button><span v-else>—</span>
                </td>
                <td v-if="isColumnVisible('fixtureName')" class="name-cell">{{ row.fixtureName || "—" }}</td>
                <td v-if="isColumnVisible('stockQty')" class="number-cell">{{ row.stockQty ?? "—" }}</td>
                <td v-if="isColumnVisible('customerSuppliedQty')" class="number-cell">{{ row.customerSuppliedQty ?? "—" }}</td>
                <td v-if="isColumnVisible('selfPurchasedQty')" class="number-cell">{{ row.selfPurchasedQty ?? "—" }}</td>
                <td v-if="isColumnVisible('minStockQty')" class="number-cell">{{ row.minStockQty ?? "—" }}</td>
                <td v-if="isColumnVisible('waterStatus')"><span class="status-badge" :class="`status-${row.waterStatus}`">{{ waterStatusLabel(row.waterStatus) }}</span></td>
                <td v-if="isColumnVisible('lineStorage')">{{ row.lineStorage || "—" }}</td><td v-if="isColumnVisible('departmentStorage')">{{ row.departmentStorage || "—" }}</td>
                <td v-if="isColumnVisible('modelCode')" class="code-cell">{{ row.modelCode || "—" }}</td>
                <td v-if="isColumnVisible('station')"><span class="station-cell"><b>{{ row.stationCode || "—" }}</b><small v-if="row.stationName">{{ row.stationName }}</small></span></td>
                <td v-if="isColumnVisible('requiredQty')" class="number-cell">{{ row.requiredQty ?? "—" }}</td>
                <td v-if="isColumnVisible('maxOpenStationCount')" class="number-cell">{{ row.maxOpenStationCount === null ? "—" : `${row.maxOpenStationCount} 站` }}</td>
                <td v-if="isColumnVisible('configurationStatus')"><span class="configuration-badge" :class="`configuration-${row.configurationStatus}`">{{ configurationStatusLabel(row.configurationStatus) }}</span></td>
                <td v-if="canOperateFixtures" class="row-action-cell">
                  <FixtureReportRowActions
                    v-if="row.fixtureCode"
                    :row="row"
                    @quick-transaction="emit('quickTransaction', row, $event)"
                    @edit-fixture="emit('editFixture', row)"
                    @view-production="emit('viewProduction', row)"
                  />
                  <span v-else>—</span>
                </td>
              </tr>
              <tr v-if="shouldShowTransactionDetails(row, index)" class="transaction-detail-row">
                <td :colspan="visibleColumnCount + (canOperateFixtures ? 1 : 0)"><section class="transaction-detail-panel">
                  <header><div><strong>{{ row.fixtureCode }} 收／退料明細</strong><span>符合目前日期與收退料條件</span></div><b>{{ transactionDetailsForRow(row).length }} 筆</b></header>
                  <div class="transaction-detail-scroll"><table>
                    <caption class="sr-only">{{ row.fixtureCode }} 符合目前篩選條件的收退料明細</caption>
                    <thead><tr><th>類型</th><th>來源</th><th>日期</th><th>單號</th><th>datecode/編號</th><th class="number-column">數量</th></tr></thead>
                    <tbody><tr v-for="(detail, detailIndex) in transactionDetailsForRow(row)" :key="`${detail.id}-${detail.fixture_code}-${detail.identifier ?? ''}-${detailIndex}`">
                      <td><span class="transaction-type-badge" :class="`transaction-${detail.transaction_type}`">{{ transactionTypeLabel(detail.transaction_type) }}</span></td>
                      <td>{{ detail.ownership_type === "customer_supplied" ? "客供" : "自購" }}</td><td>{{ transactionDateLabel(detail.occurred_at) }}</td>
                      <td>{{ transactionNoLabel(detail.transaction_no) }}</td><td>{{ detail.identifier || "—" }}</td><td class="number-cell">{{ detail.quantity }}</td>
                    </tr></tbody>
                  </table></div>
                </section></td>
              </tr>
            </template>
            <tr v-if="rows.length === 0"><td class="empty-cell" :colspan="visibleColumnCount + (canOperateFixtures ? 1 : 0)"><strong>沒有符合條件的資料</strong><span>請調整篩選條件後重新查詢。</span></td></tr>
          </tbody>
        </table>
      </div>
      <InventoryReportMobileCards
        :rows="rows" :page="page" :page-size="pageSize" :visible-columns="effectiveVisibleColumns"
        :show-transaction-details="showTransactionDetails" :transaction-details-by-fixture-code="transactionDetailsByFixtureCode"
        :can-operate-fixtures="canOperateFixtures"
        @open-image="emit('openImage', $event)"
        @quick-transaction="emit('quickTransaction', $event[0], $event[1])"
        @edit-fixture="emit('editFixture', $event)"
        @view-production="emit('viewProduction', $event)"
      />
    </div>

    <nav v-if="!loading && reportTotal" class="pagination" data-tour="report-pagination" aria-label="報表分頁">
      <label class="page-size-control"><span>每頁</span><select :value="pageSize" aria-label="每頁顯示筆數" @change="emit('changePageSize', Number(($event.target as HTMLSelectElement).value))"><option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }} 筆</option></select></label>
      <div class="page-navigation"><button type="button" :disabled="page <= 1" @click="emit('changePage', page - 1)">上一頁</button><span>第 <strong>{{ page }}</strong> / {{ totalPages }} 頁</span><button type="button" :disabled="page >= totalPages" @click="emit('changePage', page + 1)">下一頁</button></div>
      <form class="page-jump-control" @submit.prevent="emit('jumpPage')"><label><span>跳至</span><input :value="jumpPage" type="number" min="1" :max="totalPages" inputmode="numeric" aria-label="跳至頁碼" @input="emit('update:jumpPage', Number(($event.target as HTMLInputElement).value))" /></label><button type="submit">跳轉</button></form>
    </nav>
  </section>
</template>
