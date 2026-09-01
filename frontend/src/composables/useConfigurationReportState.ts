import { computed, onBeforeUnmount, reactive, ref, type Ref } from "vue";
import type { LocationQueryRaw, RouteLocationNormalizedLoaded, Router } from "vue-router";

import { api } from "@/api";
import { selectedCustomerId } from "@/appState";
import { pushToast } from "@/toastState";
import type { ConfigurationReportQuery } from "@/types";
import { pendingReportConditionCount } from "@/utils/reportFilterState";
import type { ReportColumnKey } from "@/utils/reportColumnPresets";
import {
  buildReportTransactionQuery,
  reportTransactionDateError,
  type ReportTransactionMode
} from "@/utils/reportTransactionFilters";

export type WaterFilter = "attention" | "low" | "empty" | "normal";
export type FixtureStatusFilter = "active" | "inactive";
export type TransactionActivityFilters = {
  mode: ReportTransactionMode;
  dateFrom: string;
  dateTo: string;
  ownershipType: Array<"customer_supplied" | "self_purchased">;
};
export type ReportFilters = {
  keyword: string;
  fixtureStatus: FixtureStatusFilter[];
  fixtureId: string;
  stationId: string;
  modelId: string;
  waterStatus: WaterFilter[];
  storage: string;
  configurationStatus: Array<"configured" | "unconfigured" | "unbound">;
};
export type LinkedFilterKey = Exclude<keyof ReportFilters, "fixtureStatus">;

export const linkedFilterKeys: LinkedFilterKey[] = [
  "keyword",
  "fixtureId",
  "modelId",
  "stationId",
  "waterStatus",
  "storage",
  "configurationStatus"
];

const priorityApiKeys: Record<LinkedFilterKey, string> = {
  keyword: "keyword",
  fixtureId: "fixture_id",
  modelId: "model_id",
  stationId: "station_id",
  waterStatus: "water_status",
  storage: "storage",
  configurationStatus: "configuration_status"
};

export function createEmptyReportFilters(): ReportFilters {
  return {
    keyword: "",
    fixtureStatus: ["active"],
    fixtureId: "",
    stationId: "",
    modelId: "",
    waterStatus: [],
    storage: "",
    configurationStatus: []
  };
}

export function createEmptyTransactionFilters(): TransactionActivityFilters {
  return { mode: "", dateFrom: "", dateTo: "", ownershipType: [] };
}

function todayDateValue(): string {
  const today = new Date();
  return [
    today.getFullYear(),
    String(today.getMonth() + 1).padStart(2, "0"),
    String(today.getDate()).padStart(2, "0")
  ].join("-");
}

function allowedId(value: unknown): string {
  if (typeof value !== "string") return "";
  const id = Number(value);
  return Number.isInteger(id) && id > 0 ? value : "";
}

