<script setup lang="ts">
import type { Customer } from "@/types";

type MenuEntry = {
  label: string;
  to: string;
  disabled: boolean;
};

const props = defineProps<{
  open: boolean;
  authDisplayName: string;
  canOperateInventory: boolean;
  selectedCustomerCode: string;
  customers: Customer[];
  selectedCustomerId: number | null;
  todayReceiptQty: number;
  todayReturnQty: number;
  lowStockCount: number;
  menuEntries: MenuEntry[];
}>();

const emit = defineEmits<{
  close: [];
  "update:selectedCustomerId": [value: number | null];
  openBatch: [];
  openExport: [];
  openOnboarding: [];
  openMenuRoute: [path: string, disabled: boolean];
  logout: [];
}>();

function handleCustomerChange(event: Event): void {
  const value = Number.parseInt((event.target as HTMLSelectElement).value, 10);
  emit("update:selectedCustomerId", Number.isFinite(value) ? value : null);
}

function handleOpenBatch(): void {
  emit("openBatch");
  emit("close");
}

function handleOpenExport(): void {
  emit("openExport");
  emit("close");
}

function handleOpenOnboarding(): void {
  emit("openOnboarding");
  emit("close");
}

// Keep mobile navigation isolated so App.vue does not duplicate shell markup across breakpoints.
</script>

<template>
  <template v-if="open">
    <button class="mobile-backdrop" type="button" aria-label="關閉選單" @click="emit('close')"></button>
    <aside class="mobile-drawer">
      <div class="drawer-head">
        <strong>功能選單</strong>
        <button class="outline-btn btn-sm" type="button" @click="emit('close')">關閉</button>
      </div>
      <button v-if="canOperateInventory" class="primary-btn receipt-btn mobile-receipt-btn" type="button" @click="handleOpenBatch">治具收/退料</button>
      <button class="primary-btn receipt-btn mobile-receipt-btn" type="button" @click="handleOpenExport">匯出中心</button>
      <button class="outline-btn drawer-link" type="button" @click="handleOpenOnboarding">新手教學</button>
      <button
        v-for="entry in menuEntries"
        :key="`mobile-${entry.to}`"
        class="outline-btn drawer-link"
        type="button"
        :disabled="entry.disabled"
        @click="emit('openMenuRoute', entry.to, entry.disabled)"
      >
        {{ entry.label }}
      </button>
      <label class="customer-picker mobile-picker">
        <span>客戶</span>
        <select :value="selectedCustomerId ?? undefined" aria-label="選擇客戶" @change="handleCustomerChange">
          <option v-for="customer in customers" :key="customer.id" :value="customer.id">{{ customer.code }} - {{ customer.name }}</option>
        </select>
      </label>
      <div class="drawer-stats">
        <span class="pill">{{ authDisplayName }}</span>
        <span class="pill">客戶 {{ selectedCustomerCode || "未選" }}</span>
        <span class="pill"><span>今日收料</span><strong class="pill-number">{{ todayReceiptQty }}</strong></span>
        <span class="pill"><span>今日退料</span><strong class="pill-number">{{ todayReturnQty }}</strong></span>
        <span class="pill warn"><span>低水位</span><strong class="pill-number">{{ lowStockCount }}</strong></span>
      </div>
      <button class="outline-btn drawer-link" type="button" @click="emit('logout')">登出</button>
    </aside>
  </template>
</template>

<style scoped>
.mobile-backdrop {
  position: fixed;
  inset: 0;
  z-index: 39;
  border: 0;
  background: rgba(17, 24, 39, 0.34);
}

.mobile-drawer {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 40;
  width: min(360px, calc(100vw - 40px));
  padding: 16px;
  display: grid;
  align-content: start;
  gap: 12px;
  overflow-y: auto;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 22px 44px rgba(17, 24, 39, 0.18);
}

.drawer-head {
  position: sticky;
  top: -16px;
  z-index: 1;
  margin: -16px -16px 0;
  padding: 16px 16px 8px;
  background: rgba(255, 255, 255, 0.98);
}

.drawer-head,
.drawer-stats {
  display: grid;
  gap: 8px;
}

.pill {
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
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

.customer-picker {
  display: grid;
  gap: 6px;
}

.customer-picker span {
  color: #56657f;
  font-size: 14px;
  font-weight: 700;
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

.drawer-link {
  justify-content: center;
  min-height: 44px;
  font-size: 14px;
}

.mobile-receipt-btn {
  width: 100%;
  min-width: 100%;
  min-height: 44px;
  font-size: 14px;
}

.primary-btn.receipt-btn {
  border-color: #2f6ee5;
  background: linear-gradient(180deg, #4b89ff 0%, #2f6ee5 100%);
}

@media (min-width: 1367px) {
  .mobile-backdrop,
  .mobile-drawer {
    display: none;
  }
}
</style>
