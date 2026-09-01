<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from "vue";

import { api } from "@/api";
import { selectedCustomerId } from "@/appState";
import UiMultiSelect from "@/components/common/UiMultiSelect.vue";
import { pushToast } from "@/toastState";
import type { TransactionOverviewPage, TransactionQueryFilters } from "@/types";
import { completeBlobExport } from "@/utils/exportFeedback";
import { formOperationError } from "@/utils/formOperations";
import { scrollReportResultsIntoView } from "@/utils/scrollReportResults";

defineProps<{ workbenchLayout?: boolean }>();

const loading = ref(false);
const exporting = ref(false);
const resultsSection = ref<HTMLElement | null>(null);
const page = ref<TransactionOverviewPage | null>(null);
const pageNumber = ref(1);
const pageSize = ref(50);
const appliedFilters = ref<TransactionQueryFilters>({});
const expandedNoteIds = ref<Set<number>>(new Set());
const filters = reactive({
  transaction_type: [] as Array<"receipt" | "return">,
  ownership_type: [] as Array<"customer_supplied" | "self_purchased">,
  date_from: "",
  date_to: "",
  fixture_code: "",
  transaction_no: "",
  identifier: "",
  created_by: "",
});

function query(): TransactionQueryFilters {
  return {
    transaction_type: filters.transaction_type.length
      ? [...filters.transaction_type]
      : undefined,
    ownership_type: filters.ownership_type.length
      ? [...filters.ownership_type]
      : undefined,
    date_from: filters.date_from || undefined,
    date_to: filters.date_to || undefined,
    fixture_code: filters.fixture_code.trim() || undefined,
    transaction_no: filters.transaction_no.trim() || undefined,
    identifier: filters.identifier.trim() || undefined,
    created_by: filters.created_by.trim() || undefined,
  };
}

const appliedFilterLabels = computed(() => {
  const value = appliedFilters.value;
  const labels: string[] = [];
  if (value.transaction_type) {
    const values = Array.isArray(value.transaction_type)
      ? value.transaction_type
      : [value.transaction_type];
    labels.push(
      `類型 ${values.map((item) => (item === "receipt" ? "收料" : "退料")).join("＋")}`,
    );
  }
  if (value.ownership_type) {
    const values = Array.isArray(value.ownership_type)
      ? value.ownership_type
      : [value.ownership_type];
    labels.push(
      `來源 ${values.map((item) => (item === "self_purchased" ? "自購" : "客供")).join("＋")}`,
    );
  }
  if (value.date_from) labels.push(`自 ${value.date_from}`);
  if (value.date_to) labels.push(`至 ${value.date_to}`);
  if (value.fixture_code) labels.push(`治具 ${value.fixture_code}`);
  if (value.transaction_no) labels.push(`單號 ${value.transaction_no}`);
  if (value.identifier) labels.push(`編號 ${value.identifier}`);
  if (value.created_by) labels.push(`操作人 ${value.created_by}`);
  return labels;
});

async function load(): Promise<void> {
  loading.value = true;
  try {
    page.value = await api.listTransactionOverviewPage(
      pageNumber.value,
      pageSize.value,
      selectedCustomerId.value ?? undefined,
      query(),
    );
  } catch (error) {
    pushToast(formOperationError(error, "載入收退料總檢視失敗"), "error");
  } finally {
    loading.value = false;
  }
}

function resetFilters(): void {
  Object.assign(filters, {
    transaction_type: [],
    ownership_type: [],
    date_from: "",
    date_to: "",
    fixture_code: "",
    transaction_no: "",
    identifier: "",
    created_by: "",
  });
  appliedFilters.value = {};
  pageNumber.value = 1;
  void load();
}

async function applyFilters(): Promise<void> {
  pageNumber.value = 1;
  appliedFilters.value = { ...query() };
  await load();
  await nextTick();
  scrollReportResultsIntoView(resultsSection.value);
}

function notePreview(note: string | null): string {
  if (!note) return "-";
  return note.length > 24 ? `${note.slice(0, 24)}…` : note;
}

function toggleNote(rowId: number): void {
  const next = new Set(expandedNoteIds.value);
  if (next.has(rowId)) next.delete(rowId);
  else next.add(rowId);
  expandedNoteIds.value = next;
}

async function exportResults(): Promise<void> {
  if (exporting.value) return;
  const rowCount = page.value?.total ?? 0;
  if (rowCount === 0) {
    pushToast("目前沒有可匯出的資料。", "warning");
    return;
  }
  exporting.value = true;
  try {
    const response = await api.exportTransactionsCsv(
      selectedCustomerId.value ?? undefined,
      query(),
    );
    completeBlobExport(response, "form-transactions-filtered.csv", rowCount);
  } catch (error) {
    pushToast(formOperationError(error, "匯出篩選結果失敗"), "error");
  } finally {
    exporting.value = false;
  }
}

watch(
  selectedCustomerId,
  () => {
    pageNumber.value = 1;
    void load();
  },
  { immediate: true },
);
</script>

