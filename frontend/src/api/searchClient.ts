import type { SearchFixtureContext, SearchModelContext, SearchResultPage } from "@/types";

import { request } from "@/api/core";

export const searchApi = {
  globalSearch(params: {
    q: string;
    customerId?: number;
    entityType?: "fixture" | "model" | "station";
    page?: number;
    pageSize?: number;
  }) {
    const search = new URLSearchParams({
      q: params.q,
      page: String(params.page ?? 1),
      page_size: String(params.pageSize ?? 12)
    });
    if (params.customerId) {
      search.set("customer_id", String(params.customerId));
    }
    if (params.entityType) {
      search.set("entity_type", params.entityType);
    }
    return request<SearchResultPage>(`/search/global?${search.toString()}`);
  },
  getFixtureSearchContext(fixtureId: number, customerId: number, recentTransactionLimit = 8) {
    const search = new URLSearchParams({
      customer_id: String(customerId),
      recent_transaction_limit: String(recentTransactionLimit)
    });
    return request<SearchFixtureContext>(`/search/fixtures/${fixtureId}/context?${search.toString()}`);
  },
  getModelSearchContext(modelId: number, customerId: number) {
    const search = new URLSearchParams({
      customer_id: String(customerId)
    });
    return request<SearchModelContext>(`/search/models/${modelId}/context?${search.toString()}`);
  }
};
