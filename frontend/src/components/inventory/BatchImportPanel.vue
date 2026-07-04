<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { api } from "@/api";
import { authSession, onboardingActive, onboardingStepIndex } from "@/appState";
import InlineSpinner from "@/components/common/InlineSpinner.vue";
import { onboardingSteps } from "@/onboarding";
import { pushToast } from "@/toastState";
import type { Fixture } from "@/types";

type ImportMode = "receipt" | "return";
type BatchRowStatus = "ready" | "needs-confirm" | "needs-add" | "skipped" | "error";

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
};

const props = withDefaults(defineProps<{
  customerId: number | undefined;
  title?: string;
  description?: string;
  showModeSwitch?: boolean;
  initialMode?: ImportMode;
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
}>();

const mode = ref<ImportMode>(props.initialMode);
const loading = ref(false);
const saving = ref(false);
const fixtures = ref<Fixture[]>([]);
const batchPasteText = ref("");
const batchTransactionNo = ref("");
const batchNote = ref("");
const rows = ref<BatchImportRow[]>([]);

const readyRows = computed(() => rows.value.filter((row) => row.status === "ready"));
const pendingRows = computed(() => rows.value.filter((row) => row.status === "needs-confirm" || row.status === "needs-add"));
const errorRows = computed(() => rows.value.filter((row) => row.status === "error"));
const canSubmit = computed(() => readyRows.value.length > 0 && pendingRows.value.length === 0 && errorRows.value.length === 0 && batchTransactionNo.value.trim().length > 0);
const currentOnboardingStepId = computed(() => onboardingSteps[onboardingStepIndex.value]?.id ?? "");
const tutorialBannerText = computed(() =>
  mode.value === "receipt" ? "教學模式：本次會模擬收料，不會寫入正式資料。" : "教學模式：本次會模擬退料，不會寫入正式資料。"
);

function normalizeText(value: string): string {
  return value.replace(/\u00a0/g, " ").trim();
}

function normalizeCode(value: string): string {
  return normalizeText(value).toUpperCase();
}

function normalizeIdentifier(value: string): string {
  const normalized = normalizeText(value);
  if (!normalized) return "";
  if (!/^\d+$/.test(normalized)) return normalized;
  return normalized.padStart(4, "0");
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
    message
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

  const identifier = normalizeIdentifier(tokenText);
  if (!identifier) {
    return makeErrorRow(lineNo, raw, "缺少識別碼");
  }
  if (!/^\d+$/.test(identifier)) {
    return makeErrorRow(lineNo, raw, "識別碼必須為數字");
  }
  if (identifier.length > 4) {
    return makeErrorRow(lineNo, raw, "識別碼必須為 4 位數字");
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
      message: null
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
      message: `可能是 ${similarFixture.code}，請確認`
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
    message: `找不到治具 ${fixtureCodeText}`
  };
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
    rows.value = [];
    return;
  }
  loading.value = true;
  try {
    fixtures.value = await api.listFixtures(props.customerId);
    rows.value = parseRows(batchPasteText.value);
  } finally {
    loading.value = false;
  }
}

function refreshPreview(): void {
  rows.value = parseRows(batchPasteText.value);
}

function clearPanel(): void {
  batchPasteText.value = "";
  batchTransactionNo.value = "";
  batchNote.value = "";
  rows.value = [];
}

function acceptSimilar(row: BatchImportRow): void {
  if (!row.suggestedFixtureId) return;
  row.resolvedFixtureId = row.suggestedFixtureId;
  row.resolvedFixtureCode = row.suggestedFixtureCode;
  row.suggestedFixtureId = null;
  row.suggestedFixtureCode = "";
  row.status = "ready";
  row.message = "已接受相似治具";
}

function rejectSimilar(row: BatchImportRow): void {
  row.suggestedFixtureId = null;
  row.suggestedFixtureCode = "";
  row.status = "needs-add";
  row.message = `找不到治具 ${row.inputFixtureCode}`;
}

