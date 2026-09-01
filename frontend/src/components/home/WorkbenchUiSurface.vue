<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import type { LocationQueryRaw } from "vue-router";

import { api, fetchFixtureImageObjectUrl } from "@/api";
import { ApiRequestError } from "@/api/core";
import { authSession, customers, selectedCustomerId } from "@/appState";
import WorkbenchBatchOperations from "@/components/home/WorkbenchBatchOperations.vue";
import FixtureEditForm from "@/components/search/FixtureEditForm.vue";
import ModelEditForm from "@/components/search/ModelEditForm.vue";
import { requestConfirmation } from "@/confirmState";
import { pushToast } from "@/toastState";
import type {
  AppUser,
  Fixture,
  MachineModel,
  ModelShortcutPreference,
  SearchFixtureContext,
  SearchModelContext,
  SearchResult,
  TransactionOverviewRow
} from "@/types";
import { setUnsavedChangesGuard } from "@/unsavedChangesGuard";
import { formatLocalDate } from "@/utils/date";
import { normalizeIdentifierForWrite } from "@/utils/identifier";
import { uiSurfaceRouteQuery } from "@/utils/uiSurface";
import { canManageAdminReports, canOperate as canOperateRole, roleLabel } from "@/utils/roles";

export type WorkbenchMode = "transaction" | "fixture" | "model" | "management";
type TransactionDirection = "receipt" | "return";
type FixtureSearchMode = "fixture" | "identifier";
type RelatedSearchTarget = {
  id: number;
  code: string;
  name: string;
};
type RelatedSearchSuggestion = {
  sourceKind: "fixture" | "model";
  sourceCode: string;
  targetMode: "fixture" | "model";
  targets: RelatedSearchTarget[];
};

const props = withDefaults(defineProps<{
  surface?: "workbench" | "workspace";
  showHeader?: boolean;
}>(), {
  surface: "workbench",
  showHeader: true
});

const emit = defineEmits<{
  "update:selectedCustomerId": [value: number | null];
  openExport: [];
}>();

const route = useRoute();
const router = useRouter();

function initialMode(): WorkbenchMode {
  const requested = String(route.query.workbench_mode ?? "");
  if (requested === "receipt" || requested === "return" || requested === "transaction") return "transaction";
  if (requested === "fixture" || requested === "model" || requested === "management") return requested;
  return route.path === "/inventory" ? "transaction" : "fixture";
}

function initialTransactionDirection(): TransactionDirection {
  const requested = String(route.query.transaction_type ?? route.query.workbench_mode ?? "");
  return requested === "return" ? "return" : "receipt";
}

const activeMode = ref<WorkbenchMode>(initialMode());
const transactionDirection = ref<TransactionDirection>(initialTransactionDirection());
const query = ref(String(route.query.q ?? ""));
const fixtureSearchMode = ref<FixtureSearchMode>(route.query.fixture_search === "identifier" ? "identifier" : "fixture");
const loading = ref(false);
const submitting = ref(false);
const fixtures = ref<Fixture[]>([]);
const models = ref<MachineModel[]>([]);
const recentTransactionRows = ref<TransactionOverviewRow[]>([]);
const recentTotal = ref(0);
const recentLoading = ref(false);
const searchResults = ref<SearchResult[]>([]);
const fixtureContext = ref<SearchFixtureContext | null>(null);
const modelContext = ref<SearchModelContext | null>(null);
const imageUrl = ref("");
const imageMissing = ref(false);
const batchPanelOpen = ref(route.query.workbench_batch === "true");
const resultsPanel = ref<HTMLElement | null>(null);
const lastSearchMiss = ref<{ token: string; entityLabel: "治具" | "機種" } | null>(null);
const relatedSearchSuggestion = ref<RelatedSearchSuggestion | null>(null);
const inlineEditMode = ref<"fixture" | "model" | null>(null);
const inlineEditDirty = ref(false);
const inlineEditLoading = ref(false);
const inlineEditUsers = ref<AppUser[]>([]);
const recentPage = ref(1);
const RECENT_PAGE_SIZE = 50;
let syncingWorkbenchRoute = false;
let workbenchRouteReady = false;

type ModelShortcutUsage = Record<string, {
  queryCount: number;
  lastQueriedAt: number;
  pinned: boolean;
}>;

const modelShortcutUsage = ref<ModelShortcutUsage>({});

const transactionForm = ref({
  transactionNo: "",
  fixtureCode: "",
  identifier: "",
  quantity: 1,
  ownershipType: "customer_supplied" as "customer_supplied" | "self_purchased",
  note: ""
});

const canOperate = computed(() => canOperateRole(authSession.value?.role));
const canInlineEdit = computed(() => props.surface === "workspace" && canManageAdminReports(authSession.value?.role));
const isTransactionMode = computed(() => activeMode.value === "transaction");
const batchMode = computed<TransactionDirection>(() => transactionDirection.value);
const currentCustomer = computed(() => customers.value.find((row) => row.id === selectedCustomerId.value) ?? null);
const currentUserName = computed(
  () => authSession.value?.user?.display_name || authSession.value?.display_name || "訪客"
);
const currentRoleLabel = computed(() => {
  return roleLabel(authSession.value?.role);
});
const modeLabel = computed(() => ({
  transaction: "收料／退料",
  fixture: "查詢治具",
  model: "查詢機種",
  management: props.surface === "workspace" ? "收／退料總檢視" : "管理後臺"
})[activeMode.value]);
const modeTabs = computed(() => [
  { key: "transaction" as const, label: "收料／退料" },
  { key: "fixture" as const, label: "查詢治具" },
  { key: "model" as const, label: "查詢機種" },
  {
    key: "management" as const,
    label: props.surface === "workspace" ? "收／退料總檢視" : "管理後臺"
  }
]);
const managementEntries = computed(() => {
  const role = authSession.value?.role ?? "guest";
  return [
    { label: "收退料總檢視", description: "庫存流向、近期紀錄與篩選報表", path: "/inventory/overview", allowed: true },
    { label: "產能設定", description: "機種、站點與治具需求配置", path: "/production/requirements", allowed: role !== "guest" },
    { label: "資料維護", description: "治具、機種與站點主資料", path: "/master/fixtures", allowed: role !== "guest" },
    { label: "收退料帳目管理", description: "案件明細、重算與撤回", path: "/master/ledger", allowed: canManageAdminReports(role) },
    { label: "治具資料品質", description: "異常檢查與資料修復", path: "/master/quality", allowed: canManageAdminReports(role) }
  ].filter((entry) => entry.allowed);
});
const matchingTransactionFixture = computed(() => {
  const token = transactionForm.value.fixtureCode.trim().toLocaleUpperCase();
  return fixtures.value.find((row) => row.code.toLocaleUpperCase() === token) ?? null;
});
const recentRows = computed(() => recentTransactionRows.value.map((row) => ({
  key: String(row.id),
  type: row.transaction_type,
  transactionNo: row.transaction_no || "－",
  occurredAt: row.occurred_at,
  fixtureCode: row.fixture_code,
  identifier: row.identifier || "－",
  ownership: row.ownership_type,
  quantity: row.quantity,
  createdBy: row.created_by || "－",
  note: row.note || ""
})));
const recentFixtureRows = computed(() => {
  const seen = new Set<string>();
  return recentRows.value.filter((row) => {
    const key = row.fixtureCode.toLocaleUpperCase();
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  }).slice(0, 6);
});
const recentPageCount = computed(() => Math.max(1, Math.ceil(recentTotal.value / RECENT_PAGE_SIZE)));
const modelUsageRows = computed(() => models.value
  .filter((row) => row.is_active)
  .map((model) => ({ model, usage: modelShortcutUsage.value[model.code] }))
);
const recentModelCodes = computed(() => new Set(
  modelUsageRows.value
    .filter((row) => (row.usage?.lastQueriedAt ?? 0) > 0 && !row.usage?.pinned)
    .sort((left, right) => (right.usage?.lastQueriedAt ?? 0) - (left.usage?.lastQueriedAt ?? 0))
    .slice(0, 2)
    .map((row) => row.model.code)
));
const frequentModelCodes = computed(() => new Set(
  modelUsageRows.value
    .filter((row) => (row.usage?.queryCount ?? 0) > 0 && !row.usage?.pinned && !recentModelCodes.value.has(row.model.code))
    .sort((left, right) => (right.usage?.queryCount ?? 0) - (left.usage?.queryCount ?? 0))
    .slice(0, 2)
    .map((row) => row.model.code)
));
const modelShortcuts = computed(() => [...modelUsageRows.value]
  .sort((left, right) => {
    const leftPinned = left.usage?.pinned ? 1 : 0;
    const rightPinned = right.usage?.pinned ? 1 : 0;
    if (leftPinned !== rightPinned) return rightPinned - leftPinned;
    const leftRecent = recentModelCodes.value.has(left.model.code) ? 1 : 0;
    const rightRecent = recentModelCodes.value.has(right.model.code) ? 1 : 0;
    if (leftRecent !== rightRecent) return rightRecent - leftRecent;
    const leftFrequent = frequentModelCodes.value.has(left.model.code) ? 1 : 0;
    const rightFrequent = frequentModelCodes.value.has(right.model.code) ? 1 : 0;
    if (leftFrequent !== rightFrequent) return rightFrequent - leftFrequent;
    if ((left.usage?.lastQueriedAt ?? 0) !== (right.usage?.lastQueriedAt ?? 0)) {
      return (right.usage?.lastQueriedAt ?? 0) - (left.usage?.lastQueriedAt ?? 0);
    }
    if ((left.usage?.queryCount ?? 0) !== (right.usage?.queryCount ?? 0)) {
      return (right.usage?.queryCount ?? 0) - (left.usage?.queryCount ?? 0);
    }
    return left.model.code.localeCompare(right.model.code);
  })
  .slice(0, 6)
  .map((row) => row.model)
);
const sortedModelStations = computed(() => [...(modelContext.value?.query.stations ?? [])].sort(
  (left, right) => left.max_open_station_count - right.max_open_station_count || left.station_code.localeCompare(right.station_code)
));
const designatedModelRequirements = computed(() =>
  (modelContext.value?.query.station_requirements ?? []).filter((row) => row.designated_mode)
);
const bottleneckStation = computed(() => {
  const context = modelContext.value;
  if (!context?.query.stations.length) return null;
  return sortedModelStations.value.find(
    (station) => station.max_open_station_count === context.query.max_open_station_count
  ) ?? sortedModelStations.value[0] ?? null;
});
const fixtureStockStatusLabel = computed(() => {
  const status = fixtureContext.value?.stock?.stock_status;
  if (status === "out_of_stock") return "缺料";
  if (status === "low_stock") return "低水位";
  if (status === "normal") return "正常";
  return "尚無庫存";
});

