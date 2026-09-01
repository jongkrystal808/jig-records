import type {
  ConfigurationReportOptions,
  ConfigurationReportPage,
  ConfigurationReportQuery,
  InventoryDashboardSummary,
  InventoryRecalculateResult,
  IdentifierStockSummary,
  MaterialTransaction,
  MaterialTransactionPage,
  StockSummary,
  StockTransactionCreate,
  TransactionOverviewPage,
  TransactionReverseResult,
  TransactionQueryFilters
} from "@/types";

import { request, requestBlob, requestText, setOptionalParam, setOptionalParams } from "@/api/core";

type AlertRow = {
  fixture_id: number;
  fixture_code: string;
  fixture_name: string;
  stock_qty: number;
  customer_supplied_qty: number;
  self_purchased_qty: number;
  min_stock_qty: number;
  stock_status: "low_stock" | "out_of_stock";
};

function buildTransactionParams(limit: number, customerId?: number, filters?: TransactionQueryFilters): URLSearchParams {
  const params = new URLSearchParams({ limit: String(limit) });
  return appendTransactionFilterParams(params, customerId, filters);
}

function buildTransactionOverviewParams(page: number, pageSize: number, customerId?: number, filters?: TransactionQueryFilters): URLSearchParams {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  return appendTransactionFilterParams(params, customerId, filters);
}

function appendTransactionFilterParams(
  params: URLSearchParams,
  customerId?: number,
  filters?: TransactionQueryFilters
): URLSearchParams {
  setOptionalParam(params, "customer_id", customerId);
  setOptionalParams(params, "transaction_type", filters?.transaction_type);
  setOptionalParams(params, "ownership_type", filters?.ownership_type);
  setOptionalParam(params, "date_from", filters?.date_from);
  setOptionalParam(params, "date_to", filters?.date_to);
  setOptionalParam(params, "fixture_code", filters?.fixture_code);
  setOptionalParam(params, "transaction_no", filters?.transaction_no);
  setOptionalParam(params, "identifier", filters?.identifier);
  setOptionalParam(params, "created_by", filters?.created_by);
  return params;
}

function buildConfigurationReportParams(params: ConfigurationReportQuery): URLSearchParams {
  const search = new URLSearchParams({ customer_id: String(params.customer_id) });
  setOptionalParam(search, "page", params.page);
  setOptionalParam(search, "page_size", params.page_size);
  setOptionalParam(search, "keyword", params.keyword);
  setOptionalParams(search, "fixture_status", params.fixture_status);
  setOptionalParam(search, "fixture_id", params.fixture_id);
  setOptionalParam(search, "model_id", params.model_id);
  setOptionalParam(search, "station_id", params.station_id);
  setOptionalParams(search, "water_status", params.water_status);
  setOptionalParam(search, "storage", params.storage);
  setOptionalParams(search, "configuration_status", params.configuration_status);
  setOptionalParams(search, "transaction_type", params.transaction_type);
  setOptionalParams(search, "ownership_type", params.ownership_type);
  setOptionalParam(search, "date_from", params.date_from);
  setOptionalParam(search, "date_to", params.date_to);
  setOptionalParam(search, "sort_by", params.sort_by);
  setOptionalParam(search, "sort_direction", params.sort_direction);
  setOptionalParam(search, "priority", params.priority);
  if (params.include_transaction_details) {
    search.set("include_transaction_details", "true");
  }
  return search;
}

