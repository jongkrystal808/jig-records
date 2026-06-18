<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { RouterLink, RouterView, useRoute } from "vue-router";

import { api } from "@/api";
import { authSession, customers, resetSession, selectedCustomerId } from "@/appState";
import { dismissToast, pushToast, toasts } from "@/toastState";
import { formatLocalDateKey as formatDateKey } from "@/utils/date";

const SESSION_KEY = "jig-record-session";
const CUSTOMER_KEY = "jig-record-customer-id";
const SIDEBAR_KEY = "jig-record-sidebar-compact";

const route = useRoute();
const todayReceiptQty = ref(0);
const todayReturnQty = ref(0);
const lowStockCount = ref(0);
const loginForm = ref({ username: "", password: "" });
const loggingIn = ref(false);
const mobileMenuOpen = ref(false);
const sidebarCompact = ref(false);
const clockNow = ref(new Date());
let clockTimer: ReturnType<typeof window.setInterval> | null = null;

const currentCustomerId = computed(() => selectedCustomerId.value ?? undefined);
const selectedCustomer = computed(() => customers.value.find((row) => row.id === selectedCustomerId.value) ?? null);
const userInitial = computed(() => authSession.value?.display_name?.trim().charAt(0).toUpperCase() || "U");
const canEnterMaster = computed(() => authSession.value?.role !== "guest");
const currentDateTimeLabel = computed(() =>
  new Intl.DateTimeFormat("zh-TW", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(clockNow.value)
);
const today = computed(() => formatDateKey(new Date()));

const sideNav = computed(() =>
  [
    { label: "收退料作業", short: "作業", to: "/inventory", exact: true },
    { label: "收退料總檢視", short: "總檢視", to: "/inventory/overview", exact: true },
    { label: "治具 / 機種查詢", short: "查詢", to: "/search" },
    { label: "產能管理", short: "產能", to: "/production" },
    canEnterMaster.value ? { label: "資料維護", short: "維護", to: "/master" } : null
  ].filter((item): item is { label: string; short: string; to: string; exact?: boolean } => item !== null)
);

function isActive(path: string, exact = false): boolean {
  if (exact) {
    return route.path === path;
  }
  return route.path === path || route.path.startsWith(`${path}/`);
}

async function loadCustomers(): Promise<void> {
  customers.value = await api.listCustomers();
  if (!selectedCustomerId.value && customers.value.length > 0) {
    selectedCustomerId.value = customers.value[0].id;
  }
}

async function loadSidebarStats(): Promise<void> {
  try {
    const [alerts, transactions] = await Promise.all([
      api.listAlerts(currentCustomerId.value),
      api.listTransactions(200, currentCustomerId.value)
    ]);
    lowStockCount.value = alerts.length;
    todayReceiptQty.value = transactions
      .filter((tx) => tx.transaction_type === "receipt" && formatDateKey(new Date(tx.occurred_at)) === today.value)
      .reduce((sum, tx) => sum + tx.items.reduce((itemSum, item) => itemSum + item.quantity, 0), 0);
    todayReturnQty.value = transactions
      .filter((tx) => tx.transaction_type === "return" && formatDateKey(new Date(tx.occurred_at)) === today.value)
      .reduce((sum, tx) => sum + tx.items.reduce((itemSum, item) => itemSum + item.quantity, 0), 0);
  } catch {
    todayReceiptQty.value = 0;
    todayReturnQty.value = 0;
    lowStockCount.value = 0;
  }
}

async function login(): Promise<void> {
  loggingIn.value = true;
  try {
    authSession.value = await api.login({
      username: loginForm.value.username.trim(),
      password: loginForm.value.password
    });
    await loadCustomers();
    await loadSidebarStats();
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
    await loadSidebarStats();
    pushToast("已使用訪客入口登入", "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "訪客登入失敗", "error");
  } finally {
    loggingIn.value = false;
  }
}

function logout(): void {
  resetSession();
  todayReceiptQty.value = 0;
  todayReturnQty.value = 0;
  lowStockCount.value = 0;
  mobileMenuOpen.value = false;
  pushToast("已登出", "info");
}

function toggleSidebarCompact(): void {
  sidebarCompact.value = !sidebarCompact.value;
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
    await loadSidebarStats();
  }
});

watch(sidebarCompact, (value) => {
  sessionStorage.setItem(SIDEBAR_KEY, value ? "1" : "0");
});

watch(
  () => route.path,
  () => {
    mobileMenuOpen.value = false;
  }
);