function setInlineEditDirty(dirty: boolean): void {
  inlineEditDirty.value = dirty;
  setUnsavedChangesGuard(
    "workspace-inline-master-edit",
    dirty,
    "Workspace 快速編輯有尚未儲存的主資料"
  );
}

function closeInlineEditor(): void {
  inlineEditMode.value = null;
  inlineEditLoading.value = false;
  setInlineEditDirty(false);
}

async function confirmInlineEditorClose(): Promise<boolean> {
  if (!inlineEditMode.value) return true;
  if (inlineEditDirty.value) {
    const confirmed = await requestConfirmation("快速編輯內有尚未儲存的內容，確定要捨棄嗎？", {
      title: "捨棄快速編輯？",
      confirmLabel: "捨棄修改",
      tone: "danger"
    });
    if (!confirmed) return false;
  }
  closeInlineEditor();
  return true;
}

async function openInlineEditor(kind: "fixture" | "model"): Promise<void> {
  const customerId = selectedCustomerId.value;
  if (!canInlineEdit.value || !customerId) return;
  if (kind === "fixture" && !fixtureContext.value) return;
  if (kind === "model" && !modelContext.value) return;
  if (inlineEditMode.value && !(await confirmInlineEditorClose())) return;

  inlineEditLoading.value = true;
  try {
    if (kind === "fixture") {
      inlineEditUsers.value = await api.listCustomerUsers(customerId);
    }
    inlineEditMode.value = kind;
    setInlineEditDirty(false);
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "載入快速編輯資料失敗", "error");
  } finally {
    inlineEditLoading.value = false;
  }
}

async function handleInlineEditSaved(entityId: number): Promise<void> {
  const customerId = selectedCustomerId.value;
  const kind = inlineEditMode.value;
  if (!customerId || !kind) return;
  closeInlineEditor();
  loading.value = true;
  try {
    await loadBaseData();
    if (kind === "fixture") {
      const context = await api.getFixtureSearchContext(entityId, customerId, 12);
      fixtureContext.value = context;
      modelContext.value = null;
      query.value = context.fixture.code;
      transactionForm.value.fixtureCode = context.fixture.code;
      searchResults.value = searchResults.value.map((row) => row.entity_type === "fixture" && row.reference_id === entityId
        ? { ...row, title: context.fixture.code, subtitle: context.fixture.name, is_active: context.fixture.is_active }
        : row);
      await loadFixtureImage();
    } else {
      const context = await api.getModelSearchContext(entityId, customerId);
      modelContext.value = context;
      fixtureContext.value = null;
      query.value = context.model.code;
      searchResults.value = searchResults.value.map((row) => row.entity_type === "model" && row.reference_id === entityId
        ? { ...row, title: context.model.code, subtitle: context.model.name, is_active: context.model.is_active }
        : row);
      clearImage();
    }
    await syncWorkbenchRoute("replace", "/search", { q: query.value, selected_id: String(entityId) });
    pushToast(`${kind === "fixture" ? "治具" : "機種"}資料已更新。`, "success");
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "快速編輯後重新載入失敗", "error");
  } finally {
    loading.value = false;
  }
}

function clearImage(): void {
  if (imageUrl.value) URL.revokeObjectURL(imageUrl.value);
  imageUrl.value = "";
  imageMissing.value = false;
}

function modelShortcutStorageKey(): string {
  const customerId = selectedCustomerId.value;
  if (!customerId) return "";
  const userKey = authSession.value?.user?.id ?? currentUserName.value;
  return `fixture-m-workbench-model-shortcuts:${userKey}:${customerId}`;
}

function applyServerModelShortcut(preference: ModelShortcutPreference): void {
  modelShortcutUsage.value = {
    ...modelShortcutUsage.value,
    [preference.model_code]: {
      queryCount: preference.query_count,
      lastQueriedAt: preference.last_queried_at ? Date.parse(preference.last_queried_at) : 0,
      pinned: preference.pinned
    }
  };
}

async function loadModelShortcutUsage(): Promise<void> {
  const key = modelShortcutStorageKey();
  const customerId = selectedCustomerId.value;
  if (!key || !customerId) {
    modelShortcutUsage.value = {};
    return;
  }
  if (authSession.value?.mode === "user") {
    try {
      const preferences = await api.listModelShortcutPreferences(customerId);
      modelShortcutUsage.value = {};
      for (const preference of preferences) applyServerModelShortcut(preference);
    } catch {
      modelShortcutUsage.value = {};
      pushToast("機種捷徑暫時無法同步，其他工作台資料仍可正常使用。", "warning");
    }
    return;
  }
  if (typeof window === "undefined") return;
  try {
    const parsed = JSON.parse(window.localStorage.getItem(key) ?? "{}") as ModelShortcutUsage;
    modelShortcutUsage.value = parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    modelShortcutUsage.value = {};
  }
}

function persistModelShortcutUsage(): void {
  if (authSession.value?.mode === "user") return;
  const key = modelShortcutStorageKey();
  if (!key || typeof window === "undefined") return;
  window.localStorage.setItem(key, JSON.stringify(modelShortcutUsage.value));
}

