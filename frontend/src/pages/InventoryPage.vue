<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter, type LocationQuery, type LocationQueryRaw } from "vue-router";

import { api } from "@/api";
import { authSession, globalFixtureKeyword, onboardingSandboxMode, selectedCustomerId } from "@/appState";
import InventoryOperationBoard from "@/components/inventory/InventoryOperationBoard.vue";
import InventoryOverviewPanel from "@/components/inventory/InventoryOverviewPanel.vue";
import { pushToast } from "@/toastState";
import type { Fixture, MaterialTransaction, StockSummary, TransactionOverviewPage, TransactionQueryFilters } from "@/types";
import { formatLocalDateKey as formatDateKey } from "@/utils/date";
import { matchesFixtureKeywords, parseFixtureKeywords } from "@/utils/fixtureSearch";

const route = useRoute();
const router = useRouter();
const OVERVIEW_DEFAULT_PAGE_SIZE = 50;
const OVERVIEW_QUERY_KEYS = [
  "transaction_type",
  "date_from",
  "date_to",
  "fixture_code",
  "transaction_no",
  "tracking_code",
  "created_by",
  "page",
  "page_size"
] as const;

const fixtures = ref<Fixture[]>([]);
const stockRows = ref<StockSummary[]>([]);
const alerts = ref<Array<{ fixture_id: number; fixture_code: string; fixture_name: string; stock_qty: number; min_stock_qty: number; stock_status: "low_stock" | "out_of_stock" }>>([]);
const transactions = ref<MaterialTransaction[]>([]);
const overviewPage = ref<TransactionOverviewPage | null>(null);
const overviewLoading = ref(false);
const overviewPageNumber = ref(1);
const overviewPageSize = ref(OVERVIEW_DEFAULT_PAGE_SIZE);

function createOverviewFilters() {
  return {
    transaction_type: "" as "" | "receipt" | "return",
    date_from: "",
    date_to: "",
    fixture_code: "",
    transaction_no: "",
    tracking_code: "",
    created_by: ""
  };
}

const overviewFilters = ref(createOverviewFilters());

const pageMode = computed(() => (route.path.endsWith("/overview") ? "overview" : "operation"));
const canOperateInventory = computed(() => authSession.value?.role !== "guest");
const today = computed(() => formatDateKey(new Date()));
const globalFixtureKeywords = computed(() => parseFixtureKeywords(globalFixtureKeyword.value));

const filteredStockRows = computed(() =>
  stockRows.value.filter((row) => matchesFixtureKeywords(row.fixture_code, globalFixtureKeywords.value))
);
const filteredAlerts = computed(() =>
  alerts.value.filter((row) => matchesFixtureKeywords(row.fixture_code, globalFixtureKeywords.value))
);
const activeFixtureIds = computed(() => new Set(fixtures.value.filter((row) => row.is_active).map((row) => row.id)));
const activeStockRows = computed(() => filteredStockRows.value.filter((row) => activeFixtureIds.value.has(row.fixture_id)));
const totalStockQty = computed(() => filteredStockRows.value.reduce((sum, row) => sum + row.stock_qty, 0));
const outOfStockCount = computed(() => filteredStockRows.value.filter((row) => row.stock_status === "out_of_stock").length);
const activeFixtureCount = computed(() => filteredStockRows.value.filter((row) => row.stock_qty > 0).length);

const recentReceiptRows = computed(() =>
  transactions.value
    .filter((tx) => tx.transaction_type === "receipt")
    .flatMap((tx) =>
      tx.items.map((item, index) => ({
        id: `${tx.id}-${index}`,
        transaction_no: tx.transaction_no,
        fixture_id: item.fixture_id,
        fixture_code: item.fixture_code,
        identifier: item.identifier,
        quantity: item.quantity
      }))
    )
    .filter((row) => matchesFixtureKeywords(row.fixture_code, globalFixtureKeywords.value))
    .slice(0, 6)
);

