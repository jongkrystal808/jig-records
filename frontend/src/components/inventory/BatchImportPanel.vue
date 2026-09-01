<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

import { api } from "@/api";
import { onboardingActive, onboardingFlowId, onboardingStepIndex, setCustomerSwitchGuard } from "@/appState";
import InlineSpinner from "@/components/common/InlineSpinner.vue";
import InventoryBatchEntryGrid from "@/components/inventory/InventoryBatchEntryGrid.vue";
import {
  useInventoryBatchParser,
  type InventoryBatchImportRow as BatchImportRow,
  type InventoryBatchOwnershipType as BatchOwnershipType,
  type InventoryImportMode as ImportMode
} from "@/composables/useInventoryBatchParser";
import { useInventoryBatchPreviewState } from "@/composables/useInventoryBatchPreviewState";
import { useInventoryBatchSubmit } from "@/composables/useInventoryBatchSubmit";
import { getOnboardingFlow } from "@/onboarding";
import { pushToast } from "@/toastState";
import type { Fixture, IdentifierStockSummary, StockSummary } from "@/types";
import { downloadCsvRows } from "@/utils/csvDownload";

type BatchDraftState = {
  hasPendingDraft: boolean;
  pendingRowCount: number;
  promptMessage: string;
};

const props = withDefaults(defineProps<{
  customerId: number | undefined;
  title?: string;
  description?: string;
  showModeSwitch?: boolean;
  initialMode?: ImportMode;
  mode?: ImportMode | undefined;
  presetFixtureCode?: string;
  hideFrame?: boolean;
  tutorialMode?: boolean;
}>(), {
  title: "批次貼上匯入",
  description: "可在資料方格直接輸入，或從 Excel／其他表格整塊貼上。",
  showModeSwitch: true,
  initialMode: "receipt",
  hideFrame: false,
  tutorialMode: false
});

const emit = defineEmits<{
  success: [];
  "update:mode": [value: ImportMode];
  "draft-state-change": [value: BatchDraftState];
}>();

const internalMode = ref<ImportMode>(props.initialMode);
const loading = ref(false);
const fixtures = ref<Fixture[]>([]);
const stockRows = ref<StockSummary[]>([]);
const identifierStockRows = ref<IdentifierStockSummary[]>([]);
const batchPasteText = ref("");
const batchTransactionNo = ref("");
const batchNote = ref("");
const batchOwnershipType = ref<BatchOwnershipType>("customer_supplied");
const rows = ref<BatchImportRow[]>([]);
const {
  parseRows: parseBatchRows,
  validateRowsForInventory: validateRowsForCurrentMode
} = useInventoryBatchParser({ fixtures, identifierStockRows });

function parseRows(text: string): BatchImportRow[] {
  return parseBatchRows(text, {
    mode: mode.value,
    transactionNo: batchTransactionNo.value.trim(),
    ownershipType: batchOwnershipType.value,
    note: batchNote.value.trim()
  });
}