async function recordModelShortcut(model: MachineModel): Promise<void> {
  const current = modelShortcutUsage.value[model.code];
  modelShortcutUsage.value = {
    ...modelShortcutUsage.value,
    [model.code]: {
      queryCount: (current?.queryCount ?? 0) + 1,
      lastQueriedAt: Date.now(),
      pinned: current?.pinned ?? false
    }
  };
  if (authSession.value?.mode === "user" && selectedCustomerId.value) {
    try {
      applyServerModelShortcut(await api.recordModelShortcutQuery(selectedCustomerId.value, model.id));
    } catch {
      pushToast("機種使用紀錄暫時無法同步，查詢功能不受影響。", "warning");
    }
  } else {
    persistModelShortcutUsage();
  }
}

async function toggleModelPin(model: MachineModel): Promise<void> {
  const current = modelShortcutUsage.value[model.code];
  const pinned = !(current?.pinned ?? false);
  modelShortcutUsage.value = {
    ...modelShortcutUsage.value,
    [model.code]: {
      queryCount: current?.queryCount ?? 0,
      lastQueriedAt: current?.lastQueriedAt ?? 0,
      pinned
    }
  };
  if (authSession.value?.mode === "user" && selectedCustomerId.value) {
    try {
      applyServerModelShortcut(await api.setModelShortcutPin(selectedCustomerId.value, model.id, pinned));
    } catch {
      modelShortcutUsage.value = {
        ...modelShortcutUsage.value,
        [model.code]: {
          queryCount: current?.queryCount ?? 0,
          lastQueriedAt: current?.lastQueriedAt ?? 0,
          pinned: current?.pinned ?? false
        }
      };
      pushToast("釘選狀態同步失敗，請稍後再試。", "error");
    }
  } else {
    persistModelShortcutUsage();
  }
}

function modelShortcutReason(model: MachineModel): string {
  if (modelShortcutUsage.value[model.code]?.pinned) return "已釘選";
  if (recentModelCodes.value.has(model.code)) return "最近查詢";
  if (frequentModelCodes.value.has(model.code)) return "常用機種";
  return "可用機種";
}

async function clearSearch(): Promise<void> {
  if (!(await confirmInlineEditorClose())) return;
  query.value = "";
  searchResults.value = [];
  fixtureContext.value = null;
  modelContext.value = null;
  lastSearchMiss.value = null;
  relatedSearchSuggestion.value = null;
  clearImage();
  await syncWorkbenchRoute("push", "/search", { q: undefined, selected_id: undefined });
}

function buildRelatedSearchSuggestion(targetMode: WorkbenchMode): RelatedSearchSuggestion | null {
  if (activeMode.value === "fixture" && targetMode === "model" && fixtureContext.value) {
    const modelById = new Map<number, RelatedSearchTarget>();
    for (const model of fixtureContext.value.related_models) {
      modelById.set(model.id, { id: model.id, code: model.code, name: model.name });
    }
    for (const row of fixtureContext.value.station_rows) {
      if (!modelById.has(row.model_id)) {
        modelById.set(row.model_id, { id: row.model_id, code: row.model_code, name: row.model_name });
      }
    }
    const targets = [...modelById.values()].sort((left, right) => left.code.localeCompare(right.code));
    if (targets.length) {
      return {
        sourceKind: "fixture",
        sourceCode: fixtureContext.value.fixture.code,
        targetMode: "model",
        targets
      };
    }
  }
  if (activeMode.value === "model" && targetMode === "fixture" && modelContext.value) {
    const fixtureById = new Map<number, RelatedSearchTarget>();
    for (const fixture of modelContext.value.query.fixtures) {
      fixtureById.set(fixture.fixture_id, {
        id: fixture.fixture_id,
        code: fixture.fixture_code,
        name: fixture.fixture_name
      });
    }
    const targets = [...fixtureById.values()].sort((left, right) => left.code.localeCompare(right.code));
    if (targets.length) {
      return {
        sourceKind: "model",
        sourceCode: modelContext.value.model.code,
        targetMode: "fixture",
        targets
      };
    }
  }
  return null;
}

async function runRelatedSearch(target: RelatedSearchTarget): Promise<void> {
  query.value = target.code;
  relatedSearchSuggestion.value = null;
  await runSearch();
}

function relatedSearchTargetLabel(target: RelatedSearchTarget): string {
  const kind = activeMode.value === "model" ? "機種" : "治具";
  const name = target.name && target.name !== target.code ? ` ${target.name}` : "";
  return `查詢${kind} ${target.code}${name}`;
}

function workbenchRouteQuery(
  mode: WorkbenchMode = activeMode.value,
  overrides: LocationQueryRaw = {}
): LocationQueryRaw {
  const token = query.value.trim();
  return {
    ...uiSurfaceRouteQuery(props.surface),
    ...(selectedCustomerId.value ? { customer: String(selectedCustomerId.value) } : {}),
    workbench_mode: mode,
    ...(mode === "transaction" ? { transaction_type: transactionDirection.value } : {}),
    ...(mode === "fixture" ? { fixture_search: fixtureSearchMode.value } : {}),
    ...(token ? { q: token } : {}),
    ...((mode === "fixture" && fixtureContext.value?.fixture.id)
      ? { selected_id: String(fixtureContext.value.fixture.id) }
      : (mode === "model" && modelContext.value?.model.id)
        ? { selected_id: String(modelContext.value.model.id) }
        : {}),
    ...overrides
  };
}

async function syncWorkbenchRoute(
  history: "push" | "replace",
  path = activeMode.value === "transaction" && canOperate.value ? "/inventory" : "/search",
  overrides: LocationQueryRaw = {}
): Promise<void> {
  const target = { path, query: workbenchRouteQuery(activeMode.value, overrides) };
  if (router.resolve(target).fullPath === route.fullPath) return;
  syncingWorkbenchRoute = true;
  try {
    await router[history](target);
  } finally {
    syncingWorkbenchRoute = false;
  }
}

async function revealResultsIfOutsideViewport(): Promise<void> {
  await nextTick();
  const panel = resultsPanel.value;
  if (!panel || typeof window === "undefined") return;
  const rect = panel.getBoundingClientRect();
  if ((rect.top >= window.innerHeight || rect.bottom <= 0) && typeof panel.scrollIntoView === "function") {
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

async function loadFixtureImage(): Promise<void> {
  clearImage();
  const context = fixtureContext.value;
  const customerId = selectedCustomerId.value;
  if (!context?.fixture.has_image || !customerId) {
    imageMissing.value = true;
    return;
  }
  try {
    imageUrl.value = await fetchFixtureImageObjectUrl(context.fixture.code, customerId);
  } catch {
    imageMissing.value = true;
  }
}

async function loadBaseData(): Promise<void> {
  const customerId = selectedCustomerId.value;
  if (!customerId) {
    fixtures.value = [];
    models.value = [];
    recentTransactionRows.value = [];
    recentTotal.value = 0;
    fixtureContext.value = null;
    modelContext.value = null;
    return;
  }
  loading.value = true;
  try {
    const [fixtureRows, modelRows, transactionPage] = await Promise.all([
      api.listFixtures(customerId),
      api.listModels(customerId),
      api.listTransactionOverviewPage(1, RECENT_PAGE_SIZE, customerId),
      loadModelShortcutUsage()
    ]);
    fixtures.value = fixtureRows.filter((row) => row.is_active);
    models.value = modelRows.filter((row) => row.is_active);
    recentTransactionRows.value = transactionPage.items;
    recentTotal.value = transactionPage.total;
    recentPage.value = transactionPage.page;
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "載入工作台資料失敗", "error");
  } finally {
    loading.value = false;
  }
}

async function selectResult(result: SearchResult, syncHistory = true): Promise<void> {
  if (!(await confirmInlineEditorClose())) return;
  const customerId = selectedCustomerId.value;
  if (!customerId) return;
  loading.value = true;
  lastSearchMiss.value = null;
  try {
    if (result.entity_type === "fixture") {
      fixtureContext.value = await api.getFixtureSearchContext(
        result.reference_id,
        customerId,
        12,
        result.matched_identifier ?? undefined
      );
      modelContext.value = null;
      transactionForm.value.fixtureCode = fixtureContext.value.fixture.code;
      await loadFixtureImage();
    } else if (result.entity_type === "model") {
      modelContext.value = await api.getModelSearchContext(result.reference_id, customerId);
      fixtureContext.value = null;
      clearImage();
      void recordModelShortcut(modelContext.value.model);
    }
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "載入查詢內容失敗", "error");
  } finally {
    loading.value = false;
  }
  if (syncHistory) await syncWorkbenchRoute("push", "/search");
}

