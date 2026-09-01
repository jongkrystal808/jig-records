<script setup lang="ts">
import UiSectionHeader from "@/components/UiSectionHeader.vue";
import UiMultiSelect from "@/components/common/UiMultiSelect.vue";
import type { MaterialTransaction } from "@/types";
import { formatLocalDate } from "@/utils/date";

const props = defineProps<{
  rows: MaterialTransaction[];
  selectedTransactionId: number | null;
  loading: boolean;
  transactionNo: string;
  createdBy: string;
  fixtureCode: string;
  transactionType: Array<"receipt" | "return">;
  page: number;
  pageSize: number;
  totalPages: number;
  total: number;
  embeddedForm?: boolean;
  embeddedWorkbench?: boolean;
  onTransactionNoChange: (value: string) => void;
  onCreatedByChange: (value: string) => void;
  onFixtureCodeChange: (value: string) => void;
  onTransactionTypeChange: (value: Array<"receipt" | "return">) => void;
  onPageSizeChange: (value: number) => void;
  onSelectRow: (id: number) => void;
  onPreviousPage: () => void;
  onNextPage: () => void;
}>();

function summarizeQuantity(row: MaterialTransaction): number {
  return row.items.reduce((sum, item) => sum + item.quantity, 0);
}

function displayTransactionNo(value: string | null): string {
  return value?.trim() || "（無單號）";
}
</script>

<template>
  <article class="panel list-panel" :class="{ 'form-list-panel': embeddedForm, 'workbench-ledger-list': embeddedWorkbench }" data-tour="master-ledger-list">
    <UiSectionHeader v-if="!embeddedForm && !embeddedWorkbench" class="panel-head" title="收退料帳目管理" :description="`共 ${total} 筆案件`" />

    <div v-if="!embeddedForm && !embeddedWorkbench && total > 0" class="list-footer">
      <span>第 {{ page }} / {{ totalPages }} 頁，共 {{ total }} 筆案件</span>
      <div class="pager-actions">
        <label class="page-size-field">
          <span>每頁</span>
          <select
            :value="String(pageSize)"
            :disabled="loading"
            @change="onPageSizeChange(Number(($event.target as HTMLSelectElement).value))"
          >
            <option value="12">12</option>
            <option value="25">25</option>
            <option value="50">50</option>
          </select>
        </label>
        <button class="outline-btn small" type="button" :disabled="loading || page <= 1" @click="onPreviousPage">上一頁</button>
        <button class="outline-btn small" type="button" :disabled="loading || page >= totalPages" @click="onNextPage">下一頁</button>
      </div>
    </div>

    <div v-if="!embeddedForm && !embeddedWorkbench" class="list-toolbar" data-tour="master-ledger-filters">
      <input
        :value="transactionNo"
        placeholder="搜尋單號"
        :disabled="loading"
        @input="onTransactionNoChange(($event.target as HTMLInputElement).value)"
      />
      <input
        :value="createdBy"
        placeholder="搜尋操作人"
        :disabled="loading"
        @input="onCreatedByChange(($event.target as HTMLInputElement).value)"
      />
      <input
        :value="fixtureCode"
        placeholder="搜尋治具編號"
        :disabled="loading"
        @input="onFixtureCodeChange(($event.target as HTMLInputElement).value)"
      />
      <UiMultiSelect :model-value="transactionType" label="類型" placeholder="全部帳目" :disabled="loading" :options="[{ value: 'receipt', label: '收料' }, { value: 'return', label: '退料' }]" @update:model-value="onTransactionTypeChange($event as Array<'receipt' | 'return'>)" />
    </div>

    <div v-if="loading" class="loading-banner">帳目資料載入中...</div>

    <div class="table-scroll">
      <table class="data-table" :class="{ 'form-data-table': embeddedForm, 'workbench-ledger-table': embeddedWorkbench }">
        <thead>
          <tr>
            <th>單號</th>
            <th>類型</th>
            <th>日期</th>
            <th>操作人</th>
            <th>筆數</th>
            <th>總數量</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in rows"
            :key="row.id"
            :class="{ selected: selectedTransactionId === row.id }"
            :aria-selected="selectedTransactionId === row.id"
            tabindex="0"
            @click="onSelectRow(row.id)"
            @keydown.enter.prevent="onSelectRow(row.id)"
            @keydown.space.prevent="onSelectRow(row.id)"
          >
            <td>{{ displayTransactionNo(row.transaction_no) }}</td>
            <td>
              <span class="type-pill" :class="row.transaction_type">
                {{ row.transaction_type === "receipt" ? "收料" : "退料" }}
              </span>
            </td>
            <td>{{ formatLocalDate(row.occurred_at) }}</td>
            <td>{{ row.created_by }}</td>
            <td>{{ row.items.length }}</td>
            <td>{{ summarizeQuantity(row) }}</td>
          </tr>
          <tr v-if="!loading && rows.length === 0">
            <td colspan="6" class="empty-cell">目前沒有符合條件的收退料案件</td>
          </tr>
        </tbody>
      </table>
    </div>
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

