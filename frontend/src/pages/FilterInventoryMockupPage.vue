<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter, type LocationQueryRaw } from "vue-router";

type ViewMode = "fixture" | "station" | "model";
type FilterKey = "jig" | "station" | "model" | "customer";
type StockStatus = "normal" | "low" | "empty";

type FilterOption = {
  value: string;
  label: string;
  description: string;
};

type InventoryRelation = {
  id: number;
  fixtureCode: string;
  fixtureName: string;
  stationCode: string;
  stationName: string;
  modelCode: string;
  customerCode: string;
  stock: number;
  minimum: number;
  requiredQty: number;
  location: string;
};

type ResultGroup = {
  key: string;
  eyebrow: string;
  title: string;
  subtitle: string;
  stock: number;
  status: StockStatus;
  location: string;
  rows: InventoryRelation[];
};

const route = useRoute();
const router = useRouter();

const viewModes: Array<{ value: ViewMode; label: string; helper: string }> = [
  { value: "fixture", label: "治具", helper: "查看治具庫存與使用關係" },
  { value: "station", label: "站點", helper: "查看各站點所需治具" },
  { value: "model", label: "機種", helper: "查看機種的站點與治具" }
];

const filterLabels: Record<FilterKey, string> = {
  jig: "治具",
  station: "站點",
  model: "機種",
  customer: "客戶"
};

const options: Record<FilterKey, FilterOption[]> = {
  jig: [
    { value: "L-00062", label: "L-00062", description: "壓合定位治具" },
    { value: "L-00475", label: "L-00475", description: "連接器檢測治具" },
    { value: "C-00003", label: "C-00003", description: "外觀檢查治具" },
    { value: "T-00128", label: "T-00128", description: "功能測試載具" },
    { value: "P-00216", label: "P-00216", description: "燒錄定位板" }
  ],
  station: [
    { value: "ST-01", label: "ST-01", description: "組裝站" },
    { value: "ST-02", label: "ST-02", description: "功能測試站" },
    { value: "ST-06", label: "ST-06", description: "外觀檢查站" },
    { value: "ST-09", label: "ST-09", description: "包裝站" }
  ],
  model: [
    { value: "T1_MAC", label: "T1_MAC", description: "T1 主機板" },
    { value: "VPort-254", label: "VPort-254", description: "VPort 工業交換器" },
    { value: "Moxa-A7", label: "Moxa-A7", description: "A7 控制模組" },
    { value: "NPort-6000", label: "NPort-6000", description: "NPort 串列伺服器" }
  ],
  customer: [
    { value: "MOXA", label: "MOXA", description: "四零四科技" },
    { value: "DELTA", label: "DELTA", description: "台達電子" }
  ]
};

const relations: InventoryRelation[] = [
  { id: 1, fixtureCode: "L-00062", fixtureName: "壓合定位治具", stationCode: "ST-01", stationName: "組裝站", modelCode: "T1_MAC", customerCode: "MOXA", stock: 326, minimum: 80, requiredQty: 1, location: "A-01-01" },
  { id: 2, fixtureCode: "L-00062", fixtureName: "壓合定位治具", stationCode: "ST-01", stationName: "組裝站", modelCode: "VPort-254", customerCode: "MOXA", stock: 326, minimum: 80, requiredQty: 2, location: "A-01-01" },
  { id: 3, fixtureCode: "L-00475", fixtureName: "連接器檢測治具", stationCode: "ST-01", stationName: "組裝站", modelCode: "T1_MAC", customerCode: "MOXA", stock: 263, minimum: 60, requiredQty: 1, location: "A-01-03" },
  { id: 4, fixtureCode: "L-00475", fixtureName: "連接器檢測治具", stationCode: "ST-02", stationName: "功能測試站", modelCode: "VPort-254", customerCode: "MOXA", stock: 263, minimum: 60, requiredQty: 1, location: "A-01-03" },
  { id: 5, fixtureCode: "C-00003", fixtureName: "外觀檢查治具", stationCode: "ST-06", stationName: "外觀檢查站", modelCode: "Moxa-A7", customerCode: "MOXA", stock: 18, minimum: 30, requiredQty: 1, location: "B-02-08" },
  { id: 6, fixtureCode: "C-00003", fixtureName: "外觀檢查治具", stationCode: "ST-06", stationName: "外觀檢查站", modelCode: "NPort-6000", customerCode: "MOXA", stock: 18, minimum: 30, requiredQty: 1, location: "B-02-08" },
  { id: 7, fixtureCode: "T-00128", fixtureName: "功能測試載具", stationCode: "ST-02", stationName: "功能測試站", modelCode: "Moxa-A7", customerCode: "DELTA", stock: 0, minimum: 12, requiredQty: 2, location: "C-01-02" },
  { id: 8, fixtureCode: "P-00216", fixtureName: "燒錄定位板", stationCode: "ST-09", stationName: "包裝站", modelCode: "NPort-6000", customerCode: "DELTA", stock: 42, minimum: 15, requiredQty: 1, location: "C-01-06" }
];

