import type {
  FixtureRequirement,
  FixtureRequirementListItem,
  ModelQuery,
  ModelStation,
  StationCapacity
} from "@/types";

import { request, requestText, setOptionalParam } from "@/api/core";

export const productionApi = {
  listModelStations(customerId?: number) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<ModelStation[]>(`/production/model-stations${suffix}`);
  },
  exportModelStationsCsv(customerId?: number) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return requestText(`/production/model-stations/export${suffix}`);
  },
  downloadModelStationTemplateCsv() {
    return requestText("/production/model-stations/template");
  },
  importModelStationsCsv(customerId: number | undefined, content: string, filename?: string) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<{ imported_count: number }>(`/production/model-stations/import${suffix}`, {
      method: "POST",
      body: JSON.stringify({ filename, content })
    });
  },
  createModelStation(payload: { customer_id: number; model_id: number; station_id: number }) {
    return request<ModelStation>("/production/model-stations", { method: "POST", body: JSON.stringify(payload) });
  },
  updateModelStation(rowId: number, payload: { customer_id: number; model_id: number; station_id: number }) {
    return request<ModelStation>(`/production/model-stations/${rowId}`, { method: "PUT", body: JSON.stringify(payload) });
  },
  deleteModelStation(rowId: number, customerId?: number) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<void>(`/production/model-stations/${rowId}${suffix}`, { method: "DELETE" });
  },
  exportFixtureRequirementsCsv(customerId?: number) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return requestText(`/production/fixture-requirements/export${suffix}`);
  },
  downloadFixtureRequirementTemplateCsv() {
    return requestText("/production/fixture-requirements/template");
  },
  importFixtureRequirementsCsv(customerId: number | undefined, content: string, filename?: string) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<{ imported_count: number }>(`/production/fixture-requirements/import${suffix}`, {
      method: "POST",
      body: JSON.stringify({ filename, content })
    });
  },
  createFixtureRequirement(payload: { customer_id: number; model_id: number; station_id: number; fixture_id: number; required_qty: number }) {
    return request<FixtureRequirement>("/production/fixture-requirements", { method: "POST", body: JSON.stringify(payload) });
  },
  updateFixtureRequirement(
    requirementId: number,
    payload: { customer_id: number; model_id: number; station_id: number; fixture_id: number; required_qty: number }
  ) {
    return request<FixtureRequirement>(`/production/fixture-requirements/${requirementId}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  },
  listFixtureRequirements(customerId?: number) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<FixtureRequirementListItem[]>(`/production/fixture-requirements${suffix}`);
  },
  deleteFixtureRequirement(requirementId: number, customerId?: number) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<void>(`/production/fixture-requirements/${requirementId}${suffix}`, { method: "DELETE" });
  },
  getStationCapacity(stationId: number, modelId: number, customerId?: number) {
    const params = new URLSearchParams({ model_id: String(modelId) });
    setOptionalParam(params, "customer_id", customerId);
    return request<StationCapacity>(`/production/capacity/stations/${stationId}?${params.toString()}`);
  },
  getModelQuery(modelId: number, stationId?: number, customerId?: number) {
    const params = new URLSearchParams();
    setOptionalParam(params, "station_id", stationId);
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<ModelQuery>(`/production/models/${modelId}/query${suffix}`);
  }
};
