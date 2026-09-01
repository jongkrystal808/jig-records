<script setup lang="ts">
import InlineSpinner from "@/components/common/InlineSpinner.vue";
import type { SearchResult, StockStatus } from "@/types";

defineProps<{
  rows: SearchResult[];
  total: number;
  loading: boolean;
  loadingMore: boolean;
  hasMore: boolean;
  formatCount: (value: number) => string;
  stockTone: (status: StockStatus | undefined) => "normal" | "warn" | "danger" | "muted";
}>();

const emit = defineEmits<{
  select: [row: SearchResult];
  loadMore: [];
}>();

function stockStatusLabel(status: StockStatus | null | undefined): string {
  if (status === "out_of_stock") return "無庫存";
  if (status === "low_stock") return "低庫存";
  return "正常";
}
</script>

<template>
  <section class="fixture-overview-panel" aria-labelledby="fixture-overview-title">
    <header class="overview-head">
      <div>
        <span class="eyebrow">Fixture overview</span>
        <h2 id="fixture-overview-title">治具總清單</h2>
        <p>未輸入查詢條件時顯示客戶範圍內的簡略治具總覽。</p>
      </div>
      <span class="overview-count">共 {{ formatCount(total) }} 筆</span>
    </header>

    <div v-if="loading" class="overview-state">
      <InlineSpinner label="載入治具總覽..." />
    </div>

    <div v-else-if="rows.length === 0" class="overview-state empty">
      <strong>目前沒有治具資料</strong>
      <span>建立治具後，會自動顯示在這份總清單。</span>
    </div>

    <template v-else>
      <div class="overview-table-wrap">
        <table class="overview-table">
          <thead>
            <tr>
              <th>治具編號</th>
              <th>名稱</th>
              <th class="number-cell">目前庫存</th>
              <th>庫存狀態</th>
              <th>儲位</th>
              <th>資料狀態</th>
              <th><span class="sr-only">操作</span></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in rows" :key="row.reference_id">
              <td><strong>{{ row.title }}</strong></td>
              <td>{{ row.subtitle || "-" }}</td>
              <td class="number-cell">{{ formatCount(row.stock_qty ?? 0) }}</td>
              <td>
                <span class="status-badge" :class="stockTone(row.stock_status ?? undefined)">
                  {{ stockStatusLabel(row.stock_status) }}
                </span>
              </td>
              <td>{{ row.location_code || "-" }}</td>
              <td>
                <span class="data-status" :class="row.is_active ? 'active' : 'inactive'">
                  {{ row.is_active ? "啟用" : "停用" }}
                </span>
              </td>
              <td class="action-cell">
                <button type="button" :aria-label="`查看治具 ${row.title}`" @click="emit('select', row)">
                  查看
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="overview-mobile-list" aria-label="治具總清單">
        <button
          v-for="row in rows"
          :key="row.reference_id"
          class="overview-mobile-card"
          type="button"
          :aria-label="`查看治具 ${row.title} 詳情`"
          @click="emit('select', row)"
        >
          <span class="mobile-card-head">
            <span class="mobile-card-identity">
              <strong>{{ row.title }}</strong>
              <span>{{ row.subtitle || "-" }}</span>
            </span>
            <span class="status-badge" :class="stockTone(row.stock_status ?? undefined)">
              {{ stockStatusLabel(row.stock_status) }}
            </span>
          </span>
          <span class="mobile-card-details">
            <span>
              <small>目前庫存</small>
              <strong class="mobile-stock">{{ formatCount(row.stock_qty ?? 0) }}</strong>
            </span>
            <span>
              <small>儲位</small>
              <strong>{{ row.location_code || "-" }}</strong>
            </span>
          </span>
        </button>
      </div>

      <footer v-if="hasMore" class="overview-actions">
        <span>已顯示 {{ formatCount(rows.length) }} / {{ formatCount(total) }} 筆</span>
        <button type="button" :disabled="loadingMore" @click="emit('loadMore')">
          {{ loadingMore ? "載入中..." : "載入更多" }}
        </button>
      </footer>
    </template>
  </section>
</template>

<style scoped>
.fixture-overview-panel {
  display: grid;
  gap: 16px;
  padding: 18px;
}

