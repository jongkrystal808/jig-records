// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";

import UiModalShell from "@/components/common/UiModalShell.vue";
import ProductionRequirementCopyModal from "@/components/production/ProductionRequirementCopyModal.vue";

const baseProps = {
  open: true,
  saving: false,
  sourceModelId: 1,
  sourceModelCode: "MODEL-A",
  sourceStationId: 10,
  sourceStationCode: "ST-01",
  models: [
    { id: 1, customer_id: 20, code: "MODEL-A", name: "Model A", is_active: true }
  ],
  stations: [
    { id: 10, customer_id: 20, code: "ST-01", name: "Station 1", is_active: true },
    { id: 11, customer_id: 20, code: "ST-02", name: "Station 2", is_active: true }
  ],
  mappings: [
    { id: 1, model_id: 1, station_id: 10 },
    { id: 2, model_id: 1, station_id: 11 }
  ],
  requirements: [
    {
      id: 1,
      model_id: 1,
      model_code: "MODEL-A",
      station_id: 10,
      station_code: "ST-01",
      fixture_id: 100,
      fixture_code: "FIX-01",
      fixture_name: "Fixture 1",
      required_qty: 2,
      stock_qty: 4
    }
  ]
};

afterEach(() => {
  document.body.innerHTML = "";
});

describe("ProductionRequirementCopyModal", () => {
  it("uses the shared shell and ignores Escape while saving", async () => {
    const trigger = document.createElement("button");
    trigger.textContent = "開啟需求複製";
    document.body.append(trigger);
    trigger.focus();

    const wrapper = mount(ProductionRequirementCopyModal, {
      attachTo: document.body,
      props: baseProps
    });
    await flushPromises();

    expect(wrapper.findComponent(UiModalShell).exists()).toBe(true);
    expect(document.activeElement).toBe(document.body.querySelector(".copy-fields select"));

    await wrapper.setProps({ saving: true });
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    expect(wrapper.emitted("close")).toBeUndefined();

    await wrapper.setProps({ saving: false });
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    expect(wrapper.emitted("close")).toHaveLength(1);

    await wrapper.setProps({ open: false });
    await flushPromises();
    expect(document.activeElement).toBe(trigger);
    wrapper.unmount();
  });
});