async function runSearch(options: { history?: "push" | "replace" | false; preferredId?: number | null } = {}): Promise<void> {
  if (!(await confirmInlineEditorClose())) return;
  const customerId = selectedCustomerId.value;
  const token = query.value.trim();
  if (!customerId || !token) {
    pushToast("請輸入治具或機種關鍵字。", "warning");
    return;
  }
  loading.value = true;
  lastSearchMiss.value = null;
  relatedSearchSuggestion.value = null;
  try {
    const entityType = activeMode.value === "model" ? "model" : "fixture";
    const page = await api.globalSearch({
      q: token,
      customerId,
      entityType,
      fixtureSearchMode: entityType === "fixture" ? fixtureSearchMode.value : undefined,
      pageSize: 20
    });
    searchResults.value = page.items;
    if (page.items.length === 0) {
      fixtureContext.value = null;
      modelContext.value = null;
      clearImage();
      lastSearchMiss.value = { token, entityLabel: entityType === "model" ? "機種" : "治具" };
      if (options.history !== false) {
        await syncWorkbenchRoute(options.history ?? "push", "/search", { q: token, selected_id: undefined });
      }
      await revealResultsIfOutsideViewport();
      pushToast(`找不到符合「${token}」的${entityType === "model" ? "機種" : "治具"}。`, "info");
      return;
    }
    const preferred = page.items.find((row) => row.reference_id === options.preferredId);
    const exact = page.items.find((row) => row.title.toLocaleUpperCase() === token.toLocaleUpperCase());
    await selectResult(preferred ?? exact ?? page.items[0]!, false);
    if (options.history !== false) {
      await syncWorkbenchRoute(options.history ?? "push", "/search", { q: token });
    }
    await revealResultsIfOutsideViewport();
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "查詢失敗", "error");
  } finally {
    loading.value = false;
  }
}

async function showTransactionFixture(): Promise<void> {
  if (!(await confirmInlineEditorClose())) return;
  const fixture = matchingTransactionFixture.value;
  const customerId = selectedCustomerId.value;
  if (!fixture || !customerId) return;
  loading.value = true;
  try {
    fixtureContext.value = await api.getFixtureSearchContext(fixture.id, customerId, 12);
    modelContext.value = null;
    lastSearchMiss.value = null;
    await loadFixtureImage();
    await revealResultsIfOutsideViewport();
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "載入治具資料失敗", "error");
  } finally {
    loading.value = false;
  }
}

async function submitTransaction(): Promise<void> {
  const customerId = selectedCustomerId.value;
  const fixture = matchingTransactionFixture.value;
  const form = transactionForm.value;
  if (!canOperate.value || !customerId) return;
  if (!form.transactionNo.trim()) {
    pushToast("請輸入派發／調扣單號。", "warning");
    return;
  }
  if (!fixture) {
    pushToast("請輸入有效且已啟用的治具編號。", "warning");
    return;
  }
  const identifier = normalizeIdentifierForWrite(form.identifier);
  if (!identifier) {
    pushToast("請輸入 Datecode／流水號。", "warning");
    return;
  }
  if (!Number.isInteger(form.quantity) || form.quantity <= 0) {
    pushToast("數量必須是大於 0 的整數。", "warning");
    return;
  }

  const payload = {
    customer_id: customerId,
    transaction_no: form.transactionNo.trim(),
    note: form.note.trim() || undefined,
    items: [{
      fixture_id: fixture.id,
      ownership_type: form.ownershipType,
      identifier,
      quantity: form.quantity,
      note: form.note.trim() || undefined
    }]
  };
  const send = async (confirmDuplicate = false) => {
    if (transactionDirection.value === "receipt") {
      await api.createReceiptWithOptions(payload, { confirmDuplicate });
    } else {
      await api.createReturnWithOptions(payload, { confirmDuplicate });
    }
  };

  submitting.value = true;
  try {
    try {
      await send();
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 409) {
        const confirmed = await requestConfirmation(error.message, {
          title: `單號 ${form.transactionNo.trim()} 已存在`,
          confirmLabel: "仍要送出",
          tone: "danger"
        });
        if (!confirmed) return;
        await send(true);
      } else {
        throw error;
      }
    }
    pushToast(`${transactionDirection.value === "receipt" ? "收料" : "退料"}已建立。`, "success");
    form.identifier = "";
    form.quantity = 1;
    form.note = "";
    await loadBaseData();
    await showTransactionFixture();
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "收退料送出失敗", "error");
  } finally {
    submitting.value = false;
  }
}

async function selectMode(mode: WorkbenchMode): Promise<void> {
  if (!(await confirmInlineEditorClose())) return;
  if (mode === "management" && props.surface === "workspace") {
    await router.push({
      path: "/inventory/overview",
      query: workbenchRouteQuery("management", { selected_id: undefined })
    });
    return;
  }
  const previousMode = activeMode.value;
  const suggestion = buildRelatedSearchSuggestion(mode);
  activeMode.value = mode;
  batchPanelOpen.value = false;
  searchResults.value = [];
  lastSearchMiss.value = null;
  relatedSearchSuggestion.value = suggestion;
  recentPage.value = 1;
  if ((previousMode === "fixture" || previousMode === "model") && (mode === "fixture" || mode === "model") && previousMode !== mode) {
    query.value = "";
  }
  if (mode === "fixture" || mode === "model" || mode === "management") {
    fixtureContext.value = null;
    modelContext.value = null;
    clearImage();
  }
  if (mode === "management") query.value = "";
  const path = mode === "transaction" && canOperate.value ? "/inventory" : "/search";
  await syncWorkbenchRoute("push", path, { selected_id: undefined });
}

async function selectTransactionDirection(direction: TransactionDirection): Promise<void> {
  transactionDirection.value = direction;
  if (activeMode.value !== "transaction") return;
  await syncWorkbenchRoute("push", route.path);
}

async function openBatchImport(): Promise<void> {
  if (activeMode.value !== "transaction") return;
  batchPanelOpen.value = true;
  await syncWorkbenchRoute("push", route.path, { workbench_batch: "true" });
  void revealResultsIfOutsideViewport();
}

async function closeBatchImport(): Promise<void> {
  batchPanelOpen.value = false;
  await syncWorkbenchRoute("push", route.path, { workbench_batch: undefined });
}

async function selectFixtureSearchMode(nextMode: FixtureSearchMode): Promise<void> {
  if (nextMode === fixtureSearchMode.value) return;
  if (!(await confirmInlineEditorClose())) return;
  fixtureSearchMode.value = nextMode;
  fixtureContext.value = null;
  searchResults.value = [];
  lastSearchMiss.value = null;
  if (query.value.trim()) {
    await runSearch({ history: "push" });
    return;
  }
  await syncWorkbenchRoute("push", "/search", { selected_id: undefined });
}

async function loadRecentPage(page: number): Promise<void> {
  const customerId = selectedCustomerId.value;
  if (!customerId || recentLoading.value) return;
  recentLoading.value = true;
  try {
    const result = await api.listTransactionOverviewPage(page, RECENT_PAGE_SIZE, customerId);
    recentTransactionRows.value = result.items;
    recentTotal.value = result.total;
    recentPage.value = result.page;
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "近期作業分頁載入失敗", "error");
  } finally {
    recentLoading.value = false;
  }
}

function previousRecentPage(): void {
  void loadRecentPage(Math.max(1, recentPage.value - 1));
}

