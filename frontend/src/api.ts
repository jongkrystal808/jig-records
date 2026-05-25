import type { FixtureImage, MaterialTransaction, SearchResult, StockSummary } from "@/types";

const API_ROOT = "/api/v2";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_ROOT}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    ...init
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

export const api = {
  listStock: () => request<StockSummary[]>("/inventory/stock"),
  listTransactions: (limit = 20) => request<MaterialTransaction[]>(`/inventory/transactions?limit=${limit}`),
  globalSearch: (q: string) => request<SearchResult[]>(`/search/global?q=${encodeURIComponent(q)}`),
  listFixtureImages: (fixtureId?: number) =>
    request<FixtureImage[]>(fixtureId ? `/warehouse/fixture-images?fixture_id=${fixtureId}` : "/warehouse/fixture-images")
};