export function useConfigurationReportState(options: {
  route: RouteLocationNormalizedLoaded;
  router: Router;
  isMobileReportMode: Ref<boolean>;
}) {
  const draftFilters = reactive<ReportFilters>(createEmptyReportFilters());
  const appliedFilters = reactive<ReportFilters>(createEmptyReportFilters());
  const draftTransactionFilters = reactive<TransactionActivityFilters>(createEmptyTransactionFilters());
  const appliedTransactionFilters = reactive<TransactionActivityFilters>(createEmptyTransactionFilters());
  const filterOrder = ref<LinkedFilterKey[]>([]);
  const page = ref(1);
  const pageSize = ref<20 | 50 | 100>(options.isMobileReportMode.value ? 20 : 50);
  const jumpPage = ref(1);
  const routeSyncing = ref(false);
  const exportFormat = ref<"csv" | "xlsx">("xlsx");
  const exportFeedbackMessage = ref("");
  const exportLoading = ref(false);
  let exportFeedbackTimer: ReturnType<typeof setTimeout> | null = null;

  const usesTransactionDateRange = computed(() =>
    ["range_receipt", "range_return"].includes(draftTransactionFilters.mode)
  );
  const transactionDateValidationMessage = computed(() =>
    reportTransactionDateError(
      draftTransactionFilters.mode,
      draftTransactionFilters.dateFrom,
      draftTransactionFilters.dateTo
    )
  );
  const activeFilterCount = computed(
    () =>
      Object.values(appliedFilters).filter((value) => String(value).trim()).length +
      (appliedTransactionFilters.mode ? 1 : 0) +
      (appliedTransactionFilters.ownershipType.length ? 1 : 0)
  );
  const pendingFilterCount = computed(() =>
    pendingReportConditionCount(
      draftFilters,
      appliedFilters,
      draftTransactionFilters,
      appliedTransactionFilters
    )
  );
  const hasPendingFilters = computed(() => pendingFilterCount.value > 0);

  function buildReportApiQuery(
    filters: ReportFilters,
    transactionFilters: TransactionActivityFilters,
    queryOptions: { includeDetails?: boolean; targetPage?: number } = {}
  ): ConfigurationReportQuery | null {
    const customerId = selectedCustomerId.value;
    if (!customerId) return null;
    const transactionQuery = buildReportTransactionQuery(
      transactionFilters.mode,
      transactionFilters.dateFrom,
      transactionFilters.dateTo,
      todayDateValue()
    );
    return {
      customer_id: customerId,
      page: queryOptions.targetPage ?? page.value,
      page_size: pageSize.value,
      keyword: filters.keyword.trim() || undefined,
      fixture_status: [...filters.fixtureStatus],
      fixture_id: filters.fixtureId ? Number(filters.fixtureId) : undefined,
      model_id: filters.modelId ? Number(filters.modelId) : undefined,
      station_id: filters.stationId ? Number(filters.stationId) : undefined,
      water_status: filters.waterStatus.length ? [...filters.waterStatus] : undefined,
      storage: filters.storage.trim() || undefined,
      configuration_status: filters.configurationStatus.length ? [...filters.configurationStatus] : undefined,
      transaction_type: transactionQuery?.transaction_type
        ? [transactionQuery.transaction_type as "receipt" | "return"]
        : undefined,
      ownership_type:
        transactionQuery && transactionFilters.ownershipType.length
          ? [...transactionFilters.ownershipType]
          : undefined,
      date_from: transactionQuery?.date_from,
      date_to: transactionQuery?.date_to,
      sort_by: "fixture_code",
      sort_direction: "asc",
      priority:
        filterOrder.value
          .filter((key) => String(filters[key]).trim())
          .map((key) => priorityApiKeys[key])
          .join(",") || undefined,
      include_transaction_details: queryOptions.includeDetails === true
    };
  }

  function buildRouteQuery(): LocationQueryRaw {
    const query: LocationQueryRaw = { page: String(page.value), page_size: String(pageSize.value) };
    if (options.route.name === "search") {
      query.ui_surface = "form";
      query.home_mode = "report";
    }
    if (selectedCustomerId.value) query.customer = String(selectedCustomerId.value);
    if (appliedFilters.keyword.trim()) query.q = appliedFilters.keyword.trim();
    if (appliedFilters.fixtureStatus.join(",") !== "active") query.fixture_status = appliedFilters.fixtureStatus;
    if (appliedFilters.fixtureId) query.fixture = appliedFilters.fixtureId;
    if (appliedFilters.stationId) query.station = appliedFilters.stationId;
    if (appliedFilters.modelId) query.model = appliedFilters.modelId;
    if (appliedFilters.waterStatus.length) query.water = appliedFilters.waterStatus;
    if (appliedFilters.storage.trim()) query.storage = appliedFilters.storage.trim();
    if (appliedFilters.configurationStatus.length) query.configuration = appliedFilters.configurationStatus;
    if (appliedTransactionFilters.mode) {
      query.transaction_activity = appliedTransactionFilters.mode;
      if (appliedTransactionFilters.ownershipType.length) {
        query.transaction_ownership = appliedTransactionFilters.ownershipType;
      }
      if (["range_receipt", "range_return"].includes(appliedTransactionFilters.mode)) {
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

  async function syncRoute(): Promise<void> {
    if (routeSyncing.value) return;
    routeSyncing.value = true;
    try {
      await options.router.replace({ path: options.route.path, query: buildRouteQuery() });
    } finally {
      routeSyncing.value = false;
    }
  }

  function applyRouteState(): void {
    const nextFilters: ReportFilters = {
      keyword: typeof options.route.query.q === "string" ? options.route.query.q : "",
      fixtureStatus: (Array.isArray(options.route.query.fixture_status) ? options.route.query.fixture_status : [options.route.query.fixture_status])
        .filter((value): value is FixtureStatusFilter => value === "active" || value === "inactive").length
          ? (Array.isArray(options.route.query.fixture_status) ? options.route.query.fixture_status : [options.route.query.fixture_status])
              .filter((value): value is FixtureStatusFilter => value === "active" || value === "inactive")
          : ["active"],
      fixtureId: allowedId(options.route.query.fixture),
      stationId: allowedId(options.route.query.station),
      modelId: allowedId(options.route.query.model),
      waterStatus: (Array.isArray(options.route.query.water) ? options.route.query.water : [options.route.query.water])
        .filter((value): value is WaterFilter => ["attention", "low", "empty", "normal"].includes(String(value))),
      storage: typeof options.route.query.storage === "string" ? options.route.query.storage : "",
      configurationStatus: (Array.isArray(options.route.query.configuration) ? options.route.query.configuration : [options.route.query.configuration])
        .filter((value): value is "configured" | "unconfigured" | "unbound" => ["configured", "unconfigured", "unbound"].includes(String(value)))
    };
    Object.assign(draftFilters, nextFilters);
    Object.assign(appliedFilters, nextFilters);
    const routeTransactionValue =
      typeof options.route.query.transaction_activity === "string"
        ? options.route.query.transaction_activity
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
      typeof options.route.query.transaction_date_from === "string"
        ? options.route.query.transaction_date_from
        : "";
    const routeDateTo =
      typeof options.route.query.transaction_date_to === "string"
        ? options.route.query.transaction_date_to
        : "";
    const routeRangeIsComplete =
      !routeTransactionMode.startsWith("range") || Boolean(routeDateFrom && routeDateTo);
    const routeOwnership = (Array.isArray(options.route.query.transaction_ownership)
      ? options.route.query.transaction_ownership
      : [options.route.query.transaction_ownership])
      .filter((value): value is "customer_supplied" | "self_purchased" => value === "customer_supplied" || value === "self_purchased");
    const nextTransactionFilters: TransactionActivityFilters = {
      mode: routeRangeIsComplete ? routeTransactionMode : "",
      dateFrom: routeRangeIsComplete && routeTransactionMode.startsWith("range") ? routeDateFrom : "",
      dateTo: routeRangeIsComplete && routeTransactionMode.startsWith("range") ? routeDateTo : "",
      ownershipType: routeTransactionMode && routeRangeIsComplete ? routeOwnership : []
    };
    Object.assign(draftTransactionFilters, nextTransactionFilters);
    Object.assign(appliedTransactionFilters, nextTransactionFilters);
    const activeKeys = new Set(
      linkedFilterKeys.filter((key) => String(nextFilters[key]).trim().length > 0)
    );
    const routePriority =
      typeof options.route.query.priority === "string"
        ? options.route.query.priority
            .split(",")
            .filter(
              (key): key is LinkedFilterKey =>
                linkedFilterKeys.includes(key as LinkedFilterKey) && activeKeys.has(key as LinkedFilterKey)
            )
        : [];
    filterOrder.value = [
      ...new Set([...routePriority, ...linkedFilterKeys.filter((key) => activeKeys.has(key))])
    ];
    const requestedPage = Number(options.route.query.page);
    page.value = Number.isFinite(requestedPage) && requestedPage > 0 ? requestedPage : 1;
    const requestedPageSize = Number(options.route.query.page_size);
    pageSize.value = options.isMobileReportMode.value
      ? requestedPageSize === 50 || requestedPageSize === 100
        ? 50
        : 20
      : requestedPageSize === 100
        ? 100
        : 50;
    jumpPage.value = page.value;
  }

  function resetFilterState(): void {
    Object.assign(draftFilters, createEmptyReportFilters());
    Object.assign(appliedFilters, createEmptyReportFilters());
    Object.assign(draftTransactionFilters, createEmptyTransactionFilters());
    Object.assign(appliedTransactionFilters, createEmptyTransactionFilters());
    filterOrder.value = [];
    page.value = 1;
    jumpPage.value = 1;
  }

  function commitDraftFilters(): void {
    Object.assign(appliedFilters, draftFilters);
    Object.assign(appliedTransactionFilters, draftTransactionFilters);
  }

  function transactionFiltersAreValid(filters: TransactionActivityFilters): boolean {
    const message = reportTransactionDateError(filters.mode, filters.dateFrom, filters.dateTo);
    if (!message) return true;
    pushToast(message, "warning");
    return false;
  }

  async function exportFilteredRows(exportOptions: {
    reportTotal: number;
    effectiveVisibleColumns: ReportColumnKey[];
    showTransactionDetails: boolean;
  }): Promise<void> {
    if (exportOptions.reportTotal === 0 || exportLoading.value) {
      pushToast("目前篩選條件沒有可匯出的資料。", "warning");
      return;
    }
    const includeTransactionDetails =
      exportOptions.showTransactionDetails && Boolean(appliedTransactionFilters.mode);
    const query = buildReportApiQuery(appliedFilters, appliedTransactionFilters, {
      includeDetails: includeTransactionDetails
    });
    if (!query) return;
    exportLoading.value = true;
    try {
      const result = await api.exportConfigurationReport({
        ...query,
        file_format: exportFormat.value,
        columns: exportOptions.effectiveVisibleColumns,
        include_transaction_details: includeTransactionDetails
      });
      const objectUrl = URL.createObjectURL(result.blob);
      const fileName = result.filename ?? `fixture-inventory-report.${exportFormat.value}`;
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = fileName;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(objectUrl);
      const exportedRows = result.rowCount ?? exportOptions.reportTotal;
      const exportedColumns =
        result.columnCount ??
        exportOptions.effectiveVisibleColumns.length + (includeTransactionDetails ? 6 : 0);
      exportFeedbackMessage.value = `已匯出 ${exportedRows.toLocaleString("zh-TW")} 筆資料、${exportedColumns} 個欄位${includeTransactionDetails ? "（含收退料明細）" : ""}：${fileName}`;
      if (exportFeedbackTimer) clearTimeout(exportFeedbackTimer);
      exportFeedbackTimer = setTimeout(() => {
        exportFeedbackMessage.value = "";
        exportFeedbackTimer = null;
      }, 8000);
      pushToast(exportFeedbackMessage.value, "success", 5200);
    } catch (error) {
      pushToast(error instanceof Error ? error.message : "報表匯出失敗。", "error");
    } finally {
      exportLoading.value = false;
    }
  }

  onBeforeUnmount(() => {
    if (exportFeedbackTimer) clearTimeout(exportFeedbackTimer);
  });

  return {
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
    applyRouteState,
    resetFilterState,
    commitDraftFilters,
    transactionFiltersAreValid,
    exportFilteredRows
  };
}
