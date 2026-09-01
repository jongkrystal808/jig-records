// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import AppTopbar from "./AppTopbar.vue";

const baseProps = {
  authDisplayName: "System Admin",
  canOperateInventory: true,
  selectedCustomerCode: "MOXA",
  customers: [{ id: 1, code: "MOXA", name: "Moxa", is_active: true, assigned_user_ids: [] }],
  selectedCustomerId: 1,
  todayReceiptQty: 0,
  todayReturnQty: 0,
  lowStockCount: 0,
  recentReceiptEntries: [],
  recentReturnEntries: [],
  lowStockPreviewEntries: [],
  hasMoreLowStockEntries: false,
  menuEntries: [],
  moreMenuOpen: false,
  formatHoverDate: (value: string) => value
};

describe("AppTopbar compact desktop actions", () => {
  it("keeps menu, current customer, and inventory action in the compact shell", () => {
    const wrapper = mount(AppTopbar, {
      props: baseProps,
      global: {
        stubs: {
          RouterLink: { template: '<a><slot /></a>' }
        }
      }
    });

    expect(wrapper.get(".mobile-trigger").text()).toContain("選單");
    expect(wrapper.get(".mobile-customer").text()).toBe("MOXA");
    expect(wrapper.get("[data-tour='inventory-entry-trigger'] .compact-inventory-label").text()).toBe("收／退料");
    expect(wrapper.get("[data-tour='search-onboarding-entry']").text()).toBe("Modern UI 教學");
    expect(wrapper.findAll(".secondary-primary-action")).toHaveLength(2);
  });

  it("keeps the system UI switcher in layout flow before the user actions", () => {
    const wrapper = mount(AppTopbar, {
      props: baseProps,
      slots: { "ui-switcher": '<div data-test="ui-switcher">Modern / Form</div>' },
      global: {
        stubs: {
          RouterLink: { template: '<a><slot /></a>' }
        }
      }
    });

    expect(wrapper.get(".topbar-ui-switcher [data-test='ui-switcher']").text()).toBe("Modern / Form");
    expect(wrapper.get(".topbar-ui-switcher").element.nextElementSibling).toBe(wrapper.get(".topbar-actions").element);
    expect(wrapper.get(".topbar-context-actions").text()).toContain("更多");
    expect(wrapper.get(".topbar-context-actions").text()).toContain("登出");
  });

  it("does not render the inventory shortcut for read-only sessions", () => {
    const wrapper = mount(AppTopbar, {
      props: { ...baseProps, canOperateInventory: false },
      global: {
        stubs: {
          RouterLink: { template: '<a><slot /></a>' }
        }
      }
    });

    expect(wrapper.find("[data-tour='inventory-entry-trigger']").exists()).toBe(false);
  });

  it("exposes the current-user password action from the account menu", async () => {
    const wrapper = mount(AppTopbar, {
      props: { ...baseProps, moreMenuOpen: true },
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } }
    });

    const passwordButton = wrapper.findAll(".more-menu-item").find((button) => button.text() === "修改密碼");
    await passwordButton!.trigger("click");
    expect(wrapper.emitted("openPassword")).toHaveLength(1);
  });

});
