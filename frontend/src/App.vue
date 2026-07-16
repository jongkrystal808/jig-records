<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { RouterView, useRoute, useRouter } from "vue-router";

import { api } from "@/api";
import {
  authSession,
  customers,
  onboardingActive,
  onboardingFlowId,
  onboardingPickerOpen,
  onboardingSandboxMode,
  onboardingStepIndex,
  resetSession,
  selectedCustomerId
} from "@/appState";
import AppAuthScreen from "@/components/app/AppAuthScreen.vue";
import AppGlobalModals from "@/components/app/AppGlobalModals.vue";
import AppMobileDrawer from "@/components/app/AppMobileDrawer.vue";
import AppReleaseNoticeModal from "@/components/app/AppReleaseNoticeModal.vue";
import AppToastStack from "@/components/app/AppToastStack.vue";
import AppTopbar from "@/components/app/AppTopbar.vue";
import GuidedTour from "@/components/common/GuidedTour.vue";
import OnboardingFlowPicker from "@/components/common/OnboardingFlowPicker.vue";
import { getOnboardingFlow, onboardingFlows } from "@/onboarding";
import { currentReleaseNotice } from "@/releaseNotice";
import { dismissToast, pushToast, toasts } from "@/toastState";
import type { MaterialTransaction } from "@/types";
import { formatLocalDateKey as formatDateKey } from "@/utils/date";
import type { OnboardingFlowId } from "@/onboarding";

const SESSION_KEY = "jig-record-session";
const CUSTOMER_KEY = "jig-record-customer-id";
const RELEASE_NOTICE_KEY = "jig-record-release-notice";

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
const releaseNoticeOpen = ref(false);

const currentCustomerId = computed(() => selectedCustomerId.value ?? undefined);
const selectedCustomer = computed(() => customers.value.find((row) => row.id === selectedCustomerId.value) ?? null);
const canEnterMaster = computed(() => authSession.value?.role !== "guest");
const canOperateInventory = computed(() => authSession.value?.role !== "guest");
const today = computed(() => formatDateKey(new Date()));
const currentOnboardingFlow = computed(() => getOnboardingFlow(onboardingFlowId.value));
const currentOnboardingSteps = computed(() => currentOnboardingFlow.value?.steps ?? []);
const currentOnboardingStep = computed(() => currentOnboardingSteps.value[onboardingStepIndex.value] ?? null);
const onboardingFlowCards = computed(() =>
  onboardingFlows.map((flow) => {
    let disabled = false;
    let disabledReason = "";
    if (flow.requiresInventoryAccess && !canOperateInventory.value) {
      disabled = true;
      disabledReason = "訪客不可操作收退料";
    } else if (flow.requiresMasterAccess && !canEnterMaster.value) {
      disabled = true;
      disabledReason = "訪客不可進入資料維護";
    }
    return {
      id: flow.id,
      sectionLabel: flow.sectionLabel,
      label: flow.label,
      summary: flow.summary,
      stepCount: flow.steps.length,
      disabled,
      disabledReason
    };
  })
);
const dateTimeFormatter = new Intl.DateTimeFormat("zh-TW", {
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit"
});

// Keep App.vue focused on session, routing, onboarding, and shared data refresh orchestration.

function closeActiveModal(): void {
  if (releaseNoticeOpen.value) {
    closeReleaseNotice();
    return;
  }
  if (exportModalOpen.value) {
    exportModalOpen.value = false;
    return;
  }
  if (batchModalOpen.value) {
    batchModalOpen.value = false;
  }
}

function handleGlobalKeydown(event: KeyboardEvent): void {
  if (event.key !== "Escape") {
    return;
  }
  closeActiveModal();
}

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

function maybeOpenReleaseNotice(): boolean {
  if (!currentReleaseNotice.versionId) {
    return false;
  }
  if (!authSession.value) {
    return false;
  }
  if (localStorage.getItem(RELEASE_NOTICE_KEY) === currentReleaseNotice.versionId) {
    return false;
  }
  releaseNoticeOpen.value = true;
  return true;
}