export const inventoryApi = {
  getConfigurationReport(params: ConfigurationReportQuery) {
    return request<ConfigurationReportPage>(
      `/inventory/configuration-report?${buildConfigurationReportParams(params).toString()}`
    );
  },
  getConfigurationReportOptions(params: ConfigurationReportQuery) {
    return request<ConfigurationReportOptions>(
      `/inventory/configuration-report/options?${buildConfigurationReportParams(params).toString()}`
    );
  },
  exportConfigurationReport(
    params: ConfigurationReportQuery & {
      file_format: "csv" | "xlsx";
      columns: string[];
    }
  ) {
    const search = buildConfigurationReportParams(params);
    search.set("file_format", params.file_format);
    if (params.columns.length) search.set("columns", params.columns.join(","));
    return requestBlob(`/inventory/configuration-report/export?${search.toString()}`);
  },
  listStock(customerId?: number) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<StockSummary[]>(`/inventory/stock${suffix}`);
  },
  listAlerts(customerId?: number) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<AlertRow[]>(`/inventory/alerts${suffix}`);
  },
  listDashboardSummary(customerId?: number) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<InventoryDashboardSummary>(`/inventory/dashboard-summary${suffix}`);
  },
  listIdentifierStockSummary(customerId?: number, fixtureId?: number) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    setOptionalParam(params, "fixture_id", fixtureId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<IdentifierStockSummary[]>(`/inventory/identifier-stock-summary${suffix}`);
  },
  listTransactions(limit = 20, customerId?: number, filters?: TransactionQueryFilters) {
    return request<MaterialTransaction[]>(`/inventory/transactions?${buildTransactionParams(limit, customerId, filters).toString()}`);
  },
  listTransactionLedgerPage(page = 1, pageSize = 20, customerId?: number, filters?: TransactionQueryFilters) {
    return request<MaterialTransactionPage>(
      `/inventory/admin/transactions?${buildTransactionOverviewParams(page, pageSize, customerId, filters).toString()}`
    );
  },
  listTransactionOverviewPage(page = 1, pageSize = 50, customerId?: number, filters?: TransactionQueryFilters) {
    return request<TransactionOverviewPage>(
      `/inventory/transactions/overview?${buildTransactionOverviewParams(page, pageSize, customerId, filters).toString()}`
    );
  },
  exportTransactionsCsv(customerId?: number, filters?: TransactionQueryFilters) {
    const search = new URLSearchParams();
    appendTransactionFilterParams(search, customerId, filters);
    return requestBlob(`/inventory/transactions/export?${search.toString()}`);
  },
  exportTransactionReport(params: {
    customer_id: number;
    report_type: "summary" | "detail";
    file_format: "xlsx" | "txt";
    transaction_type?: Array<"receipt" | "return">;
    date_from?: string;
    date_to?: string;
    fixture_code?: string;
    transaction_no?: string;
    ownership_type?: Array<"customer_supplied" | "self_purchased">;
    identifier?: string;
  }) {
    const search = new URLSearchParams({
      customer_id: String(params.customer_id),
      report_type: params.report_type,
      file_format: params.file_format
    });
    setOptionalParams(search, "transaction_type", params.transaction_type);
    setOptionalParam(search, "date_from", params.date_from);
    setOptionalParam(search, "date_to", params.date_to);
    setOptionalParam(search, "fixture_code", params.fixture_code);
    setOptionalParam(search, "transaction_no", params.transaction_no);
    setOptionalParams(search, "ownership_type", params.ownership_type);
    setOptionalParam(search, "identifier", params.identifier);
    return requestBlob(`/inventory/transactions/export-report?${search.toString()}`);
  },
  previewTransactionReportExport(params: {
    customer_id: number;
    report_type: "summary" | "detail";
    transaction_type?: Array<"receipt" | "return">;
    date_from?: string;
    date_to?: string;
    fixture_code?: string;
    transaction_no?: string;
    ownership_type?: Array<"customer_supplied" | "self_purchased">;
    identifier?: string;
  }) {
    const search = new URLSearchParams({
      customer_id: String(params.customer_id),
      report_type: params.report_type
    });
    setOptionalParams(search, "transaction_type", params.transaction_type);
    setOptionalParam(search, "date_from", params.date_from);
    setOptionalParam(search, "date_to", params.date_to);
    setOptionalParam(search, "fixture_code", params.fixture_code);
    setOptionalParam(search, "transaction_no", params.transaction_no);
    setOptionalParams(search, "ownership_type", params.ownership_type);
    setOptionalParam(search, "identifier", params.identifier);
    return request<{ report_type: "summary" | "detail"; column_count: number; raw_item_count: number; export_row_count: number }>(
      `/inventory/transactions/export-report/preview?${search.toString()}`
    );
  },
  downloadTransactionTemplateCsv() {
    return requestText("/inventory/transactions/template");
  },
  importTransactionsCsv(customerId: number, content: string, filename?: string) {
    return request<{ imported_count: number }>(
      `/inventory/transactions/import?customer_id=${customerId}`,
      { method: "POST", body: JSON.stringify({ filename, content }) }
    );
  },
  createReceipt(payload: StockTransactionCreate) {
    return request<void>("/inventory/receipts", { method: "POST", body: JSON.stringify(payload) });
  },
  createReceiptWithOptions(payload: StockTransactionCreate, options?: { confirmDuplicate?: boolean }) {
    const params = new URLSearchParams();
    if (options?.confirmDuplicate) {
      params.set("confirm_duplicate", "true");
    }
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<void>(`/inventory/receipts${suffix}`, { method: "POST", body: JSON.stringify(payload) });
  },
  createReturn(payload: StockTransactionCreate) {
    return request<void>("/inventory/returns", { method: "POST", body: JSON.stringify(payload) });
  },
  createReturnWithOptions(payload: StockTransactionCreate, options?: { confirmDuplicate?: boolean }) {
    const params = new URLSearchParams();
    if (options?.confirmDuplicate) {
      params.set("confirm_duplicate", "true");
    }
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<void>(`/inventory/returns${suffix}`, { method: "POST", body: JSON.stringify(payload) });
  },
  reverseTransaction(transactionId: number, customerId: number) {
    return request<TransactionReverseResult>(`/inventory/admin/transactions/${transactionId}?customer_id=${customerId}`, { method: "DELETE" });
  },
  recalculateInventoryState(customerId: number) {
    return request<InventoryRecalculateResult>(`/inventory/admin/recalculate?customer_id=${customerId}`, { method: "POST" });
  }
};
