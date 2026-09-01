import type { SearchFixtureContext, SearchModelContext, SearchResultPage } from "@/types";

import { request } from "@/api/core";

export const searchApi = {
  getFixtureOverview(customerId: number, page = 1, pageSize = 20) {
    const search = new URLSearchParams({
      customer_id: String(customerId),
      page: String(page),
      page_size: String(pageSize)
    });
    return request<SearchResultPage>(`/search/fixtures/overview?${search.toString()}`);
  },
  globalSearch(params: {
    q: string;
    customerId?: number;
    entityType?: "fixture" | "model" | "station";
    fixtureSearchMode?: "fixture" | "identifier";
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
    if (params.entityType === "fixture" && params.fixtureSearchMode) {
      search.set("fixture_search_mode", params.fixtureSearchMode);
    }
    return request<SearchResultPage>(`/search/global?${search.toString()}`);
  },
  getFixtureSearchContext(fixtureId: number, customerId: number, recentTransactionLimit = 8, identifier?: string) {
    const search = new URLSearchParams({
      customer_id: String(customerId),
      recent_transaction_limit: String(recentTransactionLimit)
    });
    if (identifier) {
      search.set("identifier", identifier);
    }
    return request<SearchFixtureContext>(`/search/fixtures/${fixtureId}/context?${search.toString()}`);
  },
  getModelSearchContext(modelId: number, customerId: number) {
    const search = new URLSearchParams({
      customer_id: String(customerId)
    });
    return request<SearchModelContext>(`/search/models/${modelId}/context?${search.toString()}`);
  }
};
