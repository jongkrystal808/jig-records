<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "@/api";
import { completeSessionExpirationRedirect } from "@/api/core";
import {
  authSession,
  customers,
  inventoryBatchShortcutFixtureCode,
  inventoryBatchShortcutMode,
  inventoryBatchShortcutRequestId,
  onboardingActive,
  onboardingFlowId,
  onboardingPickerOpen,
  onboardingSandboxMode,
  onboardingStepIndex,
  resetSession,
  searchWorkspaceHandoffState,
  selectedCustomerId
} from "@/appState";
import AppAuthScreen from "@/components/app/AppAuthScreen.vue";
import AppGlobalModals from "@/components/app/AppGlobalModals.vue";
import AppMobileDrawer from "@/components/app/AppMobileDrawer.vue";
import FormSystemSurface from "@/components/app/FormSystemSurface.vue";
import WorkspaceSystemSurface from "@/components/app/WorkspaceSystemSurface.vue";
import AppToastStack from "@/components/app/AppToastStack.vue";
import AppTopbar from "@/components/app/AppTopbar.vue";
import GuidedTour from "@/components/common/GuidedTour.vue";
import HomeUiSurfaceSwitcher from "@/components/home/HomeUiSurfaceSwitcher.vue";
import OnboardingFlowPicker from "@/components/common/OnboardingFlowPicker.vue";
import SystemConfirmDialog from "@/components/common/SystemConfirmDialog.vue";
import { confirmationState, requestConfirmation, settleConfirmation } from "@/confirmState";
import {
  getOnboardingFlow,
  onboardingFlows,
  onboardingSurfaceForFlow,
  onboardingVariantForFlow
} from "@/onboarding";
import { dismissToast, pushToast, toasts } from "@/toastState";
import type { OnboardingFlowId, OnboardingSurface } from "@/onboarding";
import type { AuthSession } from "@/types";
import {
  clearSessionExpiredReturnPath,
  consumeSessionExpiredReturnPath,
  SESSION_EXPIRED_EVENT
} from "@/sessionExpiry";
import { formatLocalDate } from "@/utils/date";
import { canManageAccounts, canManageAdminReports } from "@/utils/roles";
import {
  buildReportModeQuery,
  buildWorkbenchQueryModeQuery,
  readWorkbenchQueryModeState
} from "@/utils/searchHomeModeState";
import {
  readSessionUiSurface,
  resolveAppUiSurface,
  UI_SURFACE_SESSION_KEY,
  uiSurfaceRouteQuery,
  type HomeUiSurface
} from "@/utils/uiSurface";
import {
  allowNextRouteNavigation,
  confirmUnsavedChanges,
  installUnsavedChangesBeforeUnloadGuard
} from "@/unsavedChangesGuard";

const SESSION_KEY = "jig-record-session";
const CUSTOMER_KEY = "jig-record-customer-id";
const UI_SURFACE_PREFERENCE_PREFIX = "home-ui-surface-default";
const LEGACY_UI_SURFACE_PREFERENCE_PREFIX = "search-home-default-mode";

type TopbarRecentEntry = {
  id: string;
  occurredAt: string;
  transactionNo: string | null;
  fixtureCode: string;
  identifier: string;
  quantity: number;
};

function onboardingSurfaceForAppSurface(surface: HomeUiSurface): OnboardingSurface {
  return surface === "workspace" ? "workbench" : surface;
}

const route = useRoute();
const router = useRouter();

function surfacePreferenceKey(prefix: string, session: AuthSession): string {
  const identity = session.user?.id ?? session.user?.username ?? session.display_name;
  return `${prefix}:${identity}`;
}

function roleDefaultSurface(_session: AuthSession | null): HomeUiSurface {
  return "workspace";
}

function readPreferredSurface(session: AuthSession | null): HomeUiSurface {
  const fallback = roleDefaultSurface(session);
  if (!session || session.role === "guest") return fallback;
  try {
    const saved = window.localStorage.getItem(surfacePreferenceKey(UI_SURFACE_PREFERENCE_PREFIX, session));
    if (saved === "form" || saved === "workspace") return saved;
    if (saved === "modern" || saved === "workbench") return "workspace";
    const legacy = window.localStorage.getItem(surfacePreferenceKey(LEGACY_UI_SURFACE_PREFERENCE_PREFIX, session));
    if (legacy === "query") return "workspace";
    if (legacy === "report") return "form";
  } catch {
    return fallback;
  }
  return fallback;
}

