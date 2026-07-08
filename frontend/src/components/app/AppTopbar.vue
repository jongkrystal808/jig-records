<script setup lang="ts">
import { RouterLink } from "vue-router";
import type { Customer } from "@/types";

type MenuEntry = {
  label: string;
  to: string;
  disabled: boolean;
};

type RecentEntry = {
  id: string;
  occurredAt: string;
  transactionNo: string;
  fixtureCode: string;
  identifier: string;
  quantity: number;
};

type AlertEntry = {
  fixture_id: number;
  fixture_code: string;
  fixture_name: string;
  stock_qty: number;
  min_stock_qty: number;
  stock_status: "low_stock" | "out_of_stock";
};

const props = defineProps<{
  authDisplayName: string;
  selectedCustomerCode: string;
  customers: Customer[];
  selectedCustomerId: number | null;
  todayReceiptQty: number;
  todayReturnQty: number;
  lowStockCount: number;
  recentReceiptEntries: RecentEntry[];
  recentReturnEntries: RecentEntry[];
  lowStockPreviewEntries: AlertEntry[];
  hasMoreLowStockEntries: boolean;
  menuEntries: MenuEntry[];
  moreMenuOpen: boolean;
  formatHoverDate: (value: string) => string;
}>();

const emit = defineEmits<{
  toggleMobileMenu: [];
  openBatch: [];
  openExport: [];
  "update:selectedCustomerId": [value: number | null];
  toggleMoreMenu: [];
  openMenuRoute: [path: string, disabled: boolean];
  openLowStockPage: [];
  logout: [];
}>();

function handleCustomerChange(event: Event): void {
  const value = Number.parseInt((event.target as HTMLSelectElement).value, 10);
  emit("update:selectedCustomerId", Number.isFinite(value) ? value : null);
}

// Keep desktop shell UI isolated so App.vue only orchestrates session, routing, and stats loading.
</script>

<template>
  <header class="topbar">
    <div class="topbar-main">
      <button class="outline-btn mobile-trigger" type="button" @click="emit('toggleMobileMenu')">選單</button>
      <RouterLink class="brand-link" to="/search">
        <span class="brand-mark">JR</span>
        <span class="brand-copy">
          <strong>Jig Record</strong>
          <small>回首頁</small>
        </span>
      </RouterLink>
      <div class="mobile-customer">{{ selectedCustomerCode || "未選客戶" }}</div>
    </div>

    <div class="topbar-primary-action">
      <button class="primary-btn action-btn receipt-btn desktop-receipt-btn" data-tour="inventory-entry-trigger" type="button" @click="emit('openBatch')">治具收/退料</button>
      <button class="primary-btn action-btn receipt-btn desktop-receipt-btn" data-tour="inventory-export-entry-trigger" type="button" @click="emit('openExport')">收退料資訊匯出</button>
    </div>

    <div class="topbar-actions">
      <div class="topbar-info">
        <span class="pill">{{ authDisplayName }}</span>
        <span class="pill">客戶 {{ selectedCustomerCode || "未選" }}</span>
        <div class="pill-hover">
          <span class="pill">今日收料 {{ todayReceiptQty }}</span>
          <div class="hover-panel">
            <div class="hover-head">
              <strong>最近收料 10 筆</strong>
            </div>
            <div v-if="recentReceiptEntries.length > 0" class="hover-list">
              <div v-for="entry in recentReceiptEntries" :key="entry.id" class="hover-row">
                <strong>{{ entry.fixtureCode }}</strong>
                <span>{{ entry.identifier }} / {{ entry.quantity }}</span>
                <small>{{ formatHoverDate(entry.occurredAt) }} / {{ entry.transactionNo }}</small>
              </div>
            </div>
            <div v-else class="hover-empty">今天尚無收料資料</div>
          </div>
        </div>
        <div class="pill-hover">
          <span class="pill">今日退料 {{ todayReturnQty }}</span>
          <div class="hover-panel">
            <div class="hover-head">
              <strong>最近退料 10 筆</strong>
            </div>
            <div v-if="recentReturnEntries.length > 0" class="hover-list">
              <div v-for="entry in recentReturnEntries" :key="entry.id" class="hover-row">
                <strong>{{ entry.fixtureCode }}</strong>
                <span>{{ entry.identifier }} / {{ entry.quantity }}</span>
                <small>{{ formatHoverDate(entry.occurredAt) }} / {{ entry.transactionNo }}</small>
              </div>
            </div>
            <div v-else class="hover-empty">今天尚無退料資料</div>
          </div>
        </div>
        <div class="pill-hover">
          <span class="pill warn">低水位 {{ lowStockCount }}</span>
          <div class="hover-panel">
            <div class="hover-head">
              <strong>低水位治具</strong>
            </div>
            <div v-if="lowStockPreviewEntries.length > 0" class="hover-list">
              <div v-for="entry in lowStockPreviewEntries" :key="entry.fixture_id" class="hover-row">
                <strong>{{ entry.fixture_code }}</strong>
                <span>{{ entry.fixture_name }}</span>
                <small>庫存 {{ entry.stock_qty }} / 最低 {{ entry.min_stock_qty }}</small>
              </div>
            </div>
            <div v-else class="hover-empty">目前沒有低水位治具</div>
            <button v-if="hasMoreLowStockEntries" class="hover-more-btn" type="button" @click="emit('openLowStockPage')">查看更多</button>
          </div>
        </div>
      </div>

      <label class="customer-picker" data-tour="global-customer-picker">
        <select :value="selectedCustomerId ?? undefined" @change="handleCustomerChange">
          <option v-for="customer in customers" :key="customer.id" :value="customer.id">{{ customer.code }} - {{ customer.name }}</option>
        </select>
      </label>

      <div class="more-menu">
        <button class="outline-btn action-btn" data-tour="home-more-menu-trigger" type="button" :aria-expanded="moreMenuOpen" @click="emit('toggleMoreMenu')">更多功能</button>
        <div v-if="moreMenuOpen" class="more-menu-panel">
          <button
            v-for="entry in menuEntries"
            :key="entry.to"
            class="more-menu-item"
            :data-tour="entry.to === '/inventory/overview' ? 'home-overview-entry' : entry.to === '/master' ? 'home-master-entry' : entry.to === '/production' ? 'home-production-entry' : undefined"
            :disabled="entry.disabled"
            type="button"
            @click="emit('openMenuRoute', entry.to, entry.disabled)"
          >
            {{ entry.label }}
          </button>
        </div>
      </div>

      <button class="outline-btn action-btn" type="button" @click="emit('logout')">登出</button>
    </div>
  </header>
