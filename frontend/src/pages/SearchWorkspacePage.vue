<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter, type LocationQueryRaw } from "vue-router";

import { api, fetchFixtureImageObjectUrl } from "@/api";
import { authSession, requestInventoryBatchOpen, selectedCustomerId, setCustomerSwitchGuard } from "@/appState";
import { requestConfirmation } from "@/confirmState";
import InlineSpinner from "@/components/common/InlineSpinner.vue";
import FixtureOverviewPanel from "@/components/search/FixtureOverviewPanel.vue";
import FixtureInfoPanel from "@/components/search/FixtureInfoPanel.vue";
import ModelInfoPanel from "@/components/search/ModelInfoPanel.vue";
import SearchHeroSection from "@/components/search/SearchHeroSection.vue";
import SearchResultPanel from "@/components/search/SearchResultPanel.vue";
import { pushToast } from "@/toastState";
import type {
  AppUser,
  MaterialTransaction,
  ModelQueryFixture,
  SearchFixtureContext,
  SearchModelContext,
  SearchResult,
  StockStatus
} from "@/types";
import type { FixtureSearchMode, SearchWorkspaceHandoffState } from "@/utils/searchHomeModeState";
import { formatLocalDate } from "@/utils/date";
import { groupIdentifierStockByOwnership } from "@/utils/display";

type SearchMode = "fixture" | "model";

const emit = defineEmits<{
  reportContextChange: [state: SearchWorkspaceHandoffState];
}>();
type DetailTab = "info" | "edit";

type RecentFixtureShortcut = {
  fixtureCode: string;
  transactionType: "receipt" | "return";
  occurredAt: string;
};

const SEARCH_PAGE_SIZE = 12;
const FIXTURE_OVERVIEW_PAGE_SIZE = 20;
const RECENT_SHORTCUT_TRANSACTION_LIMIT = 80;
const FIXTURE_CONTEXT_TRANSACTION_LIMIT = 8;
const MAX_RECENT_FIXTURE_SHORTCUTS = 20;

const FixtureEditForm = defineAsyncComponent({
  loader: () => import("@/components/search/FixtureEditForm.vue"),
  loadingComponent: InlineSpinner,
  delay: 120
});

const ModelEditForm = defineAsyncComponent({
  loader: () => import("@/components/search/ModelEditForm.vue"),
  loadingComponent: InlineSpinner,
  delay: 120
});

const router = useRouter();
const route = useRoute();
const nf = new Intl.NumberFormat("zh-TW");

const FIXTURE_SECTION_KEY = "search-fixture-sections";
const MODEL_SECTION_KEY = "search-model-sections";
const MODE_KEY = "search-mode";
const DETAIL_TAB_KEY = "search-detail-tab";

const defaultFixtureSections = ["summary", "image", "identifier", "transactions", "models", "stations"];
const defaultModelSections = ["summary", "stations", "fixtures", "requirements"];

const mode = ref<SearchMode>("fixture");
const fixtureSearchMode = ref<FixtureSearchMode>("fixture");
const detailTab = ref<DetailTab>("info");
const queryDraft = ref("");
const committedQuery = ref("");
const loading = ref(false);
const loadingMore = ref(false);
const detailLoading = ref(false);
const customerUsers = ref<AppUser[]>([]);
const recentTransactions = ref<MaterialTransaction[]>([]);
const searchResults = ref<SearchResult[]>([]);
const searchTotal = ref(0);
const searchPage = ref(1);
const searchHasMore = ref(false);
const fixtureOverviewRows = ref<SearchResult[]>([]);
const fixtureOverviewTotal = ref(0);
const fixtureOverviewPage = ref(1);
const fixtureOverviewHasMore = ref(false);
const fixtureOverviewLoading = ref(false);
const fixtureOverviewLoadingMore = ref(false);
const selectedResultId = ref<number | null>(null);
const selectedFixtureContext = ref<SearchFixtureContext | null>(null);
const selectedModelContext = ref<SearchModelContext | null>(null);
const selectedFixtureImage = ref("");
const imageLoadFailed = ref(false);
const resultPanel = ref<HTMLElement | null>(null);
const hasUnsavedFixtureDraft = ref(false);
const hasUnsavedModelDraft = ref(false);

const fixtureSectionSelection = ref<string[]>(loadSelection(FIXTURE_SECTION_KEY, defaultFixtureSections));
const modelSectionSelection = ref<string[]>(loadSelection(MODEL_SECTION_KEY, defaultModelSections));

let detailRequestId = 0;
let searchRequestId = 0;
let fixtureOverviewRequestId = 0;
let syncingSearchRoute = false;
let searchRouteReady = false;

const SEARCH_ROUTE_KEYS = new Set([
  "mode",
  "fixture_search",
  "q",
  "query_draft",
  "page",
  "selected_id",
  "detail"
]);

function loadSelection(key: string, fallback: string[]): string[] {
  const raw = localStorage.getItem(key);
  if (!raw) return [...fallback];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) && parsed.length > 0 ? parsed : [...fallback];
  } catch {
    return [...fallback];
  }
}