.list-panel {
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr) auto;
  gap: 8px;
  overflow: auto;
}

.list-toolbar {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

input,
select {
  width: 100%;
  border: 1px solid var(--line-strong);
  border-radius: 8px;
  padding: 5px 8px;
  background: #fff;
  font: inherit;
  font-size: 12px;
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
  padding: 4px 8px;
  text-align: left;
  border-bottom: 1px solid var(--line);
  font-size: 12px;
}

.data-table thead th {
  background: #f7f9fd;
  color: #52607b;
  font-weight: 700;
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.data-table tbody tr:hover {
  background: #f6f9ff;
  cursor: pointer;
}

.data-table tbody tr.selected {
  background: #edf3ff;
}

.data-table tbody tr:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--blue) 62%, white);
  outline-offset: -2px;
}

.form-list-panel {
  display: block;
  overflow: visible;
  padding: 0;
  border: 0;
  border-radius: 0;
}

.form-list-panel .loading-banner {
  border-top: 0;
  border-bottom: 1px solid var(--line);
}

.form-list-panel .table-scroll {
  width: 100%;
  overflow: auto;
}

.form-data-table {
  min-width: 680px;
  border: 0;
  border-radius: 0;
}

.form-data-table th,
.form-data-table td {
  padding: 7px 9px;
  border-right: 1px solid var(--line);
  font-size: 0.75rem;
}

.form-data-table th:last-child,
.form-data-table td:last-child {
  border-right: 0;
}

.form-data-table thead th {
  position: sticky;
  top: 0;
  z-index: 1;
  color: #314e73;
  background: #dce9f8;
  font-weight: 800;
}

.form-data-table tbody tr:nth-child(even) {
  background: #f7faff;
}

.form-data-table tbody tr:hover {
  background: #edf4fc;
}

.form-data-table tbody tr.selected {
  background: #e1edfb;
  box-shadow: inset 3px 0 #4b79b8;
}

.form-data-table .type-pill {
  min-width: 46px;
  border-radius: 4px;
}

.type-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 52px;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 700;
}

.type-pill.receipt {
  color: var(--green);
  background: var(--green-soft);
}

.type-pill.return {
  color: #9a4d00;
  background: #fff0db;
}

.list-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  color: #5d6d89;
  font-size: 12px;
}

.pager-actions {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}

.page-size-field {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #5d6d89;
}

.page-size-field span {
  font-size: 12px;
}

.outline-btn {
  border-radius: 10px;
  border: 1px solid var(--line-strong);
  background: linear-gradient(180deg, #ffffff 0%, #f7f9fd 100%);
  color: #5b677d;
  padding: 6px 10px;
  font-weight: 700;
  cursor: pointer;
  min-height: 30px;
  font-size: 12px;
}

.outline-btn.small {
  padding: 5px 8px;
  min-height: 28px;
}

.outline-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

@media (max-width: 900px) {
  .list-toolbar {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .list-toolbar {
    grid-template-columns: 1fr;
  }
}
</style>
