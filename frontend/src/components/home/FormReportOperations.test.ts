// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "@/api";
import { authSession, selectedCustomerId } from "@/appState";
import FormReportOperations from "@/components/home/FormReportOperations.vue";
import { toasts } from "@/toastState";
import type { AppUser } from "@/types";

const managedUser: AppUser = {
  id: 7,
  username: "operator",
  email: "operator@example.com",
  display_name: "Operator",
  role: "user",
  is_active: true,
  allowed_customer_ids: [20],
  allowed_customers: [{ id: 20, code: "TEST", name: "客戶" }],
  created_at: "",
  updated_at: ""
};

function mockApi(): void {
  const fixture = {
    id: 1,
    customer_id: 20,
    responsible_user_id: null,
    code: "C-00001",
    name: "治具一",
    line_storage_location: "A1",
    department_storage_location: "D1",
    min_stock_qty: 2,
    description: null,
    is_active: true,
    has_image: false
  };
  const model = { id: 2, customer_id: 20, code: "MODEL-1", name: "機種一", is_active: true };
  const station = { id: 3, customer_id: 20, code: "T1", name: "站點一", is_active: true };
  vi.spyOn(api, "listFixtures").mockResolvedValue([fixture]);
  vi.spyOn(api, "listFixturesPage").mockResolvedValue({ items: [fixture], page: 1, page_size: 50, total: 1 });
  vi.spyOn(api, "listModels").mockResolvedValue([model]);
  vi.spyOn(api, "listModelsPage").mockResolvedValue({ items: [model], page: 1, page_size: 50, total: 1 });
  vi.spyOn(api, "listStations").mockResolvedValue([station]);
  vi.spyOn(api, "listStationsPage").mockResolvedValue({ items: [station], page: 1, page_size: 50, total: 1 });
  vi.spyOn(api, "listCustomers").mockResolvedValue([
    { id: 20, code: "TEST", name: "客戶", assigned_user_ids: [7] },
    { id: 21, code: "MOXA", name: "Moxa", assigned_user_ids: [] }
  ]);
  vi.spyOn(api, "listCustomersPage").mockResolvedValue({ items: [
    { id: 20, code: "TEST", name: "客戶", assigned_user_ids: [7] },
    { id: 21, code: "MOXA", name: "Moxa", assigned_user_ids: [] }
  ], page: 1, page_size: 50, total: 2 });
  vi.spyOn(api, "listUsers").mockResolvedValue([managedUser]);
  vi.spyOn(api, "listUsersPage").mockResolvedValue({ items: [managedUser], page: 1, page_size: 50, total: 1 });
  vi.spyOn(api, "listStock").mockResolvedValue([]);
  const requirement = {
    id: 4,
    model_id: 2,
    model_code: "MODEL-1",
    station_id: 3,
    station_code: "T1",
    fixture_id: 1,
    fixture_code: "C-00001",
    fixture_name: "治具一",
    required_qty: 1,
    stock_qty: 4
  };
  vi.spyOn(api, "listFixtureRequirements").mockResolvedValue([requirement]);
  vi.spyOn(api, "listFixtureRequirementsPage").mockResolvedValue({ items: [requirement], page: 1, page_size: 50, total: 1 });
  vi.spyOn(api, "listModelStations").mockResolvedValue([{ id: 5, model_id: 2, station_id: 3 }]);
  vi.spyOn(api, "listModelStationsPage").mockResolvedValue({ items: [{ id: 5, model_id: 2, station_id: 3, model_code: "MODEL-1", model_name: "機種一", station_code: "T1", station_name: "站點一" }], page: 1, page_size: 50, total: 1 });
  vi.spyOn(api, "listTransactionOverviewPage").mockResolvedValue({
    items: [{
      id: 6,
      transaction_type: "receipt",
      transaction_no: "TX-1",
      occurred_at: "2026-08-06T08:00:00",
      created_by: "Admin",
      fixture_id: 1,
      fixture_code: "C-00001",
      fixture_name: "治具一",
      ownership_type: "customer_supplied",
      identifier: "2608",
      quantity: 1,
      note: "這是一段超過二十四個字元並且需要在平板表格中點擊後完整展開的測試備註"
    }],
    page: 1,
    page_size: 50,
    total: 1
  });
}

