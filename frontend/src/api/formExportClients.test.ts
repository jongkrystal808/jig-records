// @vitest-environment jsdom

import { afterEach, describe, expect, it, vi } from "vitest";

import { authApi } from "@/api/authClient";
import { masterApi } from "@/api/masterClient";
import { productionApi } from "@/api/productionClient";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Form filtered export clients", () => {
  it("uses one unpaged backend export request per domain", async () => {
    const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(
      new Response("header\n", { status: 200, headers: { "Content-Type": "text/csv" } })
    ));
    vi.stubGlobal("fetch", fetchMock);

    await masterApi.exportFormMasterCsv({
      entity: "fixture-images",
      customerId: 17,
      keyword: "FX",
      imageStatus: "missing-image"
    });
    await authApi.exportFormUsersCsv("operator", "active");
    await productionApi.exportFormProductionCsv({
      entity: "requirements",
      customerId: 17,
      modelId: 8,
      stationId: 9,
      keyword: "FIX"
    });

    const urls = fetchMock.mock.calls.map((call) => new URL(String(call[0]), "http://localhost"));
    expect(urls.map((url) => url.pathname)).toEqual([
      "/api/v2/master/form-export",
      "/api/v2/auth/users/form-export",
      "/api/v2/production/form-export"
    ]);
    expect(urls[0].searchParams.get("image_status")).toBe("missing-image");
    expect(urls[1].searchParams.get("status_filter")).toBe("active");
    expect(urls[2].searchParams.get("model_id")).toBe("8");
    expect(urls[2].searchParams.get("station_id")).toBe("9");
    for (const url of urls) {
      expect(url.searchParams.has("page")).toBe(false);
      expect(url.searchParams.has("page_size")).toBe(false);
    }
  });
});
