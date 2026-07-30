import { describe, expect, it } from "vitest";

import { groupIdentifierStockByOwnership } from "@/utils/display";

describe("groupIdentifierStockByOwnership", () => {
  it("creates only a customer-supplied group when self-purchased stock is zero", () => {
    expect(
      groupIdentifierStockByOwnership([
        { identifier: "0001", customer_supplied_qty: 8, self_purchased_qty: 0 }
      ])
    ).toEqual([
      {
        ownershipType: "customer_supplied",
        label: "客供",
        totalQty: 8,
        entries: [{ identifier: "0001", quantity: 8 }]
      }
    ]);
  });

  it("creates only a self-purchased group when customer-supplied stock is zero", () => {
    expect(
      groupIdentifierStockByOwnership([
        { identifier: "0002", customer_supplied_qty: 0, self_purchased_qty: 5 }
      ])
    ).toEqual([
      {
        ownershipType: "self_purchased",
        label: "自購",
        totalQty: 5,
        entries: [{ identifier: "0002", quantity: 5 }]
      }
    ]);
  });

  it("splits a mixed identifier into both source groups using each source quantity", () => {
    expect(
      groupIdentifierStockByOwnership([
        { identifier: "0001", customer_supplied_qty: 1, self_purchased_qty: 0 },
        { identifier: "0002", customer_supplied_qty: 0, self_purchased_qty: 2 },
        { identifier: "0003", customer_supplied_qty: 1, self_purchased_qty: 1 }
      ])
    ).toEqual([
      {
        ownershipType: "customer_supplied",
        label: "客供",
        totalQty: 2,
        entries: [
          { identifier: "0001", quantity: 1 },
          { identifier: "0003", quantity: 1 }
        ]
      },
      {
        ownershipType: "self_purchased",
        label: "自購",
        totalQty: 3,
        entries: [
          { identifier: "0002", quantity: 2 },
          { identifier: "0003", quantity: 1 }
        ]
      }
    ]);
  });
});