const currentOnboardingStepId = computed(() => getOnboardingFlow(onboardingFlowId.value)?.steps[onboardingStepIndex.value]?.id ?? "");
const mode = computed<ImportMode>({
  get: () => props.mode ?? internalMode.value,
  set: (value) => {
    if (props.mode === undefined) {
      internalMode.value = value;
    }
    emit("update:mode", value);
  }
});
const {
  showReadyDetails,
  showAllExceptions,
  readyRows,
  pendingRows,
  errorRows,
  skippedRows,
  exceptionRows,
  visibleExceptionRows,
  hiddenExceptionCount,
  mergedReadyItems,
  mergedReadyItemCount,
  mergedDuplicateReductionCount,
  mergedDuplicateGroupCount,
  readyModes,
  previewHeadline,
  canSubmit,
  previewStats
} = useInventoryBatchPreviewState({ rows, mode, fixtures, stockRows, identifierStockRows });
const tutorialBannerText = computed(() =>
  mode.value === "receipt" ? "教學模式：本次會模擬收料，不會寫入正式資料。" : "教學模式：本次會模擬退料，不會寫入正式資料。"
);
const hasPendingBatchDraft = computed(
  () =>
    batchPasteText.value.trim().length > 0 ||
    batchTransactionNo.value.trim().length > 0 ||
    batchNote.value.trim().length > 0 ||
    rows.value.length > 0
);
const pendingDraftRowCount = computed(() => rows.value.length);
const draftStorageKey = computed(() => {
  if (!props.hideFrame || !props.customerId || props.tutorialMode) {
    return "";
  }
  return `jig-record-inventory-batch-draft:${props.customerId}`;
});
async function loadFixtures(): Promise<void> {
  if (!props.customerId) {
    fixtures.value = [];
    stockRows.value = [];
    identifierStockRows.value = [];
    rows.value = [];
    return;
  }
  loading.value = true;
  try {
    const [fixtureRows, stockSummaryRows, identifierRows] = await Promise.all([
      api.listFixtures(props.customerId),
      api.listStock(props.customerId),
      api.listIdentifierStockSummary(props.customerId)
    ]);
    fixtures.value = fixtureRows;
    stockRows.value = stockSummaryRows;
    identifierStockRows.value = identifierRows;
    rows.value = validateRowsForCurrentMode(parseRows(batchPasteText.value));
  } catch (err) {
    fixtures.value = [];
    stockRows.value = [];
    identifierStockRows.value = [];
    rows.value = [];
    pushToast(err instanceof Error ? err.message : "載入批次匯入資料失敗", "error");
  } finally {
    loading.value = false;
  }
}

function refreshPreview(): void {
  rows.value = validateRowsForCurrentMode(parseRows(batchPasteText.value));
  showAllExceptions.value = false;
}

function clearPersistedDraft(): void {
  if (typeof window === "undefined" || !draftStorageKey.value) {
    return;
  }
  window.sessionStorage.removeItem(draftStorageKey.value);
}

function clearPanel(): void {
  batchPasteText.value = "";
  batchTransactionNo.value = "";
  batchNote.value = "";
  batchOwnershipType.value = "customer_supplied";
  rows.value = [];
  showReadyDetails.value = false;
  showAllExceptions.value = false;
  clearPersistedDraft();
}

function restoreDraftFromSessionStorage(): boolean {
  if (typeof window === "undefined" || !draftStorageKey.value) {
    return false;
  }
  const raw = window.sessionStorage.getItem(draftStorageKey.value);
  if (!raw) {
    return false;
  }
  try {
    const draft = JSON.parse(raw) as {
      mode?: ImportMode;
      batchPasteText?: string;
      batchTransactionNo?: string;
      batchNote?: string;
    };
    if (props.mode === undefined && (draft.mode === "receipt" || draft.mode === "return")) {
      internalMode.value = draft.mode;
    }
    batchOwnershipType.value = "customer_supplied";
    batchPasteText.value = typeof draft.batchPasteText === "string" ? draft.batchPasteText : "";
    batchTransactionNo.value = typeof draft.batchTransactionNo === "string" ? draft.batchTransactionNo : "";
    batchNote.value = typeof draft.batchNote === "string" ? draft.batchNote : "";
    return hasPendingBatchDraft.value;
  } catch {
    window.sessionStorage.removeItem(draftStorageKey.value);
    return false;
  }
}

function persistDraftToSessionStorage(): void {
  if (typeof window === "undefined" || !draftStorageKey.value) {
    return;
  }
  if (!hasPendingBatchDraft.value) {
    clearPersistedDraft();
    return;
  }
  window.sessionStorage.setItem(
    draftStorageKey.value,
    JSON.stringify({
      mode: mode.value,
      batchPasteText: batchPasteText.value,
      batchTransactionNo: batchTransactionNo.value,
      batchNote: batchNote.value
    })
  );
}

