import { describe, expect, it } from "vitest";

import type { ModelStation, Station } from "@/types";
import { getAvailableRequirementStations } from "@/utils/productionStations";

describe("getAvailableRequirementStations", () => {
  it("returns only stations mapped to the selected model, sorted by code", () => {
    const stations = [
      { id: 6, customer_id: 2, code: "Z-UNMAPPED", name: "Unmapped", is_active: true } satisfies Station,
      { id: 7, customer_id: 2, code: "B-ST02", name: "Station 2", is_active: true } satisfies Station,
      { id: 8, customer_id: 2, code: "A-ST01", name: "Station 1", is_active: true } satisfies Station
    ];
    const mappings = [
      { id: 1, model_id: 4, station_id: 7 } satisfies ModelStation,
      { id: 2, model_id: 4, station_id: 8 } satisfies ModelStation,
      { id: 3, model_id: 5, station_id: 6 } satisfies ModelStation
    ];

    expect(getAvailableRequirementStations(stations, mappings, 4).map((row) => row.id)).toEqual([8, 7]);
  });

  it("returns an empty list when no model is selected", () => {
    expect(getAvailableRequirementStations([], [], null)).toEqual([]);
  });
});