const preferredAppUiSurface = ref<HomeUiSurface>(readPreferredSurface(authSession.value));
const activeAppUiSurface = ref<HomeUiSurface>(
  resolveAppUiSurface(
    route.path,
    route.query.ui_surface,
    route.query.home_mode,
    readSessionUiSurface() ?? preferredAppUiSurface.value
  )
);
if (authSession.value) {
  try {
    window.sessionStorage.setItem(UI_SURFACE_SESSION_KEY, activeAppUiSurface.value);
  } catch {
    // Storage may be unavailable in hardened browser modes; route state remains authoritative.
  }
}
const isSwitchingAppUiSurface = ref(false);
const todayReceiptQty = ref(0);
const todayReturnQty = ref(0);
const lowStockCount = ref(0);
const recentReceiptEntries = ref<TopbarRecentEntry[]>([]);
const recentReturnEntries = ref<TopbarRecentEntry[]>([]);
const lowStockPreviewEntries = ref<Array<{ fixture_id: number; fixture_code: string; fixture_name: string; stock_qty: number; min_stock_qty: number; stock_status: "low_stock" | "out_of_stock" }>>([]);
const hasMoreLowStockEntries = ref(false);
const loginForm = ref({ username: "", password: "" });
const loggingIn = ref(false);
const moreMenuOpen = ref(false);
const mobileMenuOpen = ref(false);
const batchModalOpen = ref(false);
const exportModalOpen = ref(false);
const passwordModalOpen = ref(false);
let beforeUnloadGuardCleanup: (() => void) | null = null;
const batchPresetFixtureCode = ref("");
const batchPresetMode = ref<"receipt" | "return">("receipt");
const onboardingReturnFullPath = ref("");
const onboardingPickerSurface = ref<OnboardingSurface>(
  onboardingSurfaceForAppSurface(activeAppUiSurface.value)
);
const batchDraftState = ref({
  hasPendingDraft: false,
  pendingRowCount: 0,
  promptMessage: ""
});

const currentCustomerId = computed(() => selectedCustomerId.value ?? undefined);
const currentRole = computed(() => authSession.value?.role ?? "guest");
const selectedCustomer = computed(() => customers.value.find((row) => row.id === selectedCustomerId.value) ?? null);
const canEnterMaster = computed(() => authSession.value?.role !== "guest");
const canEnterProduction = computed(() => authSession.value?.role !== "guest");
const canOperateInventory = computed(() => authSession.value?.role !== "guest");
const canAccessAdminOnboarding = computed(() => canManageAdminReports(authSession.value?.role));
const canAccessSuperAdminOnboarding = computed(() => canManageAccounts(authSession.value?.role));
const isGuest = computed(() => authSession.value?.role === "guest");
const isFormSystemActive = computed(() => activeAppUiSurface.value === "form");
const showModernChrome = computed(() => activeAppUiSurface.value === "workspace");
const topbarOnboardingSurface = computed<OnboardingSurface>(() =>
  activeAppUiSurface.value === "workspace" && (
    route.path === "/search" ||
    route.path === "/inventory" ||
    route.path === "/inventory/overview"
  )
    ? "workbench"
    : "modern"
);
const currentOnboardingFlow = computed(() => getOnboardingFlow(onboardingFlowId.value));
const currentOnboardingSteps = computed(() =>
  (currentOnboardingFlow.value?.steps ?? []).filter(
    (step) =>
      (!step.requiresAdminAccess || canAccessAdminOnboarding.value) &&
      (!step.requiresSuperAdminAccess || canAccessSuperAdminOnboarding.value)
  )
);
const currentOnboardingStep = computed(() => currentOnboardingSteps.value[onboardingStepIndex.value] ?? null);
const onboardingFlowCards = computed(() =>
  onboardingFlows
    .filter((flow) => {
      const roleMatches = currentRole.value === "guest"
        ? flow.guestOnly === true
        : flow.guestOnly !== true;
      return roleMatches && onboardingSurfaceForFlow(flow) === onboardingPickerSurface.value;
    })
    .map((flow) => {
      let disabled = false;
      let disabledReason = "";
      if (flow.requiresInventoryAccess && !canOperateInventory.value) {
        disabled = true;
        disabledReason = "訪客不可操作收退料";
      } else if (flow.requiresMasterAccess && !canEnterMaster.value) {
        disabled = true;
        disabledReason = "訪客不可進入資料維護";
      } else if (flow.requiresAdminAccess && !canAccessAdminOnboarding.value) {
        disabled = true;
        disabledReason = "只有 Admin 可觀看這組教學";
      } else if (flow.requiresSuperAdminAccess && !canAccessSuperAdminOnboarding.value) {
        disabled = true;
        disabledReason = "只有 Super Admin 可觀看這組教學";
      }
      return {
        id: flow.id,
        sectionLabel: flow.sectionLabel,
        label: flow.label,
        summary: flow.summary,
        stepCount: flow.steps.length,
        disabled,
        disabledReason,
        variant: onboardingVariantForFlow(flow)
      };
    })
);
// Keep App.vue focused on session, routing, onboarding, and shared data refresh orchestration.