const recentReturnRows = computed(() =>
  transactions.value
    .filter((tx) => tx.transaction_type === "return")
    .flatMap((tx) =>
      tx.items.map((item, index) => ({
        id: `${tx.id}-${index}`,
        transaction_no: tx.transaction_no,
        fixture_id: item.fixture_id,
        fixture_code: item.fixture_code,
        identifier: item.identifier,
        quantity: item.quantity
      }))
    )
    .filter((row) => matchesFixtureKeywords(row.fixture_code, globalFixtureKeywords.value))
    .slice(0, 6)
);

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

// Keep summary-card rendering shared so inventory only assembles operation metrics.
const inventorySummaryCards = computed(() => [
  { label: "缺料治具", value: outOfStockCount.value, tone: "danger", emphasis: true },
  { label: "低水位", value: filteredAlerts.value.length, tone: "warn", emphasis: true },
  { label: "治具總數", value: totalStockQty.value, tone: "normal", emphasis: false },
  { label: "有庫存治具", value: activeFixtureCount.value, tone: "normal", emphasis: false },
  { label: "今日收料", value: todayReceiptQty.value, tone: "success", emphasis: false },
  { label: "今日退料", value: todayReturnQty.value, tone: "danger", emphasis: false }
]);

const overviewRows = computed(() => overviewPage.value?.items ?? []);
const overviewReturnTo = computed(() => {
  const raw = route.query.return_to;
  if (typeof raw === "string" && raw.startsWith("/")) {
    return raw;
  }
  return "";
});
const overviewBackLabel = computed(() => (overviewReturnTo.value ? "返回來源" : ""));

function readQueryString(value: LocationQuery[string]): string {
  if (typeof value === "string") {
    return value;
  }
  if (Array.isArray(value) && typeof value[0] === "string") {
    return value[0];
  }
  return "";
}

function parsePositivePage(value: string, fallback: number): number {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function parseOverviewPageSize(value: string): number {
  const parsed = Number.parseInt(value, 10);
  return parsed === 100 ? 100 : OVERVIEW_DEFAULT_PAGE_SIZE;
}

function applyOverviewStateFromRoute(query: LocationQuery): boolean {
  const transactionType = (() => {
    const value = readQueryString(query.transaction_type);
    return value === "receipt" || value === "return" ? value : "";
  })() as "" | "receipt" | "return";
  const nextFilters: typeof overviewFilters.value = {
    transaction_type: transactionType,
    date_from: readQueryString(query.date_from),
    date_to: readQueryString(query.date_to),
    fixture_code: readQueryString(query.fixture_code),
    transaction_no: readQueryString(query.transaction_no),
    tracking_code: readQueryString(query.tracking_code),
    created_by: readQueryString(query.created_by)
  };
  const nextPage = parsePositivePage(readQueryString(query.page), 1);
  const nextPageSize = parseOverviewPageSize(readQueryString(query.page_size));

  const changed =
    overviewFilters.value.transaction_type !== nextFilters.transaction_type ||
    overviewFilters.value.date_from !== nextFilters.date_from ||
    overviewFilters.value.date_to !== nextFilters.date_to ||
    overviewFilters.value.fixture_code !== nextFilters.fixture_code ||
    overviewFilters.value.transaction_no !== nextFilters.transaction_no ||
    overviewFilters.value.tracking_code !== nextFilters.tracking_code ||
    overviewFilters.value.created_by !== nextFilters.created_by ||
    overviewPageNumber.value !== nextPage ||
    overviewPageSize.value !== nextPageSize;

  if (!changed) {
    return false;
  }

  overviewFilters.value = nextFilters;
  overviewPageNumber.value = nextPage;
  overviewPageSize.value = nextPageSize;
  return true;
}

function buildOverviewRouteQuery(): LocationQueryRaw {
  const preservedEntries = Object.entries(route.query).filter(([key]) => !OVERVIEW_QUERY_KEYS.includes(key as (typeof OVERVIEW_QUERY_KEYS)[number]));
  const query: LocationQueryRaw = Object.fromEntries(preservedEntries);
  if (overviewFilters.value.transaction_type) query.transaction_type = overviewFilters.value.transaction_type;
  if (overviewFilters.value.date_from) query.date_from = overviewFilters.value.date_from;
  if (overviewFilters.value.date_to) query.date_to = overviewFilters.value.date_to;
  if (overviewFilters.value.fixture_code.trim()) query.fixture_code = overviewFilters.value.fixture_code.trim();
  if (overviewFilters.value.transaction_no.trim()) query.transaction_no = overviewFilters.value.transaction_no.trim();
  if (overviewFilters.value.tracking_code.trim()) query.tracking_code = overviewFilters.value.tracking_code.trim();
  if (overviewFilters.value.created_by.trim()) query.created_by = overviewFilters.value.created_by.trim();
  if (overviewPageNumber.value > 1) query.page = String(overviewPageNumber.value);
  if (overviewPageSize.value !== OVERVIEW_DEFAULT_PAGE_SIZE) query.page_size = String(overviewPageSize.value);
  return query;
}

function serializeQuery(query: LocationQuery | LocationQueryRaw): string {
  return Object.entries(query)
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([key, value]) => {
      if (Array.isArray(value)) {
        return `${key}=${value.join(",")}`;
      }
      return `${key}=${value ?? ""}`;
    })
    .join("&");
}