function nextRecentPage(): void {
  void loadRecentPage(Math.min(recentPageCount.value, recentPage.value + 1));
}

async function handleBatchSuccess(): Promise<void> {
  await loadBaseData();
  if (matchingTransactionFixture.value) await showTransactionFixture();
}

function handleCustomerChange(event: Event): void {
  const value = Number.parseInt((event.target as HTMLSelectElement).value, 10);
  emit("update:selectedCustomerId", Number.isFinite(value) ? value : null);
}

async function openRecentFixture(row: (typeof recentFixtureRows.value)[number]): Promise<void> {
  transactionForm.value.fixtureCode = row.fixtureCode;
  if (activeMode.value === "fixture") {
    query.value = row.fixtureCode;
    await runSearch();
    return;
  }
  await showTransactionFixture();
}

async function openModelShortcut(model: MachineModel): Promise<void> {
  query.value = model.code;
  await runSearch();
}

function openManagement(path: string): void {
  void router.push({ path, query: workbenchRouteQuery() });
}

function openExportCenter(): void {
  emit("openExport");
}

watch(selectedCustomerId, async (customerId) => {
  closeInlineEditor();
  inlineEditUsers.value = [];
  fixtures.value = [];
  models.value = [];
  recentTransactionRows.value = [];
  recentTotal.value = 0;
  recentPage.value = 1;
  searchResults.value = [];
  fixtureContext.value = null;
  modelContext.value = null;
  lastSearchMiss.value = null;
  relatedSearchSuggestion.value = null;
  clearImage();
  const nextCustomer = customerId ? String(customerId) : undefined;
  if (route.query.customer !== nextCustomer) {
    await router.replace({ path: route.path, query: workbenchRouteQuery(activeMode.value) });
  }
  await loadBaseData();
});

watch(
  () => route.query.workbench_batch,
  (value) => {
    batchPanelOpen.value = value === "true";
  }
);

async function restoreWorkbenchStateFromRoute(): Promise<void> {
  closeInlineEditor();
  const requestedMode = String(route.query.workbench_mode ?? "");
  const nextMode: WorkbenchMode = requestedMode === "receipt" || requestedMode === "return" || requestedMode === "transaction"
    ? "transaction"
    : requestedMode === "model"
      ? "model"
      : requestedMode === "management"
        ? "management"
        : "fixture";
  activeMode.value = nextMode;
  transactionDirection.value = route.query.transaction_type === "return" || requestedMode === "return" ? "return" : "receipt";
  fixtureSearchMode.value = route.query.fixture_search === "identifier" ? "identifier" : "fixture";
  batchPanelOpen.value = route.query.workbench_batch === "true";
  query.value = typeof route.query.q === "string" ? route.query.q : "";
  relatedSearchSuggestion.value = null;
  searchResults.value = [];
  fixtureContext.value = null;
  modelContext.value = null;
  lastSearchMiss.value = null;
  clearImage();
  if ((nextMode === "fixture" || nextMode === "model") && query.value.trim()) {
    const preferredId = Number.parseInt(String(route.query.selected_id ?? ""), 10);
    await runSearch({ history: false, preferredId: Number.isFinite(preferredId) ? preferredId : null });
  }
}

watch(
  () => route.fullPath,
  async () => {
    if (!workbenchRouteReady || syncingWorkbenchRoute) return;
    await restoreWorkbenchStateFromRoute();
  }
);

onMounted(async () => {
  await loadBaseData();
  await restoreWorkbenchStateFromRoute();
  workbenchRouteReady = true;
});

onBeforeUnmount(() => {
  clearImage();
  closeInlineEditor();
});
</script>

