<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { api } from "@/api";
import type { ProductionImportPreview } from "@/api/productionClient";
import UiModalShell from "@/components/common/UiModalShell.vue";
import { requestConfirmation } from "@/confirmState";
import { pushToast } from "@/toastState";
import { toCsv } from "@/utils/productionBatchImport";

type ProductionPasteView = "mappings" | "requirements";
type PreviewRow = { line: number; cells: string[]; error: string };

const props = defineProps<{
  open: boolean;
  view: ProductionPasteView;
  customerId?: number;
}>();

const emit = defineEmits<{
  close: [];
  imported: [];
}>();

const text = ref("");
const saving = ref(false);
const previewing = ref(false);
const serverPreview = ref<ProductionImportPreview | null>(null);
const expectedColumns = computed(() => props.view === "mappings" ? 2 : 4);
const title = computed(() => props.view === "mappings" ? "貼上匯入機種站點" : "貼上匯入治具需求");
const description = computed(() => props.view === "mappings"
  ? "從 Excel 貼上兩欄：機種編號、站點編號。每列建立一組機種與站點綁定。"
  : "從 Excel 貼上四欄：機種編號、站點編號、治具編號、每站需求量。需求量必須是大於 0 的整數。"
);
const placeholder = computed(() => props.view === "mappings"
  ? "例如：\nMODEL-A\tSTATION-01\nMODEL-A\tSTATION-02"
  : "例如：\nMODEL-A\tSTATION-01\tFIXTURE-001\t2\nMODEL-A\tSTATION-01\tFIXTURE-002\t1"
);

function splitCells(line: string): string[] {
  const value = line.trim();
  if (value.includes("\t")) return value.split("\t").map((cell) => cell.trim());
  if (value.includes("|")) return value.split("|").map((cell) => cell.trim());
  if (/[;,，；]/.test(value)) return value.split(/[;,，；]/).map((cell) => cell.trim());
  return value.split(/\s+/).map((cell) => cell.trim());
}

function isHeader(cells: string[]): boolean {
  const first = (cells[0] ?? "").trim().toLowerCase();
  return ["model_code", "model code", "機種", "機種編號"].includes(first);
}

const previewRows = computed<PreviewRow[]>(() => {
  const rows: PreviewRow[] = [];
  for (const [index, line] of text.value.replace(/\r/g, "").split("\n").entries()) {
    if (!line.trim()) continue;
    const cells = splitCells(line);
    if (isHeader(cells)) continue;
    let error = "";
    if (cells.length !== expectedColumns.value || cells.some((cell) => !cell)) {
      error = `需要 ${expectedColumns.value} 欄且不可空白`;
    } else if (props.view === "requirements" && !/^[1-9]\d*$/.test(cells[3] ?? "")) {
      error = "每站需求量必須是大於 0 的整數";
    }
    rows.push({ line: index + 1, cells, error });
  }
  return rows;
});
const readyRows = computed(() => previewRows.value.filter((row) => !row.error));
const errorRows = computed(() => previewRows.value.filter((row) => row.error));
const actionLabel = computed(() => {
  if (previewing.value) return "檢查中...";
  if (saving.value) return "匯入中...";
  if (!serverPreview.value) return "檢查差異";
  if (serverPreview.value.error_count > 0) return "請先修正錯誤";
  if (serverPreview.value.conflict_count > 0) return `確認並取代 ${serverPreview.value.conflict_count} 筆差異`;
  if (serverPreview.value.new_count > 0) return `匯入 ${serverPreview.value.new_count} 筆新資料`;
  return "沒有需要匯入的資料";
});
const actionDisabled = computed(() =>
  saving.value ||
  previewing.value ||
  Boolean(serverPreview.value && serverPreview.value.error_count > 0) ||
  Boolean(serverPreview.value && serverPreview.value.new_count === 0 && serverPreview.value.conflict_count === 0)
);

function buildCsv(): string {
  return props.view === "mappings"
    ? toCsv(["model_code", "station_code"], readyRows.value.map((row) => row.cells))
    : toCsv(
        ["model_code", "station_code", "fixture_code", "required_qty"],
        readyRows.value.map((row) => row.cells)
      );
}

function clear(): void {
  text.value = "";
  serverPreview.value = null;
}

function validatePaste(): boolean {
  if (!props.customerId) {
    pushToast("請先選擇客戶。", "warning");
    return false;
  }
  if (previewRows.value.length === 0) {
    pushToast("請先貼上要匯入的產能資料。", "warning");
    return false;
  }
  if (errorRows.value.length > 0) {
    pushToast("貼上內容仍有錯誤列，請先修正。", "warning");
    return false;
  }
  return true;
}

