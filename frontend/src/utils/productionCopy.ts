type RequirementCopyRow = {
  fixture_id: number;
  required_qty: number;
};

export type RequirementCopyPreview = {
  sourceCount: number;
  createCount: number;
  conflictCount: number;
  updateCount: number;
  unchangedCount: number;
  skipCount: number;
};

export function calculateRequirementCopyPreview(
  sourceRows: RequirementCopyRow[],
  targetRows: RequirementCopyRow[],
  overwriteExisting: boolean
): RequirementCopyPreview {
  const targetByFixtureId = new Map(targetRows.map((row) => [row.fixture_id, row.required_qty]));
  let createCount = 0;
  let conflictCount = 0;
  let updateCount = 0;
  let unchangedCount = 0;

  for (const sourceRow of sourceRows) {
    const targetQty = targetByFixtureId.get(sourceRow.fixture_id);
    if (targetQty === undefined) {
      createCount += 1;
      continue;
    }
    conflictCount += 1;
    if (targetQty === sourceRow.required_qty) {
      unchangedCount += 1;
    } else if (overwriteExisting) {
      updateCount += 1;
    }
  }

  return {
    sourceCount: sourceRows.length,
    createCount,
    conflictCount,
    updateCount,
    unchangedCount,
    skipCount: overwriteExisting ? unchangedCount : conflictCount
  };
}