</template>

<style scoped>
.topbar {
  position: sticky;
  top: 0;
  z-index: 30;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(221, 229, 240, 0.94);
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(16px);
}

.topbar-main,
.topbar-primary-action,
.topbar-actions,
.topbar-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.topbar-primary-action {
  flex: 0 0 auto;
  margin-inline: 16px 20px;
}

.topbar-actions {
  margin-left: auto;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.brand-link {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
}

.brand-mark {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: linear-gradient(180deg, #183055 0%, #0f213e 100%);
  color: #edf4ff;
  font-weight: 800;
}

.brand-copy {
  display: grid;
  gap: 1px;
}

.brand-copy strong {
  color: #1a2945;
  font-size: 15px;
}

.brand-copy small {
  color: #5d6d89;
  font-size: 11px;
}

.pill {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 4px 10px;
  border: 1px solid #d7e2f5;
  border-radius: 999px;
  background: #f7faff;
  color: #35527d;
  font-size: 12px;
  font-weight: 700;
}

.pill.warn {
  border-color: rgba(224, 142, 31, 0.32);
  background: #fff7e7;
  color: #9b5f00;
}

.pill-hover {
  position: relative;
}

.hover-panel {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  z-index: 50;
  width: 280px;
  display: none;
  gap: 8px;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 18px 36px rgba(28, 47, 84, 0.16);
}

.pill-hover:hover .hover-panel {
  display: grid;
}

.hover-head strong,
.hover-row strong {
  color: #22314a;
  font-size: 12px;
}

.hover-list {
  display: grid;
  gap: 8px;
  max-height: 360px;
  overflow: auto;
}

.hover-row {
  display: grid;
  gap: 2px;
  padding: 8px 9px;
  border: 1px solid #e2e8f3;
  border-radius: 10px;
  background: #fbfdff;
}

.hover-row span,
.hover-row small,
.hover-empty {
  color: #5d6d89;
  font-size: 11px;
}

.hover-empty {
  padding: 6px 2px;
}

.hover-more-btn {
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  background: linear-gradient(180deg, #ffffff 0%, #f7f9fd 100%);
  color: #35527d;
  padding: 8px 10px;
  min-height: 34px;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.customer-picker {
  display: grid;
  gap: 6px;
}

select {
  width: 100%;
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  padding: 8px 10px;
  background: #fff;
  color: var(--text);
}

.action-btn {
  width: auto;
}

.primary-btn.receipt-btn {
  border-color: #2f6ee5;
  background: linear-gradient(180deg, #4b89ff 0%, #2f6ee5 100%);
  min-width: 236px;
  min-height: 42px;
  padding-inline: 44px;
}

.desktop-receipt-btn {
  min-width: 268px;
}

.mobile-trigger,
.mobile-customer {
  display: none;
}

.more-menu {
  position: relative;
}

.more-menu-panel {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 160px;
  display: grid;
  gap: 4px;
  padding: 6px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 14px 28px rgba(28, 47, 84, 0.14);
}

.more-menu-item {
  border: 1px solid transparent;
  border-radius: 8px;
  background: #fff;
  padding: 8px 10px;
  color: #324462;
  font: inherit;
  font-weight: 700;
  text-align: left;
  cursor: pointer;
}

.more-menu-item:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

@media (max-width: 1200px) {
  .topbar {
    flex-wrap: wrap;
  }

  .topbar-primary-action {
    order: 3;
    width: 100%;
    margin: 0;
  }
}

@media (max-width: 960px) {
  .mobile-trigger,
  .mobile-customer {
    display: inline-flex;
    align-items: center;
  }

  .topbar-primary-action,
  .topbar-info,
  .customer-picker,
  .more-menu,
  .topbar-actions > .outline-btn {
    display: none;
  }

  .topbar {
    padding: 10px 12px;
  }
}
</style>