async function checkDifferences(): Promise<void> {
  if (!validatePaste() || !props.customerId) return;
  previewing.value = true;
  try {
    const csv = buildCsv();
    serverPreview.value = props.view === "mappings"
      ? await api.previewModelStationsCsv(props.customerId, csv, "form-paste-model-stations.csv")
      : await api.previewFixtureRequirementsCsv(props.customerId, csv, "form-paste-fixture-requirements.csv");
    if (serverPreview.value.error_count > 0) {
      pushToast("差異預覽中有錯誤，請依狀態欄修正。", "warning");
    } else if (serverPreview.value.conflict_count > 0) {
      pushToast(`發現 ${serverPreview.value.conflict_count} 筆與既有資料不同，請先預覽再決定是否取代。`, "warning");
    } else {
      pushToast("差異檢查完成，請確認預覽後再匯入。", "info");
    }
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "產能匯入差異檢查失敗", "error");
  } finally {
    previewing.value = false;
  }
}

async function submit(): Promise<void> {
  if (!serverPreview.value) {
    await checkDifferences();
    return;
  }
  if (!validatePaste() || !props.customerId || serverPreview.value.error_count > 0) return;

  const conflicts = serverPreview.value.rows.filter((row) => row.status === "conflict");
  const overwriteExisting = conflicts.length > 0;
  if (overwriteExisting) {
    const examples = conflicts.slice(0, 5).map((row) =>
      `${row.model_code} / ${row.station_code} / ${row.fixture_code}：${row.existing_required_qty} → ${row.incoming_required_qty}`
    );
    const suffix = conflicts.length > examples.length ? `\n另有 ${conflicts.length - examples.length} 筆差異。` : "";
    const confirmed = await requestConfirmation(
      `以下既有治具需求量將被取代：\n${examples.join("\n")}${suffix}\n\n未貼上的其他站點與治具綁定不會被刪除。`,
      { title: "是否直接取代既有綁定？", confirmLabel: "直接取代", cancelLabel: "返回預覽" }
    );
    if (!confirmed) return;
  }

  saving.value = true;
  try {
    const csv = buildCsv();
    if (props.view === "mappings") {
      const result = await api.importModelStationsCsv(props.customerId, csv, "form-paste-model-stations.csv", false);
      pushToast(`機種站點匯入完成：新增 ${result.created_count} 筆、略過 ${result.skipped_count} 筆。`, "success");
    } else {
      const result = await api.importFixtureRequirementsCsv(
        props.customerId,
        csv,
        "form-paste-fixture-requirements.csv",
        overwriteExisting
      );
      pushToast(`治具需求匯入完成：新增 ${result.created_count} 筆、取代 ${result.updated_count} 筆、略過 ${result.skipped_count} 筆。`, "success");
    }
    clear();
    emit("imported");
    emit("close");
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "產能貼上匯入失敗", "error");
  } finally {
    saving.value = false;
  }
}

watch(() => props.view, clear);
watch([text, () => props.customerId], () => {
  serverPreview.value = null;
});
</script>

