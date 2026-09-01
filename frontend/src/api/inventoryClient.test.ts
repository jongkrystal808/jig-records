// @vitest-environment jsdom

import { afterEach, describe, expect, it, vi } from "vitest";

import { inventoryApi } from "@/api/inventoryClient";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("transaction CSV export", () => {
  it("requests the complete filtered result without a client-side limit", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response("transaction_type,transaction_no\n", {
        status: 200,
        headers: { "Content-Type": "text/csv; charset=utf-8" }
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    await inventoryApi.exportTransactionsCsv(17, {
      transaction_type: "receipt",
      fixture_code: "FIX-001"
    });

    const requestedUrl = new URL(String(fetchMock.mock.calls[0][0]), "http://localhost");
    expect(requestedUrl.pathname).toBe("/api/v2/inventory/transactions/export");
    expect(requestedUrl.searchParams.get("customer_id")).toBe("17");
    expect(requestedUrl.searchParams.get("transaction_type")).toBe("receipt");
    expect(requestedUrl.searchParams.get("fixture_code")).toBe("FIX-001");
    expect(requestedUrl.searchParams.has("limit")).toBe(false);
  });
});

describe("workbench transaction pagination", () => {
  it("requests an item-level backend page of fifty rows", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(JSON.stringify({
      items: [],
      page: 2,
      page_size: 50,
      total: 380
    }), { status: 200, headers: { "Content-Type": "application/json" } }));

    await inventoryApi.listTransactionOverviewPage(2, 50, 7);

    const requestedUrl = new URL(vi.mocked(fetch).mock.calls[0]![0] as string, "http://localhost");
    expect(requestedUrl.pathname).toBe("/api/v2/inventory/transactions/overview");
    expect(requestedUrl.searchParams.get("page")).toBe("2");
    expect(requestedUrl.searchParams.get("page_size")).toBe("50");
    expect(requestedUrl.searchParams.get("customer_id")).toBe("7");
  });
});
