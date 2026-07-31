<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter, type LocationQueryRaw } from "vue-router";

import { api, fetchFixtureImageObjectUrl } from "@/api";
import { customers, selectedCustomerId } from "@/appState";
import { pushToast } from "@/toastState";
import type {
  Fixture,
  FixtureRequirementListItem,
  MachineModel,
  ModelStation,
  Station,
  StationCapacity,
  StockSummary
} from "@/types";
import { buildCsv, type CsvValue } from "@/utils/csv";
import {
  buildReportTransactionQuery,
  type ReportTransactionMode
} from "@/utils/reportTransactionFilters";

type WaterStatus = "normal" | "low" | "empty" | "na";
type WaterFilter = "" | "attention" | "low" | "empty" | "normal";
type TransactionActivityFilters = {
  mode: ReportTransactionMode;
  dateFrom: string;
  dateTo: string;
};

type ReportFilters = {
  keyword: string;
  fixtureId: string;
  stationId: string;
  modelId: string;
  waterStatus: WaterFilter;
  storage: string;
};

type LinkedFilterKey = keyof ReportFilters;
type ColumnKey =
  | "index"
  | "customer"
  | "fixtureCode"
  | "fixtureName"
  | "stockQty"
  | "minStockQty"
  | "waterStatus"
  | "lineStorage"
  | "departmentStorage"
  | "modelCode"
  | "station"
  | "requiredQty"
  | "configurationStatus";

type ReportRow = {
  key: string;
  customerCode: string;
  fixtureId: number;
  fixtureCode: string;
  fixtureName: string;
  stockQty: number | null;
  minStockQty: number | null;
  waterStatus: WaterStatus;
  lineStorage: string;
  departmentStorage: string;
  modelId: number;
  modelCode: string;
  stationId: number;
  stationCode: string;
  stationName: string;
  requiredQty: number | null;
  configurationStatus: "configured" | "unconfigured" | "unbound";
};

const route = useRoute();
const router = useRouter();

const fixtures = ref<Fixture[]>([]);
const models = ref<MachineModel[]>([]);
const stations = ref<Station[]>([]);
const modelStations = ref<ModelStation[]>([]);
const requirements = ref<FixtureRequirementListItem[]>([]);
const stocks = ref<StockSummary[]>([]);
const loading = ref(false);
const loadError = ref("");
const capacityLoading = ref(false);
const capacityResults = ref<StationCapacity[]>([]);
const expandedBottleneckStationIds = ref<Set<number>>(new Set());
const transactionFilterLoading = ref(false);
const transactionFixtureCodes = ref<Set<string> | null>(null);
const transactionFilterSignature = ref("__uninitialized__");
const fixtureImageOpen = ref(false);
const fixtureImageLoading = ref(false);
const fixtureImageUrl = ref("");
const fixtureImageFailed = ref(false);
const fixtureImageCode = ref("");
const fixtureImageName = ref("");
const page = ref(1);
const pageSize = 50;
const COLUMN_PREFERENCE_KEY = "guest-inventory-report-columns-v1";
let loadRequestId = 0;
let fixtureImageRequestId = 0;
let transactionFilterRequestId = 0;
let routeSyncing = false;

const emptyFilters = (): ReportFilters => ({
  keyword: "",
  fixtureId: "",
  stationId: "",
  modelId: "",
  waterStatus: "",
  storage: ""
});

const draftFilters = reactive<ReportFilters>(emptyFilters());
const appliedFilters = reactive<ReportFilters>(emptyFilters());
const emptyTransactionFilters = (): TransactionActivityFilters => ({
  mode: "",
  dateFrom: "",
  dateTo: ""
});
const draftTransactionFilters = reactive<TransactionActivityFilters>(
  emptyTransactionFilters()
);
const appliedTransactionFilters = reactive<TransactionActivityFilters>(
  emptyTransactionFilters()
);
const filterOrder = ref<LinkedFilterKey[]>([]);
const columnPickerOpen = ref(false);

const columnDefinitions: Array<{ key: ColumnKey; label: string }> = [
  { key: "index", label: "序號" },
  { key: "customer", label: "客戶" },
  { key: "fixtureCode", label: "治具代碼" },
  { key: "fixtureName", label: "治具名稱" },
  { key: "stockQty", label: "總庫存" },
  { key: "minStockQty", label: "最低水位" },
  { key: "waterStatus", label: "水位狀態" },
  { key: "lineStorage", label: "產線儲位" },
  { key: "departmentStorage", label: "部門儲位" },
  { key: "modelCode", label: "機種" },
  { key: "station", label: "站點" },
  { key: "requiredQty", label: "需求數量" },
  { key: "configurationStatus", label: "配置狀態" }
];
const visibleColumns = ref<ColumnKey[]>(columnDefinitions.map((column) => column.key));

const linkedFilterLabels: Record<LinkedFilterKey, string> = {
  keyword: "關鍵字",
  fixtureId: "治具",
  stationId: "站點",
  modelId: "機種",
  waterStatus: "水位狀態",
  storage: "儲位"
};

const linkedFilterKeys: LinkedFilterKey[] = [
  "keyword",
  "fixtureId",
  "modelId",
  "stationId",
  "waterStatus",
  "storage"
];

const currentCustomer = computed(
  () => customers.value.find((customer) => customer.id === selectedCustomerId.value) ?? null
);
const usesTransactionDateRange = computed(() =>
  ["range_receipt", "range_return"].includes(draftTransactionFilters.mode)
);

function resolveWaterStatus(fixture: Fixture | undefined, stock: StockSummary | undefined): WaterStatus {
  if (!fixture) return "na";
  if (stock?.stock_status === "out_of_stock") return "empty";
  if (stock?.stock_status === "low_stock") return "low";
  if (stock?.stock_status === "normal") return "normal";
  const quantity = stock?.stock_qty ?? 0;
  if (quantity <= 0) return "empty";
  if (quantity < fixture.min_stock_qty) return "low";
  return "normal";
}

const reportRows = computed<ReportRow[]>(() => {
  const customerCode = currentCustomer.value?.code ?? "";
  const fixtureMap = new Map(fixtures.value.map((fixture) => [fixture.id, fixture]));
  const modelMap = new Map(models.value.map((model) => [model.id, model]));
  const stationMap = new Map(stations.value.map((station) => [station.id, station]));
  const stockMap = new Map(stocks.value.map((stock) => [stock.fixture_id, stock]));
  const rows: ReportRow[] = requirements.value.map((requirement) => {
    const fixture = fixtureMap.get(requirement.fixture_id);
    const model = modelMap.get(requirement.model_id);
    const station = stationMap.get(requirement.station_id);
    const stock = stockMap.get(requirement.fixture_id);
    return {
      key: `requirement-${requirement.id}`,
      customerCode,
      fixtureId: requirement.fixture_id,
      fixtureCode: fixture?.code ?? requirement.fixture_code,
      fixtureName: fixture?.name ?? requirement.fixture_name,
      stockQty: stock?.stock_qty ?? 0,
      minStockQty: fixture?.min_stock_qty ?? stock?.min_stock_qty ?? 0,
      waterStatus: resolveWaterStatus(fixture, stock),
      lineStorage: fixture?.line_storage_location ?? "",
      departmentStorage: fixture?.department_storage_location ?? "",
      modelId: requirement.model_id,
      modelCode: model?.code ?? requirement.model_code,
      stationId: requirement.station_id,
      stationCode: station?.code ?? requirement.station_code,
      stationName: station?.name ?? "",
      requiredQty: requirement.required_qty,
      configurationStatus: "configured"
    };
  });

  const fixtureIdsWithRequirements = new Set(requirements.value.map((row) => row.fixture_id));
  fixtures.value.forEach((fixture) => {
    if (fixtureIdsWithRequirements.has(fixture.id)) return;
    const stock = stockMap.get(fixture.id);
    rows.push({
      key: `fixture-${fixture.id}`,
      customerCode,
      fixtureId: fixture.id,
      fixtureCode: fixture.code,
      fixtureName: fixture.name,
      stockQty: stock?.stock_qty ?? 0,
      minStockQty: fixture.min_stock_qty,
      waterStatus: resolveWaterStatus(fixture, stock),
      lineStorage: fixture.line_storage_location ?? "",
      departmentStorage: fixture.department_storage_location ?? "",
      modelId: 0,
      modelCode: "",
      stationId: 0,
      stationCode: "",
      stationName: "",
      requiredQty: null,
      configurationStatus: "unbound"
    });
  });

  modelStations.value.forEach((mapping) => {
    const hasRequirement = requirements.value.some(
      (requirement) =>
        requirement.model_id === mapping.model_id && requirement.station_id === mapping.station_id
    );
    if (hasRequirement) return;
    const model = modelMap.get(mapping.model_id);
    const station = stationMap.get(mapping.station_id);
    rows.push({
      key: `mapping-${mapping.id}`,
      customerCode,
      fixtureId: 0,
      fixtureCode: "",
      fixtureName: "",
      stockQty: null,
      minStockQty: null,
      waterStatus: "na",
      lineStorage: "",
      departmentStorage: "",
      modelId: mapping.model_id,
      modelCode: model?.code ?? "",
      stationId: mapping.station_id,
      stationCode: station?.code ?? "",
      stationName: station?.name ?? "",
      requiredQty: null,
      configurationStatus: "unconfigured"
    });
  });

  models.value.forEach((model) => {
    if (modelStations.value.some((mapping) => mapping.model_id === model.id)) return;
    rows.push({
      key: `model-${model.id}`,
      customerCode,
      fixtureId: 0,
      fixtureCode: "",
      fixtureName: "",
      stockQty: null,
      minStockQty: null,
      waterStatus: "na",
      lineStorage: "",
      departmentStorage: "",
      modelId: model.id,
      modelCode: model.code,
      stationId: 0,
      stationCode: "",
      stationName: "",
      requiredQty: null,
      configurationStatus: "unconfigured"
    });
  });

  stations.value.forEach((station) => {
    const isMapped = modelStations.value.some((mapping) => mapping.station_id === station.id);
    if (isMapped) return;
    rows.push({
      key: `station-${station.id}`,
      customerCode,
      fixtureId: 0,
      fixtureCode: "",
      fixtureName: "",
      stockQty: null,
      minStockQty: null,
      waterStatus: "na",
      lineStorage: "",
      departmentStorage: "",
      modelId: 0,
      modelCode: "",
      stationId: station.id,
      stationCode: station.code,
      stationName: station.name,
      requiredQty: null,
      configurationStatus: "unconfigured"
    });
  });

  return rows.sort((left, right) => {
    const leftFixture = left.fixtureCode || "\uffff";
    const rightFixture = right.fixtureCode || "\uffff";
    return (
      leftFixture.localeCompare(rightFixture, "zh-TW", { numeric: true }) ||
      left.modelCode.localeCompare(right.modelCode, "zh-TW", { numeric: true }) ||
      left.stationCode.localeCompare(right.stationCode, "zh-TW", { numeric: true })
    );
  });
});

