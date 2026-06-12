<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { api, fixtureImageUrlByCode } from "@/api";
import { selectedCustomerId } from "@/appState";
import { pushToast } from "@/toastState";
import type { MaterialTransaction, ModelQuery, ModelQueryStationRequirement, SearchResult, StockSummary } from "@/types";
import { formatLocalDateKey as formatDateKey } from "@/utils/date";

type Mode = "receipt" | "return" | "fixture" | "model";

const mode = ref<Mode>("fixture");
const query = ref("C-00003");
const loading = ref(false);
const showFilters = ref(true);
const resultPage = ref(1);
const resultPageSize = 10;

const models = ref<Array<{ id: number; code: string; name: string }>>([]);
const selectedModelId = ref<number | null>(null);
const modelQuery = ref<ModelQuery | null>(null);
const modelQueryUpdatedAt = ref<string>("-");
const showCapacityDetails = ref(false);

const stockRows = ref<StockSummary[]>([]);
const transactions = ref<MaterialTransaction[]>([]);
const searchResults = ref<SearchResult[]>([]);
const selectedFixtureCode = ref("");
const imageLoadFailed = ref(false);

const selectedStock = computed(() => stockRows.value.find((row) => row.fixture_code === selectedFixtureCode.value) ?? null);
const today = computed(() => formatDateKey(new Date()));

const statusLabel = computed(() => {
  if (!selectedStock.value) return "未設定";
  if (selectedStock.value.stock_status === "out_of_stock") return "缺料";
  if (selectedStock.value.stock_status === "low_stock") return "低於水位";
  return "正常庫存";
});

const statusClass = computed(() => selectedStock.value?.stock_status ?? "normal");

const selectedLocation = computed(() => {
  const matched = searchResults.value.find((item) => item.title.startsWith(selectedFixtureCode.value));
  return matched?.location_code || "-";
});

const selectedModels = computed(() => {
  if (mode.value === "model" && modelQuery.value) {
    return [modelQuery.value.model_code];
  }
  const matched = searchResults.value.find((item) => item.title.startsWith(selectedFixtureCode.value));
  const subtitle = matched?.subtitle || "";
  if (!subtitle || subtitle === "Fixture") return [];
  return subtitle
    .split(/[\/,]/)
    .map((item) => item.trim())
    .filter(Boolean);
});

const currentImage = computed(() => (selectedFixtureCode.value && !imageLoadFailed.value ? fixtureImageUrlByCode(selectedFixtureCode.value) : ""));

const lowStockCount = computed(
  () => stockRows.value.filter((row) => row.stock_status === "low_stock" || row.stock_status === "out_of_stock").length
);

const totalFixtureQty = computed(() => stockRows.value.reduce((sum, row) => sum + row.stock_qty, 0));

const todayReceiptQty = computed(() =>
  transactions.value
    .filter((tx) => tx.transaction_type === "receipt" && formatDateKey(new Date(tx.occurred_at)) === today.value)
    .reduce((sum, tx) => sum + tx.items.reduce((itemSum, item) => itemSum + item.quantity, 0), 0)
);

const todayReturnQty = computed(() =>
  transactions.value
    .filter((tx) => tx.transaction_type === "return" && formatDateKey(new Date(tx.occurred_at)) === today.value)
    .reduce((sum, tx) => sum + tx.items.reduce((itemSum, item) => itemSum + item.quantity, 0), 0)
);

const displayRows = computed(() => {
  const q = query.value.trim().toLowerCase();
  const resultFixtureCodes = searchResults.value
    .filter((item) => item.entity_type === "fixture")
    .map((item) => item.title.split(" - ")[0]?.trim())
    .filter((code): code is string => !!code);

  let rows = stockRows.value;
  if (resultFixtureCodes.length > 0) {
    rows = rows.filter((row) => resultFixtureCodes.includes(row.fixture_code));
  } else if (q) {
    rows = rows.filter((row) => row.fixture_code.toLowerCase().includes(q) || row.fixture_name.toLowerCase().includes(q));
  }

  return rows;
});

const displayPageTotal = computed(() => Math.max(1, Math.ceil(displayRows.value.length / resultPageSize)));
const pagedDisplayRows = computed(() => {
  const start = (resultPage.value - 1) * resultPageSize;
  return displayRows.value.slice(start, start + resultPageSize);
});

const modelStationRows = computed(() => modelQuery.value?.stations ?? []);
const modelRequirementRows = computed(() => modelQuery.value?.station_requirements ?? []);

