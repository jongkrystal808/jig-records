<script setup lang="ts">
import UiSectionHeader from "@/components/UiSectionHeader.vue";
import type { MaterialTransaction } from "@/types";
import { formatLocalDate } from "@/utils/date";

const props = defineProps<{
  transaction: MaterialTransaction | null;
  processing: boolean;
  onReload: () => void | Promise<void>;
  onRecalculate: () => void | Promise<void>;
  onReverse: () => void | Promise<void>;
}>();

function summarizeQuantity(row: MaterialTransaction | null): number {
  if (!row) {
    return 0;
  }
  return row.items.reduce((sum, item) => sum + item.quantity, 0);
}
</script>

<template>
  <article class="panel detail-panel">
    <UiSectionHeader
      class="panel-head"
      title="案件詳細"
      :description="transaction ? transaction.transaction_no : '尚未選擇案件'"
    >
      <template #actions>
        <div class="action-group">
          <button class="outline-btn small" type="button" :disabled="processing" @click="onReload">重載</button>
          <button class="outline-btn small warn-btn" type="button" :disabled="processing" @click="onRecalculate">一鍵重算</button>
          <button class="danger-btn small" type="button" :disabled="processing || !transaction" @click="onReverse">撤回此案件</button>
        </div>
      </template>
    </UiSectionHeader>

    <div v-if="!transaction" class="empty-state">請先從左側選擇要管理的收退料案件。</div>

    <template v-else>
      <div class="summary-grid">
        <div class="summary-card">
          <span class="summary-label">類型</span>
          <strong>{{ transaction.transaction_type === "receipt" ? "收料" : "退料" }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">日期</span>
          <strong>{{ formatLocalDate(transaction.occurred_at) }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">操作人</span>
          <strong>{{ transaction.created_by }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">明細筆數</span>
          <strong>{{ transaction.items.length }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">總數量</span>
          <strong>{{ summarizeQuantity(transaction) }}</strong>
        </div>
      </div>

      <label class="note-field">
        <span>案件備註</span>
        <textarea :value="transaction.note || ''" rows="3" disabled />
      </label>

      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th>治具 ID</th>
              <th>治具編號</th>
              <th>識別碼</th>
              <th>數量</th>
              <th>歸屬</th>
              <th>備註</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in transaction.items" :key="`${transaction.id}-${item.fixture_id}-${index}`">
              <td>{{ item.fixture_id ?? "已刪除" }}</td>
              <td>{{ item.fixture_code }}</td>
              <td>{{ item.identifier || "-" }}</td>
              <td>{{ item.quantity }}</td>
              <td>{{ item.ownership_type === "self_purchased" ? "自購" : "客供" }}</td>
              <td>{{ item.note || "-" }}</td>
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

.detail-panel {
  display: grid;
  grid-template-rows: auto auto auto minmax(0, 1fr);
  gap: 10px;
  overflow: auto;
}

.action-group {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.empty-state {
  display: grid;
  place-items: center;
  min-height: 180px;
  border: 1px dashed #d6dfec;
  border-radius: 10px;
  color: #5d6d89;
  background: #fbfcff;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
}

.summary-card {
  display: grid;
  gap: 4px;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}

.summary-label,
.note-field span {
  color: #5d6d89;
  font-size: 12px;
  font-weight: 700;
}

.note-field {
  display: grid;
  gap: 6px;
}

textarea {
  width: 100%;
  border: 1px solid var(--line-strong);
  border-radius: 8px;
  padding: 8px 10px;
  background: #f7f9fd;
  font: inherit;
  font-size: 12px;
  resize: vertical;
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

.outline-btn,
.danger-btn {
  border-radius: 10px;
  font-weight: 700;
  cursor: pointer;
  min-height: 30px;
  font-size: 12px;
  padding: 6px 10px;
}

.outline-btn {
  border: 1px solid var(--line-strong);
  background: linear-gradient(180deg, #ffffff 0%, #f7f9fd 100%);
  color: #5b677d;
}

.outline-btn.warn-btn {
  border-color: #f0c287;
  color: #9a4d00;
  background: linear-gradient(180deg, #fff7eb 0%, #ffefdc 100%);
}

.danger-btn {
  border: 1px solid #d35656;
  color: #fff;
  background: linear-gradient(180deg, #e16f6f 0%, #bf3f3f 100%);
}

.outline-btn:disabled,
.danger-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

@media (max-width: 1100px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
