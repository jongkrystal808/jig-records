<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "@/api";
import {
  authSession,
  customers,
  requestInventoryBatchOpen,
  selectedCustomerId
} from "@/appState";
import FixtureImageDialog from "@/components/inventory/FixtureImageDialog.vue";
import InventoryReportFilters from "@/components/inventory/InventoryReportFilters.vue";
import type { InventoryReportMobileRow } from "@/components/inventory/InventoryReportMobileCards.vue";
import InventoryReportResults from "@/components/inventory/InventoryReportResults.vue";
import {
  createEmptyTransactionFilters,
  linkedFilterKeys,
  useConfigurationReportState,
  type FixtureStatusFilter,
  type LinkedFilterKey,
  type WaterFilter
} from "@/composables/useConfigurationReportState";
import { pushToast } from "@/toastState";
import type {
  ConfigurationReportOption,
  ModelQueryStationRequirement,
  StationCapacity,
  TransactionOverviewRow
} from "@/types";
import {
  groupReportTransactionDetails
} from "@/utils/reportTransactionDetails";
import type { ReportTransactionMode } from "@/utils/reportTransactionFilters";
import {
  orderReportColumns,
  REPORT_COLUMN_DEFINITIONS,
  REPORT_COLUMN_PRESETS,
  reportColumnPreset,
  reportColumnPresetKey,
  type ReportColumnKey,
  type ReportColumnPresetKey
} from "@/utils/reportColumnPresets";
import {
  autoHiddenReportColumns,
  effectiveReportColumns
} from "@/utils/reportVisibleColumns";
import { scrollReportResultsIntoView } from "@/utils/scrollReportResults";
import { uiSurfaceRouteQuery } from "@/utils/uiSurface";
import { canOperate } from "@/utils/roles";

const props = withDefaults(defineProps<{
  hideHeading?: boolean;
  embeddedShell?: boolean;
}>(), {
  hideHeading: false,
  embeddedShell: false
});

const reportResultsComponent = ref<InstanceType<typeof InventoryReportResults> | null>(null);
const canOperateFixtures = computed(() => canOperate(authSession.value?.role));

type WaterStatus = "normal" | "low" | "empty" | "na";
type FilterChip = {
  key: string;
  label: string;
  value: string;
};

type ReportRow = InventoryReportMobileRow;

function isMobileReportViewport(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(max-width: 680px)").matches
  );
}

const route = useRoute();
const router = useRouter();
const isMobileReportMode = ref(isMobileReportViewport());
const {
  draftFilters,
  appliedFilters,
  draftTransactionFilters,
  appliedTransactionFilters,
  filterOrder,
  page,
  pageSize,
  jumpPage,
  routeSyncing,
  exportFormat,
  exportFeedbackMessage,
  exportLoading,
  usesTransactionDateRange,
  transactionDateValidationMessage,
  activeFilterCount,
  pendingFilterCount,
  hasPendingFilters,
  buildReportApiQuery,
  syncRoute,
  applyRouteState: applyConfigurationRouteState,
  resetFilterState,
  commitDraftFilters,
  transactionFiltersAreValid,
  exportFilteredRows: exportConfigurationReportRows
} = useConfigurationReportState({ route, router, isMobileReportMode });

const fixtures = ref<ConfigurationReportOption[]>([]);
const models = ref<ConfigurationReportOption[]>([]);
const stations = ref<ConfigurationReportOption[]>([]);
const availableWaterStatuses = ref<Set<WaterStatus>>(new Set());
const serverRows = ref<ReportRow[]>([]);
const populatedColumns = ref<ReportColumnKey[]>([]);
const reportTotal = ref(0);
const fixtureCount = ref(0);
const attentionFixtureCount = ref(0);
const missingConfigurationCount = ref(0);
const totalStockQty = ref(0);
const customerSuppliedQty = ref(0);
const selfPurchasedQty = ref(0);
const loading = ref(false);
const loadError = ref("");
const capacityLoading = ref(false);
const capacityResults = ref<StationCapacity[]>([]);
const capacityRequirementsByStationId = ref<Map<number, ModelQueryStationRequirement[]>>(
  new Map()
);
const expandedBottleneckStationIds = ref<Set<number>>(new Set());
const transactionFilterLoading = ref(false);
const transactionDetailsByFixtureCode = ref<Map<string, TransactionOverviewRow[]>>(new Map());
const showTransactionDetails = ref(false);
const fixtureImageOpen = ref(false);
const fixtureImageCode = ref("");
const fixtureImageName = ref("");
const filterPanelCollapsed = ref(isMobileReportViewport());
const COLUMN_PREFERENCE_KEY = "guest-inventory-report-columns-v2";
let reportRequestId = 0;
let optionsRequestId = 0;
let optionsRefreshTimer: ReturnType<typeof setTimeout> | null = null;
const columnPickerOpen = ref(false);

