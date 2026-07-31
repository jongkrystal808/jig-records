import { describe, expect, it } from "vitest";

import { buildReportTransactionQuery } from "@/utils/reportTransactionFilters";

describe("buildReportTransactionQuery", () => {
  it("ignores date values when no receipt or return mode is selected", () => {
    expect(
      buildReportTransactionQuery("", "2026-07-01", "2026-07-30", "2026-07-30")
    ).toBeNull();
  });

  it("uses today's date for a today receipt filter", () => {
    expect(
      buildReportTransactionQuery("today_receipt", "", "", "2026-07-30")
    ).toEqual({
      transaction_type: "receipt",
      date_from: "2026-07-30",
      date_to: "2026-07-30"
    });
  });

  it("keeps the explicit range and return direction together", () => {
    expect(
      buildReportTransactionQuery(
        "range_return",
        "2026-07-01",
        "2026-07-15",
        "2026-07-30"
      )
    ).toEqual({
      transaction_type: "return",
      date_from: "2026-07-01",
      date_to: "2026-07-15"
    });
  });
});
