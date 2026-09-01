<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";

import { api } from "@/api";
import { authSession, selectedCustomerId } from "@/appState";
import UiMultiSelect from "@/components/common/UiMultiSelect.vue";
import FixtureQualityPanel from "@/components/master/FixtureQualityPanel.vue";
import TransactionAccountDetailPanel from "@/components/master/TransactionAccountDetailPanel.vue";
import TransactionAccountListPanel from "@/components/master/TransactionAccountListPanel.vue";
import { useMasterLedger } from "@/composables/useMasterLedger";
import { pushToast } from "@/toastState";
import type { Fixture, FixtureQualityReport } from "@/types";
import { completeBlobExport, completeCsvRowsExport } from "@/utils/exportFeedback";
import { scrollReportResultsIntoView } from "@/utils/scrollReportResults";
import { canManageAdminReports } from "@/utils/roles";

export type FormAdminReportMode = "ledger" | "quality";

const props = defineProps<{ mode: FormAdminReportMode }>();
const emit = defineEmits<{ navigate: [workspace: "ledger" | "production" | "master" | "image"] }>();

const fixtures = ref<Fixture[]>([]);
const qualityReport = ref<FixtureQualityReport | null>(null);
const qualityLoading = ref(false);
const qualityInlineSavingFixtureId = ref<number | null>(null);
const qualityIssueFilter = ref<string[]>([]);
const exporting = ref(false);
const resultsSection = ref<HTMLElement | null>(null);

function rowMatchesIssue(row: FixtureQualityReport["rows"][number], issueCode: string): boolean {
  if (issueCode === "missing_storage_and_min_stock") {
    return row.issue_codes.includes("missing_storage_location") || row.issue_codes.includes("missing_min_stock_qty");
  }
  return row.issue_codes.includes(issueCode);
}

const filteredQualityRows = computed(() =>
  (qualityReport.value?.rows ?? []).filter((row) =>
    qualityIssueFilter.value.length
      ? qualityIssueFilter.value.some((issueCode) => rowMatchesIssue(row, issueCode))
      : ["missing_storage_location", "missing_min_stock_qty", "missing_image", "missing_model_relation"]
          .some((issueCode) => row.issue_codes.includes(issueCode))
  )
);

async function loadQuality(): Promise<void> {
  const customerId = selectedCustomerId.value;
  if (!customerId || !canManageAdminReports(authSession.value?.role)) {
    fixtures.value = [];
    qualityReport.value = null;
    return;
  }
  qualityLoading.value = true;
  try {
    [fixtures.value, qualityReport.value] = await Promise.all([
      api.listFixtures(customerId),
      api.getFixtureQualityReport(customerId)
    ]);
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "載入治具資料品質失敗", "error");
  } finally {
    qualityLoading.value = false;
  }
}

const {
  ledgerTransactions,
  ledgerTransactionNoFilter,
  ledgerCreatedByFilter,
  ledgerFixtureCodeFilter,
  ledgerTypeFilter,
  ledgerPage,
  ledgerPageSize,
  ledgerTotal,
  ledgerLoading,
  ledgerProcessing,
  ledgerTotalPages,
  selectedLedgerTransactionId,
  selectedLedgerTransaction,
  loadLedgerPage,
  selectLedgerTransaction,
  updateLedgerTransactionNo,
  updateLedgerCreatedBy,
  updateLedgerFixtureCode,
  updateLedgerTypeFilter,
  updateLedgerPageSize,
  previousLedgerPage,
  nextLedgerPage,
  reloadLedgerSelection,
  recalculateLedgerState,
  reverseSelectedLedgerTransaction
} = useMasterLedger({
  selectedCustomerId,
  canManage: () => canManageAdminReports(authSession.value?.role),
  reloadData: async () => {
    await Promise.all([loadQuality(), loadLedgerPage({ preserveSelection: true })]);
  }
});

