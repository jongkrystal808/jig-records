import type { Fixture, IdentifierStockSummary, StockSummary } from "@/types";

export type InventoryPreviewSeedRow = {
  resolvedFixtureId: number | null;
  inputToken: string;
  quantity: number;
};

export type InventoryPreviewStats = {
  currentIdentifierStockQty: number | null;
  nextIdentifierStockQty: number | null;
};

function buildIdentifierKey(fixtureId: number, identifier: string): string {
  return `${fixtureId}::${identifier}`;
}

export function buildInventoryPreviewStats(
  rows: InventoryPreviewSeedRow[],
  identifierStockRows: IdentifierStockSummary[],
  fixtures: Fixture[],
  stockRows: StockSummary[]
): InventoryPreviewStats[] {
  const identifierQtyByKey = new Map(identifierStockRows.map((row) => [buildIdentifierKey(row.fixture_id, row.identifier), row.stock_qty]));
  const fixtureById = new Map(fixtures.map((fixture) => [fixture.id, fixture]));
  const stockByFixtureId = new Map(stockRows.map((row) => [row.fixture_id, row]));
  const runningIdentifierDeltaByKey = new Map<string, number>();

  return rows.map((row) => {
    if (!row.resolvedFixtureId || !row.inputToken) {
      return {
        currentIdentifierStockQty: null,
        nextIdentifierStockQty: null
      };
    }

    const fixture = fixtureById.get(row.resolvedFixtureId);
    const stock = stockByFixtureId.get(row.resolvedFixtureId);
    if (!fixture || !stock) {
      return {
        currentIdentifierStockQty: null,
        nextIdentifierStockQty: null
      };
    }

    const identifierKey = buildIdentifierKey(row.resolvedFixtureId, row.inputToken);
    const currentIdentifierStockQty = identifierQtyByKey.get(identifierKey) ?? 0;
    const previousIdentifierDelta = runningIdentifierDeltaByKey.get(identifierKey) ?? 0;
    const nextIdentifierStockQty = currentIdentifierStockQty + previousIdentifierDelta + row.quantity;
    runningIdentifierDeltaByKey.set(identifierKey, previousIdentifierDelta + row.quantity);

    return {
      currentIdentifierStockQty,
      nextIdentifierStockQty
    };
  });
}
