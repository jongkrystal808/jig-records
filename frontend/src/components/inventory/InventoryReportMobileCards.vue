<script setup lang="ts">
import type { TransactionOverviewRow } from "@/types";
import FixtureReportRowActions from "@/components/inventory/FixtureReportRowActions.vue";
import { normalizeReportFixtureCode } from "@/utils/reportTransactionDetails";
import type { ReportColumnKey } from "@/utils/reportColumnPresets";

export type InventoryReportMobileRow = {
  key: string;
  customerCode: string;
  fixtureId: number;
  fixtureCode: string;
  fixtureName: string;
  stockQty: number | null;
  customerSuppliedQty: number | null;
  selfPurchasedQty: number | null;
  minStockQty: number | null;
  waterStatus: "normal" | "low" | "empty" | "na";
  lineStorage: string;
  departmentStorage: string;
  modelId: number;
  modelCode: string;
  stationId: number;
  stationCode: string;
  stationName: string;
  requiredQty: number | null;
  maxOpenStationCount: number | null;
  configurationStatus: "configured" | "unconfigured" | "unbound";
};

const props = defineProps<{
  rows: InventoryReportMobileRow[];
  page: number;
  pageSize: number;
  visibleColumns: ReportColumnKey[];
  showTransactionDetails: boolean;
  transactionDetailsByFixtureCode: Map<string, TransactionOverviewRow[]>;
  canOperateFixtures: boolean;
}>();

const emit = defineEmits<{
  openImage: [row: InventoryReportMobileRow];
  quickTransaction: [payload: [row: InventoryReportMobileRow, mode: "receipt" | "return"]];
  editFixture: [row: InventoryReportMobileRow];
  viewProduction: [row: InventoryReportMobileRow];
}>();

function isColumnVisible(key: ReportColumnKey): boolean {
  return props.visibleColumns.includes(key);
}

function waterStatusLabel(status: InventoryReportMobileRow["waterStatus"]): string {
  if (status === "low") return "低水位";
  if (status === "empty") return "無庫存";
  if (status === "na") return "不適用";
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
  return (
    props.transactionDetailsByFixtureCode.get(normalizeReportFixtureCode(row.fixtureCode)) ?? []
  );
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
</script>

<template>
  <div class="mobile-report-list" aria-label="手機版報表摘要卡片">
    <article
      v-for="(row, index) in rows"
      :key="`mobile-${row.key}`"
      class="mobile-report-card"
      :class="[
        `water-${row.waterStatus}`,
        { 'configuration-missing': row.configurationStatus === 'unconfigured' }
      ]"
    >
      <header>
        <span class="mobile-row-index">#{{ (page - 1) * pageSize + index + 1 }}</span>
        <div class="mobile-fixture-identity">
          <button
            v-if="row.fixtureCode"
            type="button"
            :aria-label="`查看治具 ${row.fixtureCode} 圖片`"
            @click="emit('openImage', row)"
          >
            {{ row.fixtureCode }}
          </button>
          <strong v-else>{{ row.modelCode || "未配置項目" }}</strong>
          <small>{{ row.fixtureName || row.stationName || "—" }}</small>
        </div>
        <div class="mobile-status-stack">
          <span
            v-if="isColumnVisible('waterStatus')"
            class="status-badge"
            :class="`status-${row.waterStatus}`"
          >
            {{ waterStatusLabel(row.waterStatus) }}
          </span>
          <span
            v-if="isColumnVisible('configurationStatus')"
            class="configuration-badge"
            :class="`configuration-${row.configurationStatus}`"
          >
            {{ configurationStatusLabel(row.configurationStatus) }}
          </span>
        </div>
      </header>

      <dl class="mobile-report-fields">
        <div v-if="isColumnVisible('customer')"><dt>客戶</dt><dd>{{ row.customerCode || "—" }}</dd></div>
        <div v-if="isColumnVisible('stockQty')"><dt>總庫存</dt><dd>{{ row.stockQty ?? "—" }}</dd></div>
        <div v-if="isColumnVisible('customerSuppliedQty')"><dt>客供</dt><dd>{{ row.customerSuppliedQty ?? "—" }}</dd></div>
        <div v-if="isColumnVisible('selfPurchasedQty')"><dt>自購</dt><dd>{{ row.selfPurchasedQty ?? "—" }}</dd></div>
        <div v-if="isColumnVisible('minStockQty')"><dt>最低水位</dt><dd>{{ row.minStockQty ?? "—" }}</dd></div>
        <div v-if="isColumnVisible('modelCode')"><dt>機種</dt><dd>{{ row.modelCode || "—" }}</dd></div>
        <div v-if="isColumnVisible('station')"><dt>站點</dt><dd>{{ row.stationCode || "—" }} {{ row.stationName }}</dd></div>
        <div v-if="isColumnVisible('requiredQty')"><dt>需求</dt><dd>{{ row.requiredQty ?? "—" }}</dd></div>
        <div v-if="isColumnVisible('maxOpenStationCount')"><dt>此治具可支援站數</dt><dd>{{ row.maxOpenStationCount === null ? "—" : `${row.maxOpenStationCount} 站` }}</dd></div>
        <div v-if="isColumnVisible('lineStorage')"><dt>產線儲位</dt><dd>{{ row.lineStorage || "—" }}</dd></div>
        <div v-if="isColumnVisible('departmentStorage')"><dt>部門儲位</dt><dd>{{ row.departmentStorage || "—" }}</dd></div>
      </dl>

      <footer v-if="canOperateFixtures && row.fixtureCode" class="mobile-report-actions">
        <FixtureReportRowActions
          :row="row"
          @quick-transaction="emit('quickTransaction', [row, $event])"
          @edit-fixture="emit('editFixture', row)"
          @view-production="emit('viewProduction', row)"
        />
      </footer>

      <section
        v-if="shouldShowTransactionDetails(row, index)"
        class="mobile-transaction-details"
      >
        <strong>收／退料明細（{{ transactionDetailsForRow(row).length }}）</strong>
        <div
          v-for="(detail, detailIndex) in transactionDetailsForRow(row)"
          :key="`mobile-detail-${detail.id}-${detailIndex}`"
        >
          <span>{{ transactionTypeLabel(detail.transaction_type) }}</span>
          <span>{{ transactionDateLabel(detail.occurred_at) }}</span>
          <span>{{ transactionNoLabel(detail.transaction_no) }}</span>
          <span>{{ detail.identifier || "—" }}</span>
          <b>{{ detail.quantity }}</b>
        </div>
      </section>
    </article>

    <div v-if="rows.length === 0" class="mobile-report-empty">
      <strong>沒有符合條件的資料</strong>
      <span>請調整篩選條件後重新查詢。</span>
    </div>
  </div>