function readRouteString(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }
  if (Array.isArray(value) && typeof value[0] === "string") {
    return value[0];
  }
  return "";
}

function readPositiveInteger(value: unknown, fallback: number): number {
  const parsed = Number.parseInt(readRouteString(value), 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function formatCount(value: number): string {
  return nf.format(value);
}

function stockTone(status: StockStatus | undefined): "normal" | "warn" | "danger" | "muted" {
  if (status === "low_stock") return "warn";
  if (status === "out_of_stock") return "danger";
  if (status === "normal") return "normal";
  return "muted";
}

const customerId = computed(() => selectedCustomerId.value ?? undefined);
const canEdit = computed(() => authSession.value?.role !== "guest");
const canOperateInventory = computed(() => authSession.value?.role !== "guest");
const canAccessProduction = computed(() => authSession.value?.role !== "guest");
const hasActiveQuery = computed(() => committedQuery.value.trim().length > 0);
const panelLoading = computed(() => loading.value || detailLoading.value);
const selectedFixture = computed(() => selectedFixtureContext.value?.fixture ?? null);
const selectedFixtureStock = computed(() => selectedFixtureContext.value?.stock ?? null);
const selectedModel = computed(() => selectedModelContext.value?.model ?? null);
const selectedSearchResult = computed(() =>
  searchResults.value.find((row) => row.reference_id === selectedResultId.value) ?? null
);
const selectedExactIdentifier = computed(() =>
  mode.value === "fixture" && fixtureSearchMode.value === "identifier"
    ? selectedSearchResult.value?.matched_identifier?.trim() || ""
    : ""
);
const visibleFixtureSections = computed(() => {
  const keys = new Set(fixtureSectionSelection.value);
  return {
    summary: keys.has("summary"),
    image: keys.has("image"),
    identifier: keys.has("identifier"),
    transactions: keys.has("transactions"),
    models: keys.has("models"),
    stations: keys.has("stations"),
    maintenance: keys.has("maintenance")
  };
});
const effectiveVisibleFixtureSections = computed(() =>
  selectedExactIdentifier.value
    ? {
        summary: true,
        image: true,
        identifier: false,
        transactions: true,
        models: false,
        stations: false,
        maintenance: false
      }
    : visibleFixtureSections.value
);
const visibleModelSections = computed(() => {
  const keys = new Set(modelSectionSelection.value);
  return {
    summary: keys.has("summary"),
    stations: keys.has("stations"),
    fixtures: keys.has("fixtures"),
    requirements: keys.has("requirements"),
    maintenance: keys.has("maintenance")
  };
});
const shouldShowFixtureCreateForm = computed(
  () => mode.value === "fixture" && searchResults.value.length === 0 && visibleFixtureSections.value.maintenance && detailTab.value === "edit" && canEdit.value
);
const shouldShowModelCreateForm = computed(
  () => mode.value === "model" && searchResults.value.length === 0 && visibleModelSections.value.maintenance && detailTab.value === "edit" && canEdit.value
);
const fixtureSectionChips = computed(() =>
  [
    { key: "summary", label: "總覽" },
    { key: "image", label: "圖片" },
    { key: "identifier", label: "datecode/編號庫存" },
    { key: "transactions", label: "收退料" },
    { key: "models", label: "相關機種" },
    { key: "stations", label: "站點詳細" },
    canEdit.value ? { key: "maintenance", label: "資料維護" } : null
  ].filter((item): item is { key: string; label: string } => item !== null)
);
const modelSectionChips = computed(() =>
  [
    { key: "summary", label: "總覽" },
    { key: "stations", label: "站點" },
    { key: "fixtures", label: "治具" },
    { key: "requirements", label: "需求明細" },
    canEdit.value ? { key: "maintenance", label: "資料維護" } : null
  ].filter((item): item is { key: string; label: string } => item !== null)
);
const activeSectionKeys = computed(() =>
  selectedExactIdentifier.value
    ? []
    : mode.value === "fixture"
      ? fixtureSectionSelection.value
      : modelSectionSelection.value
);
const currentSectionChips = computed(() =>
  selectedExactIdentifier.value
    ? []
    : mode.value === "fixture"
      ? fixtureSectionChips.value
      : modelSectionChips.value
);
const shouldShowEmptyResultState = computed(
  () => searchResults.value.length === 0 && !shouldShowFixtureCreateForm.value && !shouldShowModelCreateForm.value
);
const hasUnsavedDraft = computed(() => detailTab.value === "edit" && (hasUnsavedFixtureDraft.value || hasUnsavedModelDraft.value));
const selectedFixtureIdentifierGroups = computed(() =>
  groupIdentifierStockByOwnership(selectedFixtureContext.value?.identifier_rows ?? [])
);
const selectedFixtureIdentifierTotalQty = computed(() =>
  (selectedFixtureContext.value?.identifier_rows ?? []).reduce((sum, row) => sum + row.stock_qty, 0)
);
const selectedFixtureTransactions = computed(() => selectedFixtureContext.value?.transactions ?? []);
const selectedFixtureModels = computed(() => selectedFixtureContext.value?.related_models ?? []);
const selectedFixtureStationRows = computed(() => selectedFixtureContext.value?.station_rows ?? []);
const selectedModelFixtures = computed(() =>
  (selectedModelContext.value?.query.fixtures ?? []).map((row) => ({
    ...(row as ModelQueryFixture),
    identifierTags: [] as string[]
  }))
);
const recentFixtureShortcuts = computed<RecentFixtureShortcut[]>(() => {
  const seen = new Set<string>();
  const shortcuts: RecentFixtureShortcut[] = [];
  const sortedTransactions = recentTransactions.value
    .slice()
    .sort((a, b) => new Date(b.occurred_at).getTime() - new Date(a.occurred_at).getTime());

  for (const tx of sortedTransactions) {
    for (const item of tx.items) {
      if (!item.fixture_code || seen.has(item.fixture_code)) {
        continue;
      }
      seen.add(item.fixture_code);
      shortcuts.push({
        fixtureCode: item.fixture_code,
        transactionType: tx.transaction_type,
        occurredAt: tx.occurred_at
      });
      if (shortcuts.length >= MAX_RECENT_FIXTURE_SHORTCUTS) {
        return shortcuts;
      }
    }
  }

  return shortcuts;
});

function clearSelectedFixtureImage(): void {
  if (selectedFixtureImage.value) {
    URL.revokeObjectURL(selectedFixtureImage.value);
    selectedFixtureImage.value = "";
  }
}

async function refreshSelectedFixtureImage(): Promise<void> {
  clearSelectedFixtureImage();
  imageLoadFailed.value = false;
  if (!selectedFixture.value || selectedCustomerId.value == null) {
    return;
  }
  try {
    selectedFixtureImage.value = await fetchFixtureImageObjectUrl(selectedFixture.value.code, selectedCustomerId.value);
  } catch {
    imageLoadFailed.value = true;
  }
}

async function loadCustomerScopedShellData(): Promise<void> {
  if (!customerId.value) {
    customerUsers.value = [];
    recentTransactions.value = [];
    return;
  }
  try {
    const [assignedUsers, txRows] = await Promise.all([
      api.listCustomerUsers(customerId.value),
      api.listTransactions(RECENT_SHORTCUT_TRANSACTION_LIMIT, customerId.value)
    ]);
    customerUsers.value = assignedUsers;
    recentTransactions.value = txRows;
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "載入查詢頁輔助資料失敗", "error");
  }
}

async function loadSelectedContext(): Promise<void> {
  if (!customerId.value || !selectedResultId.value) {
    selectedFixtureContext.value = null;
    selectedModelContext.value = null;
    clearSelectedFixtureImage();
    return;
  }
  const requestId = ++detailRequestId;
  detailLoading.value = true;
  try {
    if (mode.value === "fixture") {
      const matchedIdentifier = selectedExactIdentifier.value || undefined;
      const context = await api.getFixtureSearchContext(
        selectedResultId.value,
        customerId.value,
        FIXTURE_CONTEXT_TRANSACTION_LIMIT,
        matchedIdentifier
      );
      if (requestId !== detailRequestId) return;
      selectedFixtureContext.value = context;
      selectedModelContext.value = null;
      await refreshSelectedFixtureImage();
      return;
    }

    const context = await api.getModelSearchContext(selectedResultId.value, customerId.value);
    if (requestId !== detailRequestId) return;
    selectedModelContext.value = context;
    selectedFixtureContext.value = null;
    clearSelectedFixtureImage();
  } catch (err) {
    if (requestId !== detailRequestId) return;
    selectedFixtureContext.value = null;
    selectedModelContext.value = null;
    pushToast(err instanceof Error ? err.message : "載入查詢結果詳細資料失敗。", "error");
  } finally {
    if (requestId === detailRequestId) {
      detailLoading.value = false;
    }
  }
}

function buildSearchRouteQuery(): LocationQueryRaw {
  const query: LocationQueryRaw = {
    mode: mode.value,
    q: committedQuery.value.trim()
  };
  if (mode.value === "fixture") {
    query.fixture_search = fixtureSearchMode.value;
  }
  if (searchPage.value > 1) {
    query.page = String(searchPage.value);
  }
  if (selectedResultId.value !== null) {
    query.selected_id = String(selectedResultId.value);
  }
  if (detailTab.value === "edit") {
    query.detail = "edit";
  }
  const draftQuery = queryDraft.value.trim();
  if (draftQuery && draftQuery !== committedQuery.value.trim()) {
    query.query_draft = draftQuery;
  }
  return query;
}

function buildCurrentSearchLocation(): { path: string; query: LocationQueryRaw } {
  const preserved = Object.fromEntries(
    Object.entries(route.query).filter(([key]) => !SEARCH_ROUTE_KEYS.has(key))
  );
  return {
    path: route.path,
    query: {
      ...preserved,
      ...buildSearchRouteQuery()
    }
  };
}

async function syncSearchRoute(history: "push" | "replace"): Promise<void> {
  const target = buildCurrentSearchLocation();
  if (router.resolve(target).fullPath === route.fullPath) return;
  syncingSearchRoute = true;
  try {
    await router[history](target);
  } finally {
    syncingSearchRoute = false;
  }
}

async function loadFixtureOverview(append = false): Promise<void> {
  const requestId = ++fixtureOverviewRequestId;
  if (!customerId.value) {
    fixtureOverviewRows.value = [];
    fixtureOverviewTotal.value = 0;
    fixtureOverviewPage.value = 1;
    fixtureOverviewHasMore.value = false;
    fixtureOverviewLoading.value = false;
    fixtureOverviewLoadingMore.value = false;
    return;
  }

  const targetPage = append ? fixtureOverviewPage.value + 1 : 1;
  if (append) {
    fixtureOverviewLoadingMore.value = true;
  } else {
    fixtureOverviewRows.value = [];
    fixtureOverviewTotal.value = 0;
    fixtureOverviewPage.value = 1;
    fixtureOverviewHasMore.value = false;
    fixtureOverviewLoading.value = true;
  }
  try {
    const page = await api.getFixtureOverview(
      customerId.value,
      targetPage,
      FIXTURE_OVERVIEW_PAGE_SIZE
    );
    if (requestId !== fixtureOverviewRequestId) return;
    fixtureOverviewRows.value = append
      ? [...fixtureOverviewRows.value, ...page.items]
      : page.items;
    fixtureOverviewTotal.value = page.total;
    fixtureOverviewPage.value = page.page;
    fixtureOverviewHasMore.value = page.has_more;
  } catch (err) {
    if (requestId !== fixtureOverviewRequestId) return;
    pushToast(err instanceof Error ? err.message : "載入治具總覽失敗。", "error");
  } finally {
    if (requestId === fixtureOverviewRequestId) {
      fixtureOverviewLoading.value = false;
      fixtureOverviewLoadingMore.value = false;
    }
  }
}

function notifyReportContextChange(): void {
  emit("reportContextChange", {
    mode: mode.value,
    fixtureSearchMode: fixtureSearchMode.value,
    draftQuery: queryDraft.value,
    committedQuery: committedQuery.value,
    selectedResultId: selectedResultId.value
  });
}

function buildSearchReturnTo(): string {
  const query = buildSearchRouteQuery();
  if (route.name === "search") {
    query.ui_surface = "modern";
    query.home_mode = "query";
  }
  return router.resolve({
    name: route.name === "search" ? "search" : "search-detail",
    query
  }).fullPath;
}

async function confirmDiscardSearchDraft(message = "目前有未儲存的修改，離開後會遺失。要繼續嗎？"): Promise<boolean> {
  if (!hasUnsavedDraft.value) {
    return true;
  }
  return requestConfirmation(message, {
    title: "捨棄未儲存修改？",
    confirmLabel: "捨棄並繼續",
    tone: "danger"
  });
}

function resetDraftFlags(): void {
  hasUnsavedFixtureDraft.value = false;
  hasUnsavedModelDraft.value = false;
}

async function runSearch(options: { append?: boolean; preferredId?: number | null; scrollToPanel?: boolean } = {}): Promise<void> {
  const q = committedQuery.value.trim();
  if (!q || !customerId.value) {
    searchResults.value = [];
    searchTotal.value = 0;
    searchPage.value = 1;
    searchHasMore.value = false;
    selectedResultId.value = null;
    selectedFixtureContext.value = null;
    selectedModelContext.value = null;
    return;
  }

  const append = options.append === true;
  const shouldScrollToPanel = options.scrollToPanel !== false;
  const targetPage = append ? searchPage.value + 1 : 1;
  const requestId = ++searchRequestId;
  if (append) {
    loadingMore.value = true;
  } else {
    loading.value = true;
  }
  try {
    const page = await api.globalSearch({
      q,
      customerId: customerId.value,
      entityType: mode.value,
      fixtureSearchMode: mode.value === "fixture" ? fixtureSearchMode.value : undefined,
      page: targetPage,
      pageSize: SEARCH_PAGE_SIZE
    });
    if (requestId !== searchRequestId) return;
    searchResults.value = append ? [...searchResults.value, ...page.items] : page.items;
    searchPage.value = page.page;
    searchTotal.value = page.total;
    searchHasMore.value = page.has_more;

    const preferredId = options.preferredId ?? selectedResultId.value;
    const nextSelectedId = searchResults.value.find((row) => row.reference_id === preferredId)?.reference_id ?? searchResults.value[0]?.reference_id ?? null;
    if (selectedResultId.value !== nextSelectedId) {
      selectedResultId.value = nextSelectedId;
    } else if (!append && nextSelectedId !== null) {
      await loadSelectedContext();
    }
    if (!append && shouldScrollToPanel && page.items.length > 0) {
      await scrollToResultPanel();
    }
  } catch (err) {
    if (requestId !== searchRequestId) return;
    pushToast(err instanceof Error ? err.message : "搜尋失敗", "error");
  } finally {
    if (requestId === searchRequestId) {
      loading.value = false;
      loadingMore.value = false;
    }
  }
}

async function restoreSearchFromRoute(): Promise<void> {
  const routeMode = readRouteString(route.query.mode);
  const routeFixtureSearchMode = readRouteString(route.query.fixture_search);
  const routeQuery = readRouteString(route.query.q).trim();
  const routeDraftQuery = readRouteString(route.query.query_draft).trim();
  if (routeMode === "fixture" || routeMode === "model") {
    mode.value = routeMode;
  }
  fixtureSearchMode.value = routeFixtureSearchMode === "identifier" ? "identifier" : "fixture";
  queryDraft.value = routeDraftQuery || routeQuery;
  committedQuery.value = routeQuery;
  detailTab.value = readRouteString(route.query.detail) === "edit" ? "edit" : "info";
  if (!routeQuery) {
    searchResults.value = [];
    searchTotal.value = 0;
    searchPage.value = 1;
    searchHasMore.value = false;
    selectedResultId.value = null;
    selectedFixtureContext.value = null;
    selectedModelContext.value = null;
    clearSelectedFixtureImage();
    return;
  }

  const targetPage = readPositiveInteger(route.query.page, 1);
  const preferredId = readPositiveInteger(route.query.selected_id, 0) || null;

  await runSearch({ preferredId, scrollToPanel: false });
  while (searchPage.value < targetPage && searchHasMore.value) {
    await runSearch({ append: true, preferredId, scrollToPanel: false });
  }
  if (searchResults.value.length > 0) {
    await scrollToResultPanel();
  }
}

async function submitSearch(): Promise<void> {
  if (!(await confirmDiscardSearchDraft())) {
    return;
  }
  resetDraftFlags();
  committedQuery.value = queryDraft.value.trim();
  detailTab.value = "info";
  searchPage.value = 1;
  selectedResultId.value = null;
  await runSearch();
  await syncSearchRoute("push");
}

async function clearSearch(): Promise<void> {
  if (!(await confirmDiscardSearchDraft())) {
    return;
  }
  queryDraft.value = "";
  committedQuery.value = "";
  detailTab.value = "info";
  searchResults.value = [];
  searchTotal.value = 0;
  searchPage.value = 1;
  searchHasMore.value = false;
  selectedResultId.value = null;
  selectedFixtureContext.value = null;
  selectedModelContext.value = null;
  clearSelectedFixtureImage();
  resetDraftFlags();
  await syncSearchRoute("push");
}

async function loadMoreResults(): Promise<void> {
  if (!searchHasMore.value || loadingMore.value) {
    return;
  }
  await runSearch({ append: true });
  await syncSearchRoute("replace");
}

function toggleSection(targetMode: SearchMode, key: string): void {
  const source = targetMode === "fixture" ? fixtureSectionSelection : modelSectionSelection;
  const current = new Set(source.value);
  if (current.has(key)) {
    if (current.size === 1) {
      pushToast("至少保留一個顯示區塊。", "warning");
      return;
    }
    current.delete(key);
  } else {
    current.add(key);
  }
  source.value = [...current];
  if (key === "maintenance" && !current.has("maintenance") && detailTab.value === "edit") {
    detailTab.value = "info";
  }
}

function persistSelections(): void {
  localStorage.setItem(FIXTURE_SECTION_KEY, JSON.stringify(fixtureSectionSelection.value));
  localStorage.setItem(MODEL_SECTION_KEY, JSON.stringify(modelSectionSelection.value));
  localStorage.setItem(MODE_KEY, mode.value);
  localStorage.setItem(DETAIL_TAB_KEY, detailTab.value);
}

async function applyRecentFixtureShortcut(fixtureCode: string): Promise<void> {
  if (!(await confirmDiscardSearchDraft())) {
    return;
  }
  resetDraftFlags();
  mode.value = "fixture";
  queryDraft.value = fixtureCode;
  committedQuery.value = fixtureCode;
  detailTab.value = "info";
  await runSearch();
  await syncSearchRoute("push");
}

async function openFixtureFromOverview(row: SearchResult): Promise<void> {
  await applyRecentFixtureShortcut(row.title);
}

function goToFixtureInventoryOverview(): void {
  if (!selectedFixture.value) {
    return;
  }
  void router.push({
    path: "/inventory/overview",
    query: {
      fixture_code: selectedFixture.value.code,
      ...(selectedExactIdentifier.value ? { tracking_code: selectedExactIdentifier.value } : {}),
      return_to: buildSearchReturnTo()
    }
  });
}

function goToFixtureBatchImport(): void {
  if (!selectedFixture.value) {
    return;
  }
  requestInventoryBatchOpen(selectedFixture.value.code);
}

async function goCreateFromNoResult(): Promise<void> {
  if (!canEdit.value) {
    return;
  }
  const selection = mode.value === "fixture" ? fixtureSectionSelection : modelSectionSelection;
  if (!selection.value.includes("maintenance")) {
    selection.value = [...selection.value, "maintenance"];
  }
  detailTab.value = "edit";
  await syncSearchRoute("push");
}

async function handleModeChange(nextMode: SearchMode): Promise<void> {
  if (nextMode === mode.value) {
    return;
  }
  if (!(await confirmDiscardSearchDraft())) {
    return;
  }
  resetDraftFlags();
  mode.value = nextMode;
  searchPage.value = 1;
  selectedResultId.value = null;
  if (hasActiveQuery.value) await runSearch();
  await syncSearchRoute("push");
}

async function handleFixtureSearchModeChange(nextMode: FixtureSearchMode): Promise<void> {
  if (nextMode === fixtureSearchMode.value) return;
  if (!(await confirmDiscardSearchDraft())) return;
  resetDraftFlags();
  fixtureSearchMode.value = nextMode;
  searchPage.value = 1;
  selectedResultId.value = null;
  if (hasActiveQuery.value) await runSearch();
  await syncSearchRoute("push");
}

async function handleResultSelection(nextResultId: number): Promise<void> {
  if (nextResultId === selectedResultId.value) {
    return;
  }
  if (!(await confirmDiscardSearchDraft())) {
    return;
  }
  resetDraftFlags();
  selectedResultId.value = nextResultId;
  await syncSearchRoute("push");
}

async function handleDetailTabChange(nextTab: DetailTab): Promise<void> {
  if (nextTab === detailTab.value) {
    return;
  }
  if (detailTab.value === "edit" && !(await confirmDiscardSearchDraft())) {
    return;
  }
  if (nextTab !== "edit") {
    resetDraftFlags();
  }
  detailTab.value = nextTab;
  await syncSearchRoute("push");
}

async function cancelEdit(): Promise<void> {
  if (detailTab.value === "edit" && !(await confirmDiscardSearchDraft())) {
    return;
  }
  resetDraftFlags();
  detailTab.value = "info";
  await syncSearchRoute("replace");
}

function goToProduction(): void {
  if (!selectedModel.value) {
    return;
  }
  void router.push({
    name: "production",
    query: {
      model_id: String(selectedModel.value.id),
      return_to: buildSearchReturnTo()
    }
  });
}

async function handleFixtureSaved(fixtureId: number): Promise<void> {
  detailTab.value = "info";
  await runSearch({ preferredId: fixtureId });
  await syncSearchRoute("replace");
  pushToast("治具資料已更新。", "success");
}

async function handleModelSaved(modelId: number): Promise<void> {
  detailTab.value = "info";
  await runSearch({ preferredId: modelId });
  await syncSearchRoute("replace");
  pushToast("機種資料已更新。", "success");
}

async function scrollToResultPanel(): Promise<void> {
  await nextTick();
  await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));
  const panel = resultPanel.value;
  if (!panel) {
    return;
  }
  const top = panel.getBoundingClientRect().top + window.scrollY - 200;
  window.scrollTo({
    top: Math.max(0, top),
    behavior: "smooth"
  });
}

