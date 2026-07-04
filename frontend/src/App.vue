<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink, RouterView, useRoute, useRouter } from "vue-router";

import { api } from "@/api";
import {
  authSession,
  customers,
  onboardingActive,
  onboardingSandboxMode,
  onboardingStepIndex,
  resetSession,
  selectedCustomerId
} from "@/appState";
import GuidedTour from "@/components/common/GuidedTour.vue";
import BatchImportPanel from "@/components/inventory/BatchImportPanel.vue";
import InventoryExportPanel from "@/components/inventory/InventoryExportPanel.vue";
import { onboardingSteps } from "@/onboarding";
import { dismissToast, pushToast, toasts } from "@/toastState";
import type { MaterialTransaction } from "@/types";
import { formatLocalDateKey as formatDateKey } from "@/utils/date";

const SESSION_KEY = "jig-record-session";
const CUSTOMER_KEY = "jig-record-customer-id";
const ONBOARDING_KEY = "jig-record-onboarding-seen";

const route = useRoute();
const router = useRouter();
const todayReceiptQty = ref(0);
const todayReturnQty = ref(0);
const lowStockCount = ref(0);
const recentTodayTransactions = ref<MaterialTransaction[]>([]);
const topbarAlerts = ref<Array<{ fixture_id: number; fixture_code: string; fixture_name: string; stock_qty: number; min_stock_qty: number; stock_status: "low_stock" | "out_of_stock" }>>([]);
const loginForm = ref({ username: "", password: "" });
const loggingIn = ref(false);
const moreMenuOpen = ref(false);
const mobileMenuOpen = ref(false);
const batchModalOpen = ref(false);
const exportModalOpen = ref(false);

const currentCustomerId = computed(() => selectedCustomerId.value ?? undefined);
const selectedCustomer = computed(() => customers.value.find((row) => row.id === selectedCustomerId.value) ?? null);
const canEnterMaster = computed(() => authSession.value?.role !== "guest");
const today = computed(() => formatDateKey(new Date()));
const currentOnboardingStep = computed(() => onboardingSteps[onboardingStepIndex.value] ?? null);
const dateTimeFormatter = new Intl.DateTimeFormat("zh-TW", {
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit"
});

const menuEntries = computed(() => [
  { label: "收退料總檢視", to: "/inventory/overview", disabled: false },
  { label: "資料維護", to: "/master", disabled: !canEnterMaster.value },
  { label: "產能管理", to: "/production", disabled: false }
]);

async function loadCustomers(): Promise<void> {
  customers.value = await api.listCustomers();
  if (!selectedCustomerId.value && customers.value.length > 0) {
    selectedCustomerId.value = customers.value[0].id;
  }
}

function resolveOnboardingCustomerId(): number | null {
  if (selectedCustomerId.value) {
    return selectedCustomerId.value;
  }
  return customers.value[0]?.id ?? null;
}

async function runFirstLoginOnboarding(): Promise<void> {
  const hasSeenOnboarding = sessionStorage.getItem(ONBOARDING_KEY) === "1";
  if (hasSeenOnboarding) {
    return;
  }
  const onboardingCustomerId = resolveOnboardingCustomerId();
  if (onboardingCustomerId === null) {
    pushToast("目前沒有可用客戶，無法自動啟動新手導覽。", "warning");
    return;
  }
  selectedCustomerId.value = onboardingCustomerId;
  onboardingStepIndex.value = 0;
  onboardingActive.value = true;
  sessionStorage.setItem(ONBOARDING_KEY, "1");
  await router.push({ path: onboardingSteps[0].route, query: { tour: "1" } });
}

function stopOnboarding(): void {
  onboardingActive.value = false;
  onboardingSandboxMode.value = false;
  batchModalOpen.value = false;
  exportModalOpen.value = false;
  moreMenuOpen.value = false;
  if (route.query.tour === "1") {
    void router.replace({ path: route.path, query: {} });
  }
}

