<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

import { api, fetchFixtureImageObjectUrl } from "@/api";
import { selectedCustomerId } from "@/appState";
import { pushToast } from "@/toastState";
import type {
  Fixture,
  FixtureRequirementListItem,
  MachineModel,
  MaterialTransaction,
  ModelQuery,
  ModelQueryStationRequirement,
  Station,
  StockSummary
} from "@/types";
import { fallbackText, stockStatusLabel } from "@/utils/display";
import UiStatusPill from "@/components/UiStatusPill.vue";

type SearchMode = "fixture" | "model";

const nf = new Intl.NumberFormat("zh-TW");
const df = new Intl.DateTimeFormat("zh-TW", { dateStyle: "medium", timeStyle: "short", hour12: false });

const mode = ref<SearchMode>("fixture");
const query = ref("");
const loading = ref(false);
const modelLoading = ref(false);

const fixtures = ref<Fixture[]>([]);
const stockRows = ref<StockSummary[]>([]);
const transactions = ref<MaterialTransaction[]>([]);
const models = ref<MachineModel[]>([]);
const stations = ref<Station[]>([]);
const fixtureRequirements = ref<FixtureRequirementListItem[]>([]);

const selectedFixtureId = ref<number | null>(null);
const selectedModelId = ref<number | null>(null);
const modelQuery = ref<ModelQuery | null>(null);
const imageLoadFailed = ref(false);
const selectedFixtureImage = ref("");
const showFixtureStationDetail = ref(false);
const showModelStationDetail = ref(false);

function formatCount(value: number): string {
  return nf.format(value);
}

function formatDateTime(value: string | null | undefined): string {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "-" : df.format(date);
}

function modeLabel(value: SearchMode): string {
  return value === "fixture" ? "治具" : "機種";
}

function stockTone(status: StockSummary["stock_status"] | undefined): "normal" | "warn" | "danger" | "muted" {
  if (status === "low_stock") return "warn";
  if (status === "out_of_stock") return "danger";
  if (status === "normal") return "normal";
  return "muted";
}

const customerId = computed(() => selectedCustomerId.value ?? undefined);
const searchText = computed(() => query.value.trim().toLowerCase());

const fixtureMatches = computed(() =>
  fixtures.value
    .filter((row) => {
      const q = searchText.value;
      return !q || [row.code, row.name, row.storage_location ?? ""].some((value) => value.toLowerCase().includes(q));
    })
    .slice()
    .sort((a, b) => a.code.localeCompare(b.code))
    .slice(0, 12)
);

const modelMatches = computed(() =>
  models.value
    .filter((row) => {
      const q = searchText.value;
      return !q || [row.code, row.name].some((value) => value.toLowerCase().includes(q));
    })
    .slice()
    .sort((a, b) => a.code.localeCompare(b.code))
    .slice(0, 12)
);

const selectedFixture = computed(() => fixtures.value.find((row) => row.id === selectedFixtureId.value) ?? null);
const selectedFixtureStock = computed(() => stockRows.value.find((row) => row.fixture_id === selectedFixture.value?.id) ?? null);
const selectedFixtureTransactions = computed(() =>
  transactions.value.filter((tx) => tx.items.some((item) => item.fixture_id === selectedFixture.value?.id)).slice(0, 8)
);
const selectedFixtureRequirementRows = computed(() =>
  fixtureRequirements.value
    .filter((row) => row.fixture_id === selectedFixture.value?.id)
    .slice()
    .sort((a, b) => {
      const modelCompare = a.model_code.localeCompare(b.model_code);
      if (modelCompare !== 0) return modelCompare;
      return a.station_code.localeCompare(b.station_code);
    })
);
const selectedFixtureStationRows = computed(() =>
  selectedFixtureRequirementRows.value.map((row) => {
    const station = stations.value.find((item) => item.id === row.station_id);
    const model = models.value.find((item) => item.id === row.model_id);
    return {
      model_id: row.model_id,
      model_code: row.model_code || model?.code || `機種 ${row.model_id}`,
      station_id: row.station_id,
      station_code: row.station_code || station?.code || `站點 ${row.station_id}`,
      station_name: station?.name || "-",
      required_qty: row.required_qty
    };
  })
);
const selectedFixtureModelRows = computed(() => {
  const modelIds = new Set(selectedFixtureRequirementRows.value.map((row) => row.model_id));
  return models.value.filter((row) => modelIds.has(row.id)).slice().sort((a, b) => a.code.localeCompare(b.code));
});
const selectedFixtureStationCount = computed(() => new Set(selectedFixtureRequirementRows.value.map((row) => row.station_id)).size);

