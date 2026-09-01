import { describe, expect, it } from "vitest";

import {
  buildReportTransactionQuery,
  reportTransactionDateError
} from "@/utils/reportTransactionFilters";

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

  it("requires both dates for a specified receipt or return range", () => {
    expect(reportTransactionDateError("range_receipt", "", "")).toBe(
      "請同時選擇起始與結束日期。"
    );
    expect(reportTransactionDateError("range_return", "2026-07-01", "")).toBe(
      "請同時選擇起始與結束日期。"
    );
  });

  it("rejects a date range whose start is later than its end", () => {
    expect(
      reportTransactionDateError("range_receipt", "2026-07-31", "2026-07-01")
    ).toBe("起始日期不可晚於結束日期。");
  });

  it("accepts today modes and complete ordered ranges", () => {
    expect(reportTransactionDateError("today_receipt", "", "")).toBe("");
    expect(
      reportTransactionDateError("range_return", "2026-07-01", "2026-07-31")
    ).toBe("");
  });
});
