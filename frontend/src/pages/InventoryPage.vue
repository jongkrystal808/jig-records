<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { api } from "@/api";
import { authSession, selectedCustomerId } from "@/appState";
import { pushToast } from "@/toastState";
import type { Fixture, MaterialTransaction, StockSummary, TransactionQueryFilters } from "@/types";
import { fallbackText, ownershipLabel, stockStatusLabel } from "@/utils/display";
import UiStatusPill from "@/components/UiStatusPill.vue";
import { formatLocalDateKey as formatDateKey } from "@/utils/date";

const route = useRoute();

const mode = ref<"receipt" | "return">("receipt");
const fixtures = ref<Fixture[]>([]);
const stockRows = ref<StockSummary[]>([]);
const alerts = ref<Array<{ fixture_id: number; fixture_code: string; fixture_name: string; stock_qty: number; min_stock_qty: number; stock_status: "low_stock" | "out_of_stock" }>>([]);
const transactions = ref<MaterialTransaction[]>([]);
const overviewTransactions = ref<MaterialTransaction[]>([]);
const saving = ref(false);
const overviewLoading = ref(false);
const showBatchPanel = ref(false);
const batchPasteText = ref("");
const batchTransactionNo = ref("");
const batchNote = ref("");

type BatchImportRow = {
  lineNo: number;
  raw: string;
  rawCode: string;
  inputFixtureCode: string;
  inputToken: string;
  resolvedFixtureId: number | null;
  resolvedFixtureCode: string;
  suggestedFixtureId: number | null;
  suggestedFixtureCode: string;
  quantity: number;
  status: "ready" | "needs-confirm" | "needs-add" | "skipped" | "error";
  message: string | null;
  note: string | null;
};

const batchImportRows = ref<BatchImportRow[]>([]);

const overviewFilters = ref({
  transaction_type: "" as "" | "receipt" | "return",
  date_from: "",
  date_to: "",
  fixture_code: "",
  transaction_no: "",
  tracking_code: "",
  created_by: ""
});

const pageMode = computed(() => (route.path.endsWith("/overview") ? "overview" : "operation"));
const today = computed(() => formatDateKey(new Date()));
const batchReadyRows = computed(() => batchImportRows.value.filter((row) => row.status === "ready"));
const batchPendingRows = computed(() => batchImportRows.value.filter((row) => row.status === "needs-confirm" || row.status === "needs-add"));
const batchErrorRows = computed(() => batchImportRows.value.filter((row) => row.status === "error"));
const batchImportCount = computed(() => batchReadyRows.value.length);
const batchPendingCount = computed(() => batchPendingRows.value.length);
const batchImportErrorCount = computed(() => batchErrorRows.value.length);
const batchImportLabel = computed(() => (mode.value === "receipt" ? "批次收料" : "批次退料"));
const batchCanSubmit = computed(
  () =>
    batchImportCount.value > 0 &&
    batchPendingCount.value === 0 &&
    batchImportErrorCount.value === 0 &&
    batchTransactionNo.value.trim().length > 0
);

const recentRows = computed(() =>
  transactions.value
    .filter((tx) => tx.transaction_type === mode.value)
    .flatMap((tx) =>
      tx.items.map((item, index) => ({
        id: `${tx.id}-${index}`,
        transaction_no: tx.transaction_no,
        fixture_code: item.fixture_code,
        identifier: item.identifier,
        quantity: item.quantity
      }))
    )
    .slice(0, 6)
);

const overviewRows = computed(() =>
  overviewTransactions.value.flatMap((tx) =>
    tx.items.map((item, index) => ({
      id: `${tx.id}-${index}`,
      transaction_type: tx.transaction_type,
      transaction_no: tx.transaction_no,
      occurred_at: tx.occurred_at,
      created_by: tx.created_by,
      fixture_code: item.fixture_code,
      fixture_name: item.fixture_name,
      ownership_type: item.ownership_type,
      identifier: item.identifier,
      quantity: item.quantity,
      note: item.note || tx.note || ""
    }))
  )
);

const totalStockQty = computed(() => stockRows.value.reduce((sum, row) => sum + row.stock_qty, 0));
const outOfStockCount = computed(() => stockRows.value.filter((row) => row.stock_status === "out_of_stock").length);
const activeFixtureCount = computed(() => stockRows.value.filter((row) => row.stock_qty > 0).length);
const activeStockRows = computed(() => {
  const activeFixtureIds = new Set(fixtures.value.filter((row) => row.is_active).map((row) => row.id));
  return stockRows.value.filter((row) => activeFixtureIds.has(row.fixture_id));
});

const inventorySummaryCards = computed(() => [
  { label: "治具總數", value: totalStockQty.value, tone: "normal" },
  { label: "有庫存治具", value: activeFixtureCount.value, tone: "normal" },
  { label: "今日收料", value: todayReceiptQty.value, tone: "success" },
  { label: "今日退料", value: todayReturnQty.value, tone: "danger" },
  { label: "低水位", value: alerts.value.length, tone: "warn" },
  { label: "缺料治具", value: outOfStockCount.value, tone: "danger" }
]);

function stockWaterLevelPercent(row: StockSummary): number {
  const minStock = row.min_stock_qty ?? 0;
  if (minStock <= 0) {
    return row.stock_qty > 0 ? 100 : 0;
  }
  return Math.max(0, Math.min(100, Math.round((row.stock_qty / minStock) * 100)));
}