const columnDefinitions = REPORT_COLUMN_DEFINITIONS;
const columnPresets = REPORT_COLUMN_PRESETS;
const visibleColumns = ref<ReportColumnKey[]>(reportColumnPreset("full"));

const linkedFilterLabels: Record<LinkedFilterKey, string> = {
  keyword: "關鍵字",
  fixtureId: "治具",
  stationId: "站點",
  modelId: "機種",
  waterStatus: "水位狀態",
  storage: "儲位",
  configurationStatus: "配置狀態"
};

const currentCustomer = computed(
  () => customers.value.find((customer) => customer.id === selectedCustomerId.value) ?? null
);

const availableFixtures = computed(() => fixtures.value);
const availableModels = computed(() => models.value);
const availableStations = computed(() => stations.value);

function linkedFilterValueLabel(key: LinkedFilterKey, value: string): string {
  if ((key === "waterStatus" || key === "configurationStatus") && value.includes(",")) {
    return value.split(",").map((item) => linkedFilterValueLabel(key, item)).join("＋");
  }
  if (key === "fixtureId") {
    return fixtures.value.find((fixture) => fixture.id === Number(value))?.code ?? value;
  }
  if (key === "modelId") {
    return models.value.find((model) => model.id === Number(value))?.code ?? value;
  }
  if (key === "stationId") {
    return stations.value.find((station) => station.id === Number(value))?.code ?? value;
  }
  if (key === "waterStatus") {
    return {
      attention: "低水位與缺料",
      low: "低水位",
      empty: "缺料",
      normal: "正常"
    }[value] ?? value;
  }
  if (key === "configurationStatus") return value === "unconfigured" ? "未配置" : value;
  return value;
}

const orderedDraftFilterChips = computed<FilterChip[]>(() =>
  filterOrder.value
    .filter((key) => String(draftFilters[key]).trim())
    .map((key) => ({
      key,
      label: linkedFilterLabels[key],
      value: linkedFilterValueLabel(key, String(draftFilters[key]))
    }))
);

const appliedFilterChips = computed<FilterChip[]>(() => {
  const fixtureStatusLabels: Record<FixtureStatusFilter, string> = {
    active: "已啟用",
    inactive: "已停用"
  };
  const chips: FilterChip[] = [{
    key: "fixtureStatus",
    label: "治具狀態",
    value: appliedFilters.fixtureStatus.map((value) => fixtureStatusLabels[value]).join("＋") || "所有治具"
  }, ...linkedFilterKeys
    .filter((key) => String(appliedFilters[key]).trim())
    .map((key) => ({
      key,
      label: linkedFilterLabels[key],
      value: linkedFilterValueLabel(key, String(appliedFilters[key]))
    }))];
  const transactionLabels: Record<Exclude<ReportTransactionMode, "">, string> = {
    today_receipt: "今日收料",
    today_return: "今日退料",
    range_receipt: "指定日期收料",
    range_return: "指定日期退料"
  };
  const transactionMode = appliedTransactionFilters.mode;
  if (transactionMode) {
    const isRange = transactionMode.startsWith("range");
    chips.push({
      key: "transactionActivity",
      label: "收退料",
      value: isRange
        ? `${transactionLabels[transactionMode]} ${appliedTransactionFilters.dateFrom}～${appliedTransactionFilters.dateTo}`
        : transactionLabels[transactionMode]
    });
    if (appliedTransactionFilters.ownershipType.length) {
      chips.push({
        key: "transactionOwnership",
        label: "交易來源",
        value: appliedTransactionFilters.ownershipType
          .map((value) => value === "customer_supplied" ? "客供" : "自購")
          .join("＋")
      });
    }
  }
  return chips;
});

function waterOptionAvailable(value: WaterFilter): boolean {
  if (value === "attention") {
    return availableWaterStatuses.value.has("low") || availableWaterStatuses.value.has("empty");
  }
  return availableWaterStatuses.value.has(value);
}

