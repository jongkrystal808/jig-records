<script setup lang="ts">
import UiSectionHeader from "@/components/UiSectionHeader.vue";
import type { MaterialTransaction } from "@/types";
import { formatLocalDate } from "@/utils/date";

const props = defineProps<{
  transaction: MaterialTransaction | null;
  processing: boolean;
  embeddedForm?: boolean;
  embeddedWorkbench?: boolean;
  workbenchSidePanel?: boolean;
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

function displayTransactionNo(value: string | null | undefined): string {
  return value?.trim() || "（無單號）";
}
</script>

<template>
  <article class="panel detail-panel" :class="{ 'form-detail-panel': embeddedForm, 'workbench-ledger-detail': embeddedWorkbench, 'workbench-ledger-side': workbenchSidePanel }" data-tour="master-ledger-detail">
    <UiSectionHeader
      v-if="!embeddedForm && !embeddedWorkbench"
      class="panel-head"
      title="案件詳細"
      :description="transaction ? displayTransactionNo(transaction.transaction_no) : '尚未選擇案件'"
    >
      <template #actions>
        <div class="action-group">
          <button class="outline-btn small" type="button" :disabled="processing" @click="onReload">重載</button>
          <button class="outline-btn small warn-btn" type="button" :disabled="processing" @click="onRecalculate">一鍵重算</button>
          <button class="danger-btn small" type="button" :disabled="processing || !transaction" @click="onReverse">撤回此案件</button>
        </div>
      </template>
    </UiSectionHeader>

    <header v-else-if="embeddedForm" class="form-detail-bar">
      <div class="form-detail-title">
        <strong>案件詳細</strong>
        <span>{{ transaction ? displayTransactionNo(transaction.transaction_no) : "尚未選擇案件" }}</span>
      </div>
      <div class="action-group">
        <button class="outline-btn small" type="button" :disabled="processing" @click="onReload">重載</button>
        <button class="outline-btn small warn-btn" type="button" :disabled="processing" @click="onRecalculate">一鍵重算</button>
        <button class="danger-btn small" type="button" :disabled="processing || !transaction" @click="onReverse">撤回此案件</button>
      </div>
    </header>

    <header v-else class="workbench-ledger-detail-bar">
      <div class="workbench-ledger-detail-title">
        <span>SELECTED CASE</span>
        <strong>{{ transaction ? displayTransactionNo(transaction.transaction_no) : "尚未選擇案件" }}</strong>
      </div>
      <div class="action-group">
        <button class="outline-btn small" type="button" :disabled="processing" @click="onReload">重載</button>
        <button class="outline-btn small warn-btn" type="button" :disabled="processing" @click="onRecalculate">一鍵重算</button>
        <button class="danger-btn small" type="button" :disabled="processing || !transaction" @click="onReverse">撤回案件</button>
      </div>
    </header>

    <div v-if="!transaction" class="empty-state">請從中間案件清單選擇一筆帳目。</div>

    <template v-else>
      <div class="summary-grid" :class="{ 'form-summary-grid': embeddedForm, 'workbench-ledger-summary': embeddedWorkbench, 'workbench-side-summary': workbenchSidePanel }">
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

      <label class="note-field" :class="{ 'form-note-field': embeddedForm, 'workbench-ledger-note': embeddedWorkbench }">
        <span>案件備註</span>
        <textarea :value="transaction.note || ''" :rows="embeddedForm ? 2 : 3" disabled />
      </label>

      <div v-if="workbenchSidePanel" class="workbench-ledger-item-list" aria-label="案件治具明細">
        <article v-for="(item, index) in transaction.items" :key="`${transaction.id}-${item.fixture_id}-${index}`">
          <header><strong>{{ item.fixture_code }}</strong><span>{{ item.quantity }} pcs</span></header>
          <dl>
            <div><dt>識別碼</dt><dd>{{ item.identifier || "-" }}</dd></div>
            <div><dt>歸屬</dt><dd>{{ item.ownership_type === "self_purchased" ? "自購" : "客供" }}</dd></div>
            <div v-if="item.note"><dt>備註</dt><dd>{{ item.note }}</dd></div>
          </dl>
        </article>
      </div>

      <div v-else class="table-scroll">
        <table class="data-table" :class="{ 'form-data-table': embeddedForm, 'workbench-ledger-detail-table': embeddedWorkbench }">
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

.form-detail-panel {
  grid-template-rows: auto auto auto minmax(0, 1fr);
  gap: 0;
  overflow: hidden;
  padding: 0;
  border-color: #c3d2e5;
  border-radius: 0;
}

.form-detail-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 40px;
  padding: 6px 9px;
  border-bottom: 1px solid #c3d2e5;
  background: #eef4fb;
}