function closeActiveModal(): void {
  if (passwordModalOpen.value) {
    passwordModalOpen.value = false;
    return;
  }
  if (exportModalOpen.value) {
    exportModalOpen.value = false;
    return;
  }
  if (batchModalOpen.value) {
    void closeBatchModal();
  }
}

function handleGlobalKeydown(event: KeyboardEvent): void {
  if (event.key !== "Escape") {
    return;
  }
  closeActiveModal();
}

const menuEntries = computed(() =>
  [
    { label: "治具收納", to: "/storage", disabled: false },
    canEnterMaster.value ? { label: "資料維護", to: "/master", disabled: false } : null,
    canEnterProduction.value ? { label: "產能管理", to: "/production", disabled: false } : null
  ].filter((entry): entry is { label: string; to: string; disabled: boolean } => entry !== null)
);

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

async function stopOnboarding(): Promise<void> {
  const returnFullPath = onboardingReturnFullPath.value;
  onboardingReturnFullPath.value = "";
  onboardingPickerOpen.value = false;
  onboardingActive.value = false;
  onboardingFlowId.value = null;
  onboardingSandboxMode.value = false;
  batchModalOpen.value = false;
  exportModalOpen.value = false;
  moreMenuOpen.value = false;
  if (returnFullPath) {
    await router.replace(returnFullPath);
    return;
  }
  if (route.query.tour === "1") {
    const nextQuery = { ...route.query };
    delete nextQuery.tour;
    await router.replace({ path: route.path, query: nextQuery });
  }
}

function openOnboardingPicker(
  surface: OnboardingSurface = onboardingSurfaceForAppSurface(activeAppUiSurface.value)
): void {
  const onboardingCustomerId = resolveOnboardingCustomerId();
  if (onboardingCustomerId === null) {
    pushToast("目前沒有可用客戶，無法啟動教學。", "warning");
    return;
  }
  selectedCustomerId.value = onboardingCustomerId;
  onboardingActive.value = false;
  onboardingStepIndex.value = 0;
  onboardingPickerSurface.value = surface;
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
  const targetQuery = {
    ...route.query,
    ...(step.query ?? {}),
    tour: "1"
  };
  if (route.path !== step.route) {
    await router.push({ path: step.route, query: targetQuery });
    return;
  }
  const stepQueryChanged = Object.entries(step.query ?? {}).some(
    ([key, value]) => route.query[key] !== value
  );
  if (route.query.tour !== "1" || stepQueryChanged) {
    await router.replace({ path: step.route, query: targetQuery });
  }
}

