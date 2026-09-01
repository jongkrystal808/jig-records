<script setup lang="ts">
import { computed, ref, watch } from "vue";

import UiSectionHeader from "@/components/UiSectionHeader.vue";
import UiMultiSelect from "@/components/common/UiMultiSelect.vue";
import type { Fixture, FixtureQualityReport } from "@/types";
import { fallbackText } from "@/utils/display";

const ISSUE_LABELS: Record<string, string> = {
  missing_name: "沒有名稱",
  missing_storage_location: "沒有儲位",
  missing_image: "沒有圖片",
  missing_min_stock_qty: "沒有最低水位",
  missing_model_relation: "沒有任何機種關聯",
  stock_mismatch: "Identifier 庫存與總庫存不一致",
  missing_storage_and_min_stock: "沒有儲位 / 沒有最低水位"
};

const ISSUE_FILTER_LABELS: Record<string, string> = {
  missing_storage_and_min_stock: ISSUE_LABELS.missing_storage_and_min_stock,
  missing_image: ISSUE_LABELS.missing_image,
  missing_model_relation: ISSUE_LABELS.missing_model_relation
};

const VISIBLE_ISSUE_CODES = new Set([
  "missing_storage_location",
  "missing_min_stock_qty",
  "missing_image",
  "missing_model_relation"
]);

const props = defineProps<{
  report: FixtureQualityReport | null;
  fixtures: Fixture[];
  loading: boolean;
  inlineSavingFixtureId: number | null;
  embeddedForm?: boolean;
  embeddedWorkbench?: boolean;
  workbenchSideEditor?: boolean;
  issueFilter?: string[];
}>();

const emit = defineEmits<{
  openIssueEditor: [fixtureId: number, issueCode: string];
  saveInlineIssue: [fixtureId: number, lineStorageLocation: string, departmentStorageLocation: string, minStockQty: number];
}>();

const selectedIssueCodes = ref<string[]>([]);
const selectedInlineFixtureId = ref<number | null>(null);
const inlineDrafts = ref<
  Record<number, { lineStorageLocation: string; departmentStorageLocation: string; minStockQty: number }>
>({});

function rowMatchesIssueFilter(row: FixtureQualityReport["rows"][number], issueCode: string): boolean {
  if (issueCode === "missing_storage_and_min_stock") {
    return row.issue_codes.includes("missing_storage_location") || row.issue_codes.includes("missing_min_stock_qty");
  }
  return row.issue_codes.includes(issueCode);
}

const filteredRows = computed(() => {
  const rows = (props.report?.rows ?? []).filter((row) =>
    row.issue_codes.some((issueCode) => VISIBLE_ISSUE_CODES.has(issueCode))
  );
  const issueCodes = props.issueFilter ?? selectedIssueCodes.value;
  if (!issueCodes.length) return rows;
  return rows.filter((row) => issueCodes.some((issueCode) => rowMatchesIssueFilter(row, issueCode)));
});
const selectedInlineRow = computed(
  () => filteredRows.value.find((row) => row.fixture_id === selectedInlineFixtureId.value) ?? null,
);

const missingStorageOrMinStockCount = computed(
  () => props.report?.rows.filter((row) => rowMatchesIssueFilter(row, "missing_storage_and_min_stock")).length ?? 0
);

function isIssueClickable(issueCode: string): boolean {
  return issueCode.length > 0 && issueCode !== "missing_storage_and_min_stock";
}

function rowNeedsInlineFix(row: FixtureQualityReport["rows"][number]): boolean {
  return rowMatchesIssueFilter(row, "missing_storage_and_min_stock");
}

function inlineDraft(
  row: FixtureQualityReport["rows"][number]
): { lineStorageLocation: string; departmentStorageLocation: string; minStockQty: number } {
  return (
    inlineDrafts.value[row.fixture_id] ?? {
      lineStorageLocation: "",
      departmentStorageLocation: "",
      minStockQty: row.min_stock_qty
    }
  );
}