watch(mode, () => {
  if (mode.value === "fixture" && !visibleFixtureSections.value.maintenance && detailTab.value === "edit") {
    detailTab.value = "info";
  }
  if (mode.value === "model" && !visibleModelSections.value.maintenance && detailTab.value === "edit") {
    detailTab.value = "info";
  }
  persistSelections();
});

watch([fixtureSectionSelection, modelSectionSelection, detailTab], persistSelections, { deep: true });
watch(queryDraft, () => {
  if (queryDraft.value.trim().length === 0 && committedQuery.value.length > 0) {
    committedQuery.value = "";
  }
});
watch(customerId, async () => {
  await Promise.all([loadCustomerScopedShellData(), loadFixtureOverview()]);
  if (hasActiveQuery.value) {
    await runSearch();
    return;
  }
  clearSearch();
});
watch(selectedResultId, async () => {
  await loadSelectedContext();
});
watch([mode, fixtureSearchMode, queryDraft, committedQuery, selectedResultId], notifyReportContextChange);
onMounted(async () => {
  const savedMode = localStorage.getItem(MODE_KEY);
  if (savedMode === "fixture" || savedMode === "model") {
    mode.value = savedMode;
  }
  const savedDetailTab = localStorage.getItem(DETAIL_TAB_KEY);
  if (savedDetailTab === "info" || savedDetailTab === "edit") {
    detailTab.value = savedDetailTab;
  }

  await Promise.all([loadCustomerScopedShellData(), loadFixtureOverview()]);
  await restoreSearchFromRoute();
  searchRouteReady = true;
  notifyReportContextChange();
});

