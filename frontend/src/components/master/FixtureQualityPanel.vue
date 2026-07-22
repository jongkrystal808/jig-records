<script setup lang="ts">
import { computed, ref } from "vue";

import UiSectionHeader from "@/components/UiSectionHeader.vue";
import type { FixtureQualityReport } from "@/types";
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
  missing_name: ISSUE_LABELS.missing_name,
  missing_storage_and_min_stock: ISSUE_LABELS.missing_storage_and_min_stock,
  missing_image: ISSUE_LABELS.missing_image,
  missing_model_relation: ISSUE_LABELS.missing_model_relation,
  stock_mismatch: ISSUE_LABELS.stock_mismatch
};

const props = defineProps<{
  report: FixtureQualityReport | null;
  loading: boolean;
}>();

const emit = defineEmits<{
  openIssueEditor: [fixtureId: number, issueCode: string];
}>();

const selectedIssueCode = ref<"all" | keyof typeof ISSUE_FILTER_LABELS>("all");

function rowMatchesIssueFilter(row: FixtureQualityReport["rows"][number], issueCode: string): boolean {
  if (issueCode === "missing_storage_and_min_stock") {
    return row.issue_codes.includes("missing_storage_location") || row.issue_codes.includes("missing_min_stock_qty");
  }
  return row.issue_codes.includes(issueCode);
}

function displayIssueCodes(row: FixtureQualityReport["rows"][number]): string[] {
  const issueCodes = row.issue_codes.filter(
    (issueCode) => issueCode !== "missing_storage_location" && issueCode !== "missing_min_stock_qty"
  );
  if (row.issue_codes.includes("missing_storage_location") || row.issue_codes.includes("missing_min_stock_qty")) {
    issueCodes.unshift("missing_storage_and_min_stock");
  }
  return issueCodes;
}

const filteredRows = computed(() => {
  const rows = props.report?.rows ?? [];
  if (selectedIssueCode.value === "all") {
    return rows;
  }
  return rows.filter((row) => rowMatchesIssueFilter(row, selectedIssueCode.value));
});

const missingStorageOrMinStockCount = computed(
  () => props.report?.rows.filter((row) => rowMatchesIssueFilter(row, "missing_storage_and_min_stock")).length ?? 0
);

function issueLabel(issueCode: string): string {
  return ISSUE_LABELS[issueCode] ?? issueCode;
}

function isIssueClickable(issueCode: string): boolean {
  return issueCode !== "missing_model_relation";
}

function exportCsv(): void {
  const header = ["治具編號", "治具名稱", "儲位", "最低水位", "總庫存", "Identifier庫存", "機種關聯數", "圖片", "問題"];
  const csvRows = filteredRows.value.map((row) =>
    [
      row.fixture_code,
      fallbackText(row.fixture_name),
      fallbackText(row.storage_location),
      String(row.min_stock_qty),
      String(row.stock_qty),
      String(row.identifier_stock_qty),
      String(row.related_model_count),
      row.has_image ? "有" : "缺",
      displayIssueCodes(row).map((issueCode) => issueLabel(issueCode)).join(" / ")
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
</script>

<template>
  <article class="panel quality-panel">
    <UiSectionHeader
      class="panel-head"
      title="治具資料品質"
      :description="report ? `異常 ${report.problematic_fixture_count} / ${report.total_fixture_count} 筆（僅統計啟用中治具）` : 'Admin 檢查治具資料完整度（僅統計啟用中治具）'"
    >
      <template #actions>
        <div class="panel-actions">
          <select v-model="selectedIssueCode" class="issue-filter">
            <option value="all">全部問題</option>
            <option v-for="(label, issueCode) in ISSUE_FILTER_LABELS" :key="issueCode" :value="issueCode">{{ label }}</option>
          </select>
          <button class="outline-btn small" type="button" :disabled="filteredRows.length === 0" @click="exportCsv">匯出 CSV</button>
        </div>
      </template>
    </UiSectionHeader>

    <div v-if="loading" class="loading-banner">資料載入中，請稍候...</div>

    <template v-else>
      <div class="quality-summary">
        <div class="quality-card">
          <span>沒有名稱</span>
          <strong>{{ report?.missing_name_count ?? 0 }}</strong>
        </div>
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
        <div class="quality-card">
          <span>庫存不一致</span>
          <strong>{{ report?.stock_mismatch_count ?? 0 }}</strong>
        </div>
      </div>

      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th>治具編號</th>
              <th>治具名稱</th>
              <th>儲位</th>
              <th>最低水位</th>
              <th>總庫存</th>
              <th>Identifier 庫存</th>
              <th>機種關聯</th>
              <th>圖片</th>
              <th>問題</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in filteredRows" :key="row.fixture_id">
              <td>{{ row.fixture_code }}</td>
              <td>{{ fallbackText(row.fixture_name) }}</td>
              <td>{{ fallbackText(row.storage_location) }}</td>
              <td>{{ row.min_stock_qty }}</td>
              <td>{{ row.stock_qty }}</td>
              <td>{{ row.identifier_stock_qty }}</td>
              <td>{{ row.related_model_count }}</td>
              <td>{{ row.has_image ? "有" : "缺" }}</td>
              <td>
                <div class="issue-list">
                  <template v-for="issueCode in displayIssueCodes(row)" :key="`${row.fixture_id}-${issueCode}`">
                    <button
                      v-if="isIssueClickable(issueCode)"
                      class="issue-pill clickable"
                      type="button"
                      @click="handleIssueClick(row, issueCode)"
                    >
                      {{ issueLabel(issueCode) }}
                    </button>
                    <span v-else class="issue-pill">
                      {{ issueLabel(issueCode) }}
                    </span>
                  </template>
                </div>
              </td>
            </tr>
            <tr v-if="filteredRows.length === 0">
              <td colspan="9" class="empty-cell">目前沒有資料品質異常</td>
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
  grid-template-columns: repeat(5, minmax(0, 1fr));
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
}
</style>
