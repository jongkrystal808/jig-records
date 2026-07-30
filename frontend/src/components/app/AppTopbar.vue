<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
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
  transactionNo: string | null;
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
  canOperateInventory: boolean;
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
  openBatch: [fixtureCode?: string];
  openExport: [];
  openOnboarding: [];
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

const activePopover = ref<"receipt" | "return" | "low_stock" | null>(null);

function togglePopover(target: "receipt" | "return" | "low_stock"): void {
  activePopover.value = activePopover.value === target ? null : target;
}

function closePopover(): void {
  activePopover.value = null;
}

function displayTransactionNo(value: string | null): string {
  return value?.trim() || "（無單號）";
}

function handleDocumentClick(event: MouseEvent): void {
  const target = event.target;
  if (!(target instanceof Element) || target.closest("[data-topbar-popover]")) {
    return;
  }
  closePopover();
}

function handleDocumentKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape") {
    closePopover();
  }
}

onMounted(() => {
  document.addEventListener("click", handleDocumentClick);
  document.addEventListener("keydown", handleDocumentKeydown);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", handleDocumentClick);
  document.removeEventListener("keydown", handleDocumentKeydown);
});

// Keep desktop shell UI isolated so App.vue only orchestrates session, routing, and stats loading.
</script>

<template>
  <header class="topbar">
    <div class="topbar-main">
      <button class="outline-btn mobile-trigger" type="button" @click="emit('toggleMobileMenu')">選單</button>
      <RouterLink class="brand-link" data-tour="detailed-home-button" to="/search">
        <span class="brand-mark">JR</span>
        <span class="brand-copy">
          <strong>Jig Record</strong>
          <small>回首頁</small>
        </span>
      </RouterLink>
      <div class="mobile-customer">{{ selectedCustomerCode || "未選客戶" }}</div>
    </div>

    <div class="topbar-primary-action" data-tour="detailed-primary-actions">
      <button
        v-if="canOperateInventory"
        class="primary-btn action-btn compact-primary-btn"
        data-tour="inventory-entry-trigger"
        type="button"
        @click="emit('openBatch')"
      >
        治具收/退料
      </button>
      <button class="primary-btn action-btn compact-primary-btn" data-tour="inventory-export-entry-trigger" type="button" @click="emit('openExport')">
        匯出中心
      </button>
      <button class="outline-btn action-btn compact-outline-btn" data-tour="search-onboarding-entry" type="button" @click="emit('openOnboarding')">
        新手教學
      </button>
    </div>

    <div class="topbar-actions">
      <div class="topbar-info" data-tour="detailed-status-actions">
        <span class="pill">{{ authDisplayName }}</span>
        <div class="pill-hover" data-topbar-popover>
          <button class="pill pill-trigger" type="button" :aria-expanded="activePopover === 'receipt'" @click="togglePopover('receipt')">
            <span>今日收料</span>
            <strong class="pill-number">{{ todayReceiptQty }}</strong>
          </button>
          <div v-if="activePopover === 'receipt'" class="hover-panel popover-panel">
            <div class="hover-head">
              <strong>最近收料 10 筆</strong>
            </div>
            <div v-if="recentReceiptEntries.length > 0" class="hover-list">
              <div v-for="entry in recentReceiptEntries" :key="entry.id" class="hover-row">
                <strong>{{ entry.fixtureCode }}</strong>
                <span>{{ entry.identifier }} / {{ entry.quantity }}</span>
                <small>{{ formatHoverDate(entry.occurredAt) }} / {{ displayTransactionNo(entry.transactionNo) }}</small>
              </div>
            </div>
            <div v-else class="hover-empty">今天尚無收料資料</div>
          </div>
        </div>
        <div class="pill-hover" data-topbar-popover>
          <button class="pill pill-trigger" type="button" :aria-expanded="activePopover === 'return'" @click="togglePopover('return')">
            <span>今日退料</span>
            <strong class="pill-number">{{ todayReturnQty }}</strong>
          </button>
          <div v-if="activePopover === 'return'" class="hover-panel popover-panel">
            <div class="hover-head">
              <strong>最近退料 10 筆</strong>
            </div>
            <div v-if="recentReturnEntries.length > 0" class="hover-list">
              <div v-for="entry in recentReturnEntries" :key="entry.id" class="hover-row">
                <strong>{{ entry.fixtureCode }}</strong>
                <span>{{ entry.identifier }} / {{ entry.quantity }}</span>
                <small>{{ formatHoverDate(entry.occurredAt) }} / {{ displayTransactionNo(entry.transactionNo) }}</small>
              </div>
            </div>
            <div v-else class="hover-empty">今天尚無退料資料</div>
          </div>
        </div>
        <div class="pill-hover" data-topbar-popover>
          <button class="pill warn pill-trigger" type="button" :aria-expanded="activePopover === 'low_stock'" @click="togglePopover('low_stock')">
            <span>低水位</span>
            <strong class="pill-number">{{ lowStockCount }}</strong>
          </button>
          <div v-if="activePopover === 'low_stock'" class="hover-panel popover-panel">
            <div class="hover-head">
              <strong>低水位治具</strong>
            </div>
            <div v-if="lowStockPreviewEntries.length > 0" class="hover-list">
              <div v-for="entry in lowStockPreviewEntries" :key="entry.fixture_id" class="hover-row">
                <div class="hover-row-main">
                  <strong>{{ entry.fixture_code }}</strong>
                  <span>{{ entry.fixture_name }}</span>
                  <small>庫存 {{ entry.stock_qty }} / 最低 {{ entry.min_stock_qty }}</small>
                </div>
                <button
                  v-if="canOperateInventory"
                  class="hover-inline-btn"
                  type="button"
                  @click="closePopover(); emit('openBatch', entry.fixture_code)"
                >
                  收 / 退料
                </button>
              </div>
            </div>
            <div v-else class="hover-empty">目前沒有低水位治具</div>
            <button v-if="hasMoreLowStockEntries" class="hover-more-btn" type="button" @click="emit('openLowStockPage')">查看更多</button>
          </div>
        </div>
      </div>

      <label class="customer-picker" data-tour="global-customer-picker">
        <select :value="selectedCustomerId ?? undefined" aria-label="選擇客戶" @change="handleCustomerChange">
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

      <button class="outline-btn action-btn" data-tour="detailed-logout-button" type="button" @click="emit('logout')">登出</button>
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
  margin-inline: 12px 18px;
  gap: 8px;
  flex-wrap: wrap;
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
  min-height: 44px;
  padding: 8px 12px;
  border: 1px solid #d7e2f5;
  border-radius: 999px;
  background: #f7faff;
  color: #35527d;
  font-size: 14px;
  font-weight: 700;
}