const stationRequirementGroups = computed(() => {
  const groups = new Map<number, { station_id: number; station_code: string; rows: ModelQueryStationRequirement[] }>();
  for (const row of modelRequirementRows.value) {
    const group = groups.get(row.station_id);
    if (group) {
      group.rows.push(row);
    } else {
      groups.set(row.station_id, {
        station_id: row.station_id,
        station_code: row.station_code,
        rows: [row]
      });
    }
  }
  return [...groups.values()].map((group) => ({
    ...group,
    rows: group.rows.slice().sort((a, b) => a.fixture_code.localeCompare(b.fixture_code))
  })).sort((a, b) => a.station_code.localeCompare(b.station_code));
});

const capacityPreviewGroups = computed(() => stationRequirementGroups.value.slice(0, 2));
const hasMoreCapacityRows = computed(() => stationRequirementGroups.value.length > capacityPreviewGroups.value.length);
const stationCards = computed(() => modelQuery.value?.stations ?? []);
const stationCapacityById = computed(() => {
  const map = new Map<number, number>();
  for (const row of modelQuery.value?.stations ?? []) {
    map.set(row.station_id, row.max_open_station_count);
  }
  return map;
});

const selectedTransactions = computed(() => {
  let rows = transactions.value;
  if (mode.value === "receipt" || mode.value === "return") {
    rows = rows.filter((tx) => tx.transaction_type === mode.value);
  }
  if (!selectedFixtureCode.value) return rows.slice(0, 8);
  return rows
    .filter((tx) => tx.items.some((item) => item.fixture_code === selectedFixtureCode.value))
    .slice(0, 8);
});

const latestEvents = computed(() =>
  selectedTransactions.value.slice(0, 3).map((tx) => {
    const qty = tx.items.reduce((sum, item) => sum + item.quantity, 0);
    return {
      id: tx.id,
      date: new Date(tx.occurred_at).toLocaleDateString("zh-TW"),
      type: tx.transaction_type,
      qty
    };
  })
);

function pickFixture(code: string): void {
  selectedFixtureCode.value = code;
  imageLoadFailed.value = false;
}

async function refreshFixtureContext(code: string): Promise<void> {
  try {
    const rows = await api.globalSearch(code, selectedCustomerId.value ?? undefined);
    searchResults.value = rows.filter((item) => item.entity_type === "fixture" || item.entity_type === "serial");
  } catch {
    searchResults.value = [];
  }
}

async function doModelSearch(modelIdFromButton?: number): Promise<void> {
  const q = query.value.trim().toLowerCase();
  const pickedModel =
    models.value.find((item) => item.id === modelIdFromButton) ||
    models.value.find((item) => item.code.toLowerCase() === q) ||
    models.value.find((item) => item.code.toLowerCase().includes(q) || item.name.toLowerCase().includes(q)) ||
    models.value[0];

  if (!pickedModel) {
    modelQuery.value = null;
    return;
  }

  selectedModelId.value = pickedModel.id;
  query.value = pickedModel.code;
  modelQuery.value = await api.getModelQuery(pickedModel.id, selectedCustomerId.value ?? undefined);
  modelQueryUpdatedAt.value = new Date().toLocaleString("zh-TW");
  showCapacityDetails.value = false;

  const firstFixture = modelQuery.value.fixtures[0];
  if (firstFixture) {
    selectedFixtureCode.value = firstFixture.fixture_code;
    imageLoadFailed.value = false;
    await refreshFixtureContext(firstFixture.fixture_code);
  } else {
    selectedFixtureCode.value = "";
    imageLoadFailed.value = false;
    searchResults.value = [];
  }
}

async function doSearch(): Promise<void> {
  if (mode.value === "model") {
    loading.value = true;
    try {
      await doModelSearch();
    } catch (err) {
      pushToast(err instanceof Error ? err.message : "查詢機種失敗", "error");
    } finally {
      loading.value = false;
    }
    return;
  }

  const q = query.value.trim();
  if (!q) {
    searchResults.value = [];
    return;
  }

  loading.value = true;
  try {
    const rows = await api.globalSearch(q, selectedCustomerId.value ?? undefined);
    if (mode.value === "fixture") {
      searchResults.value = rows.filter((item) => item.entity_type === "fixture" || item.entity_type === "serial");
    } else {
      searchResults.value = rows;
    }
    resultPage.value = 1;

    const firstFixture = searchResults.value.find((item) => item.entity_type === "fixture");
    if (firstFixture) {
      selectedFixtureCode.value = firstFixture.title.split(" - ")[0] ?? "";
      imageLoadFailed.value = false;
    } else {
      selectedFixtureCode.value = "";
      imageLoadFailed.value = false;
    }
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "查詢失敗", "error");
  } finally {
    loading.value = false;
  }
}

