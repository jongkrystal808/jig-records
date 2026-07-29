import { describe, expect, it } from "vitest";

import { calculateProjectedStationCapacity } from "@/utils/productionCapacityPreview";

const stocks = [
  { fixture_id: 1, stock_qty: 12 },
  { fixture_id: 2, stock_qty: 5 },
  { fixture_id: 3, stock_qty: 0 }
];

describe("calculateProjectedStationCapacity", () => {
  it("returns null until a fixture is selected", () => {
    expect(
      calculateProjectedStationCapacity({
        requirements: [],
        stocks,
        fixtureId: null,
        fixtureCode: "",
        requiredQty: 1,
        editingRequirementId: null
      })
    ).toBeNull();
  });

  it("calculates the new station bottleneck", () => {
    expect(
      calculateProjectedStationCapacity({
        requirements: [
          { id: 10, fixture_id: 1, fixture_code: "F-001", required_qty: 2 }
        ],
        stocks,
        fixtureId: 2,
        fixtureCode: "F-002",
        requiredQty: 2,
        editingRequirementId: null
      })
    ).toEqual({
      maxOpenStationCount: 2,
      bottleneckFixtureCode: "F-002"
    });
  });

  it("replaces an existing fixture instead of counting it twice", () => {
    expect(
      calculateProjectedStationCapacity({
        requirements: [
          { id: 10, fixture_id: 1, fixture_code: "F-001", required_qty: 2 },
          { id: 11, fixture_id: 2, fixture_code: "F-002", required_qty: 1 }
        ],
        stocks,
        fixtureId: 1,
        fixtureCode: "F-001",
        requiredQty: 4,
        editingRequirementId: 10
      })
    ).toEqual({
      maxOpenStationCount: 3,
      bottleneckFixtureCode: "F-001"
    });
  });

  it("treats missing inventory as zero capacity", () => {
    expect(
      calculateProjectedStationCapacity({
        requirements: [],
        stocks,
        fixtureId: 99,
        fixtureCode: "F-099",
        requiredQty: 1,
        editingRequirementId: null
      })
    ).toEqual({
      maxOpenStationCount: 0,
      bottleneckFixtureCode: "F-099"
    });
  });
});
