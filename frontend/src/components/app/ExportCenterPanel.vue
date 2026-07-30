<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { api } from "@/api";
import { onboardingActive, onboardingFlowId, onboardingStepIndex } from "@/appState";
import { getOnboardingFlow } from "@/onboarding";
import { pushToast } from "@/toastState";

type ExportDataset =
  | "inventory-summary"
  | "inventory-detail"
  | "fixtures"
  | "models"
  | "stations"
  | "station-settings"
  | "fixture-requirements"
  | "fixture-quality";
type FileFormat = "xlsx" | "txt" | "csv";
type ExportScopeMode = "all" | "custom";

type DatasetOption = {
  id: ExportDataset;
  label: string;
  description: string;
  formats: FileFormat[];
};

const DATASET_OPTIONS: DatasetOption[] = [
  { id: "inventory-summary", label: "收退料摘要", description: "適合快速核對各治具收退料加總。", formats: ["xlsx", "txt"] },
  { id: "inventory-detail", label: "收退料明細", description: "適合追 identifier、單號與異常明細。", formats: ["xlsx", "txt"] },
  { id: "fixtures", label: "治具主資料", description: "匯出目前客戶的治具主檔。", formats: ["csv"] },
  { id: "models", label: "機種主資料", description: "匯出目前客戶的機種主檔。", formats: ["csv"] },
  { id: "stations", label: "站點主資料", description: "匯出目前客戶的站點主檔。", formats: ["csv"] },
  { id: "station-settings", label: "站點設定", description: "匯出機種對應站點設定。", formats: ["csv"] },
  { id: "fixture-requirements", label: "治具需求", description: "匯出各機種站點的治具需求。", formats: ["csv"] },
  { id: "fixture-quality", label: "治具資料品質", description: "匯出品質異常報表與 issue 狀態。", formats: ["csv"] }
];

let exportCenterInstanceCount = 0;

const props = defineProps<{
  customerId: number | undefined;
  role?: string;
}>();

const emit = defineEmits<{
  close: [];
}>();

const instanceId = ++exportCenterInstanceCount;
const datasetGroupName = `export-center-dataset-${instanceId}`;
const formatGroupName = `export-center-format-${instanceId}`;
const scopeModeGroupName = `export-center-scope-${instanceId}`;

const exporting = ref(false);
const dataset = ref<ExportDataset>("inventory-summary");
const fileFormat = ref<FileFormat>("xlsx");
const scopeMode = ref<ExportScopeMode>("all");
const dateFrom = ref("");
const dateTo = ref("");
const transactionNo = ref("");
const fixtureCode = ref("");
const identifier = ref("");
const transactionType = ref<"" | "receipt" | "return">("");
const ownershipType = ref<"" | "customer_supplied" | "self_purchased">("");

const visibleDatasetOptions = computed(() =>
  DATASET_OPTIONS.filter((option) => option.id !== "fixture-quality" || props.role === "admin")
);
const selectedDataset = computed(() => visibleDatasetOptions.value.find((option) => option.id === dataset.value) ?? visibleDatasetOptions.value[0]);
const formatOptions = computed(() => selectedDataset.value.formats);
const usingCustomScope = computed(() => scopeMode.value === "custom");
const supportsCustomScope = computed(() => dataset.value === "inventory-summary" || dataset.value === "inventory-detail");
const currentOnboardingStepId = computed(() => getOnboardingFlow(onboardingFlowId.value)?.steps[onboardingStepIndex.value]?.id ?? "");
const previewColumns = computed(() => {
  if (dataset.value === "inventory-summary") return ["治具編號", "收料數", "退料數", "總數"];
  if (dataset.value === "inventory-detail") return ["治具編號", "識別碼", "收料數", "退料數", "總數"];
  if (dataset.value === "fixtures") return ["治具編號", "治具名稱", "產線儲位", "部門儲位", "最低水位"];
  if (dataset.value === "models") return ["機種編號", "機種名稱", "是否啟用"];
  if (dataset.value === "stations") return ["站點編號", "站點名稱", "是否啟用"];
  if (dataset.value === "station-settings") return ["機種編號", "站點編號"];
  if (dataset.value === "fixture-requirements") return ["機種編號", "站點編號", "治具編號", "需求數量"];
  return ["治具編號", "治具名稱", "儲位", "最低水位", "總庫存", "Identifier庫存", "機種關聯數", "圖片", "問題"];
});

