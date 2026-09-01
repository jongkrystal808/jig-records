import { describe, expect, it } from "vitest";

import {
  REPORT_COLUMN_DEFINITIONS,
  reportColumnPreset,
  reportColumnPresetKey
} from "./reportColumnPresets";

describe("report column presets", () => {
  it("provides the requested stock ownership fields in floor stock", () => {
    expect(reportColumnPreset("floorStock")).toEqual(
      expect.arrayContaining([
        "stockQty",
        "customerSuppliedQty",
        "selfPurchasedQty",
        "minStockQty",
        "waterStatus"
      ])
    );
  });

  it("provides model, station, requirement and capacity in configuration check", () => {
    const configurationCheck = reportColumnPreset("configurationCheck");

    expect(configurationCheck).toEqual(
      expect.arrayContaining([
        "modelCode",
        "station",
        "requiredQty",
        "maxOpenStationCount"
      ])
    );
    expect(reportColumnPresetKey(configurationCheck)).toBe("configurationCheck");
  });

  it("keeps full report synchronized with every column definition", () => {
    const full = reportColumnPreset("full");

    expect(full).toEqual(REPORT_COLUMN_DEFINITIONS.map((column) => column.key));
    expect(reportColumnPresetKey(full)).toBe("full");
    expect(reportColumnPresetKey(full.filter((column) => column !== "customer"))).toBeNull();
  });
});
