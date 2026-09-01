// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import { onboardingActive } from "@/appState";
import ProductionDetailSection from "./ProductionDetailSection.vue";

function props() {
  return {
    canEdit: true,
    loading: false,
    savingMapping: false,
    savingRequirement: false,
    editingMappingId: null,
    editingRequirementId: null,
    selectedModelCode: "MODEL-01",
    selectedRequirementStationId: 1,
    selectedStationCode: "ST-01",
    selectedStationName: "測試站",
    stationCapacityCount: 2,
    stationBottleneckFixtureCode: "",
    projectedCapacity: null,
    selectedFixtureAlreadyConfigured: false,
    selectedModelStationRows: [],
    selectedStationRequirementRows: [],
    sourceRequirementCount: 0,
    mappingStationCodeInput: "",
    fixtureCodeInput: "",
    requiredQty: 1,
    designatedMode: false,
    designatedIdentifiers: [],
    identifierStockRows: [],
    openAutocompleteKey: null,
    filteredStationSuggestions: [],
    filteredFixtureSuggestions: [],
    onOpenMappingBatchModal: vi.fn(),
    onOpenRequirementBatchModal: vi.fn(),
    onOpenRequirementCopyModal: vi.fn(),
    onImportModelStationsCsv: vi.fn(),
    onImportFixtureRequirementsCsv: vi.fn(),
    onSaveMapping: vi.fn(),
    onResetMappingEditor: vi.fn(),
    onStartEditMapping: vi.fn(),
    onRemoveMapping: vi.fn(),
    onSelectMappingStation: vi.fn(),
    onSaveRequirement: vi.fn(),
    onResetRequirementEditor: vi.fn(),
    onStartEditRequirement: vi.fn(),
    onRemoveRequirement: vi.fn(),
    onMappingStationFocus: vi.fn(),
    onMappingStationInput: vi.fn(),
    onMappingStationBlur: vi.fn(),
    onSelectMappingStationSuggestion: vi.fn(),
    onFixtureFocus: vi.fn(),
    onFixtureInput: vi.fn(),
    onFixtureBlur: vi.fn(),
    onSelectFixtureSuggestion: vi.fn(),
    onRequiredQtyChange: vi.fn(),
    onDesignatedModeChange: vi.fn(),
    onDesignatedIdentifiersChange: vi.fn()
  };
}

describe("ProductionDetailSection editors", () => {
  it("starts both create forms collapsed and expands them on demand", async () => {
    onboardingActive.value = false;
    const wrapper = mount(ProductionDetailSection, {
      props: props()
    });

    expect(wrapper.find(".station-create-card").exists()).toBe(false);
    expect(wrapper.find(".requirement-editor").exists()).toBe(false);
    expect(wrapper.find(".read-only-note").exists()).toBe(false);

    await wrapper.get("button[aria-expanded='false']").trigger("click");
    expect(wrapper.find(".station-create-card").exists()).toBe(true);

    const requirementButton = wrapper
      .findAll("button")
      .find((button) => button.text().includes("加入治具需求"));
    expect(requirementButton).toBeTruthy();
    await requirementButton!.trigger("click");
    expect(wrapper.find(".requirement-editor").exists()).toBe(true);

    wrapper.unmount();
  });

  it("shows the read-only note only when editing is unavailable", () => {
    onboardingActive.value = false;
    const wrapper = mount(ProductionDetailSection, {
      props: {
        ...props(),
        canEdit: false
      }
    });

    expect(wrapper.find(".station-create-card").exists()).toBe(false);
    expect(wrapper.get(".read-only-note").text()).toBe("目前為訪客模式，可查看設定但不能修改。");

    wrapper.unmount();
  });

  it("shows in-stock identifiers and reports selected values in designated mode", async () => {
    const componentProps = {
      ...props(),
      fixtureCodeInput: "FX-01",
      designatedMode: true,
      identifierStockRows: [
        {
          fixture_id: 100,
          identifier: "0001",
          stock_qty: 3,
          customer_supplied_qty: 0,
          self_purchased_qty: 3
        }
      ]
    };
    const wrapper = mount(ProductionDetailSection, { props: componentProps });
    const requirementButton = wrapper.findAll("button").find((button) => button.text().includes("加入治具需求"));
    await requirementButton!.trigger("click");

    expect(wrapper.get(".identifier-option").text()).toContain("0001");
    expect(wrapper.get(".identifier-option").text()).toContain("可用 3 pcs");
    await wrapper.get(".identifier-option input").setValue(true);
    expect(componentProps.onDesignatedIdentifiersChange).toHaveBeenCalledWith(["0001"]);
  });
});
