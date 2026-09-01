// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import FixtureReportRowActions from "@/components/inventory/FixtureReportRowActions.vue";
import type { InventoryReportMobileRow } from "@/components/inventory/InventoryReportMobileCards.vue";

const row: InventoryReportMobileRow = {
  key: "fixture-1-model-2-station-3",
  customerCode: "TEST",
  fixtureId: 1,
  fixtureCode: "FX-001",
  fixtureName: "治具一",
  stockQty: 5,
  customerSuppliedQty: 5,
  selfPurchasedQty: 0,
  minStockQty: 1,
  waterStatus: "normal",
  lineStorage: "A1",
  departmentStorage: "D1",
  modelId: 2,
  modelCode: "MODEL-1",
  stationId: 3,
  stationCode: "ST-1",
  stationName: "站點一",
  requiredQty: 1,
  maxOpenStationCount: 5,
  configurationStatus: "configured"
};

describe("FixtureReportRowActions", () => {
  it("offers role-gated report handoffs for a configured fixture", async () => {
    const wrapper = mount(FixtureReportRowActions, { props: { row } });
    const buttons = wrapper.findAll("button");

    await buttons[0].trigger("click");
    await buttons[1].trigger("click");
    await buttons[2].trigger("click");
    await buttons[3].trigger("click");

    expect(wrapper.emitted("quickTransaction")).toEqual([["receipt"], ["return"]]);
    expect(wrapper.emitted("editFixture")).toHaveLength(1);
    expect(wrapper.emitted("viewProduction")).toHaveLength(1);
  });

  it("disables production handoff when the row has no model/station configuration", () => {
    const wrapper = mount(FixtureReportRowActions, {
      props: { row: { ...row, modelId: 0, stationId: 0 } }
    });

    expect(wrapper.findAll("button")[3].attributes("disabled")).toBeDefined();
  });
});
