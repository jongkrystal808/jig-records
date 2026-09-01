import { describe, expect, it } from "vitest";

import { extractErrorMessage } from "@/utils/apiError";
import { formatLocalDate, formatLocalDateKey } from "@/utils/date";
import { fixtureImageUrlByCode } from "@/api";
import { fallbackText, ownershipLabel, stockStatusLabel, capacityStateLabel } from "@/utils/display";

describe("frontend utils", () => {
  it("formats a local date key", () => {
    const value = formatLocalDateKey(new Date(2026, 5, 10));
    expect(value).toBe("2026-06-10");
  });

  it("formats all user-facing date values without time", () => {
    expect(formatLocalDate("2026-08-04T15:37:29+08:00")).toBe("2026-08-04");
    expect(formatLocalDate("2026-08-04")).toBe("2026-08-04");
    expect(formatLocalDate(new Date(2026, 7, 4, 15, 37, 29))).toBe("2026-08-04");
  });

  it("extracts API detail messages", () => {
    expect(extractErrorMessage('{"detail":"欄位驗證失敗"}', "fallback")).toBe("欄位驗證失敗");
    expect(extractErrorMessage('{"error":{"message":"not found"}}', "fallback")).toBe("not found");
    expect(
      extractErrorMessage(
        '{"detail":[{"loc":["body","code"],"msg":"Field required","type":"missing"},{"loc":["query","customer_id"],"msg":"Must be positive","type":"greater_than"}]}',
        "fallback"
      )
    ).toBe("body.code: Field required；query.customer_id: Must be positive");
  });

  it("falls back to raw body or fallback message", () => {
    expect(extractErrorMessage("plain text error", "fallback")).toBe("plain text error");
    expect(extractErrorMessage("", "fallback")).toBe("fallback");
    expect(extractErrorMessage("x".repeat(300), "fallback")).toHaveLength(240);
  });

  it("builds fixture image urls", () => {
    expect(fixtureImageUrlByCode("C-00003", 7)).toBe(
      "/api/v2/master/fixtures/C-00003/image?customer_id=7"
    );
  });

  it("formats shared display helpers", () => {
    expect(fallbackText("")).toBe("-");
    expect(fallbackText("  ", "N/A")).toBe("N/A");
    expect(stockStatusLabel("low_stock")).toBe("低水位");
    expect(ownershipLabel("self_purchased")).toBe("自購");
    expect(capacityStateLabel("warn")).toBe("接近上限");
  });
});
