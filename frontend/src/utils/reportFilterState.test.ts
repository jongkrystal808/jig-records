import { describe, expect, it } from "vitest";

import {
  pendingReportConditionCount,
  type ReportFilterState,
  type ReportTransactionFilterState
} from "./reportFilterState";

const emptyFilters = (): ReportFilterState => ({
  keyword: "",
  fixtureStatus: ["active"],
  fixtureId: "",
  stationId: "",
  modelId: "",
  waterStatus: [],
  storage: "",
  configurationStatus: []
});

const emptyTransactions = (): ReportTransactionFilterState => ({
  mode: "",
  dateFrom: "",
  dateTo: "",
  ownershipType: []
});

describe("pending report conditions", () => {
  it("counts a newly selected model as one unapplied condition", () => {
    const draft = emptyFilters();
    draft.modelId = "12";

    expect(
      pendingReportConditionCount(draft, emptyFilters(), emptyTransactions(), emptyTransactions())
    ).toBe(1);
  });

  it("counts a fixture status change as one unapplied condition", () => {
    const draft = emptyFilters();
    draft.fixtureStatus = ["inactive"];

    expect(
      pendingReportConditionCount(draft, emptyFilters(), emptyTransactions(), emptyTransactions())
    ).toBe(1);
  });

  it("counts the quick unconfigured filter as one condition", () => {
    const draft = emptyFilters();
    draft.configurationStatus = ["unconfigured"];

    expect(
      pendingReportConditionCount(draft, emptyFilters(), emptyTransactions(), emptyTransactions())
    ).toBe(1);
  });

  it("treats a changed date range as one condition", () => {
    const appliedTransaction = {
      mode: "range_receipt",
      dateFrom: "2026-07-01",
      dateTo: "2026-07-02",
      ownershipType: []
    };
    const draftTransaction = {
      ...appliedTransaction,
      dateTo: "2026-07-03"
    };

    expect(
      pendingReportConditionCount(
        emptyFilters(),
        emptyFilters(),
        draftTransaction,
        appliedTransaction
      )
    ).toBe(1);
  });

  it("counts a range mode without dates as one pending condition", () => {
    const draftTransaction = {
      ...emptyTransactions(),
      mode: "range_receipt"
    };

    expect(
      pendingReportConditionCount(
        emptyFilters(),
        emptyFilters(),
        draftTransaction,
        emptyTransactions()
      )
    ).toBe(1);
  });

  it("ignores inactive date and ownership values", () => {
    const draftTransaction = {
      mode: "",
      dateFrom: "2026-07-01",
      dateTo: "2026-07-02",
      ownershipType: ["customer_supplied"]
    };

    expect(
      pendingReportConditionCount(
        emptyFilters(),
        emptyFilters(),
        draftTransaction,
        emptyTransactions()
      )
    ).toBe(0);
  });
});
