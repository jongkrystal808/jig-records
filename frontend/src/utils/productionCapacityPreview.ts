export type CapacityPreviewRequirement = {
  id: number;
  fixture_id: number;
  fixture_code: string;
  required_qty: number;
};

export type CapacityPreviewStock = {
  fixture_id: number;
  stock_qty: number;
};

export type ProjectedStationCapacity = {
  maxOpenStationCount: number;
  bottleneckFixtureCode: string;
};

type CalculateProjectedCapacityOptions = {
  requirements: CapacityPreviewRequirement[];
  stocks: CapacityPreviewStock[];
  fixtureId: number | null;
  fixtureCode: string;
  requiredQty: number;
  editingRequirementId: number | null;
};

export function calculateProjectedStationCapacity(
  options: CalculateProjectedCapacityOptions
): ProjectedStationCapacity | null {
  if (options.fixtureId === null || !options.fixtureCode.trim() || options.requiredQty < 1) {
    return null;
  }

  const stockByFixtureId = new Map(options.stocks.map((row) => [row.fixture_id, row.stock_qty]));
  const nextRequirements = options.requirements
    .filter(
      (row) =>
        row.id !== options.editingRequirementId &&
        row.fixture_id !== options.fixtureId
    )
    .map((row) => ({
      fixtureId: row.fixture_id,
      fixtureCode: row.fixture_code,
      requiredQty: row.required_qty
    }));

  nextRequirements.push({
    fixtureId: options.fixtureId,
    fixtureCode: options.fixtureCode,
    requiredQty: options.requiredQty
  });

  let maxOpenStationCount = Number.POSITIVE_INFINITY;
  let bottleneckFixtureCode = "";

  for (const requirement of nextRequirements) {
    const stockQty = stockByFixtureId.get(requirement.fixtureId) ?? 0;
    const capacity = Math.floor(stockQty / requirement.requiredQty);
    if (capacity < maxOpenStationCount) {
      maxOpenStationCount = capacity;
      bottleneckFixtureCode = requirement.fixtureCode;
    }
  }

  return {
    maxOpenStationCount:
      maxOpenStationCount === Number.POSITIVE_INFINITY ? 0 : maxOpenStationCount,
    bottleneckFixtureCode
  };
}