function optionStillAvailable(key: LinkedFilterKey, value: string): boolean {
  if (key === "fixtureId") return fixtures.value.some((row) => String(row.id) === value);
  if (key === "modelId") return models.value.some((row) => String(row.id) === value);
  if (key === "stationId") return stations.value.some((row) => String(row.id) === value);
  if (key === "waterStatus") return value.split(",").every((item) => waterOptionAvailable(item as WaterFilter));
  return true;
}

function reconcileLinkedFilters(changedKey: LinkedFilterKey): boolean {
  const changedIndex = filterOrder.value.indexOf(changedKey);
  if (changedIndex < 0) return false;
  const downstreamKeys = filterOrder.value.slice(changedIndex + 1);
  const selectKeys: LinkedFilterKey[] = [
    "fixtureId",
    "modelId",
    "stationId",
    "waterStatus"
  ];
  let changed = false;
  downstreamKeys.forEach((key) => {
    if (!selectKeys.includes(key) || !draftFilters[key]) return;
    if (optionStillAvailable(key, String(draftFilters[key]))) return;
    draftFilters[key] = (key === "waterStatus" || key === "configurationStatus" ? [] : "") as never;
    filterOrder.value = filterOrder.value.filter((entry) => entry !== key);
    changed = true;
  });
  return changed;
}

function handleDraftFilterChange(key: LinkedFilterKey): void {
  if (key === "modelId" || key === "stationId") closeCapacityResults();
  const hasValue = String(draftFilters[key]).trim().length > 0;
  if (!hasValue) {
    filterOrder.value = filterOrder.value.filter((entry) => entry !== key);
    void refreshReportOptions();
    return;
  }
  if (!filterOrder.value.includes(key)) {
    filterOrder.value = [...filterOrder.value, key];
  }
  void refreshReportOptions(key);
}

function handleFixtureStatusChange(): void {
  closeCapacityResults();
  refreshReportOptions(undefined, true);
}

function removeDraftFilter(rawKey: string): void {
  const key = rawKey as LinkedFilterKey;
  if (!linkedFilterKeys.includes(key)) return;
  draftFilters[key] = (key === "waterStatus" || key === "configurationStatus" ? [] : "") as never;
  filterOrder.value = filterOrder.value.filter((entry) => entry !== key);
  if (key === "modelId" || key === "stationId") closeCapacityResults();
  void refreshReportOptions();
}

const totalPages = computed(() => Math.max(1, Math.ceil(reportTotal.value / pageSize.value)));
const pageSizeOptions = computed<Array<20 | 50 | 100>>(() =>
  isMobileReportMode.value ? [20, 50] : [50, 100]
);
const pagedRows = computed(() => serverRows.value);
const transactionDetailCount = ref(0);
const pageStart = computed(() =>
  reportTotal.value ? (page.value - 1) * pageSize.value + 1 : 0
);
const pageEnd = computed(() => Math.min(page.value * pageSize.value, reportTotal.value));
const canCalculateCapacity = computed(
  () =>
    Boolean(selectedCustomerId.value) &&
    Boolean(appliedFilters.modelId) &&
    !hasPendingFilters.value &&
    !loading.value
);
const canRunSearch = computed(
  () =>
    Boolean(selectedCustomerId.value) &&
    hasPendingFilters.value &&
    !loading.value &&
    !transactionFilterLoading.value &&
    !transactionDateValidationMessage.value
);
const effectiveVisibleColumns = computed(() =>
  effectiveReportColumns(
    visibleColumns.value,
    populatedColumns.value,
    reportTotal.value
  )
);
const autoHiddenColumns = computed(() =>
  autoHiddenReportColumns(visibleColumns.value, effectiveVisibleColumns.value)
);
const visibleColumnCount = computed(() => effectiveVisibleColumns.value.length);
const tableMinWidth = computed(() => `${Math.max(720, visibleColumnCount.value * 108)}px`);
const selectedColumnPreset = computed(() => reportColumnPresetKey(visibleColumns.value));
const selectedColumnPresetLabel = computed(
  () =>
    columnPresets.find((preset) => preset.key === selectedColumnPreset.value)?.label ??
    "自訂欄位"
);
function isColumnSelected(key: ReportColumnKey): boolean {
  return visibleColumns.value.includes(key);
}

