// @vitest-environment jsdom

import { beforeEach, describe, expect, it, vi } from "vitest";

import { requestConfirmation } from "@/confirmState";
import {
  allowNextRouteNavigation,
  clearUnsavedChangesGuards,
  confirmUnsavedChanges,
  consumeRouteNavigationBypass,
  handleUnsavedChangesBeforeUnload,
  setUnsavedChangesGuard,
  unsavedChangesMessages
} from "@/unsavedChangesGuard";

vi.mock("@/confirmState", () => ({ requestConfirmation: vi.fn() }));

beforeEach(() => {
  clearUnsavedChangesGuards();
  vi.clearAllMocks();
});

describe("unsaved changes guard", () => {
  it("shares one deduplicated registry across navigation contexts", async () => {
    vi.mocked(requestConfirmation).mockResolvedValue(false);
    setUnsavedChangesGuard("master", true, "表格內有草稿");
    setUnsavedChangesGuard("production", true, "表格內有草稿");

    expect(unsavedChangesMessages()).toEqual(["表格內有草稿"]);
    await expect(confirmUnsavedChanges("logout")).resolves.toBe(false);
    expect(requestConfirmation).toHaveBeenCalledWith(
      expect.stringContaining("登出後"),
      expect.objectContaining({ title: "登出並捨棄草稿？" })
    );
  });

  it("blocks browser unload while any registered draft exists", () => {
    setUnsavedChangesGuard("master", true, "表格內有草稿");
    const event = new Event("beforeunload", { cancelable: true }) as BeforeUnloadEvent;

    handleUnsavedChangesBeforeUnload(event);

    expect(event.defaultPrevented).toBe(true);
  });

  it("consumes an explicitly allowed route navigation only once", () => {
    allowNextRouteNavigation();
    expect(consumeRouteNavigationBypass()).toBe(true);
    expect(consumeRouteNavigationBypass()).toBe(false);
  });
});