<template>
  <section class="workbench-ui" :class="{ 'without-header': !showHeader }" :data-system-ui="surface" :aria-label="surface === 'workspace' ? 'Workspace UI 快速作業' : '工作台 UI 系統介面'">
    <header v-if="showHeader" class="workbench-header">
      <div class="workbench-brand">
        <span class="workbench-mark">FM</span>
        <div>
          <p>Fixture-M Lite</p>
          <h1>現場工作台</h1>
        </div>
      </div>

      <div class="workbench-header-center">
        <slot name="ui-switcher" />
      </div>

      <div class="workbench-session">
        <slot name="heading-actions" />
        <label>
          <span>目前客戶</span>
          <select :value="selectedCustomerId ?? undefined" aria-label="工作台客戶" @change="handleCustomerChange">
            <option v-for="customer in customers" :key="customer.id" :value="customer.id">
              {{ customer.code }}－{{ customer.name }}
            </option>
          </select>
        </label>
        <div class="workbench-account">
          <strong>{{ currentUserName }}</strong>
          <span>{{ currentRoleLabel }}</span>
        </div>
        <slot name="account-action" />
      </div>
    </header>

    <div class="workbench-columns">
      <aside class="workbench-panel workbench-controls" aria-label="工作台操作區">
        <div class="workbench-panel-heading">
          <div>
            <span>快速作業</span>
            <h2>{{ modeLabel }}</h2>
          </div>
          <span v-if="loading" class="workbench-loading">載入中…</span>
        </div>

        <div class="workbench-mode-tabs" data-tour="workbench-mode-tabs" role="tablist" aria-label="工作台作業模式">
          <button
            v-for="item in modeTabs"
            :key="item.key"
            type="button"
            role="tab"
            :data-tour="item.key === 'management' && surface === 'workspace' ? 'workspace-overview-entry' : undefined"
            :aria-selected="activeMode === item.key"
            :class="{ active: activeMode === item.key }"
            @click="selectMode(item.key)"
          >
            {{ item.label }}
          </button>
        </div>

        <form v-if="isTransactionMode" class="workbench-form" data-tour="workbench-transaction-form" @submit.prevent="submitTransaction">
          <fieldset class="workbench-transaction-direction">
            <legend>作業類型</legend>
            <div role="radiogroup" aria-label="選擇收料或退料">
              <button
                v-for="item in ([{ value: 'receipt', label: '收料入庫' }, { value: 'return', label: '退料出庫' }] as const)"
                :key="item.value"
                type="button"
                role="radio"
                :aria-checked="transactionDirection === item.value"
                :class="{ active: transactionDirection === item.value }"
                @click="selectTransactionDirection(item.value)"
              >
                {{ item.label }}
              </button>
            </div>
          </fieldset>
          <label>
            <span>{{ transactionDirection === "receipt" ? "派發單號" : "調扣單號" }}</span>
            <input v-model.trim="transactionForm.transactionNo" autocomplete="off" placeholder="輸入單號" />
          </label>
          <label>
            <span>治具編號</span>
            <input
              v-model.trim="transactionForm.fixtureCode"
              list="workbench-fixture-options"
              autocomplete="off"
              placeholder="掃描或輸入治具編號"
              @change="showTransactionFixture"
            />
            <datalist id="workbench-fixture-options">
              <option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.code">
                {{ fixture.name }}
              </option>
            </datalist>
          </label>
          <label>
            <span>Datecode／流水號</span>
            <input v-model.trim="transactionForm.identifier" autocomplete="off" placeholder="短數字會自動補至 4 碼" />
          </label>
          <div class="workbench-form-row">
            <label>
              <span>數量</span>
              <input v-model.number="transactionForm.quantity" type="number" min="1" step="1" inputmode="numeric" />
            </label>
            <label>
              <span>來源</span>
              <select v-model="transactionForm.ownershipType">
                <option value="customer_supplied">客供</option>
                <option value="self_purchased">自購</option>
              </select>
            </label>
          </div>
          <label>
            <span>備註（選填）</span>
            <input v-model.trim="transactionForm.note" autocomplete="off" placeholder="本筆說明" />
          </label>
          <p v-if="transactionForm.fixtureCode && !matchingTransactionFixture" class="workbench-inline-error">
            找不到已啟用的治具編號
          </p>
          <button class="workbench-primary" type="submit" :disabled="submitting || !canOperate">
            {{ submitting ? "送出中…" : transactionDirection === "receipt" ? "建立收料" : "建立退料" }}
          </button>
          <button
            class="workbench-secondary"
            type="button"
            :disabled="!canOperate"
            @click="openBatchImport"
          >
            開啟批次收退料
          </button>
          <p v-if="!canOperate" class="workbench-readonly">訪客可以查詢，但不能建立收退料。</p>
        </form>

        <form v-else-if="activeMode === 'fixture' || activeMode === 'model'" class="workbench-form workbench-query-form" data-tour="workbench-query-form" @submit.prevent="runSearch()">
          <div v-if="activeMode === 'fixture'" class="workbench-search-kind" aria-label="治具搜尋類型">
            <button type="button" :class="{ active: fixtureSearchMode === 'fixture' }" :aria-pressed="fixtureSearchMode === 'fixture'" @click="selectFixtureSearchMode('fixture')">治具資料</button>
            <button type="button" :class="{ active: fixtureSearchMode === 'identifier' }" :aria-pressed="fixtureSearchMode === 'identifier'" @click="selectFixtureSearchMode('identifier')">Datecode／序號</button>
          </div>
          <label>
            <span>{{ activeMode === "fixture" ? fixtureSearchMode === "identifier" ? "Datecode／序號" : "治具編號或名稱" : "機種編號或名稱" }}</span>
            <input
              v-model="query"
              autofocus
              autocomplete="off"
              :placeholder="activeMode === 'fixture' ? fixtureSearchMode === 'identifier' ? '只輸入 Datecode／序號，例如 2204' : '例如 L-00143' : '例如 AWK-1137C'"
              @input="relatedSearchSuggestion = null"
            />
          </label>
          <aside
            v-if="relatedSearchSuggestion?.targetMode === activeMode"
            class="workbench-related-search-suggestion"
            data-tour="workbench-related-search-suggestion"
            role="status"
          >
            <div>
              <span>關聯搜尋建議</span>
              <button type="button" aria-label="關閉關聯搜尋建議" @click="relatedSearchSuggestion = null">×</button>
            </div>
            <p>
              是否要查詢{{ relatedSearchSuggestion.sourceKind === "fixture" ? "治具" : "機種" }}
              <strong>{{ relatedSearchSuggestion.sourceCode }}</strong>
              的關聯{{ activeMode === "model" ? "機種" : "治具" }}？
            </p>
            <div class="workbench-related-search-actions">
              <button
                v-for="target in relatedSearchSuggestion.targets"
                :key="`${activeMode}-${target.id}`"
                type="button"
                :aria-label="relatedSearchTargetLabel(target)"
                @click="runRelatedSearch(target)"
              >
                <strong>{{ target.code }}</strong>
                <span v-if="target.name && target.name !== target.code">{{ target.name }}</span>
              </button>
            </div>
          </aside>
          <button class="workbench-primary" type="submit" :disabled="loading">
            {{ loading ? "查詢中…" : activeMode === "fixture" ? fixtureSearchMode === "identifier" ? "查詢 Datecode／序號" : "查詢治具" : "查詢機種" }}
          </button>
        </form>

        <nav v-else class="workbench-management-launcher" data-tour="workbench-management-launcher" aria-label="管理後臺快捷入口">
          <div class="workbench-management-intro">
            <span>MANAGEMENT</span>
            <p>選擇管理功能；權限不足的項目不會顯示。</p>
          </div>
          <button
            v-for="entry in managementEntries"
            :key="entry.path"
            type="button"
            @click="openManagement(entry.path)"
          >
            <span><strong>{{ entry.label }}</strong><small>{{ entry.description }}</small></span>
            <span aria-hidden="true">›</span>
          </button>
          <button class="workbench-export-entry" type="button" @click="openExportCenter">
            <span><strong>匯出中心</strong><small>依權限選擇資料集與多選條件</small></span>
            <span aria-hidden="true">↗</span>
          </button>
        </nav>

        <section
          v-if="activeMode !== 'management'"
          class="workbench-today"
          :aria-label="activeMode === 'model' ? '機種捷徑' : '最近收退料治具'"
        >
          <div class="workbench-subheading">
            <h3>{{ activeMode === "model" ? "機種捷徑" : "最近收退料治具" }}</h3>
            <span>{{ activeMode === "model" ? modelShortcuts.length : recentFixtureRows.length }} 筆</span>
          </div>
          <div v-if="activeMode === 'model' && modelShortcuts.length" class="workbench-mini-list workbench-model-shortcuts">
            <div
              v-for="model in modelShortcuts"
              :key="model.id"
              class="workbench-model-shortcut-row"
            >
              <button
                class="workbench-shortcut-open"
                type="button"
                :aria-label="`查詢機種 ${model.code} ${model.name}`"
                @click="openModelShortcut(model)"
              >
                <span class="workbench-shortcut-mark">M</span>
                <span class="workbench-recent-copy">
                  <strong>{{ model.code }}</strong>
                  <small>{{ model.name }} · {{ modelShortcutReason(model) }}</small>
                </span>
                <span aria-hidden="true">›</span>
              </button>
              <button
                class="workbench-shortcut-pin"
                type="button"
                :class="{ active: modelShortcutUsage[model.code]?.pinned }"
                :aria-label="modelShortcutUsage[model.code]?.pinned ? `取消釘選 ${model.code}` : `釘選 ${model.code}`"
                :title="modelShortcutUsage[model.code]?.pinned ? '取消釘選' : '釘選機種'"
                @click="toggleModelPin(model)"
              >
                {{ modelShortcutUsage[model.code]?.pinned ? "★" : "☆" }}
              </button>
            </div>
          </div>
          <div v-else-if="activeMode !== 'model' && recentFixtureRows.length" class="workbench-mini-list workbench-recent-fixtures">
            <button
              v-for="row in recentFixtureRows"
              :key="row.key"
              type="button"
              :aria-label="`${row.type === 'receipt' ? '收料' : '退料'} ${row.fixtureCode} ${row.identifier} ${row.quantity} pcs ${formatLocalDate(row.occurredAt)}`"
              @click="openRecentFixture(row)"
            >
              <span :class="['flow-dot', row.type]"></span>
              <span class="workbench-recent-copy">
                <strong>{{ row.fixtureCode }}</strong>
                <small>{{ row.type === "receipt" ? "收料" : "退料" }} · {{ row.ownership === "customer_supplied" ? "客供" : "自購" }} · {{ row.createdBy }}</small>
                <small>{{ row.identifier }} · {{ formatLocalDate(row.occurredAt) }}</small>
              </span>
              <span class="workbench-recent-quantity">{{ row.quantity }} pcs</span>
            </button>
          </div>
          <p v-else class="workbench-empty-small">
            {{ activeMode === "model" ? "目前沒有可用機種。" : "目前沒有近期資料。" }}
          </p>
        </section>

      </aside>

      <main ref="resultsPanel" class="workbench-panel workbench-results" data-tour="workbench-results" :class="{ 'is-batch-open': batchPanelOpen }" aria-live="polite">
        <div class="workbench-panel-heading workbench-results-heading">
          <div>
            <span>查詢結果</span>
            <h2>
              <template v-if="batchPanelOpen">批次收退料</template>
              <template v-else-if="fixtureContext">{{ fixtureContext.fixture.code }} · {{ fixtureContext.fixture.name }}</template>
              <template v-else-if="modelContext">{{ modelContext.model.code }} · {{ modelContext.model.name }}</template>
              <template v-else-if="lastSearchMiss">找不到{{ lastSearchMiss.entityLabel }}</template>
              <template v-else-if="activeMode === 'management'">管理功能入口</template>
              <template v-else>{{ isTransactionMode ? "近期作業紀錄" : "尚未查詢" }}</template>
            </h2>
          </div>
          <button v-if="batchPanelOpen" class="workbench-panel-back" type="button" @click="closeBatchImport">
            返回查詢結果
          </button>
          <span v-else-if="currentCustomer" class="workbench-customer-chip">{{ currentCustomer.code }}</span>
        </div>

        <div v-if="searchResults.length > 1 && !isTransactionMode && !batchPanelOpen" class="workbench-result-strip">
          <button
            v-for="result in searchResults"
            :key="`${result.entity_type}-${result.reference_id}`"
            type="button"
            :class="{ active: fixtureContext?.fixture.id === result.reference_id || modelContext?.model.id === result.reference_id }"
            @click="selectResult(result)"
          >
            <strong>{{ result.title }}</strong>
            <span>{{ result.subtitle || "－" }}</span>
          </button>
        </div>

        <section v-if="batchPanelOpen" class="workbench-batch-panel" data-tour="workbench-batch-panel" aria-label="工作台批次收退料">
          <WorkbenchBatchOperations
            :customer-id="selectedCustomerId ?? undefined"
            :initial-mode="batchMode"
            :preset-fixture-code="transactionForm.fixtureCode"
            @success="handleBatchSuccess"
          />
        </section>

        <template v-else-if="fixtureContext">
          <div class="workbench-summary-grid">
            <article>
              <span>現有治具</span>
              <strong>{{ fixtureContext.stock?.stock_qty ?? 0 }} <small>pcs</small></strong>
            </article>
            <article>
              <span>客供／自購</span>
              <strong>{{ fixtureContext.stock?.customer_supplied_qty ?? 0 }}／{{ fixtureContext.stock?.self_purchased_qty ?? 0 }}</strong>
            </article>
            <article :data-status="fixtureContext.stock?.stock_status ?? 'none'">
              <span>庫存狀態</span>
              <strong>{{ fixtureStockStatusLabel }}</strong>
            </article>
          </div>

          <section class="workbench-table-section">
            <div class="workbench-subheading">
              <h3>Datecode／流水號庫存</h3>
              <span>{{ fixtureContext.identifier_rows.length }} 筆</span>
            </div>
            <div class="workbench-table-wrap">
              <table>
                <thead><tr><th>識別碼</th><th>客供</th><th>自購</th><th>總數</th></tr></thead>
                <tbody>
                  <tr v-for="row in fixtureContext.identifier_rows" :key="row.identifier">
                    <td>{{ row.identifier }}</td>
                    <td>{{ row.customer_supplied_qty }}</td>
                    <td>{{ row.self_purchased_qty }}</td>
                    <td><strong>{{ row.stock_qty }} pcs</strong></td>
                  </tr>
                  <tr v-if="fixtureContext.identifier_rows.length === 0"><td colspan="4">尚無識別碼庫存。</td></tr>
                </tbody>
              </table>
            </div>
          </section>

          <section class="workbench-table-section">
            <div class="workbench-subheading"><h3>收退料記錄</h3></div>
            <div class="workbench-table-wrap">
              <table>
                <thead><tr><th>日期</th><th>類型</th><th>單號</th><th>識別碼</th><th>數量</th></tr></thead>
                <tbody>
                  <template v-for="transaction in fixtureContext.transactions" :key="transaction.id">
                    <tr v-for="(item, index) in transaction.items" :key="`${transaction.id}-${index}`">
                      <td>{{ formatLocalDate(transaction.occurred_at) }}</td>
                      <td>{{ transaction.transaction_type === "receipt" ? "收料" : "退料" }}</td>
                      <td>{{ transaction.transaction_no || "－" }}</td>
                      <td>{{ item.identifier || "－" }}</td>
                      <td><strong>{{ item.quantity }} pcs</strong></td>
                    </tr>
                  </template>
                  <tr v-if="fixtureContext.transactions.length === 0"><td colspan="5">尚無收退料記錄。</td></tr>
                </tbody>
              </table>
            </div>
          </section>
        </template>

        <template v-else-if="modelContext">
          <div class="workbench-summary-grid">
            <article>
              <span>整機瓶頸產能</span>
              <strong>{{ modelContext.query.max_open_station_count }} <small>站</small></strong>
            </article>
            <article><span>站點數</span><strong>{{ modelContext.query.station_count }}</strong></article>
            <article><span>治具種類</span><strong>{{ modelContext.query.fixture_type_count }}</strong></article>
          </div>
          <div v-if="bottleneckStation" class="workbench-bottleneck-callout">
            <span>目前瓶頸</span>
            <strong>{{ bottleneckStation.station_code }} · {{ bottleneckStation.station_name }}</strong>
            <small>瓶頸治具 {{ bottleneckStation.bottleneck_fixture_code || "尚未判定" }}</small>
          </div>
          <section class="workbench-table-section">
            <div class="workbench-subheading"><h3>各站最大開站數</h3></div>
            <div class="workbench-table-wrap">
              <table>
                <thead><tr><th>站點</th><th>站點名稱</th><th>最大開站數</th><th>瓶頸治具</th></tr></thead>
                <tbody>
                  <tr
                    v-for="station in sortedModelStations"
                    :key="station.station_id"
                    :class="{ 'workbench-bottleneck-row': station.station_id === bottleneckStation?.station_id }"
                  >
                    <td>{{ station.station_code }}</td>
                    <td>{{ station.station_name }}</td>
                    <td><strong>{{ station.max_open_station_count }}</strong></td>
                    <td>
                      {{ station.bottleneck_fixture_code || "－" }}
                      <span v-if="station.station_id === bottleneckStation?.station_id" class="workbench-bottleneck-badge">目前瓶頸</span>
                    </td>
                  </tr>
                  <tr v-if="modelContext.query.stations.length === 0"><td colspan="4">此機種尚未配置站點。</td></tr>
                </tbody>
              </table>
            </div>
          </section>
          <section class="workbench-table-section">
            <div class="workbench-subheading">
              <h3>治具需求明細</h3>
              <span v-if="designatedModelRequirements.length">{{ designatedModelRequirements.length }} 筆指定模式</span>
            </div>
            <div v-if="designatedModelRequirements.length" class="workbench-designated-notice">
              此機種含指定 identifier 的治具需求；指定列的庫存與可支援站數只採計列出的 identifier。
            </div>
            <div class="workbench-table-wrap">
              <table>
                <thead><tr><th>站點</th><th>治具</th><th>需求</th><th>使用模式</th><th>庫存</th><th>可支援站數</th></tr></thead>
                <tbody>
                  <tr v-for="row in modelContext.query.station_requirements" :key="`${row.station_id}-${row.fixture_id}`">
                    <td>{{ row.station_code }}</td>
                    <td>{{ row.fixture_code }} · {{ row.fixture_name }}</td>
                    <td>{{ row.required_qty }}</td>
                    <td class="workbench-designated-cell">
                      <template v-if="row.designated_mode">
                        <span class="workbench-designated-badge">指定模式</span>
                        <small>{{ row.designated_identifiers.join("、") }}</small>
                      </template>
                      <span v-else>不限 identifier</span>
                    </td>
                    <td>{{ row.stock_qty }}</td>
                    <td><strong>{{ row.max_open_station_count }}</strong></td>
                  </tr>
                  <tr v-if="modelContext.query.station_requirements.length === 0"><td colspan="6">此機種尚無治具需求。</td></tr>
                </tbody>
              </table>
            </div>
          </section>
        </template>

        <section v-else-if="isTransactionMode" class="workbench-table-section workbench-recent-table">
          <div class="workbench-subheading"><h3>近期收退料明細</h3><span>共 {{ recentTotal }} 筆 · 每頁 {{ RECENT_PAGE_SIZE }} 筆</span></div>
          <div class="workbench-table-wrap" :aria-busy="recentLoading">
            <table>
              <thead><tr><th>日期</th><th>類型</th><th>單號</th><th>治具</th><th>識別碼</th><th>來源</th><th>數量</th></tr></thead>
              <tbody>
                <tr v-for="row in recentRows" :key="row.key">
                  <td>{{ formatLocalDate(row.occurredAt) }}</td>
                  <td>{{ row.type === "receipt" ? "收料" : "退料" }}</td>
                  <td>{{ row.transactionNo }}</td>
                  <td><button class="workbench-table-link" type="button" @click="transactionForm.fixtureCode = row.fixtureCode; showTransactionFixture()">{{ row.fixtureCode }}</button></td>
                  <td>{{ row.identifier }}</td>
                  <td>{{ row.ownership === "customer_supplied" ? "客供" : "自購" }}</td>
                  <td><strong>{{ row.quantity }} pcs</strong></td>
                </tr>
                <tr v-if="recentRows.length === 0"><td colspan="7">目前沒有近期作業。</td></tr>
              </tbody>
            </table>
          </div>
          <div v-if="recentTotal > RECENT_PAGE_SIZE" class="workbench-table-pager" aria-label="近期作業分頁">
            <button type="button" :disabled="recentPage <= 1 || recentLoading" @click="previousRecentPage">上一頁</button>
            <span>第 {{ recentPage }} / {{ recentPageCount }} 頁</span>
            <button type="button" :disabled="recentPage >= recentPageCount || recentLoading" @click="nextRecentPage">下一頁</button>
          </div>
        </section>

        <div v-else-if="activeMode === 'management'" class="workbench-empty-state workbench-management-empty">
          <span>ADMIN</span>
          <h3>從左側選擇管理功能</h3>
          <p>管理頁會沿用工作台框架；匯出中心則在目前頁面直接開啟。</p>
        </div>

        <div
          v-else
          class="workbench-empty-state"
          :data-workbench-empty-state="lastSearchMiss ? 'not-found' : 'idle'"
        >
          <span v-if="lastSearchMiss" class="workbench-empty-search-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" focusable="false"><circle cx="10.5" cy="10.5" r="5.5"/><path d="m15 15 5 5"/></svg>
          </span>
          <span v-else>{{ activeMode === "fixture" ? "治具" : "機種" }}</span>
          <h3 v-if="lastSearchMiss">找不到「{{ lastSearchMiss.token }}」</h3>
          <h3 v-else>從左側輸入條件開始查詢</h3>
          <p v-if="lastSearchMiss">請確認{{ lastSearchMiss.entityLabel }}編號、名稱或目前客戶是否正確，再重新查詢。</p>
          <p v-else>結果會留在同一畫面，右側同步顯示圖片、儲位與關聯資料。</p>
          <button v-if="lastSearchMiss" class="workbench-clear-search" type="button" @click="clearSearch">清除搜尋</button>
        </div>
      </main>

      <aside class="workbench-panel workbench-detail" aria-label="治具與機種詳情">
        <div class="workbench-panel-heading">
          <div><span>現場資訊</span><h2>{{ fixtureContext ? "治具詳情" : modelContext ? "機種摘要" : activeMode === "management" ? "管理捷徑" : "等待查詢" }}</h2></div>
          <button
            v-if="canInlineEdit && !inlineEditMode && (fixtureContext || modelContext)"
            class="workbench-inline-edit-trigger"
            type="button"
            :disabled="inlineEditLoading"
            :aria-label="fixtureContext ? '編輯治具資料' : '編輯機種資料'"
            @click="openInlineEditor(fixtureContext ? 'fixture' : 'model')"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
              <path d="M4 20h4l11-11-4-4L4 16v4Z" />
              <path d="m13.5 6.5 4 4" />
            </svg>
            <span>{{ inlineEditLoading ? "載入中" : "Edit" }}</span>
          </button>
        </div>

        <div v-if="inlineEditLoading" class="workbench-inline-edit-loading" role="status">載入可編輯欄位…</div>

        <FixtureEditForm
          v-else-if="inlineEditMode === 'fixture' && fixtureContext"
          class="workbench-inline-editor"
          :customer-id="selectedCustomerId ?? undefined"
          :fixture="fixtureContext.fixture"
          :assigned-users="inlineEditUsers"
          @saved="handleInlineEditSaved"
          @cancel="confirmInlineEditorClose"
          @dirty-change="setInlineEditDirty"
        />

        <ModelEditForm
          v-else-if="inlineEditMode === 'model' && modelContext"
          class="workbench-inline-editor"
          :customer-id="selectedCustomerId ?? undefined"
          :model="modelContext.model"
          @saved="handleInlineEditSaved"
          @cancel="confirmInlineEditorClose"
          @dirty-change="setInlineEditDirty"
        />

        <template v-else-if="fixtureContext">
          <div class="workbench-image-frame">
            <img v-if="imageUrl" :src="imageUrl" :alt="`${fixtureContext.fixture.code} 治具圖片`" />
            <div v-else class="workbench-image-empty">
              <span>IMAGE</span>
              <p>{{ imageMissing ? "目前沒有治具圖片" : "圖片載入中" }}</p>
            </div>
          </div>
          <dl class="workbench-detail-list">
            <div><dt>治具編號</dt><dd>{{ fixtureContext.fixture.code }}</dd></div>
            <div><dt>治具名稱</dt><dd>{{ fixtureContext.fixture.name }}</dd></div>
            <div><dt>線邊儲位</dt><dd>{{ fixtureContext.fixture.line_storage_location || "尚未設定" }}</dd></div>
            <div><dt>部門儲位</dt><dd>{{ fixtureContext.fixture.department_storage_location || "尚未設定" }}</dd></div>
          </dl>
          <section class="workbench-related">
            <div class="workbench-subheading"><h3>使用機種與站點</h3><span>{{ fixtureContext.station_rows.length }}</span></div>
            <div v-if="fixtureContext.station_rows.length" class="workbench-related-list">
              <article v-for="row in fixtureContext.station_rows" :key="`${row.model_id}-${row.station_id}`">
                <strong>{{ row.model_code }}</strong>
                <span>{{ row.station_code }} · 每站 {{ row.required_qty }} pcs</span>
              </article>
            </div>
            <p v-else class="workbench-empty-small">尚未配置使用機種。</p>
          </section>
        </template>

        <template v-else-if="modelContext">
          <div class="workbench-model-hero">
            <span>MODEL</span>
            <strong>{{ modelContext.model.code }}</strong>
            <p>{{ modelContext.model.name }}</p>
          </div>
          <dl class="workbench-detail-list">
            <div><dt>整機瓶頸產能</dt><dd>{{ modelContext.query.max_open_station_count }} 站</dd></div>
            <div><dt>瓶頸站點</dt><dd>{{ bottleneckStation?.station_code || "尚未判定" }}</dd></div>
            <div><dt>瓶頸治具</dt><dd>{{ bottleneckStation?.bottleneck_fixture_code || "尚未判定" }}</dd></div>
            <div><dt>站點數</dt><dd>{{ modelContext.query.station_count }}</dd></div>
            <div><dt>治具種類</dt><dd>{{ modelContext.query.fixture_type_count }}</dd></div>
            <div><dt>治具總庫存</dt><dd>{{ modelContext.query.total_stock_qty }} pcs</dd></div>
          </dl>
          <p class="workbench-capacity-note">整機瓶頸產能取各站完整需求集合的最低可開站數；中間表格可查看每站及各治具的計算結果。</p>
        </template>

        <div v-else class="workbench-detail-empty" :data-workbench-detail-state="lastSearchMiss ? 'not-found' : activeMode === 'management' ? 'management' : 'idle'">
          <div class="workbench-empty-icon">⌁</div>
          <h3>{{ lastSearchMiss ? "查無結果" : activeMode === "management" ? "依角色顯示可用功能" : "尚未選擇資料" }}</h3>
          <p v-if="lastSearchMiss">目前客戶沒有符合「{{ lastSearchMiss.token }}」的{{ lastSearchMiss.entityLabel }}。</p>
          <p v-else-if="activeMode === 'management'">Admin 可使用帳目與品質管理，Super Admin 另可管理客戶與使用者；一般使用者與訪客只會看到符合權限的入口。</p>
          <p v-else>查詢治具後顯示圖片、儲位和使用機種；查詢機種後顯示產能摘要。</p>
        </div>
      </aside>
    </div>
  </section>
</template>

<style scoped src="@/styles/surfaces/workbench.css"></style>
