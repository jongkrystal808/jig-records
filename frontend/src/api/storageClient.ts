import type {
  FixturePlacementDetail,
  FixturePlacementInput,
  StorageContainer,
  StorageOverview
} from "@/types";

import { request } from "@/api/core";


export const storageApi = {
  getOverview(customerId: number, keyword = "") {
    const params = new URLSearchParams({ customer_id: String(customerId), keyword });
    return request<StorageOverview>(`/storage/overview?${params.toString()}`);
  },
  createContainer(payload: { customer_id: number; name: string; description?: string | null }) {
    return request<StorageContainer>("/storage/containers", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  updateContainer(containerId: number, customerId: number, payload: { name: string; description?: string | null }) {
    return request<StorageContainer>(`/storage/containers/${containerId}?customer_id=${customerId}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  },
  deleteContainer(containerId: number, customerId: number) {
    return request<void>(`/storage/containers/${containerId}?customer_id=${customerId}`, { method: "DELETE" });
  },
  registerCodes(customerId: number, locationText: string) {
    return request<StorageOverview>("/storage/codes/register", {
      method: "POST",
      body: JSON.stringify({ customer_id: customerId, location_text: locationText })
    });
  },
  organizeCodes(customerId: number, storageCodeIds: number[], containerId: number | null) {
    return request<StorageOverview>("/storage/codes/organize", {
      method: "PUT",
      body: JSON.stringify({
        customer_id: customerId,
        storage_code_ids: storageCodeIds,
        container_id: containerId
      })
    });
  },
  getFixturePlacements(fixtureId: number) {
    return request<FixturePlacementDetail>(`/storage/fixtures/${fixtureId}/placements`);
  },
  syncFixturePlacements(fixtureId: number) {
    return request<FixturePlacementDetail>(`/storage/fixtures/${fixtureId}/sync`, { method: "POST" });
  },
  replaceFixturePlacements(fixtureId: number, placements: FixturePlacementInput[]) {
    return request<FixturePlacementDetail>(`/storage/fixtures/${fixtureId}/placements`, {
      method: "PUT",
      body: JSON.stringify({ placements })
    });
  }
};