function matchesFilter(
  row: ReportRow,
  key: LinkedFilterKey,
  rawValue: ReportFilters[LinkedFilterKey]
): boolean {
  const value = String(rawValue).trim();
  if (!value) return true;
  if (key === "fixtureId") return row.fixtureId === Number(value);
  if (key === "stationId") return row.stationId === Number(value);
  if (key === "modelId") return row.modelId === Number(value);
  if (key === "waterStatus") {
    return value === "attention"
      ? ["low", "empty"].includes(row.waterStatus)
      : row.waterStatus === value;
  }
  if (key === "storage") {
    return `${row.lineStorage} ${row.departmentStorage}`
      .toLocaleLowerCase()
      .includes(value.toLocaleLowerCase());
  }
  const searchableText = [
    row.customerCode,
    row.fixtureCode,
    row.fixtureName,
    row.modelCode,
    row.stationCode,
    row.stationName,
    row.lineStorage,
    row.departmentStorage
  ]
    .join(" ")
    .toLocaleLowerCase();
  return searchableText.includes(value.toLocaleLowerCase());
}

function rowsBeforeFilter(targetKey: LinkedFilterKey): ReportRow[] {
  const targetIndex = filterOrder.value.indexOf(targetKey);
  const precedingKeys =
    targetIndex >= 0 ? filterOrder.value.slice(0, targetIndex) : filterOrder.value;
  return reportRows.value.filter((row) =>
    precedingKeys.every((key) => matchesFilter(row, key, draftFilters[key]))
  );
}

const availableFixtures = computed(() => {
  const fixtureIds = new Set(
    rowsBeforeFilter("fixtureId")
      .filter((row) => row.fixtureId)
      .map((row) => row.fixtureId)
  );
  return fixtures.value.filter(
    (fixture) => fixtureIds.has(fixture.id) || String(fixture.id) === draftFilters.fixtureId
  );
});

const availableModels = computed(() => {
  const modelIds = new Set(
    rowsBeforeFilter("modelId")
      .filter((row) => row.modelId)
      .map((row) => row.modelId)
  );
  return models.value.filter(
    (model) => modelIds.has(model.id) || String(model.id) === draftFilters.modelId
  );
});

const availableStations = computed(() => {
  const stationIds = new Set(
    rowsBeforeFilter("stationId")
      .filter((row) => row.stationId)
      .map((row) => row.stationId)
  );
  return stations.value.filter(
    (station) => stationIds.has(station.id) || String(station.id) === draftFilters.stationId
  );
});

const primaryFilterLabel = computed(() =>
  filterOrder.value[0] ? linkedFilterLabels[filterOrder.value[0]] : ""
);

function waterOptionAvailable(value: Exclude<WaterFilter, "">): boolean {
  return rowsBeforeFilter("waterStatus").some((row) =>
    matchesFilter(row, "waterStatus", value)
  );
}

function reconcileLinkedFilters(changedKey: LinkedFilterKey): void {
  const changedIndex = filterOrder.value.indexOf(changedKey);
  if (changedIndex < 0) return;
  const downstreamKeys = filterOrder.value.slice(changedIndex + 1);
  const selectKeys: LinkedFilterKey[] = [
    "fixtureId",
    "modelId",
    "stationId",
    "waterStatus"
  ];
  downstreamKeys.forEach((key) => {
    if (!selectKeys.includes(key) || !draftFilters[key]) return;
    const remainsAvailable = rowsBeforeFilter(key).some((row) =>
      matchesFilter(row, key, draftFilters[key])
    );
    if (remainsAvailable) return;
    draftFilters[key] = "" as never;
    filterOrder.value = filterOrder.value.filter((entry) => entry !== key);
  });
}

function handleDraftFilterChange(key: LinkedFilterKey): void {
  if (key === "modelId" || key === "stationId") closeCapacityResults();
  const hasValue = String(draftFilters[key]).trim().length > 0;
  if (!hasValue) {
    filterOrder.value = filterOrder.value.filter((entry) => entry !== key);
    return;
  }
  if (!filterOrder.value.includes(key)) {
    filterOrder.value = [...filterOrder.value, key];
  }
  reconcileLinkedFilters(key);
}

const filteredRows = computed(() => {
  return reportRows.value.filter((row) => {
    const matchesLinkedFilters = linkedFilterKeys.every((key) =>
      matchesFilter(row, key, appliedFilters[key])
    );
    if (!matchesLinkedFilters) return false;
    if (transactionFixtureCodes.value === null) return true;
    return Boolean(
      row.fixtureCode &&
        transactionFixtureCodes.value.has(row.fixtureCode.trim().toLocaleUpperCase())
    );
  });
});

const fixtureCount = computed(
  () => new Set(filteredRows.value.filter((row) => row.fixtureId).map((row) => row.fixtureId)).size
);
const attentionFixtureCount = computed(
  () =>
    new Set(
      filteredRows.value
        .filter((row) => row.fixtureId && ["low", "empty"].includes(row.waterStatus))
        .map((row) => row.fixtureId)
    ).size
);
const missingConfigurationCount = computed(
  () => filteredRows.value.filter((row) => row.configurationStatus === "unconfigured").length
);
const totalPages = computed(() => Math.max(1, Math.ceil(filteredRows.value.length / pageSize)));
const pagedRows = computed(() =>
  filteredRows.value.slice((page.value - 1) * pageSize, page.value * pageSize)
);
const pageStart = computed(() =>
  filteredRows.value.length ? (page.value - 1) * pageSize + 1 : 0
);
const pageEnd = computed(() => Math.min(page.value * pageSize, filteredRows.value.length));
const activeFilterCount = computed(
  () =>
    Object.values(appliedFilters).filter((value) => String(value).trim()).length +
    (appliedTransactionFilters.mode ? 1 : 0)
);
const canCalculateCapacity = computed(
  () =>
    Boolean(selectedCustomerId.value) &&
    Boolean(draftFilters.modelId) &&
    !loading.value
);
const visibleColumnCount = computed(() => visibleColumns.value.length);
const tableMinWidth = computed(() => `${Math.max(720, visibleColumnCount.value * 108)}px`);