function normalizeOptional(value: string): string | undefined {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function downloadText(content: string, filename: string, mime = "text/csv;charset=utf-8"): void {
  const blob = new Blob(["\ufeff", content], { type: mime });
  downloadBlob(blob, filename);
}

function displayQualityIssueCodes(issueCodes: string[]): string[] {
  const visibleCodes = issueCodes.filter((issueCode) => issueCode !== "missing_storage_location" && issueCode !== "missing_min_stock_qty");
  if (issueCodes.includes("missing_storage_location") || issueCodes.includes("missing_min_stock_qty")) {
    visibleCodes.unshift("missing_storage_and_min_stock");
  }
  return visibleCodes;
}

function qualityIssueLabel(issueCode: string): string {
  if (issueCode === "missing_name") return "沒有名稱";
  if (issueCode === "missing_storage_and_min_stock") return "沒有儲位 / 沒有最低水位";
  if (issueCode === "missing_image") return "沒有圖片";
  if (issueCode === "missing_model_relation") return "沒有任何機種關聯";
  if (issueCode === "stock_mismatch") return "Identifier 庫存與總庫存不一致";
  return issueCode;
}

function buildFixtureQualityCsv(report: Awaited<ReturnType<typeof api.getFixtureQualityReport>>): string {
  const header = ["治具編號", "治具名稱", "儲位", "最低水位", "總庫存", "Identifier庫存", "機種關聯數", "圖片", "問題"];
  const rows = report.rows.map((row) =>
    [
      row.fixture_code,
      row.fixture_name ?? "",
      row.storage_location ?? "",
      String(row.min_stock_qty),
      String(row.stock_qty),
      String(row.identifier_stock_qty),
      String(row.related_model_count),
      row.has_image ? "有" : "缺",
      displayQualityIssueCodes(row.issue_codes).map((issueCode) => qualityIssueLabel(issueCode)).join(" / ")
    ].map((value) => `"${String(value).replace(/"/g, '""')}"`)
  );
  return [header, ...rows].map((row) => row.join(",")).join("\n");
}

async function exportReport(): Promise<void> {
  if (!props.customerId) {
    pushToast("請先選擇客戶後再匯出。", "warning");
    return;
  }
  if (supportsCustomScope.value && usingCustomScope.value && dateFrom.value && dateTo.value && dateFrom.value > dateTo.value) {
    pushToast("開始日期不能晚於結束日期。", "warning");
    return;
  }

  exporting.value = true;
  try {
    if (dataset.value === "inventory-summary" || dataset.value === "inventory-detail") {
      const response = await api.exportTransactionReport({
        customer_id: props.customerId,
        report_type: dataset.value === "inventory-summary" ? "summary" : "detail",
        file_format: fileFormat.value as "xlsx" | "txt",
        transaction_type: supportsCustomScope.value && usingCustomScope.value ? (transactionType.value || undefined) : undefined,
        date_from: supportsCustomScope.value && usingCustomScope.value ? normalizeOptional(dateFrom.value) : undefined,
        date_to: supportsCustomScope.value && usingCustomScope.value ? normalizeOptional(dateTo.value) : undefined,
        transaction_no: supportsCustomScope.value && usingCustomScope.value ? normalizeOptional(transactionNo.value) : undefined,
        fixture_code: supportsCustomScope.value && usingCustomScope.value ? normalizeOptional(fixtureCode.value) : undefined,
        ownership_type:
          dataset.value === "inventory-detail" && usingCustomScope.value ? (ownershipType.value || undefined) : undefined,
        identifier: supportsCustomScope.value && usingCustomScope.value ? normalizeOptional(identifier.value) : undefined
      });
      const fallbackName = `transaction-${dataset.value === "inventory-summary" ? "summary" : "detail"}.${fileFormat.value}`;
      downloadBlob(response.blob, response.filename ?? fallbackName);
    } else if (dataset.value === "fixtures") {
      downloadText(await api.exportFixturesCsv(props.customerId), "fixtures.csv");
    } else if (dataset.value === "models") {
      downloadText(await api.exportModelsCsv(props.customerId), "models.csv");
    } else if (dataset.value === "stations") {
      downloadText(await api.exportStationsCsv(props.customerId), "stations.csv");
    } else if (dataset.value === "station-settings") {
      downloadText(await api.exportModelStationsCsv(props.customerId), "station-settings.csv");
    } else if (dataset.value === "fixture-requirements") {
      downloadText(await api.exportFixtureRequirementsCsv(props.customerId), "fixture-requirements.csv");
    } else {
      const report = await api.getFixtureQualityReport(props.customerId);
      downloadText(buildFixtureQualityCsv(report), "fixture-quality-report.csv");
    }
    pushToast("匯出完成。", "success");
    emit("close");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "匯出失敗", "error");
  } finally {
    exporting.value = false;
  }
}