async function saveInlineQualityIssue(
  fixtureId: number,
  lineStorageLocation: string,
  departmentStorageLocation: string,
  minStockQty: number
): Promise<void> {
  const customerId = selectedCustomerId.value;
  const fixture = fixtures.value.find((row) => row.id === fixtureId);
  if (!customerId || !fixture) return;
  qualityInlineSavingFixtureId.value = fixtureId;
  try {
    await api.updateFixture(fixtureId, {
      customer_id: customerId,
      responsible_user_id: fixture.responsible_user_id,
      code: fixture.code,
      name: fixture.name,
      line_storage_location: lineStorageLocation || null,
      department_storage_location: departmentStorageLocation || null,
      min_stock_qty: Math.max(0, minStockQty),
      description: fixture.description ?? "",
      is_active: fixture.is_active
    });
    await loadQuality();
    pushToast("治具資料品質已更新。", "success");
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "更新治具資料品質失敗", "error");
  } finally {
    qualityInlineSavingFixtureId.value = null;
  }
}

function openQualityIssue(fixtureId: number, issueCode: string): void {
  const fixtureCode = fixtures.value.find((row) => row.id === fixtureId)?.code ?? "";
  if (issueCode === "stock_mismatch") {
    updateLedgerFixtureCode(fixtureCode);
    emit("navigate", "ledger");
    return;
  }
  if (issueCode === "missing_model_relation") {
    emit("navigate", "production");
    return;
  }
  if (issueCode === "missing_image") {
    emit("navigate", "image");
    return;
  }
  emit("navigate", "master");
  pushToast("已切換到資料維護，請直接修正治具主檔。", "info");
}

async function exportFilteredResults(): Promise<void> {
  if (exporting.value) return;
  const rowCount = props.mode === "ledger" ? ledgerTotal.value : filteredQualityRows.value.length;
  if (rowCount === 0) {
    pushToast("目前沒有可匯出的資料。", "warning");
    return;
  }
  exporting.value = true;
  try {
    if (props.mode === "ledger") {
      const response = await api.exportTransactionsCsv(
        selectedCustomerId.value ?? undefined,
        {
          transaction_type: ledgerTypeFilter.value.length ? [...ledgerTypeFilter.value] : undefined,
          transaction_no: ledgerTransactionNoFilter.value.trim() || undefined,
          created_by: ledgerCreatedByFilter.value.trim() || undefined,
          fixture_code: ledgerFixtureCodeFilter.value.trim() || undefined
        }
      );
      completeBlobExport(response, "form-ledger-filtered.csv", ledgerTotal.value);
      return;
    }
    completeCsvRowsExport(
      "form-fixture-quality-filtered.csv",
      ["治具編號", "儲位", "最低水位", "機種關聯", "圖片"],
      filteredQualityRows.value.map((row) => [
        row.fixture_code,
        row.storage_location,
        row.min_stock_qty,
        row.related_model_count,
        row.has_image ? "有" : "缺"
      ])
    );
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "匯出篩選結果失敗", "error");
  } finally {
    exporting.value = false;
  }
}

async function applyAdminFilters(): Promise<void> {
  if (props.mode === "ledger") await loadLedgerPage();
  await nextTick();
  scrollReportResultsIntoView(resultsSection.value);
}

watch(
  () => props.mode,
  (mode) => {
    if (mode === "ledger") void loadLedgerPage();
    else void loadQuality();
  },
  { immediate: true }
);

watch(selectedCustomerId, () => {
  ledgerPage.value = 1;
  void (props.mode === "ledger" ? loadLedgerPage() : loadQuality());
});
</script>