function isColumnVisible(key: ColumnKey): boolean {
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
      (key): key is ColumnKey => typeof key === "string" && allowedKeys.has(key as ColumnKey)
    );
    if (savedKeys.length > 0) visibleColumns.value = [...new Set(savedKeys)];
  } catch {
    try {
      window.localStorage.removeItem(COLUMN_PREFERENCE_KEY);
    } catch {
      // Ignore unavailable browser storage and keep the default full-column view.
    }
  }
}

function toggleColumn(key: ColumnKey, event?: Event): void {
  if (isColumnVisible(key)) {
    if (visibleColumns.value.length === 1) {
      const checkbox = event?.target;
      if (checkbox instanceof HTMLInputElement) checkbox.checked = true;
      pushToast("報表至少需要保留一個顯示欄位。", "warning");
      return;
    }
    visibleColumns.value = visibleColumns.value.filter((column) => column !== key);
  } else {
    const selectedKeys = new Set([...visibleColumns.value, key]);
    visibleColumns.value = columnDefinitions
      .map((column) => column.key)
      .filter((column) => selectedKeys.has(column));
  }
  persistColumnPreference();
}

function showAllColumns(): void {
  visibleColumns.value = columnDefinitions.map((column) => column.key);
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

function waterStatusLabel(status: WaterStatus): string {
  if (status === "empty") return "缺料";
  if (status === "low") return "低水位";
  if (status === "normal") return "正常";
  return "—";
}

function configurationStatusLabel(status: ReportRow["configurationStatus"]): string {
  if (status === "configured") return "已配置";
  if (status === "unconfigured") return "未配置";
  return "未綁定";
}

function handleTransactionModeChange(): void {
  if (!usesTransactionDateRange.value) {
    draftTransactionFilters.dateFrom = "";
    draftTransactionFilters.dateTo = "";
  }
}

function todayDateValue(): string {
  const today = new Date();
  return [
    today.getFullYear(),
    String(today.getMonth() + 1).padStart(2, "0"),
    String(today.getDate()).padStart(2, "0")
  ].join("-");
}

function transactionFiltersAreValid(filters: TransactionActivityFilters): boolean {
  if (!filters.mode || filters.mode.startsWith("today")) return true;
  if (!filters.dateFrom || !filters.dateTo) {
    pushToast("指定日期收退料需要同時選擇起始與結束日期。", "warning");
    return false;
  }
  if (filters.dateFrom > filters.dateTo) {
    pushToast("收退料篩選的起始日期不可晚於結束日期。", "warning");
    return false;
  }
  return true;
}

async function ensureTransactionMatches(
  filters: TransactionActivityFilters
): Promise<void> {
  const customerId = selectedCustomerId.value;
  const queryFilters = buildReportTransactionQuery(
    filters.mode,
    filters.dateFrom,
    filters.dateTo,
    todayDateValue()
  );
  const signature = JSON.stringify({ customerId, queryFilters });
  if (transactionFilterSignature.value === signature) return;
  const requestId = ++transactionFilterRequestId;
  transactionFilterLoading.value = true;
  try {
    if (!customerId || !queryFilters) {
      if (requestId !== transactionFilterRequestId) return;
      transactionFixtureCodes.value = null;
      transactionFilterSignature.value = signature;
      return;
    }
    const fixtureCodes = new Set<string>();
    let transactionPage = 1;
    let transactionTotal = 0;
    do {
      const response = await api.listTransactionOverviewPage(
        transactionPage,
        200,
        customerId,
        queryFilters
      );
      if (requestId !== transactionFilterRequestId) return;
      transactionTotal = response.total;
      response.items.forEach((item) => {
        const fixtureCode = item.fixture_code.trim().toLocaleUpperCase();
        if (fixtureCode) fixtureCodes.add(fixtureCode);
      });
      transactionPage += 1;
    } while ((transactionPage - 1) * 200 < transactionTotal);
    transactionFixtureCodes.value = fixtureCodes;
    transactionFilterSignature.value = signature;
  } finally {
    if (requestId === transactionFilterRequestId) transactionFilterLoading.value = false;
  }
}

function closeCapacityResults(): void {
  capacityResults.value = [];
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
  const modelId = Number(draftFilters.modelId);
  const stationId = draftFilters.stationId ? Number(draftFilters.stationId) : null;
  if (!Number.isFinite(modelId) || (stationId !== null && !Number.isFinite(stationId))) return;
  capacityLoading.value = true;
  closeCapacityResults();
  try {
    if (stationId !== null) {
      capacityResults.value = [
        await api.getStationCapacity(
          stationId,
          modelId,
          selectedCustomerId.value ?? undefined
        )
      ];
    } else {
      const modelQuery = await api.getModelQuery(
        modelId,
        undefined,
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
      if (capacityResults.value.length === 0) {
        pushToast("此機種沒有可計算的已綁定站點。", "warning");
      }
    }
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "最大開站數計算失敗。", "error");
  } finally {
    capacityLoading.value = false;
  }
}

function releaseFixtureImageUrl(): void {
  if (!fixtureImageUrl.value) return;
  URL.revokeObjectURL(fixtureImageUrl.value);
  fixtureImageUrl.value = "";
}

function closeFixtureImage(): void {
  fixtureImageRequestId += 1;
  fixtureImageOpen.value = false;
  fixtureImageLoading.value = false;
  releaseFixtureImageUrl();
}

async function openFixtureImage(row: ReportRow): Promise<void> {
  if (!row.fixtureCode) return;
  const requestId = ++fixtureImageRequestId;
  releaseFixtureImageUrl();
  fixtureImageCode.value = row.fixtureCode;
  fixtureImageName.value = row.fixtureName;
  fixtureImageFailed.value = false;
  fixtureImageLoading.value = true;
  fixtureImageOpen.value = true;
  try {
    const objectUrl = await fetchFixtureImageObjectUrl(row.fixtureCode);
    if (requestId !== fixtureImageRequestId) {
      URL.revokeObjectURL(objectUrl);
      return;
    }
    fixtureImageUrl.value = objectUrl;
  } catch {
    if (requestId === fixtureImageRequestId) fixtureImageFailed.value = true;
  } finally {
    if (requestId === fixtureImageRequestId) fixtureImageLoading.value = false;
  }
}

function exportCellValue(key: ColumnKey, row: ReportRow, index: number): CsvValue {
  if (key === "index") return index + 1;
  if (key === "customer") return row.customerCode || "—";
  if (key === "fixtureCode") return row.fixtureCode || "—";
  if (key === "fixtureName") return row.fixtureName || "—";
  if (key === "stockQty") return row.stockQty ?? "—";
  if (key === "minStockQty") return row.minStockQty ?? "—";
  if (key === "waterStatus") return waterStatusLabel(row.waterStatus);
  if (key === "lineStorage") return row.lineStorage || "—";
  if (key === "departmentStorage") return row.departmentStorage || "—";
  if (key === "modelCode") return row.modelCode || "—";
  if (key === "station") {
    if (!row.stationCode) return "—";
    return row.stationName ? `${row.stationCode}－${row.stationName}` : row.stationCode;
  }
  if (key === "requiredQty") return row.requiredQty ?? "—";
  return configurationStatusLabel(row.configurationStatus);
}

function exportFilteredRows(): void {
  if (filteredRows.value.length === 0) {
    pushToast("目前篩選條件沒有可匯出的資料。", "warning");
    return;
  }
  const selectedColumns = columnDefinitions.filter((column) =>
    visibleColumns.value.includes(column.key)
  );
  const csv = buildCsv(
    selectedColumns.map((column) => column.label),
    filteredRows.value.map((row, index) =>
      selectedColumns.map((column) => exportCellValue(column.key, row, index))
    )
  );
  const date = new Date();
  const dateStamp = [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, "0"),
    String(date.getDate()).padStart(2, "0")
  ].join("");
  const customerCode = (currentCustomer.value?.code ?? "customer").replace(/[\\/:*?"<>|]/g, "-");
  const blob = new Blob(["\ufeff", csv], { type: "text/csv;charset=utf-8" });
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = `fixture-inventory-report-${customerCode}-${dateStamp}.csv`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
  pushToast(`已匯出符合目前篩選條件的 ${filteredRows.value.length} 筆資料。`, "success");
}

function buildQuery(): LocationQueryRaw {
  const query: LocationQueryRaw = {
    page: String(page.value)
  };
  if (route.name === "search") query.home_mode = "report";
  if (selectedCustomerId.value) query.customer = String(selectedCustomerId.value);
  if (appliedFilters.keyword.trim()) query.q = appliedFilters.keyword.trim();
  if (appliedFilters.fixtureId) query.fixture = appliedFilters.fixtureId;
  if (appliedFilters.stationId) query.station = appliedFilters.stationId;
  if (appliedFilters.modelId) query.model = appliedFilters.modelId;
  if (appliedFilters.waterStatus) query.water = appliedFilters.waterStatus;
  if (appliedFilters.storage.trim()) query.storage = appliedFilters.storage.trim();
  if (appliedTransactionFilters.mode) {
    query.transaction_activity = appliedTransactionFilters.mode;
    if (
      ["range_receipt", "range_return"].includes(appliedTransactionFilters.mode)
    ) {
      query.transaction_date_from = appliedTransactionFilters.dateFrom;
      query.transaction_date_to = appliedTransactionFilters.dateTo;
    }
  }
  const appliedOrder = filterOrder.value.filter(
    (key) => String(appliedFilters[key]).trim().length > 0
  );
  if (appliedOrder.length) query.priority = appliedOrder.join(",");
  return query;
}

function syncRoute(): void {
  if (routeSyncing) return;
  void router.replace({ path: route.path, query: buildQuery() });
}

function allowedId(value: unknown, rows: Array<{ id: number }>): string {
  if (typeof value !== "string") return "";
  const id = Number(value);
  return rows.some((row) => row.id === id) ? value : "";
}

function applyRouteState(): void {
  routeSyncing = true;
  try {
    closeCapacityResults();
    const nextFilters: ReportFilters = {
      keyword: typeof route.query.q === "string" ? route.query.q : "",
      fixtureId: allowedId(route.query.fixture, fixtures.value),
      stationId: allowedId(route.query.station, stations.value),
      modelId: allowedId(route.query.model, models.value),
      waterStatus: ["attention", "low", "empty", "normal"].includes(String(route.query.water))
        ? (route.query.water as WaterFilter)
        : "",
      storage: typeof route.query.storage === "string" ? route.query.storage : ""
    };
    Object.assign(draftFilters, nextFilters);
    Object.assign(appliedFilters, nextFilters);
    const routeTransactionValue =
      typeof route.query.transaction_activity === "string"
        ? route.query.transaction_activity
        : "";
    const routeTransactionMode = [
      "today_receipt",
      "today_return",
      "range_receipt",
      "range_return"
    ].includes(routeTransactionValue)
      ? (routeTransactionValue as ReportTransactionMode)
      : "";
    const routeDateFrom =
      typeof route.query.transaction_date_from === "string"
        ? route.query.transaction_date_from
        : "";
    const routeDateTo =
      typeof route.query.transaction_date_to === "string"
        ? route.query.transaction_date_to
        : "";
    const routeRangeIsComplete =
      !routeTransactionMode.startsWith("range") || Boolean(routeDateFrom && routeDateTo);
    const nextTransactionFilters: TransactionActivityFilters = {
      mode: routeRangeIsComplete ? routeTransactionMode : "",
      dateFrom:
        routeRangeIsComplete && routeTransactionMode.startsWith("range") ? routeDateFrom : "",
      dateTo:
        routeRangeIsComplete && routeTransactionMode.startsWith("range") ? routeDateTo : ""
    };
    Object.assign(draftTransactionFilters, nextTransactionFilters);
    Object.assign(appliedTransactionFilters, nextTransactionFilters);
    const activeKeys = new Set(
      linkedFilterKeys.filter((key) => String(nextFilters[key]).trim().length > 0)
    );
    const routePriority =
      typeof route.query.priority === "string"
        ? route.query.priority
            .split(",")
            .filter(
              (key): key is LinkedFilterKey =>
                linkedFilterKeys.includes(key as LinkedFilterKey) &&
                activeKeys.has(key as LinkedFilterKey)
            )
        : [];
    filterOrder.value = [
      ...new Set([
        ...routePriority,
        ...linkedFilterKeys.filter((key) => activeKeys.has(key))
      ])
    ];
    const requestedPage = Number(route.query.page);
    page.value = Number.isFinite(requestedPage) && requestedPage > 0 ? requestedPage : 1;
  } finally {
    routeSyncing = false;
  }
}

async function loadData(): Promise<void> {
  const requestId = ++loadRequestId;
  const customerId = selectedCustomerId.value;
  loadError.value = "";
  if (!customerId) {
    fixtures.value = [];
    models.value = [];
    stations.value = [];
    modelStations.value = [];
    requirements.value = [];
    stocks.value = [];
    transactionFilterRequestId += 1;
    transactionFixtureCodes.value = null;
    transactionFilterSignature.value = "__uninitialized__";
    loading.value = false;
    return;
  }
  loading.value = true;
  try {
    const [fixtureRows, modelRows, stationRows, mappingRows, requirementRows, stockRows] =
      await Promise.all([
        api.listFixtures(customerId),
        api.listModels(customerId),
        api.listStations(customerId),
        api.listModelStations(customerId),
        api.listFixtureRequirements(customerId),
        api.listStock(customerId)
      ]);
    if (requestId !== loadRequestId) return;
    fixtures.value = fixtureRows;
    models.value = modelRows;
    stations.value = stationRows;
    modelStations.value = mappingRows;
    requirements.value = requirementRows;
    stocks.value = stockRows;
    applyRouteState();
    await ensureTransactionMatches(appliedTransactionFilters);
  } catch (error) {
    if (requestId !== loadRequestId) return;
    loadError.value = error instanceof Error ? error.message : "報表資料載入失敗";
    pushToast(loadError.value, "error");
  } finally {
    if (requestId === loadRequestId) loading.value = false;
  }
}

async function runSearch(): Promise<void> {
  const nextTransactionFilters = { ...draftTransactionFilters };
  if (!transactionFiltersAreValid(nextTransactionFilters)) return;
  try {
    await ensureTransactionMatches(nextTransactionFilters);
    Object.assign(appliedFilters, draftFilters);
    Object.assign(appliedTransactionFilters, nextTransactionFilters);
    page.value = 1;
    syncRoute();
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "收退料篩選查詢失敗。", "error");
  }
}

function clearFilters(): void {
  Object.assign(draftFilters, emptyFilters());
  Object.assign(appliedFilters, emptyFilters());
  Object.assign(draftTransactionFilters, emptyTransactionFilters());
  Object.assign(appliedTransactionFilters, emptyTransactionFilters());
  filterOrder.value = [];
  closeCapacityResults();
  transactionFilterRequestId += 1;
  transactionFilterLoading.value = false;
  transactionFixtureCodes.value = null;
  transactionFilterSignature.value = JSON.stringify({
    customerId: selectedCustomerId.value,
    queryFilters: null
  });
  page.value = 1;
  syncRoute();
}

function changePage(nextPage: number): void {
  page.value = Math.min(Math.max(1, nextPage), totalPages.value);
}

function changeCustomer(event: Event): void {
  const customerId = Number((event.target as HTMLSelectElement).value);
  if (!Number.isFinite(customerId) || customerId === selectedCustomerId.value) return;
  selectedCustomerId.value = customerId;
}

watch(page, () => {
  syncRoute();
});

watch(
  () => route.query,
  async () => {
    if (loading.value) return;
    applyRouteState();
    try {
      await ensureTransactionMatches(appliedTransactionFilters);
    } catch (error) {
      pushToast(error instanceof Error ? error.message : "收退料篩選查詢失敗。", "error");
    }
  }
);

watch(selectedCustomerId, async () => {
  Object.assign(draftFilters, emptyFilters());
  Object.assign(appliedFilters, emptyFilters());
  Object.assign(draftTransactionFilters, emptyTransactionFilters());
  Object.assign(appliedTransactionFilters, emptyTransactionFilters());
  filterOrder.value = [];
  closeCapacityResults();
  transactionFilterRequestId += 1;
  transactionFixtureCodes.value = null;
  transactionFilterSignature.value = "__uninitialized__";
  page.value = 1;
  await router.replace({
    path: route.path,
    query: {
      ...(selectedCustomerId.value ? { customer: String(selectedCustomerId.value) } : {}),
      page: "1"
    }
  });
  await loadData();
  syncRoute();
});

watch(totalPages, (nextTotal) => {
  if (page.value > nextTotal) page.value = nextTotal;
});

onMounted(() => {
  restoreColumnPreference();
  document.addEventListener("pointerdown", closeColumnPickerFromPointer);
  document.addEventListener("keydown", closeColumnPickerFromKeyboard);
  void loadData();
});

onBeforeUnmount(() => {
  document.removeEventListener("pointerdown", closeColumnPickerFromPointer);
  document.removeEventListener("keydown", closeColumnPickerFromKeyboard);
  transactionFilterRequestId += 1;
  closeFixtureImage();
});
</script>

<template>
  <main class="guest-report-page">
    <header class="report-heading">
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

    <section class="filter-panel" data-tour="report-filter-panel" aria-label="報表篩選條件">
      <div class="filter-panel-title">
        <div>
          <strong>篩選條件</strong>
          <span>依選擇順序聯動，第一個條件優先</span>
          <em v-if="primaryFilterLabel">
            第一優先：{{ primaryFilterLabel }}
          </em>
        </div>
        <button v-if="activeFilterCount" class="text-button" type="button" @click="clearFilters">
          清除全部
        </button>
      </div>

      <div class="filter-grid">
        <label>
          <span>客戶</span>
          <select
            :value="selectedCustomerId ?? ''"
            aria-label="選擇報表客戶"
            @change="changeCustomer"
          >
            <option value="" disabled>請選擇客戶</option>
            <option v-for="customer in customers" :key="customer.id" :value="customer.id">
              {{ customer.code }}－{{ customer.name }}
            </option>
          </select>
        </label>

        <label class="keyword-field">
          <span>關鍵字</span>
          <input
            v-model="draftFilters.keyword"
            type="search"
            placeholder="治具、機種、站點或名稱"
            @input="handleDraftFilterChange('keyword')"
            @keydown.enter.prevent="runSearch"
          />
        </label>

        <label>
          <span>治具</span>
          <select v-model="draftFilters.fixtureId" @change="handleDraftFilterChange('fixtureId')">
            <option value="">全部治具</option>
            <option v-for="fixture in availableFixtures" :key="fixture.id" :value="String(fixture.id)">
              {{ fixture.code }}－{{ fixture.name }}
            </option>
          </select>
        </label>

        <label>
          <span>機種</span>
          <select v-model="draftFilters.modelId" @change="handleDraftFilterChange('modelId')">
            <option value="">全部機種</option>
            <option v-for="model in availableModels" :key="model.id" :value="String(model.id)">
              {{ model.code }}
            </option>
          </select>
        </label>

        <label>
          <span>站點</span>
          <select v-model="draftFilters.stationId" @change="handleDraftFilterChange('stationId')">
            <option value="">全部站點</option>
            <option v-for="station in availableStations" :key="station.id" :value="String(station.id)">
              {{ station.code }}－{{ station.name }}
            </option>
          </select>
        </label>

        <label>
          <span>水位狀態</span>
          <select v-model="draftFilters.waterStatus" @change="handleDraftFilterChange('waterStatus')">
            <option value="">全部水位</option>
            <option value="attention" :disabled="!waterOptionAvailable('attention')">低水位與缺料</option>
            <option value="low" :disabled="!waterOptionAvailable('low')">只看低水位</option>
            <option value="empty" :disabled="!waterOptionAvailable('empty')">只看缺料</option>
            <option value="normal" :disabled="!waterOptionAvailable('normal')">只看正常</option>
          </select>
        </label>

        <label>
          <span>儲位</span>
          <input
            v-model="draftFilters.storage"
            type="search"
            placeholder="產線或部門儲位"
            @input="handleDraftFilterChange('storage')"
            @keydown.enter.prevent="runSearch"
          />
        </label>

        <label>
          <span>收退料</span>
          <select
            v-model="draftTransactionFilters.mode"
            @change="handleTransactionModeChange"
          >
            <option value="">不篩選收退料</option>
            <option value="today_receipt">今日收料</option>
            <option value="today_return">今日退料</option>
            <option value="range_receipt">指定日期收料</option>
            <option value="range_return">指定日期退料</option>
          </select>
        </label>

        <label>
          <span>起始日期</span>
          <input
            v-model="draftTransactionFilters.dateFrom"
            type="date"
            :disabled="!usesTransactionDateRange"
            aria-describedby="transaction-date-hint"
          />
        </label>

        <label>
          <span>結束日期</span>
          <input
            v-model="draftTransactionFilters.dateTo"
            type="date"
            :disabled="!usesTransactionDateRange"
            aria-describedby="transaction-date-hint"
          />
        </label>

        <div class="filter-actions">
          <button class="secondary-button" type="button" @click="clearFilters">重設</button>
          <button
            class="capacity-button"
            data-tour="report-capacity-trigger"
            type="button"
            :disabled="!canCalculateCapacity || capacityLoading"
            @click="calculateCapacity"
          >
            {{ capacityLoading ? "計算中…" : "計算最大開站數" }}
          </button>
          <button
            class="primary-button"
            type="button"
            :disabled="loading || transactionFilterLoading || !selectedCustomerId"
            @click="runSearch"
          >
            {{ transactionFilterLoading ? "查詢中…" : "查詢" }}
          </button>
        </div>

        <p id="transaction-date-hint" class="transaction-date-hint">
          日期只會套用在「指定日期收料／退料」；未選收退料模式時不參與其他條件篩選。
        </p>

        <div v-if="capacityResults.length" class="capacity-result" role="status">
          <header>
            <div>
              <span>{{ draftFilters.stationId ? "指定站點計算結果" : "全部站點計算結果" }}</span>
              <strong>{{ capacityResults[0].model_code }}</strong>
              <small>共 {{ capacityResults.length }} 個站點</small>
            </div>
            <button type="button" aria-label="關閉最大開站數結果" @click="closeCapacityResults">
              關閉
            </button>
          </header>
          <div class="capacity-result-list">
            <article v-for="capacity in capacityResults" :key="capacity.station_id">
              <div>
                <strong>{{ capacity.station_code }}</strong>
                <span>{{ capacity.station_name || "—" }}</span>
              </div>
              <dl>
                <div>
                  <dt>最大開站數</dt>
                  <dd>{{ capacity.max_open_station_count }} 站</dd>
                </div>
              </dl>
              <button
                class="capacity-bottleneck-toggle"
                type="button"
                :aria-expanded="expandedBottleneckStationIds.has(capacity.station_id)"
                @click="toggleBottleneck(capacity.station_id)"
              >
                {{
                  expandedBottleneckStationIds.has(capacity.station_id)
                    ? "收起瓶頸治具"
                    : "查看瓶頸治具"
                }}
              </button>
              <p
                v-if="expandedBottleneckStationIds.has(capacity.station_id)"
                class="capacity-bottleneck-detail"
              >
                {{ capacity.bottleneck_fixture_code || "無瓶頸治具" }}
              </p>
            </article>
          </div>
        </div>
      </div>
    </section>

    <section class="report-section" aria-label="治具庫存與配置結果">
      <div class="report-toolbar">
        <div class="report-summary">
          <strong>{{ filteredRows.length }}</strong>
          <span>筆資料</span>
          <i></i>
          <span><b>{{ fixtureCount }}</b> 支治具</span>
          <span class="attention"><b>{{ attentionFixtureCount }}</b> 支低水位／缺料</span>
          <span class="missing"><b>{{ missingConfigurationCount }}</b> 筆未配置</span>
        </div>
        <div class="report-toolbar-actions">
          <div class="report-range">
            顯示 {{ pageStart }}–{{ pageEnd }} / 共 {{ filteredRows.length }} 筆
          </div>
          <button
            class="report-export-button"
            type="button"
            :disabled="loading || filteredRows.length === 0"
            @click="exportFilteredRows"
          >
            匯出篩選結果
          </button>
          <div class="column-picker">
            <button
              class="column-picker-trigger"
              type="button"
              :aria-expanded="columnPickerOpen"
              aria-haspopup="true"
              @click.stop="columnPickerOpen = !columnPickerOpen"
            >
              顯示欄位
              <b>{{ visibleColumnCount }} / {{ columnDefinitions.length }}</b>
            </button>
            <div
              v-if="columnPickerOpen"
              class="column-picker-popover"
              role="group"
              aria-label="選擇報表顯示欄位"
            >
              <div class="column-picker-heading">
                <div>
                  <strong>選擇顯示欄位</strong>
                  <span>可複選</span>
                </div>
                <button
                  type="button"
                  :disabled="visibleColumnCount === columnDefinitions.length"
                  @click="showAllColumns"
                >
                  全部顯示
                </button>
              </div>
              <div class="column-picker-options">
                <label
                  v-for="column in columnDefinitions"
                  :key="column.key"
                  :class="{ selected: isColumnVisible(column.key) }"
                >
                  <input
                    type="checkbox"
                    :checked="isColumnVisible(column.key)"
                    @change="toggleColumn(column.key, $event)"
                  />
                  <span class="column-option-indicator" aria-hidden="true"></span>
                  <span class="column-option-label">{{ column.label }}</span>
                </label>
              </div>
              <small>至少保留一個欄位；設定會儲存在此瀏覽器。</small>
            </div>
          </div>
        </div>
      </div>

      <div v-if="!selectedCustomerId" class="report-state">
        <strong>請先選擇客戶</strong>
        <p>選擇客戶後即可載入治具庫存與配置報表。</p>
      </div>

      <div v-else-if="loading" class="report-state">
        <strong>正在載入報表…</strong>
        <p>正在整理治具、庫存、機種與站點資料。</p>
      </div>

      <div v-else-if="loadError" class="report-state error">
        <strong>資料載入失敗</strong>
        <p>{{ loadError }}</p>
        <button type="button" @click="loadData">重新載入</button>
      </div>

      <div v-else class="table-frame" data-tour="report-result-table">
        <div class="table-scroll" tabindex="0" aria-label="報表可左右捲動">
          <table :style="{ minWidth: tableMinWidth }">
            <thead>
              <tr>
                <th v-if="isColumnVisible('index')" class="index-column">序號</th>
                <th v-if="isColumnVisible('customer')">客戶</th>
                <th v-if="isColumnVisible('fixtureCode')">治具代碼</th>
                <th v-if="isColumnVisible('fixtureName')">治具名稱</th>
                <th v-if="isColumnVisible('stockQty')" class="number-column">總庫存</th>
                <th v-if="isColumnVisible('minStockQty')" class="number-column">最低水位</th>
                <th v-if="isColumnVisible('waterStatus')">水位狀態</th>
                <th v-if="isColumnVisible('lineStorage')">產線儲位</th>
                <th v-if="isColumnVisible('departmentStorage')">部門儲位</th>
                <th v-if="isColumnVisible('modelCode')">機種</th>
                <th v-if="isColumnVisible('station')">站點</th>
                <th v-if="isColumnVisible('requiredQty')" class="number-column">需求數量</th>
                <th v-if="isColumnVisible('configurationStatus')">配置狀態</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(row, index) in pagedRows"
                :key="row.key"
                :class="[
                  `water-${row.waterStatus}`,
                  { 'configuration-missing': row.configurationStatus === 'unconfigured' }
                ]"
              >
                <td v-if="isColumnVisible('index')" class="index-column">
                  {{ (page - 1) * pageSize + index + 1 }}
                </td>
                <td v-if="isColumnVisible('customer')">{{ row.customerCode || "—" }}</td>
                <td v-if="isColumnVisible('fixtureCode')" class="code-cell">
                  <button
                    v-if="row.fixtureCode"
                    class="fixture-image-trigger"
                    type="button"
                    :aria-label="`查看治具 ${row.fixtureCode} 圖片`"
                    @click="openFixtureImage(row)"
                  >
                    {{ row.fixtureCode }}
                  </button>
                  <span v-else>—</span>
                </td>
                <td v-if="isColumnVisible('fixtureName')" class="name-cell">
                  {{ row.fixtureName || "—" }}
                </td>
                <td v-if="isColumnVisible('stockQty')" class="number-cell">
                  {{ row.stockQty ?? "—" }}
                </td>
                <td v-if="isColumnVisible('minStockQty')" class="number-cell">
                  {{ row.minStockQty ?? "—" }}
                </td>
                <td v-if="isColumnVisible('waterStatus')">
                  <span class="status-badge" :class="`status-${row.waterStatus}`">
                    {{ waterStatusLabel(row.waterStatus) }}
                  </span>
                </td>
                <td v-if="isColumnVisible('lineStorage')">{{ row.lineStorage || "—" }}</td>
                <td v-if="isColumnVisible('departmentStorage')">
                  {{ row.departmentStorage || "—" }}
                </td>
                <td v-if="isColumnVisible('modelCode')" class="code-cell">
                  {{ row.modelCode || "—" }}
                </td>
                <td v-if="isColumnVisible('station')">
                  <span class="station-cell">
                    <b>{{ row.stationCode || "—" }}</b>
                    <small v-if="row.stationName">{{ row.stationName }}</small>
                  </span>
                </td>
                <td v-if="isColumnVisible('requiredQty')" class="number-cell">
                  {{ row.requiredQty ?? "—" }}
                </td>
                <td v-if="isColumnVisible('configurationStatus')">
                  <span
                    class="configuration-badge"
                    :class="`configuration-${row.configurationStatus}`"
                  >
                    {{ configurationStatusLabel(row.configurationStatus) }}
                  </span>
                </td>
              </tr>
              <tr v-if="pagedRows.length === 0">
                <td class="empty-cell" :colspan="visibleColumnCount">
                  <strong>沒有符合條件的資料</strong>
                  <span>請調整篩選條件後重新查詢。</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <nav v-if="!loading && filteredRows.length" class="pagination" aria-label="報表分頁">
        <button type="button" :disabled="page <= 1" @click="changePage(page - 1)">上一頁</button>
        <span>第 <strong>{{ page }}</strong> / {{ totalPages }} 頁</span>
        <button type="button" :disabled="page >= totalPages" @click="changePage(page + 1)">下一頁</button>
      </nav>
    </section>

    <Teleport to="body">
      <div v-if="fixtureImageOpen" class="fixture-image-layer">
        <button
          class="fixture-image-backdrop"
          type="button"
          aria-label="關閉治具圖片"
          @click="closeFixtureImage"
        ></button>
        <section
          class="fixture-image-dialog"
          role="dialog"
          aria-modal="true"
          :aria-label="`治具 ${fixtureImageCode} 圖片`"
        >
          <header>
            <div>
              <span>治具圖片</span>
              <strong>{{ fixtureImageCode }}</strong>
              <small>{{ fixtureImageName || "—" }}</small>
            </div>
            <button type="button" @click="closeFixtureImage">關閉</button>
          </header>
          <div class="fixture-image-content">
            <span v-if="fixtureImageLoading">圖片載入中…</span>
            <img
              v-else-if="fixtureImageUrl"
              :src="fixtureImageUrl"
              :alt="`${fixtureImageCode} ${fixtureImageName} 治具圖片`"
            />
            <div v-else class="fixture-image-empty">
              <strong>{{ fixtureImageFailed ? "尚未建立圖片" : "無法顯示圖片" }}</strong>
              <span>請聯絡管理人員於治具主資料補上圖片。</span>
            </div>
          </div>
        </section>
      </div>
    </Teleport>
  </main>