async function syncOverviewRoute(mode: "push" | "replace" = "push"): Promise<boolean> {
  const nextQuery = buildOverviewRouteQuery();
  if (serializeQuery(route.query) === serializeQuery(nextQuery)) {
    return false;
  }
  await router[mode]({ path: route.path, query: nextQuery });
  return true;
}

async function returnToSource(): Promise<void> {
  if (!overviewReturnTo.value) {
    return;
  }
  await router.push(overviewReturnTo.value);
}

async function loadData(): Promise<void> {
  const customerId = selectedCustomerId.value ?? undefined;
  try {
    const [fixtureRows, stock, alertRows, tx] = await Promise.all([
      api.listFixtures(customerId),
      api.listStock(customerId),
      api.listAlerts(customerId),
      api.listTransactions(40, customerId)
    ]);
    fixtures.value = fixtureRows;
    stockRows.value = stock;
    alerts.value = alertRows;
    transactions.value = tx;
    if (pageMode.value === "overview") {
      await loadOverview();
    }
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "載入收退料資料失敗", "error");
  }
}

function buildOverviewFilters(): TransactionQueryFilters {
  const fixtureKeywords = [...globalFixtureKeywords.value];
  const directFixtureFilter = overviewFilters.value.fixture_code.trim();
  if (directFixtureFilter) {
    fixtureKeywords.unshift(directFixtureFilter);
  }
  return {
    transaction_type: overviewFilters.value.transaction_type || undefined,
    date_from: overviewFilters.value.date_from || undefined,
    date_to: overviewFilters.value.date_to || undefined,
    fixture_code: fixtureKeywords.length > 0 ? fixtureKeywords.join(",") : undefined,
    transaction_no: overviewFilters.value.transaction_no.trim() || undefined,
    identifier: overviewFilters.value.tracking_code.trim() || undefined,
    created_by: overviewFilters.value.created_by.trim() || undefined
  };
}

async function loadOverview(): Promise<void> {
  overviewLoading.value = true;
  try {
    overviewPage.value = await api.listTransactionOverviewPage(
      overviewPageNumber.value,
      overviewPageSize.value,
      selectedCustomerId.value ?? undefined,
      buildOverviewFilters()
    );
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "載入收退料總檢視失敗", "error");
  } finally {
    overviewLoading.value = false;
  }
}

async function handleBatchImportSuccess(): Promise<void> {
  await loadData();
}

