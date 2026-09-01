// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import ModelInfoPanel from "./ModelInfoPanel.vue";

describe("ModelInfoPanel designated requirements", () => {
  it("shows selected identifiers and explains designated stock capacity", () => {
    const wrapper = mount(ModelInfoPanel, {
      props: {
        model: { id: 1, code: "MODEL-01", name: "Model 01" },
        queryData: {
          model_id: 1,
          model_code: "MODEL-01",
          model_name: "Model 01",
          max_open_station_count: 1,
          station_count: 1,
          fixture_type_count: 1,
          total_stock_qty: 2,
          stations: [{
            station_id: 2,
            station_code: "ST-01",
            station_name: "Station 01",
            max_open_station_count: 1,
            bottleneck_fixture_code: "FX-01"
          }],
          station_requirements: [{
            station_id: 2,
            station_code: "ST-01",
            fixture_id: 3,
            fixture_code: "FX-01",
            fixture_name: "Fixture 01",
            required_qty: 2,
            designated_mode: true,
            designated_identifiers: ["0001", "DC-A"],
            stock_qty: 2,
            max_open_station_count: 1,
            stock_status: "normal"
          }],
          fixtures: []
        },
        fixtures: [],
        visibleSections: { summary: false, stations: false, fixtures: false, requirements: true },
        formatCount: (value: number) => String(value),
        canAccessProduction: true,
        goToProduction: vi.fn()
      }
    });

    expect(wrapper.get(".designated-mode-note").text()).toContain("只採計列出的 identifier");
    expect(wrapper.get(".designated-mode-cell").text()).toContain("指定模式");
    expect(wrapper.get(".designated-mode-cell").text()).toContain("0001、DC-A");
  });
});
