<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

import { api } from "@/api";
import { ApiRequestError } from "@/api/core";
import { authSession, onboardingActive, onboardingFlowId, onboardingStepIndex, setCustomerSwitchGuard } from "@/appState";
import InlineSpinner from "@/components/common/InlineSpinner.vue";
import { getOnboardingFlow } from "@/onboarding";
import { pushToast } from "@/toastState";
import type { Fixture, IdentifierStockSummary, StockSummary } from "@/types";
import { buildInventoryPreviewStats } from "@/utils/inventoryBatchPreview";
import { normalizeIdentifierForWrite } from "@/utils/identifier";

type ImportMode = "receipt" | "return";
type BatchRowStatus = "ready" | "needs-confirm" | "needs-add" | "skipped" | "error";
type BatchOwnershipType = "customer_supplied" | "self_purchased";

type BatchImportRow = {
  lineNo: number;
  raw: string;
  inputFixtureCode: string;
  inputToken: string;
  quantity: number;
  resolvedFixtureId: number | null;
  resolvedFixtureCode: string;
  suggestedFixtureId: number | null;
  suggestedFixtureCode: string;
  status: BatchRowStatus;
  message: string | null;
  errorSource: "parse" | "inventory" | null;
};

type ReadySubmissionItem = {
  fixtureId: number;
  identifier: string;
  quantity: number;
  sourceRowCount: number;
};

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
  description: "支援兩行一組與表格式單行資料。",
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
const saving = ref(false);
const fixtures = ref<Fixture[]>([]);
const stockRows = ref<StockSummary[]>([]);
const identifierStockRows = ref<IdentifierStockSummary[]>([]);
const batchPasteText = ref("");
const batchTransactionNo = ref("");
const batchNote = ref("");
const batchOwnershipType = ref<BatchOwnershipType>("customer_supplied");
const rows = ref<BatchImportRow[]>([]);
const showReadyDetails = ref(false);
const showAllExceptions = ref(false);
const quickFixtureCode = ref("");
const quickIdentifier = ref("");
const quickQuantity = ref(1);

const readyRows = computed(() => rows.value.filter((row) => row.status === "ready"));
const pendingRows = computed(() => rows.value.filter((row) => row.status === "needs-confirm" || row.status === "needs-add"));
const errorRows = computed(() => rows.value.filter((row) => row.status === "error"));
const skippedRows = computed(() => rows.value.filter((row) => row.status === "skipped"));
const exceptionRows = computed(() => rows.value.filter((row) => row.status === "needs-confirm" || row.status === "needs-add" || row.status === "error"));
const visibleExceptionRows = computed(() => (showAllExceptions.value ? exceptionRows.value : exceptionRows.value.slice(0, 3)));
const hiddenExceptionCount = computed(() => Math.max(0, exceptionRows.value.length - visibleExceptionRows.value.length));
const mergedReadyItems = computed<ReadySubmissionItem[]>(() => {
  const merged = new Map<string, ReadySubmissionItem>();
  for (const row of readyRows.value) {
    if (!row.resolvedFixtureId || !row.inputToken) {
      continue;
    }
    const key = `${row.resolvedFixtureId}::${row.inputToken}`;
    const existing = merged.get(key);
    if (existing) {
      existing.quantity += row.quantity;
      existing.sourceRowCount += 1;
      continue;
    }
    merged.set(key, {
      fixtureId: row.resolvedFixtureId,
      identifier: row.inputToken,
      quantity: row.quantity,
      sourceRowCount: 1
    });
  }
  return [...merged.values()];
});
const mergedReadyItemCount = computed(() => mergedReadyItems.value.length);
const mergedDuplicateReductionCount = computed(() => readyRows.value.length - mergedReadyItemCount.value);
const mergedDuplicateGroupCount = computed(() => mergedReadyItems.value.filter((item) => item.sourceRowCount > 1).length);
const batchOwnershipLabel = computed(() => (batchOwnershipType.value === "self_purchased" ? "自購" : "客供"));
const batchModeLabel = computed(() => (mode.value === "receipt" ? "收料" : "退料"));
const previewHeadline = computed(() => `預覽 ${rows.value.length} 筆｜${batchModeLabel.value}｜來源：${batchOwnershipLabel.value}`);
const isSelfPurchasedBatch = computed(() => batchOwnershipType.value === "self_purchased");
const canSubmit = computed(
  () => mergedReadyItems.value.length > 0 && pendingRows.value.length === 0 && errorRows.value.length === 0 && batchTransactionNo.value.trim().length > 0
);
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
const tutorialBannerText = computed(() =>
  mode.value === "receipt" ? "教學模式：本次會模擬收料，不會寫入正式資料。" : "教學模式：本次會模擬退料，不會寫入正式資料。"
);
const hasPresetFixtureShortcut = computed(() => quickFixtureCode.value.length > 0);
const batchPasteExpanded = ref(false);
const showBatchPasteEditor = computed(() => props.tutorialMode || !hasPresetFixtureShortcut.value || batchPasteExpanded.value);
const batchPasteToggleLabel = computed(() => (showBatchPasteEditor.value ? "收合批次貼上" : "改用批次貼上"));
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
const previewStats = computed(() =>
  buildInventoryPreviewStats(
    rows.value.map((row) => ({
      resolvedFixtureId: row.resolvedFixtureId,
      inputToken: row.inputToken,
      quantity: mode.value === "receipt" ? row.quantity : -row.quantity
    })),
    identifierStockRows.value,
    fixtures.value,
    stockRows.value
  )
);