onMounted(async () => {
  clockTimer = window.setInterval(() => {
    clockNow.value = new Date();
  }, 60_000);

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
  sidebarCompact.value = sessionStorage.getItem(SIDEBAR_KEY) === "1";

  if (authSession.value) {
    await loadCustomers();
    await loadSidebarStats();
  }
});

onBeforeUnmount(() => {
  if (clockTimer !== null) {
    window.clearInterval(clockTimer);
    clockTimer = null;
  }
});
</script>

<template>
  <div class="viewport-shell">
    <a class="skip-link" href="#main-content">跳到主要內容</a>
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
                <input v-model="loginForm.username" name="username" autocomplete="username" spellcheck="false" placeholder="例如：admin…" required />
              </label>
              <label>
                <span>密碼</span>
                <input v-model="loginForm.password" name="password" autocomplete="current-password" placeholder="例如：admin123…" type="password" required />
              </label>
              <button class="primary-btn" type="submit" :disabled="loggingIn">{{ loggingIn ? "登入中..." : "登入" }}</button>
            </form>
            <button class="outline-btn" type="button" :disabled="loggingIn" @click="guestEntry">訪客入口</button>
          </article>
        </section>
      </template>

      <template v-else>
        <button
          class="outline-btn nav-toggle shell-menu-toggle"
          type="button"
          :aria-expanded="mobileMenuOpen"
          aria-controls="side-nav"
          @click="mobileMenuOpen = !mobileMenuOpen"
        >
          {{ mobileMenuOpen ? "關閉選單" : "功能選單" }}
        </button>

        <div class="body-shell">
          <aside id="side-nav" class="side-nav" :class="{ open: mobileMenuOpen, compact: sidebarCompact }">
            <div class="brand-block">
              <p class="brand-title" translate="no">Jig Record</p>
              <h1>E 化治具清單</h1>
              <p class="brand-copy">治具庫存 / 機種 / 站點集中維護</p>
            </div>

            <section class="session-card">
              <div class="session-top">
                <div>
                  <p class="session-eyebrow">登入狀態</p>
                  <strong translate="no">{{ authSession.display_name }}</strong>
                </div>
                <button class="user-avatar" type="button" :aria-label="`使用者：${authSession.display_name}`" :title="authSession.display_name">
                  <span>{{ userInitial }}</span>
                </button>
              </div>

              <div class="session-row">
                <span>客戶</span>
                <strong translate="no">{{ selectedCustomer ? selectedCustomer.code : "未選客戶" }}</strong>
              </div>
              <label class="customer-picker session-picker">
                <span class="sr-only">客戶</span>
                <select v-model.number="selectedCustomerId">
                  <option v-for="customer in customers" :key="customer.id" :value="customer.id">{{ customer.code }} - {{ customer.name }}</option>
                </select>
              </label>
              <div class="session-row">
                <span>時間</span>
                <strong>{{ currentDateTimeLabel }}</strong>
              </div>
              <div class="session-actions">
                <button class="outline-btn small" type="button" @click="toggleSidebarCompact">
                  {{ sidebarCompact ? "展開側欄" : "收合側欄" }}
                </button>
                <button class="outline-btn small" type="button" @click="logout">登出</button>
              </div>
            </section>

            <div class="side-nav-tools">
              <button class="ghost-btn small" type="button" @click="toggleSidebarCompact">
                {{ sidebarCompact ? "展開" : "收合" }}
              </button>
            </div>

            <nav class="side-menu">
              <RouterLink
                v-for="item in sideNav"
                :key="`${item.label}-${item.to}`"
                :to="item.to"
                class="side-item"
                :class="{ active: isActive(item.to, item.exact) }"
                @click="mobileMenuOpen = false"
              >
                {{ sidebarCompact ? item.short : item.label }}
              </RouterLink>
            </nav>

            <section class="today-card">
              <h3>今日統計</h3>
              <div class="stat-row"><span>今日收料</span><strong>{{ todayReceiptQty }} pcs</strong></div>
              <div class="stat-row"><span>今日退料</span><strong>{{ todayReturnQty }} pcs</strong></div>
              <div class="stat-row"><span>低水位治具</span><strong>{{ lowStockCount }} 項</strong></div>
            </section>
          </aside>

          <main id="main-content" class="page-content">
            <RouterView />
          </main>
        </div>
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
  width: 100%;
  background:
    radial-gradient(circle at top left, rgba(82, 126, 227, 0.08), transparent 28%),
    linear-gradient(180deg, #f6f8fc 0%, #eef2f8 100%);
}

