<script setup lang="ts">
import UiSectionHeader from "@/components/UiSectionHeader.vue";
import UiMultiSelect from "@/components/common/UiMultiSelect.vue";
import type { AppUser, Customer, Fixture, MachineModel, Station } from "@/types";
import { fallbackText } from "@/utils/display";

type MasterTab = "fixture" | "model" | "station" | "customer" | "user";

const props = defineProps<{
  activeTab: MasterTab;
  tabTitle: string;
  currentRowsLength: number;
  keyword: string;
  searchPlaceholder: string;
  loading: boolean;
  statusFilter: Array<"active" | "inactive">;
  canCreate: boolean;
  emptyStateMessage: string;
  listPage: number;
  listTotalPages: number;
  pagedFixtureRows: Fixture[];
  pagedModelRows: MachineModel[];
  pagedStationRows: Station[];
  pagedCustomerRows: Customer[];
  pagedUserRows: AppUser[];
  selectedFixtureId: number | null;
  selectedModelId: number | null;
  selectedStationId: number | null;
  selectedCustomerRowId: number | null;
  selectedUserId: number | null;
  onKeywordChange: (value: string) => void;
  onStatusFilterChange: (value: Array<"active" | "inactive">) => void;
  onStartCreate: () => void;
  onSelectRow: (id: number) => void;
  onPreviousPage: () => void;
  onNextPage: () => void;
}>();

function handleRowKeydown(event: KeyboardEvent, id: number): void {
  if (event.key !== "Enter" && event.key !== " ") {
    return;
  }
  event.preventDefault();
  props.onSelectRow(id);
}
</script>

<template>
  <article class="panel list-panel" data-tour="detailed-master-list">
    <UiSectionHeader class="panel-head" :title="`${tabTitle}清單`" />

    <div v-if="currentRowsLength > 0" class="list-footer" data-tour="detailed-master-pager">
      <span>第 {{ listPage }} / {{ listTotalPages }} 頁，共 {{ currentRowsLength }} 筆</span>
      <div class="pager-actions">
        <button class="outline-btn small" type="button" :disabled="loading || listPage <= 1" @click="onPreviousPage">上一頁</button>
        <button class="outline-btn small" type="button" :disabled="loading || listPage >= listTotalPages" @click="onNextPage">下一頁</button>
      </div>
    </div>

    <div class="list-toolbar" data-tour="master-list-toolbar">
      <input :value="keyword" :placeholder="searchPlaceholder" :disabled="loading" @input="onKeywordChange(($event.target as HTMLInputElement).value)" />
      <UiMultiSelect v-if="activeTab !== 'customer'" :model-value="statusFilter" label="狀態" placeholder="全部狀態" :options="[{ value: 'active', label: '啟用中' }, { value: 'inactive', label: '停用' }]" @update:model-value="onStatusFilterChange($event as Array<'active' | 'inactive'>)" />
      <button class="primary-btn" type="button" :disabled="loading || !canCreate" @click="onStartCreate">+ 新增{{ tabTitle }}</button>
    </div>

    <div v-if="loading" class="loading-banner">資料載入中，請稍候...</div>

    <div class="table-scroll" data-tour="master-list-table">
      <table class="data-table">
        <thead>
          <tr v-if="activeTab === 'fixture'"><th>治具編號</th><th>治具名稱</th><th>水位</th><th>產線儲位</th><th>部門儲位</th><th>狀態</th></tr>
          <tr v-else-if="activeTab === 'model'"><th>機種編號</th><th>機種名稱</th><th>狀態</th></tr>
          <tr v-else-if="activeTab === 'station'"><th>站點編號</th><th>站點名稱</th><th>狀態</th></tr>
          <tr v-else-if="activeTab === 'customer'"><th>客戶代碼</th><th>客戶名稱</th></tr>
          <tr v-else><th>帳號</th><th>Email</th><th>顯示名稱</th><th>角色</th><th>狀態</th></tr>
        </thead>

        <tbody v-if="activeTab === 'fixture'">
          <tr
            v-for="row in pagedFixtureRows"
            :key="row.id"
            :class="{ selected: selectedFixtureId === row.id }"
            tabindex="0"
            @click="onSelectRow(row.id)"
            @keydown="handleRowKeydown($event, row.id)"
          >
            <td>{{ row.code }}</td><td>{{ row.name }}</td><td>{{ row.min_stock_qty }}</td><td>{{ row.line_storage_location || "-" }}</td><td>{{ row.department_storage_location || "-" }}</td><td><span class="status-pill" :class="row.is_active ? 'active' : 'inactive'">{{ row.is_active ? "啟用中" : "停用" }}</span></td>
          </tr>
          <tr v-if="!loading && currentRowsLength === 0">
            <td colspan="6" class="empty-cell">{{ emptyStateMessage }}</td>
          </tr>
        </tbody>
        <tbody v-else-if="activeTab === 'model'">
          <tr
            v-for="row in pagedModelRows"
            :key="row.id"
            :class="{ selected: selectedModelId === row.id }"
            tabindex="0"
            @click="onSelectRow(row.id)"
            @keydown="handleRowKeydown($event, row.id)"
          >
            <td>{{ row.code }}</td><td>{{ row.name }}</td><td><span class="status-pill" :class="row.is_active ? 'active' : 'inactive'">{{ row.is_active ? "啟用中" : "停用" }}</span></td>
          </tr>
          <tr v-if="!loading && currentRowsLength === 0">
            <td colspan="3" class="empty-cell">{{ emptyStateMessage }}</td>
          </tr>
        </tbody>
        <tbody v-else-if="activeTab === 'station'">
          <tr
            v-for="row in pagedStationRows"
            :key="row.id"
            :class="{ selected: selectedStationId === row.id }"
            tabindex="0"
            @click="onSelectRow(row.id)"
            @keydown="handleRowKeydown($event, row.id)"
          >
            <td>{{ row.code }}</td><td>{{ row.name }}</td><td><span class="status-pill" :class="row.is_active ? 'active' : 'inactive'">{{ row.is_active ? "啟用中" : "停用" }}</span></td>
          </tr>
          <tr v-if="!loading && currentRowsLength === 0">
            <td colspan="3" class="empty-cell">{{ emptyStateMessage }}</td>
          </tr>
        </tbody>
        <tbody v-else-if="activeTab === 'customer'">
          <tr
            v-for="row in pagedCustomerRows"
            :key="row.id"
            :class="{ selected: selectedCustomerRowId === row.id }"
            tabindex="0"
            @click="onSelectRow(row.id)"
            @keydown="handleRowKeydown($event, row.id)"
          >
            <td>{{ row.code }}</td><td>{{ row.name }}</td>
          </tr>
          <tr v-if="!loading && currentRowsLength === 0">
            <td colspan="2" class="empty-cell">{{ emptyStateMessage }}</td>
          </tr>
        </tbody>
        <tbody v-else>
          <tr
            v-for="row in pagedUserRows"
            :key="row.id"
            :class="{ selected: selectedUserId === row.id }"
            tabindex="0"
            @click="onSelectRow(row.id)"
            @keydown="handleRowKeydown($event, row.id)"
          >
            <td>{{ row.username }}</td><td>{{ fallbackText(row.email) }}</td><td>{{ row.display_name }}</td><td>{{ row.role }}</td><td><span class="status-pill" :class="row.is_active ? 'active' : 'inactive'">{{ row.is_active ? "啟用中" : "停用" }}</span></td>
          </tr>
          <tr v-if="!loading && currentRowsLength === 0">
            <td colspan="5" class="empty-cell">{{ emptyStateMessage }}</td>
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
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: hidden;
  min-height: 0;
}

