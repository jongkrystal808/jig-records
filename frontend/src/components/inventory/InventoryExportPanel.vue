<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";

import { api } from "@/api";
import { pushToast } from "@/toastState";
import { formatLocalDateKey } from "@/utils/date";

type ReportType = "summary" | "detail";
type FileFormat = "xlsx" | "txt";
type TransactionScope = "all" | "receipt" | "return";

const props = defineProps<{
  customerId: number | undefined;
}>();

const exporting = ref(false);
const reportType = ref<ReportType>("summary");
const fileFormat = ref<FileFormat>("xlsx");
const transactionScope = ref<TransactionScope>("all");
const dateFrom = ref(formatLocalDateKey(new Date()));
const dateTo = ref(formatLocalDateKey(new Date()));
const transactionNo = ref("");
const fixtureCode = ref("");
const identifier = ref("");
const previewLoading = ref(false);
const preview = ref<{ raw_item_count: number; export_row_count: number } | null>(null);
let previewTimer: ReturnType<typeof setTimeout> | null = null;

const previewColumns = computed(() =>
  reportType.value === "summary"
    ? ["治具編號", "收料數", "退料數", "總數"]
    : ["治具編號", "識別碼", "收料數", "退料數", "總數"]
);

const dateShortcuts = computed(() => {
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);
  const last7Start = new Date();
  last7Start.setDate(today.getDate() - 6);
  const monthStart = new Date(today.getFullYear(), today.getMonth(), 1);
  return [
    { key: "today", label: "今天", from: formatLocalDateKey(today), to: formatLocalDateKey(today) },
    { key: "yesterday", label: "昨天", from: formatLocalDateKey(yesterday), to: formatLocalDateKey(yesterday) },
    { key: "last7", label: "近 7 天", from: formatLocalDateKey(last7Start), to: formatLocalDateKey(today) },
    { key: "month", label: "本月", from: formatLocalDateKey(monthStart), to: formatLocalDateKey(today) }
  ];
});