async function searchOverview(): Promise<void> {
  if (!selectedCustomerId.value) {
    pushToast("請先在側邊欄選擇客戶。", "warning");
    return;
  }
  overviewPageNumber.value = 1;
  if (!(await syncOverviewRoute("push"))) {
    await loadOverview();
  }
}

async function resetOverviewFilters(): Promise<void> {
  overviewFilters.value = createOverviewFilters();
  overviewPageNumber.value = 1;
  overviewPageSize.value = OVERVIEW_DEFAULT_PAGE_SIZE;
  if (!(await syncOverviewRoute("push"))) {
    await loadOverview();
  }
}

function updateOverviewFilters(value: typeof overviewFilters.value): void {
  overviewFilters.value = value;
}

async function updateOverviewPage(page: number): Promise<void> {
  if (page === overviewPageNumber.value) {
    return;
  }
  overviewPageNumber.value = page;
  if (!(await syncOverviewRoute("push"))) {
    await loadOverview();
  }
}

async function updateOverviewPageSize(pageSize: number): Promise<void> {
  if (pageSize === overviewPageSize.value) {
    return;
  }
  overviewPageSize.value = pageSize;
  overviewPageNumber.value = 1;
  if (!(await syncOverviewRoute("push"))) {
    await loadOverview();
  }
}

onMounted(async () => {
  if (!canOperateInventory.value && pageMode.value === "operation") {
    await router.replace("/inventory/overview");
    return;
  }
  if (pageMode.value === "overview") {
    applyOverviewStateFromRoute(route.query);
  }
  await loadData();
});

watch(selectedCustomerId, async () => {
  overviewPageNumber.value = 1;
  await loadData();
});

watch(globalFixtureKeyword, async () => {
  if (pageMode.value !== "overview") {
    return;
  }
  overviewPageNumber.value = 1;
  await loadOverview();
});

watch(
  () => [canOperateInventory.value, pageMode.value] as const,
  async ([canOperate, mode]) => {
    if (!canOperate && mode === "operation") {
      await router.replace("/inventory/overview");
    }
  }
);

watch(pageMode, async (value) => {
  if (value === "overview") {
    const changed = applyOverviewStateFromRoute(route.query);
    if (changed || !overviewPage.value) {
      await loadOverview();
    }
  }
});

watch(
  () => route.query,
  async (query) => {
    if (pageMode.value !== "overview") {
      return;
    }
    const changed = applyOverviewStateFromRoute(query);
    if (changed || !overviewPage.value) {
      await loadOverview();
    }
  }
);
</script>

<template>
  <div class="inventory-shell">
    <InventoryOperationBoard
      v-if="pageMode === 'operation'"
      :customer-id="selectedCustomerId ?? undefined"
      :tutorial-mode="onboardingSandboxMode"
      :summary-cards="inventorySummaryCards"
      :receipt-rows="recentReceiptRows"
      :return-rows="recentReturnRows"
      :stock-rows="activeStockRows"
      :alert-rows="filteredAlerts"
      @refreshed="handleBatchImportSuccess"
    />

    <InventoryOverviewPanel
      v-else
      :filters="overviewFilters"
      :rows="overviewRows"
      :page="overviewPage?.page ?? overviewPageNumber"
      :page-size="overviewPage?.page_size ?? overviewPageSize"
      :total="overviewPage?.total ?? 0"
      :loading="overviewLoading"
      :back-label="overviewBackLabel"
      @update:filters="updateOverviewFilters"
      @update:page="updateOverviewPage"
      @update:page-size="updateOverviewPageSize"
      @back="returnToSource"
      @search="searchOverview"
      @reset="resetOverviewFilters"
    />
  </div>
</template>

<style scoped>
.inventory-shell {
  height: 100%;
  overflow: hidden;
  padding: 8px;
  background: #fff;
}

@media (max-width: 900px) {
  .inventory-shell {
    padding: 8px;
  }
}
</style>
