// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { authSession, customers, selectedCustomerId } from "@/appState";
import WorkbenchManagementSurface from "./WorkbenchManagementSurface.vue";

const routes = [
  "/search",
  "/inventory/overview",
  "/production/requirements",
  "/production/mapping",
  "/master/fixtures",
  "/master/models",
  "/master/stations",
  "/master/customers",
  "/master/users",
  "/master/images",
  "/master/ledger",
  "/master/quality"
].map((path) => ({ path, component: { template: "<div />" } }));

async function mountAt(path: string, props: Record<string, unknown> = {}) {
  const router = createRouter({ history: createMemoryHistory(), routes });
  await router.push(path);
  await router.isReady();

  const wrapper = mount(WorkbenchManagementSurface, {
    props,
    global: {
      plugins: [router],
      stubs: {
        FormReportOperations: {
          props: ["mode", "requestedProductionView", "requestedMasterView", "workbenchLayout"],
          template: `
            <div
              data-testid="management-operations"
              :data-mode="mode"
              :data-production-view="requestedProductionView"
              :data-master-view="requestedMasterView"
            />
          `
        },
        WorkbenchAdminOperations: {
          props: ["mode"],
          template: '<div data-testid="workbench-admin-operations" :data-mode="mode" />'
        },
        FormImageMaintenance: {
          props: ["workbenchLayout"],
          template: '<div data-testid="workbench-image-maintenance" />'
        }
      }
    }
  });
  await flushPromises();
  return { router, wrapper };
}

