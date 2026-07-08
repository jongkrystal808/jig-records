<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";

import { api, fetchFixtureImageObjectUrl } from "@/api";
import { customers, onboardingActive, onboardingStepIndex, selectedCustomerId } from "@/appState";
import InlineSpinner from "@/components/common/InlineSpinner.vue";
import FixtureInfoPanel from "@/components/search/FixtureInfoPanel.vue";
import ModelInfoPanel from "@/components/search/ModelInfoPanel.vue";
import SearchHeroSection from "@/components/search/SearchHeroSection.vue";
import SearchResultPanel from "@/components/search/SearchResultPanel.vue";
import { authSession } from "@/appState";
import { pushToast } from "@/toastState";
import type {
  AppUser,
  Fixture,
  FixtureRequirementListItem,
  IdentifierStockSummary,
  MachineModel,
  MaterialTransaction,
  ModelQuery,
  Station,
  StockSummary
} from "@/types";
import { formatLocalDate } from "@/utils/date";
import { formatIdentifierStockTags } from "@/utils/display";
import { matchesFixtureKeywords, parseFixtureKeywords } from "@/utils/fixtureSearch";

type SearchMode = "fixture" | "model";
type DetailTab = "info" | "edit";
type SearchHint = {
  key: string;
  mode: SearchMode;
  entityId: number;
  title: string;
  subtitle: string;
  badge: string;
};

type RecentFixtureShortcut = {
  fixtureCode: string;
  transactionType: "receipt" | "return";
  occurredAt: string;
};

const MAX_RECENT_FIXTURE_SHORTCUTS = 20;
const MAX_FIXTURE_TRANSACTION_ROWS = 30;
const FULL_FIXTURE_TRANSACTION_HISTORY_LIMIT = 2000;

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
const nf = new Intl.NumberFormat("zh-TW");

const FIXTURE_SECTION_KEY = "search-fixture-sections";
const MODEL_SECTION_KEY = "search-model-sections";
const MODE_KEY = "search-mode";
const DETAIL_TAB_KEY = "search-detail-tab";

const defaultFixtureSections = ["summary", "image", "identifier", "transactions", "models", "stations"];
const defaultModelSections = ["summary", "stations", "fixtures", "requirements"];

const mode = ref<SearchMode>("fixture");
const detailTab = ref<DetailTab>("info");
const queryDraft = ref("");
const committedQuery = ref("");
const loading = ref(false);
const modelLoading = ref(false);
const customerUsers = ref<AppUser[]>([]);

const fixtures = ref<Fixture[]>([]);
const stockRows = ref<StockSummary[]>([]);
const transactions = ref<MaterialTransaction[]>([]);
const identifierStockRows = ref<IdentifierStockSummary[]>([]);
const models = ref<MachineModel[]>([]);
const stations = ref<Station[]>([]);
const fixtureRequirements = ref<FixtureRequirementListItem[]>([]);

const selectedFixtureId = ref<number | null>(null);
const selectedModelId = ref<number | null>(null);
const modelQuery = ref<ModelQuery | null>(null);
const selectedFixtureImage = ref("");
const imageLoadFailed = ref(false);
const resultPanel = ref<HTMLElement | null>(null);
const fixtureTransactionHistoryRows = ref<MaterialTransaction[]>([]);
const fixtureTransactionHistoryLoadedForCode = ref<string | null>(null);
const fixtureTransactionHistoryLoading = ref(false);

const fixtureSectionSelection = ref<string[]>(loadSelection(FIXTURE_SECTION_KEY, defaultFixtureSections));
const modelSectionSelection = ref<string[]>(loadSelection(MODEL_SECTION_KEY, defaultModelSections));

function startOnboarding(): void {
  if (!selectedCustomerId.value && customers.value.length > 0) {
    selectedCustomerId.value = customers.value[0].id;
  }
  onboardingStepIndex.value = 0;
  onboardingActive.value = true;
}

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

function formatCount(value: number): string {
  return nf.format(value);
}

function normalizeSearchText(value: string): string {
  return value.trim().toLowerCase();
}

function normalizeCodeToken(value: string): string {
  return normalizeSearchText(value).replace(/[^a-z0-9]/g, "");
}