function skipRow(row: BatchImportRow): void {
  row.status = "skipped";
  row.message = "已略過，不會送出";
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
  row.message = "已建立新治具";
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
  if (!props.customerId || !canSubmit.value) {
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
      items: readyRows.value.map((row) => ({
        fixture_id: row.resolvedFixtureId as number,
        ownership_type: "customer_supplied" as const,
        identifier: row.inputToken,
        quantity: row.quantity
      }))
    };

    if (mode.value === "receipt") {
      await api.createReceipt(payload);
    } else {
      await api.createReturn(payload);
    }
    clearPanel();
    emit("success");
    await loadFixtures();
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

onMounted(async () => {
  await loadFixtures();
});
</script>

<template>
  <section class="batch-panel" :class="{ frameless: hideFrame }">
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
        <label>
          <span>備註</span>
          <input v-model="batchNote" placeholder="選填" />
        </label>
      </div>

      <label class="paste-field" data-tour="inventory-paste-field">
        <span>批次內容</span>
        <textarea v-model="batchPasteText" placeholder="支援 fixture-code-identifier / quantity，或 fixture-code[TAB]identifier[TAB]quantity"></textarea>
      </label>

      <div class="action-row">
        <div class="summary-text">
          <span>可送出 {{ readyRows.length }} 筆</span>
          <span>待處理 {{ pendingRows.length }} 筆</span>
          <span>錯誤 {{ errorRows.length }} 筆</span>
        </div>
        <div class="action-group">
          <button
            v-if="tutorialMode"
            class="ghost-btn"
            data-tour="inventory-sandbox-action"
            type="button"
            :disabled="saving || fixtures.length === 0"
            @click="fillTutorialSample"
          >
            套用教學試跑
          </button>
          <button class="outline-btn" type="button" :disabled="saving" @click="clearPanel">清空</button>
          <button class="primary-btn" data-tour="inventory-submit-action" type="button" :disabled="saving || !canSubmit" @click="submit">
            {{ saving ? "送出中..." : mode === "receipt" ? "送出收料" : "送出退料" }}
          </button>
        </div>
      </div>

      <div class="table-wrap">
        <table class="preview-table">
          <thead>
            <tr><th>#</th><th>治具</th><th>識別碼</th><th>數量</th><th>狀態</th><th>處理</th></tr>
          </thead>
          <tbody>
            <tr v-for="row in rows" :key="`${row.lineNo}-${row.raw}`">
              <td>{{ row.lineNo }}</td>
              <td>{{ row.resolvedFixtureCode || row.suggestedFixtureCode || row.inputFixtureCode || "-" }}</td>
              <td>{{ row.inputToken || "-" }}</td>
              <td>{{ row.quantity || "-" }}</td>
              <td>
                <span class="status-pill" :class="row.status">{{ row.status }}</span>
                <div v-if="row.message" class="row-note">{{ row.message }}</div>
              </td>
              <td>
                <div class="row-actions">
                  <template v-if="row.status === 'needs-confirm'">
                    <button class="ghost-btn small" type="button" @click="acceptSimilar(row)">同一治具</button>
                    <button class="outline-btn small" type="button" @click="rejectSimilar(row)">改為新增</button>
                    <button class="outline-btn small" type="button" @click="skipRow(row)">略過</button>
                  </template>
                  <template v-else-if="row.status === 'needs-add'">
                    <button class="ghost-btn small" type="button" @click="createMissingFixture(row)">新增治具</button>
                    <button class="outline-btn small" type="button" @click="skipRow(row)">略過</button>
                  </template>
                  <template v-else-if="row.status === 'error'">
                    <span class="muted">請修正原始資料</span>
                  </template>
                  <template v-else-if="row.status === 'skipped'">
                    <span class="muted">已排除</span>
                  </template>
                  <template v-else>
                    <span class="muted">可送出</span>
                  </template>
                </div>
              </td>
            </tr>
            <tr v-if="rows.length === 0">
              <td colspan="6" class="empty-cell">貼上資料後會自動解析預覽</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </section>
</template>

<style scoped>
.batch-panel {
  display: grid;
  gap: 12px;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: #fff;
  padding: 14px;
}

.batch-panel.frameless {
  border: 0;
  border-radius: 0;
  padding: 0;
  background: transparent;
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
  border: 1px solid #cfe0ff;
  border-radius: 12px;
  background: linear-gradient(180deg, #f8fbff 0%, #eef5ff 100%);
}

.tutorial-banner strong {
  color: #214b97;
  font-size: 12px;
}

.segmented-control {
  display: inline-flex;
  gap: 4px;
  padding: 4px;
  border: 1px solid #d7e2f5;
  border-radius: 999px;
  background: #f5f9ff;
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
  background: #fff;
  color: #2f6ee5;
  box-shadow: 0 6px 16px rgba(47, 110, 229, 0.12);
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

label {
  display: grid;
  gap: 6px;
}

label span {
  font-weight: 700;
}

input,
textarea {
  width: 100%;
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  padding: 8px 10px;
  background: #fff;
  font: inherit;
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

.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 82px;
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 700;
  text-transform: capitalize;
}

.status-pill.ready {
  color: var(--green);
  background: var(--green-soft);
}

.status-pill.needs-confirm,
.status-pill.needs-add {
  color: var(--orange);
  background: var(--orange-soft);
}

.status-pill.error {
  color: var(--red);
  background: var(--red-soft);
}

.status-pill.skipped {
  color: #66748d;
  background: #edf1f7;
}

.primary-btn,
.outline-btn,
.ghost-btn {
  border-radius: 10px;
  font-weight: 700;
  min-height: 34px;
}

.primary-btn {
  border: 1px solid var(--green);
  background: linear-gradient(180deg, #4cc36b 0%, #2ea54e 100%);
  color: #fff;
  padding: 8px 14px;
}

.outline-btn,
.ghost-btn {
  border: 1px solid var(--line-strong);
  background: linear-gradient(180deg, #ffffff 0%, #f7f9fd 100%);
  color: #5b677d;
  padding: 8px 14px;
}

.ghost-btn {
  border-color: #bfd0ef;
  color: #2f6ee5;
  background: #f7faff;
}

.small {
  min-height: 30px;
  padding: 6px 10px;
}

.loading-row {
  display: flex;
  align-items: center;
  min-height: 72px;
}

@media (max-width: 720px) {
  .batch-head,
  .action-row {
    flex-direction: column;
  }

  .meta-grid {
    grid-template-columns: 1fr;
  }
}
</style>