.form-detail-title {
  display: flex;
  align-items: baseline;
  gap: 8px;
  min-width: 0;
}

.form-detail-title strong {
  color: #29476d;
  font-size: 0.82rem;
}

.form-detail-title span {
  overflow: hidden;
  color: var(--muted);
  font-size: 0.72rem;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.form-detail-panel .empty-state {
  min-height: 220px;
  margin: 10px;
  border-radius: 4px;
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

.form-summary-grid {
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0;
  margin: 10px 10px 0;
  border: 1px solid var(--line);
}

.form-summary-grid .summary-card {
  min-height: 58px;
  padding: 7px 8px;
  border: 0;
  border-right: 1px solid var(--line);
  border-radius: 0;
  background: #f7faff;
}

.form-summary-grid .summary-card:last-child {
  border-right: 0;
}

.form-summary-grid .summary-card strong {
  color: #203f67;
  font-size: 0.88rem;
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

.form-note-field {
  display: grid;
  grid-template-columns: 82px minmax(0, 1fr);
  align-items: stretch;
  gap: 0;
  margin: 0 10px 10px;
  border: 1px solid var(--line);
  border-top: 0;
}

.form-note-field span {
  display: flex;
  align-items: center;
  padding: 7px 8px;
  border-right: 1px solid var(--line);
  color: #314e73;
  background: #eef4fb;
}

.form-note-field textarea {
  min-height: 52px;
  border: 0;
  border-radius: 0;
  background: #fff;
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

.form-detail-panel > .table-scroll {
  border-top: 1px solid #c3d2e5;
}

.form-data-table {
  min-width: 660px;
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
  color: #314e73;
  background: #dce9f8;
  font-weight: 800;
}

.form-data-table tbody tr:nth-child(even) {
  background: #f7faff;
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

.form-detail-panel .outline-btn,
.form-detail-panel .danger-btn {
  min-height: 28px;
  padding: 4px 8px;
  border-radius: 4px;
  background-image: none;
}

.form-detail-panel .outline-btn {
  background: #fff;
}

.form-detail-panel .outline-btn.warn-btn {
  background: #fff7eb;
}

.form-detail-panel .danger-btn {
  background: #bd3e3e;
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

.workbench-ledger-side {
  display: grid;
  grid-template-rows: auto auto auto minmax(0, 1fr);
  gap: 0;
  padding: 0;
  overflow: visible;
  border: 0;
  border-radius: 0;
}

.workbench-ledger-side .empty-state {
  min-height: 108px;
  margin: 10px;
  padding: 14px;
  font-size: 0.72rem;
  text-align: center;
}

.workbench-side-summary {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 7px;
  margin: 10px 10px 0;
}

.workbench-side-summary .summary-card {
  min-height: 58px;
  padding: 8px;
  border-radius: 9px;
}

.workbench-side-summary .summary-card:first-child {
  border-left: 3px solid #2f6ee5;
}

.workbench-ledger-side .workbench-ledger-note {
  margin: 9px 10px;
}

.workbench-ledger-item-list {
  display: grid;
  max-height: 320px;
  gap: 7px;
  overflow: auto;
  padding: 0 10px 10px;
}

.workbench-ledger-item-list > article {
  padding: 9px;
  border: 1px solid #d5e0ef;
  border-radius: 10px;
  background: #fbfcff;
}

.workbench-ledger-item-list header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 7px;
}

.workbench-ledger-item-list header strong {
  color: #245c9f;
  font-size: 0.78rem;
}

.workbench-ledger-item-list header span {
  padding: 3px 7px;
  border-radius: 999px;
  color: #245c9f;
  background: #eaf2ff;
  font-size: 0.67rem;
  font-weight: 800;
}

.workbench-ledger-item-list dl {
  display: grid;
  gap: 4px;
  margin: 0;
}

.workbench-ledger-item-list dl > div {
  display: grid;
  grid-template-columns: 58px minmax(0, 1fr);
  gap: 7px;
  font-size: 0.68rem;
}

.workbench-ledger-item-list dt {
  color: #6a7890;
}

.workbench-ledger-item-list dd {
  min-width: 0;
  margin: 0;
  overflow-wrap: anywhere;
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

  .form-detail-bar {
    align-items: flex-start;
    flex-direction: column;
  }

  .form-summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .form-summary-grid .summary-card {
    border-right: 1px solid var(--line);
    border-bottom: 1px solid var(--line);
  }

  .form-note-field {
    grid-template-columns: 1fr;
  }

  .form-note-field span {
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }
}
</style>