.list-toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 150px 128px;
  gap: 8px;
  align-items: start;
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
  flex: 1 1 auto;
  min-width: 0;
  min-height: 0;
  overflow: auto;
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
  padding: 3px 8px;
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
  background: #edf3ff;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 64px;
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 700;
}

.status-pill.active {
  color: var(--green);
  background: var(--green-soft);
}

.status-pill.inactive {
  color: var(--red);
  background: var(--red-soft);
}

.list-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  color: #5d6d89;
  font-size: 12px;
}

.pager-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.primary-btn,
.outline-btn {
  border-radius: 10px;
  font-weight: 700;
  cursor: pointer;
  min-height: 30px;
  font-size: 12px;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease, filter 0.15s ease;
}

.primary-btn {
  border: 1px solid var(--green);
  background: linear-gradient(180deg, #4cc36b 0%, #2ea54e 100%);
  color: #fff;
  padding: 6px 10px;
  box-shadow: 0 6px 14px rgba(46, 165, 78, 0.16);
}

.outline-btn {
  border: 1px solid var(--line-strong);
  background: linear-gradient(180deg, #ffffff 0%, #f7f9fd 100%);
  color: #5b677d;
  padding: 6px 10px;
}

.outline-btn.small {
  padding: 5px 8px;
  min-height: 28px;
}

.primary-btn:hover,
.outline-btn:hover {
  transform: translateY(-1px);
}

.primary-btn:hover {
  box-shadow: 0 10px 22px rgba(46, 165, 78, 0.24);
  filter: brightness(1.02);
}

.outline-btn:hover {
  border-color: #c0cad9;
  box-shadow: 0 4px 12px rgba(28, 47, 84, 0.08);
}

.primary-btn:disabled,
.outline-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.primary-btn:active,
.outline-btn:active {
  transform: translateY(0);
}

@media (max-width: 900px) {
  .list-toolbar {
    grid-template-columns: 1fr;
  }
}
</style>
