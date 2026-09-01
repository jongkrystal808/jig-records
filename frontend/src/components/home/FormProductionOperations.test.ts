// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "@/api";
import { selectedCustomerId } from "@/appState";
import FormProductionOperations from "./FormProductionOperations.vue";

vi.mock("@/confirmState", () => ({ requestConfirmation: vi.fn().mockResolvedValue(true) }));

afterEach(() => {
  vi.restoreAllMocks();
  selectedCustomerId.value = null;
});

describe("FormProductionOperations pagination", () => {
  it("returns to the previous page after deleting the final row on the last page", async () => {
    const row = {
      id: 4,
      model_id: 2,
      model_code: "MODEL-1",
      station_id: 3,
      station_code: "T1",
      fixture_id: 1,
      fixture_code: "FX-001",
      fixture_name: "治具一",
      required_qty: 1,
      stock_qty: 4
    };
    let deleted = false;
    const listFixtureRequirementsPage = vi.spyOn(api, "listFixtureRequirementsPage").mockImplementation(
      async (_customerId, page, pageSize) => ({
        items: [row],
        page: page ?? 1,
        page_size: pageSize ?? 50,
        total: deleted ? 50 : 51
      })
    );
    vi.spyOn(api, "deleteFixtureRequirement").mockImplementation(async () => {
      deleted = true;
      return undefined as never;
    });
    selectedCustomerId.value = 20;
    const wrapper = mount(FormProductionOperations, { props: { requestedView: "requirements" } });
    await flushPromises();

    await wrapper.findAll(".form-grid-pager button")[1].trigger("click");
    await flushPromises();
    expect(listFixtureRequirementsPage).toHaveBeenLastCalledWith(20, 2, 50, null, null, "");

    await wrapper.get(".danger-text-button").trigger("click");
    await flushPromises();

    expect(listFixtureRequirementsPage).toHaveBeenLastCalledWith(20, 1, 50, null, null, "");
    expect(wrapper.get(".form-grid-pager span").text()).toBe("第 1 / 1 頁");
    wrapper.unmount();
  });

  it("keeps Workbench filters and row editing in the right tool panel", async () => {
    const row = {
      id: 9,
      model_id: 2,
      model_code: "MODEL-1",
      station_id: 3,
      station_code: "T1",
      fixture_id: 1,
      fixture_code: "FX-001",
      fixture_name: "治具一",
      required_qty: 2,
      stock_qty: 8
    };
    vi.spyOn(api, "listFixtureRequirementsPage").mockResolvedValue({
      items: [row], page: 1, page_size: 50, total: 1
    });
    const toolPanel = document.createElement("div");
    toolPanel.id = "workbench-management-tools";
    document.body.appendChild(toolPanel);
    selectedCustomerId.value = 20;

    const wrapper = mount(FormProductionOperations, {
      attachTo: document.body,
      props: { requestedView: "requirements", workbenchLayout: true }
    });
    await flushPromises();

    expect(toolPanel.textContent).toContain("篩選條件");
    await wrapper.get(".form-report-grid .text-button").trigger("click");
    await flushPromises();
    expect(toolPanel.textContent).toContain("編輯治具需求");
    expect(toolPanel.textContent).toContain("每站需求量");
    expect(wrapper.find(".form-report-grid input").exists()).toBe(false);

    wrapper.unmount();
    toolPanel.remove();
  });
});
