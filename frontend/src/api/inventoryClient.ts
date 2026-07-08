import type {
  IdentifierStockSummary,
  MaterialTransaction,
  StockSummary,
  StockTransactionCreate,
  TransactionQueryFilters
} from "@/types";

import { request, requestBlob, requestText, setOptionalParam } from "@/api/core";

type AlertRow = {
  fixture_id: number;
  fixture_code: string;
  fixture_name: string;
  stock_qty: number;
  min_stock_qty: number;
  stock_status: "low_stock" | "out_of_stock";
};

function buildTransactionParams(limit: number, customerId?: number, filters?: TransactionQueryFilters): URLSearchParams {
  const params = new URLSearchParams({ limit: String(limit) });
  setOptionalParam(params, "customer_id", customerId);
  setOptionalParam(params, "transaction_type", filters?.transaction_type);
  setOptionalParam(params, "date_from", filters?.date_from);
  setOptionalParam(params, "date_to", filters?.date_to);
  setOptionalParam(params, "fixture_code", filters?.fixture_code);
  setOptionalParam(params, "transaction_no", filters?.transaction_no);
  setOptionalParam(params, "identifier", filters?.identifier);
  setOptionalParam(params, "created_by", filters?.created_by);
  return params;
}

export const inventoryApi = {
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
  listIdentifierStockSummary(customerId?: number) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<IdentifierStockSummary[]>(`/inventory/identifier-stock-summary${suffix}`);
  },
  listTransactions(limit = 20, customerId?: number, filters?: TransactionQueryFilters) {
    return request<MaterialTransaction[]>(`/inventory/transactions?${buildTransactionParams(limit, customerId, filters).toString()}`);
  },
  exportTransactionsCsv(limit = 200, customerId?: number, filters?: TransactionQueryFilters) {
    return requestText(`/inventory/transactions/export?${buildTransactionParams(limit, customerId, filters).toString()}`);
  },
  exportTransactionReport(params: {
    customer_id: number;
    report_type: "summary" | "detail";
    file_format: "xlsx" | "txt";
    transaction_type?: "receipt" | "return";
    date_from?: string;
    date_to?: string;
    fixture_code?: string;
    transaction_no?: string;
    identifier?: string;
  }) {
    const search = new URLSearchParams({
      customer_id: String(params.customer_id),
      report_type: params.report_type,
      file_format: params.file_format
    });
    setOptionalParam(search, "transaction_type", params.transaction_type);
    setOptionalParam(search, "date_from", params.date_from);
    setOptionalParam(search, "date_to", params.date_to);
    setOptionalParam(search, "fixture_code", params.fixture_code);
    setOptionalParam(search, "transaction_no", params.transaction_no);
    setOptionalParam(search, "identifier", params.identifier);
    return requestBlob(`/inventory/transactions/export-report?${search.toString()}`);
  },
  previewTransactionReportExport(params: {
    customer_id: number;
    report_type: "summary" | "detail";
    transaction_type?: "receipt" | "return";
    date_from?: string;
    date_to?: string;
    fixture_code?: string;
    transaction_no?: string;
    identifier?: string;
  }) {
    const search = new URLSearchParams({
      customer_id: String(params.customer_id),
      report_type: params.report_type
    });
    setOptionalParam(search, "transaction_type", params.transaction_type);
    setOptionalParam(search, "date_from", params.date_from);
    setOptionalParam(search, "date_to", params.date_to);
    setOptionalParam(search, "fixture_code", params.fixture_code);
    setOptionalParam(search, "transaction_no", params.transaction_no);
    setOptionalParam(search, "identifier", params.identifier);
    return request<{ report_type: "summary" | "detail"; column_count: number; raw_item_count: number; export_row_count: number }>(
      `/inventory/transactions/export-report/preview?${search.toString()}`
    );
  },
  downloadTransactionTemplateCsv() {
    return requestText("/inventory/transactions/template");
  },
  importTransactionsCsv(customerId: number, operatorName: string, content: string, filename?: string) {
    return request<{ imported_count: number }>(
      `/inventory/transactions/import?customer_id=${customerId}&operator_name=${encodeURIComponent(operatorName)}`,
      { method: "POST", body: JSON.stringify({ filename, content }) }
    );
  },
  createReceipt(payload: StockTransactionCreate) {
    return request<void>("/inventory/receipts", { method: "POST", body: JSON.stringify(payload) });
  },
  createReturn(payload: StockTransactionCreate) {
    return request<void>("/inventory/returns", { method: "POST", body: JSON.stringify(payload) });
  }
};
