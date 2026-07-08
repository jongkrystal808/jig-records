import type { SearchResult } from "@/types";

import { request } from "@/api/core";

export const searchApi = {
  globalSearch(q: string, customerId?: number) {
    return request<SearchResult[]>(`/search/global?q=${encodeURIComponent(q)}${customerId ? `&customer_id=${customerId}` : ""}`);
  }
};