const viewMode = ref<ViewMode>("fixture");
const selected = ref<Record<FilterKey, string[]>>({
  jig: [],
  station: [],
  model: [],
  customer: []
});
const openFilter = ref<FilterKey | null>(null);
const filterSearch = ref("");
const keyword = ref("");
const expandedGroups = ref(new Set<string>());
const copied = ref(false);
const demoMessage = ref("");
let routeSyncing = false;
let copyTimer: ReturnType<typeof setTimeout> | undefined;
let demoTimer: ReturnType<typeof setTimeout> | undefined;

const activeFilterCount = computed(() =>
  Object.values(selected.value).reduce((total, values) => total + values.length, 0)
);

const visibleOptions = computed(() => {
  if (!openFilter.value) return [];
  const query = filterSearch.value.trim().toLocaleLowerCase();
  if (!query) return options[openFilter.value];
  return options[openFilter.value].filter((option) =>
    `${option.label} ${option.description}`.toLocaleLowerCase().includes(query)
  );
});

const filteredRelations = computed(() => {
  const query = keyword.value.trim().toLocaleLowerCase();
  return relations.filter((row) => {
    const matchesSelected =
      (selected.value.jig.length === 0 || selected.value.jig.includes(row.fixtureCode)) &&
      (selected.value.station.length === 0 || selected.value.station.includes(row.stationCode)) &&
      (selected.value.model.length === 0 || selected.value.model.includes(row.modelCode)) &&
      (selected.value.customer.length === 0 || selected.value.customer.includes(row.customerCode));
    if (!matchesSelected) return false;
    if (!query) return true;
    return `${row.fixtureCode} ${row.fixtureName} ${row.stationCode} ${row.stationName} ${row.modelCode} ${row.customerCode} ${row.location}`
      .toLocaleLowerCase()
      .includes(query);
  });
});

function stockStatus(stock: number, minimum: number): StockStatus {
  if (stock <= 0) return "empty";
  if (stock < minimum) return "low";
  return "normal";
}

const resultGroups = computed<ResultGroup[]>(() => {
  const groups = new Map<string, InventoryRelation[]>();
  filteredRelations.value.forEach((row) => {
    const key =
      viewMode.value === "fixture"
        ? row.fixtureCode
        : viewMode.value === "station"
          ? row.stationCode
          : row.modelCode;
    groups.set(key, [...(groups.get(key) ?? []), row]);
  });

  return Array.from(groups.entries()).map(([key, rows]) => {
    const first = rows[0];
    if (viewMode.value === "fixture") {
      return {
        key,
        eyebrow: "Fixture",
        title: first.fixtureCode,
        subtitle: first.fixtureName,
        stock: first.stock,
        status: stockStatus(first.stock, first.minimum),
        location: first.location,
        rows
      };
    }
    if (viewMode.value === "station") {
      const stocks = rows.map((row) => stockStatus(row.stock, row.minimum));
      return {
        key,
        eyebrow: "Station",
        title: first.stationCode,
        subtitle: first.stationName,
        stock: new Set(rows.map((row) => row.fixtureCode)).size,
        status: stocks.includes("empty") ? "empty" : stocks.includes("low") ? "low" : "normal",
        location: `${new Set(rows.map((row) => row.modelCode)).size} 個機種`,
        rows
      };
    }
    const stocks = rows.map((row) => stockStatus(row.stock, row.minimum));
    return {
      key,
      eyebrow: "Model",
      title: first.modelCode,
      subtitle: `${new Set(rows.map((row) => row.stationCode)).size} 個站點`,
      stock: new Set(rows.map((row) => row.fixtureCode)).size,
      status: stocks.includes("empty") ? "empty" : stocks.includes("low") ? "low" : "normal",
      location: first.customerCode,
      rows
    };
  });
});