function normalizeText(value: string): string {
  return value.replace(/\u00a0/g, " ").trim();
}

function normalizeCode(value: string): string {
  return normalizeText(value).toUpperCase();
}

function splitCells(line: string): string[] {
  const trimmed = normalizeText(line);
  if (!trimmed) return [];
  if (trimmed.includes("\t")) return trimmed.split("\t").map(normalizeText).filter(Boolean);
  if (trimmed.includes("|")) return trimmed.split("|").map(normalizeText).filter(Boolean);
  if (/[;,，；]/.test(trimmed)) return trimmed.split(/[;,，；]/).map(normalizeText).filter(Boolean);
  return trimmed.split(/\s{2,}/).map(normalizeText).filter(Boolean);
}

function splitCombinedFixtureText(value: string): { fixtureCode: string; token: string } {
  const trimmed = normalizeText(value);
  const lastDash = trimmed.lastIndexOf("-");
  if (lastDash <= 0 || lastDash >= trimmed.length - 1) {
    return { fixtureCode: trimmed, token: "" };
  }
  return {
    fixtureCode: trimmed.slice(0, lastDash).trim(),
    token: trimmed.slice(lastDash + 1).trim()
  };
}

function findFixtureByCode(code: string): Fixture | undefined {
  const target = normalizeCode(code);
  return fixtures.value.find((row) => normalizeCode(row.code) === target);
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

function findSimilarFixture(code: string): Fixture | undefined {
  const target = normalizeCode(code);
  let best: { fixture: Fixture; distance: number; prefix: number } | null = null;
  for (const fixture of fixtures.value) {
    const candidate = normalizeCode(fixture.code);
    const prefix = commonPrefixLength(target, candidate);
    const distance = levenshteinDistance(target, candidate);
    if (prefix < 4 && distance > 2) continue;
    if (best === null || distance < best.distance || (distance === best.distance && prefix > best.prefix)) {
      best = { fixture, distance, prefix };
    }
  }
  return best && best.distance <= 2 ? best.fixture : undefined;
}

function makeErrorRow(lineNo: number, raw: string, message: string): BatchImportRow {
  return {
    lineNo,
    raw,
    inputFixtureCode: "",
    inputToken: "",
    quantity: 0,
    resolvedFixtureId: null,
    resolvedFixtureCode: "",
    suggestedFixtureId: null,
    suggestedFixtureCode: "",
    status: "error",
    message,
    errorSource: "parse"
  };
}

function buildRow(lineNo: number, codeLine: string, qtyLine: string): BatchImportRow {
  const raw = `${codeLine}\n${qtyLine}`;
  const codeCells = splitCells(codeLine);
  const qtyCells = splitCells(qtyLine);
  const qtyText = qtyCells[0] ?? "";

  if (!qtyText || !/^\d+$/.test(qtyText) || Number.parseInt(qtyText, 10) <= 0) {
    return makeErrorRow(lineNo, raw, "數量必須是大於 0 的整數");
  }

  let fixtureCodeText = normalizeText(codeLine);
  let tokenText = "";
  if (codeCells.length >= 3) {
    fixtureCodeText = `${codeCells[0]}-${codeCells[1]}`;
    tokenText = codeCells[2];
  } else if (codeCells.length === 2) {
    fixtureCodeText = codeCells[0];
    tokenText = codeCells[1];
  } else {
    const split = splitCombinedFixtureText(codeLine);
    fixtureCodeText = split.fixtureCode;
    tokenText = split.token;
  }

  const identifier = normalizeIdentifierForWrite(tokenText);
  if (!identifier) {
    return makeErrorRow(lineNo, raw, "缺少 datecode/編號");
  }

  const exactFixture = findFixtureByCode(fixtureCodeText);
  if (exactFixture) {
    return {
      lineNo,
      raw,
      inputFixtureCode: fixtureCodeText,
      inputToken: identifier,
      quantity: Number.parseInt(qtyText, 10),
      resolvedFixtureId: exactFixture.id,
      resolvedFixtureCode: exactFixture.code,
      suggestedFixtureId: null,
      suggestedFixtureCode: "",
      status: "ready",
      message: null,
      errorSource: null
    };
  }

  const similarFixture = findSimilarFixture(fixtureCodeText);
  if (similarFixture) {
    return {
      lineNo,
      raw,
      inputFixtureCode: fixtureCodeText,
      inputToken: identifier,
      quantity: Number.parseInt(qtyText, 10),
      resolvedFixtureId: null,
      resolvedFixtureCode: "",
      suggestedFixtureId: similarFixture.id,
      suggestedFixtureCode: similarFixture.code,
      status: "needs-confirm",
      message: `可能是 ${similarFixture.code}，請確認`,
      errorSource: null
    };
  }

  return {
    lineNo,
    raw,
    inputFixtureCode: fixtureCodeText,
    inputToken: identifier,
    quantity: Number.parseInt(qtyText, 10),
    resolvedFixtureId: null,
    resolvedFixtureCode: "",
    suggestedFixtureId: null,
    suggestedFixtureCode: "",
    status: "needs-add",
    message: `找不到治具 ${fixtureCodeText}`,
    errorSource: null
  };
}

function buildInventoryKey(fixtureId: number, identifier: string): string {
  return `${fixtureId}::${identifier}`;
}

function validateRowsForCurrentMode(sourceRows: BatchImportRow[]): BatchImportRow[] {
  const clonedRows = sourceRows.map((row) => ({ ...row }));
  if (mode.value !== "return") {
    return clonedRows.map((row) =>
      row.errorSource === "inventory"
        ? {
            ...row,
            status: "ready",
            message: null,
            errorSource: null
          }
        : row
    );
  }

  const availableQtyByKey = new Map(identifierStockRows.value.map((row) => [buildInventoryKey(row.fixture_id, row.identifier), row.stock_qty]));
  const requestedQtyByKey = new Map<string, number>();

  return clonedRows.map((row) => {
    if (row.status === "skipped" || row.status === "needs-add" || row.status === "needs-confirm" || row.errorSource === "parse") {
      return row;
    }
    if (!row.resolvedFixtureId || !row.inputToken) {
      return row;
    }

    const key = buildInventoryKey(row.resolvedFixtureId, row.inputToken);
    const availableQty = availableQtyByKey.get(key) ?? 0;
    const requestedQty = (requestedQtyByKey.get(key) ?? 0) + row.quantity;
    requestedQtyByKey.set(key, requestedQty);

    if (availableQty <= 0) {
      return {
        ...row,
        status: "error",
        message: `退料無庫存：${row.resolvedFixtureCode} / ${row.inputToken}`,
        errorSource: "inventory"
      };
    }

    if (requestedQty > availableQty) {
      return {
        ...row,
        status: "error",
        message: `退料超出庫存：${row.resolvedFixtureCode} / ${row.inputToken} 可退 ${availableQty} pcs，本次解析合計 ${requestedQty} pcs`,
        errorSource: "inventory"
      };
    }

    return {
      ...row,
      status: "ready",
      message: null,
      errorSource: null
    };
  });
}

function parseRows(text: string): BatchImportRow[] {
  const lines = text.replace(/\r/g, "").split("\n").map(normalizeText).filter(Boolean);
  const parsed: BatchImportRow[] = [];
  for (let index = 0; index < lines.length; ) {
    const current = lines[index];
    const cells = splitCells(current);
    if (cells.length >= 3 && /^\d+$/.test(cells[cells.length - 1])) {
      const codePart = cells.slice(0, cells.length - 1).join("\t");
      const qtyPart = cells[cells.length - 1];
      parsed.push(buildRow(parsed.length + 1, codePart, qtyPart));
      index += 1;
      continue;
    }

    const qtyLine = lines[index + 1];
    if (!qtyLine) {
      parsed.push(makeErrorRow(parsed.length + 1, current, "缺少數量列"));
      break;
    }
    parsed.push(buildRow(parsed.length + 1, current, qtyLine));
    index += 2;
  }
  return parsed;
}

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
  quickIdentifier.value = "";
  quickQuantity.value = 1;
  clearPersistedDraft();
}

