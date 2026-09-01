// @vitest-environment jsdom

import { afterEach, describe, expect, it } from "vitest";

import {
  inventoryBatchShortcutFixtureCode,
  inventoryBatchShortcutMode,
  inventoryBatchShortcutRequestId,
  requestInventoryBatchOpen
} from "@/appState";

afterEach(() => {
  inventoryBatchShortcutFixtureCode.value = "";
  inventoryBatchShortcutMode.value = "receipt";
  inventoryBatchShortcutRequestId.value = 0;
});

describe("inventory batch shortcut", () => {
  it("carries the normalized fixture and requested receipt/return mode", () => {
    requestInventoryBatchOpen(" fx-001 ", "return");

    expect(inventoryBatchShortcutFixtureCode.value).toBe("FX-001");
    expect(inventoryBatchShortcutMode.value).toBe("return");
    expect(inventoryBatchShortcutRequestId.value).toBe(1);
  });
});