function emitDraftState(): void {
  if (props.tutorialMode) {
    emit("draft-state-change", {
      hasPendingDraft: false,
      pendingRowCount: 0,
      promptMessage: ""
    });
    return;
  }
  const rowCount = pendingDraftRowCount.value;
  emit("draft-state-change", {
    hasPendingDraft: hasPendingBatchDraft.value,
    pendingRowCount: rowCount,
    promptMessage:
      rowCount > 0
        ? `目前有尚未送出的 ${rowCount} 筆資料，確定離開嗎？`
        : "目前有尚未送出的草稿，確定離開嗎？"
  });
}

function acceptSimilar(row: BatchImportRow): void {
  if (!row.suggestedFixtureId) return;
  row.resolvedFixtureId = row.suggestedFixtureId;
  row.resolvedFixtureCode = row.suggestedFixtureCode;
  row.suggestedFixtureId = null;
  row.suggestedFixtureCode = "";
  row.status = "ready";
  row.message = null;
  row.errorSource = null;
  rows.value = validateRowsForCurrentMode(rows.value);
}

function rejectSimilar(row: BatchImportRow): void {
  row.suggestedFixtureId = null;
  row.suggestedFixtureCode = "";
  row.status = "needs-add";
  row.message = `找不到治具 ${row.inputFixtureCode}`;
  row.errorSource = null;
}

function skipRow(row: BatchImportRow): void {
  row.status = "skipped";
  row.message = "已略過，不會送出";
  row.errorSource = null;
  rows.value = validateRowsForCurrentMode(rows.value);
}

async function createMissingFixture(row: BatchImportRow): Promise<void> {
  if (!props.customerId) return;
  const defaultName = row.inputFixtureCode;
  const fixtureName = window.prompt(`為 ${row.inputFixtureCode} 輸入治具名稱`, defaultName)?.trim();
  if (!fixtureName) return;
  const created = await api.createFixture({
    customer_id: props.customerId,
    code: row.inputFixtureCode.trim(),
    name: fixtureName
  });
  fixtures.value = [...fixtures.value, created];
  row.resolvedFixtureId = created.id;
  row.resolvedFixtureCode = created.code;
  row.status = "ready";
  row.message = null;
  row.errorSource = null;
  rows.value = validateRowsForCurrentMode(rows.value);
}

function fillTutorialSample(): void {
  const sampleFixture = fixtures.value[0];
  if (!sampleFixture) {
    pushToast("目前客戶下沒有治具資料，無法進行教學試跑。", "warning");
    return;
  }
  const sampleIdentifier = "0001";
  batchTransactionNo.value = `TUTORIAL-${mode.value === "receipt" ? "RCV" : "RTN"}-001`;
  batchNote.value = "導覽教學試跑";
  batchPasteText.value = `${sampleFixture.code}-${sampleIdentifier}\n1`;
  refreshPreview();
}

function exportCurrentRows(): void {
  downloadCsvRows(
    "form-inventory-import-current.csv",
    ["收／退料", "單號", "治具", "來源", "datecode/編號", "數量", "備註", "解析狀態"],
    rows.value.map((row) => [
      row.mode === "receipt" ? "收料" : "退料",
      row.transactionNo,
      row.resolvedFixtureCode || row.inputFixtureCode,
      row.ownershipType === "self_purchased" ? "自購" : "客供",
      row.inputToken,
      row.quantity,
      row.note,
      row.status
    ])
  );
}

const { saving, submit } = useInventoryBatchSubmit({
  customerId: () => props.customerId,
  tutorialMode: () => props.tutorialMode,
  readyRows,
  mergedReadyItems,
  canSubmit,
  clearPanel,
  emitSuccess: () => emit("success"),
  reloadFixtures: loadFixtures
});
watch(() => props.customerId, async () => {
  await loadFixtures();
});

watch(batchPasteText, () => {
  refreshPreview();
});

watch(mode, () => {
  refreshPreview();
});

watch(
  () => props.initialMode,
  (value) => {
    if (props.mode === undefined) {
      internalMode.value = value;
    }
  }
);