const selectedModel = computed(() => models.value.find((row) => row.id === selectedModelId.value) ?? null);
const selectedModelFixtures = computed(() => modelQuery.value?.fixtures ?? []);
const selectedModelStations = computed(() => modelQuery.value?.stations ?? []);
const selectedModelGroups = computed(() => {
  const query = modelQuery.value;
  if (!query) return [];
  const stationMap = new Map(query.stations.map((row) => [row.station_id, row]));
  const groups = new Map<number, { station_id: number; station_code: string; station_name: string; max_open_station_count: number; rows: ModelQueryStationRequirement[] }>();
  for (const row of query.station_requirements) {
    const station = stationMap.get(row.station_id);
    const group = groups.get(row.station_id) ?? {
      station_id: row.station_id,
      station_code: station?.station_code || row.station_code,
      station_name: station?.station_name || "-",
      max_open_station_count: station?.max_open_station_count ?? row.max_open_station_count,
      rows: []
    };
    group.rows.push(row);
    groups.set(row.station_id, group);
  }
  return [...groups.values()]
    .map((group) => ({ ...group, rows: group.rows.slice().sort((a, b) => a.fixture_code.localeCompare(b.fixture_code)) }))
    .sort((a, b) => a.station_code.localeCompare(b.station_code));
});

const statsCards = computed(() => [
  {
    label: "治具種類總數",
    value: `共有 ${formatCount(fixtures.value.length)}`,
    meta: `已啟用 ${formatCount(fixtures.value.filter((row) => row.is_active).length)}`,
    tone: "blue"
  },
  { label: "治具總數", value: formatCount(stockRows.value.reduce((sum, row) => sum + row.stock_qty, 0)), meta: "", tone: "green" },
  { label: "機種 / 站點總數", value: `${formatCount(models.value.length)} / ${formatCount(stations.value.length)}`, meta: "", tone: "orange" }
]);

function syncSelection(): void {
  if (mode.value === "fixture") {
    if (fixtureMatches.value.length === 0) {
      selectedFixtureId.value = null;
      return;
    }
    if (!fixtureMatches.value.some((row) => row.id === selectedFixtureId.value)) {
      selectedFixtureId.value = fixtureMatches.value[0].id;
      imageLoadFailed.value = false;
    }
    return;
  }

  if (modelMatches.value.length === 0) {
    selectedModelId.value = null;
    modelQuery.value = null;
    return;
  }
  if (!modelMatches.value.some((row) => row.id === selectedModelId.value)) {
    selectedModelId.value = modelMatches.value[0].id;
  }
}