const distinctFixtures = computed(() => new Set(filteredRelations.value.map((row) => row.fixtureCode)).size);
const distinctStations = computed(() => new Set(filteredRelations.value.map((row) => row.stationCode)).size);
const distinctModels = computed(() => new Set(filteredRelations.value.map((row) => row.modelCode)).size);
const issueCount = computed(() =>
  new Set(
    filteredRelations.value
      .filter((row) => stockStatus(row.stock, row.minimum) !== "normal")
      .map((row) => row.fixtureCode)
  ).size
);

function readQueryList(value: unknown, allowed: FilterOption[]): string[] {
  if (typeof value !== "string") return [];
  const allowedValues = new Set(allowed.map((option) => option.value));
  return value.split(",").filter((entry) => allowedValues.has(entry));
}

function applyRouteState(): void {
  routeSyncing = true;
  const mode = route.query.view;
  viewMode.value = mode === "station" || mode === "model" ? mode : "fixture";
  selected.value = {
    jig: readQueryList(route.query.jig, options.jig),
    station: readQueryList(route.query.station, options.station),
    model: readQueryList(route.query.model, options.model),
    customer: readQueryList(route.query.customer, options.customer)
  };
  keyword.value = typeof route.query.q === "string" ? route.query.q : "";
  queueMicrotask(() => {
    routeSyncing = false;
  });
}

function buildQuery(): LocationQueryRaw {
  const query: LocationQueryRaw = {};
  if (viewMode.value !== "fixture") query.view = viewMode.value;
  (Object.keys(selected.value) as FilterKey[]).forEach((key) => {
    if (selected.value[key].length > 0) query[key] = selected.value[key].join(",");
  });
  if (keyword.value.trim()) query.q = keyword.value.trim();
  return query;
}

function toggleFilterPanel(key: FilterKey): void {
  openFilter.value = openFilter.value === key ? null : key;
  filterSearch.value = "";
}

function toggleOption(key: FilterKey, value: string): void {
  const values = selected.value[key];
  selected.value = {
    ...selected.value,
    [key]: values.includes(value) ? values.filter((entry) => entry !== value) : [...values, value]
  };
}

function removeFilter(key: FilterKey, value: string): void {
  selected.value = {
    ...selected.value,
    [key]: selected.value[key].filter((entry) => entry !== value)
  };
}

function resetFilters(): void {
  selected.value = { jig: [], station: [], model: [], customer: [] };
  keyword.value = "";
  openFilter.value = null;
}

function toggleGroup(key: string): void {
  const next = new Set(expandedGroups.value);
  next.has(key) ? next.delete(key) : next.add(key);
  expandedGroups.value = next;
}

function isExpanded(key: string): boolean {
  return expandedGroups.value.has(key) || activeFilterCount.value > 0 || Boolean(keyword.value.trim());
}

function statusLabel(status: StockStatus): string {
  if (status === "empty") return "缺料";
  if (status === "low") return "低水位";
  return "正常";
}

function groupMetricLabel(): string {
  return viewMode.value === "fixture" ? "庫存" : "治具";
}

async function copyShareLink(): Promise<void> {
  await navigator.clipboard?.writeText(window.location.href);
  copied.value = true;
  if (copyTimer) clearTimeout(copyTimer);
  copyTimer = setTimeout(() => {
    copied.value = false;
  }, 1800);
}

function showDemoMessage(message: string): void {
  demoMessage.value = message;
  if (demoTimer) clearTimeout(demoTimer);
  demoTimer = setTimeout(() => {
    demoMessage.value = "";
  }, 2200);
}

watch(
  [viewMode, selected, keyword],
  () => {
    if (routeSyncing) return;
    void router.replace({ path: route.path, query: buildQuery() });
  },
  { deep: true }
);

watch(
  () => route.query,
  () => {
    if (!routeSyncing) applyRouteState();
  }
);

onMounted(applyRouteState);
</script>