const todayReceiptQty = computed(() =>
  overviewTransactions.value
    .filter((tx) => tx.transaction_type === "receipt" && formatDateKey(new Date(tx.occurred_at)) === today.value)
    .reduce((sum, tx) => sum + tx.items.reduce((itemSum, item) => itemSum + item.quantity, 0), 0)
);

const todayReturnQty = computed(() =>
  overviewTransactions.value
    .filter((tx) => tx.transaction_type === "return" && formatDateKey(new Date(tx.occurred_at)) === today.value)
    .reduce((sum, tx) => sum + tx.items.reduce((itemSum, item) => itemSum + item.quantity, 0), 0)
);

function normalizeBatchText(value: string): string {
  return value.replace(/\u00a0/g, " ").trim();
}

function splitBatchCells(line: string): string[] {
  const trimmed = normalizeBatchText(line);
  if (!trimmed) return [];

  if (trimmed.includes("\t")) {
    return trimmed.split("\t").map(normalizeBatchText).filter(Boolean);
  }

  if (trimmed.includes("|")) {
    return trimmed.split("|").map(normalizeBatchText).filter(Boolean);
  }

  if (/[;,，；]/.test(trimmed)) {
    return trimmed.split(/[;,，；]/).map(normalizeBatchText).filter(Boolean);
  }

  return trimmed.split(/\s{2,}/).map(normalizeBatchText).filter(Boolean);
}

function extractInlineBatchGroups(cells: string[]): Array<{ codeLine: string; qtyLine: string }> {
  const groups: Array<{ codeLine: string; qtyLine: string }> = [];
  const codeCells: string[] = [];

  for (const cell of cells) {
    if (/^\d+$/.test(cell) && codeCells.length > 0) {
      groups.push({
        codeLine: codeCells.join("\t"),
        qtyLine: cell
      });
      codeCells.length = 0;
      continue;
    }
    codeCells.push(cell);
  }

  return codeCells.length === 0 ? groups : [];
}

function isHeaderLikeLine(line: string): boolean {
  const normalized = normalizeBatchText(line).toLowerCase();
  if (!normalized) return true;
  const hasHeaderWord = /(治具|識別碼|datecode|流水號|序號|數量|quantity|qty)/i.test(normalized);
  const looksLikeCode = /^[a-z]\-\d/i.test(normalized) || /^\d+$/.test(normalized);
  return hasHeaderWord && !looksLikeCode;
}

function splitCombinedFixtureText(value: string): { fixtureCode: string; token: string } {
  const trimmed = normalizeBatchText(value);
  const lastDash = trimmed.lastIndexOf("-");
  if (lastDash <= 0 || lastDash >= trimmed.length - 1) {
    return { fixtureCode: trimmed, token: "" };
  }
  return {
    fixtureCode: trimmed.slice(0, lastDash).trim(),
    token: trimmed.slice(lastDash + 1).trim()
  };
}

function normalizeFixtureCode(value: string): string {
  return normalizeBatchText(value).toUpperCase();
}

function commonPrefixLength(left: string, right: string): number {
  const maxLength = Math.min(left.length, right.length);
  let index = 0;
  while (index < maxLength && left[index] === right[index]) {
    index += 1;
  }
  return index;
}

function levenshteinDistance(left: string, right: string): number {
  const a = left.toUpperCase();
  const b = right.toUpperCase();
  const previous = Array.from({ length: b.length + 1 }, (_, index) => index);
  for (let i = 1; i <= a.length; i += 1) {
    const current = [i];
    for (let j = 1; j <= b.length; j += 1) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      current[j] = Math.min(current[j - 1] + 1, previous[j] + 1, previous[j - 1] + cost);
    }
    previous.splice(0, previous.length, ...current);
  }
  return previous[b.length] ?? 0;
}

function findFixtureByCode(code: string): Fixture | undefined {
  const target = normalizeFixtureCode(code);
  return fixtures.value.find((row) => normalizeFixtureCode(row.code) === target);
}

function findFixtureById(fixtureId: number): Fixture | undefined {
  return fixtures.value.find((row) => row.id === fixtureId);
}

function findSimilarFixture(code: string): Fixture | undefined {
  const target = normalizeFixtureCode(code);
  let best: { fixture: Fixture; distance: number; prefix: number } | null = null;

  for (const fixture of fixtures.value) {
    const candidate = normalizeFixtureCode(fixture.code);
    const prefix = commonPrefixLength(target, candidate);
    const distance = levenshteinDistance(target, candidate);
    if (prefix < 4 && distance > 2) continue;
    if (
      best === null ||
      distance < best.distance ||
      (distance === best.distance && prefix > best.prefix) ||
      (distance === best.distance && prefix === best.prefix && candidate.length < normalizeFixtureCode(best.fixture.code).length)
    ) {
      best = { fixture, distance, prefix };
    }
  }

  return best && best.distance <= 2 ? best.fixture : undefined;
}

function makeBatchError(lineNo: number, raw: string, message: string): BatchImportRow {
  return {
    lineNo,
    raw,
    rawCode: "",
    inputFixtureCode: "",
    inputToken: "",
    resolvedFixtureId: null,
    resolvedFixtureCode: "",
    suggestedFixtureId: null,
    suggestedFixtureCode: "",
    quantity: 0,
    status: "error",
    message,
    note: null
  };
}

