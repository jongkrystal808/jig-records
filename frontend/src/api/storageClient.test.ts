// @vitest-environment jsdom

import { afterEach, describe, expect, it, vi } from "vitest";

import { storageApi } from "@/api/storageClient";


afterEach(() => {
  vi.unstubAllGlobals();
});

describe("storage client", () => {
  it("registers comma-separated location text in the selected customer scope", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ customer_id: 7, containers: [], codes: [], ungrouped_code_count: 0, pending_quantity_count: 0 }), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    await storageApi.registerCodes(7, "AXG001, MOXA001");

    const [url, init] = fetchMock.mock.calls[0];
    expect(new URL(String(url), "http://localhost").pathname).toBe("/api/v2/storage/codes/register");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ customer_id: 7, location_text: "AXG001, MOXA001" });
  });

  it("sends complete model and station context for a station placement", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({
        fixture_id: 91,
        fixture_code: "L-00091",
        fixture_name: "Fixture",
        customer_id: 7,
        stock_qty: 3,
        allocated_qty: 3,
        unallocated_qty: 0,
        has_pending_quantities: false,
        placements: [],
        station_options: []
      }), { status: 200, headers: { "Content-Type": "application/json" } })
    );
    vi.stubGlobal("fetch", fetchMock);

    await storageApi.replaceFixturePlacements(91, [{
      target_type: "model_station",
      model_id: 12,
      station_id: 22,
      quantity: 3
    }]);

    const [, init] = fetchMock.mock.calls[0];
    expect(JSON.parse(init.body).placements[0]).toEqual({
      target_type: "model_station",
      model_id: 12,
      station_id: 22,
      quantity: 3
    });
  });
});
