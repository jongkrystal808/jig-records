<script setup lang="ts">
import { computed, ref } from "vue";

import { api } from "@/api";
import { pushToast } from "@/toastState";

type ReportType = "summary" | "detail";
type ExportScopeMode = "all" | "custom";

let exportPanelInstanceCount = 0;

const props = defineProps<{
  customerId: number | undefined;
}>();

const emit = defineEmits<{
  close: [];
}>();

const instanceId = ++exportPanelInstanceCount;
const reportTypeGroupName = `inventory-export-report-type-${instanceId}`;
const scopeModeGroupName = `inventory-export-scope-mode-${instanceId}`;

const exporting = ref(false);
const reportType = ref<ReportType>("summary");
const scopeMode = ref<ExportScopeMode>("all");
const dateFrom = ref("");
const dateTo = ref("");
const transactionNo = ref("");
const fixtureCode = ref("");
const identifier = ref("");

const selectedColumns = computed(() =>
  reportType.value === "summary"
    ? ["治具編號", "收料數", "退料數", "總數"]
    : ["日期", "單號", "治具編號", "datecode/編號", "數量"]
);
const usingCustomScope = computed(() => scopeMode.value === "custom");

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

async function exportReport(): Promise<void> {
  if (!props.customerId) {
    pushToast("請先選擇客戶後再匯出。", "warning");
    return;
  }
  if (usingCustomScope.value && dateFrom.value && dateTo.value && dateFrom.value > dateTo.value) {
    pushToast("開始日期不能晚於結束日期。", "warning");
    return;
  }

  exporting.value = true;
  try {
    const response = await api.exportTransactionReport({
      customer_id: props.customerId,
      report_type: reportType.value,
      file_format: "xlsx",
      transaction_type: undefined,
      date_from: usingCustomScope.value ? normalizeOptional(dateFrom.value) : undefined,
      date_to: usingCustomScope.value ? normalizeOptional(dateTo.value) : undefined,
      transaction_no: usingCustomScope.value ? normalizeOptional(transactionNo.value) : undefined,
      fixture_code: usingCustomScope.value ? normalizeOptional(fixtureCode.value) : undefined,
      identifier: usingCustomScope.value ? normalizeOptional(identifier.value) : undefined
    });
    const fallbackName = `transaction-${reportType.value}.xlsx`;
    downloadBlob(response.blob, response.filename ?? fallbackName);
    pushToast("收退料匯出完成。", "success");
    emit("close");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "匯出失敗", "error");
  } finally {
    exporting.value = false;
  }
}
</script>

<template>
  <section class="export-panel">
    <header class="export-head">
      <div class="title-row">
        <h2>收退料匯出</h2>
        <span class="export-pill">Export</span>
      </div>
      <button class="outline-btn" type="button" @click="emit('close')">關閉</button>
    </header>

    <div class="selection-grid">
      <fieldset class="selection-block selection-fieldset">
        <legend>匯出內容</legend>
        <label class="radio-row" :class="{ selected: reportType === 'summary' }">
          <input v-model="reportType" type="radio" :name="reportTypeGroupName" value="summary" />
          <span class="radio-indicator" aria-hidden="true"></span>
          <span>匯出摘要</span>
        </label>
        <label class="radio-row" :class="{ selected: reportType === 'detail' }">
          <input v-model="reportType" type="radio" :name="reportTypeGroupName" value="detail" />
          <span class="radio-indicator" aria-hidden="true"></span>
          <span>匯出明細</span>
        </label>
      </fieldset>

      <fieldset class="selection-block selection-fieldset">
        <legend>匯出範圍</legend>
        <label class="radio-row" :class="{ selected: scopeMode === 'all' }">
          <input v-model="scopeMode" type="radio" :name="scopeModeGroupName" value="all" />
          <span class="radio-indicator" aria-hidden="true"></span>
          <span>全部</span>
        </label>
        <label class="radio-row" :class="{ selected: scopeMode === 'custom' }">
          <input v-model="scopeMode" type="radio" :name="scopeModeGroupName" value="custom" />
          <span class="radio-indicator" aria-hidden="true"></span>
          <span>自定義</span>
        </label>
      </fieldset>
    </div>

    <section v-if="usingCustomScope" class="filter-card">
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
          <span>單號</span>
          <input v-model="transactionNo" placeholder="25123456" spellcheck="false" />
        </label>
        <label class="field">
          <span>datecode/編號 / 舊 Datecode</span>
          <input v-model="identifier" placeholder="例如 0001 或 2024W12" spellcheck="false" />
        </label>
        <label class="field">
          <span>治具編號</span>
          <input v-model="fixtureCode" placeholder="C-00001" spellcheck="false" />
        </label>
      </div>
    </section>

    <div class="column-note">
      <span>匯出欄位</span>
      <div class="preview-columns">
        <span v-for="column in selectedColumns" :key="column" class="preview-chip">{{ column }}</span>
      </div>
    </div>

    <div class="actions">
      <button class="outline-btn" type="button" :disabled="exporting" @click="emit('close')">取消</button>
      <button class="primary-btn export-submit" type="button" :disabled="exporting" @click="exportReport">
        {{ exporting ? "匯出中..." : "確定匯出" }}
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

.radio-row span {
  line-height: 1.4;
}

.filter-card {
  display: grid;
  gap: 12px;
  padding: 14px;
  border: 1px solid color-mix(in srgb, var(--blue) 18%, var(--line));
  border-radius: 16px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--blue-soft) 56%, white) 0%, #ffffff 100%);
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.date-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.field {
  display: grid;
  gap: 6px;
}

.field input {
  width: 100%;
  border: 1px solid var(--line-strong);
  border-radius: 14px;
  padding: 10px 12px;
  background: #fff;
  color: var(--text);
}

.field input:focus {
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

@media (max-width: 720px) {
  .selection-grid,
  .field-grid,
  .date-grid {
    grid-template-columns: 1fr;
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