.overview-head,
.overview-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.eyebrow {
  color: var(--blue);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h2 {
  margin: 4px 0 0;
  color: #22314a;
  font-size: 20px;
}

p {
  margin: 6px 0 0;
  color: #64738b;
  font-size: 13px;
}

.overview-count,
.data-status,
.status-badge {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  white-space: nowrap;
}

.overview-count {
  color: var(--tone-info);
  background: color-mix(in srgb, var(--blue-soft) 82%, white);
}

.overview-table-wrap {
  overflow-x: auto;
  border: 1px solid var(--line);
  border-radius: 14px;
}

.overview-table {
  width: 100%;
  min-width: 780px;
  border-collapse: collapse;
}

.overview-mobile-list {
  display: none;
}

th,
td {
  padding: 11px 12px;
  border-bottom: 1px solid var(--line);
  color: #44536a;
  font-size: 13px;
  text-align: left;
}

th {
  color: #59677e;
  background: color-mix(in srgb, var(--blue-soft) 42%, white);
  font-size: 12px;
}

tbody tr:last-child td {
  border-bottom: 0;
}

tbody tr:hover {
  background: color-mix(in srgb, var(--blue-soft) 30%, white);
}

td strong {
  color: #22314a;
}

.number-cell {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.status-badge.normal {
  color: #247044;
  background: #e8f5ed;
}

.status-badge.warn {
  color: #a85b00;
  background: #fff0dc;
}

.status-badge.danger {
  color: #a13535;
  background: #fde8e8;
}

.status-badge.muted,
.data-status.inactive {
  color: #68758a;
  background: #eef1f5;
}

.data-status.active {
  color: var(--tone-info);
  background: color-mix(in srgb, var(--blue-soft) 82%, white);
}

.action-cell {
  text-align: right;
}

.action-cell button,
.overview-actions button {
  min-height: 34px;
  padding: 7px 13px;
  border: 1px solid color-mix(in srgb, var(--blue) 24%, var(--line));
  border-radius: 10px;
  color: var(--tone-info);
  background: #fff;
  font-weight: 800;
}

.overview-actions {
  color: #64738b;
  font-size: 12px;
}

.overview-state {
  min-height: 160px;
  display: grid;
  place-items: center;
}

.overview-state.empty {
  gap: 6px;
  align-content: center;
  color: #64738b;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 680px) {
  .fixture-overview-panel {
    padding: 14px;
  }

  .overview-head,
  .overview-actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .overview-actions button {
    width: 100%;
  }

  .overview-table-wrap {
    display: none;
  }

  .overview-mobile-list {
    display: grid;
    gap: 10px;
  }

  .overview-mobile-card {
    width: 100%;
    display: grid;
    gap: 12px;
    padding: 14px;
    border: 1px solid var(--line);
    border-radius: 14px;
    color: #44536a;
    background: #fff;
    font: inherit;
    text-align: left;
  }

  .overview-mobile-card:active {
    background: color-mix(in srgb, var(--blue-soft) 30%, white);
  }

  .overview-mobile-card:focus-visible {
    outline: 3px solid color-mix(in srgb, var(--blue) 35%, transparent);
    outline-offset: 2px;
  }

  .mobile-card-head,
  .mobile-card-details,
  .mobile-card-identity,
  .mobile-card-details > span {
    display: flex;
  }

  .mobile-card-head {
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
  }

  .mobile-card-identity,
  .mobile-card-details > span {
    min-width: 0;
    flex-direction: column;
    gap: 3px;
  }

  .mobile-card-identity strong {
    color: #22314a;
    font-size: 15px;
    overflow-wrap: anywhere;
  }

  .mobile-card-identity > span {
    color: #64738b;
    font-size: 13px;
    overflow-wrap: anywhere;
  }

  .mobile-card-details {
    display: grid;
    grid-template-columns: minmax(82px, auto) minmax(0, 1fr);
    gap: 16px;
    padding-top: 11px;
    border-top: 1px solid var(--line);
  }

  .mobile-card-details small {
    color: #718096;
    font-size: 11px;
  }

  .mobile-card-details strong {
    color: #34435a;
    font-size: 13px;
    overflow-wrap: anywhere;
  }

  .mobile-card-details .mobile-stock {
    color: #22314a;
    font-size: 16px;
    font-variant-numeric: tabular-nums;
  }
}
</style>
