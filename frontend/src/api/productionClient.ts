import type {
  FixtureRequirement,
  FixtureRequirementCopyResult,
  FixtureRequirementListItem,
  ModelQuery,
  ModelStation,
  ModelStationListItem,
  PageResult,
  StationCapacity
} from "@/types";

import { request, requestBlob, requestText, setOptionalParam } from "@/api/core";

export type ProductionImportPreviewRow = {
  line: number;
  model_code: string;
  station_code: string;
  fixture_code: string | null;
  incoming_required_qty: number | null;
  existing_required_qty: number | null;
  status: "new" | "unchanged" | "conflict" | "error";
  message: string;
};

export type ProductionImportPreview = {
  rows: ProductionImportPreviewRow[];
  new_count: number;
  unchanged_count: number;
  conflict_count: number;
  error_count: number;
};

export type ProductionImportResult = {
  imported_count: number;
  created_count: number;
  updated_count: number;
  skipped_count: number;
};

export const productionApi = {
  listModelStations(customerId?: number) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<ModelStation[]>(`/production/model-stations${suffix}`);
  },
  listModelStationsPage(customerId: number, page = 1, pageSize = 50, modelId?: number | null, stationId?: number | null, keyword = "") {
    const params = new URLSearchParams({ customer_id: String(customerId), page: String(page), page_size: String(pageSize), keyword });
    setOptionalParam(params, "model_id", modelId ?? undefined);
    setOptionalParam(params, "station_id", stationId ?? undefined);
    return request<PageResult<ModelStationListItem>>(`/production/model-stations/page?${params.toString()}`);
  },
  exportFormProductionCsv(params: {
    entity: "requirements" | "mappings";
    customerId: number;
    modelId?: number | null;
    stationId?: number | null;
    keyword?: string;
  }) {
    const search = new URLSearchParams({
      entity: params.entity,
      customer_id: String(params.customerId)
    });
    setOptionalParam(search, "model_id", params.modelId);
    setOptionalParam(search, "station_id", params.stationId);
    setOptionalParam(search, "keyword", params.keyword);
    return requestBlob(`/production/form-export?${search.toString()}`);
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
  previewModelStationsCsv(customerId: number | undefined, content: string, filename?: string) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<ProductionImportPreview>(`/production/model-stations/import/preview${suffix}`, {
      method: "POST",
      body: JSON.stringify({ filename, content })
    });
  },
  importModelStationsCsv(customerId: number | undefined, content: string, filename?: string, overwriteExisting = true) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<ProductionImportResult>(`/production/model-stations/import${suffix}`, {
      method: "POST",
      body: JSON.stringify({ filename, content, overwrite_existing: overwriteExisting })
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
  previewFixtureRequirementsCsv(customerId: number | undefined, content: string, filename?: string) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<ProductionImportPreview>(`/production/fixture-requirements/import/preview${suffix}`, {
      method: "POST",
      body: JSON.stringify({ filename, content })
    });
  },
  importFixtureRequirementsCsv(customerId: number | undefined, content: string, filename?: string, overwriteExisting = true) {
    const params = new URLSearchParams();
    setOptionalParam(params, "customer_id", customerId);
    const suffix = params.size ? `?${params.toString()}` : "";
    return request<ProductionImportResult>(`/production/fixture-requirements/import${suffix}`, {
      method: "POST",
      body: JSON.stringify({ filename, content, overwrite_existing: overwriteExisting })
    });
  },
  createFixtureRequirement(payload: { customer_id: number; model_id: number; station_id: number; fixture_id: number; required_qty: number; designated_mode?: boolean; designated_identifiers?: string[] }) {
    return request<FixtureRequirement>("/production/fixture-requirements", { method: "POST", body: JSON.stringify(payload) });
  },
  copyFixtureRequirements(payload: {
    customer_id: number;
    source_model_id: number;
    source_station_id: number;
    target_model_id: number;
    target_station_id: number;
    overwrite_existing: boolean;
  }) {
    return request<FixtureRequirementCopyResult>("/production/fixture-requirements/copy", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  updateFixtureRequirement(
    requirementId: number,
    payload: { customer_id: number; model_id: number; station_id: number; fixture_id: number; required_qty: number; designated_mode?: boolean; designated_identifiers?: string[] }
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
  listFixtureRequirementsPage(customerId: number, page = 1, pageSize = 50, modelId?: number | null, stationId?: number | null, keyword = "") {
    const params = new URLSearchParams({ customer_id: String(customerId), page: String(page), page_size: String(pageSize), keyword });
    setOptionalParam(params, "model_id", modelId ?? undefined);
    setOptionalParam(params, "station_id", stationId ?? undefined);
    return request<PageResult<FixtureRequirementListItem>>(`/production/fixture-requirements/page?${params.toString()}`);
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
