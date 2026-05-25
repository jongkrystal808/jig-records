<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { api } from "@/api";
import type { FixtureImage, MaterialTransaction, SearchResult, StockSummary } from "@/types";

type Mode = "receipt" | "return" | "fixture" | "model";

const mode = ref<Mode>("fixture");
const query = ref("C-00003");
const loading = ref(false);
const error = ref("");

const stockRows = ref<StockSummary[]>([]);
const transactions = ref<MaterialTransaction[]>([]);
const searchResults = ref<SearchResult[]>([]);
const images = ref<FixtureImage[]>([]);
const selectedFixtureCode = ref("");

const selectedStock = computed(() => stockRows.value.find((row) => row.fixture_code === selectedFixtureCode.value) ?? null);

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
  const matched = searchResults.value.find((item) => item.title.startsWith(selectedFixtureCode.value));
  const subtitle = matched?.subtitle || "";
  if (!subtitle || subtitle === "Fixture") return [];
  return subtitle
    .split(/[\/,]/)
    .map((item) => item.trim())
    .filter(Boolean);
});

const currentImage = computed(() => {
  const main = images.value.find((item) => item.is_main) ?? images.value[0];
  return main?.thumbnail_path || main?.image_path || "";
});

const lowStockCount = computed(
  () => stockRows.value.filter((row) => row.stock_status === "low_stock" || row.stock_status === "out_of_stock").length
);

const totalFixtureQty = computed(() => stockRows.value.reduce((sum, row) => sum + row.stock_qty, 0));

const todayReceiptQty = computed(() => {
  const today = new Date().toISOString().slice(0, 10);
  return transactions.value
    .filter((tx) => tx.transaction_type === "receipt" && tx.created_at.startsWith(today))
    .reduce((sum, tx) => sum + tx.items.reduce((itemSum, item) => itemSum + item.qty, 0), 0);
});

const todayReturnQty = computed(() => {
  const today = new Date().toISOString().slice(0, 10);
  return transactions.value
    .filter((tx) => tx.transaction_type === "return" && tx.created_at.startsWith(today))
    .reduce((sum, tx) => sum + tx.items.reduce((itemSum, item) => itemSum + item.qty, 0), 0);
});

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

  return rows.slice(0, 8);
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
    const qty = tx.items.reduce((sum, item) => sum + item.qty, 0);
    return {
      id: tx.id,
      date: new Date(tx.created_at).toLocaleDateString("zh-TW"),
      type: tx.transaction_type,
      qty
    };
  })
);

function pickFixture(code: string): void {
  selectedFixtureCode.value = code;
  const fixtureRow = stockRows.value.find((row) => row.fixture_code === code);
  if (fixtureRow) {
    void loadFixtureImages(fixtureRow.fixture_id);
  }
}

async function loadFixtureImages(fixtureId: number): Promise<void> {
  try {
    images.value = await api.listFixtureImages(fixtureId);
  } catch {
    images.value = [];
  }
}

