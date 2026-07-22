import type { AppUser, Customer, Fixture, FixtureQualityReport, MachineModel, Station } from "@/types";

import { request, requestText, setOptionalParam } from "@/api/core";

export const masterApi = {
  listCustomers() {
    return request<Customer[]>("/master/customers");
  },
  listCustomerUsers(customerId: number) {
    return request<AppUser[]>(`/master/customers/${customerId}/users`);
  },
  createCustomer(payload: { code: string; name: string; assigned_user_ids?: number[] }) {
    return request<Customer>("/master/customers", { method: "POST", body: JSON.stringify(payload) });
  },
  updateCustomer(customerId: number, payload: { code: string; name: string; assigned_user_ids?: number[] }) {
    return request<Customer>(`/master/customers/${customerId}`, { method: "PUT", body: JSON.stringify(payload) });
  },
  listFixtures(customerId?: number) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<Fixture[]>(`/master/fixtures${suffix}`);
  },
  getFixtureQualityReport(customerId: number) {
    return request<FixtureQualityReport>(`/master/fixtures/quality?customer_id=${customerId}`);
  },
  exportFixturesCsv(customerId: number) {
    return requestText(`/master/fixtures/export?customer_id=${customerId}`);
  },
  downloadFixtureTemplateCsv() {
    return requestText("/master/fixtures/template");
  },
  importFixturesCsv(customerId: number, content: string, filename?: string) {
    return request<{ imported_count: number }>(`/master/fixtures/import?customer_id=${customerId}`, {
      method: "POST",
      body: JSON.stringify({ filename, content })
    });
  },
  createFixture(payload: {
    customer_id: number;
    responsible_user_id?: number | null;
    code: string;
    name: string;
    line_storage_location?: string | null;
    department_storage_location?: string | null;
    min_stock_qty?: number | null;
    description?: string;
  }) {
    return request<Fixture>("/master/fixtures", { method: "POST", body: JSON.stringify(payload) });
  },
  updateFixture(
    fixtureId: number,
    payload: {
      customer_id: number;
      responsible_user_id?: number | null;
      code: string;
      name: string;
      line_storage_location?: string | null;
      department_storage_location?: string | null;
      min_stock_qty?: number | null;
      description?: string;
      is_active: boolean;
    }
  ) {
    return request<Fixture>(`/master/fixtures/${fixtureId}`, { method: "PUT", body: JSON.stringify(payload) });
  },
  deleteFixture(fixtureId: number, customerId: number, deleteTransactions: boolean) {
    const params = new URLSearchParams({
      customer_id: String(customerId),
      delete_transactions: String(deleteTransactions)
    });
    return request<{
      fixture_id: number;
      fixture_code: string;
      transaction_records_deleted: boolean;
      transaction_item_count: number;
      affected_transaction_count: number;
      deleted_transaction_count: number;
      deleted_requirement_count: number;
    }>(`/master/fixtures/${fixtureId}?${params.toString()}`, {
      method: "DELETE"
    });
  },
  listModels(customerId?: number) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<MachineModel[]>(`/master/models${suffix}`);
  },
  exportModelsCsv(customerId?: number) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return requestText(`/master/models/export${suffix}`);
  },
  downloadModelTemplateCsv() {
    return requestText("/master/models/template");
  },
  importModelsCsv(customerId: number | undefined, content: string, filename?: string) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<{ imported_count: number }>(`/master/models/import${suffix}`, {
      method: "POST",
      body: JSON.stringify({ filename, content })
    });
  },
  createModel(payload: { customer_id: number; code: string; name: string }) {
    return request<MachineModel>("/master/models", { method: "POST", body: JSON.stringify(payload) });
  },
  updateModel(modelId: number, payload: { customer_id: number; code: string; name: string; is_active: boolean }) {
    return request<MachineModel>(`/master/models/${modelId}`, { method: "PUT", body: JSON.stringify(payload) });
  },
  listStations(customerId?: number) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<Station[]>(`/master/stations${suffix}`);
  },
  exportStationsCsv(customerId?: number) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return requestText(`/master/stations/export${suffix}`);
  },
  downloadStationTemplateCsv() {
    return requestText("/master/stations/template");
  },
  importStationsCsv(customerId: number | undefined, content: string, filename?: string) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<{ imported_count: number }>(`/master/stations/import${suffix}`, {
      method: "POST",
      body: JSON.stringify({ filename, content })
    });
  },
  createStation(payload: { customer_id: number; code: string; name: string }) {
    return request<Station>("/master/stations", { method: "POST", body: JSON.stringify(payload) });
  },
  updateStation(stationId: number, payload: { customer_id: number; code: string; name: string; is_active: boolean }) {
    return request<Station>(`/master/stations/${stationId}`, { method: "PUT", body: JSON.stringify(payload) });
  }
};