<template>
  <main class="filter-view-page">
    <section class="page-heading">
      <div>
        <p class="eyebrow">Inventory relationships</p>
        <h1>庫存關聯瀏覽</h1>
        <p class="heading-copy">用一組篩選條件，快速看清治具、站點與機種之間的綁定關係。</p>
      </div>
      <button class="share-button" type="button" @click="copyShareLink">
        <span aria-hidden="true">↗</span>
        {{ copied ? "連結已複製" : "分享目前檢視" }}
      </button>
    </section>

    <section class="control-card" aria-label="庫存關聯篩選器">
      <div class="view-switch-row">
        <div>
          <span class="control-label">檢視方式</span>
          <p>切換資料的主要分組，不會清除篩選條件。</p>
        </div>
        <div class="view-switch" role="group" aria-label="選擇檢視方式">
          <button
            v-for="mode in viewModes"
            :key="mode.value"
            type="button"
            :class="{ active: viewMode === mode.value }"
            :aria-pressed="viewMode === mode.value"
            :title="mode.helper"
            @click="viewMode = mode.value"
          >
            {{ mode.label }}
          </button>
        </div>
      </div>

      <div class="filter-builder">
        <div class="filter-builder-head">
          <div>
            <span class="control-label">篩選條件</span>
            <span class="logic-hint">同類別 OR <i></i> 跨類別 AND</span>
          </div>
          <button v-if="activeFilterCount || keyword" class="reset-button" type="button" @click="resetFilters">清除全部</button>
        </div>

        <div class="filter-buttons">
          <div v-for="key in (Object.keys(filterLabels) as FilterKey[])" :key="key" class="filter-control">
            <button
              class="filter-add-button"
              :class="{ active: openFilter === key, populated: selected[key].length > 0 }"
              type="button"
              :aria-expanded="openFilter === key"
              @click="toggleFilterPanel(key)"
            >
              <span class="plus">＋</span>
              {{ filterLabels[key] }}
              <span v-if="selected[key].length" class="filter-count">{{ selected[key].length }}</span>
            </button>

            <div v-if="openFilter === key" class="filter-popover">
              <label>
                <span class="sr-only">搜尋{{ filterLabels[key] }}</span>
                <input v-model="filterSearch" type="search" :placeholder="`搜尋${filterLabels[key]}代碼或名稱`" autofocus />
              </label>
              <div class="option-list">
                <button
                  v-for="option in visibleOptions"
                  :key="option.value"
                  type="button"
                  :class="{ selected: selected[key].includes(option.value) }"
                  @click="toggleOption(key, option.value)"
                >
                  <span class="check-box">{{ selected[key].includes(option.value) ? "✓" : "" }}</span>
                  <span><strong>{{ option.label }}</strong><small>{{ option.description }}</small></span>
                </button>
                <p v-if="visibleOptions.length === 0" class="empty-options">找不到符合的項目</p>
              </div>
            </div>
          </div>

          <label class="quick-search">
            <span aria-hidden="true">⌕</span>
            <input v-model="keyword" type="search" placeholder="搜尋代碼、名稱或儲位" />
          </label>
        </div>

        <div v-if="activeFilterCount > 0" class="active-filter-area">
          <template v-for="key in (Object.keys(filterLabels) as FilterKey[])" :key="key">
            <span v-for="value in selected[key]" :key="`${key}-${value}`" class="filter-chip">
              <small>{{ filterLabels[key] }}</small>
              {{ value }}
              <button type="button" :aria-label="`移除 ${value}`" @click="removeFilter(key, value)">×</button>
            </span>
          </template>
        </div>
      </div>
    </section>

    <section class="result-summary" aria-label="篩選結果摘要">
      <div class="result-intro">
        <p><strong>{{ resultGroups.length }}</strong> 組結果</p>
        <span v-if="activeFilterCount === 0 && !keyword">尚未篩選，明細預設收合</span>
        <span v-else>已依 {{ activeFilterCount || 1 }} 個條件顯示關聯明細</span>
      </div>
      <div class="summary-metrics">
        <span><strong>{{ distinctFixtures }}</strong> 治具</span>
        <span><strong>{{ distinctStations }}</strong> 站點</span>
        <span><strong>{{ distinctModels }}</strong> 機種</span>
        <span :class="{ alert: issueCount > 0 }"><strong>{{ issueCount }}</strong> 庫存異常</span>
      </div>
    </section>

    <section class="result-list" aria-live="polite">
      <article v-for="group in resultGroups" :key="group.key" class="result-group" :class="{ expanded: isExpanded(group.key) }">
        <div
          class="group-summary"
          role="button"
          tabindex="0"
          :aria-expanded="isExpanded(group.key)"
          @click="toggleGroup(group.key)"
          @keydown.enter.prevent="toggleGroup(group.key)"
          @keydown.space.prevent="toggleGroup(group.key)"
        >
          <button class="expand-button" type="button" tabindex="-1" aria-hidden="true">
            <span>{{ isExpanded(group.key) ? "−" : "+" }}</span>
          </button>
          <div class="group-identity">
            <span class="group-icon" aria-hidden="true">{{ viewMode === "fixture" ? "治" : viewMode === "station" ? "站" : "機" }}</span>
            <div>
              <small>{{ group.eyebrow }}</small>
              <strong>{{ group.title }}</strong>
              <span>{{ group.subtitle }}</span>
            </div>
          </div>
          <div class="group-meta">
            <div>
              <small>{{ groupMetricLabel() }}</small>
              <strong>{{ group.stock }}</strong>
            </div>
            <div>
              <small>{{ viewMode === "fixture" ? "儲位" : "範圍" }}</small>
              <strong>{{ group.location }}</strong>
            </div>
            <span class="status-pill" :class="group.status"><i></i>{{ statusLabel(group.status) }}</span>
          </div>
          <div class="group-actions" @click.stop>
            <button type="button" @click="showDemoMessage(`${group.title}：開啟編輯面板（Mockup）`)">編輯</button>
            <button class="primary-action" type="button" @click="showDemoMessage(`${group.title}：開啟入出庫面板（Mockup）`)">入 / 出庫</button>
          </div>
        </div>

        <div v-if="isExpanded(group.key)" class="group-detail">
          <div class="detail-heading">
            <span>綁定明細</span>
            <small>{{ group.rows.length }} 筆關聯</small>
          </div>
          <div class="detail-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>治具</th>
                  <th>站點</th>
                  <th>機種</th>
                  <th>客戶</th>
                  <th>每站需求</th>
                  <th>目前庫存</th>
                  <th>可開站數</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in group.rows" :key="row.id">
                  <td><strong>{{ row.fixtureCode }}</strong><small>{{ row.fixtureName }}</small></td>
                  <td><strong>{{ row.stationCode }}</strong><small>{{ row.stationName }}</small></td>
                  <td><strong>{{ row.modelCode }}</strong></td>
                  <td>{{ row.customerCode }}</td>
                  <td>{{ row.requiredQty }} 支</td>
                  <td><strong :class="`stock-${stockStatus(row.stock, row.minimum)}`">{{ row.stock }}</strong></td>
                  <td>{{ Math.floor(row.stock / row.requiredQty) }} 站</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </article>

      <div v-if="resultGroups.length === 0" class="empty-state">
        <span aria-hidden="true">⌕</span>
        <h2>沒有符合的綁定資料</h2>
        <p>可以移除部分條件，或改用其他代碼搜尋。</p>
        <button type="button" @click="resetFilters">清除篩選條件</button>
      </div>
    </section>

    <transition name="toast">
      <div v-if="demoMessage" class="demo-toast" role="status">{{ demoMessage }}</div>
    </transition>
  </main>
