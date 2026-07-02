import type {
  AppUser,
  AuthSession,
  AuditLogEntry,
  Customer,
  Fixture,
  FixtureRequirement,
  FixtureRequirementListItem,
  MachineModel,
  MaterialTransaction,
  ModelQuery,
  ModelStation,
  SearchResult,
  Station,
  StationCapacity,
  IdentifierStockSummary,
  StockSummary,
  StockTransactionCreate,
  TransactionQueryFilters,
} from "@/types";
import { authSession } from "@/appState";
import { extractErrorMessage } from "@/utils/apiError";

const API_ROOT = "/api/v2";

export function fixtureImageUrlByCode(fixtureCode: string): string {
  return `${API_ROOT}/master/fixtures/${encodeURIComponent(fixtureCode)}/image`;
}

export async function fetchFixtureImageObjectUrl(fixtureCode: string): Promise<string> {
  const headers = buildHeaders(undefined, true);
  const response = await fetch(fixtureImageUrlByCode(fixtureCode), {
    headers
  });
  if (!response.ok) {
    throw new Error(extractErrorMessage(await response.text(), `Request failed: ${response.status}`));
  }
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

function buildHeaders(init?: RequestInit, withAuth = true): Headers {
  const headers = new Headers(init?.headers ?? {});
  if (!(init?.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  headers.set("Accept", "application/json, text/plain;q=0.9, */*;q=0.8");
  if (withAuth && authSession.value?.token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${authSession.value.token}`);
  }
  return headers;
}

async function request<T>(path: string, init?: RequestInit, withAuth = true): Promise<T> {
  const headers = buildHeaders(init, withAuth);
  const response = await fetch(`${API_ROOT}${path}`, {
    headers,
    ...init
  });

  const body = await response.text();

  if (!response.ok) {
    throw new Error(extractErrorMessage(body, `Request failed: ${response.status}`));
  }

  if (response.status === 204 || !body) {
    return undefined as T;
  }

  return JSON.parse(body) as T;
}

async function requestText(path: string, init?: RequestInit, withAuth = true): Promise<string> {
  const headers = buildHeaders(init, withAuth);
  const response = await fetch(`${API_ROOT}${path}`, {
    headers,
    ...init
  });
  const body = await response.text();
  if (!response.ok) {
    throw new Error(extractErrorMessage(body, `Request failed: ${response.status}`));
  }
  return body;
}

async function requestBlob(path: string, init?: RequestInit, withAuth = true): Promise<{ blob: Blob; filename: string | null }> {
  const headers = buildHeaders(init, withAuth);
  const response = await fetch(`${API_ROOT}${path}`, {
    headers,
    ...init
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(extractErrorMessage(body, `Request failed: ${response.status}`));
  }
  const contentDisposition = response.headers.get("Content-Disposition");
  const filenameMatch = contentDisposition?.match(/filename="?([^"]+)"?/i);
  return {
    blob: await response.blob(),
    filename: filenameMatch?.[1] ?? null
  };
}

export const api = {
  listCustomers: () => request<Customer[]>("/master/customers"),
  listAuditLogs: (customerId?: number, limit = 3) =>
    request<AuditLogEntry[]>(
      customerId ? `/audit/logs?customer_id=${customerId}&limit=${limit}` : `/audit/logs?limit=${limit}`
    ),
  login: (payload: { username: string; password: string }) =>
    request<AuthSession>("/auth/login", { method: "POST", body: JSON.stringify(payload) }, false),
  guestEntry: () => request<AuthSession>("/auth/guest", { method: "POST" }, false),
  listUsers: () => request<AppUser[]>("/auth/users"),
  listCustomerUsers: (customerId: number) => request<AppUser[]>(`/master/customers/${customerId}/users`),
  createUser: (payload: { username: string; email?: string | null; password: string; display_name: string; role: string; is_active: boolean; allowed_customer_ids: number[] }) =>
    request<AppUser>("/auth/users", { method: "POST", body: JSON.stringify(payload) }),
  updateUser: (userId: number, payload: { email?: string | null; display_name: string; role: string; is_active: boolean; allowed_customer_ids: number[] }) =>
    request<AppUser>(`/auth/users/${userId}`, { method: "PUT", body: JSON.stringify(payload) }),
  resetUserPassword: (userId: number, password: string) =>
    request<void>(`/auth/users/${userId}/reset-password`, { method: "POST", body: JSON.stringify({ password }) }),
  createCustomer: (payload: { code: string; name: string; assigned_user_ids?: number[] }) =>
    request<Customer>("/master/customers", { method: "POST", body: JSON.stringify(payload) }),
  updateCustomer: (customerId: number, payload: { code: string; name: string; assigned_user_ids?: number[] }) =>
    request<Customer>(`/master/customers/${customerId}`, { method: "PUT", body: JSON.stringify(payload) }),
  listFixtures: (customerId?: number) =>
    request<Fixture[]>(customerId ? `/master/fixtures?customer_id=${customerId}` : "/master/fixtures"),
  exportFixturesCsv: (customerId: number) => requestText(`/master/fixtures/export?customer_id=${customerId}`),
  downloadFixtureTemplateCsv: () => requestText("/master/fixtures/template"),
  importFixturesCsv: (customerId: number, content: string, filename?: string) =>
    request<{ imported_count: number }>(`/master/fixtures/import?customer_id=${customerId}`, {
      method: "POST",
      body: JSON.stringify({ filename, content })
    }),
  createFixture: (payload: {
    customer_id: number;
    responsible_user_id?: number | null;
    code: string;
    name: string;
    line_storage_location?: string | null;
    department_storage_location?: string | null;
    storage_location?: string | null;
    min_stock_qty?: number | null;
    description?: string;
  }) =>
    request<Fixture>("/master/fixtures", { method: "POST", body: JSON.stringify(payload) }),
  updateFixture: (fixtureId: number, payload: {
    customer_id: number;
    responsible_user_id?: number | null;
    code: string;
    name: string;
    line_storage_location?: string | null;
    department_storage_location?: string | null;
    storage_location?: string | null;
    min_stock_qty?: number | null;
    description?: string;
    is_active: boolean;
  }) =>
    request<Fixture>(`/master/fixtures/${fixtureId}`, { method: "PUT", body: JSON.stringify(payload) }),
  listModels: (customerId?: number) =>
    request<MachineModel[]>(customerId ? `/master/models?customer_id=${customerId}` : "/master/models"),
  exportModelsCsv: (customerId?: number) =>
    requestText(customerId ? `/master/models/export?customer_id=${customerId}` : "/master/models/export"),
  downloadModelTemplateCsv: () => requestText("/master/models/template"),
  importModelsCsv: (customerId: number | undefined, content: string, filename?: string) =>
    request<{ imported_count: number }>(
      customerId ? `/master/models/import?customer_id=${customerId}` : "/master/models/import",
      {
      method: "POST",
      body: JSON.stringify({ filename, content })
      }
    ),
  createModel: (payload: { customer_id: number; code: string; name: string }) =>
    request<MachineModel>("/master/models", { method: "POST", body: JSON.stringify(payload) }),
  updateModel: (modelId: number, payload: { customer_id: number; code: string; name: string; is_active: boolean }) =>
    request<MachineModel>(`/master/models/${modelId}`, { method: "PUT", body: JSON.stringify(payload) }),
  listStations: (customerId?: number) =>
    request<Station[]>(customerId ? `/master/stations?customer_id=${customerId}` : "/master/stations"),
  exportStationsCsv: (customerId?: number) =>
    requestText(customerId ? `/master/stations/export?customer_id=${customerId}` : "/master/stations/export"),
  downloadStationTemplateCsv: () => requestText("/master/stations/template"),
  importStationsCsv: (customerId: number | undefined, content: string, filename?: string) =>
    request<{ imported_count: number }>(
      customerId ? `/master/stations/import?customer_id=${customerId}` : "/master/stations/import",
      {
      method: "POST",
      body: JSON.stringify({ filename, content })
      }
    ),
  createStation: (payload: { customer_id: number; code: string; name: string }) =>
    request<Station>("/master/stations", { method: "POST", body: JSON.stringify(payload) }),
  updateStation: (stationId: number, payload: { customer_id: number; code: string; name: string; is_active: boolean }) =>
    request<Station>(`/master/stations/${stationId}`, { method: "PUT", body: JSON.stringify(payload) }),
  listStock: (customerId?: number) => request<StockSummary[]>(customerId ? `/inventory/stock?customer_id=${customerId}` : "/inventory/stock"),
  listAlerts: (customerId?: number) =>
    request<Array<{ fixture_id: number; fixture_code: string; fixture_name: string; stock_qty: number; min_stock_qty: number; stock_status: "low_stock" | "out_of_stock" }>>(
      customerId ? `/inventory/alerts?customer_id=${customerId}` : "/inventory/alerts"
    ),
  listIdentifierStockSummary: (customerId?: number) =>
    request<IdentifierStockSummary[]>(
      customerId ? `/inventory/identifier-stock-summary?customer_id=${customerId}` : "/inventory/identifier-stock-summary"
    ),
  listTransactions: (limit = 20, customerId?: number, filters?: TransactionQueryFilters) => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (customerId) params.set("customer_id", String(customerId));
    if (filters?.transaction_type) params.set("transaction_type", filters.transaction_type);
    if (filters?.date_from) params.set("date_from", filters.date_from);
    if (filters?.date_to) params.set("date_to", filters.date_to);
    if (filters?.fixture_code) params.set("fixture_code", filters.fixture_code);
    if (filters?.transaction_no) params.set("transaction_no", filters.transaction_no);
    if (filters?.identifier) params.set("identifier", filters.identifier);
    if (filters?.created_by) params.set("created_by", filters.created_by);
    return request<MaterialTransaction[]>(`/inventory/transactions?${params.toString()}`);
  },
  exportTransactionsCsv: (limit = 200, customerId?: number, filters?: TransactionQueryFilters) => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (customerId) params.set("customer_id", String(customerId));
    if (filters?.transaction_type) params.set("transaction_type", filters.transaction_type);
    if (filters?.date_from) params.set("date_from", filters.date_from);
    if (filters?.date_to) params.set("date_to", filters.date_to);
    if (filters?.fixture_code) params.set("fixture_code", filters.fixture_code);
    if (filters?.transaction_no) params.set("transaction_no", filters.transaction_no);
    if (filters?.identifier) params.set("identifier", filters.identifier);
    if (filters?.created_by) params.set("created_by", filters.created_by);
    return requestText(`/inventory/transactions/export?${params.toString()}`);
  },
  exportTransactionReport: (params: {
    customer_id: number;
    report_type: "summary" | "detail";
    file_format: "xlsx" | "txt";
    transaction_type?: "receipt" | "return";
    date_from?: string;
    date_to?: string;
    fixture_code?: string;
    transaction_no?: string;
    identifier?: string;
  }) => {
    const search = new URLSearchParams({
      customer_id: String(params.customer_id),
      report_type: params.report_type,
      file_format: params.file_format
    });
    if (params.transaction_type) search.set("transaction_type", params.transaction_type);
    if (params.date_from) search.set("date_from", params.date_from);
    if (params.date_to) search.set("date_to", params.date_to);
    if (params.fixture_code) search.set("fixture_code", params.fixture_code);
    if (params.transaction_no) search.set("transaction_no", params.transaction_no);
    if (params.identifier) search.set("identifier", params.identifier);
    return requestBlob(`/inventory/transactions/export-report?${search.toString()}`);
  },
  previewTransactionReportExport: (params: {
    customer_id: number;
    report_type: "summary" | "detail";
    transaction_type?: "receipt" | "return";
    date_from?: string;
    date_to?: string;
    fixture_code?: string;
    transaction_no?: string;
    identifier?: string;
  }) => {
    const search = new URLSearchParams({
      customer_id: String(params.customer_id),
      report_type: params.report_type
    });
    if (params.transaction_type) search.set("transaction_type", params.transaction_type);
    if (params.date_from) search.set("date_from", params.date_from);
    if (params.date_to) search.set("date_to", params.date_to);
    if (params.fixture_code) search.set("fixture_code", params.fixture_code);
    if (params.transaction_no) search.set("transaction_no", params.transaction_no);
    if (params.identifier) search.set("identifier", params.identifier);
    return request<{ report_type: "summary" | "detail"; column_count: number; raw_item_count: number; export_row_count: number }>(
      `/inventory/transactions/export-report/preview?${search.toString()}`
    );
  },
  downloadTransactionTemplateCsv: () => requestText("/inventory/transactions/template"),
  importTransactionsCsv: (customerId: number, operatorName: string, content: string, filename?: string) =>
    request<{ imported_count: number }>(
      `/inventory/transactions/import?customer_id=${customerId}&operator_name=${encodeURIComponent(operatorName)}`,
      { method: "POST", body: JSON.stringify({ filename, content }) }
    ),
  createReceipt: (payload: StockTransactionCreate) =>
    request<void>("/inventory/receipts", { method: "POST", body: JSON.stringify(payload) }),
  createReturn: (payload: StockTransactionCreate) =>
    request<void>("/inventory/returns", { method: "POST", body: JSON.stringify(payload) }),
  globalSearch: (q: string, customerId?: number) =>
    request<SearchResult[]>(`/search/global?q=${encodeURIComponent(q)}${customerId ? `&customer_id=${customerId}` : ""}`),
  listModelStations: (customerId?: number) =>
    request<ModelStation[]>(customerId ? `/production/model-stations?customer_id=${customerId}` : "/production/model-stations"),
  exportModelStationsCsv: (customerId?: number) =>
    requestText(customerId ? `/production/model-stations/export?customer_id=${customerId}` : "/production/model-stations/export"),
  downloadModelStationTemplateCsv: () => requestText("/production/model-stations/template"),
  importModelStationsCsv: (customerId: number | undefined, content: string, filename?: string) =>
    request<{ imported_count: number }>(
      customerId ? `/production/model-stations/import?customer_id=${customerId}` : "/production/model-stations/import",
      {
      method: "POST",
      body: JSON.stringify({ filename, content })
      }
    ),
  createModelStation: (payload: { customer_id: number; model_id: number; station_id: number }) =>
    request<ModelStation>("/production/model-stations", { method: "POST", body: JSON.stringify(payload) }),
  updateModelStation: (rowId: number, payload: { customer_id: number; model_id: number; station_id: number }) =>
    request<ModelStation>(`/production/model-stations/${rowId}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteModelStation: (rowId: number, customerId?: number) =>
    request<void>(customerId ? `/production/model-stations/${rowId}?customer_id=${customerId}` : `/production/model-stations/${rowId}`, {
      method: "DELETE"
    }),
  exportFixtureRequirementsCsv: (customerId?: number) =>
    requestText(customerId ? `/production/fixture-requirements/export?customer_id=${customerId}` : "/production/fixture-requirements/export"),
  downloadFixtureRequirementTemplateCsv: () => requestText("/production/fixture-requirements/template"),
  importFixtureRequirementsCsv: (customerId: number | undefined, content: string, filename?: string) =>
    request<{ imported_count: number }>(
      customerId ? `/production/fixture-requirements/import?customer_id=${customerId}` : "/production/fixture-requirements/import",
      {
      method: "POST",
      body: JSON.stringify({ filename, content })
      }
  ),
  createFixtureRequirement: (payload: { customer_id: number; model_id: number; station_id: number; fixture_id: number; required_qty: number }) =>
    request<FixtureRequirement>("/production/fixture-requirements", { method: "POST", body: JSON.stringify(payload) }),
  updateFixtureRequirement: (
    requirementId: number,
    payload: { customer_id: number; model_id: number; station_id: number; fixture_id: number; required_qty: number }
  ) => request<FixtureRequirement>(`/production/fixture-requirements/${requirementId}`, { method: "PUT", body: JSON.stringify(payload) }),
  listFixtureRequirements: (customerId?: number) =>
    request<FixtureRequirementListItem[]>(customerId ? `/production/fixture-requirements?customer_id=${customerId}` : "/production/fixture-requirements"),
  deleteFixtureRequirement: (requirementId: number, customerId?: number) =>
    request<void>(
      customerId
        ? `/production/fixture-requirements/${requirementId}?customer_id=${customerId}`
        : `/production/fixture-requirements/${requirementId}`,
      { method: "DELETE" }
    ),
  getStationCapacity: (stationId: number, modelId: number, customerId?: number) =>
    request<StationCapacity>(
      customerId
        ? `/production/capacity/stations/${stationId}?model_id=${modelId}&customer_id=${customerId}`
        : `/production/capacity/stations/${stationId}?model_id=${modelId}`
    ),
  getModelQuery: (modelId: number, stationId?: number, customerId?: number) => {
    const params = new URLSearchParams();
    if (stationId) params.set("station_id", String(stationId));
    if (customerId) params.set("customer_id", String(customerId));
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<ModelQuery>(`/production/models/${modelId}/query${suffix}`);
  },
};
