import { describe, expect, it } from "vitest";

import { calculateRequirementCopyPreview } from "@/utils/productionCopy";

describe("calculateRequirementCopyPreview", () => {
  const sourceRows = [
    { fixture_id: 1, required_qty: 2 },
    { fixture_id: 2, required_qty: 3 },
    { fixture_id: 3, required_qty: 4 }
  ];
  const targetRows = [
    { fixture_id: 1, required_qty: 5 },
    { fixture_id: 2, required_qty: 3 }
  ];

  it("skips every target conflict in safe mode", () => {
    expect(calculateRequirementCopyPreview(sourceRows, targetRows, false)).toEqual({
      sourceCount: 3,
      createCount: 1,
      conflictCount: 2,
      updateCount: 0,
      unchangedCount: 1,
      skipCount: 2
    });
  });

  it("updates changed conflicts and skips identical rows in overwrite mode", () => {
    expect(calculateRequirementCopyPreview(sourceRows, targetRows, true)).toEqual({
      sourceCount: 3,
      createCount: 1,
      conflictCount: 2,
      updateCount: 1,
      unchangedCount: 1,
      skipCount: 1
    });
  });
});