</template>

<style scoped>
.guest-report-page {
  min-height: 100%;
  padding: 16px clamp(12px, 2vw, 28px) 32px;
  color: var(--text);
  background:
    linear-gradient(180deg, rgba(47, 110, 229, 0.07), transparent 240px),
    var(--bg);
}

button,
input,
select {
  font: inherit;
}

button {
  color: inherit;
}

.report-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  max-width: 1800px;
  margin: 0 auto 12px;
}

.report-heading h1 {
  margin: 2px 0 3px;
  font-size: clamp(1.45rem, 2vw, 2rem);
  line-height: 1.15;
}

.report-heading p {
  margin: 0;
  color: var(--muted);
}

.report-heading .eyebrow {
  color: var(--tone-info);
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.scope-badge {
  display: grid;
  gap: 2px;
  min-width: 180px;
  padding: 9px 13px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 6px 20px rgba(28, 47, 84, 0.05);
}

.scope-badge span {
  color: var(--muted);
  font-size: 0.7rem;
}

.scope-badge strong {
  color: var(--tone-info);
}

.filter-panel,
.report-section {
  max-width: 1800px;
  margin-inline: auto;
  border: 1px solid var(--line);
  background: var(--panel);
  box-shadow: 0 8px 24px rgba(28, 47, 84, 0.06);
}

.filter-panel {
  margin-bottom: 12px;
  border-radius: 10px;
}

.filter-panel-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 38px;
  padding: 7px 12px;
  border-bottom: 1px solid var(--line);
  background: var(--surface-secondary);
}