<template>
  <UiModalShell
    :open="open"
    labelled-by="form-production-paste-title"
    layer-class="form-paste-backdrop"
    dialog-class="form-paste-modal"
    @close="emit('close')"
  >
      <div data-tour="form-production-paste-modal">
        <header class="form-paste-head">
          <div><h2 id="form-production-paste-title">{{ title }}</h2><p>{{ description }}</p></div>
          <button class="outline-btn" type="button" @click="emit('close')">關閉</button>
        </header>
        <textarea v-model="text" class="form-paste-box" :placeholder="placeholder" data-modal-initial-focus></textarea>
        <div class="form-paste-actions">
          <button class="outline-btn" type="button" @click="clear">清空</button>
          <button class="primary-btn" type="button" :disabled="actionDisabled" @click="submit">{{ actionLabel }}</button>
        </div>
        <div class="form-paste-meta">可匯入 {{ readyRows.length }} / 錯誤 {{ errorRows.length }}</div>
        <div v-if="serverPreview" class="form-difference-summary" data-tour="form-production-difference-summary">
          <strong>差異預覽</strong>
          <span class="paste-new">新增 {{ serverPreview.new_count }}</span>
          <span class="paste-unchanged">相同 {{ serverPreview.unchanged_count }}</span>
          <span class="paste-conflict">待取代 {{ serverPreview.conflict_count }}</span>
          <span class="paste-error">錯誤 {{ serverPreview.error_count }}</span>
          <small>只更新貼上內容中的差異列，不會刪除其他既有綁定。</small>
        </div>
        <div class="form-paste-preview">
          <table class="paste-preview-table">
            <thead><tr><th>行</th><th>機種</th><th>站點</th><th v-if="view === 'requirements'">治具</th><th v-if="view === 'requirements'">每站需求</th><th>狀態</th></tr></thead>
            <tbody>
              <tr v-for="row in previewRows" :key="`${row.line}-${row.cells.join('-')}`"><td>{{ row.line }}</td><td>{{ row.cells[0] || "-" }}</td><td>{{ row.cells[1] || "-" }}</td><td v-if="view === 'requirements'">{{ row.cells[2] || "-" }}</td><td v-if="view === 'requirements'">{{ row.cells[3] || "-" }}</td><td><span :class="row.error ? 'paste-error' : 'paste-ready'">{{ row.error || "可匯入" }}</span></td></tr>
              <tr v-if="previewRows.length === 0"><td :colspan="view === 'requirements' ? 6 : 4" class="empty-cell">貼上資料後會在這裡預覽。</td></tr>
            </tbody>
          </table>
        </div>
        <div v-if="serverPreview" class="form-paste-preview server-difference-preview" data-tour="form-production-difference-preview">
          <table class="paste-preview-table">
            <thead><tr><th>機種</th><th>站點</th><th v-if="view === 'requirements'">治具</th><th v-if="view === 'requirements'">原需求量</th><th v-if="view === 'requirements'">匯入需求量</th><th>比對結果</th></tr></thead>
            <tbody>
              <tr v-for="row in serverPreview.rows" :key="`${row.line}-${row.model_code}-${row.station_code}-${row.fixture_code || ''}`">
                <td>{{ row.model_code || "-" }}</td><td>{{ row.station_code || "-" }}</td>
                <td v-if="view === 'requirements'">{{ row.fixture_code || "-" }}</td>
                <td v-if="view === 'requirements'">{{ row.existing_required_qty ?? "－" }}</td>
                <td v-if="view === 'requirements'">{{ row.incoming_required_qty ?? "－" }}</td>
                <td><span :class="`paste-${row.status}`">{{ row.message }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
  </UiModalShell>
</template>

<style scoped>
:global(.form-paste-backdrop) { z-index: 145; padding: 16px; background: rgba(15, 23, 42, 0.45); }
:global(.form-paste-modal) { width: min(900px, 100%); max-height: calc(100vh - 32px); padding: 18px; border-radius: 12px; box-shadow: 0 26px 70px rgba(15, 23, 42, 0.28); }
.form-paste-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.form-paste-head h2 { margin: 0; color: var(--text); font-size: 1.1rem; }
.form-paste-head p { margin: 5px 0 0; color: var(--muted); font-size: 0.75rem; line-height: 1.55; }
.form-paste-box { width: 100%; min-height: 180px; margin-top: 12px; padding: 10px; border: 1px solid var(--line-strong); border-radius: 7px; color: var(--text); background: #fff; font: inherit; line-height: 1.5; resize: vertical; }
.form-paste-actions { display: flex; justify-content: flex-end; gap: 7px; margin-top: 8px; }
.form-paste-meta { margin: 8px 0; color: var(--muted); font-size: 0.72rem; font-weight: 750; }
.form-difference-summary { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 14px; margin: 8px 0; padding: 10px; border: 1px solid #b8cae0; background: #f4f8fc; font-size: 0.74rem; }
.form-difference-summary strong { color: #244b78; }
.form-difference-summary small { flex-basis: 100%; color: var(--muted); }
.form-paste-preview { max-height: 300px; overflow: auto; }
.server-difference-preview { margin-top: 10px; border-top: 2px solid #8eaaca; }
.paste-preview-table { width: 100%; border-collapse: collapse; background: #fff; }
.paste-preview-table th, .paste-preview-table td { padding: 7px 8px; border: 1px solid var(--line); color: var(--text); font-size: 0.72rem; text-align: left; }
.paste-preview-table th { color: #314e73; background: #dce9f8; font-weight: 800; }
.paste-ready { color: #25613f; font-weight: 750; }
.paste-new { color: #25613f; font-weight: 750; }
.paste-unchanged { color: #526273; font-weight: 750; }
.paste-conflict { color: #9a5a10; font-weight: 800; }
.paste-error { color: #a43d3d; font-weight: 750; }
.empty-cell { padding: 22px !important; color: var(--muted) !important; text-align: center !important; }
@media (max-width: 620px) { .form-paste-head { flex-direction: column; } .form-paste-actions { display: grid; grid-template-columns: 1fr 1fr; } }
</style>
