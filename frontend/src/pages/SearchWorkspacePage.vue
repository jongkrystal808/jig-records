<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";

import { api, fetchFixtureImageObjectUrl } from "@/api";
import { customers, onboardingActive, onboardingStepIndex, selectedCustomerId } from "@/appState";
import InlineSpinner from "@/components/common/InlineSpinner.vue";
import FixtureInfoPanel from "@/components/search/FixtureInfoPanel.vue";
import ModelInfoPanel from "@/components/search/ModelInfoPanel.vue";
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
  return [...entry.entries()]
    .sort((a, b) => a[0].localeCompare(b[0], "zh-TW", { numeric: true }))
    .map(([identifier, quantity]) => `${identifier}（${formatCount(quantity)}）`);
});

const selectedFixtureTransactions = computed(() =>
  transactions.value.filter((tx) => tx.items.some((item) => item.fixture_id === selectedFixture.value?.id)).slice(0, 8)
);

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
    identifierTags: [...(identifierMap.value.get(row.fixture_id)?.entries() ?? [])]
      .sort((a, b) => a[0].localeCompare(b[0], "zh-TW", { numeric: true }))
      .map(([identifier, quantity]) => `${identifier}（${formatCount(quantity)}）`)
  }))
);

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
    <section class="hero-card" :class="{ idle: !hasActiveQuery }">
      <div class="hero-copy">
        <span class="eyebrow">Search Workspace</span>
        <h1>治具 / 機種查詢</h1>
      </div>

      <div class="search-toolbar">
        <div class="mode-switch" data-tour="search-mode-switch">
          <button class="mode-btn" :class="{ active: mode === 'fixture' }" type="button" @click="mode = 'fixture'">治具</button>
          <button class="mode-btn" :class="{ active: mode === 'model' }" type="button" @click="mode = 'model'">機種</button>
        </div>
        <label class="query-field" data-tour="search-query-field">
          <input
            v-model="queryDraft"
            :placeholder="mode === 'fixture' ? '請輸入治具編號 / 名稱,例如 C-00003' : '請輸入機種編號 / 名稱,例如 VPort-254'"
            autocomplete="off"
            spellcheck="false"
            @keydown.enter.prevent="submitSearch"
            @keydown.esc.prevent="clearSearch"
          />
        </label>
      </div>

      <div v-if="smartHints.length > 0" class="smart-hint-panel">
        <div class="smart-hint-head">
          <strong>相近編號</strong>
          <span>{{ smartHints.length }} 筆</span>
        </div>
        <div class="smart-hint-grid">
          <button
            v-for="hint in smartHints"
            :key="hint.key"
            class="smart-hint-card"
            type="button"
            @click="applySmartHint(hint)"
          >
            <span class="smart-hint-badge">{{ hint.badge }}</span>
            <strong>{{ hint.title }}</strong>
            <span>{{ hint.subtitle }}</span>
          </button>
        </div>
      </div>

      <div class="chip-row" data-tour="search-section-chips">
        <button
          v-for="chip in mode === 'fixture' ? fixtureSectionChips : modelSectionChips"
          :key="`${mode}-${chip.key}`"
          class="chip-toggle"
          :class="{ active: mode === 'fixture' ? fixtureSectionSelection.includes(chip.key) : modelSectionSelection.includes(chip.key) }"
          type="button"
          @click="toggleSection(mode, chip.key)"
        >
          {{ chip.label }}
        </button>
      </div>

    </section>

    <button class="floating-onboarding-btn" data-tour="search-onboarding-entry" type="button" @click="startOnboarding">開始新手教學</button>

    <section v-if="hasActiveQuery" ref="resultPanel" class="content-grid">
      <article class="detail-panel">
        <div v-if="(mode === 'fixture' ? visibleFixtureSections.maintenance : visibleModelSections.maintenance) && canEdit" class="detail-panel-tabs">
          <button class="detail-panel-tab" :class="{ active: detailTab === 'info' }" type="button" @click="detailTab = 'info'">資訊</button>
          <button class="detail-panel-tab" :class="{ active: detailTab === 'edit' }" type="button" @click="detailTab = 'edit'">編輯</button>
        </div>

        <div v-if="loading" class="loading-panel">
          <InlineSpinner label="載入查詢資料..." />
        </div>

        <div
          v-else-if="(mode === 'fixture' ? fixtureMatches : modelMatches).length === 0 && !shouldShowFixtureCreateForm && !shouldShowModelCreateForm"
          class="empty-state detail-empty-state"
        >
          <strong>找不到符合條件的資料</strong>
          <span>請調整搜尋條件，或直接建立新的 {{ mode === "fixture" ? "治具" : "機種" }}。</span>
          <button v-if="canEdit" class="outline-btn empty-action" type="button" @click="goCreateFromNoResult">找不到，新增一筆？</button>
        </div>

        <template v-else-if="mode === 'fixture'">
          <FixtureInfoPanel
            v-if="(detailTab === 'info' || !visibleFixtureSections.maintenance) && !shouldShowFixtureCreateForm"
            :fixture="selectedFixture"
            :stock="selectedFixtureStock"
            :image-url="selectedFixtureImage"
            :image-load-failed="imageLoadFailed"
            :identifier-tags="selectedFixtureIdentifierTags"
            :related-models="selectedFixtureModels"
            :station-rows="selectedFixtureStationRows"
            :transactions="selectedFixtureTransactions"
            :visible-sections="visibleFixtureSections"
            :format-count="formatCount"
            :format-date="formatLocalDate"
            :stock-tone="stockTone"
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
      </article>
    </section>
  </div>