watch(
  () => route.fullPath,
  async () => {
    if (!searchRouteReady || syncingSearchRoute) return;
    await restoreSearchFromRoute();
  }
);

onBeforeUnmount(() => {
  clearSelectedFixtureImage();
  setCustomerSwitchGuard("search-page", false, "搜尋頁有尚未儲存的治具／機種修改");
});

watch(detailTab, (value) => {
  if (value !== "edit") {
    resetDraftFlags();
  }
});

watch(
  hasUnsavedDraft,
  (value) => {
    setCustomerSwitchGuard("search-page", value, "搜尋頁有尚未儲存的治具／機種修改");
  },
  { immediate: true }
);

</script>

<template>
  <div class="search-shell" :class="{ idle: !hasActiveQuery }">
    <div class="search-workspace-card" :class="{ idle: !hasActiveQuery }">
      <div class="search-workspace-query">
        <SearchHeroSection
          :mode="mode"
          :fixture-search-mode="fixtureSearchMode"
          :query-draft="queryDraft"
          :has-active-query="hasActiveQuery"
          :recent-fixture-shortcuts="recentFixtureShortcuts"
          :section-chips="currentSectionChips"
          :active-section-keys="activeSectionKeys"
          @update:mode="handleModeChange"
          @update:fixture-search-mode="handleFixtureSearchModeChange"
          @update:query-draft="queryDraft = $event"
          @submit="submitSearch"
          @clear="clearSearch"
          @apply-recent-fixture-shortcut="applyRecentFixtureShortcut"
          @toggle-section="toggleSection"
        />
      </div>

      <div v-if="!hasActiveQuery" class="search-workspace-overview">
        <FixtureOverviewPanel
          :rows="fixtureOverviewRows"
          :total="fixtureOverviewTotal"
          :loading="fixtureOverviewLoading"
          :loading-more="fixtureOverviewLoadingMore"
          :has-more="fixtureOverviewHasMore"
          :format-count="formatCount"
          :stock-tone="stockTone"
          @select="openFixtureFromOverview"
          @load-more="loadFixtureOverview(true)"
        />
      </div>
    </div>

    <section v-if="hasActiveQuery" ref="resultPanel" class="content-grid">
      <SearchResultPanel
        :can-edit="canEdit"
        :show-maintenance-tab="mode === 'fixture' ? effectiveVisibleFixtureSections.maintenance : visibleModelSections.maintenance"
        :detail-tab="detailTab"
        :loading="panelLoading"
        :empty="shouldShowEmptyResultState"
        :mode="mode"
        @update:detail-tab="handleDetailTabChange"
        @create="goCreateFromNoResult"
      >
        <div class="search-results-layout">
          <aside class="result-list-card">
            <div class="result-list-head">
              <strong>搜尋結果</strong>
              <span>{{ searchTotal }} 筆</span>
            </div>
            <div class="result-list-body">
              <button
                v-for="row in searchResults"
                :key="`${row.entity_type}-${row.reference_id}`"
                class="result-row"
                :class="{ active: row.reference_id === selectedResultId }"
                type="button"
                @click="handleResultSelection(row.reference_id)"
              >
                <div class="result-row-head">
                  <strong>{{ row.title }}</strong>
                  <span class="result-type">{{ row.entity_type === "fixture" ? "治具" : row.entity_type === "model" ? "機種" : "站點" }}</span>
                </div>
                <span class="result-row-subtitle">{{ row.subtitle || "-" }}</span>
                <div v-if="row.entity_type === 'fixture'" class="result-row-meta">
                  <span v-if="row.matched_identifier">datecode/編號 {{ row.matched_identifier }}</span>
                  <span>庫存 {{ formatCount(row.stock_qty ?? 0) }}</span>
                  <span>{{ row.location_code || "-" }}</span>
                </div>
                <div class="result-row-foot">
                  <span class="result-row-status" :class="row.is_active ? 'active' : 'inactive'">{{ row.is_active ? "啟用" : "停用" }}</span>
                </div>
              </button>
            </div>
            <div v-if="searchHasMore" class="result-list-actions">
              <button class="outline-btn" type="button" :disabled="loadingMore" @click="loadMoreResults">
                {{ loadingMore ? "載入中..." : "載入更多" }}
              </button>
            </div>
          </aside>

          <div class="detail-column">
            <template v-if="mode === 'fixture'">
              <FixtureInfoPanel
                v-if="(detailTab === 'info' || !visibleFixtureSections.maintenance) && !shouldShowFixtureCreateForm"
                :fixture="selectedFixture"
                :can-operate-inventory="canOperateInventory"
                :stock="selectedFixtureStock"
                :image-url="selectedFixtureImage"
                :image-load-failed="imageLoadFailed"
                :identifier-groups="selectedFixtureIdentifierGroups"
                :identifier-total-qty="selectedFixtureIdentifierTotalQty"
                :related-models="selectedFixtureModels"
                :station-rows="selectedFixtureStationRows"
                :transactions="selectedFixtureTransactions"
                :matched-identifier="selectedExactIdentifier"
                :visible-sections="effectiveVisibleFixtureSections"
                :format-count="formatCount"
                :format-date="formatLocalDate"
                :stock-tone="stockTone"
                @open-batch-import="goToFixtureBatchImport"
                @open-transaction-overview="goToFixtureInventoryOverview"
              />
              <FixtureEditForm
                v-else
                :customer-id="customerId"
                :fixture="selectedFixture"
                :assigned-users="customerUsers"
                :initial-code="queryDraft.trim().toUpperCase()"
                @saved="handleFixtureSaved"
                @cancel="cancelEdit"
                @dirty-change="hasUnsavedFixtureDraft = $event"
              />
            </template>

            <template v-else>
              <ModelInfoPanel
                v-if="(detailTab === 'info' || !visibleModelSections.maintenance) && !shouldShowModelCreateForm"
                :model="selectedModel"
                :query-data="selectedModelContext?.query ?? null"
                :fixtures="selectedModelFixtures"
                :visible-sections="visibleModelSections"
                :format-count="formatCount"
                :can-access-production="canAccessProduction"
                :go-to-production="goToProduction"
              />
              <ModelEditForm
                v-else
                :customer-id="customerId"
                :model="selectedModel"
                :initial-code="queryDraft.trim().toUpperCase()"
                @saved="handleModelSaved"
                @cancel="cancelEdit"
                @dirty-change="hasUnsavedModelDraft = $event"
              />
            </template>
          </div>
        </div>
      </SearchResultPanel>
    </section>
  </div>