async function syncOnboardingRoute(): Promise<void> {
  const step = currentOnboardingStep.value;
  if (!onboardingActive.value || !step) {
    onboardingSandboxMode.value = false;
    batchModalOpen.value = false;
    exportModalOpen.value = false;
    moreMenuOpen.value = false;
    return;
  }
  onboardingSandboxMode.value = step.id === "inventory-sandbox";
  batchModalOpen.value = step.id.startsWith("inventory-");
  exportModalOpen.value = step.id.startsWith("export-");
  moreMenuOpen.value = ["menu-trigger", "overview-entry", "master-entry", "production-entry"].includes(step.id);
  if (route.path !== step.route) {
    await router.push({ path: step.route, query: { ...route.query, tour: "1" } });
    return;
  }
  if (route.query.tour !== "1") {
    await router.replace({ path: step.route, query: { ...route.query, tour: "1" } });
  }
}

async function nextOnboardingStep(): Promise<void> {
  if (onboardingStepIndex.value >= onboardingSteps.length - 1) {
    stopOnboarding();
    if (route.query.tour === "1") {
      await router.replace({ path: route.path, query: {} });
    }
    return;
  }
  onboardingStepIndex.value += 1;
  await syncOnboardingRoute();
}

async function prevOnboardingStep(): Promise<void> {
  if (onboardingStepIndex.value <= 0) {
    return;
  }
  onboardingStepIndex.value -= 1;
  await syncOnboardingRoute();
}

async function loadTopbarStats(): Promise<void> {
  try {
    const [alerts, transactions] = await Promise.all([
      api.listAlerts(currentCustomerId.value),
      api.listTransactions(200, currentCustomerId.value)
    ]);
    topbarAlerts.value = alerts;
    recentTodayTransactions.value = transactions.filter((tx) => formatDateKey(new Date(tx.occurred_at)) === today.value);
    lowStockCount.value = alerts.length;
    todayReceiptQty.value = recentTodayTransactions.value
      .filter((tx) => tx.transaction_type === "receipt")
      .reduce((sum, tx) => sum + tx.items.reduce((itemSum, item) => itemSum + item.quantity, 0), 0);
    todayReturnQty.value = recentTodayTransactions.value
      .filter((tx) => tx.transaction_type === "return")
      .reduce((sum, tx) => sum + tx.items.reduce((itemSum, item) => itemSum + item.quantity, 0), 0);
  } catch {
    topbarAlerts.value = [];
    recentTodayTransactions.value = [];
    todayReceiptQty.value = 0;
    todayReturnQty.value = 0;
    lowStockCount.value = 0;
  }
}

const recentReceiptEntries = computed(() =>
  recentTodayTransactions.value
    .filter((tx) => tx.transaction_type === "receipt")
    .flatMap((tx) =>
      tx.items.map((item, index) => ({
        id: `${tx.id}-${index}`,
        occurredAt: tx.occurred_at,
        transactionNo: tx.transaction_no,
        fixtureCode: item.fixture_code,
        identifier: item.identifier || "-",
        quantity: item.quantity
      }))
    )
    .sort((a, b) => new Date(b.occurredAt).getTime() - new Date(a.occurredAt).getTime())
    .slice(0, 10)
);

const recentReturnEntries = computed(() =>
  recentTodayTransactions.value
    .filter((tx) => tx.transaction_type === "return")
    .flatMap((tx) =>
      tx.items.map((item, index) => ({
        id: `${tx.id}-${index}`,
        occurredAt: tx.occurred_at,
        transactionNo: tx.transaction_no,
        fixtureCode: item.fixture_code,
        identifier: item.identifier || "-",
        quantity: item.quantity
      }))
    )
    .sort((a, b) => new Date(b.occurredAt).getTime() - new Date(a.occurredAt).getTime())
    .slice(0, 10)
);

function formatHoverDate(value: string): string {
  return dateTimeFormatter.format(new Date(value));
}