describe("WorkbenchManagementSurface", () => {
  beforeEach(() => {
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: vi.fn().mockReturnValue({ matches: false })
    });
    authSession.value = {
      mode: "user",
      user: {
        id: 7,
        username: "operator",
        email: null,
        display_name: "Operator",
        role: "user",
        is_active: true,
        allowed_customer_ids: [1],
        created_at: "2026-08-25",
        updated_at: "2026-08-25"
      },
      display_name: "Operator",
      token: "user-token",
      role: "user"
    };
    customers.value = [{ id: 1, code: "MOXA", name: "Moxa", assigned_user_ids: [7] }];
    selectedCustomerId.value = 1;
  });

  it("keeps the three management modules inside the Workbench shell", async () => {
    const { router, wrapper } = await mountAt("/inventory/overview?ui_surface=workbench");
    const operations = wrapper.get('[data-testid="management-operations"]');

    expect(wrapper.find('[data-workbench-area="management"]').exists()).toBe(true);
    expect(wrapper.get(".workbench-management-nav").text()).toContain("收退料總檢視");
    expect(operations.attributes("data-mode")).toBe("transactions");

    const productionButton = wrapper.findAll(".workbench-management-module-list button")
      .find((button) => button.text().includes("產能設定"));
    await productionButton!.trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe("/production/requirements");
    expect(router.currentRoute.value.query.ui_surface).toBe("workbench");
    expect(router.currentRoute.value.query.customer).toBe("1");
    expect(wrapper.get('[data-testid="management-operations"]').attributes("data-mode")).toBe("production");
    expect(wrapper.get('[data-testid="management-operations"]').attributes("data-production-view")).toBe("requirements");

    const masterButton = wrapper.findAll(".workbench-management-module-list button")
      .find((button) => button.text().includes("資料維護"));
    await masterButton!.trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe("/master/fixtures");
    expect(wrapper.get('[data-testid="management-operations"]').attributes("data-mode")).toBe("master");
    expect(wrapper.get('[data-testid="management-operations"]').attributes("data-master-view")).toBe("fixture");
    expect(wrapper.text()).toContain("返回現場工作台");
  });

  it("separates admin reports from Super Admin account management", async () => {
    const userView = await mountAt("/master/fixtures?ui_surface=workbench");
    expect(userView.wrapper.get(".workbench-management-subnav").text()).not.toContain("客戶");
    expect(userView.wrapper.get(".workbench-management-subnav").text()).not.toContain("使用者");
    userView.wrapper.unmount();

    authSession.value = {
      ...authSession.value!,
      role: "admin",
      user: { ...authSession.value!.user!, role: "admin" }
    };
    const adminView = await mountAt("/master/fixtures?ui_surface=workbench");

    expect(adminView.wrapper.get(".workbench-management-subnav").text()).not.toContain("客戶");
    expect(adminView.wrapper.get(".workbench-management-subnav").text()).not.toContain("使用者");
    expect(adminView.wrapper.get(".workbench-management-module-list").text()).toContain("收退料帳目管理");
    expect(adminView.wrapper.get(".workbench-management-module-list").text()).toContain("治具資料品質");

    const ledgerButton = adminView.wrapper.findAll(".workbench-management-module-list button")
      .find((button) => button.text().includes("收退料帳目管理"));
    await ledgerButton!.trigger("click");
    await flushPromises();
    expect(adminView.router.currentRoute.value.path).toBe("/master/ledger");
    expect(adminView.wrapper.get('[data-testid="workbench-admin-operations"]').attributes("data-mode")).toBe("ledger");
    adminView.wrapper.unmount();

    authSession.value = {
      ...authSession.value!,
      role: "super_admin",
      user: { ...authSession.value!.user!, role: "super_admin" }
    };
    const superAdminView = await mountAt("/master/fixtures?ui_surface=workbench");
    expect(superAdminView.wrapper.get(".workbench-management-subnav").text()).toContain("客戶");
    expect(superAdminView.wrapper.get(".workbench-management-subnav").text()).toContain("使用者");
  });

  it("does not expose protected management modules to guests", async () => {
    authSession.value = {
      mode: "guest",
      user: null,
      display_name: "訪客",
      token: "guest-token",
      role: "guest"
    };
    const { wrapper } = await mountAt("/inventory/overview?ui_surface=workbench&customer=1");
    const navigation = wrapper.get(".workbench-management-module-list");

    expect(navigation.text()).toContain("收退料總檢視");
    expect(navigation.text()).not.toContain("產能設定");
    expect(navigation.text()).not.toContain("資料維護");
    expect(wrapper.get(".workbench-management-access-note").text()).toContain("需要登入");
  });

  it("reserves the right panel for filters and editors and includes image maintenance", async () => {
    const { router, wrapper } = await mountAt("/master/fixtures?ui_surface=workbench&customer=1");

    expect(wrapper.find("#workbench-management-tools").exists()).toBe(true);
    expect(wrapper.get(".workbench-management-detail").text()).toContain("篩選與編輯");
    expect(wrapper.get(".workbench-management-detail").text()).not.toContain("操作角色");
    expect(wrapper.get(".workbench-management-subnav").text()).toContain("圖片");

    const imageButton = wrapper.findAll(".workbench-management-subnav button")
      .find((button) => button.text().includes("圖片"));
    await imageButton!.trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe("/master/images");
    expect(wrapper.find('[data-testid="workbench-image-maintenance"]').exists()).toBe(true);
  });

  it("collapses and restores the right-side filter controls", async () => {
    const { wrapper } = await mountAt("/inventory/overview?ui_surface=workbench&customer=1");
    const toggle = wrapper.get(".workbench-filter-toggle");

    expect(toggle.text()).toBe("收合篩選");
    expect(toggle.attributes("aria-expanded")).toBe("true");
    expect(wrapper.get(".workbench-management-operation-shell").classes()).not.toContain("filters-collapsed");

    await toggle.trigger("click");

    expect(toggle.text()).toBe("展開篩選");
    expect(toggle.attributes("aria-expanded")).toBe("false");
    expect(wrapper.get(".workbench-management-operation-shell").classes()).toContain("filters-collapsed");
  });

  it("supports the Workspace transaction-only overview without a duplicate header", async () => {
    const { router, wrapper } = await mountAt(
      "/inventory/overview?ui_surface=workspace&customer=1",
      { surface: "workspace", showHeader: false, transactionsOnly: true }
    );

    expect(wrapper.find(".workbench-header").exists()).toBe(false);
    expect(wrapper.find(".workbench-management-module-list").exists()).toBe(false);
    expect(wrapper.find('[data-workbench-area="floor"]').exists()).toBe(true);
    expect(wrapper.attributes("aria-label")).toBe("現場工作台收退料總檢視");
    expect(wrapper.get(".workbench-management-nav").text()).toContain("現場工作台");
    expect(wrapper.find(".workbench-return-floor").exists()).toBe(false);
    expect(wrapper.get(".workbench-mode-tabs").text()).toContain("收料／退料");
    expect(wrapper.get(".workbench-mode-tabs").text()).toContain("查詢治具");
    expect(wrapper.get(".workbench-mode-tabs").text()).toContain("查詢機種");
    expect(wrapper.get(".workbench-mode-tabs").text()).toContain("收／退料總檢視");
    expect(wrapper.get('[data-testid="management-operations"]').attributes("data-mode")).toBe("transactions");

    const fixtureTab = wrapper.findAll(".workbench-mode-tabs button")
      .find((button) => button.text().includes("查詢治具"));
    await fixtureTab!.trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.path).toBe("/search");
    expect(router.currentRoute.value.query.ui_surface).toBe("workspace");
    expect(router.currentRoute.value.query.workbench_mode).toBe("fixture");
  });
});