.app-shell {
  height: 100dvh;
  width: 100%;
  background: #f5f7fb;
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
  width: min(420px, 100%);
  border: 1px solid var(--line);
  border-radius: 18px;
  background: #fff;
  box-shadow: var(--shadow);
  padding: 28px;
  display: grid;
  gap: 16px;
}

.login-eyebrow {
  margin: 0;
  color: var(--blue);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.login-card h1 {
  margin: 0;
  font-size: 28px;
  color: #1f2b45;
}

.login-copy {
  margin: 0;
  color: var(--muted);
  font-size: 14px;
}

.login-form {
  display: grid;
  gap: 12px;
}

.login-form label {
  display: grid;
  gap: 6px;
}

.login-form span {
  color: #55647e;
  font-size: 12px;
  font-weight: 700;
}

input,
select {
  width: 100%;
  border: 1px solid var(--line-strong);
  border-radius: 8px;
  padding: 8px 10px;
  background: #fff;
  color: var(--text);
}

.app-top-nav {
  min-height: 44px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 6px 10px;
  border-bottom: 1px solid var(--line);
  background: #fff;
}

.nav-toggle {
  display: none;
}

.top-nav-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.top-item {
  border: 1px solid var(--line-strong);
  border-radius: 8px;
  padding: 5px 10px;
  text-decoration: none;
  font-size: 12px;
  font-weight: 700;
  color: #324462;
  background: #fff;
}

.top-item.active {
  border-color: #a9c3f9;
  background: var(--blue-soft);
  color: var(--blue);
}

.top-meta {
  margin-left: auto;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.customer-picker {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #51617c;
  font-size: 12px;
  font-weight: 600;
}

.customer-scope {
  border: 1px solid #c9d8ee;
  border-radius: 999px;
  background: #eef5ff;
  color: #274a8e;
  font-size: 12px;
  font-weight: 700;
  padding: 6px 10px;
  white-space: nowrap;
}

.customer-scope.empty {
  border-color: #f0d6a5;
  background: #fff7e7;
  color: #9b5f00;
}

.customer-picker select {
  width: 170px;
  padding: 6px 10px;
}

.customer-create {
  display: flex;
  align-items: center;
  gap: 6px;
}

.customer-create input {
  width: 108px;
  padding: 6px 10px;
}

.who {
  color: #2a3854;
  font-size: 12px;
  font-weight: 700;
}

.body-shell {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: grid;
  grid-template-columns: minmax(72px, 212px) minmax(0, 1fr);
  gap: 8px;
  padding: 8px;
}

.side-nav {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #f7f9fd;
  padding: 10px 10px;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  overflow-y: auto;
  scrollbar-gutter: stable;
  transition: width 0.18s ease, padding 0.18s ease, gap 0.18s ease;
}

.side-nav.compact {
  padding: 10px 8px;
}

.side-nav-tools {
  display: none;
  margin-bottom: 10px;
}

.side-nav.compact .brand-copy,
.side-nav.compact .today-card {
  display: none;
}

.side-nav.compact .session-card {
  gap: 8px;
}

.side-nav.compact .brand-block h1 {
  font-size: 16px;
}

.side-nav.compact .side-menu {
  gap: 5px;
}

.side-nav.compact .side-item {
  text-align: center;
  padding-inline: 6px;
}

.side-nav.compact .side-nav-tools {
  display: block;
}

.brand-block {
  margin-bottom: 10px;
}

.brand-title {
  margin: 0 0 2px;
  color: #52627c;
  font-size: 12px;
  font-weight: 700;
}

.brand-block h1 {
  margin: 0;
  color: #1a2945;
  font-size: 20px;
  line-height: 1.15;
}

.brand-copy {
  margin: 6px 0 0;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.55;
}

.side-menu {
  display: grid;
  gap: 6px;
}

.side-item {
  border: 1px solid var(--line-strong);
  border-radius: 8px;
  padding: 7px 9px;
  text-decoration: none;
  color: #324462;
  font-size: 12px;
  font-weight: 700;
  background: #fff;
}

.side-item.active {
  border-color: var(--blue);
  background: var(--blue);
  color: #fff;
}

.today-card {
  border: 1px solid #dbe4f1;
  border-radius: 10px;
  background: #eef3fb;
  padding: 10px;
  display: grid;
  gap: 6px;
}

.today-card h3 {
  margin: 0;
  color: #21314c;
  font-size: 13px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #4d5d78;
  font-size: 12px;
}

.stat-row strong {
  color: #1f2b45;
}

.page-content {
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
}

.primary-btn {
  border: 1px solid var(--green);
  border-radius: 8px;
  background: linear-gradient(180deg, #4cc36b 0%, #2ea54e 100%);
  color: #fff;
  font-weight: 700;
  padding: 8px 14px;
  min-height: 36px;
  box-shadow: 0 8px 18px rgba(46, 165, 78, 0.18);
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
}

.outline-btn {
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  background: linear-gradient(180deg, #ffffff 0%, #f7f9fd 100%);
  color: #5b677d;
  font-weight: 700;
  padding: 8px 14px;
  min-height: 36px;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.8) inset;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}

.outline-btn.small {
  padding: 7px 12px;
  min-height: 32px;
}

.primary-btn:hover,
.outline-btn:hover,
.nav-toggle:hover {
  transform: translateY(-1px);
}

.primary-btn:hover {
  box-shadow: 0 10px 22px rgba(46, 165, 78, 0.24);
  filter: brightness(1.02);
}

.outline-btn:hover,
.nav-toggle:hover {
  border-color: #c0cad9;
  box-shadow: 0 4px 12px rgba(28, 47, 84, 0.08);
}

.primary-btn:active,
.outline-btn:active,
.nav-toggle:active {
  transform: translateY(0);
}

.primary-btn:disabled,
.outline-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

.toast-stack {
  position: absolute;
  top: 54px;
  right: 16px;
  z-index: 30;
  display: grid;
  gap: 8px;
  width: 300px;
  pointer-events: none;
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
  pointer-events: auto;
  animation: toast-in 0.18s ease-out;
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
  line-height: 1;
}

@keyframes toast-in {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 1280px) {
  .body-shell {
    grid-template-columns: 1fr;
  }

  .side-nav {
    display: none;
  }

  .side-nav.open {
    display: flex;
    gap: 12px;
    max-height: calc(100dvh - 64px);
  }

  .side-nav.compact .brand-copy,
  .side-nav.compact .today-card {
    display: block;
  }

  .side-nav-tools {
    display: none;
  }

  .nav-toggle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .shell-menu-toggle {
    display: inline-flex;
  }
}

@media (max-width: 920px) {
  .app-top-nav {
    align-items: stretch;
  }

  .nav-toggle {
    width: 100%;
    order: -1;
  }

  .top-nav-group,
  .top-meta {
    width: 100%;
  }

  .top-meta {
    margin-left: 0;
  }

  .top-meta > .outline-btn.small {
    width: 100%;
  }

  .customer-scope {
    width: 100%;
    white-space: normal;
    text-align: center;
  }

  .customer-picker {
    width: 100%;
    justify-content: space-between;
  }

  .customer-picker select {
    flex: 1;
    min-width: 0;
  }

  .customer-create {
    width: 100%;
    flex-direction: column;
    align-items: stretch;
  }

  .customer-create input {
    flex: 1 1 auto;
    min-width: 0;
    width: 100%;
  }

  .body-shell {
    padding: 8px;
  }

  .page-content {
    border-radius: 10px;
  }
}

@media (max-width: 640px) {
  .viewport-shell {
    background: #f6f8fc;
  }

  .login-shell {
    padding: 16px;
  }

  .login-card {
    padding: 20px;
  }

  .app-top-nav {
    padding: 8px;
  }

  .nav-toggle {
    padding: 8px 12px;
  }

  .top-item {
    flex: 1 1 120px;
    text-align: center;
  }

  .side-menu {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .today-card {
    margin-top: 0;
  }

  .toast-stack {
    left: 10px;
    right: 10px;
    width: auto;
    top: auto;
    bottom: 10px;
  }
}

.viewport-shell {
  min-height: 100dvh;
  width: 100%;
  background:
    radial-gradient(circle at 12% 0%, rgba(47, 110, 229, 0.16), transparent 30%),
    radial-gradient(circle at 88% 0%, rgba(32, 164, 92, 0.1), transparent 24%),
    linear-gradient(180deg, #f8fbff 0%, #edf3f9 100%);
}

.app-shell {
  position: relative;
  width: 100%;
  min-height: 100dvh;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.64) 0%, rgba(255, 255, 255, 0.28) 100%);
  backdrop-filter: blur(10px);
}

.shell-menu-toggle {
  position: fixed;
  top: 12px;
  left: 12px;
  z-index: 40;
  display: none;
}

.skip-link {
  position: absolute;
  top: 10px;
  left: 12px;
  z-index: 80;
  transform: translateY(-180%);
  padding: 8px 12px;
  border-radius: 999px;
  background: #0f213e;
  color: #fff;
  text-decoration: none;
  font-weight: 700;
  box-shadow: 0 12px 24px rgba(15, 33, 62, 0.22);
  transition: transform 0.16s ease;
}

.skip-link:focus-visible {
  transform: translateY(0);
}

.login-shell {
  padding: 28px;
}

.login-card {
  position: relative;
  width: min(460px, 100%);
  padding: 30px;
  border: 1px solid rgba(214, 224, 238, 0.94);
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(247, 250, 255, 0.96) 100%);
  box-shadow: 0 28px 60px rgba(28, 47, 84, 0.14);
  overflow: hidden;
}

.login-card::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 8px;
  background: linear-gradient(180deg, #2f6ee5 0%, #20a45c 100%);
}

.login-brand {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 10px;
}

.login-brand-mark {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: linear-gradient(180deg, #183055 0%, #0f213e 100%);
  color: #edf4ff;
  font-weight: 800;
  letter-spacing: 0.08em;
  box-shadow: 0 14px 28px rgba(15, 33, 62, 0.18);
}

.login-card h1 {
  text-wrap: balance;
}

.login-form {
  gap: 14px;
}

.login-form label {
  gap: 7px;
}

.login-form span {
  color: #51617c;
  font-size: 12px;
  font-weight: 700;
}

.login-form input {
  border-radius: 14px;
  padding: 10px 12px;
}

.outline-btn,
.ghost-btn,
.primary-btn {
  transform-origin: center;
}

.outline-btn:hover,
.ghost-btn:hover,
.primary-btn:hover {
  transform: translateY(-1px);
}

.app-top-nav {
  position: sticky;
  top: 0;
  z-index: 20;
  min-height: 56px;
  padding: 10px 12px;
  gap: 10px;
  border-bottom: 1px solid rgba(221, 229, 240, 0.94);
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(16px);
}

.top-nav-group {
  gap: 8px;
}

.top-item {
  border-radius: 999px;
  padding: 8px 13px;
  border-color: rgba(210, 220, 232, 1);
  background: linear-gradient(180deg, #ffffff 0%, #f6f9fd 100%);
}

.top-item.active {
  border-color: rgba(47, 110, 229, 0.24);
  background: linear-gradient(180deg, rgba(47, 110, 229, 0.12) 0%, rgba(32, 164, 92, 0.1) 100%);
  color: var(--blue);
}

.top-meta {
  gap: 8px;
}

.customer-scope {
  border: 1px solid rgba(191, 209, 241, 1);
  border-radius: 999px;
  background: linear-gradient(180deg, #f1f7ff 0%, #e7f0ff 100%);
  color: #2550a0;
  padding: 7px 12px;
  font-weight: 700;
}

.customer-scope.empty {
  border-color: rgba(238, 210, 155, 1);
  background: linear-gradient(180deg, #fff8ea 0%, #fff1d7 100%);
  color: #936100;
}

.customer-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.chip-dot {
  width: 9px;
  height: 9px;
  border-radius: 999px;
  background: var(--blue);
  box-shadow: 0 0 0 4px rgba(47, 110, 229, 0.12);
}

.customer-scope.empty .chip-dot {
  background: var(--orange);
  box-shadow: 0 0 0 4px rgba(224, 138, 30, 0.12);
}

.customer-picker {
  gap: 6px;
  color: #51617c;
  font-weight: 700;
}

.customer-picker select {
  width: 190px;
  border-radius: 999px;
}

.customer-create input {
  width: 116px;
  border-radius: 999px;
}

.user-avatar {
  width: 38px;
  height: 38px;
  border: 1px solid rgba(191, 209, 241, 1);
  border-radius: 999px;
  background: linear-gradient(180deg, #173255 0%, #0f213e 100%);
  color: #eef5ff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  box-shadow: 0 10px 18px rgba(15, 33, 62, 0.16);
}

.body-shell {
  padding: 12px;
  gap: 12px;
  grid-template-columns: minmax(236px, 252px) minmax(0, 1fr);
}

.side-nav {
  position: relative;
  padding: 14px;
  border: 1px solid rgba(216, 224, 236, 0.95);
  border-radius: 22px;
  background: linear-gradient(180deg, #ffffff 0%, #f7f9fd 100%);
  color: #324462;
  box-shadow: 0 18px 36px rgba(28, 47, 84, 0.08);
  overflow: hidden;
}

.side-nav::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at top left, rgba(47, 110, 229, 0.06), transparent 24%),
    radial-gradient(circle at bottom right, rgba(32, 164, 92, 0.05), transparent 30%);
  pointer-events: none;
}

.side-nav > * {
  position: relative;
}

.brand-block {
  margin-bottom: 12px;
}

.brand-title {
  margin: 0 0 5px;
  color: #56708f;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.brand-block h1 {
  color: #1a2945;
  font-size: 20px;
  line-height: 1.12;
  text-wrap: balance;
}

.brand-copy {
  color: #6f7d95;
}

.session-card {
  display: grid;
  gap: 10px;
  margin-bottom: 12px;
  padding: 12px;
  border: 1px solid #dbe4f1;
  border-radius: 18px;
  background: linear-gradient(180deg, #f8fbff 0%, #eef3fb 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.session-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.session-eyebrow {
  margin: 0 0 4px;
  color: #6b7891;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.session-top strong {
  display: block;
  color: #1f2b45;
  font-size: 14px;
  line-height: 1.2;
  word-break: break-word;
}

.session-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
}

.session-row span {
  color: #6f7d95;
  font-size: 12px;
  font-weight: 700;
}

.session-row strong {
  color: #21314c;
  font-size: 12px;
  font-weight: 800;
  text-align: right;
  word-break: break-word;
}

.session-picker select {
  width: 100%;
}

.session-actions {
  display: flex;
  gap: 8px;
}

.session-actions .outline-btn {
  flex: 1 1 0;
}

.side-menu {
  gap: 8px;
}

.side-item {
  display: flex;
  align-items: center;
  border-radius: 14px;
  padding: 10px 12px;
  border-color: rgba(207, 217, 230, 1);
  background: #ffffff;
  color: #324462;
}

.side-item:hover {
  border-color: rgba(173, 195, 227, 1);
  background: #f3f7ff;
}

.side-item.active {
  border-color: rgba(120, 170, 255, 0.46);
  background: linear-gradient(180deg, #eef5ff 0%, #e3eeff 100%);
  box-shadow: 0 8px 18px rgba(47, 110, 229, 0.08);
  color: var(--blue);
}

.today-card {
  margin-top: auto;
  padding: 12px;
  border: 1px solid rgba(216, 224, 236, 0.95);
  border-radius: 18px;
  background: linear-gradient(180deg, #f8fbff 0%, #eef3fb 100%);
  gap: 8px;
}

.today-card h3 {
  color: #21314c;
}

.today-card .stat-row {
  color: #596b83;
}

.today-card .stat-row strong {
  color: #1f2b45;
}

.page-content {
  border: 1px solid rgba(216, 224, 236, 0.9);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 22px 48px rgba(28, 47, 84, 0.1);
}

.toast-stack {
  top: 66px;
  right: 16px;
  width: 320px;
}

.toast-card {
  border-radius: 14px;
  border-color: rgba(216, 224, 236, 0.92);
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

@media (max-width: 1280px) {
  .body-shell {
    grid-template-columns: 1fr;
  }

  .side-nav {
    display: none;
  }

  .side-nav.open {
    display: flex;
    gap: 12px;
    max-height: calc(100dvh - 64px);
  }

  .nav-toggle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
}

@media (max-width: 920px) {
  .app-top-nav {
    align-items: stretch;
  }

  .nav-toggle {
    width: 100%;
    order: -1;
  }

  .top-nav-group,
  .top-meta {
    width: 100%;
  }

  .top-meta {
    margin-left: 0;
  }

  .top-meta > .outline-btn.small {
    width: 100%;
  }

  .customer-scope,
  .customer-picker,
  .customer-create {
    width: 100%;
  }

  .customer-picker select,
  .customer-create input {
    width: 100%;
    min-width: 0;
  }
}

@media (max-width: 640px) {
  .login-shell {
    padding: 16px;
  }

  .login-card {
    padding: 22px;
    border-radius: 20px;
  }

  .app-top-nav {
    padding: 8px;
  }

  .nav-toggle {
    padding: 8px 12px;
  }

  .top-item {
    flex: 1 1 120px;
    justify-content: center;
  }

  .body-shell {
    padding: 8px;
    gap: 8px;
  }

  .page-content {
    border-radius: 16px;
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