.filter-panel-title div {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.filter-panel-title strong {
  font-size: 0.9rem;
}

.filter-panel-title span {
  color: var(--muted);
  font-size: 0.72rem;
}

.filter-panel-title em {
  padding: 3px 7px;
  border-radius: 999px;
  color: var(--tone-info);
  background: var(--tone-info-soft);
  font-size: 0.68rem;
  font-style: normal;
  font-weight: 800;
  white-space: nowrap;
}

.text-button {
  border: 0;
  color: var(--tone-info);
  background: transparent;
  cursor: pointer;
  font-weight: 700;
}

.filter-grid {
  display: grid;
  grid-template-columns:
    minmax(150px, 1fr)
    minmax(220px, 1.5fr)
    minmax(180px, 1.2fr)
    minmax(270px, 1.6fr);
  gap: 9px 10px;
  padding: 10px 12px 12px;
}

.filter-grid label {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 7px;
  min-width: 0;
}

.filter-grid label > span {
  color: #4f5f79;
  font-size: 0.73rem;
  font-weight: 700;
  white-space: nowrap;
}

.filter-grid input,
.filter-grid select {
  width: 100%;
  min-width: 0;
  height: 34px;
  padding: 0 9px;
  border: 1px solid var(--line-strong);
  border-radius: 5px;
  outline: none;
  color: var(--text);
  background: #fff;
}

.filter-grid input:focus,
.filter-grid select:focus {
  border-color: var(--tone-info);
  box-shadow: 0 0 0 3px var(--tone-info-soft);
}

.filter-grid input:disabled,
.filter-grid select:disabled {
  color: #8995a8;
  background: #f1f4f8;
  cursor: not-allowed;
}

.filter-actions {
  display: flex;
  grid-column: -2 / -1;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.filter-actions button,
.report-state button,
.pagination button {
  min-height: 34px;
  padding: 0 16px;
  border-radius: 5px;
  cursor: pointer;
  font-weight: 750;
}

.secondary-button,
.pagination button {
  border: 1px solid var(--line-strong);
  background: #fff;
}

.primary-button,
.report-state button {
  border: 1px solid var(--tone-info);
  color: #fff;
  background: var(--tone-info);
}

.capacity-button {
  border: 1px solid var(--tone-info);
  color: var(--tone-info);
  background: var(--tone-info-soft);
}

.capacity-button:not(:disabled):hover {
  color: #fff;
  background: var(--tone-info);
}

.filter-actions button:disabled,
.pagination button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.transaction-date-hint {
  grid-column: 1 / -1;
  margin: -2px 0 0;
  color: #6c788b;
  font-size: 0.67rem;
  font-weight: 650;
}

.capacity-result {
  display: grid;
  grid-column: 1 / -1;
  gap: 9px;
  padding: 10px;
  border: 1px solid #9bbdee;
  border-radius: 8px;
  color: #344b6b;
  background: #f0f6ff;
}

.capacity-result > header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.capacity-result > header > div {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.capacity-result span,
.capacity-result small,
.capacity-result dt {
  color: #5d6d84;
  font-size: 0.72rem;
  font-weight: 700;
}

.capacity-result > header strong {
  color: #1f5fa4;
  font-size: 0.95rem;
}

.capacity-result > header button {
  min-height: 28px;
  padding: 3px 8px;
  border: 1px solid #9bbdee;
  border-radius: 5px;
  color: #245c9f;
  background: #fff;
  font: inherit;
  font-size: 0.68rem;
  font-weight: 750;
  cursor: pointer;
}

.capacity-result-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(235px, 1fr));
  gap: 8px;
  max-height: 286px;
  overflow-y: auto;
}

.capacity-result-list article {
  display: grid;
  gap: 7px;
  padding: 9px 10px;
  border: 1px solid #c5d8f2;
  border-radius: 7px;
  background: #fff;
}

.capacity-result-list article > div {
  display: flex;
  align-items: baseline;
  gap: 7px;
}

.capacity-result-list article > div strong {
  color: #245c9f;
}

.capacity-result-list dl {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
  margin: 0;
}

.capacity-result-list dl > div {
  display: grid;
  gap: 2px;
}

.capacity-result-list dt,
.capacity-result-list dd {
  margin: 0;
}

.capacity-result-list dd {
  color: #31445f;
  font-size: 0.76rem;
  font-weight: 800;
}

.capacity-bottleneck-toggle {
  justify-self: start;
  padding: 2px 0;
  border: 0;
  color: #3973b5;
  background: transparent;
  font: inherit;
  font-size: 0.68rem;
  font-weight: 800;
  cursor: pointer;
}

.capacity-bottleneck-toggle:hover {
  color: #1f5a9a;
  text-decoration: underline;
}

.capacity-bottleneck-detail {
  margin: -2px 0 0;
  padding: 6px 8px;
  border-left: 3px solid #8eb5e8;
  border-radius: 3px;
  color: #31445f;
  background: #eef5ff;
  font-size: 0.72rem;
  font-weight: 750;
}

.report-section {
  overflow: hidden;
  border-radius: 10px;
}

.report-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  min-height: 44px;
  padding: 7px 12px;
  border-bottom: 1px solid var(--line);
  background: #f8fafd;
}