</template>

<style scoped>
.filter-view-page {
  --ink: #17231f;
  --muted: #69756f;
  --line: #dde4df;
  --soft-line: #edf1ee;
  --green: #0b7654;
  --green-dark: #075c42;
  --green-soft: #eaf5f0;
  min-height: 100%;
  padding: 32px clamp(20px, 4vw, 56px) 56px;
  color: var(--ink);
  background:
    radial-gradient(circle at 94% 0%, rgba(11, 118, 84, 0.07), transparent 29rem),
    #f7f9f7;
  font-family: "Noto Sans TC", "Microsoft JhengHei", system-ui, sans-serif;
}

button,
input {
  font: inherit;
}

button {
  color: inherit;
}

.page-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  max-width: 1480px;
  margin: 0 auto 24px;
}

.eyebrow {
  margin: 0 0 6px;
  color: var(--green);
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.page-heading h1 {
  margin: 0;
  font-size: clamp(1.85rem, 3vw, 2.55rem);
  letter-spacing: -0.04em;
}

.heading-copy {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 0.98rem;
}

.share-button,
.reset-button {
  border: 0;
  background: transparent;
  cursor: pointer;
}

.share-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 42px;
  padding: 0 15px;
  border: 1px solid #cbd6d0;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.82);
  font-weight: 700;
}