watch(
  dataset,
  (value) => {
    const option = visibleDatasetOptions.value.find((item) => item.id === value);
    fileFormat.value = option?.formats[0] ?? "csv";
    if (!supportsCustomScope.value) {
      scopeMode.value = "all";
    }
    if (value !== "inventory-detail") {
      ownershipType.value = "";
    }
  },
  { immediate: true }
);

watch(
  visibleDatasetOptions,
  (options) => {
    if (!options.some((option) => option.id === dataset.value)) {
      dataset.value = options[0]?.id ?? "inventory-summary";
    }
  },
  { immediate: true }
);

watch(
  () => [onboardingActive.value, currentOnboardingStepId.value] as const,
  ([active, stepId]) => {
    if (
      active &&
      ["inventory-export-filters", "detailed-export-filters", "detailed-export-source"].includes(stepId)
    ) {
      dataset.value = "inventory-detail";
      scopeMode.value = "custom";
    }
  },
  { immediate: true }
);
</script>

<template>
  <section class="export-panel" data-tour="inventory-export-content">
    <header class="export-head">
      <div class="title-row">
        <h2>統一匯出中心</h2>
        <span class="export-pill">Export Center</span>
      </div>
      <button class="outline-btn" type="button" @click="emit('close')">關閉</button>
    </header>

    <fieldset class="selection-block selection-fieldset" data-tour="detailed-export-dataset">
      <legend>匯出資料</legend>
      <div class="dataset-grid">
        <label v-for="option in visibleDatasetOptions" :key="option.id" class="dataset-card" :class="{ selected: dataset === option.id }">
          <input v-model="dataset" type="radio" :name="datasetGroupName" :value="option.id" />
          <strong>{{ option.label }}</strong>
          <span>{{ option.description }}</span>
        </label>
      </div>
    </fieldset>

    <div class="selection-grid">
      <fieldset class="selection-block selection-fieldset" data-tour="inventory-export-report-type">
        <legend>匯出格式</legend>
        <label v-for="format in formatOptions" :key="format" class="radio-row" :class="{ selected: fileFormat === format }">
          <input v-model="fileFormat" type="radio" :name="formatGroupName" :value="format" />
          <span class="radio-indicator" aria-hidden="true"></span>
          <span>{{ format.toUpperCase() }}</span>
        </label>
      </fieldset>

      <fieldset class="selection-block selection-fieldset" data-tour="inventory-export-scope-mode">
        <legend>資料範圍</legend>
        <template v-if="supportsCustomScope">
          <label class="radio-row" :class="{ selected: scopeMode === 'all' }">
            <input v-model="scopeMode" type="radio" :name="scopeModeGroupName" value="all" />
            <span class="radio-indicator" aria-hidden="true"></span>
            <span>全部</span>
          </label>
          <label class="radio-row" :class="{ selected: scopeMode === 'custom' }">
            <input v-model="scopeMode" type="radio" :name="scopeModeGroupName" value="custom" />
            <span class="radio-indicator" aria-hidden="true"></span>
            <span>自定義條件</span>
          </label>
        </template>
        <div v-else class="scope-note">
          <strong>目前客戶全部資料</strong>
          <span>這類資料會直接依目前選擇的客戶匯出完整內容。</span>
        </div>
      </fieldset>
    </div>

    <section v-if="supportsCustomScope && usingCustomScope" class="filter-card" data-tour="inventory-export-filters">
      <div class="filter-card-head">
        <strong>進階篩選條件</strong>
        <span>留空代表不限制；多個條件會同時套用。</span>
      </div>
      <div class="field-grid date-grid">
        <label class="field">
          <span>日期 (起)</span>
          <input v-model="dateFrom" type="date" />
        </label>
        <label class="field">
          <span>日期 (迄)</span>
          <input v-model="dateTo" type="date" />
        </label>
      </div>

      <div class="field-grid">
        <label class="field">
          <span>交易類型</span>
          <select v-model="transactionType">
            <option value="">全部</option>
            <option value="receipt">收料</option>
            <option value="return">退料</option>
          </select>
        </label>
        <label v-if="dataset === 'inventory-detail'" class="field" data-tour="detailed-export-source">
          <span>來源</span>
          <select v-model="ownershipType">
            <option value="">全部</option>
            <option value="customer_supplied">客供</option>
            <option value="self_purchased">自購</option>
          </select>
        </label>
        <label class="field">
          <span>單號</span>
          <input v-model="transactionNo" placeholder="25123456" spellcheck="false" />
        </label>
        <label class="field">
          <span>治具編號</span>
          <input v-model="fixtureCode" placeholder="C-00001" spellcheck="false" />
        </label>
        <label class="field field-wide">
          <span>datecode/編號 / 舊 Datecode</span>
          <input v-model="identifier" placeholder="例如 0001 或 2024W12" spellcheck="false" />
        </label>
      </div>
    </section>

    <div class="column-note" data-tour="detailed-export-columns">
      <span>預計匯出欄位</span>
      <div class="preview-columns">
        <span v-for="column in previewColumns" :key="column" class="preview-chip">{{ column }}</span>
      </div>
    </div>

    <div class="actions" data-tour="inventory-export-submit">
      <button class="outline-btn" type="button" :disabled="exporting" @click="emit('close')">取消</button>
      <button class="primary-btn export-submit" type="button" :disabled="exporting" @click="exportReport">
        {{ exporting ? "匯出中..." : "開始匯出" }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.export-panel {
  display: grid;
  gap: 18px;
}

.export-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-row h2 {
  margin: 0;
  color: #22314a;
  font-size: 20px;
}

.export-pill {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 0 10px;
  border: 1px solid color-mix(in srgb, var(--blue) 18%, var(--line));
  border-radius: 999px;
  background: color-mix(in srgb, var(--blue-soft) 74%, white);
  color: color-mix(in srgb, var(--blue) 78%, var(--text));
  font-size: 12px;
  font-weight: 700;
}

.outline-btn,
.primary-btn {
  min-height: 38px;
  border-radius: 14px;
}

.primary-btn:disabled,
.outline-btn:disabled {
  opacity: 0.64;
  cursor: not-allowed;
}

.selection-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 28px;
}