.report-summary {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 10px;
}

.report-summary > strong {
  color: var(--tone-info);
  font-size: 1.2rem;
}

.report-summary > i {
  width: 1px;
  height: 18px;
  background: var(--line-strong);
}

.report-summary span {
  color: var(--muted);
}

.report-summary b {
  color: var(--text);
}

.report-summary .attention b {
  color: var(--tone-warn);
}

.report-summary .missing b {
  color: var(--tone-danger);
}

.report-range {
  color: var(--muted);
  font-size: 0.73rem;
  white-space: nowrap;
}

.report-toolbar-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 9px;
}

.column-picker {
  position: relative;
}

.column-picker-trigger,
.report-export-button {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 30px;
  padding: 5px 9px;
  border: 1px solid var(--line-strong);
  border-radius: 5px;
  color: #31445f;
  background: #fff;
  font: inherit;
  font-size: 0.72rem;
  font-weight: 800;
  cursor: pointer;
}

.report-export-button {
  color: #fff;
  border-color: var(--tone-info);
  background: var(--tone-info);
}

.report-export-button:hover:not(:disabled) {
  border-color: #1e5f9f;
  background: #1e5f9f;
}

.report-export-button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.column-picker-trigger:hover,
.column-picker-trigger[aria-expanded="true"] {
  border-color: var(--tone-info);
  color: var(--tone-info);
  background: var(--tone-info-soft);
}