function rankCodeMatch(code: string, query: string): number {
  const normalizedCode = normalizeCodeToken(code);
  const normalizedQuery = normalizeCodeToken(query);
  if (!normalizedQuery) return Number.MAX_SAFE_INTEGER;
  const startsWithScore = normalizedCode.startsWith(normalizedQuery) ? 0 : 1000;
  const containsIndex = normalizedCode.indexOf(normalizedQuery);
  const containsScore = containsIndex >= 0 ? containsIndex : 500;
  const lengthScore = Math.abs(normalizedCode.length - normalizedQuery.length);
  return startsWithScore + containsScore * 10 + lengthScore;
}

function stockTone(status: StockSummary["stock_status"] | undefined): "normal" | "warn" | "danger" | "muted" {
  if (status === "low_stock") return "warn";
  if (status === "out_of_stock") return "danger";
  if (status === "normal") return "normal";
  return "muted";
}

const customerId = computed(() => selectedCustomerId.value ?? undefined);
const canEdit = computed(() => authSession.value?.role !== "guest");
const hintSearchText = computed(() => queryDraft.value.trim().toLowerCase());
const resultSearchText = computed(() => committedQuery.value.trim().toLowerCase());
const hasActiveQuery = computed(() => committedQuery.value.trim().length > 0);
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
  () => mode.value === "fixture" && fixtureMatches.value.length === 0 && visibleFixtureSections.value.maintenance && detailTab.value === "edit" && canEdit.value
);
const shouldShowModelCreateForm = computed(
  () => mode.value === "model" && modelMatches.value.length === 0 && visibleModelSections.value.maintenance && detailTab.value === "edit" && canEdit.value
);