function closeReleaseNotice(): void {
  if (currentReleaseNotice.versionId) {
    localStorage.setItem(RELEASE_NOTICE_KEY, currentReleaseNotice.versionId);
  }
  releaseNoticeOpen.value = false;
}

function stopOnboarding(): void {
  onboardingPickerOpen.value = false;
  onboardingActive.value = false;
  onboardingFlowId.value = null;
  onboardingSandboxMode.value = false;
  batchModalOpen.value = false;
  exportModalOpen.value = false;
  moreMenuOpen.value = false;
  if (route.query.tour === "1") {
    void router.replace({ path: route.path, query: {} });
  }
}

function openOnboardingPicker(): void {
  const onboardingCustomerId = resolveOnboardingCustomerId();
  if (onboardingCustomerId === null) {
    pushToast("目前沒有可用客戶，無法啟動教學。", "warning");
    return;
  }
  selectedCustomerId.value = onboardingCustomerId;
  onboardingActive.value = false;
  onboardingStepIndex.value = 0;
  onboardingPickerOpen.value = true;
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
  onboardingSandboxMode.value = step.sandboxMode ?? false;
  batchModalOpen.value = step.openBatchModal ?? false;
  exportModalOpen.value = step.openExportModal ?? false;
  moreMenuOpen.value = step.openMoreMenu ?? false;
  if (route.path !== step.route) {
    await router.push({ path: step.route, query: { ...route.query, tour: "1" } });
    return;
  }
  if (route.query.tour !== "1") {
    await router.replace({ path: step.route, query: { ...route.query, tour: "1" } });
  }
}

async function nextOnboardingStep(): Promise<void> {
  if (onboardingStepIndex.value >= currentOnboardingSteps.value.length - 1) {
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

async function startOnboardingFlow(flowId: OnboardingFlowId): Promise<void> {
  const flow = getOnboardingFlow(flowId);
  if (!flow) {
    return;
  }
  if (flow.requiresInventoryAccess && !canOperateInventory.value) {
    pushToast("訪客模式不可操作收退料，請改看其他教學分類。", "warning");
    return;
  }
  if (flow.requiresMasterAccess && !canEnterMaster.value) {
    pushToast("訪客模式不可進入資料維護。", "warning");
    return;
  }
  const onboardingCustomerId = resolveOnboardingCustomerId();
  if (onboardingCustomerId === null) {
    pushToast("目前沒有可用客戶，無法啟動教學。", "warning");
    return;
  }
  selectedCustomerId.value = onboardingCustomerId;
  onboardingPickerOpen.value = false;
  onboardingFlowId.value = flow.id;
  onboardingStepIndex.value = 0;
  onboardingActive.value = true;
  await router.push({ path: flow.steps[0].route, query: { tour: "1" } });
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
    maybeOpenReleaseNotice();
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
    maybeOpenReleaseNotice();
    pushToast("已使用訪客入口登入", "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "訪客登入失敗", "error");
  } finally {
    loggingIn.value = false;
  }
}

function logout(): void {
  resetSession();
  releaseNoticeOpen.value = false;
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
  void router.push(canOperateInventory.value ? "/inventory" : "/inventory/overview");
}

function openBatchImport(): void {
  if (!canOperateInventory.value) {
    pushToast("訪客模式不可進行治具收/退料。", "warning");
    return;
  }
  moreMenuOpen.value = false;
  mobileMenuOpen.value = false;
  batchModalOpen.value = true;
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
    if (onboardingActive.value) {
      void syncOnboardingRoute();
    }
  }
);

onMounted(async () => {
  window.addEventListener("keydown", handleGlobalKeydown);
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
    maybeOpenReleaseNotice();
  }
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleGlobalKeydown);
});
</script>