function previousResultPage(): void {
  resultPage.value = Math.max(1, resultPage.value - 1);
}

function nextResultPage(): void {
  resultPage.value = Math.min(displayPageTotal.value, resultPage.value + 1);
}

function modeLabel(txType: "receipt" | "return"): string {
  return txType === "receipt" ? "收料" : "退料";
}

onMounted(async () => {
  try {
    const customerId = selectedCustomerId.value ?? undefined;
    const [stock, tx, modelRows] = await Promise.all([
      api.listStock(customerId),
      api.listTransactions(40, customerId),
      customerId ? api.listModels(customerId) : Promise.resolve([])
    ]);
    stockRows.value = stock;
    transactions.value = tx;
    models.value = modelRows;
    selectedFixtureCode.value = stock[0]?.fixture_code ?? "";
    imageLoadFailed.value = false;
    if (stock[0]) {
      await refreshFixtureContext(stock[0].fixture_code);
    }
    await doSearch();
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "初始化失敗", "error");
  }
});

watch(mode, () => {
  resultPage.value = 1;
  void doSearch();
});

watch(selectedCustomerId, async () => {
  resultPage.value = 1;
  const customerId = selectedCustomerId.value ?? undefined;
  const [stock, tx, modelRows] = await Promise.all([
    api.listStock(customerId),
    api.listTransactions(40, customerId),
    customerId ? api.listModels(customerId) : Promise.resolve([])
  ]);
  stockRows.value = stock;
  transactions.value = tx;
  models.value = modelRows;
  await doSearch();
});

watch([query, showFilters], () => {
  resultPage.value = 1;
});

watch(displayRows, () => {
  if (resultPage.value > displayPageTotal.value) {
    resultPage.value = displayPageTotal.value;
  }
});

watch(selectedFixtureCode, () => {
  imageLoadFailed.value = false;
});
</script>