async function doSearch(): Promise<void> {
  const q = query.value.trim();
  if (!q) {
    searchResults.value = [];
    return;
  }

  loading.value = true;
  error.value = "";
  try {
    const rows = await api.globalSearch(q);
    if (mode.value === "fixture") {
      searchResults.value = rows.filter((item) => item.entity_type === "fixture" || item.entity_type === "serial");
    } else if (mode.value === "model") {
      searchResults.value = rows.filter((item) => item.entity_type === "model");
    } else {
      searchResults.value = rows;
    }

    const firstFixture = searchResults.value.find((item) => item.entity_type === "fixture");
    if (firstFixture) {
      selectedFixtureCode.value = firstFixture.title.split(" - ")[0] ?? "";
      await loadFixtureImages(firstFixture.reference_id);
    } else {
      selectedFixtureCode.value = "";
      images.value = [];
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : "查詢失敗";
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  try {
    const [stock, tx] = await Promise.all([api.listStock(), api.listTransactions(40)]);
    stockRows.value = stock;
    transactions.value = tx;
    selectedFixtureCode.value = stock[0]?.fixture_code ?? "";
    if (stock[0]) {
      await loadFixtureImages(stock[0].fixture_id);
    }
    await doSearch();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "初始化失敗";
  }
});

watch(mode, () => {
  void doSearch();
});
</script>

<template>
  <div class="page-wrap">
    <div class="workspace">
      <aside class="sidebar">
        <div class="side-head">
          <div class="logo-dot">◎</div>
          <strong>治具管理系統</strong>
        </div>

        <div class="menu-block">
          <p class="menu-title">功能選單</p>
          <button class="menu-item" :class="{ active: mode === 'receipt' }" @click="mode = 'receipt'">收料</button>
          <button class="menu-item" :class="{ active: mode === 'return' }" @click="mode = 'return'">退料</button>
          <button class="menu-item" :class="{ active: mode === 'fixture' }" @click="mode = 'fixture'">治具查詢</button>
          <button class="menu-item" :class="{ active: mode === 'model' }" @click="mode = 'model'">機種查詢</button>
        </div>

        <div class="menu-block">
          <p class="menu-title">快速資訊</p>
          <p class="quick-row"><span>今日收料</span><strong>{{ todayReceiptQty }} pcs</strong></p>
          <p class="quick-row"><span>今日退料</span><strong>{{ todayReturnQty }} pcs</strong></p>
          <p class="quick-row warn"><span>低於水位</span><strong>{{ lowStockCount }} pcs</strong></p>
        </div>

        <button class="logout-btn">登出</button>
      </aside>

      <section class="query-panel">
        <h3>查詢條件</h3>
        <label><input v-model="mode" value="receipt" type="radio" /> 收料</label>
        <label><input v-model="mode" value="return" type="radio" /> 退料</label>
        <label><input v-model="mode" value="fixture" type="radio" /> 查詢治具</label>
        <label><input v-model="mode" value="model" type="radio" /> 查詢機種</label>

        <form class="search-form" @submit.prevent="doSearch">
          <p class="hint">治具編號 / 治具名稱 / 流水號</p>
          <input v-model="query" placeholder="C-00003" />
          <button type="submit">查詢</button>
        </form>
        <p v-if="loading" class="hint">查詢中...</p>
        <p v-if="error" class="error">{{ error }}</p>
      </section>

      <main class="result-panel">
        <h2>查詢結果 <span class="soft">{{ selectedFixtureCode || "NET RJ45-8P8C" }}</span></h2>

        <div class="kpi-grid">
          <article class="kpi-card">
            <p>現有治具</p>
            <strong>{{ totalFixtureQty }}</strong>
            <span>pcs</span>
          </article>
          <article class="kpi-card">
            <p>低於水位</p>
            <strong>{{ lowStockCount }}</strong>
            <span>pcs</span>
          </article>
          <article class="kpi-card">
            <p>今日收料</p>
            <strong>{{ todayReceiptQty }}</strong>
            <span>pcs</span>
          </article>
          <article class="kpi-card">
            <p>今日退料</p>
            <strong>{{ todayReturnQty }}</strong>
            <span>pcs</span>
          </article>
        </div>

        <div class="table-head">
          <h3>現有治具列表</h3>
          <button class="ghost-btn">匯出</button>
        </div>

        <table class="data-table">
          <thead>
            <tr>
              <th>治具編號 + 流水號</th>
              <th>數量</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in displayRows"
              :key="row.fixture_id"
              :class="{ active: row.fixture_code === selectedFixtureCode }"
              @click="pickFixture(row.fixture_code)"
            >
              <td>{{ row.fixture_code }}</td>
              <td>{{ row.stock_qty }} pcs</td>
            </tr>
          </tbody>
        </table>

        <h3 class="mt">收料紀錄</h3>
        <table class="data-table">
          <thead>
            <tr>
              <th>治具編號</th>
              <th>數量</th>
              <th>派發單號</th>
              <th>日期</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="tx in selectedTransactions" :key="tx.id">
              <td>{{ tx.items[0]?.fixture_code || "-" }}</td>
              <td>{{ tx.items.reduce((sum, item) => sum + item.qty, 0) }} pcs</td>
              <td>{{ tx.note || "-" }}</td>
              <td>{{ new Date(tx.created_at).toLocaleString("zh-TW") }}</td>
            </tr>
          </tbody>
        </table>
      </main>

      <aside class="detail-panel">
        <h3>治具詳細資訊</h3>
        <div class="detail-top">
          <h2>{{ selectedFixtureCode || "NET RJ45-8P8C" }}</h2>
          <span class="status" :class="statusClass">{{ statusLabel }}</span>
        </div>

        <div class="image-box">
          <img v-if="currentImage" :src="currentImage" alt="fixture" />
          <div v-else class="img-placeholder">查詢後顯示圖片</div>
        </div>

        <div class="meta-block">
          <p><strong>儲位</strong></p>
          <p>{{ selectedLocation }}</p>
        </div>

        <div class="meta-block">
          <p><strong>使用機種</strong></p>
          <div class="tag-list">
            <span v-for="tag in selectedModels" :key="tag">{{ tag }}</span>
            <span v-if="selectedModels.length === 0">-</span>
          </div>
        </div>

        <div class="meta-block">
          <p><strong>最近異動</strong></p>
          <ul class="timeline">
            <li v-for="item in latestEvents" :key="item.id">
              <span>{{ item.date }} {{ item.type === "receipt" ? "收料" : "退料" }}</span>
              <strong :class="item.type === 'receipt' ? 'gain' : 'loss'">
                {{ item.type === "receipt" ? "+" : "-" }}{{ item.qty }} pcs
              </strong>
            </li>
          </ul>
        </div>
      </aside>
    </div>
  </div>
</template>
