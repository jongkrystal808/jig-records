<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { ownershipLabel } from "@/utils/display";
import { formatLocalDate } from "@/utils/date";

const props = defineProps<{
  filters: {
    transaction_type: "" | "receipt" | "return";
    date_from: string;
    date_to: string;
    fixture_code: string;
    transaction_no: string;
    tracking_code: string;
    created_by: string;
  };
  rows: Array<{
    id: number;
    transaction_type: "receipt" | "return";
    transaction_no: string | null;
    occurred_at: string;
    created_by: string;
    fixture_id: number | null;
    fixture_code: string;
    fixture_name: string;
    ownership_type: "customer_supplied" | "self_purchased";
    identifier: string | null;
    quantity: number;
    note: string | null;
  }>;
  page: number;
  pageSize: number;
  total: number;
  loading: boolean;
  backLabel?: string;
}>();

const emit = defineEmits<{
  "update:filters": [value: typeof props.filters];
  "update:page": [value: number];
  "update:pageSize": [value: number];
  back: [];
  search: [];
  reset: [];
}>();

function updateFilter<Key extends keyof typeof props.filters>(key: Key, value: (typeof props.filters)[Key]): void {
  emit("update:filters", {
    ...props.filters,
    [key]: value
  });
}

const showAdvancedFilters = ref(false);
const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)));
const hasRows = computed(() => props.rows.length > 0);
const pageDraft = ref(String(props.page));

function jumpToPage(): void {
  const parsed = Number.parseInt(pageDraft.value, 10);
  if (!Number.isFinite(parsed) || parsed < 1) {
    pageDraft.value = String(props.page);
    return;
  }
  const nextPage = Math.min(parsed, totalPages.value);
  pageDraft.value = String(nextPage);
  emit("update:page", nextPage);
}

watch(
  () => props.page,
  (value) => {
    pageDraft.value = String(value);
  },
  { immediate: true }
);

function displayTransactionNo(value: string | null): string {
  return value?.trim() || "（無單號）";
}
</script>

