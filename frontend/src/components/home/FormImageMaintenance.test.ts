// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "@/api";
import * as apiModule from "@/api";
import { selectedCustomerId } from "@/appState";
import FormImageMaintenance from "@/components/home/FormImageMaintenance.vue";
import type { Fixture } from "@/types";

const fixture: Fixture = {
  id: 1,
  customer_id: 20,
  responsible_user_id: null,
  code: "FX-001",
  name: "Fixture 1",
  line_storage_location: null,
  department_storage_location: null,
  min_stock_qty: 0,
  description: null,
  is_active: true,
  has_image: false
};

afterEach(() => {
  vi.restoreAllMocks();
  selectedCustomerId.value = null;
});

describe("FormImageMaintenance", () => {
  it("uses backend pagination and supports 50/100 rows per page", async () => {
    selectedCustomerId.value = 20;
    const listPage = vi.spyOn(api, "listFixturesPage").mockImplementation(async (_customerId, page = 1, pageSize = 50) => ({
      items: [{ ...fixture, id: page, code: `FX-${page}` }],
      page,
      page_size: pageSize,
      total: 120
    }));

    const wrapper = mount(FormImageMaintenance, {
      global: { stubs: { FixtureImageDialog: true } }
    });
    await flushPromises();

    expect(listPage).toHaveBeenLastCalledWith(20, 1, 50, "", "all", "all");
    expect(wrapper.text()).toContain("第 1 / 3 頁");

    await wrapper.get(".form-image-pager button:last-child").trigger("click");
    await flushPromises();
    expect(listPage).toHaveBeenLastCalledWith(20, 2, 50, "", "all", "all");

    await wrapper.get(".page-size-inline select").setValue("100");
    await flushPromises();
    expect(listPage).toHaveBeenLastCalledWith(20, 1, 100, "", "all", "all");
    expect(wrapper.text()).toContain("第 1 / 2 頁");
  });

  it("uses a selected-row inspector with image preview in Workbench UI", async () => {
    selectedCustomerId.value = 20;
    Object.defineProperty(URL, "revokeObjectURL", { configurable: true, value: vi.fn() });
    vi.spyOn(api, "listFixturesPage").mockResolvedValue({
      items: [
        { ...fixture, has_image: true },
        { ...fixture, id: 2, code: "FX-002", name: "Fixture 2", has_image: false }
      ],
      page: 1,
      page_size: 50,
      total: 2
    });
    vi.spyOn(apiModule, "fetchFixtureImageObjectUrl").mockResolvedValue("blob:fx-001");
    const toolPanel = document.createElement("div");
    toolPanel.id = "workbench-management-tools";
    document.body.appendChild(toolPanel);

    const wrapper = mount(FormImageMaintenance, {
      attachTo: document.body,
      props: { workbenchLayout: true },
      global: { stubs: { FixtureImageDialog: true } }
    });
    await flushPromises();

    expect(wrapper.findAll("thead th")).toHaveLength(4);
    expect(wrapper.get("tbody tr.workbench-image-row").classes()).toContain("selected");
    expect(toolPanel.textContent).toContain("SELECTED FIXTURE");
    expect(toolPanel.textContent).toContain("FX-001");
    expect(toolPanel.querySelector("img")?.getAttribute("src")).toBe("blob:fx-001");

    await wrapper.findAll("tbody tr.workbench-image-row")[1]!.trigger("click");
    await flushPromises();
    expect(toolPanel.textContent).toContain("FX-002");
    expect(toolPanel.textContent).toContain("尚無圖片");
    expect(toolPanel.querySelector("img")).toBeNull();

    wrapper.unmount();
    toolPanel.remove();
    delete (URL as unknown as { revokeObjectURL?: (value: string) => void }).revokeObjectURL;
  });
});