async function nextOnboardingStep(): Promise<void> {
  if (onboardingStepIndex.value >= currentOnboardingSteps.value.length - 1) {
    await stopOnboarding();
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
  if (flow.requiresAdminAccess && !canAccessAdminOnboarding.value) {
    pushToast("只有 Admin 可觀看這組教學。", "warning");
    return;
  }
  if (flow.requiresSuperAdminAccess && !canAccessSuperAdminOnboarding.value) {
    pushToast("只有 Super Admin 可觀看這組教學。", "warning");
    return;
  }
  const onboardingCustomerId = resolveOnboardingCustomerId();
  if (onboardingCustomerId === null) {
    pushToast("目前沒有可用客戶，無法啟動教學。", "warning");
    return;
  }
  const onboardingTargetSurface = onboardingSurfaceForFlow(flow);
  const targetSurface: HomeUiSurface = onboardingTargetSurface === "form" ? "form" : "workspace";
  if (targetSurface !== activeAppUiSurface.value) {
    await selectAppUiSurface(targetSurface);
    if (targetSurface !== activeAppUiSurface.value) {
      pushToast("請先完成或放棄目前未儲存內容，再啟動另一套介面的教學。", "warning");
      return;
    }
  }
  selectedCustomerId.value = onboardingCustomerId;
  onboardingReturnFullPath.value = route.fullPath;
  onboardingPickerOpen.value = false;
  onboardingFlowId.value = flow.id;
  onboardingStepIndex.value = 0;
  onboardingActive.value = true;
  await router.push({
    path: flow.steps[0].route,
    query: {
      ...(flow.steps[0].query ?? {}),
      tour: "1"
    }
  });
}

async function loadTopbarStats(): Promise<void> {
  try {
    const summary = await api.listDashboardSummary(currentCustomerId.value);
    lowStockPreviewEntries.value = summary.low_stock_preview_entries;
    hasMoreLowStockEntries.value = summary.has_more_low_stock_entries;
    lowStockCount.value = summary.low_stock_count;
    todayReceiptQty.value = summary.today_receipt_qty;
    todayReturnQty.value = summary.today_return_qty;
    recentReceiptEntries.value = summary.recent_receipt_entries.map((entry) => ({
      id: `receipt-${entry.transaction_item_id}`,
      occurredAt: entry.occurred_at,
      transactionNo: entry.transaction_no,
      fixtureCode: entry.fixture_code,
      identifier: entry.identifier || "-",
      quantity: entry.quantity
    }));
    recentReturnEntries.value = summary.recent_return_entries.map((entry) => ({
      id: `return-${entry.transaction_item_id}`,
      occurredAt: entry.occurred_at,
      transactionNo: entry.transaction_no,
      fixtureCode: entry.fixture_code,
      identifier: entry.identifier || "-",
      quantity: entry.quantity
    }));
  } catch {
    recentReceiptEntries.value = [];
    recentReturnEntries.value = [];
    lowStockPreviewEntries.value = [];
    hasMoreLowStockEntries.value = false;
    todayReceiptQty.value = 0;
    todayReturnQty.value = 0;
    lowStockCount.value = 0;
  }
}

function formatHoverDate(value: string): string {
  return formatLocalDate(value);
}

async function navigateAfterAuthentication(): Promise<void> {
  const returnPath = consumeSessionExpiredReturnPath();
  completeSessionExpirationRedirect();
  if (route.path === "/login") {
    await router.replace(returnPath || "/search");
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
    await loadTopbarStats();
    await navigateAfterAuthentication();
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
    await navigateAfterAuthentication();
    pushToast("已使用訪客入口登入", "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "訪客登入失敗", "error");
  } finally {
    loggingIn.value = false;
  }
}

async function logout(): Promise<void> {
  if (!(await confirmUnsavedChanges("logout"))) return;
  clearSessionExpiredReturnPath();
  completeSessionExpirationRedirect();
  resetSession();
  sessionStorage.removeItem(UI_SURFACE_SESSION_KEY);
  recentReceiptEntries.value = [];
  recentReturnEntries.value = [];
  lowStockPreviewEntries.value = [];
  hasMoreLowStockEntries.value = false;
  todayReceiptQty.value = 0;
  todayReturnQty.value = 0;
  lowStockCount.value = 0;
  mobileMenuOpen.value = false;
  moreMenuOpen.value = false;
  await closeBatchModal(true);
  exportModalOpen.value = false;
  passwordModalOpen.value = false;
  await router.replace({ name: "login" });
  pushToast("已登出", "info");
}

function handleSessionExpired(): void {
  recentReceiptEntries.value = [];
  recentReturnEntries.value = [];
  lowStockPreviewEntries.value = [];
  hasMoreLowStockEntries.value = false;
  todayReceiptQty.value = 0;
  todayReturnQty.value = 0;
  lowStockCount.value = 0;
  mobileMenuOpen.value = false;
  moreMenuOpen.value = false;
  batchModalOpen.value = false;
  exportModalOpen.value = false;
  passwordModalOpen.value = false;
  void router.replace({ name: "login" });
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

function updateBatchDraftState(value: { hasPendingDraft: boolean; pendingRowCount: number; promptMessage: string }): void {
  batchDraftState.value = value;
}

async function confirmBatchModalClose(): Promise<boolean> {
  if (!batchDraftState.value.hasPendingDraft) {
    return true;
  }
  return requestConfirmation(
    batchDraftState.value.promptMessage || "目前有尚未送出的草稿，確定離開嗎？",
    { title: "捨棄收退料草稿？", confirmLabel: "捨棄並離開", tone: "danger" }
  );
}

async function closeBatchModal(force = false): Promise<boolean> {
  if (batchModalOpen.value && !force && !(await confirmBatchModalClose())) {
    return false;
  }
  batchModalOpen.value = false;
  batchPresetFixtureCode.value = "";
  batchPresetMode.value = "receipt";
  batchDraftState.value = {
    hasPendingDraft: false,
    pendingRowCount: 0,
    promptMessage: ""
  };
  return true;
}

async function openInventoryOverviewFromBatch(): Promise<void> {
  if (!(await closeBatchModal())) {
    return;
  }
  void router.push("/inventory/overview");
}

function openBatchImport(
  fixtureCode?: string,
  mode: "receipt" | "return" = "receipt"
): void {
  if (!canOperateInventory.value) {
    pushToast("訪客模式不可進行治具收/退料。", "warning");
    return;
  }
  moreMenuOpen.value = false;
  mobileMenuOpen.value = false;
  if (isFormSystemActive.value && !(fixtureCode ?? "").trim()) {
    void router.push("/inventory");
    return;
  }
  batchPresetFixtureCode.value = (fixtureCode ?? "").trim().toUpperCase();
  batchPresetMode.value = mode;
  batchModalOpen.value = true;
}

function openInventoryExport(): void {
  moreMenuOpen.value = false;
  mobileMenuOpen.value = false;
  exportModalOpen.value = true;
}

async function confirmCustomerSwitch(nextCustomerId: number | null): Promise<boolean> {
  if (nextCustomerId === selectedCustomerId.value) {
    return false;
  }
  return confirmUnsavedChanges("customer");
}

async function updateSelectedCustomer(nextCustomerId: number | null): Promise<void> {
  if (nextCustomerId === selectedCustomerId.value) {
    return;
  }
  if (!(await confirmCustomerSwitch(nextCustomerId))) {
    return;
  }
  await closeBatchModal(true);
  selectedCustomerId.value = nextCustomerId;
}

async function canSwitchAppUiSurface(nextSurface: HomeUiSurface): Promise<boolean> {
  if (nextSurface === activeAppUiSurface.value) return false;
  return confirmUnsavedChanges("surface", {
    title: `切換到 ${surfaceDisplayName(nextSurface)}？`
  });
}

function surfaceDisplayName(surface: HomeUiSurface): string {
  if (surface === "form") return "Form UI";
  return "Workspace UI";
}

async function selectAppUiSurface(nextSurface: HomeUiSurface): Promise<void> {
  if (isSwitchingAppUiSurface.value || !(await canSwitchAppUiSurface(nextSurface))) return;

  let nextPath = route.path;
  let nextQuery = { ...route.query, ...uiSurfaceRouteQuery(nextSurface) };
  if (route.path === "/search" || route.path === "/search/detail") {
    nextPath = "/search";
    const handoffState = activeAppUiSurface.value === "workspace"
      ? readWorkbenchQueryModeState(route.query) ?? searchWorkspaceHandoffState.value
      : searchWorkspaceHandoffState.value;
    nextQuery = nextSurface === "form"
      ? buildReportModeQuery(handoffState, selectedCustomerId.value)
      : buildWorkbenchQueryModeQuery(handoffState, selectedCustomerId.value, "workspace");
  }

  isSwitchingAppUiSurface.value = true;
  activeAppUiSurface.value = nextSurface;
  try {
    sessionStorage.setItem(UI_SURFACE_SESSION_KEY, nextSurface);
    if (nextPath !== route.path) allowNextRouteNavigation();
    await router.replace({ path: nextPath, query: nextQuery });
  } finally {
    isSwitchingAppUiSurface.value = false;
  }
}

function saveAppUiSurfaceAsDefault(surface: HomeUiSurface): void {
  const session = authSession.value;
  if (!session || session.role === "guest") return;
  try {
    localStorage.setItem(
      surfacePreferenceKey(UI_SURFACE_PREFERENCE_PREFIX, session),
      surface
    );
    preferredAppUiSurface.value = surface;
    pushToast(
      `已將「${surfaceDisplayName(surface)}」設為整個系統的登入預設介面。`,
      "success"
    );
  } catch {
    pushToast("無法儲存介面偏好，請確認瀏覽器允許本機儲存。", "error");
  }
}

watch(authSession, (value) => {
  if (value) {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(value));
  } else {
    sessionStorage.removeItem(SESSION_KEY);
  }
});

watch(
  () => [route.query.ui_surface, route.query.home_mode] as const,
  () => {
    const resolved = resolveAppUiSurface(
      route.path,
      route.query.ui_surface,
      route.query.home_mode,
      activeAppUiSurface.value
    );
    if (resolved !== activeAppUiSurface.value) {
      activeAppUiSurface.value = resolved;
      sessionStorage.setItem(UI_SURFACE_SESSION_KEY, resolved);
    }
  }
);

watch(
  () => `${authSession.value?.role ?? ""}:${authSession.value?.user?.id ?? authSession.value?.display_name ?? ""}`,
  () => {
    const session = authSession.value;
    preferredAppUiSurface.value = readPreferredSurface(session);
    activeAppUiSurface.value = resolveAppUiSurface(
      route.path,
      route.query.ui_surface,
      route.query.home_mode,
      preferredAppUiSurface.value
    );
    try {
      if (session) {
        sessionStorage.setItem(UI_SURFACE_SESSION_KEY, activeAppUiSurface.value);
      } else {
        sessionStorage.removeItem(UI_SURFACE_SESSION_KEY);
      }
    } catch {
      // Keep the in-memory surface when session storage is unavailable.
    }
  }
);

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

watch(inventoryBatchShortcutRequestId, () => {
  openBatchImport(inventoryBatchShortcutFixtureCode.value, inventoryBatchShortcutMode.value);
});

onMounted(async () => {
  beforeUnloadGuardCleanup = installUnsavedChangesBeforeUnloadGuard();
  window.addEventListener("keydown", handleGlobalKeydown);
  window.addEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired);
  if (authSession.value) {
    await loadCustomers();
    await loadTopbarStats();
  }
});

onBeforeUnmount(() => {
  beforeUnloadGuardCleanup?.();
  beforeUnloadGuardCleanup = null;
  window.removeEventListener("keydown", handleGlobalKeydown);
  window.removeEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired);
});
</script>