function handleBatchPasteKeydown(event: KeyboardEvent): void {
  if (event.key !== "Tab") {
    return;
  }
  const target = event.target;
  if (!(target instanceof HTMLTextAreaElement)) {
    return;
  }
  event.preventDefault();
  const selectionStart = target.selectionStart ?? 0;
  const selectionEnd = target.selectionEnd ?? selectionStart;
  batchPasteText.value = `${batchPasteText.value.slice(0, selectionStart)}\t${batchPasteText.value.slice(selectionEnd)}`;
  const nextCursor = selectionStart + 1;
  requestAnimationFrame(() => {
    target.focus();
    target.setSelectionRange(nextCursor, nextCursor);
  });
}

function syncQuickFixtureCode(): void {
  quickFixtureCode.value = normalizeCode(props.presetFixtureCode ?? "");
  batchPasteExpanded.value = props.tutorialMode || quickFixtureCode.value.length === 0;
  if (!draftStorageKey.value) {
    quickIdentifier.value = "";
    quickQuantity.value = 1;
  }
}

function toggleBatchPasteEditor(): void {
  if (!hasPresetFixtureShortcut.value) {
    batchPasteExpanded.value = true;
    return;
  }
  batchPasteExpanded.value = !batchPasteExpanded.value;
}

function appendPresetFixtureRow(): void {
  const fixtureCode = quickFixtureCode.value;
  const identifier = normalizeIdentifierForWrite(quickIdentifier.value);
  const quantity = Math.max(0, Number(quickQuantity.value) || 0);
  if (!fixtureCode) {
    return;
  }
  if (!identifier) {
    pushToast("請先輸入 datecode/編號。", "warning");
    return;
  }
  if (!Number.isInteger(quantity) || quantity <= 0) {
    pushToast("數量必須是大於 0 的整數。", "warning");
    return;
  }
  const nextRow = `${fixtureCode}\t${identifier}\t${quantity}`;
  batchPasteText.value = batchPasteText.value.trim().length > 0 ? `${batchPasteText.value.trimEnd()}\n${nextRow}` : nextRow;
  quickIdentifier.value = "";
  quickQuantity.value = 1;
  refreshPreview();
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
      quickIdentifier?: string;
      quickQuantity?: number;
    };
    if (props.mode === undefined && (draft.mode === "receipt" || draft.mode === "return")) {
      internalMode.value = draft.mode;
    }
    batchOwnershipType.value = "customer_supplied";
    batchPasteText.value = typeof draft.batchPasteText === "string" ? draft.batchPasteText : "";
    batchTransactionNo.value = typeof draft.batchTransactionNo === "string" ? draft.batchTransactionNo : "";
    batchNote.value = typeof draft.batchNote === "string" ? draft.batchNote : "";
    quickIdentifier.value = typeof draft.quickIdentifier === "string" ? draft.quickIdentifier : "";
    quickQuantity.value = Number.isInteger(draft.quickQuantity) && (draft.quickQuantity ?? 0) > 0 ? (draft.quickQuantity as number) : 1;
    if (hasPresetFixtureShortcut.value && batchPasteText.value.trim().length > 0) {
      batchPasteExpanded.value = true;
    }
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
      batchNote: batchNote.value,
      quickIdentifier: quickIdentifier.value,
      quickQuantity: quickQuantity.value
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