<template>
  <div class="search-shell">
    <section class="workspace">
      <article class="query-panel">
        <div class="panel-title">
          <h2>{{ mode === "model" ? "機種查詢" : "治具查詢" }}</h2>
          <p>{{ mode === "model" ? "輸入機種或點常用機種直接查詢。" : "可查詢治具、收料與退料紀錄。" }}</p>
        </div>

        <button class="ghost-btn small toggle-btn" type="button" @click="showFilters = !showFilters">
          {{ showFilters ? "收合篩選" : "展開篩選" }}
        </button>

        <div v-show="showFilters">
          <div class="query-mode-list">
            <label class="radio-card"><input v-model="mode" value="receipt" type="radio" /> 收料查詢</label>
            <label class="radio-card"><input v-model="mode" value="return" type="radio" /> 退料查詢</label>
            <label class="radio-card"><input v-model="mode" value="fixture" type="radio" /> 治具查詢</label>
            <label class="radio-card"><input v-model="mode" value="model" type="radio" /> 機種查詢</label>
          </div>

          <form class="search-form" @submit.prevent="doSearch">
            <label>
              <span>{{ mode === "model" ? "機種編號 / 名稱" : "治具編號 / 名稱 / 流水號" }}</span>
              <input v-model="query" :placeholder="mode === 'model' ? '例如 eds / VPort 254' : '例如 C-00003'" />
            </label>
            <button class="primary-btn" type="submit">{{ loading ? "查詢中..." : "查詢" }}</button>
          </form>

          <div class="search-status-strip">
            <span>模式：{{ mode === "model" ? "機種" : mode === "fixture" ? "治具" : mode === "receipt" ? "收料" : "退料" }}</span>
            <span>結果：{{ mode === "model" ? (modelQuery ? 1 : 0) : displayRows.length }} 筆</span>
            <span v-if="loading">查詢中...</span>
          </div>

          <div v-if="mode === 'model'" class="common-models">
            <div class="sub-head">
              <h3>常用機種</h3>
              <span>{{ models.length }} 筆</span>
            </div>
            <div class="common-model-grid">
              <button
                v-for="item in models.slice(0, 6)"
                :key="item.id"
                class="ghost-btn"
                :class="{ selected: item.id === selectedModelId }"
                @click="doModelSearch(item.id)"
              >
                {{ item.code }}
              </button>
            </div>
            <div v-if="models.length === 0" class="empty-banner">目前沒有可用機種資料</div>
          </div>

          <div v-else class="collapsed-filter-tip">篩選區已展開，收合後可保留結果畫面空間。</div>
        </div>
      </article>

      <article class="result-panel">
        <template v-if="mode !== 'model'">
          <div class="panel-title inline-title">
            <div>
              <h2>查詢結果</h2>
              <p>{{ selectedFixtureCode || "尚未選定治具" }}</p>
            </div>
          </div>

          <div class="kpi-strip">
            <article class="kpi-card">
              <span>治具總數</span>
              <strong>{{ totalFixtureQty }}</strong>
            </article>
            <article class="kpi-card">
              <span>低水位</span>
              <strong>{{ lowStockCount }}</strong>
            </article>
            <article class="kpi-card">
              <span>今日收料</span>
              <strong>{{ todayReceiptQty }}</strong>
            </article>
            <article class="kpi-card">
              <span>今日退料</span>
              <strong>{{ todayReturnQty }}</strong>
            </article>
          </div>

          <div v-if="loading" class="loading-banner">查詢中，請稍候...</div>

          <div class="table-section">
            <div class="sub-head">
              <h3>現有治具列表</h3>
              <span>{{ displayRows.length }} 筆</span>
            </div>
          <table class="data-table">
              <thead>
                <tr>
                  <th>治具編號</th>
                  <th>治具名稱</th>
                  <th>數量</th>
                  <th>狀態</th>
                </tr>
              </thead>
              <tbody>
                <tr
                v-for="row in pagedDisplayRows"
                :key="row.fixture_id"
                :class="{ active: row.fixture_code === selectedFixtureCode }"
                @click="pickFixture(row.fixture_code)"
                >
                  <td>{{ row.fixture_code }}</td>
                  <td>{{ row.fixture_name }}</td>
                  <td>{{ row.stock_qty }} pcs</td>
                  <td>
                    <span class="status-pill" :class="row.stock_status">
                      {{ row.stock_status === "normal" ? "充足" : row.stock_status === "low_stock" ? "偏低" : "不足" }}
                    </span>
                  </td>
                </tr>
              <tr v-if="!loading && displayRows.length === 0">
                <td colspan="4" class="empty-cell">尚無符合條件的治具</td>
              </tr>
            </tbody>
          </table>
          <div v-if="displayRows.length > 0" class="list-footer">
            <span>第 {{ resultPage }} / {{ displayPageTotal }} 頁，共 {{ displayRows.length }} 筆</span>
            <div class="pager-actions">
              <button class="ghost-btn small" type="button" :disabled="loading || resultPage <= 1" @click="previousResultPage">上一頁</button>
              <button class="ghost-btn small" type="button" :disabled="loading || resultPage >= displayPageTotal" @click="nextResultPage">下一頁</button>
            </div>
          </div>
        </div>

          <div class="table-section">
            <div class="sub-head">
              <h3>{{ mode === "receipt" ? "收料記錄" : mode === "return" ? "退料記錄" : "最近異動紀錄" }}</h3>
              <span>{{ selectedTransactions.length }} 筆</span>
            </div>
            <table class="data-table">
              <thead>
                <tr>
                  <th>治具編號</th>
                  <th>數量</th>
                  <th>單號</th>
                  <th>日期</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="tx in selectedTransactions" :key="tx.id">
                  <td>{{ tx.items[0]?.fixture_code || "-" }}</td>
                  <td>{{ tx.items.reduce((sum, item) => sum + item.quantity, 0) }} pcs</td>
                  <td>{{ tx.transaction_no }}</td>
                  <td>{{ new Date(tx.occurred_at).toLocaleString("zh-TW") }}</td>
                </tr>
                <tr v-if="!loading && selectedTransactions.length === 0">
                  <td colspan="4" class="empty-cell">尚無符合條件的紀錄</td>
              </tr>
            </tbody>
          </table>
          <div v-if="displayRows.length > 0" class="list-footer">
            <span>第 {{ resultPage }} / {{ displayPageTotal }} 頁，共 {{ displayRows.length }} 筆</span>
            <div class="pager-actions">
              <button class="ghost-btn small" type="button" :disabled="loading || resultPage <= 1" @click="previousResultPage">上一頁</button>
              <button class="ghost-btn small" type="button" :disabled="loading || resultPage >= displayPageTotal" @click="nextResultPage">下一頁</button>
            </div>
          </div>
        </div>
        </template>

        <template v-else>
          <div class="panel-title inline-title model-headline">
            <div>
              <h2>機種查詢</h2>
              <p>更新時間：{{ modelQueryUpdatedAt }}</p>
            </div>
            <div class="model-name-badge">
              {{ modelQuery?.model_name || "-" }}
            </div>
          </div>

          <div class="basic-info">
            <div class="basic-row">
              <span>機種代碼</span>
              <strong>{{ modelQuery?.model_code || "-" }}</strong>
            </div>
            <div class="basic-row">
              <span>名稱</span>
              <strong>{{ modelQuery?.model_name || "-" }}</strong>
            </div>
          </div>

          <div class="compact-section">
            <div class="section-header">
              <div>
                <h3>每站最大可開站量</h3>
                <p>每個站點只看站點編號與可開站數。</p>
              </div>
              <span>{{ stationCards.length }} 筆</span>
            </div>
            <div class="station-pill-grid">
              <article v-for="row in stationCards" :key="row.station_id" class="station-pill">
                <span>{{ row.station_code }}</span>
                <strong>{{ row.max_open_station_count }}</strong>
              </article>
            </div>
          </div>

          <div class="compact-section">
            <div class="section-header">
              <div>
                <h3>站點需求明細</h3>
                <p>預覽前兩個站點，超過時可點開完整表格。</p>
              </div>
              <button v-if="hasMoreCapacityRows" class="outline-btn mini-btn" type="button" @click="showCapacityDetails = true">
                點開看完整表格
              </button>
            </div>
            <div class="table-section">
              <table class="data-table detail-table compact-detail-table">
                <thead>
                  <tr>
                    <th>站點</th>
                    <th>治具</th>
                    <th>所需治具數量</th>
                    <th>庫存數量</th>
                    <th>站點最大可開站數</th>
                  </tr>
                </thead>
                <tbody>
                  <template v-for="group in capacityPreviewGroups" :key="group.station_id">
                    <tr v-for="(row, index) in group.rows" :key="`${group.station_id}-${row.fixture_id}`">
                      <td v-if="index === 0" :rowspan="group.rows.length" class="station-cell">{{ group.station_code }}</td>
                      <td>{{ row.fixture_code }}</td>
                      <td>{{ row.required_qty }}</td>
                      <td>{{ row.stock_qty }}</td>
                      <td v-if="index === 0" :rowspan="group.rows.length" class="capacity-cell">
                        {{ stationCapacityById.get(row.station_id) ?? 0 }}
                      </td>
                    </tr>
                  </template>
                  <tr v-if="capacityPreviewGroups.length === 0">
                    <td colspan="5" class="empty-cell">尚無站點需求資料</td>
                  </tr>
                  <tr v-if="hasMoreCapacityRows">
                    <td colspan="5" class="more-row">資料較長，請點右上角查看完整表格。</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <teleport to="body">
            <div v-if="showCapacityDetails" class="modal-backdrop" @click.self="showCapacityDetails = false">
              <div class="modal-card">
                <div class="modal-head">
                  <div>
                    <h3>完整最大可開站數</h3>
                    <p>{{ modelQuery?.model_name || "-" }}</p>
                  </div>
                  <button class="outline-btn mini-btn" type="button" @click="showCapacityDetails = false">關閉</button>
                </div>
                <div class="table-section modal-table-wrap">
                  <table class="data-table detail-table">
                    <thead>
                      <tr>
                        <th>站點</th>
                        <th>治具</th>
                        <th>數量</th>
                        <th>庫存數量</th>
                        <th>站點最大可開站數</th>
                      </tr>
                    </thead>
                    <tbody>
                      <template v-for="group in stationRequirementGroups" :key="group.station_id">
                        <tr v-for="(row, index) in group.rows" :key="`${group.station_id}-${row.fixture_id}`">
                          <td v-if="index === 0" :rowspan="group.rows.length" class="station-cell">{{ group.station_code }}</td>
                          <td>{{ row.fixture_code }}</td>
                          <td>{{ row.required_qty }}</td>
                          <td>{{ row.stock_qty }}</td>
                          <td v-if="index === 0" :rowspan="group.rows.length" class="capacity-cell">
                            {{ stationCapacityById.get(row.station_id) ?? 0 }}
                          </td>
                        </tr>
                      </template>
                      <tr v-if="stationRequirementGroups.length === 0">
                        <td colspan="5" class="empty-cell">尚無站點需求資料</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </teleport>
        </template>
      </article>

      <article class="detail-panel">
        <div class="panel-title inline-title">
          <div>
            <h2>治具資訊</h2>
            <p>{{ selectedFixtureCode || "-" }}</p>
          </div>
          <span class="status-pill" :class="statusClass">{{ statusLabel }}</span>
        </div>

        <div class="image-box">
          <img v-if="currentImage" :src="currentImage" alt="fixture" @error="imageLoadFailed = true" />
          <div v-else class="img-placeholder">在 `FIXTURE_IMAGE_DIR` 放入同名圖片即可</div>
        </div>

        <div class="detail-grid">
          <div class="meta-card">
            <span>治具庫存</span>
            <strong>{{ selectedStock?.stock_qty ?? 0 }}</strong>
          </div>
          <div class="meta-card">
            <span>最低水位</span>
            <strong>{{ selectedStock?.min_stock_qty ?? 0 }}</strong>
          </div>
        </div>

        <div class="meta-block">
          <h3>治具圖片資訊</h3>
          <p><strong>儲位：</strong>{{ selectedLocation }}</p>
        </div>

        <div class="meta-block">
          <h3>使用機種</h3>
          <div class="tag-list">
            <span v-for="tag in selectedModels" :key="tag">{{ tag }}</span>
            <span v-if="selectedModels.length === 0">-</span>
          </div>
        </div>

        <div class="meta-block">
          <h3>最近異動</h3>
          <ul class="timeline">
            <li v-for="item in latestEvents" :key="item.id">
              <span>{{ item.date }} {{ modeLabel(item.type) }}</span>
              <strong :class="item.type === 'receipt' ? 'gain' : 'loss'">
                {{ item.type === "receipt" ? "+" : "-" }}{{ item.qty }} pcs
              </strong>
            </li>
            <li v-if="latestEvents.length === 0">
              <span>尚無異動資料</span>
            </li>
          </ul>
        </div>
      </article>
    </section>
  </div>