.share-button:hover {
  border-color: var(--green);
  color: var(--green);
}

.control-card,
.result-summary,
.result-list {
  max-width: 1480px;
  margin-right: auto;
  margin-left: auto;
}

.control-card {
  overflow: visible;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 12px 36px rgba(33, 56, 46, 0.06);
}

.view-switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 20px 22px;
  border-bottom: 1px solid var(--soft-line);
}

.control-label {
  font-size: 0.92rem;
  font-weight: 800;
}

.view-switch-row p {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 0.82rem;
}

.view-switch {
  display: inline-grid;
  grid-template-columns: repeat(3, 1fr);
  width: min(100%, 340px);
  padding: 4px;
  border: 1px solid #d9e1dc;
  border-radius: 12px;
  background: #f3f6f4;
}

.view-switch button {
  min-height: 38px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: #6a756f;
  font-weight: 800;
  cursor: pointer;
}

.view-switch button.active {
  color: var(--green-dark);
  background: #fff;
  box-shadow: 0 2px 8px rgba(36, 66, 53, 0.12);
}

.filter-builder {
  padding: 20px 22px 22px;
}

.filter-builder-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 30px;
  margin-bottom: 12px;
}

.logic-hint {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-left: 12px;
  color: #87918c;
  font-size: 0.75rem;
}

.logic-hint i {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: #aab3ae;
}

.reset-button {
  color: var(--green);
  font-size: 0.82rem;
  font-weight: 800;
}

.filter-buttons {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-control {
  position: relative;
}

.filter-add-button {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 42px;
  padding: 0 13px;
  border: 1px dashed #b8c5be;
  border-radius: 10px;
  background: #fff;
  font-weight: 750;
  cursor: pointer;
}

.filter-add-button:hover,
.filter-add-button.active,
.filter-add-button.populated {
  border-style: solid;
  border-color: #79a893;
  color: var(--green-dark);
  background: var(--green-soft);
}

.plus {
  color: var(--green);
  font-size: 1.1rem;
  line-height: 1;
}

.filter-count {
  display: grid;
  place-items: center;
  min-width: 20px;
  height: 20px;
  padding: 0 5px;
  border-radius: 999px;
  color: #fff;
  background: var(--green);
  font-size: 0.7rem;
}

.filter-popover {
  position: absolute;
  z-index: 30;
  top: calc(100% + 8px);
  left: 0;
  width: 290px;
  padding: 10px;
  border: 1px solid #d8e1dc;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 18px 45px rgba(24, 48, 38, 0.18);
}

.filter-popover input {
  width: 100%;
  height: 40px;
  padding: 0 11px;
  border: 1px solid #d7dfda;
  border-radius: 8px;
  outline: none;
}

.filter-popover input:focus {
  border-color: var(--green);
  box-shadow: 0 0 0 3px rgba(11, 118, 84, 0.1);
}

.option-list {
  display: grid;
  gap: 3px;
  max-height: 250px;
  margin-top: 8px;
  overflow-y: auto;
}

.option-list > button {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 50px;
  padding: 7px 8px;
  border: 0;
  border-radius: 9px;
  text-align: left;
  background: transparent;
  cursor: pointer;
}

.option-list > button:hover,
.option-list > button.selected {
  background: #f0f7f3;
}

.check-box {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 20px;
  height: 20px;
  border: 1px solid #b8c4be;
  border-radius: 6px;
  color: #fff;
  font-size: 0.72rem;
}

.selected .check-box {
  border-color: var(--green);
  background: var(--green);
}

.option-list strong,
.option-list small {
  display: block;
}

.option-list strong {
  font-size: 0.83rem;
}

.option-list small {
  margin-top: 2px;
  color: var(--muted);
  font-size: 0.72rem;
}

.empty-options {
  padding: 18px;
  text-align: center;
  color: var(--muted);
  font-size: 0.8rem;
}

.quick-search {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 230px;
  height: 42px;
  margin-left: auto;
  padding: 0 12px;
  border: 1px solid #d7dfda;
  border-radius: 10px;
  color: #76817b;
  background: #fbfcfb;
}

.quick-search:focus-within {
  border-color: var(--green);
  box-shadow: 0 0 0 3px rgba(11, 118, 84, 0.08);
}

.quick-search input {
  min-width: 0;
  width: 100%;
  border: 0;
  outline: 0;
  background: transparent;
}

.active-filter-area {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--soft-line);
}

.filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 30px;
  padding: 0 7px 0 10px;
  border: 1px solid #c6ded2;
  border-radius: 999px;
  color: var(--green-dark);
  background: var(--green-soft);
  font-size: 0.78rem;
  font-weight: 800;
}

.filter-chip small {
  color: #658477;
  font-size: 0.66rem;
}

.filter-chip button {
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: rgba(11, 118, 84, 0.1);
  cursor: pointer;
}

.result-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 24px 2px 12px;
}

.result-intro {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.result-intro p {
  margin: 0;
  font-weight: 800;
}

.result-intro p strong {
  font-size: 1.2rem;
}

.result-intro > span {
  color: var(--muted);
  font-size: 0.78rem;
}

.summary-metrics {
  display: flex;
  align-items: center;
  gap: 8px;
}

.summary-metrics span {
  padding: 6px 9px;
  border: 1px solid #e0e6e2;
  border-radius: 8px;
  color: var(--muted);
  background: rgba(255, 255, 255, 0.7);
  font-size: 0.74rem;
}

.summary-metrics strong {
  color: var(--ink);
}

.summary-metrics .alert {
  border-color: #f0d6bd;
  color: #a65816;
  background: #fff8ef;
}

.summary-metrics .alert strong {
  color: #b24b16;
}

.result-list {
  display: grid;
  gap: 10px;
}

.result-group {
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 3px 12px rgba(35, 57, 48, 0.035);
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.result-group:hover,
.result-group.expanded {
  border-color: #becdc5;
  box-shadow: 0 8px 24px rgba(35, 57, 48, 0.07);
}

.group-summary {
  display: grid;
  grid-template-columns: 34px minmax(240px, 1.4fr) minmax(310px, 1fr) auto;
  align-items: center;
  gap: 15px;
  min-height: 86px;
  padding: 12px 16px;
  cursor: pointer;
  outline: none;
}

.group-summary:focus-visible {
  box-shadow: inset 0 0 0 3px rgba(11, 118, 84, 0.22);
}

.expand-button {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: 1px solid #d8e0db;
  border-radius: 8px;
  color: var(--green);
  background: #fff;
}

.expand-button span {
  font-size: 1rem;
  line-height: 1;
}

.group-identity {
  display: flex;
  align-items: center;
  gap: 13px;
  min-width: 0;
}

.group-icon {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 42px;
  height: 42px;
  border-radius: 11px;
  color: var(--green-dark);
  background: var(--green-soft);
  font-size: 0.78rem;
  font-weight: 900;
}

.group-identity div {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: baseline;
  column-gap: 9px;
  min-width: 0;
}

.group-identity small {
  grid-column: 1 / -1;
  color: #8b9690;
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.group-identity strong {
  font-size: 1rem;
}

.group-identity span {
  overflow: hidden;
  color: var(--muted);
  font-size: 0.78rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.group-meta {
  display: grid;
  grid-template-columns: minmax(70px, 0.6fr) minmax(100px, 1fr) auto;
  align-items: center;
  gap: 18px;
}

.group-meta > div small,
.group-meta > div strong {
  display: block;
}

.group-meta > div small {
  margin-bottom: 3px;
  color: #89938e;
  font-size: 0.67rem;
}

.group-meta > div strong {
  font-size: 0.87rem;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-width: 68px;
  min-height: 27px;
  padding: 0 9px;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 850;
}

.status-pill i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.status-pill.normal {
  color: #16724f;
  background: #eaf6f0;
}

.status-pill.low {
  color: #a85a12;
  background: #fff3e1;
}

.status-pill.empty {
  color: #b43d32;
  background: #fdeceb;
}

.group-actions {
  display: flex;
  justify-content: flex-end;
  gap: 7px;
}

.group-actions button {
  min-height: 34px;
  padding: 0 11px;
  border: 1px solid #d6dfda;
  border-radius: 8px;
  background: #fff;
  font-size: 0.74rem;
  font-weight: 800;
  cursor: pointer;
}

.group-actions button:hover {
  border-color: #83ac98;
  color: var(--green);
}

.group-actions .primary-action {
  border-color: var(--green);
  color: #fff;
  background: var(--green);
}

.group-actions .primary-action:hover {
  color: #fff;
  background: var(--green-dark);
}

.group-detail {
  border-top: 1px solid var(--soft-line);
  background: #fbfcfb;
}

.detail-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px 8px 66px;
}

.detail-heading span {
  font-size: 0.78rem;
  font-weight: 850;
}

.detail-heading small {
  color: var(--muted);
  font-size: 0.7rem;
}

.detail-table-wrap {
  overflow-x: auto;
  padding: 0 20px 18px 66px;
}

table {
  width: 100%;
  min-width: 760px;
  border-collapse: collapse;
}

th,
td {
  padding: 11px 13px;
  border-bottom: 1px solid #e8edea;
  text-align: left;
}

th {
  color: #79847e;
  font-size: 0.67rem;
  font-weight: 800;
}

td {
  color: #4e5a54;
  font-size: 0.76rem;
}

td strong,
td small {
  display: block;
}

td strong {
  color: var(--ink);
}

td small {
  margin-top: 2px;
  color: #8a948f;
  font-size: 0.66rem;
}

.stock-low {
  color: #a85a12;
}

.stock-empty {
  color: #b43d32;
}

.empty-state {
  display: grid;
  justify-items: center;
  padding: 70px 20px;
  border: 1px dashed #cbd6d0;
  border-radius: 16px;
  text-align: center;
  color: var(--muted);
  background: rgba(255, 255, 255, 0.72);
}

.empty-state > span {
  font-size: 2rem;
}

.empty-state h2 {
  margin: 12px 0 4px;
  color: var(--ink);
  font-size: 1.1rem;
}

.empty-state p {
  margin: 0 0 16px;
  font-size: 0.82rem;
}

.empty-state button {
  min-height: 38px;
  padding: 0 14px;
  border: 0;
  border-radius: 9px;
  color: #fff;
  background: var(--green);
  font-weight: 800;
  cursor: pointer;
}

.demo-toast {
  position: fixed;
  z-index: 50;
  right: 28px;
  bottom: 28px;
  max-width: min(440px, calc(100vw - 40px));
  padding: 13px 16px;
  border-radius: 11px;
  color: #fff;
  background: #183f32;
  box-shadow: 0 12px 32px rgba(14, 46, 35, 0.24);
  font-size: 0.82rem;
  font-weight: 700;
}

.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 1080px) {
  .group-summary {
    grid-template-columns: 34px minmax(230px, 1fr) minmax(260px, 0.9fr);
  }

  .group-actions {
    grid-column: 2 / -1;
  }
}

@media (max-width: 760px) {
  .filter-view-page {
    padding: 22px 14px 40px;
  }

  .page-heading,
  .view-switch-row,
  .result-summary {
    align-items: stretch;
    flex-direction: column;
  }

  .share-button {
    align-self: flex-start;
  }

  .view-switch {
    width: 100%;
  }

  .filter-buttons,
  .quick-search {
    width: 100%;
  }

  .filter-control {
    flex: 1 1 calc(50% - 8px);
  }

  .filter-add-button {
    justify-content: center;
    width: 100%;
  }

  .filter-popover {
    position: fixed;
    top: auto;
    right: 14px;
    bottom: 14px;
    left: 14px;
    width: auto;
    max-height: min(70vh, 520px);
  }

  .summary-metrics {
    flex-wrap: wrap;
  }

  .group-summary {
    grid-template-columns: 30px 1fr;
    gap: 12px;
  }

  .group-meta,
  .group-actions {
    grid-column: 2;
  }

  .group-meta {
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
  }

  .group-actions {
    justify-content: flex-start;
  }

  .detail-heading,
  .detail-table-wrap {
    padding-left: 20px;
  }
}
</style>