function canSaveInline(row: FixtureQualityReport["rows"][number]): boolean {
  const draft = inlineDraft(row);
  const fixture = props.fixtures.find((item) => item.id === row.fixture_id);
  return (
    draft.lineStorageLocation.trim() !== (fixture?.line_storage_location ?? "").trim() ||
    draft.departmentStorageLocation.trim() !== (fixture?.department_storage_location ?? "").trim() ||
    draft.minStockQty !== row.min_stock_qty
  );
}

function exportCsv(): void {
  const header = ["治具編號", "儲位", "最低水位", "機種關聯", "圖片"];
  const csvRows = filteredRows.value.map((row) =>
    [
      row.fixture_code,
      fallbackText(row.storage_location),
      String(row.min_stock_qty),
      String(row.related_model_count),
      row.has_image ? "有" : "缺"
    ].map((value) => `"${String(value).replace(/"/g, '""')}"`)
  );
  const content = [header, ...csvRows].map((row) => row.join(",")).join("\n");
  const blob = new Blob(["\ufeff", content], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "fixture-quality-report.csv";
  anchor.click();
  URL.revokeObjectURL(url);
}

function handleIssueClick(row: FixtureQualityReport["rows"][number], issueCode: string): void {
  if (!isIssueClickable(issueCode)) {
    return;
  }
  emit("openIssueEditor", row.fixture_id, issueCode);
}

function saveInline(row: FixtureQualityReport["rows"][number]): void {
  const draft = inlineDraft(row);
  emit(
    "saveInlineIssue",
    row.fixture_id,
    draft.lineStorageLocation.trim(),
    draft.departmentStorageLocation.trim(),
    draft.minStockQty
  );
}

function handleInlineEnter(row: FixtureQualityReport["rows"][number]): void {
  if (props.inlineSavingFixtureId === row.fixture_id || !canSaveInline(row)) {
    return;
  }
  saveInline(row);
}

function selectInlineRow(row: FixtureQualityReport["rows"][number]): void {
  selectedInlineFixtureId.value = row.fixture_id;
}

watch(
  [() => props.report?.rows, () => props.fixtures],
  ([rows]) => {
    const nextDrafts: Record<
      number,
      { lineStorageLocation: string; departmentStorageLocation: string; minStockQty: number }
    > = {};
    for (const row of rows ?? []) {
      const fixture = props.fixtures.find((item) => item.id === row.fixture_id);
      nextDrafts[row.fixture_id] = {
        lineStorageLocation: fixture?.line_storage_location ?? "",
        departmentStorageLocation: fixture?.department_storage_location ?? "",
        minStockQty: fixture?.min_stock_qty ?? row.min_stock_qty
      };
    }
    inlineDrafts.value = nextDrafts;
    if (selectedInlineFixtureId.value && !(rows ?? []).some((row) => row.fixture_id === selectedInlineFixtureId.value)) {
      selectedInlineFixtureId.value = null;
    }
  },
  { immediate: true }
);
</script>

<template>
  <article class="panel quality-panel" :class="{ 'form-quality-panel': embeddedForm, 'workbench-quality-panel': embeddedWorkbench }" data-tour="master-quality-panel">
    <UiSectionHeader
      v-if="!embeddedForm && !embeddedWorkbench"
      class="panel-head"
      title="治具資料品質"
      :description="report ? `異常 ${filteredRows.length} / ${report.total_fixture_count} 筆（僅統計啟用中治具）` : '管理員檢查治具資料完整度（僅統計啟用中治具）'"
    >
      <template #actions>
        <div class="panel-actions">
          <UiMultiSelect v-model="selectedIssueCodes" label="問題類型" placeholder="全部問題" :options="Object.entries(ISSUE_FILTER_LABELS).map(([value, label]) => ({ value, label }))" />
          <button class="outline-btn small" type="button" :disabled="filteredRows.length === 0" @click="exportCsv">匯出 CSV</button>
        </div>
      </template>
    </UiSectionHeader>

    <div v-if="loading" class="loading-banner">資料載入中，請稍候...</div>

    <template v-else>
      <div v-if="!embeddedForm && !embeddedWorkbench" class="quality-summary" data-tour="master-quality-summary">
        <div class="quality-card">
          <span>沒有儲位 / 沒有最低水位</span>
          <strong>{{ missingStorageOrMinStockCount }}</strong>
        </div>
        <div class="quality-card">
          <span>沒有圖片</span>
          <strong>{{ report?.missing_image_count ?? 0 }}</strong>
        </div>
        <div class="quality-card">
          <span>沒有任何機種關聯</span>
          <strong>{{ report?.missing_model_relation_count ?? 0 }}</strong>
        </div>
      </div>

      <div v-else-if="embeddedForm" class="form-quality-overview" data-tour="master-quality-summary" role="status">
        <span><small>沒有儲位／最低水位</small><strong>{{ missingStorageOrMinStockCount }}</strong></span>
        <span><small>沒有圖片</small><strong>{{ report?.missing_image_count ?? 0 }}</strong></span>
        <span><small>沒有機種關聯</small><strong>{{ report?.missing_model_relation_count ?? 0 }}</strong></span>
      </div>

      <div v-else class="workbench-quality-overview" data-tour="master-quality-summary" role="status">
        <span><small>儲位／水位</small><strong>{{ missingStorageOrMinStockCount }}</strong></span>
        <span><small>沒有圖片</small><strong>{{ report?.missing_image_count ?? 0 }}</strong></span>
        <span><small>沒有機種關聯</small><strong>{{ report?.missing_model_relation_count ?? 0 }}</strong></span>
      </div>

      <Teleport v-if="workbenchSideEditor && selectedInlineRow" defer to="#workbench-management-tools">
        <section class="workbench-side-section workbench-side-editor" aria-label="治具資料品質編輯欄位">
          <header class="workbench-side-section-heading">
            <div><span>FIX QUALITY</span><strong>{{ selectedInlineRow.fixture_code }}</strong><small>{{ fallbackText(selectedInlineRow.fixture_name) }}</small></div>
            <button class="text-button" type="button" @click="selectedInlineFixtureId = null">關閉</button>
          </header>
          <div class="workbench-side-form">
            <label><span>產線儲位</span><input v-model="inlineDraft(selectedInlineRow).lineStorageLocation" type="text" placeholder="可只填其中一個儲位" @keydown.enter.prevent="handleInlineEnter(selectedInlineRow)" /></label>
            <label><span>部門儲位</span><input v-model="inlineDraft(selectedInlineRow).departmentStorageLocation" type="text" placeholder="可只填其中一個儲位" @keydown.enter.prevent="handleInlineEnter(selectedInlineRow)" /></label>
            <label><span>最低水位</span><input v-model.number="inlineDraft(selectedInlineRow).minStockQty" type="number" min="0" @keydown.enter.prevent="handleInlineEnter(selectedInlineRow)" /></label>
          </div>
          <div class="workbench-side-actions"><button class="primary-btn" type="button" :disabled="inlineSavingFixtureId === selectedInlineRow.fixture_id || !canSaveInline(selectedInlineRow)" @click="saveInline(selectedInlineRow)">{{ inlineSavingFixtureId === selectedInlineRow.fixture_id ? "更新中…" : "儲存修正" }}</button></div>
        </section>
      </Teleport>

      <div :class="embeddedForm ? 'table-wrap form-quality-table-wrap' : embeddedWorkbench ? 'table-scroll workbench-quality-table-wrap' : 'table-scroll'">
        <table :class="embeddedForm ? 'form-quality-table' : embeddedWorkbench ? 'data-table workbench-quality-table' : 'data-table'">
          <colgroup v-if="embeddedForm">
            <col class="quality-col-code" />
            <col class="quality-col-storage" />
            <col class="quality-col-min" />
            <col class="quality-col-relation" />
            <col class="quality-col-image" />
          </colgroup>
          <thead>
            <tr>
              <th>治具編號</th>
              <th>儲位</th>
              <th>最低水位</th>
              <th>機種關聯</th>
              <th>圖片</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in filteredRows" :key="row.fixture_id" :class="{ 'editing-row': workbenchSideEditor && selectedInlineFixtureId === row.fixture_id }">
              <td>{{ row.fixture_code }}</td>
              <td>
                <template v-if="rowNeedsInlineFix(row) && !workbenchSideEditor">
                  <div class="inline-edit-stack">
                    <input
                      v-model="inlineDraft(row).lineStorageLocation"
                      class="inline-edit-input"
                      type="text"
                      placeholder="產線儲位"
                      @keydown.enter.prevent="handleInlineEnter(row)"
                    />
                    <input
                      v-model="inlineDraft(row).departmentStorageLocation"
                      class="inline-edit-input"
                      type="text"
                      placeholder="部門儲位"
                      @keydown.enter.prevent="handleInlineEnter(row)"
                    />
                    <small class="inline-edit-hint">產線儲位、部門儲位分開填寫，只填一個也可</small>
                  </div>
                </template>
                <button
                  v-else-if="workbenchSideEditor && rowNeedsInlineFix(row)"
                  class="issue-pill clickable"
                  type="button"
                  @click="selectInlineRow(row)"
                >
                  {{ fallbackText(row.storage_location, "尚無儲位") }}
                </button>
                <template v-else>
                  {{ fallbackText(row.storage_location) }}
                </template>
              </td>
              <td>
                <template v-if="rowNeedsInlineFix(row) && !workbenchSideEditor">
                  <input
                    v-model.number="inlineDraft(row).minStockQty"
                    class="inline-edit-input min-stock-input"
                    type="number"
                    min="0"
                    @keydown.enter.prevent="handleInlineEnter(row)"
                  />
                </template>
                <button
                  v-else-if="workbenchSideEditor && rowNeedsInlineFix(row)"
                  class="issue-pill clickable"
                  type="button"
                  @click="selectInlineRow(row)"
                >
                  {{ row.min_stock_qty }}
                </button>
                <template v-else>
                  {{ row.min_stock_qty }}
                </template>
              </td>
              <td>
                <button
                  v-if="row.issue_codes.includes('missing_model_relation')"
                  class="issue-pill clickable"
                  type="button"
                  @click="handleIssueClick(row, 'missing_model_relation')"
                >
                  尚無關聯
                </button>
                <template v-else>{{ row.related_model_count }}</template>
              </td>
              <td>
                <button
                  v-if="!row.has_image"
                  class="issue-pill clickable"
                  type="button"
                  @click="handleIssueClick(row, 'missing_image')"
                >
                  尚無圖片
                </button>
                <span v-else-if="embeddedForm" class="status-pill normal">已有圖片</span>
                <template v-else>有</template>
              </td>
            </tr>
            <tr v-if="filteredRows.length === 0">
              <td colspan="5" class="empty-cell">目前沒有資料品質異常</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </article>
</template>

<style scoped>
.panel {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
  padding: 10px;
  min-width: 0;
  min-height: 0;
}

.quality-panel {
  display: grid;
  gap: 10px;
  overflow: auto;
}

.form-quality-panel {
  gap: 0;
  overflow: visible;
  padding: 0;
  border: 0;
  border-radius: 0;
}

.panel-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.issue-filter {
  min-width: 180px;
}

.quality-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.quality-card {
  display: grid;
  gap: 4px;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #f8fbff;
}

.quality-card span {
  color: #5d6d89;
  font-size: 11px;
  font-weight: 700;
}

.quality-card strong {
  color: #22314a;
  font-size: 18px;
}

.form-quality-overview {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  border-bottom: 1px solid var(--line);
  background: #fbfcfe;
}

.form-quality-overview > span {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-height: 38px;
  padding: 6px 10px;
  border-right: 1px solid var(--line);
}

.form-quality-overview > span:last-child {
  border-right: 0;
}

.form-quality-overview small {
  overflow: hidden;
  color: #526985;
  font-size: 0.7rem;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.form-quality-overview strong {
  color: #9a5a00;
  font-size: 0.9rem;
}

.loading-banner,
.empty-cell {
  text-align: center;
  padding: 14px 12px;
  color: #56657f;
  background: #f8fbff;
  border-top: 1px solid var(--line);
}

.table-scroll {
  min-width: 0;
  overflow-x: auto;
  min-height: 0;
}

.data-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border: 1px solid var(--line);
  border-radius: 10px;
  overflow: hidden;
}

.data-table th,
.data-table td {
  padding: 6px 8px;
  text-align: left;
  border-bottom: 1px solid var(--line);
  font-size: 12px;
  vertical-align: top;
}

.data-table thead th {
  background: #f7f9fd;
  color: #52607b;
  font-weight: 700;
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.form-quality-table-wrap {
  width: 100%;
  overflow: auto;
}

.form-quality-table {
  width: 100%;
  min-width: 760px;
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
  font-size: 0.75rem;
}

.form-quality-table th,
.form-quality-table td {
  height: 34px;
  padding: 6px 8px;
  overflow: hidden;
  border-right: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
  text-align: left;
  text-overflow: ellipsis;
  vertical-align: middle;
}

.form-quality-table th:last-child,
.form-quality-table td:last-child {
  border-right: 0;
}

.form-quality-table thead th {
  position: sticky;
  top: 0;
  z-index: 3;
  height: 36px;
  color: #31445f;
  background: #dce8f7;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.02em;
}

.form-quality-table tbody tr:nth-child(even) td {
  background: #f2f6fb;
}

.form-quality-table tbody tr:nth-child(odd) td {
  background: #fff;
}

.form-quality-table tbody tr:hover td {
  background: #e8f1ff;
}

.form-quality-table td:nth-child(2) {
  overflow: visible;
  white-space: normal;
}

.quality-col-code { width: 130px; }
.quality-col-storage { width: 300px; }
.quality-col-min { width: 110px; }
.quality-col-relation { width: 120px; }
.quality-col-image { width: 120px; }

.form-quality-table .inline-edit-stack {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.form-quality-table .inline-edit-hint {
  grid-column: 1 / -1;
}

.form-quality-table .inline-edit-input {
  min-width: 0;
  min-height: 28px;
  padding-block: 3px;
}

.issue-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.issue-pill {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 2px 8px;
  border-radius: 999px;
  background: #fff3e6;
  color: #9a5a00;
  font-size: 11px;
  font-weight: 700;
  border: 1px solid #f0d1a5;
  cursor: default;
}

.issue-pill.clickable {
  cursor: pointer;
}

.issue-pill.clickable:hover {
  background: #ffe7c7;
}

.outline-btn {
  border: 1px solid var(--line-strong);
  background: linear-gradient(180deg, #ffffff 0%, #f7f9fd 100%);
  color: #5b677d;
  padding: 6px 10px;
  border-radius: 10px;
  font-weight: 700;
  cursor: pointer;
}

.outline-btn.small {
  padding: 5px 8px;
  min-height: 28px;
  font-size: 12px;
}

.outline-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.inline-edit-stack {
  display: grid;
  gap: 4px;
}

.inline-edit-input {
  width: 100%;
  min-width: 120px;
  min-height: 30px;
  padding: 4px 8px;
  border: 1px solid var(--line-strong);
  border-radius: 8px;
  background: #fff;
  font: inherit;
}

.inline-edit-hint {
  color: #74839b;
  font-size: 10px;
}

.min-stock-input {
  max-width: 96px;
}

.inline-save-btn {
  align-self: flex-start;
}

.form-quality-table .issue-pill {
  min-height: 22px;
  border-radius: 4px;
}

.form-quality-panel .outline-btn,
.form-quality-panel .inline-edit-input {
  border-radius: 4px;
  background-image: none;
}

.form-quality-panel .outline-btn {
  color: #29476d;
  background: #fff;
}

.form-quality-panel .inline-edit-input:focus {
  outline: none;
  border-color: var(--tone-info);
  box-shadow: 0 0 0 3px var(--tone-info-soft);
}

@media (max-width: 1400px) {
  .quality-summary {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .quality-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .quality-summary {
    grid-template-columns: 1fr;
  }

  .form-quality-overview {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .form-quality-overview > span:nth-child(even) {
    border-right: 0;
  }
}
</style>
