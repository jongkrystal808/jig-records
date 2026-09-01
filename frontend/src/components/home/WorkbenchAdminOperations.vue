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

export type WorkbenchAdminMode = "ledger" | "quality";

const props = defineProps<{ mode: WorkbenchAdminMode }>();
const emit = defineEmits<{ navigate: [workspace: "ledger" | "production" | "master" | "image"] }>();

const fixtures = ref<Fixture[]>([]);
const qualityReport = ref<FixtureQualityReport | null>(null);
const qualityLoading = ref(false);
const qualityInlineSavingFixtureId = ref<number | null>(null);
const qualityIssueFilter = ref<string[]>([]);
const exporting = ref(false);
const resultsSection = ref<HTMLElement | null>(null);

const issueOptions = [
  { value: "missing_storage_and_min_stock", label: "沒有儲位 / 沒有最低水位" },
  { value: "missing_image", label: "沒有圖片" },
  { value: "missing_model_relation", label: "沒有任何機種關聯" }
];

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
  resetLedgerFilters,
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
  } else if (issueCode === "missing_model_relation") emit("navigate", "production");
  else if (issueCode === "missing_image") emit("navigate", "image");
  else {
    emit("navigate", "master");
    pushToast("已切換到資料維護，請直接修正治具主檔。", "info");
  }
}

function resetFilters(): void {
  if (props.mode === "ledger") {
    resetLedgerFilters();
    void loadLedgerPage();
  } else {
    qualityIssueFilter.value = [];
  }
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
      const response = await api.exportTransactionsCsv(selectedCustomerId.value ?? undefined, {
        transaction_type: ledgerTypeFilter.value.length ? [...ledgerTypeFilter.value] : undefined,
        transaction_no: ledgerTransactionNoFilter.value.trim() || undefined,
        created_by: ledgerCreatedByFilter.value.trim() || undefined,
        fixture_code: ledgerFixtureCodeFilter.value.trim() || undefined
      });
      completeBlobExport(response, "workbench-ledger-filtered.csv", ledgerTotal.value);
    } else {
      completeCsvRowsExport(
        "workbench-fixture-quality-filtered.csv",
        ["治具編號", "儲位", "最低水位", "機種關聯", "圖片"],
        filteredQualityRows.value.map((row) => [
          row.fixture_code,
          row.storage_location,
          row.min_stock_qty,
          row.related_model_count,
          row.has_image ? "有" : "缺"
        ])
      );
    }
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "匯出篩選結果失敗", "error");
  } finally {
    exporting.value = false;
  }
}

async function applyFilters(): Promise<void> {
  if (props.mode === "ledger") await loadLedgerPage();
  await nextTick();
  scrollReportResultsIntoView(resultsSection.value);
}

watch(
  () => props.mode,
  (mode) => void (mode === "ledger" ? loadLedgerPage() : loadQuality()),
  { immediate: true }
);

watch(selectedCustomerId, () => {
  ledgerPage.value = 1;
  void (props.mode === "ledger" ? loadLedgerPage() : loadQuality());
});
</script>