.column-picker-trigger b {
  padding: 1px 5px;
  border-radius: 999px;
  color: var(--tone-info);
  background: var(--tone-info-soft);
  font-size: 0.66rem;
  font-variant-numeric: tabular-nums;
}

.column-picker-popover {
  position: absolute;
  z-index: 20;
  top: calc(100% + 7px);
  right: 0;
  display: grid;
  gap: 10px;
  width: 440px;
  padding: 14px;
  border: 1px solid var(--line-strong);
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 12px 30px rgba(31, 56, 91, 0.18);
}

.column-picker-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 0 2px 10px;
  border-bottom: 1px solid var(--line);
}

.column-picker-heading > div {
  display: flex;
  align-items: baseline;
  gap: 7px;
}

.column-picker-heading strong {
  color: var(--text);
  font-size: 0.82rem;
}

.column-picker-heading span {
  color: var(--muted);
  font-size: 0.68rem;
  font-weight: 650;
}

.column-picker-heading button {
  padding: 5px 7px;
  border: 0;
  border-radius: 5px;
  color: var(--tone-info);
  background: transparent;
  font: inherit;
  font-size: 0.7rem;
  font-weight: 800;
  cursor: pointer;
}

.column-picker-heading button:disabled {
  color: var(--muted);
  cursor: default;
  opacity: 0.6;
}

.column-picker-heading button:hover:not(:disabled) {
  background: var(--tone-info-soft);
}

.column-picker-options {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 9px;
  max-height: min(440px, 62vh);
  overflow-y: auto;
  padding: 1px;
}

.column-picker-options label {
  position: relative;
  display: flex;
  min-height: 48px;
  align-items: center;
  gap: 10px;
  min-width: 0;
  padding: 9px 12px;
  border: 1px solid #b9cff4;
  border-radius: 12px;
  color: #31445f;
  background: #fff;
  font-size: 0.76rem;
  font-weight: 750;
  cursor: pointer;
  transition:
    border-color 120ms ease,
    background-color 120ms ease,
    box-shadow 120ms ease;
}

.column-picker-options label.selected {
  border-color: #8fb5f7;
  background: #f1f6ff;
}

.column-picker-options label:hover {
  border-color: #76a5f2;
  background: #f6f9ff;
}

