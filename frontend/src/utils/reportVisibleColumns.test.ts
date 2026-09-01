import { describe, expect, it } from "vitest";

import {
  autoHiddenReportColumns,
  effectiveReportColumns
} from "./reportVisibleColumns";

describe("report visible columns", () => {
  it("removes selected columns that are empty across the filtered result", () => {
    const selected = [
      "index",
      "fixtureCode",
      "modelCode",
      "station",
      "requiredQty"
    ] as const;
    const effective = effectiveReportColumns(
      [...selected],
      ["index", "fixtureCode"],
      12
    );

    expect(effective).toEqual(["index", "fixtureCode"]);
    expect(autoHiddenReportColumns([...selected], effective)).toEqual([
      "modelCode",
      "station",
      "requiredQty"
    ]);
  });

  it("keeps the selected layout before data is available or when no rows match", () => {
    expect(
      effectiveReportColumns(["fixtureCode", "modelCode"], [], 0)
    ).toEqual(["fixtureCode", "modelCode"]);
  });

  it("keeps one selected column when every selected field is empty", () => {
    expect(
      effectiveReportColumns(["lineStorage", "departmentStorage"], ["fixtureCode"], 4)
    ).toEqual(["lineStorage"]);
  });
});