</template>

<style scoped>
.search-shell {
  height: 100%;
  overflow: hidden;
  padding: 8px;
  background: #fff;
}

.search-status-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  background: #f3f7ff;
  border: 1px solid #d7e3fb;
  color: #39507e;
  font-size: 12px;
  font-weight: 700;
}

.search-status-strip span {
  padding: 2px 8px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid #dbe4f5;
}

.loading-banner,
.empty-banner {
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px dashed #c9d8f6;
  background: #f7faff;
  color: #617492;
  font-size: 12px;
}

.toggle-btn {
  margin-top: 10px;
}

.collapsed-filter-tip {
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px dashed #c9d8f6;
  background: #fbfdff;
  color: #617492;
  font-size: 12px;
}

.workspace {
  display: grid;
  grid-template-columns: 240px minmax(0, 1.04fr) minmax(300px, 0.92fr);
  gap: 8px;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.query-panel,
.result-panel,
.detail-panel {
  min-width: 0;
  min-height: 0;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
  padding: 10px;
  overflow: auto;
}

.result-panel,
.detail-panel {
  display: grid;
  grid-template-rows: auto auto 1fr auto;
  gap: 12px;
}

.panel-title h2,
.sub-head h3 {
  margin: 0;
  color: #22314a;
  font-size: 16px;
}

.panel-title p {
  margin: 3px 0 0;
  color: var(--muted);
  font-size: 12px;
}

.model-headline {
  align-items: center;
}

.model-name-badge {
  border: 1px solid #d7e2f5;
  border-radius: 999px;
  background: #f7faff;
  color: #1f3b66;
  font-weight: 800;
  padding: 8px 14px;
  white-space: nowrap;
}

.compact-box {
  gap: 12px;
}

.model-tabs {
  display: flex;
  gap: 8px;
  border-bottom: 1px solid var(--line);
  padding-bottom: 10px;
}

.tab-btn {
  border: 1px solid var(--line-strong);
  border-bottom-color: #dfe6f2;
  border-radius: 8px;
  background: #fff;
  color: #5a6578;
  padding: 9px 14px;
  font-weight: 700;
  cursor: pointer;
}

.tab-btn.active {
  background: #111827;
  color: #fff;
  border-color: #111827;
}

.basic-info {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.basic-row {
  display: grid;
  gap: 6px;
}

.basic-row span {
  color: #56657f;
  font-size: 12px;
  font-weight: 700;
}

.basic-row strong {
  color: #162033;
  font-size: 18px;
  font-weight: 800;
}

.section-box {
  display: grid;
  gap: 10px;
}

.compact-section {
  display: grid;
  gap: 4px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}

.section-header h3 {
  margin: 0;
  color: #22314a;
  font-size: 15px;
}

.section-header p {
  margin: 2px 0 0;
  color: var(--muted);
  font-size: 10px;
}

.station-pill-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.station-pill {
  border: 1px solid #92e7b0;
  border-radius: 8px;
  background: #f0fff5;
  padding: 6px 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  min-height: 0;
  flex: 1 1 120px;
  min-width: 110px;
}

.station-pill span {
  color: #19733c;
  font-weight: 800;
  font-size: 12px;
  line-height: 1;
  white-space: nowrap;
}

.station-pill strong {
  color: #15803d;
  font-size: 15px;
  line-height: 1;
}

.capacity-cell {
  font-weight: 800;
  color: #15803d;
  vertical-align: middle;
  text-align: center;
  background: #f5fff8;
}

.mini-btn {
  width: auto;
  min-height: 32px;
  padding: 6px 10px;
}

.detail-table th,
.detail-table td {
  font-size: 13px;
}

.compact-detail-table th,
.compact-detail-table td {
  padding-top: 3px;
  padding-bottom: 3px;
}

.station-cell {
  font-weight: 800;
  color: #22314a;
  vertical-align: top;
  background: #fff;
}

.more-row {
  text-align: center;
  color: var(--muted);
  background: #f8fafe;
  font-size: 12px;
}

.inline-title {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}

.query-mode-list {
  display: grid;
  gap: 6px;
  margin-top: 10px;
}

.radio-card {
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #f8fafe;
  padding: 7px 10px;
  color: #344562;
  font-weight: 700;
}

.radio-card input {
  width: auto;
  margin: 0;
}

.search-form {
  display: grid;
  gap: 8px;
  margin-top: 10px;
}

.search-form label {
  display: grid;
  gap: 6px;
}

.search-form span {
  color: #56657f;
  font-size: 12px;
  font-weight: 700;
}

input {
  width: 100%;
  border: 1px solid var(--line-strong);
  border-radius: 8px;
  padding: 8px 10px;
  background: #fff;
}

.primary-btn,
.ghost-btn {
  border-radius: 10px;
  font-weight: 700;
  cursor: pointer;
  min-height: 36px;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease, filter 0.15s ease;
}

.primary-btn {
  border: 1px solid var(--green);
  background: linear-gradient(180deg, #4cc36b 0%, #2ea54e 100%);
  color: #fff;
  padding: 8px 14px;
  box-shadow: 0 8px 18px rgba(46, 165, 78, 0.18);
}

.common-models {
  margin-top: 10px;
  border-top: 1px solid var(--line);
  padding-top: 10px;
}

.sub-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.sub-head span {
  color: var(--muted);
  font-size: 12px;
}

.common-models {
  margin-top: 10px;
  border-top: 1px solid var(--line);
  padding-top: 10px;
}

.common-model-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
}

.ghost-btn {
  border: 1px solid var(--line-strong);
  background: linear-gradient(180deg, #ffffff 0%, #f7f9fd 100%);
  color: #5b677d;
  padding: 8px 12px;
  border-radius: 10px;
  font-weight: 700;
  cursor: pointer;
  min-height: 36px;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease, filter 0.15s ease;
}

.ghost-btn.selected {
  border-color: #a9c3f9;
  background: linear-gradient(180deg, #eff5ff 0%, #e3eeff 100%);
  color: var(--green);
}

.primary-btn:hover,
.ghost-btn:hover {
  transform: translateY(-1px);
}

.primary-btn:hover {
  box-shadow: 0 10px 22px rgba(46, 165, 78, 0.24);
  filter: brightness(1.02);
}

.ghost-btn:hover {
  border-color: #c0cad9;
  box-shadow: 0 4px 12px rgba(28, 47, 84, 0.08);
}

.primary-btn:active,
.ghost-btn:active {
  transform: translateY(0);
}

.kpi-strip,
.model-summary,
.detail-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.kpi-card,
.summary-card,
.meta-card {
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #f8fafe;
  padding: 6px 8px;
  display: grid;
  gap: 4px;
}

.kpi-card span,
.summary-card span,
.meta-card span {
  color: var(--muted);
  font-size: 12px;
}

.kpi-card strong,
.summary-card strong,
.meta-card strong {
  color: #22314a;
  font-size: 16px;
  line-height: 1.1;
}

.table-section {
  min-height: 0;
  overflow-x: auto;
}

.list-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  color: #5d6d89;
  font-size: 12px;
  margin-top: 8px;
}

.pager-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.data-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border: 1px solid var(--line);
  border-radius: 10px;
  overflow: hidden;
  min-width: 100%;
}

.data-table th,
.data-table td {
  padding: 4px 8px;
  border-bottom: 1px solid var(--line);
  text-align: left;
  font-size: 12px;
}

.data-table th {
  background: #f7f9fd;
  color: #52607b;
  font-weight: 700;
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.data-table tbody tr:hover {
  background: #f6f9ff;
  cursor: pointer;
}

.data-table tbody tr.active {
  background: #edf3ff;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 64px;
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 700;
}

.status-pill.normal {
  color: var(--green);
  background: var(--green-soft);
}

.status-pill.low_stock {
  color: var(--orange);
  background: var(--orange-soft);
}

.status-pill.out_of_stock {
  color: var(--red);
  background: var(--red-soft);
}

.image-box {
  min-height: 180px;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #d9deea;
  background: linear-gradient(180deg, #eef3fb 0%, #dce7fb 100%);
}

.image-box img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.img-placeholder {
  height: 100%;
  display: grid;
  place-items: center;
  color: #8391ab;
  font-size: 12px;
}

.meta-block h3 {
  margin: 0 0 6px;
  color: #22314a;
  font-size: 13px;
}

.meta-block p {
  margin: 0;
  color: #4e5d78;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag-list span {
  border: 1px solid #c9d8f6;
  background: #eaf1ff;
  color: #3f67af;
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 11px;
}

.timeline {
  list-style: none;
  margin: 0;
  padding: 0;
}

.timeline li {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding: 3px 0;
  border-bottom: 1px solid var(--line);
  color: #4e5d78;
  font-size: 12px;
}

.timeline li:last-child {
  border-bottom: none;
}

.timeline strong.gain {
  color: var(--green);
}

.timeline strong.loss {
  color: var(--red);
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 120;
  background: rgba(15, 23, 42, 0.36);
  display: grid;
  place-items: center;
  padding: 18px;
}

.modal-card {
  width: min(1180px, 100%);
  max-height: 90vh;
  overflow: hidden;
  border-radius: 16px;
  background: #fff;
  border: 1px solid rgba(148, 163, 184, 0.35);
  box-shadow: 0 24px 80px rgba(15, 23, 42, 0.24);
  display: grid;
  grid-template-rows: auto 1fr;
}

.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 18px 12px;
  border-bottom: 1px solid var(--line);
}

.modal-head h3 {
  margin: 0;
  color: #162033;
  font-size: 18px;
}

.modal-head p {
  margin: 3px 0 0;
  color: var(--muted);
  font-size: 12px;
}

.modal-table-wrap {
  overflow: auto;
  padding: 12px 18px 18px;
}

@media (max-width: 1500px) {
  .workspace {
    grid-template-columns: 1fr;
  }

  .basic-info,
  .station-pill-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .kpi-strip,
  .model-summary,
  .detail-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .search-shell {
    padding: 6px;
  }

  .query-panel,
  .result-panel,
  .detail-panel {
    padding: 10px;
  }

  .inline-title {
    flex-direction: column;
    align-items: stretch;
  }

  .model-headline {
    align-items: flex-start;
  }

  .kpi-strip,
  .model-summary,
  .detail-grid,
  .basic-info,
  .station-pill-grid {
    grid-template-columns: 1fr;
  }

  .model-name-badge {
    width: 100%;
    text-align: center;
  }

  .query-mode-list {
    gap: 6px;
  }

  .radio-card {
    padding: 8px 10px;
  }

  .toggle-btn {
    width: 100%;
  }

  .image-box {
    min-height: 160px;
  }
}

@media (max-width: 640px) {
  .panel-title h2,
  .sub-head h3 {
    font-size: 16px;
  }

  .data-table th,
  .data-table td {
    white-space: nowrap;
  }

  .timeline li {
    flex-direction: column;
    align-items: flex-start;
  }

  .modal-card {
    max-height: 94vh;
  }
}
</style>