<template>
  <div class="report-workspace form-admin-report-workspace">
    <div class="report-main-column">
      <section class="filter-panel" data-tour="form-admin-filters" :aria-label="mode === 'ledger' ? '收退料帳目管理條件' : '治具資料品質條件'">
        <div class="filter-panel-title">
          <div><strong>篩選條件</strong><span>{{ mode === "ledger" ? "收退料帳目管理" : "治具資料品質" }}</span></div>
          <div class="filter-panel-title-actions">
            <button class="text-button" type="button" :disabled="ledgerLoading || qualityLoading" @click="mode === 'ledger' ? loadLedgerPage() : loadQuality()">重新整理</button>
            <button class="primary-btn btn-sm" type="button" :disabled="ledgerLoading || qualityLoading" @click="applyAdminFilters">套用條件</button>
          </div>
        </div>
        <div v-if="mode === 'ledger'" class="form-admin-filters">
          <label><span>單號</span><input :value="ledgerTransactionNoFilter" placeholder="搜尋單號" @input="updateLedgerTransactionNo(($event.target as HTMLInputElement).value)" /></label>
          <label><span>操作人</span><input :value="ledgerCreatedByFilter" placeholder="搜尋操作人" @input="updateLedgerCreatedBy(($event.target as HTMLInputElement).value)" /></label>
          <label><span>治具編號</span><input :value="ledgerFixtureCodeFilter" placeholder="搜尋治具編號" @input="updateLedgerFixtureCode(($event.target as HTMLInputElement).value)" /></label>
          <UiMultiSelect :model-value="ledgerTypeFilter" label="類型" placeholder="全部帳目" :options="[{ value: 'receipt', label: '收料' }, { value: 'return', label: '退料' }]" @update:model-value="updateLedgerTypeFilter($event as Array<'receipt' | 'return'>)" />
        </div>
        <div v-else class="form-admin-filters">
          <UiMultiSelect v-model="qualityIssueFilter" label="問題類型" placeholder="全部問題" :options="[{ value: 'missing_storage_and_min_stock', label: '沒有儲位 / 沒有最低水位' }, { value: 'missing_image', label: '沒有圖片' }, { value: 'missing_model_relation', label: '沒有任何機種關聯' }]" />
        </div>
      </section>

      <slot name="between-filter-and-results" />

      <section ref="resultsSection" class="report-section" data-tour="form-admin-results" :aria-label="mode === 'ledger' ? '收退料帳目管理結果' : '治具資料品質結果'">
        <div class="report-toolbar">
          <div class="report-summary"><strong>{{ mode === "ledger" ? ledgerTotal : filteredQualityRows.length }}</strong><span>筆資料</span></div>
          <div class="form-admin-actions">
            <button class="outline-btn" type="button" :disabled="exporting" @click="exportFilteredResults">{{ exporting ? "匯出中..." : "匯出篩選結果" }}</button>
            <label v-if="mode === 'ledger'" class="page-size-inline">每頁<select :value="ledgerPageSize" @change="updateLedgerPageSize(Number(($event.target as HTMLSelectElement).value))"><option :value="12">12</option><option :value="25">25</option><option :value="50">50</option></select></label>
          </div>
        </div>

        <template v-if="mode === 'ledger'">
          <div class="ledger-grid">
            <TransactionAccountListPanel
              :rows="ledgerTransactions" :selected-transaction-id="selectedLedgerTransactionId" :loading="ledgerLoading"
              :transaction-no="ledgerTransactionNoFilter" :created-by="ledgerCreatedByFilter" :fixture-code="ledgerFixtureCodeFilter"
              :transaction-type="ledgerTypeFilter" :page="ledgerPage" :page-size="ledgerPageSize" :total-pages="ledgerTotalPages" :total="ledgerTotal"
              embedded-form :on-transaction-no-change="updateLedgerTransactionNo" :on-created-by-change="updateLedgerCreatedBy"
              :on-fixture-code-change="updateLedgerFixtureCode" :on-transaction-type-change="updateLedgerTypeFilter" :on-page-size-change="updateLedgerPageSize"
              :on-select-row="selectLedgerTransaction" :on-previous-page="previousLedgerPage" :on-next-page="nextLedgerPage"
            />
            <TransactionAccountDetailPanel embedded-form :transaction="selectedLedgerTransaction" :processing="ledgerProcessing" :on-reload="reloadLedgerSelection" :on-recalculate="recalculateLedgerState" :on-reverse="reverseSelectedLedgerTransaction" />
          </div>
          <div class="form-grid-pager"><button class="outline-btn btn-sm" type="button" :disabled="ledgerPage <= 1" @click="previousLedgerPage">上一頁</button><span>第 {{ ledgerPage }} / {{ ledgerTotalPages }} 頁</span><button class="outline-btn btn-sm" type="button" :disabled="ledgerPage >= ledgerTotalPages" @click="nextLedgerPage">下一頁</button></div>
        </template>

        <FixtureQualityPanel
          v-else :report="qualityReport" :fixtures="fixtures" :loading="qualityLoading"
          :inline-saving-fixture-id="qualityInlineSavingFixtureId" :issue-filter="qualityIssueFilter" embedded-form
          @open-issue-editor="openQualityIssue" @save-inline-issue="saveInlineQualityIssue"
        />
      </section>
    </div>
  </div>