<template>
  <div class="viewport-shell">
    <div class="app-shell" :data-ui-surface="activeAppUiSurface">
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
          :flow-label="currentOnboardingFlow?.label"
          :flow-section-label="currentOnboardingFlow?.sectionLabel"
          @close="stopOnboarding"
          @next="nextOnboardingStep"
          @prev="prevOnboardingStep"
        />
        <OnboardingFlowPicker
          :open="onboardingPickerOpen"
          :flows="onboardingFlowCards"
          :role="currentRole"
          :surface="onboardingPickerSurface"
          @close="onboardingPickerOpen = false"
          @select="startOnboardingFlow"
        />
        <AppTopbar
          v-if="showModernChrome"
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
          onboarding-label="Workspace UI 教學"
          @toggle-mobile-menu="mobileMenuOpen = !mobileMenuOpen"
          @open-batch="openBatchImport"
          @open-export="openInventoryExport"
          @open-onboarding="openOnboardingPicker(topbarOnboardingSurface)"
          @open-password="passwordModalOpen = true"
          @update:selected-customer-id="updateSelectedCustomer"
          @toggle-more-menu="moreMenuOpen = !moreMenuOpen"
          @open-menu-route="openMenuRoute"
          @open-low-stock-page="openLowStockPage"
          @logout="logout"
        >
          <template #ui-switcher>
            <HomeUiSurfaceSwitcher
              compact
              :active-surface="activeAppUiSurface"
              :preferred-surface="preferredAppUiSurface"
              :is-guest="isGuest"
              :switching="isSwitchingAppUiSurface"
              @select="selectAppUiSurface"
              @save-default="saveAppUiSurfaceAsDefault"
            />
          </template>
        </AppTopbar>

        <AppMobileDrawer
          v-if="showModernChrome"
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
          onboarding-label="Workspace UI 教學"
          @close="mobileMenuOpen = false"
          @update:selected-customer-id="updateSelectedCustomer"
          @open-batch="openBatchImport"
          @open-export="openInventoryExport"
          @open-onboarding="openOnboardingPicker(topbarOnboardingSurface)"
          @open-password="passwordModalOpen = true"
          @open-menu-route="openMenuRoute"
          @logout="logout"
        />

        <main class="page-shell" :class="`page-shell--${activeAppUiSurface}`">
          <Transition name="app-ui-surface" mode="out-in">
            <FormSystemSurface
              v-if="activeAppUiSurface === 'form'"
              key="form"
              @update:selected-customer-id="updateSelectedCustomer"
            >
              <template #ui-switcher>
                <HomeUiSurfaceSwitcher
                  compact
                  :active-surface="activeAppUiSurface"
                  :preferred-surface="preferredAppUiSurface"
                  :is-guest="isGuest"
                  :switching="isSwitchingAppUiSurface"
                  @select="selectAppUiSurface"
                  @save-default="saveAppUiSurfaceAsDefault"
                />
              </template>
              <template #heading-actions>
                <button
                  class="form-heading-action"
                  data-tour="form-onboarding-entry"
                  type="button"
                  @click="openOnboardingPicker('form')"
                >
                  Form UI 教學
                </button>
              </template>
              <template #account-action>
                <button
                  v-if="!isGuest"
                  class="form-heading-action"
                  type="button"
                  @click="passwordModalOpen = true"
                >
                  修改密碼
                </button>
                <button
                  class="form-heading-action form-heading-logout"
                  data-tour="detailed-logout-button"
                  type="button"
                  @click="logout"
                >
                  登出
                </button>
              </template>
            </FormSystemSurface>
            <WorkspaceSystemSurface
              v-else
              key="workspace"
              @update:selected-customer-id="updateSelectedCustomer"
              @open-export="openInventoryExport"
            >
              <template #ui-switcher>
                <HomeUiSurfaceSwitcher
                  compact
                  :active-surface="activeAppUiSurface"
                  :preferred-surface="preferredAppUiSurface"
                  :is-guest="isGuest"
                  :switching="isSwitchingAppUiSurface"
                  @select="selectAppUiSurface"
                  @save-default="saveAppUiSurfaceAsDefault"
                />
              </template>
              <template #heading-actions>
                <button
                  class="form-heading-action"
                  data-tour="workbench-onboarding-entry"
                  type="button"
                  @click="openOnboardingPicker('workbench')"
                >
                  快速作業教學
                </button>
              </template>
              <template #account-action>
                <button
                  v-if="!isGuest"
                  class="form-heading-action"
                  type="button"
                  @click="passwordModalOpen = true"
                >
                  修改密碼
                </button>
                <button
                  class="form-heading-action form-heading-logout"
                  data-tour="detailed-logout-button"
                  type="button"
                  @click="logout"
                >
                  登出
                </button>
              </template>
            </WorkspaceSystemSurface>
          </Transition>
        </main>

        <AppGlobalModals
          :batch-modal-open="batchModalOpen"
          :export-modal-open="exportModalOpen"
          :password-modal-open="passwordModalOpen"
          :customer-id="currentCustomerId"
          :role="currentRole"
          :batch-preset-fixture-code="batchPresetFixtureCode"
          :batch-preset-mode="batchPresetMode"
          @close-batch="closeBatchModal"
          @close-export="exportModalOpen = false"
          @close-password="passwordModalOpen = false"
          @open-overview-from-batch="openInventoryOverviewFromBatch"
          @batch-draft-state-change="updateBatchDraftState"
          @refresh-stats="loadTopbarStats"
        />
      </template>

      <AppToastStack :toasts="toasts" @dismiss="dismissToast" />
      <SystemConfirmDialog
        :open="confirmationState.open"
        :title="confirmationState.title"
        :message="confirmationState.message"
        :confirm-label="confirmationState.confirmLabel"
        :cancel-label="confirmationState.cancelLabel"
        :tone="confirmationState.tone"
        @confirm="settleConfirmation(true)"
        @cancel="settleConfirmation(false)"
      />
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

.app-ui-surface-enter-active,
.app-ui-surface-leave-active {
  transition: opacity 140ms ease, transform 180ms ease;
}

.app-ui-surface-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.app-ui-surface-leave-to {
  opacity: 0;
  transform: translateY(-3px);
}

@media (prefers-reduced-motion: reduce) {
  .app-ui-surface-enter-active,
  .app-ui-surface-leave-active {
    transition: none;
  }
}

@media (max-width: 720px) {
  .page-shell {
    padding: 8px;
  }
}
</style>