function persistColumnPreference(): void {
  try {
    window.localStorage.setItem(COLUMN_PREFERENCE_KEY, JSON.stringify(visibleColumns.value));
  } catch {
    // Storage can be unavailable in restricted browsing modes; the in-memory choice still works.
  }
}

function restoreColumnPreference(): void {
  try {
    const raw = window.localStorage.getItem(COLUMN_PREFERENCE_KEY);
    if (!raw) return;
    const allowedKeys = new Set(columnDefinitions.map((column) => column.key));
    const savedKeys = (JSON.parse(raw) as unknown[]).filter(
      (key): key is ReportColumnKey =>
        typeof key === "string" && allowedKeys.has(key as ReportColumnKey)
    );
    if (savedKeys.length > 0) {
      const legacyFullColumnCount = columnDefinitions.length - 1;
      visibleColumns.value =
        savedKeys.length >= legacyFullColumnCount
          ? reportColumnPreset("full")
          : orderReportColumns(savedKeys);
    }
  } catch {
    try {
      window.localStorage.removeItem(COLUMN_PREFERENCE_KEY);
    } catch {
      // Ignore unavailable browser storage and keep the default full-column view.
    }
  }
}

function toggleColumn(key: ReportColumnKey, checked: boolean): void {
  if (!checked && isColumnSelected(key)) {
    if (visibleColumns.value.length === 1) {
      visibleColumns.value = [...visibleColumns.value];
      pushToast("報表至少需要保留一個顯示欄位。", "warning");
      return;
    }
    visibleColumns.value = visibleColumns.value.filter((column) => column !== key);
  } else if (checked && !isColumnSelected(key)) {
    const selectedKeys = new Set([...visibleColumns.value, key]);
    visibleColumns.value = columnDefinitions
      .map((column) => column.key)
      .filter((column) => selectedKeys.has(column));
  }
  persistColumnPreference();
}

function showAllColumns(): void {
  applyColumnPreset("full");
}

function applyColumnPreset(key: ReportColumnPresetKey): void {
  visibleColumns.value = reportColumnPreset(key);
  persistColumnPreference();
}

function closeColumnPickerFromPointer(event: PointerEvent): void {
  if (!columnPickerOpen.value) return;
  const target = event.target;
  if (target instanceof Element && target.closest(".column-picker")) return;
  columnPickerOpen.value = false;
}

function closeColumnPickerFromKeyboard(event: KeyboardEvent): void {
  if (event.key !== "Escape") return;
  columnPickerOpen.value = false;
  closeFixtureImage();
}

function handleTransactionModeChange(): void {
  if (!usesTransactionDateRange.value) {
    draftTransactionFilters.dateFrom = "";
    draftTransactionFilters.dateTo = "";
  }
  if (!draftTransactionFilters.mode) {
    draftTransactionFilters.ownershipType = [];
  }
  closeCapacityResults();
}

async function handleShowTransactionDetailsChange(): Promise<void> {
  transactionDetailsByFixtureCode.value = new Map();
  await fetchReportPage();
}


function mapReportRow(row: {
  key: string;
  customer_code: string;
  fixture_id: number;
  fixture_code: string;
  fixture_name: string;
  stock_qty: number | null;
  customer_supplied_qty: number | null;
  self_purchased_qty: number | null;
  min_stock_qty: number | null;
  water_status: WaterStatus;
  line_storage: string;
  department_storage: string;
  model_id: number;
  model_code: string;
  station_id: number;
  station_code: string;
  station_name: string;
  required_qty: number | null;
  max_open_station_count: number | null;
  configuration_status: ReportRow["configurationStatus"];
}): ReportRow {
  return {
    key: row.key,
    customerCode: row.customer_code,
    fixtureId: row.fixture_id,
    fixtureCode: row.fixture_code,
    fixtureName: row.fixture_name,
    stockQty: row.stock_qty,
    customerSuppliedQty: row.customer_supplied_qty,
    selfPurchasedQty: row.self_purchased_qty,
    minStockQty: row.min_stock_qty,
    waterStatus: row.water_status,
    lineStorage: row.line_storage,
    departmentStorage: row.department_storage,
    modelId: row.model_id,
    modelCode: row.model_code,
    stationId: row.station_id,
    stationCode: row.station_code,
    stationName: row.station_name,
    requiredQty: row.required_qty,
    maxOpenStationCount: row.max_open_station_count,
    configurationStatus: row.configuration_status
  };
}