watch(
  hasPendingBatchDraft,
  (value) => {
    setCustomerSwitchGuard(
      props.hideFrame ? "inventory-batch-modal" : "inventory-batch-panel",
      value,
      "收退料批次資料尚未送出"
    );
  },
  { immediate: true }
);

watch(
  () => [props.tutorialMode, onboardingActive.value, currentOnboardingStepId.value, fixtures.value.length] as const,
  () => {
    if (!props.tutorialMode || !onboardingActive.value) {
      return;
    }
    if (![
      "inventory-paste",
      "inventory-submit",
      "form-detail-import-grid",
      "form-detail-import-preview",
      "form-detail-import-actions"
    ].includes(currentOnboardingStepId.value)) {
      return;
    }
    if (rows.value.length > 0 && batchTransactionNo.value.trim().length > 0) {
      return;
    }
    fillTutorialSample();
  },
  { immediate: true }
);

watch(
  [
    mode,
    batchPasteText,
    batchTransactionNo,
    batchNote,
    rows,
    () => props.tutorialMode,
    draftStorageKey
  ],
  () => {
    persistDraftToSessionStorage();
    emitDraftState();
  },
  { deep: true, immediate: true }
);

onMounted(async () => {
  const restored = restoreDraftFromSessionStorage();
  if (restored) {
    pushToast("已恢復上次未送出的收退料草稿。", "info");
  }
  await loadFixtures();
});

onBeforeUnmount(() => {
  setCustomerSwitchGuard("inventory-batch-modal", false, "收退料批次資料尚未送出");
  setCustomerSwitchGuard("inventory-batch-panel", false, "收退料批次資料尚未送出");
  emit("draft-state-change", {
    hasPendingDraft: false,
    pendingRowCount: 0,
    promptMessage: ""
  });
});
</script>