function buildBatchRow(lineNo: number, rawCodeLine: string, quantityLine: string): BatchImportRow {
  const raw = `${rawCodeLine}\n${quantityLine}`.trim();
  const cells = splitBatchCells(rawCodeLine);
  const qtyCells = splitBatchCells(quantityLine);
  const qtyText = qtyCells[0] ?? "";

  if (!rawCodeLine.trim()) {
    return makeBatchError(lineNo, raw, "缺少治具編號");
  }

  if (isHeaderLikeLine(rawCodeLine) || isHeaderLikeLine(quantityLine)) {
    return makeBatchError(lineNo, raw, "標題列");
  }

  let codeText = normalizeBatchText(rawCodeLine);
  if (cells.length >= 2 && !cells.every((cell) => cell === codeText)) {
    if (cells.length === 2) {
      codeText = cells[0];
    } else if (cells.length >= 3 && /^\d+$/.test(cells[cells.length - 1])) {
      codeText = `${cells[0]}-${cells[1]}`;
    }
  }

  if (!qtyText || !/^\d+$/.test(qtyText)) {
    return makeBatchError(lineNo, raw, "數量必須是大於 0 的整數");
  }

  const quantity = Number.parseInt(qtyText, 10);
  if (!Number.isFinite(quantity) || quantity <= 0) {
    return makeBatchError(lineNo, raw, "數量必須是大於 0 的整數");
  }

  const splitCode = splitCombinedFixtureText(codeText);
  const exactFixture = findFixtureByCode(splitCode.fixtureCode);
  if (exactFixture) {
    if (!splitCode.token) {
      return {
        lineNo,
        raw,
        rawCode: codeText,
        inputFixtureCode: splitCode.fixtureCode,
        inputToken: splitCode.token,
        resolvedFixtureId: exactFixture.id,
        resolvedFixtureCode: exactFixture.code,
        suggestedFixtureId: null,
        suggestedFixtureCode: "",
        quantity,
        status: "error",
        message: "缺少識別碼",
        note: null
      };
    }

    return {
      lineNo,
      raw,
      rawCode: codeText,
      inputFixtureCode: splitCode.fixtureCode,
      inputToken: splitCode.token,
      resolvedFixtureId: exactFixture.id,
      resolvedFixtureCode: exactFixture.code,
      suggestedFixtureId: null,
      suggestedFixtureCode: "",
      quantity,
      status: "ready",
      message: null,
      note: "已對應現有治具"
    };
  }

  const similarFixture = findSimilarFixture(splitCode.fixtureCode);
  if (similarFixture) {
    return {
      lineNo,
      raw,
      rawCode: codeText,
      inputFixtureCode: splitCode.fixtureCode,
      inputToken: splitCode.token,
      resolvedFixtureId: null,
      resolvedFixtureCode: "",
      suggestedFixtureId: similarFixture.id,
      suggestedFixtureCode: similarFixture.code,
      quantity,
      status: "needs-confirm",
      message: `可能是 ${similarFixture.code}，請先確認是否為同一個治具`,
      note: null
    };
  }

  return {
    lineNo,
    raw,
    rawCode: codeText,
    inputFixtureCode: splitCode.fixtureCode,
    inputToken: splitCode.token,
    resolvedFixtureId: null,
    resolvedFixtureCode: "",
    suggestedFixtureId: null,
    suggestedFixtureCode: "",
    quantity,
    status: "needs-add",
    message: `找不到治具 ${splitCode.fixtureCode}，可新增或跳過`,
    note: null
  };
}

function parseBatchImportText(text: string): BatchImportRow[] {
  const lines = text
    .replace(/\r/g, "")
    .split("\n")
    .map((line) => normalizeBatchText(line))
    .filter(Boolean)
    .filter((line) => !isHeaderLikeLine(line));

  const rows: BatchImportRow[] = [];
  for (let index = 0; index < lines.length; ) {
    const current = lines[index];
    const currentCells = splitBatchCells(current);
    const inlineGroups = extractInlineBatchGroups(currentCells);

    if (inlineGroups.length > 0) {
      for (const group of inlineGroups) {
        rows.push(buildBatchRow(rows.length + 1, group.codeLine, group.qtyLine));
      }
      index += 1;
      continue;
    }

    const qtyLine = lines[index + 1];
    if (!qtyLine) {
      rows.push(makeBatchError(rows.length + 1, current, "缺少數量列"));
      break;
    }
    rows.push(buildBatchRow(rows.length + 1, current, qtyLine));
    index += 2;
  }

  return rows.filter((row) => row.message !== "標題列");
}

function refreshBatchImportPreview(): void {
  batchImportRows.value = parseBatchImportText(batchPasteText.value);
}

function clearBatchImport(): void {
  batchPasteText.value = "";
  batchTransactionNo.value = "";
  batchNote.value = "";
  batchImportRows.value = [];
}

function handleBatchPaste(event: ClipboardEvent): void {
  const pastedText = event.clipboardData?.getData("text/plain") ?? "";
  if (!pastedText) return;
  event.preventDefault();
  batchPasteText.value = pastedText;
  refreshBatchImportPreview();
}

function setBatchRowReady(row: BatchImportRow, fixture: Fixture, message: string): void {
  row.resolvedFixtureId = fixture.id;
  row.resolvedFixtureCode = fixture.code;
  row.suggestedFixtureId = null;
  row.suggestedFixtureCode = "";
  row.status = "ready";
  row.message = null;
  row.note = message;
}

