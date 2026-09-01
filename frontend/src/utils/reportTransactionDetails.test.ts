import { describe, expect, it } from "vitest";

import type { TransactionOverviewRow } from "@/types";
import {
  expandReportRowsWithTransactionDetails,
  groupReportTransactionDetails
} from "@/utils/reportTransactionDetails";

function transaction(
  id: number,
  fixtureCode: string,
  identifier: string
): TransactionOverviewRow {
  return {
    id,
    transaction_type: "receipt",
    transaction_no: `TX-${id}`,
    occurred_at: "2026-07-31",
    created_by: "tester",
    fixture_id: id,
    fixture_code: fixtureCode,
    fixture_name: fixtureCode,
    ownership_type: "customer_supplied",
    identifier,
    quantity: 1,
    note: null
  };
}

describe("report transaction details", () => {
  it("groups transaction rows by normalized fixture code", () => {
    const groups = groupReportTransactionDetails([
      transaction(1, " jig-01 ", "DC-1"),
      transaction(2, "JIG-01", "DC-2"),
      transaction(3, "JIG-02", "DC-3")
    ]);

    expect(groups.get("JIG-01")?.map((row) => row.identifier)).toEqual(["DC-1", "DC-2"]);
    expect(groups.get("JIG-02")).toHaveLength(1);
  });

  it("exports each fixture detail once while retaining later configuration rows", () => {
    const reportRows = [
      { fixtureCode: "JIG-01", station: "ST-01" },
      { fixtureCode: "JIG-01", station: "ST-02" },
      { fixtureCode: "JIG-02", station: "ST-01" }
    ];
    const details = groupReportTransactionDetails([
      transaction(1, "JIG-01", "DC-1"),
      transaction(2, "JIG-01", "DC-2")
    ]);

    const rows = expandReportRowsWithTransactionDetails(reportRows, details);

    expect(rows).toHaveLength(4);
    expect(rows.map((row) => [row.reportRow.station, row.detail?.identifier ?? null])).toEqual([
      ["ST-01", "DC-1"],
      ["ST-01", "DC-2"],
      ["ST-02", null],
      ["ST-01", null]
    ]);
  });
});