<template>
  <section class="batch-panel" :class="[mode, { frameless: hideFrame }]">
    <div v-if="loading" class="loading-row">
      <InlineSpinner label="載入收退料匯入資料..." />
    </div>

    <template v-else>
      <div v-if="tutorialMode" class="tutorial-banner">
        <strong>教學模式</strong>
        <span>{{ tutorialBannerText }}</span>
      </div>

      <InventoryBatchEntryGrid
        v-model="batchPasteText"
        v-model:mode="mode"
        v-model:transaction-no="batchTransactionNo"
        :fixtures="fixtures"
        :preset-fixture-code="presetFixtureCode"
        :default-ownership-type="batchOwnershipType"
        :default-note="batchNote"
        :show-mode-switch="showModeSwitch"
        :disabled="saving"
      >
        <template #between-meta-and-grid>
          <slot name="between-meta-and-grid" />
        </template>
      </InventoryBatchEntryGrid>

      <div class="action-row">
        <div class="summary-text" data-tour="inventory-import-summary">
          <span>可直接送出 {{ readyRows.length }} 筆</span>
          <span v-if="mergedDuplicateReductionCount > 0">送出時自動合併 {{ mergedDuplicateReductionCount }} 筆重複資料</span>
          <span>待處理 {{ pendingRows.length }} 筆</span>
          <span>錯誤 {{ errorRows.length }} 筆</span>
          <span v-if="skippedRows.length > 0">已略過 {{ skippedRows.length }} 筆</span>
        </div>
        <div class="action-group" data-tour="detailed-inventory-actions">
          <button
            v-if="tutorialMode"
            class="ghost-btn panel-accent-ghost"
            data-tour="inventory-sandbox-action"
            type="button"
            :disabled="saving || fixtures.length === 0"
            @click="fillTutorialSample"
          >
            套用教學試跑
          </button>
          <button class="outline-btn" type="button" :disabled="saving" @click="clearPanel">清空</button>
          <button class="outline-btn" type="button" :disabled="saving || rows.length === 0" @click="exportCurrentRows">匯出篩選結果</button>
          <button class="primary-btn panel-accent-btn" data-tour="inventory-submit-action" type="button" :disabled="saving || !canSubmit" @click="submit">
            {{ saving ? "送出中..." : readyModes.size > 1 ? "送出收退料" : (readyRows[0]?.mode ?? mode) === "receipt" ? "送出收料" : "送出退料" }}
          </button>
        </div>
      </div>

      <div v-if="rows.length > 0" class="preview-summary-stack">
        <section class="preview-summary-card ready-card" data-tour="inventory-ready-summary">
          <div class="preview-summary-head">
            <div>
              <strong>{{ previewHeadline }}</strong>
              <p>精確匹配的治具不需逐列確認，解完例外後可一次提交全部資料。</p>
            </div>
            <button class="outline-btn btn-sm" type="button" :disabled="readyRows.length === 0" @click="showReadyDetails = !showReadyDetails">
              {{ showReadyDetails ? "收合正常列" : "查看正常列" }}
            </button>
          </div>
          <div class="preview-summary-meta">
            <span>可直接送出 {{ readyRows.length }} 筆</span>
            <span>實際送出 {{ mergedReadyItemCount }} 筆項目</span>
            <span v-if="mergedDuplicateReductionCount > 0">已自動合併 {{ mergedDuplicateGroupCount }} 組重複資料</span>
          </div>
        </section>

        <div v-if="showReadyDetails" class="table-wrap" data-tour="inventory-preview-table">
          <table class="preview-table">
            <thead>
              <tr><th>#</th><th>治具</th><th>datecode/編號</th><th>數量</th><th>目前庫存</th><th>交易後庫存</th><th>狀態</th></tr>
            </thead>
            <tbody>
              <tr v-for="row in readyRows" :key="`${row.lineNo}-${row.raw}`">
                <td>{{ row.lineNo }}</td>
                <td>{{ row.resolvedFixtureCode || row.inputFixtureCode || "-" }}</td>
                <td>{{ row.inputToken || "-" }}</td>
                <td>{{ row.mode === "receipt" ? row.quantity : `-${row.quantity}` }}</td>
                <td>{{ previewStats[row.lineNo - 1]?.currentIdentifierStockQty ?? "-" }}</td>
                <td>{{ previewStats[row.lineNo - 1]?.nextIdentifierStockQty ?? "-" }}</td>
                <td><span class="status-pill batch-state ready">ready</span></td>
              </tr>
            </tbody>
          </table>
        </div>

        <section class="preview-summary-card exception-card" data-tour="inventory-exception-summary">
          <div class="preview-summary-head">
            <div>
              <strong>{{ exceptionRows.length }} 筆需要處理</strong>
              <p v-if="exceptionRows.length > 0">預設只展開前 3 筆例外，處理完後可直接一次送出。</p>
              <p v-else>目前沒有待處理例外。</p>
            </div>
            <button v-if="hiddenExceptionCount > 0 || showAllExceptions" class="outline-btn btn-sm" type="button" @click="showAllExceptions = !showAllExceptions">
              {{ showAllExceptions ? "只看前 3 筆" : `顯示其餘 ${hiddenExceptionCount} 筆` }}
            </button>
          </div>
        </section>

        <div v-if="exceptionRows.length > 0" class="table-wrap">
          <table class="preview-table exception-table">
            <thead>
              <tr><th>#</th><th>治具</th><th>datecode/編號</th><th>數量</th><th>目前庫存</th><th>交易後庫存</th><th>狀態</th><th>處理</th></tr>
            </thead>
            <tbody>
              <tr v-for="row in visibleExceptionRows" :key="`${row.lineNo}-${row.raw}`">
                <td>{{ row.lineNo }}</td>
                <td>{{ row.resolvedFixtureCode || row.suggestedFixtureCode || row.inputFixtureCode || "-" }}</td>
                <td>{{ row.inputToken || "-" }}</td>
                <td>{{ row.mode === "receipt" ? row.quantity : `-${row.quantity}` }}</td>
                <td>{{ previewStats[row.lineNo - 1]?.currentIdentifierStockQty ?? "-" }}</td>
                <td>{{ previewStats[row.lineNo - 1]?.nextIdentifierStockQty ?? "-" }}</td>
                <td>
                  <span class="status-pill batch-state" :class="row.status">{{ row.status }}</span>
                  <div v-if="row.message" class="row-note">{{ row.message }}</div>
                </td>
                <td>
                  <div class="row-actions">
                    <template v-if="row.status === 'needs-confirm'">
                      <button class="ghost-btn panel-accent-ghost btn-sm" type="button" @click="acceptSimilar(row)">同一治具</button>
                      <button class="outline-btn btn-sm" type="button" @click="rejectSimilar(row)">改為新增</button>
                      <button class="outline-btn btn-sm" type="button" @click="skipRow(row)">略過</button>
                    </template>
                    <template v-else-if="row.status === 'needs-add'">
                      <button class="ghost-btn panel-accent-ghost btn-sm" type="button" @click="createMissingFixture(row)">新增治具</button>
                      <button class="outline-btn btn-sm" type="button" @click="skipRow(row)">略過</button>
                    </template>
                    <template v-else-if="row.status === 'error'">
                      <span class="muted">請修正原始資料</span>
                    </template>
                    <template v-else>
                      <span class="muted">待處理</span>
                    </template>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <section v-if="skippedRows.length > 0" class="preview-summary-card skipped-card">
          <div class="preview-summary-head">
            <div>
              <strong>{{ skippedRows.length }} 筆已略過</strong>
              <p>這些資料不會送出；如需補回，請回原始貼上內容修正後重新解析。</p>
            </div>
          </div>
        </section>
      </div>

      <div v-else class="table-wrap" data-tour="inventory-preview-table">
        <table class="preview-table">
          <tbody>
            <tr>
              <td colspan="8" class="empty-cell">貼上資料後會自動解析預覽</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </section>