</template>

<style scoped>
.search-shell {
  --search-accent: var(--blue);
  --search-accent-soft: var(--blue-soft);
  --search-accent-strong: var(--tone-info);
  display: grid;
  gap: 12px;
  min-height: 100%;
  align-content: start;
}

.search-shell.idle {
  min-height: 0;
  align-content: start;
}

.search-workspace-card {
  position: relative;
  border: 1px solid var(--line);
  border-radius: 20px;
  background: #fff;
  box-shadow: var(--shadow);
}

.search-workspace-card::before {
  content: "";
  position: absolute;
  z-index: 2;
  inset: 0 auto 0 0;
  width: 4px;
  border-radius: 20px 0 0 20px;
  background: linear-gradient(180deg, var(--blue) 0%, color-mix(in srgb, var(--blue) 55%, white) 100%);
  pointer-events: none;
}

.search-workspace-query {
  border-radius: 20px;
  background:
    radial-gradient(circle at 0% 0%, color-mix(in srgb, var(--blue) 16%, transparent), transparent 30%),
    radial-gradient(circle at 100% 0%, color-mix(in srgb, var(--blue) 8%, transparent), transparent 26%),
    linear-gradient(180deg, #ffffff 0%, color-mix(in srgb, var(--blue-soft) 50%, white) 100%);
}

.search-workspace-card.idle .search-workspace-query {
  border-radius: 20px 20px 0 0;
}

.search-workspace-overview {
  border-top: 1px solid color-mix(in srgb, var(--blue) 14%, var(--line));
  border-radius: 0 0 20px 20px;
  background: rgba(255, 255, 255, 0.98);
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  min-height: 0;
  align-items: start;
  scroll-margin-top: 96px;
}

@media (max-width: 680px) {
  .search-workspace-card,
  .search-workspace-query {
    border-radius: 16px;
  }

  .search-workspace-card::before {
    border-radius: 16px 0 0 16px;
  }

  .search-workspace-card.idle .search-workspace-query {
    border-radius: 16px 16px 0 0;
  }

  .search-workspace-overview {
    border-radius: 0 0 16px 16px;
  }
}

.search-results-layout {
  display: grid;
  grid-template-columns: minmax(260px, 320px) minmax(0, 1fr);
  gap: 14px;
  align-items: start;
}

.result-list-card {
  display: grid;
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, color-mix(in srgb, var(--blue-soft) 34%, white) 100%);
  box-shadow: var(--shadow);
  position: sticky;
  top: 12px;
}