afterEach(() => {
  vi.restoreAllMocks();
  authSession.value = null;
  selectedCustomerId.value = null;
  toasts.value = [];
});

describe("FormReportOperations", () => {
  it("loads production result pages without preloading option masters", async () => {
    mockApi();
    authSession.value = {
      mode: "user",
      user: { ...managedUser, id: 1, username: "admin", display_name: "Admin", role: "admin" },
      display_name: "Admin",
      token: "test-token",
      role: "admin"
    };
    selectedCustomerId.value = 20;

    const wrapper = mount(FormReportOperations, { props: { mode: "production" } });
    await flushPromises();

    expect(api.listFixtureRequirementsPage).toHaveBeenCalledWith(20, 1, 50, null, null, "");
    expect(api.listFixturesPage).not.toHaveBeenCalled();
    expect(api.listModelsPage).not.toHaveBeenCalled();
    expect(api.listStationsPage).not.toHaveBeenCalled();

    await wrapper.get("[data-tour='form-production-add-row']").trigger("click");
    await wrapper.get("input[aria-label='選擇治具']").trigger("focus");
    await new Promise((resolve) => window.setTimeout(resolve, 300));
    await flushPromises();
    expect(api.listFixturesPage).toHaveBeenCalledWith(20, 1, 20, "", "active");

    wrapper.unmount();
  });

  it("keeps one filter-and-table frame while changing fields by mode", async () => {
    mockApi();
    window.scrollTo = vi.fn();
    authSession.value = {
      mode: "user",
      user: {
        id: 1,
        username: "admin",
        email: null,
        display_name: "Admin",
        role: "admin",
        is_active: true,
        allowed_customer_ids: [20],
        created_at: "",
        updated_at: ""
      },
      display_name: "Admin",
      token: "test-token",
      role: "admin"
    };
    selectedCustomerId.value = 20;

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/search", component: { template: "<div />" } },
        { path: "/master/fixtures", component: { template: "<div />" } }
      ]
    });
    await router.push("/search");
    await router.isReady();
    const wrapper = mount(FormReportOperations, {
      props: { mode: "master" },
      global: { plugins: [router], stubs: { teleport: true } }
    });
    await flushPromises();

    expect(wrapper.find("[data-form-operation-domain='master']").exists()).toBe(true);
    expect(wrapper.find("[data-form-operation-domain='production']").exists()).toBe(false);
    expect(wrapper.findAll(".filter-panel")).toHaveLength(1);
    expect(wrapper.findAll(".report-section")).toHaveLength(1);
    expect(wrapper.text()).toContain("治具編號");
    expect(wrapper.text()).toContain("匯出篩選結果");
    expect(wrapper.find("[data-tour='form-master-view-selector']").exists()).toBe(true);
    expect(wrapper.find("[data-tour='form-master-toolbar']").exists()).toBe(true);
    expect(wrapper.find("[data-tour='form-master-fixture-table']").exists()).toBe(true);

    await wrapper.get(".form-operation-toolbar-actions .primary-btn").trigger("click");
    expect(wrapper.find(".editing-row input").exists()).toBe(true);

    await wrapper.setProps({ mode: "production" });
    await flushPromises();
    expect(wrapper.find("[data-form-operation-domain='master']").exists()).toBe(false);
    expect(wrapper.find("[data-form-operation-domain='production']").exists()).toBe(true);
    expect(wrapper.findAll(".filter-panel")).toHaveLength(1);
    expect(wrapper.findAll(".report-section")).toHaveLength(1);
    expect(wrapper.text()).toContain("每站需求");
    expect(wrapper.text()).toContain("匯出篩選結果");
    expect(wrapper.get("[data-tour='form-production-paste-import']").text()).toBe("貼上匯入");
    await wrapper.get("[data-tour='form-production-paste-import']").trigger("click");
    expect(wrapper.text()).toContain("貼上匯入治具需求");
    await wrapper.get("[data-tour='form-production-paste-modal'] .form-paste-head .outline-btn").trigger("click");

    await wrapper.setProps({ mode: "transactions" });
    await flushPromises();
    expect(wrapper.find("[data-form-operation-domain='production']").exists()).toBe(false);
    expect(wrapper.find("[data-form-operation-domain='transactions']").exists()).toBe(true);
    expect(wrapper.findAll(".filter-panel")).toHaveLength(1);
    expect(wrapper.findAll(".report-section")).toHaveLength(1);
    expect(wrapper.text()).toContain("datecode/編號");
    expect(wrapper.text()).toContain("TX-1");
    expect(wrapper.text()).toContain("匯出篩選結果");
    expect(wrapper.get(".report-note-toggle").attributes("aria-expanded")).toBe("false");
    await wrapper.get(".report-note-toggle").trigger("click");
    expect(wrapper.get(".report-note-toggle").attributes("aria-expanded")).toBe("true");

    await wrapper.findAll<HTMLInputElement>("[aria-label='類型複選'] input[type='checkbox']")[1].setValue(true);
    await wrapper.get(".filter-panel-title .primary-btn").trigger("click");
    await flushPromises();
    expect(wrapper.get(".applied-filter-summary").text()).toContain("已套用：");
    expect(wrapper.get(".applied-filter-summary").text()).toContain("退料");
    expect(wrapper.get(".applied-filter-summary").text()).toContain("共 1 筆");

    wrapper.unmount();
  });

  it("shows user scope summaries but sends permission editing to complete maintenance", async () => {
    mockApi();
    authSession.value = {
      mode: "user",
      user: { ...managedUser, id: 1, username: "admin", display_name: "Super Admin", role: "super_admin" },
      display_name: "Super Admin",
      token: "test-token",
      role: "super_admin"
    };
    selectedCustomerId.value = 20;
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/search", component: { template: "<div />" } },
        { path: "/master/users", component: { template: "<div />" } }
      ]
    });
    await router.push("/search");
    await router.isReady();

    const wrapper = mount(FormReportOperations, {
      props: { mode: "master", requestedMasterView: "user" },
      global: { plugins: [router] }
    });
    await flushPromises();

    expect(wrapper.text()).toContain("可存取客戶");
    expect(wrapper.text()).toContain("TEST－客戶");
    expect(wrapper.find("[data-tour='form-master-add-row']").exists()).toBe(false);
    await wrapper.get("tbody .text-button").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe("/master/users");
    expect(router.currentRoute.value.query).toMatchObject({ ui_surface: "modern", user_id: "7" });
    wrapper.unmount();
  });

  it("keeps permanent deletion in complete maintenance instead of Form UI", async () => {
    mockApi();
    authSession.value = {
      mode: "user",
      user: { ...managedUser, id: 1, username: "admin", display_name: "Admin", role: "admin" },
      display_name: "Admin",
      token: "test-token",
      role: "admin"
    };
    selectedCustomerId.value = 20;
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/search", component: { template: "<div />" } },
        { path: "/master/fixtures", component: { template: "<div />" } }
      ]
    });
    await router.push("/search");
    await router.isReady();

    const wrapper = mount(FormReportOperations, {
      props: { mode: "master", requestedMasterView: "fixture" },
      global: { plugins: [router] }
    });
    await flushPromises();

    expect(wrapper.find(".danger-text-button").exists()).toBe(false);
    await wrapper.get("[data-tour='form-master-open-full']").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.path).toBe("/master/fixtures");
    expect(router.currentRoute.value.query.ui_surface).toBe("modern");
    wrapper.unmount();
  });
});
