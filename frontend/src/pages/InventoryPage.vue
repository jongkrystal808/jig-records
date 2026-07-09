<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "@/api";
import { authSession, globalFixtureKeyword, onboardingSandboxMode, selectedCustomerId } from "@/appState";
import InventoryOperationBoard from "@/components/inventory/InventoryOperationBoard.vue";
import InventoryOverviewPanel from "@/components/inventory/InventoryOverviewPanel.vue";
import { pushToast } from "@/toastState";
import type { Fixture, MaterialTransaction, StockSummary, TransactionQueryFilters } from "@/types";
import { formatLocalDate, formatLocalDateKey as formatDateKey } from "@/utils/date";
import { matchesFixtureKeywords, parseFixtureKeywords } from "@/utils/fixtureSearch";
import { ownershipLabel } from "@/utils/display";

const route = useRoute();
const router = useRouter();

const fixtures = ref<Fixture[]>([]);
const stockRows = ref<StockSummary[]>([]);
const alerts = ref<Array<{ fixture_id: number; fixture_code: string; fixture_name: string; stock_qty: number; min_stock_qty: number; stock_status: "low_stock" | "out_of_stock" }>>([]);
const transactions = ref<MaterialTransaction[]>([]);
const overviewTransactions = ref<MaterialTransaction[]>([]);
const overviewLoading = ref(false);

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
        fixture_code: item.fixture_code,
        identifier: item.identifier,
        quantity: item.quantity
      }))
    )
    .filter((row) => matchesFixtureKeywords(row.fixture_code, globalFixtureKeywords.value))
    .slice(0, 6)
);

const todayReceiptQty = computed(() =>
  overviewTransactions.value
    .filter((tx) => tx.transaction_type === "receipt" && formatDateKey(new Date(tx.occurred_at)) === today.value)
    .reduce((sum, tx) => sum + tx.items.reduce((itemSum, item) => itemSum + item.quantity, 0), 0)
);

const todayReturnQty = computed(() =>
  overviewTransactions.value
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

const overviewRows = computed(() =>
  overviewTransactions.value
    .flatMap((tx) =>
      tx.items.map((item, index) => ({
        id: `${tx.id}-${index}`,
        transaction_type: tx.transaction_type,
        transaction_no: tx.transaction_no,
        occurred_at: tx.occurred_at,
        created_by: tx.created_by,
        fixture_code: item.fixture_code,
        fixture_name: item.fixture_name,
        ownership_type: item.ownership_type,
        identifier: item.identifier,
        quantity: item.quantity,
        note: item.note || tx.note || "",
        ownership_label: ownershipLabel(item.ownership_type),
        occurred_at_label: formatLocalDate(tx.occurred_at)
      }))
    )
    .filter((row) => matchesFixtureKeywords(row.fixture_code, globalFixtureKeywords.value))
);

function downloadCsv(filename: string, content: string): void {
  const blob = new Blob([content], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
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
  return {
    transaction_type: overviewFilters.value.transaction_type || undefined,
    date_from: overviewFilters.value.date_from || undefined,
    date_to: overviewFilters.value.date_to || undefined,
    fixture_code: overviewFilters.value.fixture_code.trim() || undefined,
    transaction_no: overviewFilters.value.transaction_no.trim() || undefined,
    identifier: overviewFilters.value.tracking_code.trim() || undefined,
    created_by: overviewFilters.value.created_by.trim() || undefined
  };
}

async function loadOverview(): Promise<void> {
  overviewLoading.value = true;
  try {
    overviewTransactions.value = await api.listTransactions(200, selectedCustomerId.value ?? undefined, buildOverviewFilters());
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
  await loadOverview();
}

async function resetOverviewFilters(): Promise<void> {
  overviewFilters.value = createOverviewFilters();
  await loadOverview();
}

async function exportOverviewCsv(): Promise<void> {
  if (!selectedCustomerId.value) {
    pushToast("請先在側邊欄選擇客戶。", "warning");
    return;
  }
  try {
    const customerId = selectedCustomerId.value ?? undefined;
    downloadCsv("transactions.csv", await api.exportTransactionsCsv(5000, customerId, buildOverviewFilters()));
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "匯出失敗", "error");
  }
}

function updateOverviewFilters(value: typeof overviewFilters.value): void {
  overviewFilters.value = value;
}

onMounted(async () => {
  if (!canOperateInventory.value && pageMode.value === "operation") {
    await router.replace("/inventory/overview");
    return;
  }
  await loadData();
});

watch(selectedCustomerId, async () => {
  await loadData();
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
  if (value === "overview" && overviewTransactions.value.length === 0) {
    await loadOverview();
  }
});
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
      :loading="overviewLoading"
      @update:filters="updateOverviewFilters"
      @search="searchOverview"
      @reset="resetOverviewFilters"
      @export="exportOverviewCsv"
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
