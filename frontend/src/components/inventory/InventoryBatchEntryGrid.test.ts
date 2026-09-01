// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { defineComponent, nextTick } from "vue";
import { afterEach, describe, expect, it } from "vitest";

import InventoryBatchEntryGrid from "./InventoryBatchEntryGrid.vue";

afterEach(() => {
  document.body.innerHTML = "";
});

describe("InventoryBatchEntryGrid focus navigation", () => {
  it("keeps add-row and Enter focus inside the active grid instance", async () => {
    const TestHost = defineComponent({
      components: { InventoryBatchEntryGrid },
      template: `
        <div>
          <InventoryBatchEntryGrid model-value="" :fixtures="[]" mode="receipt" transaction-no="" />
          <InventoryBatchEntryGrid model-value="" :fixtures="[]" mode="receipt" transaction-no="" />
        </div>
      `
    });
    const wrapper = mount(TestHost, { attachTo: document.body });
    const grids = wrapper.findAllComponents(InventoryBatchEntryGrid);

    await grids[0].get('button[aria-label="新增一列"]').trigger("click");
    await nextTick();
    await grids[1].get('button[aria-label="新增一列"]').trigger("click");
    await nextTick();

    const firstGridFixtureFields = grids[0].findAll<HTMLInputElement>('[data-grid-column="fixtureCode"]');
    const secondGridFixtureFields = grids[1].findAll<HTMLInputElement>('[data-grid-column="fixtureCode"]');
    expect(document.activeElement).toBe(secondGridFixtureFields.at(-1)?.element);
    expect(document.activeElement).not.toBe(firstGridFixtureFields.at(-1)?.element);

    await secondGridFixtureFields[0].trigger("keydown", { key: "Enter" });
    await nextTick();

    expect(document.activeElement).toBe(secondGridFixtureFields[1].element);
    expect(document.activeElement).not.toBe(firstGridFixtureFields[1].element);

    wrapper.unmount();
  });
});