</template>

<style scoped>
.search-shell {
  display: grid;
  gap: 12px;
  min-height: 100%;
  align-content: start;
}

.search-shell.idle {
  min-height: calc(100dvh - 210px);
  align-content: center;
}

.hero-card,
.detail-panel {
  border: 1px solid var(--line);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: var(--shadow);
}

.hero-card {
  display: grid;
  gap: 12px;
  padding: 14px;
  background:
    radial-gradient(circle at top left, rgba(47, 110, 229, 0.09), transparent 28%),
    linear-gradient(180deg, #ffffff 0%, #f6f9ff 100%);
}

.hero-card.idle {
  justify-items: center;
  text-align: center;
  padding: 28px 22px 24px;
}

.hero-card.idle .hero-copy,
.hero-card.idle .search-toolbar,
.hero-card.idle .smart-hint-panel,
.hero-card.idle .chip-row {
  width: min(760px, 100%);
}

.hero-card.idle .mode-switch,
.hero-card.idle .chip-row {
  justify-content: center;
}

.eyebrow {
  color: #2f6ee5;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h1,
h2 {
  margin: 0;
  color: #22314a;
}

h1 {
  margin-top: 4px;
  font-size: 24px;
}

.hero-copy p,
.panel-head p {
  margin: 4px 0 0;
  color: #5d6d89;
  font-size: 12px;
}

.search-toolbar {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 12px;
}

.floating-onboarding-btn {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 25;
  min-height: 42px;
  padding: 10px 16px;
  border: 1px solid #c8d8f4;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 16px 32px rgba(28, 47, 84, 0.18);
  color: #244578;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
  backdrop-filter: blur(10px);
}

.floating-onboarding-btn:hover {
  border-color: #9eb8ea;
  transform: translateY(-1px);
}

.hero-card.idle .search-toolbar {
  align-items: end;
}

.mode-switch {
  display: inline-flex;
  gap: 4px;
  padding: 4px;
  border: 1px solid #d7e2f5;
  border-radius: 999px;
  background: #f5f9ff;
}

.mode-btn {
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: #5b677d;
  padding: 8px 14px;
  min-height: 36px;
  font-weight: 800;
}

.mode-btn.active {
  background: #fff;
  color: #2f6ee5;
  box-shadow: 0 6px 16px rgba(47, 110, 229, 0.12);
}

.query-field {
  display: grid;
  gap: 6px;
}

.query-field span {
  color: #56657f;
  font-size: 12px;
  font-weight: 700;
}

input {
  width: 100%;
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  padding: 9px 10px;
  background: #fff;
  font: inherit;
}

.chip-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.smart-hint-panel {
  display: grid;
  gap: 10px;
  padding: 12px;
  border: 1px solid #dce5f3;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(245, 249, 255, 0.96) 100%);
}

.smart-hint-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.smart-hint-head strong {
  color: #22314a;
  font-size: 13px;
}

.smart-hint-head span,
.smart-hint-card span {
  color: #5d6d89;
  font-size: 12px;
}

.smart-hint-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 8px;
}

.smart-hint-card {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border: 1px solid #d7e2f5;
  border-radius: 14px;
  background: #fff;
  text-align: left;
}

.smart-hint-card strong {
  color: #22314a;
  font-size: 14px;
}

.smart-hint-badge {
  width: fit-content;
  padding: 2px 8px;
  border: 1px solid #d7e2f5;
  border-radius: 999px;
  background: #f7faff;
  color: #35527d !important;
  font-size: 11px !important;
  font-weight: 700;
}

.chip-toggle {
  border: 1px solid #d7e2f5;
  border-radius: 999px;
  background: #f7faff;
  color: #35527d;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 700;
}

.chip-toggle.active {
  border-color: rgba(47, 110, 229, 0.26);
  background: #eef5ff;
  color: #2f6ee5;
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

.detail-panel {
  min-height: 0;
  padding: 12px;
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

.detail-panel {
  display: grid;
  align-content: start;
  gap: 14px;
  position: sticky;
  top: 12px;
}

.detail-panel-tabs {
  display: inline-flex;
  align-items: center;
  gap: 0;
  width: fit-content;
  border: 1px solid #d7e2f5;
  border-radius: 12px;
  background: #f7faff;
  overflow: hidden;
}

.detail-panel-tab {
  border: 0;
  background: transparent;
  color: #5c6a81;
  padding: 10px 18px;
  font-size: 13px;
  font-weight: 800;
}

.detail-panel-tab + .detail-panel-tab {
  border-left: 1px solid #d7e2f5;
}

.detail-panel-tab.active {
  background: #eef5ff;
  color: #2f6ee5;
}

.empty-state {
  color: #5d6d89;
  font-size: 12px;
}

.empty-state {
  display: grid;
  gap: 10px;
  padding: 18px;
  border: 1px dashed var(--line-strong);
  border-radius: 14px;
  background: #fafcff;
}

.empty-action {
  width: fit-content;
}

.detail-empty-state {
  min-height: 280px;
  place-content: center;
}

.loading-panel {
  min-height: 180px;
  display: grid;
  place-items: center;
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

@media (max-width: 960px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .detail-panel {
    position: static;
    top: auto;
  }

  .search-toolbar {
    grid-template-columns: 1fr;
  }

  .floating-onboarding-btn {
    right: 14px;
    bottom: 14px;
    padding: 10px 14px;
    font-size: 12px;
  }
}
</style>