function skipBatchRow(row: BatchImportRow): void {
  row.status = "skipped";
  row.message = "已跳過";
  row.note = null;
  row.resolvedFixtureId = null;
  row.resolvedFixtureCode = "";
}

async function createFixtureForBatchRow(row: BatchImportRow): Promise<void> {
  if (!selectedCustomerId.value) {
    pushToast("請先在側邊欄選擇客戶。", "warning");
    return;
  }
  if (!row.inputFixtureCode) return;

  const code = row.inputFixtureCode;
  try {
    const created = await api.createFixture({
      customer_id: selectedCustomerId.value,
      code,
      name: code,
      storage_location: null,
      min_stock_qty: 0,
      description: "由收退料批次匯入建立"
    });
    fixtures.value = [...fixtures.value.filter((fixture) => fixture.id !== created.id), created];
    setBatchRowReady(row, created, "已新增治具並加入匯入清單");
    pushToast(`已新增治具：${created.code}`, "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "新增治具失敗", "error");
  }
}

function acceptSimilarFixture(row: BatchImportRow): void {
  const fixture = row.suggestedFixtureId ? findFixtureById(row.suggestedFixtureId) : undefined;
  if (!fixture) {
    row.status = "needs-add";
    row.message = "找不到建議治具，請選擇新增或跳過";
    row.suggestedFixtureId = null;
    row.suggestedFixtureCode = "";
    return;
  }
  setBatchRowReady(row, fixture, `已替換為 ${fixture.code}`);
}

function rejectSimilarFixture(row: BatchImportRow): void {
  row.status = "needs-add";
  row.message = `若不是 ${row.suggestedFixtureCode}，可直接新增或跳過`;
}

async function addBatchRowFixture(row: BatchImportRow): Promise<void> {
  await createFixtureForBatchRow(row);
  if (row.status === "ready") {
    return;
  }
  row.status = "needs-add";
}

function downloadCsv(filename: string, content: string): void {
  const blob = new Blob([content], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function escapeCsvCell(value: string | number | null | undefined): string {
  const text = value === null || value === undefined ? "" : String(value);
  if (/[",\n\r]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

function renderCsv(rows: Array<Record<string, string | number | null | undefined>>, headers: string[]): string {
  const lines = [headers.join(",")];
  for (const row of rows) {
    lines.push(headers.map((header) => escapeCsvCell(row[header])).join(","));
  }
  return lines.join("\n");
}

async function loadData(): Promise<void> {
  const customerId = selectedCustomerId.value ?? undefined;
  try {
    const [fixtureRows, stock, alertRows, tx] = await Promise.all([
      api.listFixtures(customerId),
      api.listStock(customerId),
      api.listAlerts(customerId),
      api.listTransactions(40, customerId)
    ]);
    fixtures.value = fixtureRows;
    stockRows.value = stock;
    alerts.value = alertRows;
    transactions.value = tx;
    if (batchPasteText.value.trim()) {
      refreshBatchImportPreview();
    }
    if (pageMode.value === "overview") {
      await loadOverview();
    }
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "載入收退料資料失敗", "error");
  }
}

function buildOverviewFilters(): TransactionQueryFilters {
  return {
    transaction_type: overviewFilters.value.transaction_type || undefined,
    date_from: overviewFilters.value.date_from || undefined,
    date_to: overviewFilters.value.date_to || undefined,
    fixture_code: overviewFilters.value.fixture_code.trim() || undefined,
    transaction_no: overviewFilters.value.transaction_no.trim() || undefined,
    identifier: overviewFilters.value.tracking_code.trim() || undefined,
    created_by: overviewFilters.value.created_by.trim() || undefined
  };
}

async function loadOverview(): Promise<void> {
  overviewLoading.value = true;
  try {
    overviewTransactions.value = await api.listTransactions(200, selectedCustomerId.value ?? undefined, buildOverviewFilters());
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "載入收退料總檢視失敗", "error");
  } finally {
    overviewLoading.value = false;
  }
}

async function searchOverview(): Promise<void> {
  if (!selectedCustomerId.value) {
    pushToast("請先在側邊欄選擇客戶。", "warning");
    return;
  }
  await loadOverview();
}

async function resetOverviewFilters(): Promise<void> {
  overviewFilters.value = {
    transaction_type: "",
    date_from: "",
    date_to: "",
    fixture_code: "",
    transaction_no: "",
    tracking_code: "",
    created_by: ""
  };
  await loadOverview();
}

async function exportOverviewCsv(): Promise<void> {
  if (!selectedCustomerId.value) {
    pushToast("請先在側邊欄選擇客戶。", "warning");
    return;
  }
  try {
    const customerId = selectedCustomerId.value ?? undefined;
    downloadCsv("transactions.csv", await api.exportTransactionsCsv(5000, customerId, buildOverviewFilters()));
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "匯出失敗", "error");
  }
}

async function submitBatchImport(): Promise<void> {
  if (!selectedCustomerId.value) {
    pushToast("請先在側邊欄選擇客戶。", "warning");
    return;
  }
  if (batchImportRows.value.length === 0) {
    pushToast("請先貼上可匯入的表格資料。", "warning");
    return;
  }
  const transactionNo = batchTransactionNo.value.trim();
  const transactionNote = batchNote.value.trim();
  if (!transactionNo) {
    pushToast("請先填寫這批的單號。", "warning");
    return;
  }
  if (batchPendingCount.value > 0) {
    pushToast("還有待確認的治具列，請先完成同治具 / 新增 / 跳過。", "warning");
    return;
  }
  if (batchErrorRows.value.length > 0) {
    pushToast("表格中有錯誤列，請先修正後再匯入。", "warning");
    return;
  }

  const items = batchReadyRows.value.map((row) => ({
    fixture_id: row.resolvedFixtureId as number,
    ownership_type: "customer_supplied" as const,
    identifier: row.inputToken,
    quantity: row.quantity,
    note: undefined
  }));

  saving.value = true;
  const payload = {
    customer_id: selectedCustomerId.value,
    created_by: authSession.value?.display_name ?? "訪客",
    transaction_no: transactionNo,
    note: transactionNote || undefined,
    items
  };

  try {
    if (mode.value === "receipt") {
      await api.createReceipt(payload);
    } else {
      await api.createReturn(payload);
    }
    clearBatchImport();
    await loadData();
    pushToast(`${batchImportLabel.value}完成，共 ${items.length} 筆。`, "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "批次送出失敗", "error");
  } finally {
    saving.value = false;
  }
}

onMounted(async () => {
  await loadData();
});

watch(selectedCustomerId, async () => {
  await loadData();
});

watch(pageMode, async (value) => {
  if (value === "overview" && overviewTransactions.value.length === 0) {
    await loadOverview();
  }
});

watch(batchPasteText, () => {
  refreshBatchImportPreview();
});
</script>

<template>
  <div class="inventory-shell">
    <section v-if="pageMode === 'operation'" class="inventory-board">
      <div class="inventory-summary-row">
        <article v-for="card in inventorySummaryCards" :key="card.label" class="summary-chip" :class="card.tone">
          <span>{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
        </article>
      </div>

      <article class="panel op-panel">
        <div class="panel-head">
          <button class="toggle-btn batch-entry-btn" type="button" @click="showBatchPanel = true">
            批次貼上匯入
          </button>
          <div class="panel-actions">
            <div class="segmented-control" role="tablist" aria-label="收退料切換">
              <button class="segmented-btn" :class="{ active: mode === 'receipt' }" type="button" @click="mode = 'receipt'">
                收料
              </button>
              <button class="segmented-btn" :class="{ active: mode === 'return' }" type="button" @click="mode = 'return'">
                退料
              </button>
            </div>
          </div>
        </div>

        <div class="recent-block">
          <div class="sub-head">
            <h3>{{ mode === "receipt" ? "最近收料" : "最近退料" }}</h3>
            <span>{{ recentRows.length }} 筆</span>
          </div>
          <table class="grid-table compact-table">
            <thead>
              <tr>
                <th>治具</th>
                <th>識別碼</th>
                <th>數量</th>
                <th>單號</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in recentRows" :key="`tx-${row.id}`">
                <td>{{ row.fixture_code || "-" }}</td>
                <td>{{ row.identifier || "-" }}</td>
                <td>{{ row.quantity }}</td>
                <td>{{ row.transaction_no }}</td>
              </tr>
              <tr v-if="recentRows.length === 0">
                <td colspan="4" class="empty-cell">尚無資料</td>
              </tr>
            </tbody>
          </table>
        </div>

      </article>

      <article class="panel stock-panel">
        <div class="sub-head">
          <h2>現有治具庫存</h2>
          <span>{{ activeStockRows.length }} 筆</span>
        </div>
        <div class="panel-table-scroll">
          <table class="grid-table">
            <thead>
              <tr>
                <th>治具編號 + 流水號</th>
                <th>數量 (pcs)</th>
                <th>水位</th>
                <th>狀態</th>
              </tr>
            </thead>
              <tbody>
                <tr v-for="row in activeStockRows" :key="row.fixture_id">
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
                <tr v-if="activeStockRows.length === 0">
                  <td colspan="4" class="empty-cell">目前沒有庫存資料</td>
                </tr>
              </tbody>
            </table>
        </div>
      </article>

      <div class="side-stack">
        <article class="panel alert-panel">
          <div class="sub-head">
            <h2>低水位提醒</h2>
            <span>{{ alerts.length }} 項</span>
          </div>
          <div class="panel-table-scroll">
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
                <tr v-for="row in alerts" :key="`a-${row.fixture_id}`">
                  <td>{{ row.fixture_code }}</td>
                  <td>{{ row.stock_qty }}</td>
                  <td>{{ row.min_stock_qty }}</td>
                  <td><UiStatusPill :label="stockStatusLabel(row.stock_status)" tone="danger" /></td>
                </tr>
                <tr v-if="alerts.length === 0">
                  <td colspan="4" class="empty-cell">目前沒有低水位提醒</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>
      </div>
    </section>

    <section v-else class="panel overview-panel">
      <div class="overview-head">
        <div>
          <h2>收 / 退料總檢視</h2>
        </div>
        <div class="overview-tools">
          <div class="toolbar-actions">
            <button class="outline-btn" type="button" @click="exportOverviewCsv">匯出 CSV</button>
          </div>
        </div>
      </div>

      <form class="overview-form" @submit.prevent="searchOverview">
        <label>
          <span>類型</span>
          <select v-model="overviewFilters.transaction_type">
            <option value="">全部</option>
            <option value="receipt">收料</option>
            <option value="return">退料</option>
          </select>
        </label>
        <label>
          <span>起始日期</span>
          <input v-model="overviewFilters.date_from" type="date" />
        </label>
        <label>
          <span>結束日期</span>
          <input v-model="overviewFilters.date_to" type="date" />
        </label>
        <label>
          <span>治具編號</span>
          <input v-model="overviewFilters.fixture_code" placeholder="例如 C-00003" />
        </label>
        <label>
          <span>單號</span>
          <input v-model="overviewFilters.transaction_no" placeholder="RCV-20260526-000001" />
        </label>
        <label>
          <span>識別碼</span>
          <input v-model="overviewFilters.tracking_code" placeholder="輸入 4 位識別碼" />
        </label>
        <label>
          <span>操作人員</span>
          <input v-model="overviewFilters.created_by" placeholder="輸入人員名稱" />
        </label>
        <div class="overview-actions">
          <button class="outline-btn" type="button" @click="resetOverviewFilters">重設</button>
          <button class="primary-btn" type="submit" :disabled="overviewLoading">
            {{ overviewLoading ? "查詢中..." : "查詢" }}
          </button>
        </div>
      </form>

      <div class="overview-table-wrap">
        <table class="grid-table overview-table">
          <thead>
            <tr>
              <th>類型</th>
              <th>單號</th>
              <th>治具編號</th>
              <th>來源</th>
              <th>識別碼</th>
              <th>數量</th>
              <th>操作人員</th>
              <th>日期</th>
              <th>備註</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in overviewRows" :key="row.id">
              <td>{{ row.transaction_type === "receipt" ? "收料" : "退料" }}</td>
              <td>{{ row.transaction_no }}</td>
              <td>{{ row.fixture_code }}</td>
              <td>{{ ownershipLabel(row.ownership_type) }}</td>
              <td>{{ row.identifier || "-" }}</td>
              <td>{{ row.quantity }}</td>
              <td>{{ row.created_by }}</td>
              <td>{{ new Date(row.occurred_at).toLocaleString("zh-TW") }}</td>
              <td>{{ row.note || "-" }}</td>
            </tr>
            <tr v-if="overviewRows.length === 0">
              <td colspan="9" class="empty-cell">{{ overviewLoading ? "查詢中..." : "查無資料" }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <teleport to="body">
      <div v-if="showBatchPanel" class="batch-modal-backdrop" @click.self="showBatchPanel = false">
        <div class="batch-modal">
          <div class="batch-modal-head">
            <div>
              <h2>批次貼上匯入</h2>
              <p>一次處理大量治具資料，解析與確認都在這裡完成，不會影響主畫面布局。</p>
            </div>
            <button class="outline-btn" type="button" @click="showBatchPanel = false">關閉</button>
          </div>

          <div class="batch-modal-body">
            <label class="batch-input">
              <span>單號</span>
              <input
                v-model="batchTransactionNo"
                placeholder="可自由輸入，例如內部批號、工單號"
                autocomplete="off"
                spellcheck="false"
              />
              <small class="batch-help-text">這個欄位只會作為整批收料 / 退料的單號，不限制格式。</small>
            </label>
            <label class="batch-input">
              <span>直接貼上每筆兩行資料</span>
              <textarea
                v-model="batchPasteText"
                placeholder="例如：\nC-00090-2605\n3\nC-00135-2606\n25"
                @paste="handleBatchPaste"
              ></textarea>
            </label>
            <label class="batch-input">
              <span>備註（非必填）</span>
              <input
                v-model="batchNote"
                type="text"
                placeholder="例如：急單補料、內部盤點補登"
              />
            </label>
            <div class="batch-actions">
              <button class="outline-btn" type="button" @click="clearBatchImport">清空</button>
              <button class="primary-btn" type="button" :disabled="saving || !batchCanSubmit" @click="submitBatchImport">
                {{ saving ? "送出中..." : batchImportLabel }}
              </button>
            </div>
            <div class="batch-tips">
              <span>格式支援兩行一筆，也支援單行 Tab / `|` 分欄。</span>
              <span>每筆資料請帶治具編號與 4 位識別碼；讀到新治具會先讓你新增。</span>
            </div>
            <div class="batch-table-wrap">
              <table class="grid-table batch-table">
                <thead>
                  <tr>
                    <th>行</th>
                    <th>原始治具</th>
                    <th>使用治具</th>
                    <th>識別碼</th>
                    <th>數量</th>
                    <th>狀態 / 操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in batchImportRows" :key="`batch-${row.lineNo}-${row.raw}`">
                    <td>{{ row.lineNo }}</td>
                    <td>{{ fallbackText(row.inputFixtureCode) }}</td>
                    <td>{{ fallbackText(row.resolvedFixtureCode || row.suggestedFixtureCode) }}</td>
                    <td>{{ fallbackText(row.inputToken) }}</td>
                    <td>{{ fallbackText(String(row.quantity || "")) }}</td>
                    <td>
                      <div class="batch-cell-stack">
                        <span v-if="row.status === 'ready'" class="batch-status ready">已確認</span>
                        <span v-else-if="row.status === 'needs-confirm'" class="batch-status warn">待確認</span>
                        <span v-else-if="row.status === 'needs-add'" class="batch-status warn">待新增</span>
                        <span v-else-if="row.status === 'skipped'" class="batch-status muted">已跳過</span>
                        <span v-else class="batch-status error">錯誤</span>
                        <span v-if="row.message || row.note" class="batch-row-note">{{ row.message || row.note }}</span>
                        <div class="batch-row-actions">
                          <template v-if="row.status === 'needs-confirm'">
                            <button class="ghost-btn batch-action-btn" type="button" @click="acceptSimilarFixture(row)">同一</button>
                            <button class="primary-btn batch-action-btn" type="button" @click="rejectSimilarFixture(row)">新增</button>
                            <button class="ghost-btn batch-action-btn" type="button" @click="skipBatchRow(row)">略過</button>
                          </template>
                          <template v-else-if="row.status === 'needs-add'">
                            <button class="primary-btn batch-action-btn" type="button" @click="addBatchRowFixture(row)">新增</button>
                            <button class="ghost-btn batch-action-btn" type="button" @click="skipBatchRow(row)">略過</button>
                          </template>
                          <template v-else-if="row.status === 'skipped'">
                            <span class="batch-inline-hint">已排除，不會送出</span>
                          </template>
                          <template v-else-if="row.status === 'error'">
                            <span class="batch-inline-hint">請修正後再匯入</span>
                          </template>
                        </div>
                      </div>
                    </td>
                  </tr>
                  <tr v-if="batchImportRows.length === 0">
                    <td colspan="6" class="empty-cell">貼上表格後會自動解析並顯示預覽</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<style scoped>
.inventory-shell {
  height: 100%;
  overflow: hidden;
  padding: 8px;
  background: #fff;
}

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

.inventory-summary-row {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 8px;
  min-width: 0;
}

.summary-chip {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #f8fafe;
  padding: 10px 12px;
  display: grid;
  gap: 4px;
  min-width: 0;
}

.summary-chip span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}

.summary-chip strong {
  color: #22314a;
  font-size: 18px;
  line-height: 1.1;
}

.summary-chip.success strong {
  color: var(--green);
}

.summary-chip.warn strong {
  color: var(--orange);
}

.summary-chip.danger strong {
  color: var(--red);
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
.sub-head,
.overview-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.panel-head p,
.overview-head p {
  margin: 3px 0 0;
  color: var(--muted);
  font-size: 12px;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.sub-head {
  align-items: center;
  margin-bottom: 8px;
}

.sub-head-actions {
  display: grid;
  gap: 8px;
  justify-items: end;
}

.sub-head span {
  color: var(--muted);
  font-size: 12px;
}

.section-hint {
  margin: 3px 0 0;
  color: #6f7d95;
  font-size: 11px;
  font-weight: 600;
}

.mode-switch {
  display: inline-flex;
  gap: 8px;
}

.segmented-control {
  display: inline-flex;
  gap: 4px;
  padding: 4px;
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  background: #f4f7fc;
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
  background: linear-gradient(180deg, #eff5ff 0%, #e3eeff 100%);
  color: var(--blue);
  box-shadow: 0 6px 14px rgba(47, 110, 229, 0.12);
}

.panel-actions {
  display: grid;
  gap: 8px;
  justify-items: end;
}

.batch-entry-btn {
  width: auto;
  min-width: 132px;
  padding-inline: 14px;
  font-size: 14px;
  font-weight: 800;
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
  display: grid;
  grid-template-rows: auto minmax(260px, 1fr);
  gap: 12px;
}

.overview-form label {
  display: grid;
  gap: 6px;
}

.overview-form span {
  color: #56657f;
  font-size: 12px;
  font-weight: 700;
  align-self: center;
}

select,
input,
.primary-btn,
.outline-btn {
  width: 100%;
  border-radius: 10px;
  font: inherit;
}

select,
input {
  border: 1px solid var(--line-strong);
  padding: 6px 10px;
  background: #fff;
}

input:disabled {
  background: #f3f5f9;
  color: #6c7891;
}

.primary-btn {
  border: 1px solid var(--green);
  background: linear-gradient(180deg, #4cc36b 0%, #2ea54e 100%);
  color: #fff;
  font-weight: 700;
  padding: 8px 14px;
  min-height: 36px;
  box-shadow: 0 8px 18px rgba(46, 165, 78, 0.18);
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
  box-shadow: 0 10px 22px rgba(46, 165, 78, 0.24);
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
.alert-panel,
.overview-panel {
  min-height: 0;
  overflow-x: auto;
}

.recent-block {
  min-height: 300px;
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

.batch-panel-body {
  display: grid;
  gap: 8px;
}

.batch-input {
  display: grid;
  gap: 6px;
}

.batch-input span,
.batch-tips {
  color: #56657f;
  font-size: 12px;
  font-weight: 700;
}

.batch-help-text {
  color: #6b7a90;
  font-size: 12px;
  line-height: 1.45;
  font-weight: 600;
}

.batch-input textarea {
  min-height: 132px;
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  padding: 10px 12px;
  resize: vertical;
  line-height: 1.55;
  font: inherit;
}

.batch-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

.batch-actions .outline-btn,
.batch-actions .primary-btn {
  width: auto;
}

.batch-tips {
  display: grid;
  gap: 2px;
  color: var(--muted);
  font-weight: 600;
}

.batch-table {
  table-layout: fixed;
  min-width: 100%;
}

.batch-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 140;
  background: rgba(15, 23, 42, 0.42);
  display: grid;
  place-items: center;
  padding: 18px;
}

.batch-modal {
  width: min(1300px, 100%);
  max-height: 92vh;
  overflow: hidden;
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: #fff;
  box-shadow: 0 24px 80px rgba(15, 23, 42, 0.24);
  display: grid;
  grid-template-rows: auto 1fr;
}

.batch-modal-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 18px 12px;
  border-bottom: 1px solid var(--line);
}

.batch-modal-head h2 {
  margin: 0;
  color: #162033;
  font-size: 18px;
}

.batch-modal-head p {
  margin: 3px 0 0;
  color: var(--muted);
  font-size: 12px;
}

.batch-modal-body {
  display: grid;
  gap: 10px;
  padding: 12px 18px 18px;
  overflow: auto;
}

.batch-table-wrap {
  min-height: 0;
  overflow: auto;
}

.batch-status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 64px;
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 700;
}

.batch-status.ready {
  color: var(--green);
  background: var(--green-soft);
}

.batch-status.warn {
  color: var(--orange);
  background: var(--orange-soft);
}

.batch-status.muted {
  color: #66748d;
  background: #edf1f7;
}

.batch-status.error {
  color: var(--red);
  background: var(--red-soft);
}

.batch-cell-stack {
  display: grid;
  gap: 6px;
}

.batch-row-note {
  color: #607089;
  font-size: 11px;
  line-height: 1.4;
}

.batch-row-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.batch-action-btn {
  width: auto;
  min-height: 28px;
  padding: 5px 10px;
  font-size: 11px;
  border-radius: 999px;
}

.batch-action-btn.primary-btn {
  min-width: 72px;
}

.batch-action-btn.ghost-btn {
  min-width: 60px;
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
  background: linear-gradient(90deg, #4cc36b 0%, #2ea54e 100%);
}

.stock-meter.low_stock .stock-meter-fill {
  background: linear-gradient(90deg, #ffbf47 0%, #e08a1e 100%);
}

.stock-meter.out_of_stock .stock-meter-fill {
  background: linear-gradient(90deg, #f46a6a 0%, #dd5757 100%);
}

.stock-meter span {
  color: #66748d;
  font-size: 11px;
  font-weight: 700;
}

.batch-inline-hint {
  color: #74839b;
  font-size: 11px;
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
.recent-block table,
.overview-table {
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

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 10px;
}

.summary-card {
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #f8fafe;
  padding: 9px 10px;
  display: grid;
  gap: 4px;
}

.summary-card span {
  color: var(--muted);
  font-size: 12px;
}

.summary-card strong {
  color: #22314a;
  font-size: 18px;
  line-height: 1.1;
}

.text-green {
  color: var(--green);
}

.text-orange {
  color: var(--orange);
}

.text-red {
  color: var(--red);
}

.status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 64px;
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 700;
}

.status.normal {
  color: var(--green);
  background: var(--green-soft);
}

.status.low_stock {
  color: var(--orange);
  background: var(--orange-soft);
}

.status.out_of_stock {
  color: var(--red);
  background: var(--red-soft);
}

.empty-cell {
  text-align: center;
  color: var(--muted);
}

.overview-panel {
  display: grid;
  grid-template-rows: auto auto 1fr;
  gap: 8px;
  height: 100%;
  overflow: auto;
}

.overview-tools {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.toolbar-actions .outline-btn,
.overview-actions .outline-btn,
.overview-actions .primary-btn {
  width: auto;
}

.overview-form {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px 10px;
  align-items: end;
}

.overview-actions {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
}

.overview-table-wrap {
  min-height: 0;
  overflow: auto;
}

.hidden-input {
  display: none;
}

@media (max-width: 1500px) {
  .inventory-board {
    grid-template-columns: 1fr;
  }

  .inventory-summary-row {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .side-stack {
    grid-template-rows: auto;
  }

  .overview-form {
    grid-template-columns: 1fr;
  }

  .overview-head,
  .panel-head {
    flex-direction: column;
  }

  .overview-tools {
    justify-content: flex-start;
  }
}

@media (max-width: 900px) {
  .inventory-shell {
    padding: 8px;
  }

  .panel {
    padding: 12px;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .inventory-summary-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .overview-form {
    grid-template-columns: 1fr;
  }

  .overview-actions {
    justify-content: stretch;
  }

  .overview-actions button {
    flex: 1 1 0;
  }

  .sub-head-actions {
    width: 100%;
    justify-items: stretch;
  }

  .sub-head-actions span,
  .sub-head-actions .toggle-btn {
    width: 100%;
  }

  .batch-summary-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .batch-modal {
    width: min(100%, 1000px);
  }
}

@media (max-width: 640px) {
  .inventory-board {
    gap: 10px;
  }

  .panel-head h2,
  .sub-head h2,
  .overview-head h2 {
    font-size: 16px;
  }

  .mode-switch {
    width: 100%;
  }

  .segmented-control {
    width: 100%;
  }

  .segmented-btn {
    flex: 1 1 0;
  }

  .panel-actions {
    width: 100%;
    justify-items: stretch;
  }

  .toggle-btn {
    flex: 1 1 0;
  }

  .overview-tools,
  .toolbar-actions {
    width: 100%;
  }

  .toolbar-actions .outline-btn {
    flex: 1 1 120px;
  }

  .batch-panel-body {
    gap: 10px;
  }

  .inventory-summary-row {
    grid-template-columns: 1fr;
  }

  .batch-input textarea {
    min-height: 108px;
  }

  .batch-modal-backdrop {
    padding: 10px;
  }

  .batch-modal-head,
  .batch-modal-body {
    padding-left: 12px;
    padding-right: 12px;
  }

  .grid-table th,
  .grid-table td {
    white-space: nowrap;
  }

  .stock-meter span {
    white-space: nowrap;
  }
}
</style>