.selection-block {
  display: grid;
  gap: 12px;
  margin: 0;
}

.selection-fieldset {
  min-width: 0;
  padding: 0;
  border: 0;
}

.selection-fieldset legend,
.field span,
.column-note span {
  margin: 0;
  color: #56657f;
  font-size: 12px;
  font-weight: 700;
}

.dataset-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.dataset-card {
  display: grid;
  gap: 6px;
  padding: 14px;
  border: 1px solid color-mix(in srgb, var(--blue) 16%, var(--line));
  border-radius: 16px;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.16s ease, background 0.16s ease, box-shadow 0.16s ease;
}

.dataset-card.selected {
  border-color: color-mix(in srgb, var(--blue) 34%, var(--line));
  background: color-mix(in srgb, var(--blue-soft) 58%, white);
  box-shadow: 0 8px 18px rgba(47, 110, 229, 0.08);
}

.dataset-card input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.dataset-card strong {
  color: #22314a;
  font-size: 14px;
}

.dataset-card span {
  color: #5d6d89;
  font-size: 12px;
  line-height: 1.5;
}

.radio-row {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid color-mix(in srgb, var(--blue) 16%, var(--line));
  border-radius: 14px;
  background: #fff;
  color: #233248;
  font-size: 14px;
  min-height: 48px;
  cursor: pointer;
  transition: border-color 0.16s ease, background 0.16s ease, box-shadow 0.16s ease;
}

