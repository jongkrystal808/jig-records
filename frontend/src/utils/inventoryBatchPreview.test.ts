import { describe, expect, it } from "vitest";

import type { Fixture, StockSummary } from "@/types";
import { buildInventoryPreviewStats } from "@/utils/inventoryBatchPreview";

const fixture: Fixture = {
  id: 17,
  customer_id: 1,
  responsible_user_id: null,
  code: "L-00017",
  name: "Fixture 17",
  line_storage_location: null,
  department_storage_location: null,
  min_stock_qty: 3,
  description: null,
  is_active: true,
  has_image: false
};

const stockRow: StockSummary = {
  fixture_id: 17,
  fixture_code: "L-00017",
  fixture_name: "Fixture 17",
  stock_qty: 10,
  min_stock_qty: 3,
  stock_status: "normal",
  last_transaction_at: null
};

describe("inventoryBatchPreview", () => {
  it("calculates next identifier stock for return rows", () => {
    const stats = buildInventoryPreviewStats(
      [{ resolvedFixtureId: 17, inputToken: "0001", quantity: -3 }],
      [{ fixture_id: 17, identifier: "0001", stock_qty: 10 }],
      [fixture],
      [stockRow]
    );

    expect(stats).toEqual([
      {
        currentIdentifierStockQty: 10,
        nextIdentifierStockQty: 7
      }
    ]);
  });

  it("accumulates repeated identifier rows in preview order", () => {
    const stats = buildInventoryPreviewStats(
      [
        { resolvedFixtureId: 17, inputToken: "0001", quantity: -3 },
        { resolvedFixtureId: 17, inputToken: "0001", quantity: -2 }
      ],
      [{ fixture_id: 17, identifier: "0001", stock_qty: 10 }],
      [fixture],
      [stockRow]
    );

    expect(stats).toEqual([
      {
        currentIdentifierStockQty: 10,
        nextIdentifierStockQty: 7
      },
      {
        currentIdentifierStockQty: 10,
        nextIdentifierStockQty: 5
      }
    ]);
  });

  it("returns null preview stats for unresolved rows", () => {
    const stats = buildInventoryPreviewStats(
      [{ resolvedFixtureId: null, inputToken: "0001", quantity: -3 }],
      [{ fixture_id: 17, identifier: "0001", stock_qty: 10 }],
      [fixture],
      [stockRow]
    );

    expect(stats[0]).toEqual({
      currentIdentifierStockQty: null,
      nextIdentifierStockQty: null
    });
  });
});