.result-list-head,
.result-row-head,
.result-row-foot,
.result-list-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.result-list-head strong,
.result-row-head strong {
  color: #22314a;
}

.result-list-head span,
.result-row-subtitle,
.result-row-meta,
.result-type,
.result-row-status {
  color: #5d6d89;
  font-size: 12px;
}

.result-list-body {
  display: grid;
  gap: 8px;
}

.result-row {
  display: grid;
  gap: 6px;
  padding: 10px 12px;
  border: 1px solid color-mix(in srgb, var(--blue) 14%, var(--line));
  border-radius: 14px;
  background: #fff;
  text-align: left;
}

.result-row.active {
  border-color: color-mix(in srgb, var(--blue) 34%, var(--line));
  box-shadow: 0 8px 20px color-mix(in srgb, var(--blue) 14%, transparent);
}

.result-row-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.result-type,
.result-row-status {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--blue-soft) 72%, white);
}

.result-row-status.inactive {
  background: color-mix(in srgb, #d7dee9 88%, white);
}

.detail-column {
  min-width: 0;
}

.outline-btn {
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  background: linear-gradient(180deg, #ffffff 0%, #f7f9fd 100%);
  color: #5b677d;
  padding: 8px 14px;
  min-height: 36px;
  font-weight: 700;
}

@media (max-width: 1080px) {
  .search-results-layout {
    grid-template-columns: 1fr;
  }

  .result-list-card {
    position: static;
    top: auto;
  }
}
</style>
