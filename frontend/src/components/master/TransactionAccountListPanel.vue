<script setup lang="ts">
import UiSectionHeader from "@/components/UiSectionHeader.vue";
import type { MaterialTransaction } from "@/types";
import { formatLocalDate } from "@/utils/date";

const props = defineProps<{
  rows: MaterialTransaction[];
  selectedTransactionId: number | null;
  loading: boolean;
  keyword: string;
  transactionType: "all" | "receipt" | "return";
  page: number;
  totalPages: number;
  onKeywordChange: (value: string) => void;
  onTransactionTypeChange: (value: "all" | "receipt" | "return") => void;
  onSelectRow: (id: number) => void;
  onPreviousPage: () => void;
  onNextPage: () => void;
}>();

function summarizeQuantity(row: MaterialTransaction): number {
  return row.items.reduce((sum, item) => sum + item.quantity, 0);
}
</script>

<template>
  <article class="panel list-panel">
    <UiSectionHeader class="panel-head" title="收退料帳目管理" :description="`${rows.length} 筆案件`" />

    <div v-if="rows.length > 0" class="list-footer">
      <span>第 {{ page }} / {{ totalPages }} 頁，共 {{ rows.length }} 筆案件</span>
      <div class="pager-actions">
        <button class="outline-btn small" type="button" :disabled="loading || page <= 1" @click="onPreviousPage">上一頁</button>
        <button class="outline-btn small" type="button" :disabled="loading || page >= totalPages" @click="onNextPage">下一頁</button>
      </div>
    </div>

    <div class="list-toolbar">
      <input
        :value="keyword"
        placeholder="搜尋單號 / 操作人 / 治具編號"
        :disabled="loading"
        @input="onKeywordChange(($event.target as HTMLInputElement).value)"
      />
      <select
        :value="transactionType"
        :disabled="loading"
        @change="onTransactionTypeChange(($event.target as HTMLSelectElement).value as 'all' | 'receipt' | 'return')"
      >
        <option value="all">全部帳目</option>
        <option value="receipt">只看收料</option>
        <option value="return">只看退料</option>
      </select>
    </div>

    <div v-if="loading" class="loading-banner">帳目資料載入中...</div>

    <div class="table-scroll">
      <table class="data-table">
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
            @click="onSelectRow(row.id)"
          >
            <td>{{ row.transaction_no }}</td>
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
  grid-template-columns: minmax(0, 1fr) 140px;
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
    grid-template-columns: 1fr;
  }
}
</style>