<template>
  <div class="workbench-admin-workspace" :data-admin-mode="mode" data-workbench-component="admin-operations">
    <Teleport defer to="#workbench-management-tools">
    <section class="workbench-admin-filter-card" data-tour="workbench-admin-filters" :aria-label="mode === 'ledger' ? '工作台收退料帳目條件' : '工作台治具品質條件'">
      <header>
        <div class="workbench-admin-filter-title">
          <span>{{ mode === "ledger" ? "LEDGER FILTER" : "QUALITY FILTER" }}</span>
          <div><strong>工作台篩選器</strong><small>{{ mode === "ledger" ? "依案件欄位快速縮小帳目" : "可同時勾選多種品質問題" }}</small></div>
        </div>
        <div class="workbench-admin-filter-actions">
          <button type="button" @click="resetFilters">清除條件</button>
          <button class="primary" type="button" @click="applyFilters">套用條件</button>
        </div>
      </header>

      <div v-if="mode === 'ledger'" class="workbench-admin-filter-grid">
        <label><span>單號</span><input :value="ledgerTransactionNoFilter" placeholder="輸入完整或部分單號" @input="updateLedgerTransactionNo(($event.target as HTMLInputElement).value)" /></label>
        <label><span>操作人</span><input :value="ledgerCreatedByFilter" placeholder="操作人姓名" @input="updateLedgerCreatedBy(($event.target as HTMLInputElement).value)" /></label>
        <label><span>治具編號</span><input :value="ledgerFixtureCodeFilter" placeholder="治具編號" @input="updateLedgerFixtureCode(($event.target as HTMLInputElement).value)" /></label>
        <UiMultiSelect :model-value="ledgerTypeFilter" label="作業類型" placeholder="全部帳目" :options="[{ value: 'receipt', label: '收料' }, { value: 'return', label: '退料' }]" @update:model-value="updateLedgerTypeFilter($event as Array<'receipt' | 'return'>)" />
      </div>
      <div v-else class="workbench-admin-filter-grid quality-filter-grid">
        <UiMultiSelect v-model="qualityIssueFilter" label="問題類型" placeholder="全部品質問題" :options="issueOptions" />
        <div class="workbench-filter-hint"><strong>{{ filteredQualityRows.length }}</strong><span>筆符合目前問題條件</span></div>
      </div>
    </section>
    </Teleport>

    <Teleport v-if="mode === 'ledger'" defer to="#workbench-management-tools">
      <section class="workbench-side-section workbench-ledger-inspector" aria-label="已選帳目詳細與操作">
        <TransactionAccountDetailPanel
          embedded-workbench
          workbench-side-panel
          :transaction="selectedLedgerTransaction"
          :processing="ledgerProcessing"
          :on-reload="reloadLedgerSelection"
          :on-recalculate="recalculateLedgerState"
          :on-reverse="reverseSelectedLedgerTransaction"
        />
      </section>
    </Teleport>

    <section ref="resultsSection" class="workbench-admin-results" data-tour="workbench-admin-results" :aria-label="mode === 'ledger' ? '工作台收退料帳目結果' : '工作台治具品質結果'">
      <header class="workbench-admin-results-toolbar">
        <div><span>{{ mode === "ledger" ? "CASES" : "ISSUES" }}</span><strong>{{ mode === "ledger" ? ledgerTotal : filteredQualityRows.length }}</strong><small>筆資料</small></div>
        <div>
          <label v-if="mode === 'ledger'">每頁<select :value="ledgerPageSize" @change="updateLedgerPageSize(Number(($event.target as HTMLSelectElement).value))"><option :value="12">12</option><option :value="25">25</option><option :value="50">50</option></select></label>
          <button type="button" :disabled="exporting" @click="exportFilteredResults">{{ exporting ? "匯出中…" : "匯出目前結果" }}</button>
        </div>
      </header>

      <template v-if="mode === 'ledger'">
        <div class="workbench-ledger-workspace">
          <TransactionAccountListPanel
            embedded-workbench
            :rows="ledgerTransactions" :selected-transaction-id="selectedLedgerTransactionId" :loading="ledgerLoading"
            :transaction-no="ledgerTransactionNoFilter" :created-by="ledgerCreatedByFilter" :fixture-code="ledgerFixtureCodeFilter"
            :transaction-type="ledgerTypeFilter" :page="ledgerPage" :page-size="ledgerPageSize" :total-pages="ledgerTotalPages" :total="ledgerTotal"
            :on-transaction-no-change="updateLedgerTransactionNo" :on-created-by-change="updateLedgerCreatedBy"
            :on-fixture-code-change="updateLedgerFixtureCode" :on-transaction-type-change="updateLedgerTypeFilter" :on-page-size-change="updateLedgerPageSize"
            :on-select-row="selectLedgerTransaction" :on-previous-page="previousLedgerPage" :on-next-page="nextLedgerPage"
          />
        </div>
        <footer class="workbench-admin-pager">
          <button type="button" :disabled="ledgerPage <= 1" @click="previousLedgerPage">上一頁</button>
          <span>第 {{ ledgerPage }} / {{ ledgerTotalPages }} 頁</span>
          <button type="button" :disabled="ledgerPage >= ledgerTotalPages" @click="nextLedgerPage">下一頁</button>
        </footer>
      </template>

      <FixtureQualityPanel
        v-else
        embedded-workbench
        workbench-side-editor
        :report="qualityReport" :fixtures="fixtures" :loading="qualityLoading"
        :inline-saving-fixture-id="qualityInlineSavingFixtureId" :issue-filter="qualityIssueFilter"
        @open-issue-editor="openQualityIssue" @save-inline-issue="saveInlineQualityIssue"
      />
    </section>
  </div>
</template>