</template>

<style scoped>
.mobile-report-list {
  display: none;
}

@media (max-width: 680px) {
  .mobile-report-list {
    display: grid;
    gap: 9px;
    padding: 10px;
    background: #eef3f9;
  }

  .mobile-report-card {
    overflow: hidden;
    border: 1px solid #cad7e7;
    border-radius: 10px;
    background: #fff;
    box-shadow: 0 3px 10px rgba(37, 66, 105, 0.06);
  }

  .mobile-report-card.water-low { border-color: #e5bd72; }
  .mobile-report-card.water-empty,
  .mobile-report-card.configuration-missing { border-color: #e4aaa6; }

  .mobile-report-card > header {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    align-items: start;
    gap: 8px;
    padding: 10px;
    border-bottom: 1px solid #dbe4ef;
    background: #f8fbff;
  }

  .mobile-report-actions {
    padding: 8px 10px;
    border-top: 1px solid #dbe4ef;
    background: #f8fbff;
  }

  .mobile-row-index { color: #75849a; font-size: 0.68rem; font-weight: 800; }
  .mobile-fixture-identity { display: grid; min-width: 0; gap: 2px; }
  .mobile-fixture-identity button,
  .mobile-fixture-identity strong {
    justify-self: start;
    overflow: hidden;
    max-width: 100%;
    padding: 0;
    border: 0;
    color: #175fa8;
    background: transparent;
    font-size: 0.86rem;
    font-weight: 850;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .mobile-fixture-identity button { cursor: pointer; text-decoration: underline; text-underline-offset: 2px; }
  .mobile-fixture-identity small { overflow: hidden; color: #66768e; font-size: 0.68rem; text-overflow: ellipsis; white-space: nowrap; }
  .mobile-status-stack { display: grid; justify-items: end; gap: 4px; }

  .status-badge,
  .configuration-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 58px;
    padding: 3px 7px;
    border-radius: 999px;
    font-size: 0.68rem;
    font-weight: 800;
  }
  .status-normal,
  .configuration-configured { color: #16784e; background: #e6f6ef; }
  .status-low { color: #a66308; background: #fff2d8; }
  .status-empty,
  .configuration-unconfigured { color: #b13731; background: #fde9e8; }
  .status-na,
  .configuration-unbound { color: #6c7788; background: #eef1f5; }

  .mobile-report-fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0; margin: 0; }
  .mobile-report-fields > div { min-width: 0; padding: 8px 10px; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; }
  .mobile-report-fields > div:nth-child(even) { border-right: 0; }
  .mobile-report-fields dt { color: #7a8799; font-size: 0.62rem; font-weight: 750; }
  .mobile-report-fields dd { overflow: hidden; margin: 2px 0 0; color: #293a54; font-size: 0.74rem; font-weight: 800; text-overflow: ellipsis; white-space: nowrap; }

  .mobile-transaction-details { display: grid; gap: 6px; padding: 9px 10px; background: #eaf2fd; }
  .mobile-transaction-details > strong { color: #274c7b; font-size: 0.7rem; }
  .mobile-transaction-details > div { display: grid; grid-template-columns: auto auto minmax(0, 1fr) minmax(0, 1fr) auto; gap: 5px; color: #53647c; font-size: 0.63rem; }
  .mobile-transaction-details > div span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

  .mobile-report-empty { display: grid; place-items: center; min-height: 180px; gap: 5px; color: #6c7788; text-align: center; }
  .mobile-report-empty strong { color: #344b6b; }
}
</style>