async function submit(): Promise<void> {
  if (!props.customerId) {
    return;
  }
  if (!batchTransactionNo.value.trim()) {
    pushToast("單號為必填，請先輸入工單號或批號。", "warning");
    return;
  }
  if (!canSubmit.value) {
    return;
  }
  saving.value = true;
  try {
    if (props.tutorialMode) {
      clearPanel();
      emit("success");
      pushToast("教學試跑完成，未寫入正式收退料資料。", "success");
      return;
    }
    const payload = {
      customer_id: props.customerId,
      created_by: authSession.value?.display_name || "System",
      transaction_no: batchTransactionNo.value.trim(),
      note: batchNote.value.trim() || undefined,
      items: mergedReadyItems.value.map((item) => ({
        fixture_id: item.fixtureId,
        ownership_type: batchOwnershipType.value,
        identifier: item.identifier,
        quantity: item.quantity
      }))
    };

    const sendTransaction = async (confirmDuplicate = false) => {
      if (mode.value === "receipt") {
        await api.createReceiptWithOptions(payload, { confirmDuplicate });
        return;
      }
      await api.createReturnWithOptions(payload, { confirmDuplicate });
    };

    try {
      await sendTransaction(false);
    } catch (err) {
      if (err instanceof ApiRequestError && err.status === 409) {
        const confirmed = window.confirm(err.message);
        if (!confirmed) {
          return;
        }
        await sendTransaction(true);
      } else {
        throw err;
      }
    }
    clearPanel();
    emit("success");
    await loadFixtures();
  } catch (err) {
    await loadFixtures();
    pushToast(err instanceof Error ? err.message : mode.value === "receipt" ? "收料送出失敗" : "退料送出失敗", "error");
  } finally {
    saving.value = false;
  }
}

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
  () => props.presetFixtureCode,
  () => {
    syncQuickFixtureCode();
  },
  { immediate: true }
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
    if (!["inventory-paste", "inventory-submit"].includes(currentOnboardingStepId.value)) {
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
    quickIdentifier,
    quickQuantity,
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
    <header class="batch-head">
      <div>
        <h2>{{ title }}</h2>
        <p>{{ description }}</p>
      </div>
      <div v-if="showModeSwitch" class="segmented-control" data-tour="inventory-mode-switch">
        <button class="segmented-btn" :class="{ active: mode === 'receipt' }" type="button" @click="mode = 'receipt'">收料</button>
        <button class="segmented-btn" :class="{ active: mode === 'return' }" type="button" @click="mode = 'return'">退料</button>
      </div>
    </header>

    <div v-if="loading" class="loading-row">
      <InlineSpinner label="載入收退料匯入資料..." />
    </div>

    <template v-else>
      <div v-if="tutorialMode" class="tutorial-banner">
        <strong>教學模式</strong>
        <span>{{ tutorialBannerText }}</span>
      </div>

      <div class="meta-grid">
        <label>
          <span>單號 *</span>
          <input v-model="batchTransactionNo" placeholder="例如工單號、批號、補料單號" autocomplete="off" spellcheck="false" />
        </label>
        <div class="batch-source-field">
          <span>來源</span>
          <div class="segmented-control batch-source-control">
            <button
              class="segmented-btn"
              :class="{ active: batchOwnershipType === 'customer_supplied' }"
              type="button"
              @click="batchOwnershipType = 'customer_supplied'"
            >
              客供（預設）
            </button>
            <button
              class="segmented-btn"
              :class="{ active: batchOwnershipType === 'self_purchased' }"
              type="button"
              @click="batchOwnershipType = 'self_purchased'"
            >
              自購
            </button>
          </div>
        </div>
        <label>
          <span>備註</span>
          <input v-model="batchNote" placeholder="選填" />
        </label>
      </div>

      <div v-if="isSelfPurchasedBatch" class="batch-source-warning">
        本批所有記錄將以「自購」來源送出。
      </div>

      <section v-if="hasPresetFixtureShortcut" class="preset-shortcut-card">
        <div class="preset-shortcut-head">
          <div>
            <strong>快速帶入治具</strong>
            <p>目前治具已預填，輸入 datecode/編號與數量後即可加入本次批次；需要一次貼多筆時再展開批次貼上。</p>
          </div>
          <button class="outline-btn btn-sm" type="button" @click="toggleBatchPasteEditor">{{ batchPasteToggleLabel }}</button>
        </div>
        <div class="preset-shortcut-grid">
          <label>
            <span>治具編號</span>
            <input :value="quickFixtureCode" readonly />
          </label>
          <label>
            <span>datecode/編號</span>
            <input v-model="quickIdentifier" placeholder="例如 240701A" autocomplete="off" spellcheck="false" />
          </label>
          <label>
            <span>數量</span>
            <input v-model.number="quickQuantity" type="number" min="1" />
          </label>
          <div class="preset-shortcut-actions">
            <button class="ghost-btn panel-accent-ghost" type="button" @click="appendPresetFixtureRow">加入批次</button>
          </div>
        </div>
      </section>

      <label v-if="showBatchPasteEditor" class="paste-field" data-tour="inventory-paste-field">
        <span>批次內容</span>
        <textarea
          v-model="batchPasteText"
          placeholder="格式: 治具ID-datecode/編號 [ENTER] 數量     |    或格式:治具ID[TAB]datecode/編號[TAB]數量"
          @keydown="handleBatchPasteKeydown"
        ></textarea>
      </label>

      <div class="action-row">
        <div class="summary-text">
          <span>可直接送出 {{ readyRows.length }} 筆</span>
          <span v-if="mergedDuplicateReductionCount > 0">送出時自動合併 {{ mergedDuplicateReductionCount }} 筆重複資料</span>
          <span>待處理 {{ pendingRows.length }} 筆</span>
          <span>錯誤 {{ errorRows.length }} 筆</span>
          <span v-if="skippedRows.length > 0">已略過 {{ skippedRows.length }} 筆</span>
        </div>
        <div class="action-group">
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
          <button class="primary-btn panel-accent-btn" data-tour="inventory-submit-action" type="button" :disabled="saving || !canSubmit" @click="submit">
            {{ saving ? "送出中..." : mode === "receipt" ? "送出收料" : "送出退料" }}
          </button>
        </div>
      </div>

      <div v-if="rows.length > 0" class="preview-summary-stack">
        <section class="preview-summary-card ready-card">
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
                <td>{{ mode === "receipt" ? row.quantity : `-${row.quantity}` }}</td>
                <td>{{ previewStats[row.lineNo - 1]?.currentIdentifierStockQty ?? "-" }}</td>
                <td>{{ previewStats[row.lineNo - 1]?.nextIdentifierStockQty ?? "-" }}</td>
                <td><span class="status-pill batch-state ready">ready</span></td>
              </tr>
            </tbody>
          </table>
        </div>

        <section class="preview-summary-card exception-card">
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
                <td>{{ mode === "receipt" ? row.quantity : `-${row.quantity}` }}</td>
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

      <section v-else-if="hasPresetFixtureShortcut && !showBatchPasteEditor" class="preview-summary-card quick-entry-hint" data-tour="inventory-preview-table">
        <div class="preview-summary-head">
          <div>
            <strong>快速模式</strong>
            <p>先輸入 datecode/編號與數量，再點「加入批次」；如果這次要處理多筆資料，再改用批次貼上。</p>
          </div>
          <span class="quick-entry-chip">{{ batchModeLabel }}｜{{ batchOwnershipLabel }}</span>
        </div>
      </section>

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

.preset-shortcut-card {
  display: grid;
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--panel-input-border);
  border-radius: 12px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--panel-accent-soft) 55%, white) 0%, #fff 100%);
}