.column-picker-options label:focus-within {
  outline: 2px solid rgba(55, 122, 226, 0.3);
  outline-offset: 1px;
}

.column-picker-options input {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  opacity: 0;
  pointer-events: none;
}

.column-option-indicator {
  display: flex;
  flex: 0 0 20px;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: 2px solid #70a0ed;
  border-radius: 50%;
  background: #fff;
}

.column-option-indicator::after {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #4e89e7;
  content: "";
  opacity: 0;
  transform: scale(0.45);
  transition:
    opacity 120ms ease,
    transform 120ms ease;
}

.column-picker-options input:checked + .column-option-indicator::after {
  opacity: 1;
  transform: scale(1);
}

.column-option-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.column-picker-popover small {
  padding: 9px 2px 0;
  border-top: 1px solid var(--line);
  color: var(--muted);
  font-size: 0.65rem;
  font-weight: 600;
}

.table-frame {
  width: 100%;
}

.table-scroll {
  max-height: calc(100dvh - 322px);
  min-height: 300px;
  overflow: auto;
  outline: none;
}

.table-scroll:focus-visible {
  box-shadow: inset 0 0 0 2px var(--tone-info);
}

table {
  width: 100%;
  min-width: 720px;
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
  font-size: 0.75rem;
}

th,
td {
  height: 34px;
  padding: 6px 8px;
  overflow: hidden;
  border-right: 1px solid #d8e1ec;
  border-bottom: 1px solid #d8e1ec;
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
}

th {
  position: sticky;
  z-index: 3;
  top: 0;
  height: 36px;
  color: #31445f;
  background: #dce8f7;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.02em;
}

tbody tr:nth-child(even) td {
  background: #f2f6fb;
}

tbody tr:nth-child(odd) td {
  background: #fff;
}

tbody tr:hover td {
  background: #e8f1ff;
}

tbody tr.water-low td {
  background: #fff8ea;
}

tbody tr.water-empty td {
  background: #fff0ef;
}

tbody tr.configuration-missing td {
  box-shadow: inset 0 -1px 0 rgba(216, 71, 63, 0.16);
}

.index-column {
  width: 58px;
  text-align: center;
}

.number-column,
.number-cell {
  width: 84px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.code-cell {
  color: #274e86;
  font-weight: 750;
}

.fixture-image-trigger {
  padding: 2px 3px;
  border: 0;
  border-bottom: 1px dashed #6e9eda;
  color: #245f9f;
  background: transparent;
  font: inherit;
  font-weight: 800;
  cursor: pointer;
}

.fixture-image-trigger:hover {
  color: #17487e;
  border-bottom-style: solid;
}

.fixture-image-trigger:focus-visible {
  border-radius: 3px;
  outline: 2px solid rgba(55, 122, 226, 0.34);
  outline-offset: 2px;
}

.name-cell {
  width: 220px;
}

.station-cell {
  display: grid;
  line-height: 1.15;
}

.station-cell small {
  overflow: hidden;
  color: var(--muted);
  text-overflow: ellipsis;
}

.status-badge,
.configuration-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 58px;
  padding: 3px 7px;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 800;
}

.status-normal,
.configuration-configured {
  color: #16784e;
  background: var(--tone-success-soft);
}

.status-low {
  color: #a66308;
  background: var(--tone-warn-soft);
}

.status-empty,
.configuration-unconfigured {
  color: #b13731;
  background: var(--tone-danger-soft);
}

.status-na,
.configuration-unbound {
  color: var(--tone-muted);
  background: var(--tone-muted-soft);
}

.empty-cell {
  height: 180px;
  text-align: center;
}

.empty-cell strong,
.empty-cell span {
  display: block;
}

.empty-cell span {
  margin-top: 5px;
  color: var(--muted);
}

.report-state {
  display: grid;
  place-items: center;
  align-content: center;
  min-height: 330px;
  padding: 30px;
  text-align: center;
}

.report-state strong {
  font-size: 1.1rem;
}

.report-state p {
  margin: 7px 0 14px;
  color: var(--muted);
}

.report-state.error strong {
  color: var(--tone-danger);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 8px 12px;
  border-top: 1px solid var(--line);
  background: #f8fafd;
}

.fixture-image-layer {
  position: fixed;
  z-index: 145;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 18px;
}

.fixture-image-backdrop {
  position: absolute;
  inset: 0;
  width: 100%;
  border: 0;
  background: rgba(15, 31, 52, 0.54);
  cursor: default;
}

.fixture-image-dialog {
  position: relative;
  z-index: 1;
  width: min(760px, 100%);
  max-height: min(760px, calc(100dvh - 36px));
  overflow: hidden;
  border: 1px solid #c5d5e9;
  border-radius: 13px;
  background: #fff;
  box-shadow: 0 24px 70px rgba(16, 36, 64, 0.3);
}

.fixture-image-dialog header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 12px 14px;
  border-bottom: 1px solid #d7e2ef;
  background: #f6f9fd;
}

.fixture-image-dialog header > div {
  display: grid;
  grid-template-columns: auto auto;
  align-items: baseline;
  gap: 2px 9px;
}

.fixture-image-dialog header span {
  grid-column: 1 / -1;
  color: #61718a;
  font-size: 0.68rem;
  font-weight: 750;
}

.fixture-image-dialog header strong {
  color: #245c9f;
  font-size: 0.95rem;
}

.fixture-image-dialog header small {
  color: #61718a;
}

.fixture-image-dialog header button {
  min-height: 30px;
  padding: 4px 10px;
  border: 1px solid #a8bdd8;
  border-radius: 6px;
  color: #344b6b;
  background: #fff;
  font: inherit;
  font-size: 0.72rem;
  font-weight: 750;
  cursor: pointer;
}

.fixture-image-content {
  display: grid;
  min-height: 300px;
  max-height: calc(100dvh - 120px);
  place-items: center;
  overflow: auto;
  padding: 18px;
  background:
    linear-gradient(45deg, #f3f6fa 25%, transparent 25%),
    linear-gradient(-45deg, #f3f6fa 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #f3f6fa 75%),
    linear-gradient(-45deg, transparent 75%, #f3f6fa 75%);
  background-position:
    0 0,
    0 8px,
    8px -8px,
    -8px 0;
  background-size: 16px 16px;
}

.fixture-image-content > span {
  color: #61718a;
  font-weight: 750;
}

.fixture-image-content img {
  display: block;
  max-width: 100%;
  max-height: calc(100dvh - 160px);
  border-radius: 7px;
  object-fit: contain;
  box-shadow: 0 8px 24px rgba(31, 53, 82, 0.14);
}

.fixture-image-empty {
  display: grid;
  gap: 5px;
  padding: 30px;
  border-radius: 9px;
  color: #61718a;
  background: rgba(255, 255, 255, 0.92);
  text-align: center;
}

.fixture-image-empty strong {
  color: #344b6b;
}

@media (max-width: 1100px) {
  .filter-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .table-scroll {
    max-height: calc(100dvh - 395px);
  }
}

@media (max-width: 680px) {
  .guest-report-page {
    padding: 12px 8px 24px;
  }

  .report-heading {
    align-items: stretch;
    flex-direction: column;
    gap: 10px;
  }

  .scope-badge {
    grid-template-columns: auto 1fr;
    min-width: 0;
  }

  .filter-grid {
    grid-template-columns: 1fr;
  }

  .filter-grid label {
    grid-template-columns: 70px minmax(0, 1fr);
  }

  .filter-actions {
    justify-content: stretch;
  }

  .filter-actions button {
    flex: 1;
  }

  .capacity-result {
    padding: 9px;
  }

  .capacity-result > header {
    align-items: flex-start;
  }

  .capacity-result > header > div {
    align-items: flex-start;
    flex-direction: column;
    gap: 2px;
  }

  .capacity-result-list {
    grid-template-columns: 1fr;
  }

  .filter-panel-title span {
    display: none;
  }

  .filter-panel-title div {
    align-items: flex-start;
    flex-direction: column;
    gap: 4px;
  }

  .report-toolbar {
    align-items: flex-start;
    flex-direction: column;
    gap: 5px;
  }

  .report-range {
    white-space: normal;
  }

  .report-toolbar-actions {
    justify-content: space-between;
    width: 100%;
  }

  .column-picker-popover {
    width: min(360px, calc(100vw - 32px));
  }

  .column-picker-options {
    grid-template-columns: 1fr;
  }

  .table-scroll {
    max-height: 62dvh;
    min-height: 360px;
  }

  .pagination {
    justify-content: space-between;
  }
}
</style>