async function fetchReportPage(): Promise<void> {
  const query = buildReportApiQuery(appliedFilters, appliedTransactionFilters, {
    includeDetails: showTransactionDetails.value
  });
  if (!query) {
    serverRows.value = [];
    populatedColumns.value = [];
    reportTotal.value = 0;
    return;
  }
  const requestId = ++reportRequestId;
  loading.value = true;
  transactionFilterLoading.value = Boolean(appliedTransactionFilters.mode);
  loadError.value = "";
  try {
    const response = await api.getConfigurationReport(query);
    if (requestId !== reportRequestId) return;
    serverRows.value = response.items.map(mapReportRow);
    const allowedColumns = new Set(columnDefinitions.map((column) => column.key));
    populatedColumns.value = response.populated_columns.filter(
      (column): column is ReportColumnKey =>
        allowedColumns.has(column as ReportColumnKey)
    );
    reportTotal.value = response.total;
    fixtureCount.value = response.fixture_count;
    attentionFixtureCount.value = response.attention_fixture_count;
    missingConfigurationCount.value = response.missing_configuration_count;
    totalStockQty.value = response.total_stock_qty;
    customerSuppliedQty.value = response.customer_supplied_qty;
    selfPurchasedQty.value = response.self_purchased_qty;
    transactionDetailCount.value = response.transaction_detail_count;
    transactionDetailsByFixtureCode.value =
      groupReportTransactionDetails(response.transaction_details);
  } catch (error) {
    if (requestId !== reportRequestId) return;
    loadError.value = error instanceof Error ? error.message : "報表資料載入失敗";
    pushToast(loadError.value, "error");
  } finally {
    if (requestId === reportRequestId) {
      loading.value = false;
      transactionFilterLoading.value = false;
    }
  }
}

async function fetchReportOptions(
  changedKey?: LinkedFilterKey,
  reconcileAll = false
): Promise<void> {
  const query = buildReportApiQuery(draftFilters, createEmptyTransactionFilters(), {
    targetPage: 1
  });
  if (!query) {
    fixtures.value = [];
    models.value = [];
    stations.value = [];
    availableWaterStatuses.value = new Set();
    return;
  }
  const requestId = ++optionsRequestId;
  try {
    const response = await api.getConfigurationReportOptions(query);
    if (requestId !== optionsRequestId) return;
    fixtures.value = response.fixtures;
    models.value = response.models;
    stations.value = response.stations;
    availableWaterStatuses.value = new Set(response.water_statuses);
    const allSelectKeys: LinkedFilterKey[] = [
      "fixtureId",
      "modelId",
      "stationId",
      "waterStatus"
    ];
    const reconciledAll = reconcileAll
      ? allSelectKeys.reduce((changed, key) => {
          if (!draftFilters[key] || optionStillAvailable(key, String(draftFilters[key]))) {
            return changed;
          }
          draftFilters[key] = (key === "waterStatus" || key === "configurationStatus" ? [] : "") as never;
          filterOrder.value = filterOrder.value.filter((entry) => entry !== key);
          return true;
        }, false)
      : false;
    if (reconciledAll || (changedKey && reconcileLinkedFilters(changedKey))) {
      await fetchReportOptions();
    }
  } catch (error) {
    if (requestId !== optionsRequestId) return;
    pushToast(error instanceof Error ? error.message : "報表篩選選項載入失敗。", "error");
  }
}

function refreshReportOptions(changedKey?: LinkedFilterKey, reconcileAll = false): void {
  if (optionsRefreshTimer) clearTimeout(optionsRefreshTimer);
  optionsRefreshTimer = setTimeout(() => {
    optionsRefreshTimer = null;
    void fetchReportOptions(changedKey, reconcileAll);
  }, 180);
}

function closeCapacityResults(): void {
  capacityResults.value = [];
  capacityRequirementsByStationId.value = new Map();
  expandedBottleneckStationIds.value = new Set();
}

function toggleBottleneck(stationId: number): void {
  const next = new Set(expandedBottleneckStationIds.value);
  if (next.has(stationId)) {
    next.delete(stationId);
  } else {
    next.add(stationId);
  }
  expandedBottleneckStationIds.value = next;
}