async function loadWorkspace(): Promise<void> {
  loading.value = true;
  try {
    const [fixtureRows, stock, txRows, modelRows, stationRows, requirementRows] = await Promise.all([
      api.listFixtures(customerId.value),
      api.listStock(customerId.value),
      api.listTransactions(200, customerId.value),
      api.listModels(customerId.value),
      api.listStations(customerId.value),
      api.listFixtureRequirements(customerId.value)
    ]);

    fixtures.value = fixtureRows;
    stockRows.value = stock;
    transactions.value = txRows;
    models.value = modelRows;
    stations.value = stationRows;
    fixtureRequirements.value = requirementRows;
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
    pushToast(err instanceof Error ? err.message : "載入機種查詢失敗", "error");
  } finally {
    modelLoading.value = false;
  }
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

function doSearch(): void {
  if (!query.value.trim()) {
    syncSelection();
    return;
  }
  if (mode.value === "fixture" && fixtureMatches.value.length === 0) {
    pushToast("找不到符合的治具。", "warning");
    return;
  }
  if (mode.value === "model" && modelMatches.value.length === 0) {
    pushToast("找不到符合的機種。", "warning");
    return;
  }
  syncSelection();
}

function resetSearch(): void {
  query.value = "";
  syncSelection();
}

watch(mode, () => {
  showFixtureStationDetail.value = false;
  showModelStationDetail.value = false;
  syncSelection();
});

watch(searchText, () => {
  syncSelection();
});

watch(selectedFixtureId, () => {
  void refreshSelectedFixtureImage();
});

watch(selectedModelId, async () => {
  await refreshModelQuery();
});

watch(selectedCustomerId, async () => {
  await loadWorkspace();
  await refreshModelQuery();
  await refreshSelectedFixtureImage();
});

onMounted(async () => {
  await loadWorkspace();
  await refreshModelQuery();
  await refreshSelectedFixtureImage();
});

onBeforeUnmount(() => {
  clearSelectedFixtureImage();
});
</script>

<template>
  <div class="search-shell">
    <section class="hero-summary">
      <div class="page-hero">
        <div class="hero-copy">
          <span class="eyebrow">Search Workspace</span>
          <h1>查詢頁</h1>
        </div>
      </div>

      <div class="stats-strip">
        <article v-for="card in statsCards" :key="card.label" class="stat-card" :class="card.tone">
          <span>{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
          <p v-if="card.meta">{{ card.meta }}</p>
        </article>
      </div>
    </section>

    <section class="search-grid">
      <article class="search-panel">
        <div class="panel-head">
          <div>
            <span class="eyebrow">Search Controls</span>
            <h2>搜尋控制</h2>
          </div>
        </div>

        <div class="mode-switch">
          <button class="mode-btn" :class="{ active: mode === 'fixture' }" type="button" @click="mode = 'fixture'">治具</button>
          <button class="mode-btn" :class="{ active: mode === 'model' }" type="button" @click="mode = 'model'">機種</button>
        </div>

        <form class="search-form" @submit.prevent="doSearch">
          <label>
            <span>{{ mode === "fixture" ? "治具編號 / 名稱" : "機種編號 / 名稱" }}</span>
            <input v-model="query" :placeholder="mode === 'fixture' ? '例如 C-00003…' : '例如 VPort-254…'" name="query" autocomplete="off" spellcheck="false" />
          </label>
          <div class="search-actions">
            <button class="outline-btn" type="button" @click="resetSearch">清空</button>
            <button class="primary-btn" type="submit" :disabled="loading">{{ loading ? "載入中…" : "查詢" }}</button>
          </div>
        </form>

        <div class="result-summary">
          <span>模式：{{ modeLabel(mode) }}</span>
          <span>{{ mode === "fixture" ? fixtureMatches.length : modelMatches.length }} 筆結果</span>
          <span v-if="mode === 'fixture' && selectedFixture">{{ selectedFixture.code }}</span>
          <span v-if="mode === 'model' && selectedModel">{{ selectedModel.code }}</span>
        </div>

        <div class="result-list">
          <button
            v-for="row in mode === 'fixture' ? fixtureMatches : modelMatches"
            :key="row.id"
            type="button"
            class="result-card"
            :class="{ active: (mode === 'fixture' ? row.id === selectedFixtureId : row.id === selectedModelId) }"
            @click="mode === 'fixture' ? (selectedFixtureId = row.id) : (selectedModelId = row.id)"
          >
            <div class="result-card-main">
              <strong>{{ row.code }}</strong>
              <span>{{ row.name }}</span>
            </div>
            <div class="result-card-meta">
              <UiStatusPill
                v-if="mode === 'fixture'"
                :label="stockStatusLabel((stockRows.find((item) => item.fixture_id === row.id)?.stock_status) ?? 'normal')"
                :tone="stockTone(stockRows.find((item) => item.fixture_id === row.id)?.stock_status)"
              />
              <span v-else class="result-tag">機種</span>
              <span v-if="mode === 'fixture'">{{ formatCount(stockRows.find((item) => item.fixture_id === row.id)?.stock_qty ?? 0) }} pcs</span>
            </div>
          </button>
          <div v-if="(mode === 'fixture' ? fixtureMatches : modelMatches).length === 0" class="empty-state">沒有符合條件的資料</div>
        </div>
      </article>

      <article class="search-panel">
        <template v-if="mode === 'fixture'">
          <div class="detail-head">
            <div class="fixture-head-copy">
              <span class="eyebrow">治具查詢</span>
              <div class="fixture-head-line">
                <h2>{{ selectedFixture?.code || "尚未選擇治具" }}</h2>
                <span class="fixture-name-chip">{{ selectedFixture?.name || "請先搜尋或點選左側結果" }}</span>
              </div>
            </div>
            <UiStatusPill :label="stockStatusLabel(selectedFixtureStock?.stock_status ?? 'normal')" :tone="stockTone(selectedFixtureStock?.stock_status)" />
          </div>

          <div class="fixture-hero">
            <div class="fixture-image">
              <img
                v-if="selectedFixtureImage"
                :src="selectedFixtureImage"
                :alt="`${selectedFixture?.code || '治具'} 圖片`"
                loading="lazy"
                @error="imageLoadFailed = true"
              />
              <div v-else class="image-placeholder">沒有圖片時顯示這裡</div>
            </div>
            <div class="fixture-metrics">
              <article class="metric-card"><span>治具庫存總量</span><strong>{{ formatCount(selectedFixtureStock?.stock_qty ?? 0) }}</strong><small>pcs 庫存</small></article>
              <article class="metric-card"><span>最低水位</span><strong>{{ formatCount(selectedFixtureStock?.min_stock_qty ?? 0) }}</strong><small>警戒門檻</small></article>
              <article class="metric-card"><span>儲位</span><strong>{{ fallbackText(selectedFixture?.storage_location) }}</strong><small>存放位置</small></article>
            </div>
          </div>

          <section class="info-block">
            <div class="block-head"><h3>收退料記錄</h3><span>{{ selectedFixtureTransactions.length }} 筆</span></div>
            <table class="query-table">
              <thead>
                <tr><th>類型</th><th>單號</th><th>識別碼</th><th>數量</th><th>日期</th></tr>
              </thead>
              <tbody>
                <tr v-for="tx in selectedFixtureTransactions" :key="tx.id">
                  <td>{{ tx.transaction_type === "receipt" ? "收料" : "退料" }}</td>
                  <td>{{ tx.transaction_no }}</td>
                  <td>{{ tx.items[0]?.identifier || "-" }}</td>
                  <td>{{ formatCount(tx.items.reduce((sum, item) => sum + item.quantity, 0)) }}</td>
                  <td>{{ formatDateTime(tx.occurred_at) }}</td>
                </tr>
                <tr v-if="selectedFixtureTransactions.length === 0"><td colspan="5" class="empty-cell">尚無相關收退料記錄</td></tr>
              </tbody>
            </table>
          </section>

          <section class="info-block">
            <div class="block-head">
              <h3>關聯範圍</h3>
              <button class="outline-btn mini-btn" type="button" @click="showFixtureStationDetail = true">查看詳細</button>
            </div>
            <div class="relation-grid">
              <article class="relation-card"><span>使用到該治具的機種</span><strong>{{ selectedFixtureModelRows.length }}</strong></article>
              <article class="relation-card"><span>使用到該治具的站點總數</span><strong>{{ selectedFixtureStationCount }}</strong></article>
            </div>
            <div class="chip-list">
              <span v-for="model in selectedFixtureModelRows" :key="model.id" class="chip">{{ model.code }}</span>
              <span v-if="selectedFixtureModelRows.length === 0" class="empty-inline">尚無關聯機種</span>
            </div>
          </section>
        </template>

        <template v-else>
          <div class="detail-head">
            <div class="fixture-head-copy">
              <span class="eyebrow">機種查詢</span>
              <div class="fixture-head-line">
                <h2>{{ selectedModel?.code || "尚未選擇機種" }}</h2>
                <span class="fixture-name-chip">{{ selectedModel?.name || "請先搜尋或點選左側結果" }}</span>
              </div>
            </div>
            <UiStatusPill :label="modelLoading ? '載入中' : '已載入'" :tone="modelLoading ? 'warn' : 'normal'" />
          </div>

          <div class="model-metrics">
            <article class="metric-card"><span>最大開站量</span><strong>{{ formatCount(modelQuery?.max_open_station_count ?? 0) }}</strong><small>整體可開站</small></article>
            <article class="metric-card"><span>站點數</span><strong>{{ formatCount(modelQuery?.station_count ?? 0) }}</strong><small>關聯站點</small></article>
            <article class="metric-card"><span>治具種類數</span><strong>{{ formatCount(modelQuery?.fixture_type_count ?? 0) }}</strong><small>相關治具種類</small></article>
          </div>

          <section class="info-block">
            <div class="block-head"><h3>相關治具</h3><span>{{ selectedModelFixtures.length }} 種</span></div>
            <table class="query-table">
              <thead>
                <tr><th>治具</th><th>庫存</th><th>最低水位</th><th>每站需求</th></tr>
              </thead>
              <tbody>
                <tr v-for="row in selectedModelFixtures" :key="row.fixture_id">
                  <td><div class="table-title"><strong>{{ row.fixture_code }}</strong><span>{{ row.fixture_name }}</span></div></td>
                  <td>{{ formatCount(row.stock_qty) }}</td>
                  <td>{{ formatCount(row.min_stock_qty) }}</td>
                  <td>{{ formatCount(row.required_per_station) }}</td>
                </tr>
                <tr v-if="selectedModelFixtures.length === 0"><td colspan="4" class="empty-cell">{{ modelLoading ? "載入中…" : "尚無關聯治具" }}</td></tr>
              </tbody>
            </table>
          </section>

          <section class="info-block">
            <div class="block-head"><h3>相關站點</h3><button class="outline-btn mini-btn" type="button" @click="showModelStationDetail = true">查看詳細</button></div>
            <table class="query-table">
              <thead>
                <tr><th>站點</th><th>站點名稱</th><th>最大開站量</th><th>瓶頸治具</th></tr>
              </thead>
              <tbody>
                <tr v-for="row in selectedModelStations" :key="row.station_id">
                  <td>{{ row.station_code }}</td>
                  <td>{{ row.station_name }}</td>
                  <td>{{ formatCount(row.max_open_station_count) }}</td>
                  <td>{{ fallbackText(row.bottleneck_fixture_code) }}</td>
                </tr>
                <tr v-if="selectedModelStations.length === 0"><td colspan="4" class="empty-cell">{{ modelLoading ? "載入中…" : "尚無相關站點" }}</td></tr>
              </tbody>
            </table>
          </section>
        </template>
      </article>
    </section>

    <teleport to="body">
      <div v-if="showFixtureStationDetail" class="modal-backdrop" @click.self="showFixtureStationDetail = false">
        <div class="modal-card">
          <div class="modal-head">
            <div>
              <span class="eyebrow">治具站點詳細</span>
              <h3>{{ selectedFixture?.code || "-" }}</h3>
              <p>{{ selectedFixture?.name || "-" }}</p>
            </div>
            <button class="outline-btn" type="button" @click="showFixtureStationDetail = false">關閉</button>
          </div>
          <table class="query-table">
            <thead><tr><th>機種</th><th>站點</th><th>站點名稱</th><th>所需數量</th></tr></thead>
            <tbody>
              <tr v-for="row in selectedFixtureStationRows" :key="`${row.model_id}-${row.station_id}`">
                <td>{{ row.model_code }}</td>
                <td>{{ row.station_code }}</td>
                <td>{{ row.station_name }}</td>
                <td>{{ formatCount(row.required_qty) }}</td>
              </tr>
              <tr v-if="selectedFixtureStationRows.length === 0"><td colspan="4" class="empty-cell">尚無站點資料</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </teleport>

    <teleport to="body">
      <div v-if="showModelStationDetail" class="modal-backdrop" @click.self="showModelStationDetail = false">
        <div class="modal-card modal-card-wide">
          <div class="modal-head">
            <div>
              <span class="eyebrow">機種站點詳細</span>
              <h3>{{ selectedModel?.code || "-" }}</h3>
              <p>{{ selectedModel?.name || "-" }}</p>
            </div>
            <button class="outline-btn" type="button" @click="showModelStationDetail = false">關閉</button>
          </div>
          <table class="query-table">
            <thead><tr><th>站點</th><th>治具</th><th>需求數量</th><th>庫存數量</th><th>站點最大開站量</th></tr></thead>
            <tbody>
              <template v-for="group in selectedModelGroups" :key="group.station_id">
                <tr v-for="(row, index) in group.rows" :key="`${group.station_id}-${row.fixture_id}`">
                  <td v-if="index === 0" :rowspan="group.rows.length" class="station-row">{{ group.station_code }}</td>
                  <td>{{ row.fixture_code }}</td>
                  <td>{{ formatCount(row.required_qty) }}</td>
                  <td>{{ formatCount(row.stock_qty) }}</td>
                  <td v-if="index === 0" :rowspan="group.rows.length" class="capacity-row">{{ formatCount(group.max_open_station_count) }}</td>
                </tr>
              </template>
              <tr v-if="selectedModelGroups.length === 0"><td colspan="5" class="empty-cell">尚無站點需求資料</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </teleport>
  </div>
</template>

<style scoped>
.search-shell {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 10px;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  padding: 10px;
}

.hero-summary {
  display: grid;
  gap: 10px;
  border: 1px solid var(--line);
  border-radius: 22px;
  background:
    radial-gradient(circle at top left, rgba(47, 110, 229, 0.09), transparent 28%),
    linear-gradient(180deg, #ffffff 0%, #f6f9ff 100%);
  box-shadow: var(--shadow);
  padding: 12px 14px;
}

.page-hero {
  display: grid;
  gap: 12px;
}

.hero-copy {
  display: grid;
  gap: 6px;
}

.page-hero h1 {
  margin: 2px 0 0;
  color: var(--text);
  font-size: 22px;
  line-height: 1.1;
  text-wrap: balance;
}

.page-hero p {
  margin: 6px 0 0;
  color: var(--muted);
}

.stats-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.stat-card {
  border: 1px solid var(--line);
  border-radius: 16px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(247, 250, 255, 0.98) 100%);
  padding: 8px 14px;
  box-shadow: var(--shadow);
}

.stat-card span,
.search-form span,
.panel-head p,
.detail-head p,
.block-head span,
.result-card-main span,
.metric-card span,
.metric-card small,
.info-grid dt,
.info-grid dd,
.empty-inline {
  color: var(--muted);
}

.stat-card strong,
.metric-card strong,
.relation-card strong {
  display: block;
  margin-top: 4px;
  font-size: 18px;
  font-weight: 900;
  line-height: 1;
}

.stat-card.blue strong,
.relation-card strong,
.metric-card strong {
  color: var(--blue);
}

.stat-card.green strong {
  color: var(--green);
}

.stat-card.orange strong {
  color: var(--orange);
}

.stat-card p {
  margin: 6px 0 0;
  color: #6a7891;
  font-size: 12px;
  font-weight: 700;
}

.search-grid {
  display: grid;
  grid-template-columns: minmax(300px, 360px) minmax(0, 1fr);
  gap: 12px;
  min-height: 0;
  overflow: hidden;
}

.search-panel {
  min-width: 0;
  min-height: 0;
  border: 1px solid var(--line);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: var(--shadow);
  padding: 14px;
  display: grid;
  gap: 14px;
  overflow: auto;
}

.panel-head h1,
.detail-head h2,
.block-head h3,
.modal-head h3 {
  margin: 0;
  color: var(--text);
}

.panel-head h2 {
  margin: 2px 0 0;
  color: var(--text);
  font-size: 16px;
}

.eyebrow {
  display: inline-block;
  margin-bottom: 4px;
  color: var(--blue);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.mode-switch,
.search-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.mode-btn {
  border: 1px solid var(--line-strong);
  border-radius: 14px;
  background: linear-gradient(180deg, #fff 0%, #f6f8fc 100%);
  color: var(--btn-outline-text);
  min-height: 42px;
  font-weight: 800;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.6) inset;
}

.mode-btn.active {
  color: var(--blue);
  border-color: rgba(47, 110, 229, 0.28);
  box-shadow: 0 8px 16px rgba(47, 110, 229, 0.12);
}

.mode-btn:hover {
  transform: translateY(-1px);
}

.search-form {
  display: grid;
  gap: 10px;
}

.search-form label {
  display: grid;
  gap: 6px;
}

.result-summary {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 8px;
  min-width: 0;
  overflow-x: auto;
  padding-bottom: 2px;
}

.result-summary span,
.result-tag,
.chip {
  border: 1px solid #cfdcf2;
  border-radius: 999px;
  background: #f7faff;
  color: #35527d;
  display: inline-flex;
  align-items: center;
  min-width: 0;
  padding: 3px 10px;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.2;
  white-space: nowrap;
}

.result-list {
  display: grid;
  gap: 8px;
  max-height: min(38vh, 360px);
  overflow: auto;
  padding-right: 2px;
}

.result-card {
  display: grid;
  gap: 8px;
  border: 1px solid var(--line);
  border-radius: 16px;
  background: linear-gradient(180deg, #fff 0%, #f8fafe 100%);
  padding: 12px 14px;
  text-align: left;
  cursor: pointer;
  transition: transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
}

.result-card.active {
  border-color: rgba(47, 110, 229, 0.36);
  box-shadow: 0 8px 18px rgba(47, 110, 229, 0.12);
}

.result-card:hover {
  transform: translateY(-1px);
  border-color: #c8d7f2;
  box-shadow: 0 6px 16px rgba(28, 47, 84, 0.08);
}

.result-card-main,
.table-title {
  display: grid;
  gap: 2px;
}

.result-card-main strong,
.table-title strong,
.info-grid dd {
  color: var(--text);
  word-break: break-word;
}

.result-card-meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
  color: #4d5d77;
  font-size: 12px;
  font-weight: 700;
}

.empty-state {
  border: 1px dashed var(--line-strong);
  border-radius: 14px;
  background: #fafcff;
  padding: 14px;
  color: var(--muted);
  text-align: center;
}

.detail-head,
.block-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.detail-head h2 {
  font-size: 20px;
}

.fixture-head-copy {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.fixture-head-line {
  display: flex;
  align-items: baseline;
  gap: 10px;
  min-width: 0;
}

.fixture-name-chip {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  min-width: 0;
  padding: 4px 10px;
  border: 1px solid #d7e2f5;
  border-radius: 999px;
  background: #f7faff;
  color: #35527d;
  font-size: 12px;
  font-weight: 800;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.fixture-hero {
  display: grid;
  grid-template-columns: minmax(220px, 320px) minmax(0, 1fr);
  gap: 12px;
}

.fixture-image,
.metric-card,
.relation-card,
.info-grid div,
.modal-card {
  border: 1px solid var(--line);
  border-radius: 18px;
  background: #fff;
}

.fixture-image {
  min-height: 180px;
  overflow: hidden;
  background: #f7faff;
}

.fixture-image img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.image-placeholder {
  display: grid;
  place-items: center;
  min-height: 180px;
  padding: 16px;
  color: var(--muted);
  text-align: center;
}

.fixture-metrics,
.model-metrics,
.relation-grid,
.info-grid {
  display: grid;
  gap: 8px;
}

.fixture-metrics,
.model-metrics,
.relation-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.model-metrics {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.metric-card,
.relation-card,
.info-grid div {
  padding: 10px 12px;
}

.metric-card {
  position: relative;
  overflow: hidden;
}

.metric-card::before {
  content: "";
  position: absolute;
  inset: 0 auto auto 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, rgba(47, 110, 229, 0.12), transparent);
}

.info-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin: 0;
}

.info-grid .wide {
  grid-column: 1 / -1;
}

.info-grid dt {
  font-size: 12px;
  font-weight: 700;
}

.query-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.query-table thead th {
  background: var(--surface-secondary);
}

.query-table th,
.query-table td {
  padding: 6px 8px;
  border-bottom: 1px solid var(--line);
  text-align: left;
  vertical-align: middle;
  font-size: 12px;
}

.empty-cell {
  color: var(--muted);
  text-align: center;
}

.mini-btn {
  width: auto;
  min-height: 32px;
  padding: 6px 10px;
}

.chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(17, 24, 39, 0.38);
}

.modal-card {
  width: min(940px, 100%);
  max-height: min(86vh, 820px);
  overflow: auto;
  padding: 14px;
  box-shadow: 0 24px 60px rgba(17, 24, 39, 0.22);
}

.modal-card-wide {
  width: min(1120px, 100%);
}

.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
}

.station-row,
.capacity-row {
  font-weight: 800;
}

.capacity-row {
  color: var(--green);
  text-align: center;
  background: #f4fff7;
}

@media (max-width: 920px) {
  .search-grid {
    grid-template-columns: 1fr;
  }

  .stats-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .search-shell {
    padding: 10px;
  }

  .page-hero,
  .stats-strip,
  .fixture-hero,
  .fixture-metrics,
  .model-metrics,
  .relation-grid,
  .info-grid {
    grid-template-columns: 1fr;
  }

  .mode-switch,
  .search-actions {
    grid-template-columns: 1fr;
  }

  .detail-head,
  .block-head,
  .modal-head {
    flex-direction: column;
  }

  .result-summary {
    flex-wrap: wrap;
    overflow-x: visible;
  }
}
</style>
