import { afterEach, describe, expect, it } from "vitest";

import {
  confirmationState,
  requestConfirmation,
  settleConfirmation
} from "./confirmState";

afterEach(() => {
  settleConfirmation(false);
});

describe("confirmation state", () => {
  it("resolves the active confirmation and applies dialog options", async () => {
    const result = requestConfirmation("確定刪除嗎？", {
      title: "刪除資料？",
      confirmLabel: "刪除",
      tone: "danger"
    });

    expect(confirmationState).toMatchObject({
      open: true,
      title: "刪除資料？",
      message: "確定刪除嗎？",
      confirmLabel: "刪除",
      tone: "danger"
    });

    settleConfirmation(true);

    await expect(result).resolves.toBe(true);
    expect(confirmationState.open).toBe(false);
  });

  it("cancels an older request when a newer confirmation replaces it", async () => {
    const first = requestConfirmation("第一個");
    const second = requestConfirmation("第二個");

    await expect(first).resolves.toBe(false);
    expect(confirmationState.message).toBe("第二個");

    settleConfirmation(false);
    await expect(second).resolves.toBe(false);
  });
});