async function calculateCapacity(): Promise<void> {
  if (!canCalculateCapacity.value || capacityLoading.value) return;
  const modelId = Number(appliedFilters.modelId);
  const stationId = appliedFilters.stationId ? Number(appliedFilters.stationId) : null;
  if (!Number.isFinite(modelId) || (stationId !== null && !Number.isFinite(stationId))) return;
  capacityLoading.value = true;
  closeCapacityResults();
  try {
    const modelQuery = await api.getModelQuery(
      modelId,
      stationId ?? undefined,
      selectedCustomerId.value ?? undefined
    );
    capacityResults.value = modelQuery.stations.map((station) => ({
      model_id: modelQuery.model_id,
      model_code: modelQuery.model_code,
      station_id: station.station_id,
      station_code: station.station_code,
      station_name: station.station_name,
      max_open_station_count: station.max_open_station_count,
      bottleneck_fixture_code: station.bottleneck_fixture_code
    }));
    const groupedRequirements = new Map<number, ModelQueryStationRequirement[]>();
    modelQuery.station_requirements.forEach((requirement) => {
      const rows = groupedRequirements.get(requirement.station_id) ?? [];
      rows.push(requirement);
      groupedRequirements.set(requirement.station_id, rows);
    });
    capacityRequirementsByStationId.value = groupedRequirements;
    if (capacityResults.value.length === 0) {
      pushToast("此機種沒有可計算的已綁定站點。", "warning");
    }
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "最大開站數計算失敗。", "error");
  } finally {
    capacityLoading.value = false;
  }
}

function closeFixtureImage(): void {
  fixtureImageOpen.value = false;
}

function openFixtureImage(row: ReportRow): void {
  if (!row.fixtureCode) return;
  fixtureImageCode.value = row.fixtureCode;
  fixtureImageName.value = row.fixtureName;
  fixtureImageOpen.value = true;
}

function openQuickTransaction(row: ReportRow, mode: "receipt" | "return"): void {
  if (!canOperateFixtures.value || !row.fixtureCode) return;
  requestInventoryBatchOpen(row.fixtureCode, mode);
}

function openFixtureMaintenance(row: ReportRow): void {
  if (!canOperateFixtures.value || !row.fixtureId) return;
  void router.push({
    path: "/master/fixtures",
    query: {
      ...uiSurfaceRouteQuery("modern"),
      fixture_id: String(row.fixtureId),
      keyword: row.fixtureCode,
      edit: "1",
      return_to: route.fullPath
    }
  });
}

function openFixtureProduction(row: ReportRow): void {
  if (!canOperateFixtures.value || !row.modelId || !row.stationId) return;
  void router.push({
    path: "/production",
    query: {
      ...uiSurfaceRouteQuery("modern"),
      model_id: String(row.modelId),
      station_id: String(row.stationId),
      fixture_id: String(row.fixtureId),
      return_to: route.fullPath
    }
  });
}

async function exportFilteredRows(): Promise<void> {
  await exportConfigurationReportRows({
    reportTotal: reportTotal.value,
    effectiveVisibleColumns: effectiveVisibleColumns.value,
    showTransactionDetails: showTransactionDetails.value
  });
}

function applyRouteState(): void {
  closeCapacityResults();
  applyConfigurationRouteState();
}

async function loadData(): Promise<void> {
  const customerId = selectedCustomerId.value;
  loadError.value = "";
  if (!customerId) {
    fixtures.value = [];
    models.value = [];
    stations.value = [];
    serverRows.value = [];
    populatedColumns.value = [];
    reportTotal.value = 0;
    fixtureCount.value = 0;
    attentionFixtureCount.value = 0;
    missingConfigurationCount.value = 0;
    totalStockQty.value = 0;
    customerSuppliedQty.value = 0;
    selfPurchasedQty.value = 0;
    transactionDetailsByFixtureCode.value = new Map();
    showTransactionDetails.value = false;
    loading.value = false;
    return;
  }
  applyRouteState();
  await Promise.all([fetchReportOptions(), fetchReportPage()]);
}

async function runSearch(): Promise<void> {
  const nextTransactionFilters = { ...draftTransactionFilters };
  if (!transactionFiltersAreValid(nextTransactionFilters)) return;
  commitDraftFilters();
  page.value = 1;
  jumpPage.value = 1;
  showTransactionDetails.value = false;
  transactionDetailsByFixtureCode.value = new Map();
  await syncRoute();
  await Promise.all([fetchReportOptions(), fetchReportPage()]);
  if (isMobileReportViewport()) {
    filterPanelCollapsed.value = true;
  }
  await nextTick();
  scrollReportResultsIntoView(reportResultsComponent.value?.$el as HTMLElement | null);
}