.radio-row.selected {
  border-color: color-mix(in srgb, var(--blue) 34%, var(--line));
  background: color-mix(in srgb, var(--blue-soft) 58%, white);
  box-shadow: 0 8px 18px rgba(47, 110, 229, 0.08);
}

.radio-row input[type="radio"] {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.radio-indicator {
  position: relative;
  flex: 0 0 18px;
  width: 18px;
  height: 18px;
  border: 2px solid color-mix(in srgb, var(--blue) 44%, #9fb2d0);
  border-radius: 999px;
  background: #fff;
}

.radio-indicator::after {
  content: "";
  position: absolute;
  inset: 3px;
  border-radius: 999px;
  background: var(--blue);
  transform: scale(0);
  transition: transform 0.16s ease;
}

.radio-row.selected .radio-indicator::after {
  transform: scale(1);
}

.scope-note {
  display: grid;
  gap: 6px;
  padding: 14px;
  border: 1px solid color-mix(in srgb, var(--blue) 16%, var(--line));
  border-radius: 16px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--blue-soft) 44%, white) 0%, #ffffff 100%);
}

.scope-note strong {
  color: #22314a;
  font-size: 14px;
}

.scope-note span {
  color: #5d6d89;
  font-size: 12px;
  line-height: 1.5;
}

.filter-card {
  display: grid;
  gap: 12px;
  padding: 14px;
  border: 1px solid color-mix(in srgb, var(--blue) 18%, var(--line));
  border-radius: 16px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--blue-soft) 56%, white) 0%, #ffffff 100%);
}

.filter-card-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.filter-card-head strong {
  color: #22314a;
  font-size: 14px;
}

.filter-card-head span {
  color: #697791;
  font-size: 12px;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.date-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.field {
  display: grid;
  gap: 6px;
}

.field-wide {
  grid-column: span 2;
}

.field input,
.field select {
  width: 100%;
  border: 1px solid var(--line-strong);
  border-radius: 14px;
  padding: 10px 12px;
  background: #fff;
  color: var(--text);
  font: inherit;
}

.field input:focus,
.field select:focus {
  outline: none;
  border-color: rgba(47, 110, 229, 0.5);
  box-shadow: 0 0 0 3px rgba(47, 110, 229, 0.12);
}

.column-note {
  display: grid;
  gap: 8px;
}

.preview-columns {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preview-chip {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 4px 10px;
  border: 1px solid color-mix(in srgb, var(--blue) 18%, var(--line));
  border-radius: 999px;
  background: color-mix(in srgb, var(--blue-soft) 70%, white);
  color: color-mix(in srgb, var(--blue) 72%, var(--text));
  font-size: 12px;
  font-weight: 700;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.export-submit {
  min-width: 110px;
}

@media (max-width: 860px) {
  .dataset-grid,
  .selection-grid,
  .field-grid,
  .date-grid {
    grid-template-columns: 1fr;
  }

  .field-wide {
    grid-column: auto;
  }
}

@media (max-width: 720px) {
  .filter-card-head {
    align-items: flex-start;
    flex-direction: column;
    gap: 4px;
  }

  .actions {
    justify-content: stretch;
    flex-direction: column;
  }

  .outline-btn,
  .primary-btn {
    width: 100%;
  }
}
</style>