.pill-number {
  font-size: 16px;
  line-height: 1;
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
  display: grid;
  gap: 8px;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 18px 36px rgba(28, 47, 84, 0.16);
}

.pill-trigger {
  cursor: pointer;
  gap: 8px;
}

.popover-panel {
  animation: fadeDown 0.14s ease;
}

.hover-head strong,
.hover-row strong {
  color: #22314a;
  font-size: 14px;
}

.hover-list {
  display: grid;
  gap: 8px;
  max-height: 360px;
  overflow: auto;
}

.hover-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 8px 9px;
  border: 1px solid #e2e8f3;
  border-radius: 10px;
  background: #fbfdff;
}

.hover-row-main {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.hover-row span,
.hover-row small,
.hover-empty {
  color: #5d6d89;
  font-size: 13px;
}

.hover-inline-btn {
  flex: 0 0 auto;
  border: 1px solid #d7e2f5;
  border-radius: 9px;
  min-height: 32px;
  padding: 6px 10px;
  background: #fff;
  color: #35527d;
  font: inherit;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
  white-space: nowrap;
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
  min-height: 44px;
  font: inherit;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

@keyframes fadeDown {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.customer-picker {
  display: grid;
  gap: 6px;
}

select {
  width: 100%;
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  min-height: 44px;
  padding: 10px 12px;
  background: #fff;
  color: var(--text);
  font-size: 14px;
}

.action-btn {
  width: auto;
}

.compact-primary-btn {
  border-color: #2f6ee5;
  background: linear-gradient(180deg, #4b89ff 0%, #2f6ee5 100%);
  min-height: 44px;
  padding: 10px 18px;
  font-size: 14px;
  font-weight: 800;
}

.compact-outline-btn {
  min-height: 44px;
  padding: 10px 14px;
  font-size: 14px;
  font-weight: 800;
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

@media (max-width: 1366px) {
  .mobile-trigger,
  .mobile-customer {
    display: inline-flex;
    align-items: center;
  }

  .topbar {
    gap: 12px;
    padding: 10px 12px;
  }

  .topbar-main {
    flex: 1 1 auto;
    min-width: 0;
  }

  .mobile-customer {
    margin-left: auto;
    min-height: 36px;
    padding: 0 10px;
    border-radius: 999px;
    background: #f7faff;
    color: #35527d;
    font-size: 13px;
    font-weight: 700;
    max-width: 180px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .topbar-primary-action {
    flex: 1 0 100%;
    width: 100%;
    margin: 0;
    justify-content: flex-start;
  }

  .topbar-primary-action,
  .topbar-info,
  .customer-picker,
  .more-menu,
  .topbar-actions > .outline-btn {
    display: none;
  }
}
</style>