async function clearFilters(): Promise<void> {
  resetFilterState();
  closeCapacityResults();
  transactionFilterLoading.value = false;
  transactionDetailsByFixtureCode.value = new Map();
  showTransactionDetails.value = false;
  filterPanelCollapsed.value = isMobileReportViewport();
  page.value = 1;
  jumpPage.value = 1;
  await syncRoute();
  await Promise.all([fetchReportOptions(), fetchReportPage()]);
}

async function changePage(nextPage: number): Promise<void> {
  page.value = Math.min(Math.max(1, nextPage), totalPages.value);
  jumpPage.value = page.value;
  await syncRoute();
  await fetchReportPage();
}

async function changePageSize(nextPageSize: number): Promise<void> {
  pageSize.value = isMobileReportMode.value
    ? nextPageSize === 50
      ? 50
      : 20
    : nextPageSize === 100
      ? 100
      : 50;
  page.value = 1;
  jumpPage.value = 1;
  await syncRoute();
  await fetchReportPage();
}

async function syncReportViewport(): Promise<void> {
  const nextMobileMode = isMobileReportViewport();
  if (nextMobileMode === isMobileReportMode.value) return;
  isMobileReportMode.value = nextMobileMode;
  const nextPageSize: 20 | 50 | 100 = nextMobileMode
    ? pageSize.value === 20
      ? 20
      : 50
    : pageSize.value === 100
      ? 100
      : 50;
  if (nextPageSize === pageSize.value) return;
  pageSize.value = nextPageSize;
  jumpPage.value = 1;
  await syncRoute();
  await fetchReportPage();
}

async function jumpToPage(): Promise<void> {
  const targetPage = Number.isFinite(jumpPage.value) ? Math.trunc(jumpPage.value) : page.value;
  await changePage(targetPage);
}

watch(
  () => route.query,
  async () => {
    if (routeSyncing.value) return;
    applyRouteState();
    await Promise.all([fetchReportOptions(), fetchReportPage()]);
  }
);

watch(selectedCustomerId, async () => {
  resetFilterState();
  closeCapacityResults();
  transactionDetailsByFixtureCode.value = new Map();
  showTransactionDetails.value = false;
  jumpPage.value = 1;
  await syncRoute();
  await loadData();
});

watch(totalPages, (nextTotal) => {
  if (page.value > nextTotal) {
    void changePage(nextTotal);
    return;
  }
  jumpPage.value = page.value;
});

watch(pendingFilterCount, (nextCount) => {
  if (nextCount > 0) closeCapacityResults();
});

onMounted(() => {
  restoreColumnPreference();
  if (isMobileReportViewport()) filterPanelCollapsed.value = true;
  document.addEventListener("pointerdown", closeColumnPickerFromPointer);
  document.addEventListener("keydown", closeColumnPickerFromKeyboard);
  window.addEventListener("resize", syncReportViewport);
  void loadData();
});

onBeforeUnmount(() => {
  document.removeEventListener("pointerdown", closeColumnPickerFromPointer);
  document.removeEventListener("keydown", closeColumnPickerFromKeyboard);
  window.removeEventListener("resize", syncReportViewport);
  reportRequestId += 1;
  optionsRequestId += 1;
  if (optionsRefreshTimer) clearTimeout(optionsRefreshTimer);
  closeFixtureImage();
});
</script>