</template>

<style scoped>
.batch-panel {
  --panel-accent: var(--action-in);
  --panel-accent-strong: var(--action-in-strong);
  --panel-accent-soft: var(--action-in-soft);
  --panel-input-border: rgba(47, 125, 224, 0.34);
  display: grid;
  gap: 12px;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--panel-accent-soft) 72%, white) 0%, #ffffff 22%);
  padding: 14px;
  position: relative;
}

.batch-panel::before {
  content: "";
  position: absolute;
  inset: 0 0 auto 0;
  height: 4px;
  border-radius: 18px 18px 0 0;
  background: linear-gradient(90deg, var(--panel-accent) 0%, var(--panel-accent-strong) 100%);
}

.batch-panel.receipt {
  --panel-accent: var(--action-in);
  --panel-accent-strong: var(--action-in-strong);
  --panel-accent-soft: var(--action-in-soft);
  --panel-input-border: rgba(47, 125, 224, 0.34);
}

.batch-panel.return {
  --panel-accent: var(--action-out);
  --panel-accent-strong: var(--action-out-strong);
  --panel-accent-soft: var(--action-out-soft);
  --panel-input-border: rgba(106, 95, 196, 0.34);
}

.batch-panel.frameless {
  border: 0;
  border-radius: 0;
  padding: 0;
  background: transparent;
}

.batch-panel.frameless::before {
  display: none;
}

.batch-head,
.action-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}

.batch-head h2 {
  margin: 0;
  color: #22314a;
  font-size: 18px;
}

.batch-head p,
.summary-text,
.row-note,
.muted,
.empty-cell,
label span {
  color: #5d6d89;
  font-size: 12px;
}

.batch-head p {
  margin: 4px 0 0;
}

.tutorial-banner {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border: 1px solid var(--panel-input-border);
  border-radius: 12px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--panel-accent-soft) 82%, white) 0%, color-mix(in srgb, var(--panel-accent-soft) 48%, white) 100%);
}

.tutorial-banner strong {
  color: var(--panel-accent-strong);
  font-size: 12px;
}