<template>
  <div
    class="report-workspace form-operation-workspace"
    data-form-operation-domain="transactions"
  >
    <div class="report-main-column">
      <Teleport
        defer
        to="#workbench-management-tools"
        :disabled="!workbenchLayout"
      >
        <section
          class="filter-panel workbench-side-section"
          data-tour="form-operation-filters"
          aria-label="收退料總檢視條件"
        >
          <div class="filter-panel-title">
            <div>
              <strong>篩選條件</strong
              ><span>收退料總檢視｜依目前功能顯示適用欄位</span>
            </div>
            <div class="filter-panel-title-actions">
              <button
                class="text-button"
                type="button"
                :disabled="loading"
                @click="load"
              >
                重新整理
              </button>
              <button
                class="outline-btn btn-sm"
                type="button"
                @click="resetFilters"
              >
                重設
              </button>
              <button
                class="primary-btn btn-sm"
                type="button"
                :disabled="loading"
                @click="applyFilters"
              >
                套用條件
              </button>
            </div>
          </div>
          <div
            v-if="appliedFilterLabels.length"
            class="applied-filter-summary"
            aria-live="polite"
          >
            <strong>已套用：</strong>
            <span>{{ appliedFilterLabels.join("、") }} ×</span>
            <span class="applied-filter-count"
              >共 {{ page?.total ?? 0 }} 筆</span
            >
            <button type="button" @click="resetFilters">清除條件</button>
          </div>
          <div class="filter-grid form-operation-filters">
            <UiMultiSelect
              v-model="filters.transaction_type"
              label="類型"
              placeholder="全部類型"
              :options="[
                { value: 'receipt', label: '收料' },
                { value: 'return', label: '退料' },
              ]"
            />
            <UiMultiSelect
              v-model="filters.ownership_type"
              label="來源"
              placeholder="全部來源"
              :options="[
                { value: 'customer_supplied', label: '客供' },
                { value: 'self_purchased', label: '自購' },
              ]"
            />
            <label
              ><span>起始日期</span
              ><input v-model="filters.date_from" type="date"
            /></label>
            <label
              ><span>結束日期</span
              ><input v-model="filters.date_to" type="date"
            /></label>
            <label
              ><span>治具編號</span
              ><input
                v-model="filters.fixture_code"
                placeholder="治具編號 / 名稱"
            /></label>
            <label
              ><span>單號</span><input v-model="filters.transaction_no"
            /></label>
            <label
              ><span>datecode/編號</span><input v-model="filters.identifier"
            /></label>
            <label
              ><span>操作人員</span><input v-model="filters.created_by"
            /></label>
          </div>
        </section>
      </Teleport>

      <slot name="between-filter-and-results" />

      <section
        ref="resultsSection"
        class="report-section"
        data-tour="form-operation-results"
        aria-label="收退料總檢視結果表格"
      >
        <div class="report-toolbar">
          <div class="report-summary">
            <strong>{{ page?.total ?? 0 }}</strong
            ><span>筆資料</span>
          </div>
          <div class="form-operation-toolbar-actions">
            <button
              class="outline-btn"
              type="button"
              :disabled="exporting"
              @click="exportResults"
            >
              {{ exporting ? "匯出中..." : "匯出篩選結果" }}
            </button>
            <label class="page-size-inline"
              >每頁<select
                v-model="pageSize"
                @change="
                  pageNumber = 1;
                  load();
                "
              >
                <option :value="50">50</option>
                <option :value="100">100</option>
              </select></label
            >
          </div>
        </div>
        <div class="form-report-grid-wrap">
          <table class="form-report-grid">
            <thead>
              <tr>
                <th>類型</th>
                <th>單號</th>
                <th>治具編號</th>
                <th>來源</th>
                <th>datecode/編號</th>
                <th>數量</th>
                <th>操作人員</th>
                <th>日期</th>
                <th>備註</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in page?.items ?? []" :key="row.id">
                <td>
                  <span
                    class="status-pill"
                    :class="
                      row.transaction_type === 'receipt' ? 'normal' : 'warning'
                    "
                    >{{
                      row.transaction_type === "receipt" ? "收料" : "退料"
                    }}</span
                  >
                </td>
                <td>{{ row.transaction_no || "-" }}</td>
                <td>{{ row.fixture_code }}</td>
                <td>
                  {{
                    row.ownership_type === "self_purchased" ? "自購" : "客供"
                  }}
                </td>
                <td>{{ row.identifier || "-" }}</td>
                <td>{{ row.quantity }}</td>
                <td>{{ row.created_by }}</td>
                <td>{{ row.occurred_at.slice(0, 10) }}</td>
                <td>
                  <button
                    v-if="row.note && row.note.length > 24"
                    class="report-note-toggle"
                    type="button"
                    :aria-expanded="expandedNoteIds.has(row.id)"
                    :title="
                      expandedNoteIds.has(row.id) ? '收合完整備註' : row.note
                    "
                    @click="toggleNote(row.id)"
                  >
                    {{
                      expandedNoteIds.has(row.id)
                        ? row.note
                        : notePreview(row.note)
                    }}
                  </button>
                  <span v-else>{{ row.note || "-" }}</span>
                </td>
              </tr>
              <tr v-if="!loading && !page?.items.length">
                <td colspan="9" class="empty-cell">查無資料</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="form-grid-pager">
          <button
            class="outline-btn btn-sm"
            type="button"
            :disabled="pageNumber <= 1"
            @click="
              pageNumber -= 1;
              load();
            "
          >
            上一頁</button
          ><span
            >第 {{ page?.page ?? pageNumber }} /
            {{ Math.max(1, Math.ceil((page?.total ?? 0) / pageSize)) }} 頁</span
          ><button
            class="outline-btn btn-sm"
            type="button"
            :disabled="pageNumber >= Math.ceil((page?.total ?? 0) / pageSize)"
            @click="
              pageNumber += 1;
              load();
            "
          >
            下一頁
          </button>
        </div>
      </section>
    </div>
  </div>
</template>