</template>

<style scoped>
.form-admin-report-workspace { width: 100%; }
.filter-panel { max-width: 1800px; margin: 0 auto 12px; border: 1px solid var(--line); border-radius: 10px; background: var(--panel); box-shadow: 0 8px 24px rgba(28, 47, 84, 0.06); overflow: hidden; }
.report-section { width: 100%; max-width: 1800px; margin-inline: auto; overflow: hidden; border: 1px solid var(--line); border-radius: 8px; background: #fff; box-shadow: 0 5px 14px rgba(28, 47, 84, 0.05); }
.report-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 18px; min-height: 44px; padding: 7px 12px; border-bottom: 1px solid var(--line); background: #f8fafd; }
.report-summary { display: flex; align-items: center; gap: 6px; }
.report-summary strong { color: var(--tone-info); font-size: 1.2rem; }
.report-summary span { color: var(--muted); font-size: .78rem; }
.filter-panel-title { display: flex; align-items: center; justify-content: space-between; gap: 16px; min-height: 38px; padding: 7px 12px; border-bottom: 1px solid var(--line); background: var(--surface-secondary); }
.filter-panel-title > div { display: flex; align-items: baseline; gap: 10px; }
.filter-panel-title strong { font-size: .9rem; }
.filter-panel-title span { color: var(--muted); font-size: .72rem; }
.filter-panel-title-actions { display: flex; align-items: center; justify-content: flex-end; flex-wrap: wrap; gap: 6px; }
.form-admin-filters { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 250px), 1fr)); gap: 9px 10px; padding: 10px 12px 12px; }
.form-admin-filters label { display: grid; grid-template-columns: auto minmax(0, 1fr); align-items: center; gap: 7px; }
.form-admin-filters label > span { color: #4f5f79; font-size: .73rem; font-weight: 700; white-space: nowrap; }
.form-admin-filters input, .form-admin-filters select { width: 100%; min-width: 0; min-height: 34px; padding: 0 9px; border: 1px solid var(--line-strong); border-radius: 5px; background: #fff; font: inherit; }
.form-admin-actions { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.form-admin-actions .outline-btn, .form-grid-pager .outline-btn { border-radius: 4px; background-image: none; box-shadow: none; }
.page-size-inline { display: inline-flex; align-items: center; gap: 6px; color: var(--muted); font-size: .72rem; }
.page-size-inline select { min-height: 30px; border: 1px solid var(--line); border-radius: 6px; background: #fff; }
.ledger-grid { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(380px, .85fr); gap: 10px; padding: 10px; background: #f5f8fc; }
.form-grid-pager { display: flex; align-items: center; justify-content: flex-end; gap: 8px; padding: 8px 12px; color: var(--muted); font-size: .75rem; }
@media (max-width: 1000px) { .ledger-grid { grid-template-columns: 1fr; } }
@media (max-width: 620px) { .form-admin-filters { grid-template-columns: 1fr; } .form-admin-filters label { grid-template-columns: 1fr; gap: 5px; } .filter-panel-title, .report-toolbar { align-items: flex-start; flex-direction: column; } .filter-panel-title-actions, .form-admin-actions { width: 100%; justify-content: flex-start; } }
</style>
