// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import MasterToolbar from "./MasterToolbar.vue";

afterEach(() => vi.restoreAllMocks());

function mountToolbar() {
  return mount(MasterToolbar, {
    props: {
      activeTab: "fixture",
      canManageCustomers: true,
      canManageUsers: true,
      canManageLedger: true,
      canManageQuality: true,
      loading: false,
      hasSelectedCustomer: true,
      imageBatchUploading: false,
      imageBatchFileCount: 0
    }
  });
}

describe("MasterToolbar", () => {
  it("keeps tab navigation and low-frequency actions inside one component", async () => {
    const wrapper = mountToolbar();

    expect(wrapper.findAll(".desktop-tab-bar .tab-btn")).toHaveLength(7);
    await wrapper.find('[data-tour="master-tab-ledger"]').trigger("click");
    expect(wrapper.emitted("switchTab")?.[0]).toEqual(["ledger"]);

    await wrapper.find(".more-menu-trigger").trigger("click");
    expect(wrapper.find(".more-menu-panel").exists()).toBe(true);
    expect(wrapper.find(".more-menu-panel").text()).toContain("匯入 CSV");
    wrapper.unmount();
  });

  it("owns the image picker while forwarding the selected files", async () => {
    const wrapper = mountToolbar();
    const input = wrapper.find<HTMLInputElement>('input[accept^="image/"]');
    const file = new File(["fixture"], "FX-001.png", { type: "image/png" });
    Object.defineProperty(input.element, "files", { value: [file], configurable: true });

    await input.trigger("change");
    expect(wrapper.emitted("imageFilesChange")?.[0]?.[0]).toBeInstanceOf(Event);

    Object.defineProperty(input.element, "value", {
      value: "C:\\fakepath\\FX-001.png",
      writable: true,
      configurable: true
    });
    (wrapper.vm as unknown as { resetImageInput: () => void }).resetImageInput();
    expect(input.element.value).toBe("");
    wrapper.unmount();
  });

  it("keeps ledger and quality tabs visible when account management is unavailable", () => {
    const wrapper = mount(MasterToolbar, {
      props: {
        activeTab: "ledger",
        canManageCustomers: false,
        canManageUsers: false,
        canManageLedger: true,
        canManageQuality: true,
        loading: false,
        hasSelectedCustomer: true,
        imageBatchUploading: false,
        imageBatchFileCount: 0
      }
    });

    expect(wrapper.find('[data-tour="master-tab-customer"]').exists()).toBe(false);
    expect(wrapper.find('[data-tour="master-tab-user"]').exists()).toBe(false);
    expect(wrapper.find('[data-tour="master-tab-ledger"]').exists()).toBe(true);
    expect(wrapper.find('[data-tour="master-tab-quality"]').exists()).toBe(true);
  });
});