const fixtureSectionChips = computed(() =>
  [
    { key: "summary", label: "總覽" },
    { key: "image", label: "圖片" },
    { key: "identifier", label: "識別碼庫存" },
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

const fixtureMatches = computed(() =>
  fixtures.value
    .filter((row) => {
      const q = resultSearchText.value;
      return !q || [row.code, row.name, row.storage_location ?? ""].some((value) => value.toLowerCase().includes(q));
    })
    .slice()
    .sort((a, b) => a.code.localeCompare(b.code))
    .slice(0, 14)
);

const modelMatches = computed(() =>
  models.value
    .filter((row) => {
      const q = resultSearchText.value;
      return !q || [row.code, row.name].some((value) => value.toLowerCase().includes(q));
    })
    .slice()
    .sort((a, b) => a.code.localeCompare(b.code))
    .slice(0, 14)
);

const selectedFixture = computed(() => fixtures.value.find((row) => row.id === selectedFixtureId.value) ?? null);
const selectedFixtureStock = computed(() => stockRows.value.find((row) => row.fixture_id === selectedFixture.value?.id) ?? null);
const selectedModel = computed(() => models.value.find((row) => row.id === selectedModelId.value) ?? null);
const fixtureMap = computed(() => new Map(fixtures.value.map((row) => [row.id, row])));
const modelMap = computed(() => new Map(models.value.map((row) => [row.id, row])));
const hasConfirmedFixtureResult = computed(() => {
  const q = committedQuery.value.trim();
  if (!q || !selectedFixture.value) return false;
  return selectedFixture.value.code.toLowerCase() === q.toLowerCase() || selectedFixture.value.name.toLowerCase() === q.toLowerCase();
});
const hasConfirmedModelResult = computed(() => {
  const q = committedQuery.value.trim();
  if (!q || !selectedModel.value) return false;
  return selectedModel.value.code.toLowerCase() === q.toLowerCase() || selectedModel.value.name.toLowerCase() === q.toLowerCase();
});
const resultScrollKey = computed(() => {
  if (!hasActiveQuery.value) return "";
  if (mode.value === "fixture") {
    return fixtureMatches.value.length > 0 && selectedFixtureId.value ? `fixture-${selectedFixtureId.value}-${committedQuery.value.trim()}` : "";
  }
  return modelMatches.value.length > 0 && selectedModelId.value ? `model-${selectedModelId.value}-${committedQuery.value.trim()}` : "";
});

// Keep the page focused on search state and result data; hero/detail shells live in dedicated components.
const activeSectionKeys = computed(() => (mode.value === "fixture" ? fixtureSectionSelection.value : modelSectionSelection.value));
const currentSectionChips = computed(() => (mode.value === "fixture" ? fixtureSectionChips.value : modelSectionChips.value));
const shouldShowEmptyResultState = computed(
  () => (mode.value === "fixture" ? fixtureMatches.value : modelMatches.value).length === 0 && !shouldShowFixtureCreateForm.value && !shouldShowModelCreateForm.value
);

const identifierMap = computed(() => {
  const map = new Map<number, Map<string, number>>();
  for (const row of identifierStockRows.value) {
    const perFixture = map.get(row.fixture_id) ?? new Map<string, number>();
    perFixture.set(row.identifier, row.stock_qty);
    map.set(row.fixture_id, perFixture);
  }
  return map;
});

const selectedFixtureIdentifierTags = computed(() => {
  const fixtureId = selectedFixture.value?.id;
  if (!fixtureId) return [];
  const entry = identifierMap.value.get(fixtureId);
  if (!entry) return [];
  return formatIdentifierStockTags(entry.entries(), formatCount);
});

const selectedFixtureIdentifierTotalQty = computed(() => {
  const fixtureId = selectedFixture.value?.id;
  if (!fixtureId) return 0;
  const entry = identifierMap.value.get(fixtureId);
  if (!entry) return 0;
  let total = 0;
  for (const quantity of entry.values()) {
    total += quantity;
  }
  return total;
});

const selectedFixtureTransactions = computed(() => {
  if (fixtureTransactionHistoryLoadedForCode.value === selectedFixture.value?.code) {
    return fixtureTransactionHistoryRows.value;
  }
  return transactions.value.filter((tx) => tx.items.some((item) => item.fixture_id === selectedFixture.value?.id)).slice(0, MAX_FIXTURE_TRANSACTION_ROWS);
});

const selectedFixtureRequirementRows = computed(() =>
  fixtureRequirements.value
    .filter((row) => row.fixture_id === selectedFixture.value?.id)
    .slice()
    .sort((a, b) => a.model_code.localeCompare(b.model_code) || a.station_code.localeCompare(b.station_code))
);

const selectedFixtureStationRows = computed(() =>
  selectedFixtureRequirementRows.value.map((row) => ({
    model_code: row.model_code,
    station_code: row.station_code,
    station_name: stations.value.find((item) => item.id === row.station_id)?.name ?? "-",
    required_qty: row.required_qty
  }))
);

const selectedFixtureModels = computed(() => {
  const ids = new Set(selectedFixtureRequirementRows.value.map((row) => row.model_id));
  return models.value.filter((row) => ids.has(row.id)).slice().sort((a, b) => a.code.localeCompare(b.code));
});

const selectedModelFixtures = computed(() =>
  (modelQuery.value?.fixtures ?? []).map((row) => ({
    ...row,
    identifierTags: formatIdentifierStockTags(identifierMap.value.get(row.fixture_id)?.entries() ?? [], formatCount)
  }))
);

// Keep recent fixture shortcuts query-free so operators can jump back to the latest receiving/returning targets quickly.
// The hero previews 5 by default, but we keep a larger recent pool here so the UI can offer a "show more" action.
const recentFixtureShortcuts = computed<RecentFixtureShortcut[]>(() => {
  const seen = new Set<string>();
  const shortcuts: RecentFixtureShortcut[] = [];
  const sortedTransactions = transactions.value
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

const smartHints = computed(() => {
  const q = hintSearchText.value;
  if (!q) return [];
  if (mode.value === "fixture" && hasConfirmedFixtureResult.value && committedQuery.value.trim() === queryDraft.value.trim()) return [];
  if (mode.value === "model" && hasConfirmedModelResult.value && committedQuery.value.trim() === queryDraft.value.trim()) return [];

  if (mode.value === "fixture") {
    return fixtures.value
      .filter((row) => normalizeCodeToken(row.code).includes(normalizeCodeToken(q)))
      .slice()
      .sort((a, b) => {
        const scoreDiff = rankCodeMatch(a.code, q) - rankCodeMatch(b.code, q);
        if (scoreDiff !== 0) return scoreDiff;
        return a.code.localeCompare(b.code);
      })
      .slice(0, 10)
      .map((row): SearchHint => ({
        key: `fixture-direct-${row.id}`,
        mode: "fixture",
        entityId: row.id,
        title: row.code,
        subtitle: row.name,
        badge: "治具"
      }));
  }

  return models.value
    .filter((row) => normalizeCodeToken(row.code).includes(normalizeCodeToken(q)))
    .slice()
    .sort((a, b) => {
      const scoreDiff = rankCodeMatch(a.code, q) - rankCodeMatch(b.code, q);
      if (scoreDiff !== 0) return scoreDiff;
      return a.code.localeCompare(b.code);
    })
    .slice(0, 10)
    .map((row): SearchHint => ({
        key: `model-direct-${row.id}`,
        mode: "model",
        entityId: row.id,
        title: row.code,
        subtitle: row.name,
        badge: "機種"
    }));
});

function applySmartHint(hint: SearchHint): void {
  mode.value = hint.mode;
  queryDraft.value = hint.title;
  committedQuery.value = hint.title;
  if (hint.mode === "fixture") {
    selectedFixtureId.value = hint.entityId;
    detailTab.value = "info";
    return;
  }
  selectedModelId.value = hint.entityId;
  detailTab.value = "info";
}

function applyRecentFixtureShortcut(fixtureCode: string): void {
  mode.value = "fixture";
  queryDraft.value = fixtureCode;
  committedQuery.value = fixtureCode;
  detailTab.value = "info";
  const matchedFixture = fixtures.value.find((row) => row.code === fixtureCode);
  selectedFixtureId.value = matchedFixture?.id ?? null;
}

async function loadSelectedFixtureTransactionHistory(): Promise<void> {
  const fixture = selectedFixture.value;
  if (!fixture || !customerId.value || fixtureTransactionHistoryLoading.value) {
    return;
  }
  if (fixtureTransactionHistoryLoadedForCode.value === fixture.code) {
    return;
  }

  fixtureTransactionHistoryLoading.value = true;
  try {
    fixtureTransactionHistoryRows.value = await api.listTransactions(FULL_FIXTURE_TRANSACTION_HISTORY_LIMIT, customerId.value, {
      fixture_code: fixture.code
    });
    fixtureTransactionHistoryLoadedForCode.value = fixture.code;
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "載入治具歷史收退料記錄失敗。", "error");
  } finally {
    fixtureTransactionHistoryLoading.value = false;
  }
}

function syncSelection(): void {
  if (mode.value === "fixture") {
    selectedFixtureId.value = fixtureMatches.value.find((row) => row.id === selectedFixtureId.value)?.id ?? fixtureMatches.value[0]?.id ?? null;
    return;
  }
  selectedModelId.value = modelMatches.value.find((row) => row.id === selectedModelId.value)?.id ?? modelMatches.value[0]?.id ?? null;
}

function submitSearch(): void {
  const nextQuery = queryDraft.value.trim();
  committedQuery.value = nextQuery;
  detailTab.value = "info";
  syncSelection();
}

function clearSearch(): void {
  queryDraft.value = "";
  committedQuery.value = "";
  detailTab.value = "info";
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

function clearSelectedFixtureImage(): void {
  if (selectedFixtureImage.value) {
    URL.revokeObjectURL(selectedFixtureImage.value);
    selectedFixtureImage.value = "";
  }
}

async function refreshSelectedFixtureImage(): Promise<void> {
  clearSelectedFixtureImage();
  imageLoadFailed.value = false;
  if (!selectedFixture.value) {
    return;
  }
  try {
    selectedFixtureImage.value = await fetchFixtureImageObjectUrl(selectedFixture.value.code);
  } catch {
    imageLoadFailed.value = true;
  }
}

async function loadWorkspace(): Promise<void> {
  loading.value = true;
  try {
    const [fixtureRows, stock, txRows, identifierRows, modelRows, stationRows, requirementRows, assignedUsers] = await Promise.all([
      api.listFixtures(customerId.value),
      api.listStock(customerId.value),
      api.listTransactions(200, customerId.value),
      api.listIdentifierStockSummary(customerId.value),
      api.listModels(customerId.value),
      api.listStations(customerId.value),
      api.listFixtureRequirements(customerId.value),
      customerId.value ? api.listCustomerUsers(customerId.value) : Promise.resolve([])
    ]);
    fixtures.value = fixtureRows;
    stockRows.value = stock;
    transactions.value = txRows;
    identifierStockRows.value = identifierRows;
    models.value = modelRows;
    stations.value = stationRows;
    fixtureRequirements.value = requirementRows;
    customerUsers.value = assignedUsers;
    syncSelection();
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "載入查詢頁失敗", "error");
  } finally {
    loading.value = false;
  }
}

async function refreshModelQuery(): Promise<void> {
  if (!selectedModelId.value) {
    modelQuery.value = null;
    return;
  }
  modelLoading.value = true;
  try {
    modelQuery.value = await api.getModelQuery(selectedModelId.value, undefined, customerId.value);
  } catch (err) {
    modelQuery.value = null;
    pushToast(err instanceof Error ? err.message : "載入機種資料失敗", "error");
  } finally {
    modelLoading.value = false;
  }
}

function goCreateFromNoResult(): void {
  if (!canEdit.value) {
    return;
  }
  const selection = mode.value === "fixture" ? fixtureSectionSelection : modelSectionSelection;
  if (!selection.value.includes("maintenance")) {
    selection.value = [...selection.value, "maintenance"];
  }
  detailTab.value = "edit";
}

function goToProduction(): void {
  if (!selectedModel.value) {
    return;
  }
  void router.push({
    name: "production",
    query: { model_id: String(selectedModel.value.id) }
  });
}

async function handleFixtureSaved(fixtureId: number): Promise<void> {
  await loadWorkspace();
  selectedFixtureId.value = fixtureId;
  detailTab.value = "info";
  await refreshSelectedFixtureImage();
  pushToast("治具資料已更新。", "success");
}

async function handleModelSaved(modelId: number): Promise<void> {
  await loadWorkspace();
  selectedModelId.value = modelId;
  detailTab.value = "info";
  await refreshModelQuery();
  pushToast("機種資料已更新。", "success");
}

function scrollToResultPanel(): void {
  void nextTick(() => {
    resultPanel.value?.scrollIntoView({
      behavior: "smooth",
      block: "start"
    });
  });
}

watch(mode, () => {
  syncSelection();
  if (mode.value === "fixture" && !visibleFixtureSections.value.maintenance && detailTab.value === "edit") {
    detailTab.value = "info";
  }
  if (mode.value === "model" && !visibleModelSections.value.maintenance && detailTab.value === "edit") {
    detailTab.value = "info";
  }
  persistSelections();
});

watch([fixtureSectionSelection, modelSectionSelection, detailTab], persistSelections, { deep: true });
watch(resultSearchText, syncSelection);
watch(queryDraft, (value) => {
  if (value.trim().length === 0 && committedQuery.value.length > 0) {
    committedQuery.value = "";
  }
});
watch(resultScrollKey, (key, previous) => {
  if (!key || key === previous) {
    return;
  }
  scrollToResultPanel();
});
watch(selectedFixtureId, () => {
  fixtureTransactionHistoryRows.value = [];
  fixtureTransactionHistoryLoadedForCode.value = null;
  fixtureTransactionHistoryLoading.value = false;
  void refreshSelectedFixtureImage();
});
watch(selectedModelId, async () => {
  await refreshModelQuery();
});
watch(selectedCustomerId, async () => {
  await loadWorkspace();
  await Promise.all([refreshModelQuery(), refreshSelectedFixtureImage()]);
});

onMounted(async () => {
  const savedMode = localStorage.getItem(MODE_KEY);
  if (savedMode === "fixture" || savedMode === "model") {
    mode.value = savedMode;
  }
  const savedDetailTab = localStorage.getItem(DETAIL_TAB_KEY);
  if (savedDetailTab === "info" || savedDetailTab === "edit") {
    detailTab.value = savedDetailTab;
  }

  await loadWorkspace();
  await Promise.all([refreshModelQuery(), refreshSelectedFixtureImage()]);
});

onBeforeUnmount(() => {
  clearSelectedFixtureImage();
});
</script>

<template>
  <div class="search-shell" :class="{ idle: !hasActiveQuery }">
    <SearchHeroSection
      :mode="mode"
      :query-draft="queryDraft"
      :has-active-query="hasActiveQuery"
      :smart-hints="smartHints"
      :recent-fixture-shortcuts="recentFixtureShortcuts"
      :section-chips="currentSectionChips"
      :active-section-keys="activeSectionKeys"
      @update:mode="mode = $event"
      @update:query-draft="queryDraft = $event"
      @submit="submitSearch"
      @clear="clearSearch"
      @apply-hint="applySmartHint"
      @apply-recent-fixture-shortcut="applyRecentFixtureShortcut"
      @toggle-section="toggleSection"
      @onboarding="startOnboarding"
    />

    <section v-if="hasActiveQuery" ref="resultPanel" class="content-grid">
      <SearchResultPanel
        :can-edit="canEdit"
        :show-maintenance-tab="mode === 'fixture' ? visibleFixtureSections.maintenance : visibleModelSections.maintenance"
        :detail-tab="detailTab"
        :loading="loading"
        :empty="shouldShowEmptyResultState"
        :mode="mode"
        @update:detail-tab="detailTab = $event"
        @create="goCreateFromNoResult"
      >
        <template v-if="mode === 'fixture'">
          <FixtureInfoPanel
            v-if="(detailTab === 'info' || !visibleFixtureSections.maintenance) && !shouldShowFixtureCreateForm"
            :fixture="selectedFixture"
            :stock="selectedFixtureStock"
            :image-url="selectedFixtureImage"
            :image-load-failed="imageLoadFailed"
            :identifier-tags="selectedFixtureIdentifierTags"
            :identifier-total-qty="selectedFixtureIdentifierTotalQty"
            :related-models="selectedFixtureModels"
            :station-rows="selectedFixtureStationRows"
            :transactions="selectedFixtureTransactions"
            :transaction-history-loaded="fixtureTransactionHistoryLoadedForCode === selectedFixture?.code"
            :transaction-history-loading="fixtureTransactionHistoryLoading"
            :visible-sections="visibleFixtureSections"
            :format-count="formatCount"
            :format-date="formatLocalDate"
            :stock-tone="stockTone"
            @load-transaction-history="loadSelectedFixtureTransactionHistory"
          />
          <FixtureEditForm
            v-else
            :customer-id="customerId"
            :fixture="selectedFixture"
            :assigned-users="customerUsers"
            :initial-code="queryDraft.trim().toUpperCase()"
            @saved="handleFixtureSaved"
            @cancel="detailTab = 'info'"
          />
        </template>

        <template v-else>
          <div v-if="modelLoading && detailTab === 'info' && !shouldShowModelCreateForm" class="loading-panel">
            <InlineSpinner label="載入機種資料..." />
          </div>
          <ModelInfoPanel
            v-else-if="(detailTab === 'info' || !visibleModelSections.maintenance) && !shouldShowModelCreateForm"
            :model="selectedModel"
            :query-data="modelQuery"
            :fixtures="selectedModelFixtures"
            :visible-sections="visibleModelSections"
            :format-count="formatCount"
            :go-to-production="goToProduction"
          />
          <ModelEditForm
            v-else
            :customer-id="customerId"
            :model="selectedModel"
            :initial-code="queryDraft.trim().toUpperCase()"
            @saved="handleModelSaved"
            @cancel="detailTab = 'info'"
          />
        </template>
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
  min-height: calc(100dvh - 210px);
  align-content: center;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  min-height: 0;
  align-items: start;
  scroll-margin-top: 96px;
}

.content-grid.idle {
  width: min(760px, 100%);
  justify-self: center;
}

.collapsed-state {
  display: grid;
  gap: 8px;
  padding: 28px 20px;
  border: 1px dashed var(--line-strong);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.78);
  color: #5d6d89;
  text-align: center;
}

.collapsed-state strong {
  color: #22314a;
  font-size: 15px;
}

@media (max-width: 960px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}
</style>