.preset-shortcut-head strong {
  color: #22314a;
  font-size: 14px;
}

.preset-shortcut-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.preset-shortcut-head p {
  margin: 4px 0 0;
  color: #5d6d89;
  font-size: 12px;
}

.preset-shortcut-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr) 120px auto;
  gap: 10px;
  align-items: end;
}

.preset-shortcut-actions {
  display: flex;
  justify-content: flex-end;
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

input,
textarea {
  width: 100%;
  border: 1px solid var(--panel-input-border);
  border-radius: 10px;
  padding: 8px 10px;
  background: #fff;
  font: inherit;
}

input:focus,
textarea:focus {
  outline: none;
  border-color: var(--panel-accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--panel-accent-soft) 88%, white);
}

textarea {
  min-height: 180px;
  resize: vertical;
  line-height: 1.55;
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

.quick-entry-hint {
  border-style: dashed;
}

.quick-entry-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 30px;
  padding: 4px 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--panel-accent-soft) 68%, white);
  color: var(--panel-accent-strong);
  font-size: 11px;
  font-weight: 800;
  white-space: nowrap;
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

  .preset-shortcut-head {
    flex-direction: column;
  }

  .preset-shortcut-grid {
    grid-template-columns: 1fr;
  }

  .preset-shortcut-actions {
    justify-content: stretch;
  }
}
</style>
