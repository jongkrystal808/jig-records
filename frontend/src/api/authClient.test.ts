// @vitest-environment jsdom

import { afterEach, describe, expect, it, vi } from "vitest";

import { authApi } from "./authClient";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("model shortcut preferences", () => {
  it("loads, records, and pins through the signed-in preference API", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockImplementation(async () => new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }));

    await authApi.listModelShortcutPreferences(3);
    await authApi.recordModelShortcutQuery(3, 21);
    await authApi.setModelShortcutPin(3, 21, true);

    const urls = fetchMock.mock.calls.map((call) => new URL(call[0] as string, "http://localhost"));
    expect(urls[0]!.pathname).toBe("/api/v2/auth/preferences/model-shortcuts");
    expect(urls[0]!.searchParams.get("customer_id")).toBe("3");
    expect(urls[1]!.pathname).toBe("/api/v2/auth/preferences/model-shortcuts/21/query");
    expect(fetchMock.mock.calls[1]![1]?.method).toBe("POST");
    expect(urls[2]!.pathname).toBe("/api/v2/auth/preferences/model-shortcuts/21/pin");
    expect(fetchMock.mock.calls[2]![1]?.method).toBe("PUT");
    expect(fetchMock.mock.calls[2]![1]?.body).toBe(JSON.stringify({ pinned: true }));
  });
});