const lowStockPreviewEntries = computed(() => topbarAlerts.value.slice(0, 20));
const hasMoreLowStockEntries = computed(() => topbarAlerts.value.length > 20);

async function login(): Promise<void> {
  loggingIn.value = true;
  try {
    authSession.value = await api.login({
      username: loginForm.value.username.trim(),
      password: loginForm.value.password
    });
    await loadCustomers();
    await loadTopbarStats();
    await runFirstLoginOnboarding();
    pushToast(`已登入：${authSession.value.display_name}`, "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "登入失敗", "error");
  } finally {
    loggingIn.value = false;
  }
}

async function guestEntry(): Promise<void> {
  loggingIn.value = true;
  try {
    authSession.value = await api.guestEntry();
    await loadCustomers();
    await loadTopbarStats();
    pushToast("已使用訪客入口登入", "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "訪客登入失敗", "error");
  } finally {
    loggingIn.value = false;
  }
}

function logout(): void {
  resetSession();
  topbarAlerts.value = [];
  recentTodayTransactions.value = [];
  todayReceiptQty.value = 0;
  todayReturnQty.value = 0;
  lowStockCount.value = 0;
  mobileMenuOpen.value = false;
  moreMenuOpen.value = false;
  batchModalOpen.value = false;
  exportModalOpen.value = false;
  pushToast("已登出", "info");
}

function openMenuRoute(path: string, disabled: boolean): void {
  if (disabled) {
    return;
  }
  moreMenuOpen.value = false;
  mobileMenuOpen.value = false;
  void router.push(path);
}

function openLowStockPage(): void {
  moreMenuOpen.value = false;
  mobileMenuOpen.value = false;
  void router.push("/inventory");
}

function openInventoryExport(): void {
  moreMenuOpen.value = false;
  mobileMenuOpen.value = false;
  exportModalOpen.value = true;
}

watch(authSession, (value) => {
  if (value) {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(value));
  } else {
    sessionStorage.removeItem(SESSION_KEY);
  }
});

watch(selectedCustomerId, async (value) => {
  if (value) {
    sessionStorage.setItem(CUSTOMER_KEY, String(value));
  } else {
    sessionStorage.removeItem(CUSTOMER_KEY);
  }
  if (authSession.value) {
    await loadTopbarStats();
  }
});

watch(
  () => [onboardingActive.value, onboardingStepIndex.value],
  async () => {
    await syncOnboardingRoute();
  }
);

watch(
  () => route.fullPath,
  () => {
    moreMenuOpen.value = false;
    mobileMenuOpen.value = false;
  }
);

onMounted(async () => {
  const savedSession = sessionStorage.getItem(SESSION_KEY);
  if (savedSession) {
    try {
      authSession.value = JSON.parse(savedSession);
    } catch {
      sessionStorage.removeItem(SESSION_KEY);
    }
  }

  const savedCustomerId = sessionStorage.getItem(CUSTOMER_KEY);
  if (savedCustomerId) {
    selectedCustomerId.value = Number(savedCustomerId);
  }

  if (authSession.value) {
    await loadCustomers();
    await loadTopbarStats();
  }
});
</script>

<template>
  <div class="viewport-shell">
    <div class="app-shell">
      <template v-if="!authSession">
        <section class="login-shell">
          <article class="login-card">
            <header class="login-brand">
              <div class="login-brand-mark" aria-hidden="true">JR</div>
              <div>
                <p class="login-eyebrow">Jig Record</p>
                <h1>人員登入入口</h1>
              </div>
            </header>
            <p class="login-copy">請使用帳號密碼登入，或以訪客身分進入系統。</p>
            <form class="login-form" @submit.prevent="login">
              <label>
                <span>帳號</span>
                <input v-model="loginForm.username" name="username" autocomplete="username" spellcheck="false" required />
              </label>
              <label>
                <span>密碼</span>
                <input v-model="loginForm.password" name="password" autocomplete="current-password" type="password" required />
              </label>
              <button class="primary-btn" type="submit" :disabled="loggingIn">{{ loggingIn ? "登入中..." : "登入" }}</button>
            </form>
            <button class="outline-btn" type="button" :disabled="loggingIn" @click="guestEntry">訪客入口</button>
          </article>
        </section>
      </template>

      <template v-else>
        <GuidedTour
          :open="onboardingActive"
          :steps="onboardingSteps"
          :current-index="onboardingStepIndex"
          @close="stopOnboarding"
          @next="nextOnboardingStep"
          @prev="prevOnboardingStep"
        />
        <header class="topbar">
          <div class="topbar-main">
            <button class="outline-btn mobile-trigger" type="button" @click="mobileMenuOpen = !mobileMenuOpen">選單</button>
            <RouterLink class="brand-link" to="/search">
              <span class="brand-mark">JR</span>
              <span class="brand-copy">
                <strong>Jig Record</strong>
                <small>回首頁</small>
              </span>
            </RouterLink>
            <div class="mobile-customer">{{ selectedCustomer?.code || "未選客戶" }}</div>
          </div>

          <div class="topbar-primary-action">
            <button class="primary-btn action-btn receipt-btn desktop-receipt-btn" data-tour="inventory-entry-trigger" type="button" @click="batchModalOpen = true">治具收/退料</button>
            <button class="primary-btn action-btn receipt-btn desktop-receipt-btn" data-tour="inventory-export-entry-trigger" type="button" @click="openInventoryExport">收退料資訊匯出</button>
          </div>

          <div class="topbar-actions">
            <div class="topbar-info">
              <span class="pill">{{ authSession.display_name }}</span>
              <span class="pill">客戶 {{ selectedCustomer?.code || "未選" }}</span>
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
                  <button v-if="hasMoreLowStockEntries" class="hover-more-btn" type="button" @click="openLowStockPage">查看更多</button>
                </div>
              </div>
            </div>

            <label class="customer-picker" data-tour="global-customer-picker">
              <select v-model.number="selectedCustomerId">
                <option v-for="customer in customers" :key="customer.id" :value="customer.id">{{ customer.code }} - {{ customer.name }}</option>
              </select>
            </label>

            <div class="more-menu">
              <button class="outline-btn action-btn" data-tour="home-more-menu-trigger" type="button" :aria-expanded="moreMenuOpen" @click="moreMenuOpen = !moreMenuOpen">更多功能</button>
              <div v-if="moreMenuOpen" class="more-menu-panel">
                <button
                  v-for="entry in menuEntries"
                  :key="entry.to"
                  class="more-menu-item"
                  :data-tour="entry.to === '/inventory/overview' ? 'home-overview-entry' : entry.to === '/master' ? 'home-master-entry' : entry.to === '/production' ? 'home-production-entry' : undefined"
                  :disabled="entry.disabled"
                  type="button"
                  @click="openMenuRoute(entry.to, entry.disabled)"
                >
                  {{ entry.label }}
                </button>
              </div>
            </div>

            <button class="outline-btn action-btn" type="button" @click="logout">登出</button>
          </div>
        </header>

        <button v-if="mobileMenuOpen" class="mobile-backdrop" type="button" @click="mobileMenuOpen = false"></button>
        <aside v-if="mobileMenuOpen" class="mobile-drawer">
          <div class="drawer-head">
            <strong>功能選單</strong>
            <button class="outline-btn small" type="button" @click="mobileMenuOpen = false">關閉</button>
          </div>
          <div class="drawer-stats">
            <span class="pill">{{ authSession.display_name }}</span>
            <span class="pill">客戶 {{ selectedCustomer?.code || "未選" }}</span>
            <span class="pill">今日收料 {{ todayReceiptQty }}</span>
            <span class="pill">今日退料 {{ todayReturnQty }}</span>
            <span class="pill warn">低水位 {{ lowStockCount }}</span>
          </div>
          <label class="customer-picker mobile-picker">
            <span>客戶</span>
            <select v-model.number="selectedCustomerId">
              <option v-for="customer in customers" :key="customer.id" :value="customer.id">{{ customer.code }} - {{ customer.name }}</option>
            </select>
          </label>
          <button class="primary-btn receipt-btn mobile-receipt-btn" type="button" @click="batchModalOpen = true; mobileMenuOpen = false">治具收/退料</button>
          <button class="primary-btn receipt-btn mobile-receipt-btn" type="button" @click="openInventoryExport">收退料資訊匯出</button>
          <button
            v-for="entry in menuEntries"
            :key="`mobile-${entry.to}`"
            class="outline-btn drawer-link"
            type="button"
            :disabled="entry.disabled"
            @click="openMenuRoute(entry.to, entry.disabled)"
          >
            {{ entry.label }}
          </button>
          <button class="outline-btn drawer-link" type="button" @click="logout">登出</button>
        </aside>

        <main class="page-shell">
          <RouterView />
        </main>

        <teleport to="body">
          <div v-if="batchModalOpen" class="modal-backdrop" @click.self="batchModalOpen = false">
            <div class="modal-card" data-tour="inventory-batch-panel">
              <div class="modal-head">
                <div>
                  <span class="modal-eyebrow">Global Action</span>
                  <h2>收 / 退料</h2>
                </div>
                <button class="outline-btn" type="button" @click="batchModalOpen = false">關閉</button>
              </div>
              <BatchImportPanel
                :customer-id="currentCustomerId"
                title="全域收退料匯入"
                description="Modal 只保留批次匯入，方便在任何頁面直接處理收退料。"
                :hide-frame="true"
                @success="loadTopbarStats"
              />
            </div>
          </div>
          <div v-if="exportModalOpen" class="modal-backdrop" @click.self="exportModalOpen = false">
            <div class="modal-card export-modal-card" data-tour="inventory-export-panel">
              <div class="modal-head">
                <div>
                  <span class="modal-eyebrow">Global Action</span>
                  <h2>收退料資訊匯出</h2>
                </div>
                <button class="outline-btn" type="button" @click="exportModalOpen = false">關閉</button>
              </div>
              <InventoryExportPanel :customer-id="currentCustomerId" />
            </div>
          </div>
        </teleport>
      </template>

      <section class="toast-stack" aria-live="polite">
        <article v-for="toast in toasts" :key="toast.id" class="toast-card" :class="toast.tone">
          <span>{{ toast.message }}</span>
          <button class="toast-close" type="button" @click="dismissToast(toast.id)">x</button>
        </article>
      </section>
    </div>
  </div>
</template>

<style scoped>
.viewport-shell {
  min-height: 100dvh;
  background:
    radial-gradient(circle at 12% 0%, rgba(47, 110, 229, 0.16), transparent 30%),
    radial-gradient(circle at 88% 0%, rgba(32, 164, 92, 0.1), transparent 24%),
    linear-gradient(180deg, #f8fbff 0%, #edf3f9 100%);
}

.app-shell {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  position: relative;
}

.login-shell {
  min-height: 100dvh;
  display: grid;
  place-items: center;
  padding: 24px;
}

.login-card {
  width: min(460px, 100%);
  padding: 30px;
  border: 1px solid rgba(214, 224, 238, 0.94);
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(247, 250, 255, 0.96) 100%);
  box-shadow: 0 28px 60px rgba(28, 47, 84, 0.14);
  display: grid;
  gap: 16px;
}

.login-brand {
  display: flex;
  align-items: center;
  gap: 14px;
}

.login-brand-mark,
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

.login-eyebrow,
.modal-eyebrow {
  margin: 0;
  color: #2f6ee5;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.login-card h1,
.modal-head h2 {
  margin: 0;
  color: #1f2b45;
}

.login-copy {
  margin: 0;
  color: #5d6d89;
  font-size: 14px;
}

.login-form {
  display: grid;
  gap: 12px;
}

.login-form label,
.customer-picker {
  display: grid;
  gap: 6px;
}

.login-form span,
.customer-picker span {
  color: #56657f;
  font-size: 12px;
  font-weight: 700;
}

input,
select {
  width: 100%;
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  padding: 8px 10px;
  background: #fff;
  color: var(--text);
}

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

.page-shell {
  flex: 1;
  min-height: 0;
  padding: 12px;
  overflow: auto;
  -webkit-overflow-scrolling: touch;
}

.mobile-backdrop {
  display: none;
}

.mobile-drawer {
  display: none;
}

.drawer-head,
.drawer-stats {
  display: grid;
  gap: 8px;
}

.drawer-link {
  justify-content: center;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(17, 24, 39, 0.42);
}

.modal-card {
  width: min(920px, 100%);
  max-height: 88vh;
  overflow: auto;
  border: 1px solid var(--line);
  border-radius: 20px;
  background: #fff;
  box-shadow: 0 24px 60px rgba(17, 24, 39, 0.22);
  padding: 16px;
}

.export-modal-card {
  width: min(760px, 100%);
}

.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
}

.primary-btn,
.outline-btn {
  border-radius: 10px;
  font-weight: 700;
  min-height: 36px;
  cursor: pointer;
}

.primary-btn {
  border: 1px solid var(--green);
  background: linear-gradient(180deg, #4cc36b 0%, #2ea54e 100%);
  color: #fff;
  padding: 8px 14px;
}

.mobile-receipt-btn {
  width: 100%;
  min-width: 100%;
}

.outline-btn {
  border: 1px solid var(--line-strong);
  background: linear-gradient(180deg, #ffffff 0%, #f7f9fd 100%);
  color: #5b677d;
  padding: 8px 14px;
}

.outline-btn.small {
  min-height: 32px;
  padding: 6px 12px;
}

.toast-stack {
  position: fixed;
  top: 78px;
  right: 16px;
  z-index: 80;
  display: grid;
  gap: 8px;
  width: 320px;
}

.toast-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: var(--shadow);
  padding: 11px 12px;
  color: #20304f;
  font-size: 12px;
}

.toast-card.success {
  border-color: #b8e2cb;
  background: #f4fff8;
  color: #18643f;
}

.toast-card.error {
  border-color: #f1c3c3;
  background: #fff6f6;
  color: #a53636;
}

.toast-card.warning {
  border-color: #f3dbab;
  background: #fffaf0;
  color: #9d6706;
}

.toast-card.info {
  border-color: #c8daf7;
  background: #f5f9ff;
  color: #255ebd;
}

.toast-close {
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: inherit;
  font-weight: 700;
}

@media (max-width: 1080px) {
  .topbar {
    gap: 10px;
  }

  .topbar-primary-action,
  .topbar-info,
  .customer-picker,
  .topbar-actions > .action-btn,
  .topbar-actions > .more-menu {
    display: none;
  }

  .mobile-trigger,
  .mobile-customer {
    display: inline-flex;
    align-items: center;
  }

  .mobile-customer {
    margin-left: auto;
    color: #22314a;
    font-size: 12px;
    font-weight: 700;
  }

  .topbar-actions {
    margin-left: 0;
  }

  .mobile-backdrop {
    position: fixed;
    inset: 0;
    z-index: 39;
    display: block;
    border: 0;
    background: rgba(15, 23, 42, 0.58);
  }

  .mobile-drawer {
    position: fixed;
    top: 12px;
    left: 12px;
    z-index: 40;
    width: min(320px, calc(100vw - 24px));
    max-height: calc(100vh - 24px);
    overflow: auto;
    display: grid;
    gap: 12px;
    padding: 14px;
    border: 1px solid var(--line);
    border-radius: 18px;
    background: #fff;
    box-shadow: 0 24px 60px rgba(17, 24, 39, 0.22);
  }
}

@media (max-width: 720px) {
  .page-shell {
    padding: 8px;
  }

  .toast-stack {
    left: 10px;
    right: 10px;
    width: auto;
    top: auto;
    bottom: 10px;
  }
}
</style>