function normalizeOptional(value: string): string | undefined {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

function applyDateShortcut(from: string, to: string): void {
  dateFrom.value = from;
  dateTo.value = to;
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
  if (dateFrom.value && dateTo.value && dateFrom.value > dateTo.value) {
    pushToast("開始日期不能晚於結束日期。", "warning");
    return;
  }
  exporting.value = true;
  try {
    const response = await api.exportTransactionReport({
      customer_id: props.customerId,
      report_type: reportType.value,
      file_format: fileFormat.value,
      transaction_type: transactionScope.value === "all" ? undefined : transactionScope.value,
      date_from: normalizeOptional(dateFrom.value),
      date_to: normalizeOptional(dateTo.value),
      transaction_no: normalizeOptional(transactionNo.value),
      fixture_code: normalizeOptional(fixtureCode.value),
      identifier: normalizeOptional(identifier.value)
    });
    const fallbackName = `transaction-${reportType.value}.${fileFormat.value}`;
    downloadBlob(response.blob, response.filename ?? fallbackName);
    pushToast("收退料匯出完成。", "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "匯出失敗", "error");
  } finally {
    exporting.value = false;
  }
}

async function loadPreview(): Promise<void> {
  if (!props.customerId) {
    preview.value = null;
    return;
  }
  if (dateFrom.value && dateTo.value && dateFrom.value > dateTo.value) {
    preview.value = null;
    return;
  }
  previewLoading.value = true;
  try {
    preview.value = await api.previewTransactionReportExport({
      customer_id: props.customerId,
      report_type: reportType.value,
      transaction_type: transactionScope.value === "all" ? undefined : transactionScope.value,
      date_from: normalizeOptional(dateFrom.value),
      date_to: normalizeOptional(dateTo.value),
      transaction_no: normalizeOptional(transactionNo.value),
      fixture_code: normalizeOptional(fixtureCode.value),
      identifier: normalizeOptional(identifier.value)
    });
  } catch {
    preview.value = null;
  } finally {
    previewLoading.value = false;
  }
}

watch([() => props.customerId, reportType, transactionScope, dateFrom, dateTo, transactionNo, fixtureCode, identifier], () => {
  if (previewTimer) {
    clearTimeout(previewTimer);
  }
  previewTimer = setTimeout(() => {
    void loadPreview();
  }, 250);
}, { immediate: true });

onBeforeUnmount(() => {
  if (previewTimer) {
    clearTimeout(previewTimer);
  }
});
</script>

<template>
  <section class="export-panel">
    <div class="export-grid">
      <label class="field">
        <span>報表類型</span>
        <select v-model="reportType">
          <option value="summary">摘要匯出</option>
          <option value="detail">明細匯出</option>
        </select>
      </label>

      <label class="field">
        <span>檔案格式</span>
        <select v-model="fileFormat">
          <option value="xlsx">Excel .xlsx</option>
          <option value="txt">文字 .txt</option>
        </select>
      </label>

      <label class="field">
        <span>收退料類型</span>
        <select v-model="transactionScope">
          <option value="all">全部</option>
          <option value="receipt">只收料</option>
          <option value="return">只退料</option>
        </select>
      </label>

      <label class="field">
        <span>開始日期</span>
        <input v-model="dateFrom" type="date" />
      </label>

      <label class="field">
        <span>結束日期</span>
        <input v-model="dateTo" type="date" />
      </label>

      <div class="field field-span-2">
        <span>快捷日期</span>
        <div class="shortcut-row">
          <button
            v-for="shortcut in dateShortcuts"
            :key="shortcut.key"
            class="shortcut-btn"
            type="button"
            @click="applyDateShortcut(shortcut.from, shortcut.to)"
          >
            {{ shortcut.label }}
          </button>
        </div>
      </div>

      <label class="field">
        <span>單號</span>
        <input v-model="transactionNo" placeholder="例如 RCV-20260701-000001" spellcheck="false" />
      </label>

      <label class="field">
        <span>治具編號</span>
        <input v-model="fixtureCode" placeholder="例如 ALG-067" spellcheck="false" />
      </label>

      <label class="field">
        <span>識別碼</span>
        <input v-model="identifier" placeholder="例如 001" spellcheck="false" />
      </label>
    </div>

    <div class="preview-card">
      <strong>匯出欄位</strong>
      <div class="preview-columns">
        <span v-for="column in previewColumns" :key="column" class="preview-chip">{{ column }}</span>
      </div>
      <small>支援日期範圍匯出；總數目前依淨額計算：收料數 - 退料數。</small>
      <div class="preview-stats">
        <span v-if="previewLoading">預估筆數計算中...</span>
        <template v-else-if="preview">
          <span>原始明細筆數 {{ preview.raw_item_count }}</span>
          <span>匯出後筆數 {{ preview.export_row_count }}</span>
        </template>
        <span v-else>目前無可預估資料</span>
      </div>
    </div>

    <div class="actions">
      <button class="primary-btn export-submit" type="button" :disabled="exporting" @click="exportReport">
        {{ exporting ? "匯出中..." : "開始匯出" }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.export-panel {
  display: grid;
  gap: 16px;
}

.export-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.field {
  display: grid;
  gap: 6px;
}

.field span {
  color: #56657f;
  font-size: 12px;
  font-weight: 700;
}

.field-span-2 {
  grid-column: 1 / -1;
}

.field input,
.field select {
  width: 100%;
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  padding: 8px 10px;
  background: #fff;
  color: var(--text);
}

.preview-card {
  display: grid;
  gap: 10px;
  padding: 14px;
  border: 1px solid #dce5f3;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(245, 249, 255, 0.96) 100%);
}

.preview-card strong {
  color: #22314a;
}

.preview-card small {
  color: #5d6d89;
  font-size: 12px;
}

.preview-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preview-stats span {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 4px 10px;
  border: 1px solid #d7e2f5;
  border-radius: 999px;
  background: #fff;
  color: #35527d;
  font-size: 12px;
  font-weight: 700;
}

.preview-columns {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.shortcut-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.shortcut-btn {
  border: 1px solid #d7e2f5;
  border-radius: 999px;
  background: #f7faff;
  color: #35527d;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.preview-chip {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 4px 10px;
  border: 1px solid #d7e2f5;
  border-radius: 999px;
  background: #f7faff;
  color: #35527d;
  font-size: 12px;
  font-weight: 700;
}

.actions {
  display: flex;
  justify-content: flex-end;
}

.primary-btn {
  border: 1px solid #2f6ee5;
  border-radius: 10px;
  background: linear-gradient(180deg, #4b89ff 0%, #2f6ee5 100%);
  color: #fff;
  padding: 8px 14px;
  min-height: 40px;
  font-weight: 700;
  cursor: pointer;
}

.primary-btn:disabled {
  opacity: 0.7;
  cursor: progress;
}

.export-submit {
  min-width: 180px;
}

@media (max-width: 720px) {
  .export-grid {
    grid-template-columns: 1fr;
  }

  .actions {
    justify-content: stretch;
  }

  .export-submit {
    width: 100%;
  }
}
</style>
