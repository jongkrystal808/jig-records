import { describe, expect, it } from "vitest";

import type { Fixture, MachineModel, Station } from "@/types";
import {
  acceptSimilarEntity,
  parseMappingBatchText,
  parseRequirementBatchText,
  type ProductionBatchCollections
} from "@/utils/productionBatchImport";

function makeCollections(): ProductionBatchCollections {
  return {
    models: [
      { id: 1, customer_id: 1, code: "EDS", name: "EDS", is_active: true } satisfies MachineModel,
      { id: 2, customer_id: 1, code: "FLEX", name: "FLEX", is_active: true } satisfies MachineModel
    ],
    stations: [
      { id: 11, customer_id: 1, code: "EDS_T1", name: "EDS_T1", is_active: true } satisfies Station,
      { id: 12, customer_id: 1, code: "EDS_T2", name: "EDS_T2", is_active: true } satisfies Station
    ],
    fixtures: [
      {
        id: 21,
        customer_id: 1,
        responsible_user_id: null,
        code: "TEST001",
        name: "TEST001",
        line_storage_location: null,
        department_storage_location: null,
        min_stock_qty: 0,
        description: null,
        is_active: true
      } satisfies Fixture
    ]
  };
}

describe("productionBatchImport", () => {
  it("parses exact mapping rows into ready state", () => {
    const rows = parseMappingBatchText("EDS,EDS_T1", makeCollections());

    expect(rows).toHaveLength(1);
    expect(rows[0]?.status).toBe("ready");
    expect(rows[0]?.model.resolvedCode).toBe("EDS");
    expect(rows[0]?.station.resolvedCode).toBe("EDS_T1");
  });

  it("marks similar mapping rows as needs-confirm and can accept suggestion", () => {
    const collections = makeCollections();
    const rows = parseMappingBatchText("EDS,EDS_T", collections);

    expect(rows[0]?.status).toBe("needs-confirm");
    expect(rows[0]?.station.suggestedCode).toBe("EDS_T1");

    acceptSimilarEntity(collections, rows[0]!.station);

    expect(rows[0]?.station.resolvedCode).toBe("EDS_T1");
  });

  it("parses requirement quantity validation errors", () => {
    const rows = parseRequirementBatchText("EDS_T1,TEST001,0", makeCollections());

    expect(rows).toHaveLength(1);
    expect(rows[0]?.status).toBe("error");
    expect(rows[0]?.message).toBe("數量必須是大於 0 的整數");
  });
});