.segmented-control {
  display: inline-flex;
  gap: 4px;
  padding: 4px;
  border: 1px solid var(--panel-input-border);
  border-radius: 999px;
  background: color-mix(in srgb, var(--panel-accent-soft) 64%, white);
}

.segmented-btn {
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: #5b677d;
  padding: 8px 14px;
  min-height: 34px;
  font-weight: 800;
}

.segmented-btn.active {
  background: linear-gradient(180deg, color-mix(in srgb, var(--panel-accent-soft) 70%, white) 0%, color-mix(in srgb, var(--panel-accent-soft) 92%, white) 100%);
  color: var(--panel-accent-strong);
  box-shadow: 0 6px 16px color-mix(in srgb, var(--panel-accent) 18%, transparent);
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

label {
  display: grid;
  gap: 6px;
}

.batch-source-field {
  display: grid;
  gap: 6px;
}

.batch-source-field > span {
  color: #5d6d89;
  font-size: 12px;
  font-weight: 700;
}

.batch-source-control {
  justify-content: flex-start;
  width: fit-content;
}

.batch-source-warning {
  padding: 10px 12px;
  border: 1px solid rgba(217, 126, 31, 0.28);
  border-radius: 12px;
  background: linear-gradient(180deg, #fff5e7 0%, #fff0db 100%);
  color: #9a4d00;
  font-size: 12px;
  font-weight: 700;
}

label span {
  font-weight: 700;
}

input {
  width: 100%;
  border: 1px solid var(--panel-input-border);
  border-radius: 10px;
  padding: 8px 10px;
  background: #fff;
  font: inherit;
}

input:focus {
  outline: none;
  border-color: var(--panel-accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--panel-accent-soft) 88%, white);
}

.summary-text,
.action-group,
.row-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.summary-text {
  align-items: center;
}

.preview-summary-stack {
  display: grid;
  gap: 10px;
}

.preview-summary-card {
  display: grid;
  gap: 8px;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: #fff;
}

.ready-card {
  background: linear-gradient(180deg, color-mix(in srgb, var(--panel-accent-soft) 38%, white) 0%, #fff 100%);
}

.exception-card {
  border-color: rgba(212, 89, 89, 0.2);
  background: linear-gradient(180deg, rgba(255, 245, 245, 0.9) 0%, #fff 100%);
}

.skipped-card {
  background: linear-gradient(180deg, #fbfcfe 0%, #fff 100%);
}

.preview-summary-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.preview-summary-head strong {
  color: #22314a;
  font-size: 15px;
}

.preview-summary-head p {
  margin: 4px 0 0;
  color: #5d6d89;
  font-size: 12px;
}

.preview-summary-meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  color: #5d6d89;
  font-size: 12px;
}

.table-wrap {
  max-height: 380px;
  overflow: auto;
}

.preview-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border: 1px solid var(--line);
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
}

.preview-table th,
.preview-table td {
  padding: 7px 8px;
  border-bottom: 1px solid var(--line);
  text-align: left;
  vertical-align: top;
  font-size: 12px;
}

.preview-table thead th {
  background: #f7f9fd;
  color: #52607b;
  font-weight: 700;
}

.preview-table tbody tr:last-child td {
  border-bottom: none;
}

.primary-btn.panel-accent-btn {
  border: 1px solid var(--panel-accent-strong);
  background: linear-gradient(180deg, var(--panel-accent) 0%, var(--panel-accent-strong) 100%);
  color: #fff;
}

.ghost-btn.panel-accent-ghost {
  border-color: var(--panel-input-border);
  color: var(--panel-accent-strong);
  background: color-mix(in srgb, var(--panel-accent-soft) 72%, white);
}

.loading-row {
  display: flex;
  align-items: center;
  min-height: 72px;
}

@media (max-width: 720px) {
  .batch-head,
  .action-row,
  .preview-summary-head {
    flex-direction: column;
  }

  .meta-grid {
    grid-template-columns: 1fr;
  }

}
</style>