<template>
  <section class="panel overview-panel">
    <div class="overview-head" data-tour="overview-page-head">
      <div>
        <h2>收 / 退料總檢視</h2>
      </div>
      <button v-if="backLabel" class="outline-btn small" type="button" @click="emit('back')">{{ backLabel }}</button>
    </div>

    <form class="overview-form" data-tour="overview-filter-form" @submit.prevent="emit('search')">
      <div class="overview-fields">
        <label>
          <span>類型</span>
          <select :value="filters.transaction_type" @change="updateFilter('transaction_type', ($event.target as HTMLSelectElement).value as '' | 'receipt' | 'return')">
            <option value="">全部</option>
            <option value="receipt">收料</option>
            <option value="return">退料</option>
          </select>
        </label>
        <label>
          <span>起始日期</span>
          <input :value="filters.date_from" type="date" @input="updateFilter('date_from', ($event.target as HTMLInputElement).value)" />
        </label>
        <label>
          <span>結束日期</span>
          <input :value="filters.date_to" type="date" @input="updateFilter('date_to', ($event.target as HTMLInputElement).value)" />
        </label>
        <label>
          <span>治具編號</span>
          <input :value="filters.fixture_code" placeholder="請輸入治具編號 / 名稱" @input="updateFilter('fixture_code', ($event.target as HTMLInputElement).value)" />
        </label>
      </div>
      <div class="overview-secondary-row">
        <button
          class="outline-btn advanced-toggle"
          type="button"
          :aria-expanded="showAdvancedFilters"
          aria-controls="overview-advanced-filters"
          @click="showAdvancedFilters = !showAdvancedFilters"
        >
          {{ showAdvancedFilters ? "收合進階篩選" : "進階篩選" }}
        </button>
      </div>
      <div v-if="showAdvancedFilters" id="overview-advanced-filters" class="overview-fields overview-fields-advanced">
        <label>
          <span>單號</span>
          <input :value="filters.transaction_no" placeholder="RCV-20260526-000001" @input="updateFilter('transaction_no', ($event.target as HTMLInputElement).value)" />
        </label>
        <label>
          <span>datecode/編號</span>
          <input :value="filters.tracking_code" placeholder="輸入 datecode/編號 或舊 Datecode" @input="updateFilter('tracking_code', ($event.target as HTMLInputElement).value)" />
        </label>
        <label>
          <span>操作人員</span>
          <input :value="filters.created_by" placeholder="輸入人員名稱" @input="updateFilter('created_by', ($event.target as HTMLInputElement).value)" />
        </label>
      </div>
      <div class="overview-actions">
        <button class="outline-btn" type="button" @click="emit('reset')">重設</button>
        <button class="primary-btn" type="submit" :disabled="loading">
          {{ loading ? "查詢中..." : "查詢" }}
        </button>
      </div>
    </form>

    <div class="overview-toolbar">
      <span class="overview-summary">共 {{ total }} 筆，第 {{ page }} / {{ totalPages }} 頁</span>
      <div class="overview-pager">
        <label class="page-size-field">
          <span>每頁</span>
          <select :value="pageSize" :disabled="loading" @change="emit('update:pageSize', Number(($event.target as HTMLSelectElement).value))">
            <option :value="50">50</option>
            <option :value="100">100</option>
          </select>
        </label>
        <button class="outline-btn small" type="button" :disabled="loading || page <= 1" @click="emit('update:page', page - 1)">上一頁</button>
        <label class="page-jump-field">
          <span>跳至</span>
          <input v-model="pageDraft" type="number" min="1" :max="totalPages" :disabled="loading || !hasRows" @keydown.enter.prevent="jumpToPage" />
        </label>
        <button class="outline-btn small" type="button" :disabled="loading || !hasRows" @click="jumpToPage">跳轉</button>
        <button class="outline-btn small" type="button" :disabled="loading || page >= totalPages || !hasRows" @click="emit('update:page', page + 1)">下一頁</button>
      </div>
    </div>

    <div class="overview-table-wrap">
      <table class="grid-table overview-table">
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
          <tr v-for="row in rows" :key="row.id">
            <td>
              <span class="status-pill" :class="row.transaction_type">
                {{ row.transaction_type === "receipt" ? "收料" : "退料" }}
              </span>
            </td>
            <td>{{ displayTransactionNo(row.transaction_no) }}</td>
            <td>{{ row.fixture_code }}</td>
            <td>{{ ownershipLabel(row.ownership_type) }}</td>
            <td>{{ row.identifier || "-" }}</td>
            <td>{{ row.quantity }}</td>
            <td>{{ row.created_by }}</td>
            <td>{{ formatLocalDate(row.occurred_at) }}</td>
            <td>{{ row.note || "-" }}</td>
          </tr>
          <tr v-if="rows.length === 0">
            <td colspan="9" class="empty-cell">{{ loading ? "查詢中..." : "查無資料" }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
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

.overview-panel {
  display: grid;
  grid-template-rows: auto auto auto 1fr;
  gap: 8px;
  height: 100%;
  overflow: auto;
}

.overview-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.overview-head h2 {
  margin: 0;
  color: #22314a;
  font-size: 16px;
}

.overview-actions .outline-btn,
.overview-actions .primary-btn {
  width: auto;
}

.overview-form {
  display: grid;
  gap: 10px;
  align-items: end;
}

.overview-fields {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px 10px;
  align-items: end;
}

.overview-form label {
  display: grid;
  gap: 6px;
}

.overview-form span,
.page-size-field span {
  color: #56657f;
  font-size: 12px;
  font-weight: 700;
  align-self: center;
}

.overview-actions {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
}

.overview-secondary-row {
  display: flex;
  justify-content: flex-start;
}

.advanced-toggle {
  width: auto;
  min-width: 132px;
}

.overview-fields-advanced {
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: linear-gradient(180deg, #fbfcff 0%, #f5f8fd 100%);
}

.overview-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.overview-summary {
  color: #56657f;
  font-size: 12px;
  font-weight: 700;
}

.overview-pager {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-size-field {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.page-jump-field {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.page-size-field select {
  min-width: 78px;
}

.page-jump-field input {
  min-width: 78px;
}

.overview-table-wrap {
  min-height: 0;
  overflow: auto;
}

.select-reset,
input,
select,
.primary-btn,
.outline-btn {
  width: 100%;
  border-radius: 10px;
  font: inherit;
}

input,
select {
  border: 1px solid var(--line-strong);
  padding: 6px 10px;
  background: #fff;
}

.primary-btn {
  border: 1px solid var(--green);
  background: linear-gradient(180deg, color-mix(in srgb, var(--green) 80%, white) 0%, var(--green) 100%);
  color: #fff;
  font-weight: 700;
  padding: 8px 14px;
  min-height: 36px;
  box-shadow: 0 8px 18px rgba(34, 169, 110, 0.18);
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
.outline-btn:hover {
  transform: translateY(-1px);
}

.primary-btn:hover {
  box-shadow: 0 10px 22px rgba(34, 169, 110, 0.24);
  filter: brightness(1.02);
}

.outline-btn:hover {
  border-color: #c0cad9;
  box-shadow: 0 4px 12px rgba(28, 47, 84, 0.08);
}

.primary-btn:active,
.outline-btn:active {
  transform: translateY(0);
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

.overview-table {
  table-layout: fixed;
}

.grid-table th,
.grid-table td {
  border-bottom: 1px solid var(--line);
  padding: 4px 8px;
  text-align: left;
  font-size: 12px;
}

.grid-table th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: #f7f9fd;
  color: #52607b;
  font-weight: 700;
}

.grid-table tbody tr:last-child td {
  border-bottom: none;
}

.empty-cell {
  text-align: center;
  color: var(--muted);
}

@media (max-width: 1500px) {
  .overview-fields {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .overview-head {
    flex-direction: column;
  }
}

@media (max-width: 1180px) {
  .overview-fields {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .panel {
    padding: 12px;
  }

  .overview-fields {
    grid-template-columns: 1fr;
  }

  .overview-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .overview-pager {
    flex-wrap: wrap;
    justify-content: space-between;
  }

  .overview-actions {
    justify-content: stretch;
  }

  .overview-actions button {
    flex: 1 1 0;
  }
}

@media (max-width: 640px) {
  .overview-head h2 {
    font-size: 16px;
  }

  .advanced-toggle,
  .overview-actions button {
    width: 100%;
  }

  .overview-secondary-row,
  .overview-actions {
    flex-direction: column;
  }

  .overview-pager,
  .page-size-field,
  .page-jump-field {
    width: 100%;
  }

  .page-size-field,
  .page-jump-field {
    justify-content: space-between;
  }

  .overview-pager .outline-btn {
    flex: 1 1 120px;
  }
}
</style>