<template>
  <main class="guest-report-page" :class="{ 'embedded-shell': props.embeddedShell }">
    <header v-if="!props.hideHeading" class="report-heading">
      <div>
        <p class="eyebrow">Inventory configuration report</p>
        <h1>治具庫存與配置報表</h1>
        <p>依治具、機種、站點、水位及儲位快速縮小資料範圍。</p>
      </div>
      <div class="scope-badge">
        <span>目前客戶</span>
        <strong>{{ currentCustomer ? `${currentCustomer.code}－${currentCustomer.name}` : "尚未選擇" }}</strong>
      </div>
    </header>

    <div class="report-workspace">
      <div class="report-main-column">
    <InventoryReportFilters
      v-model:collapsed="filterPanelCollapsed"
      :draft-filters="draftFilters"
      :transaction-filters="draftTransactionFilters"
      :ordered-filter-chips="orderedDraftFilterChips"
      :fixtures="availableFixtures"
      :models="availableModels"
      :stations="availableStations"
      :available-water-statuses="availableWaterStatuses"
      :active-filter-count="activeFilterCount"
      :pending-filter-count="pendingFilterCount"
      :report-total="reportTotal"
      :loading="loading"
      :transaction-filter-loading="transactionFilterLoading"
      :can-run-search="canRunSearch"
      :can-calculate-capacity="canCalculateCapacity"
      :capacity-loading="capacityLoading"
      :capacity-results="capacityResults"
      :capacity-requirements-by-station-id="capacityRequirementsByStationId"
      :expanded-bottleneck-station-ids="expandedBottleneckStationIds"
      :has-applied-station="Boolean(appliedFilters.stationId)"
      :transaction-date-validation-message="transactionDateValidationMessage"
      :uses-transaction-date-range="usesTransactionDateRange"
      @clear="clearFilters"
      @remove-filter="removeDraftFilter"
      @filter-change="handleDraftFilterChange"
      @fixture-status-change="handleFixtureStatusChange"
      @transaction-mode-change="handleTransactionModeChange"
      @run-search="runSearch"
      @calculate-capacity="calculateCapacity"
      @close-capacity="closeCapacityResults"
      @toggle-bottleneck="toggleBottleneck"
    />

    <slot name="between-filter-and-results" />

    <InventoryReportResults
      ref="reportResultsComponent"
      v-model:jump-page="jumpPage"
      v-model:show-transaction-details="showTransactionDetails"
      v-model:export-format="exportFormat"
      v-model:column-picker-open="columnPickerOpen"
      :rows="pagedRows"
      :report-total="reportTotal"
      :fixture-count="fixtureCount"
      :attention-fixture-count="attentionFixtureCount"
      :missing-configuration-count="missingConfigurationCount"
      :total-stock-qty="totalStockQty"
      :customer-supplied-qty="customerSuppliedQty"
      :self-purchased-qty="selfPurchasedQty"
      :page="page"
      :page-size="pageSize"
      :page-size-options="pageSizeOptions"
      :total-pages="totalPages"
      :page-start="pageStart"
      :page-end="pageEnd"
      :loading="loading"
      :load-error="loadError"
      :customer-selected="selectedCustomerId != null"
      :transaction-mode-applied="Boolean(appliedTransactionFilters.mode)"
      :transaction-filter-loading="transactionFilterLoading"
      :transaction-detail-count="transactionDetailCount"
      :transaction-details-by-fixture-code="transactionDetailsByFixtureCode"
      :export-loading="exportLoading"
      :export-feedback-message="exportFeedbackMessage"
      :column-definitions="columnDefinitions"
      :column-presets="columnPresets"
      :selected-column-preset="selectedColumnPreset"
      :selected-column-preset-label="selectedColumnPresetLabel"
      :visible-columns="visibleColumns"
      :effective-visible-columns="effectiveVisibleColumns"
      :auto-hidden-columns="autoHiddenColumns"
      :visible-column-count="visibleColumnCount"
      :table-min-width="tableMinWidth"
      :applied-filter-chips="appliedFilterChips"
      :has-pending-filters="hasPendingFilters"
      :pending-filter-count="pendingFilterCount"
      :can-run-search="canRunSearch"
      :can-operate-fixtures="canOperateFixtures"
      @show-transaction-details-change="handleShowTransactionDetailsChange"
      @export-rows="exportFilteredRows"
      @show-all-columns="showAllColumns"
      @apply-column-preset="applyColumnPreset"
      @toggle-column="toggleColumn"
      @run-search="runSearch"
      @reload="loadData"
      @open-image="openFixtureImage"
      @quick-transaction="openQuickTransaction"
      @edit-fixture="openFixtureMaintenance"
      @view-production="openFixtureProduction"
      @change-page="changePage"
      @change-page-size="changePageSize"
      @jump-page="jumpToPage"
    />
      </div>
    </div>

    <FixtureImageDialog
      :open="fixtureImageOpen"
      :fixture-code="fixtureImageCode"
      :fixture-name="fixtureImageName"
      :customer-id="selectedCustomerId"
      @close="closeFixtureImage"
    />
  </main>
</template>


<style src="@/styles/surfaces/inventory-relations.css"></style>