<template>
  <div class="viewport-shell">
    <div class="app-shell">
      <template v-if="!authSession">
        <AppAuthScreen
          :username="loginForm.username"
          :password="loginForm.password"
          :logging-in="loggingIn"
          @update:username="loginForm.username = $event"
          @update:password="loginForm.password = $event"
          @login="login"
          @guest-entry="guestEntry"
        />
      </template>

      <template v-else>
        <GuidedTour
          :open="onboardingActive"
          :steps="currentOnboardingSteps"
          :current-index="onboardingStepIndex"
          @close="stopOnboarding"
          @next="nextOnboardingStep"
          @prev="prevOnboardingStep"
        />
        <OnboardingFlowPicker
          :open="onboardingPickerOpen"
          :flows="onboardingFlowCards"
          @close="onboardingPickerOpen = false"
          @select="startOnboardingFlow"
        />
        <AppTopbar
          :auth-display-name="authSession.display_name"
          :can-operate-inventory="canOperateInventory"
          :selected-customer-code="selectedCustomer?.code || ''"
          :customers="customers"
          :selected-customer-id="selectedCustomerId"
          :today-receipt-qty="todayReceiptQty"
          :today-return-qty="todayReturnQty"
          :low-stock-count="lowStockCount"
          :recent-receipt-entries="recentReceiptEntries"
          :recent-return-entries="recentReturnEntries"
          :low-stock-preview-entries="lowStockPreviewEntries"
          :has-more-low-stock-entries="hasMoreLowStockEntries"
          :menu-entries="menuEntries"
          :more-menu-open="moreMenuOpen"
          :format-hover-date="formatHoverDate"
          @toggle-mobile-menu="mobileMenuOpen = !mobileMenuOpen"
          @open-batch="openBatchImport"
          @open-export="openInventoryExport"
          @open-onboarding="openOnboardingPicker"
          @update:selected-customer-id="selectedCustomerId = $event"
          @toggle-more-menu="moreMenuOpen = !moreMenuOpen"
          @open-menu-route="openMenuRoute"
          @open-low-stock-page="openLowStockPage"
          @logout="logout"
        />

        <AppMobileDrawer
          :open="mobileMenuOpen"
          :auth-display-name="authSession.display_name"
          :can-operate-inventory="canOperateInventory"
          :selected-customer-code="selectedCustomer?.code || ''"
          :customers="customers"
          :selected-customer-id="selectedCustomerId"
          :today-receipt-qty="todayReceiptQty"
          :today-return-qty="todayReturnQty"
          :low-stock-count="lowStockCount"
          :menu-entries="menuEntries"
          @close="mobileMenuOpen = false"
          @update:selected-customer-id="selectedCustomerId = $event"
          @open-batch="openBatchImport"
          @open-export="openInventoryExport"
          @open-onboarding="openOnboardingPicker"
          @open-menu-route="openMenuRoute"
          @logout="logout"
        />

        <main class="page-shell">
          <RouterView />
        </main>

        <AppGlobalModals
          :batch-modal-open="batchModalOpen"
          :export-modal-open="exportModalOpen"
          :customer-id="currentCustomerId"
          @close-batch="batchModalOpen = false"
          @close-export="exportModalOpen = false"
          @refresh-stats="loadTopbarStats"
        />
        <AppReleaseNoticeModal
          :open="releaseNoticeOpen"
          :version-label="currentReleaseNotice.versionLabel"
          :title="currentReleaseNotice.title"
          :summary="currentReleaseNotice.summary"
          :highlights="currentReleaseNotice.highlights"
          @close="closeReleaseNotice"
        />
      </template>

      <AppToastStack :toasts="toasts" @dismiss="dismissToast" />
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

.page-shell {
  flex: 1;
  min-height: 0;
  padding: 12px;
  overflow: auto;
  -webkit-overflow-scrolling: touch;
}

@media (max-width: 720px) {
  .page-shell {
    padding: 8px;
  }
}
</style>
