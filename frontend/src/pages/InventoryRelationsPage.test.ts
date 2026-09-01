// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { afterAll, afterEach, describe, expect, it, vi } from "vitest";

import { api } from "@/api";
import { authSession, selectedCustomerId } from "@/appState";
import type { ConfigurationReportQuery } from "@/types";

import InventoryRelationsPage from "./InventoryRelationsPage.vue";

vi.mock("@/api", () => ({
  api: {},
  fetchFixtureImageObjectUrl: vi.fn()
}));

vi.mock("@/appState", async () => {
  const { ref } = await import("vue");
  return {
    authSession: ref({ role: "guest" }),
    customers: ref([]),
    selectedCustomerId: ref(null),
    requestInventoryBatchOpen: vi.fn()
  };
});

vi.mock("@/toastState", () => ({
  pushToast: vi.fn()
}));

const originalMatchMedia = window.matchMedia;
const originalScrollTo = window.scrollTo;
window.scrollTo = vi.fn();

afterEach(() => {
  window.matchMedia = originalMatchMedia;
  selectedCustomerId.value = null;
  authSession.value = { role: "guest" } as never;
  window.localStorage.clear();
  vi.clearAllMocks();
});

afterAll(() => {
  window.scrollTo = originalScrollTo;
});

describe("InventoryRelationsPage mobile filters", () => {
  it("starts collapsed with keyword, more conditions and result summary", async () => {
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: query === "(max-width: 680px)",
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn()
    }));
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/search", component: InventoryRelationsPage }]
    });
    await router.push("/search?home_mode=report");
    await router.isReady();

    const wrapper = mount(InventoryRelationsPage, {
      global: {
        plugins: [router]
      }
    });

    expect(wrapper.find(".filter-panel").classes()).toContain("collapsed");
    expect(wrapper.find(".mobile-keyword-filter").exists()).toBe(true);
    expect(wrapper.find('[aria-label="快速篩選"]').exists()).toBe(false);
    expect(wrapper.find(".report-quick-summary").exists()).toBe(false);
    expect(wrapper.find(".mobile-filter-summary-actions").text()).toContain("更多條件");
    expect(wrapper.find(".mobile-filter-result").text()).toContain("0 筆結果");
    const fixtureStatus = wrapper.get('[aria-label="治具狀態複選"]');
    expect(fixtureStatus.findAll<HTMLInputElement>('input[type="checkbox"]')[0].element.checked).toBe(true);
    expect(fixtureStatus.text()).toContain("已啟用");
    expect(fixtureStatus.text()).toContain("已停用");
    expect(fixtureStatus.text()).toContain("清除");

    wrapper.unmount();
  });

  it("uses standard all-value filters without a primary report switcher", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/search", component: InventoryRelationsPage }]
    });
    await router.push("/search?home_mode=report");
    await router.isReady();

    const wrapper = mount(InventoryRelationsPage, {
      global: {
        plugins: [router]
      }
    });
    const fixtureFilter = wrapper.find<HTMLSelectElement>('select[aria-label="治具篩選"]');
    const modelFilter = wrapper.find<HTMLSelectElement>('select[aria-label="機種篩選"]');
    const stationFilter = wrapper.find<HTMLSelectElement>('select[aria-label="站點篩選"]');

    expect(wrapper.find(".report-basis-switcher").exists()).toBe(false);
    expect(fixtureFilter.text()).toContain("全部治具");
    expect(modelFilter.text()).toContain("全部機種");
    expect(stationFilter.text()).toContain("全部站點");
    expect(fixtureFilter.element.value).toBe("");
    expect(modelFilter.element.value).toBe("");
    expect(stationFilter.element.value).toBe("");
    expect(router.currentRoute.value.query.basis).toBeUndefined();

    wrapper.unmount();
  });

  it("renders the Form workspace switcher between filters and results", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/search", component: InventoryRelationsPage }]
    });
    await router.push("/search?home_mode=report");
    await router.isReady();

    const wrapper = mount(InventoryRelationsPage, {
      slots: {
        "between-filter-and-results": '<nav data-test="workspace-switcher">切換功能</nav>'
      },
      global: { plugins: [router] }
    });
    const filter = wrapper.get(".filter-panel").element;
    const switcher = wrapper.get('[data-test="workspace-switcher"]').element;
    const results = wrapper.get(".report-section").element;

    expect(filter.compareDocumentPosition(switcher) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(switcher.compareDocumentPosition(results) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();

    wrapper.unmount();
  });

  it("automatically collapses columns without data after the report is filtered", async () => {
    selectedCustomerId.value = 1;
    const getConfigurationReport = vi.fn(async (query: ConfigurationReportQuery) => {
      const isModelFiltered = query.model_id === 7;
      return {
        items: [
          {
            key: isModelFiltered ? "model-7" : "fixture-5",
            customer_code: "MOXA",
            fixture_id: isModelFiltered ? 0 : 5,
            fixture_code: isModelFiltered ? "" : "FX-005",
            fixture_name: isModelFiltered ? "" : "治具五",
            stock_qty: isModelFiltered ? null : 3,
            customer_supplied_qty: isModelFiltered ? null : 3,
            self_purchased_qty: isModelFiltered ? null : 0,
            min_stock_qty: isModelFiltered ? null : 1,
            water_status: isModelFiltered ? "na" : "normal",
            line_storage: "",
            department_storage: "",
            model_id: isModelFiltered ? 7 : 0,
            model_code: isModelFiltered ? "MODEL-7" : "",
            station_id: 0,
            station_code: "",
            station_name: "",
            required_qty: null,
            max_open_station_count: null,
            configuration_status: "configured"
          }
        ],
        page: 1,
        page_size: 50,
        total: 1,
        fixture_count: isModelFiltered ? 0 : 1,
        attention_fixture_count: 0,
        missing_configuration_count: 0,
        total_stock_qty: isModelFiltered ? 0 : 3,
        customer_supplied_qty: isModelFiltered ? 0 : 3,
        self_purchased_qty: 0,
        populated_columns: isModelFiltered
          ? ["index", "customer", "modelCode", "configurationStatus"]
          : [
              "index",
              "customer",
              "fixtureCode",
              "fixtureName",
              "stockQty",
              "customerSuppliedQty",
              "selfPurchasedQty",
              "minStockQty",
              "waterStatus",
              "configurationStatus"
            ],
        transaction_details: [],
        transaction_detail_count: 0
      };
    });
    Object.assign(api, {
      getConfigurationReport,
      getConfigurationReportOptions: vi.fn().mockResolvedValue({
        fixtures: [],
        models: [{ id: 7, code: "MODEL-7", name: "機種七" }],
        stations: [],
        water_statuses: []
      })
    });
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/search", component: InventoryRelationsPage }]
    });
    await router.push("/search?home_mode=report");
    await router.isReady();

    const wrapper = mount(InventoryRelationsPage, {
      global: { plugins: [router] }
    });
    await flushPromises();

    expect(
      wrapper.findAll(".desktop-report-table thead th").map((header) => header.text())
    ).toEqual([
      "序號",
      "客戶",
      "治具代碼",
      "治具名稱",
      "總庫存",
      "客供庫存",
      "自購庫存",
      "最低水位",
      "水位狀態",
      "配置狀態"
    ]);
    expect(wrapper.find(".column-picker-trigger").text()).toContain("10 / 16");

    await wrapper.find<HTMLSelectElement>('select[aria-label="機種篩選"]').setValue("7");
    await flushPromises();
    await wrapper.find(".primary-button").trigger("click");
    await flushPromises();

    expect(
      wrapper.findAll(".desktop-report-table thead th").map((header) => header.text())
    ).toEqual(["序號", "客戶", "機種", "配置狀態"]);
    expect(wrapper.find(".column-picker-trigger").text()).toContain("4 / 16");
    expect(getConfigurationReport).toHaveBeenLastCalledWith(
      expect.objectContaining({ model_id: 7 })
    );
    expect(getConfigurationReport.mock.lastCall?.[0]).not.toHaveProperty("report_dimension");

    await wrapper.find(".column-picker-trigger").trigger("click");
    expect(wrapper.findAll(".column-picker-options label.auto-hidden")).toHaveLength(12);
    expect(wrapper.find(".auto-hidden-note").text()).toContain(
      "已自動收合 12 個無資料欄位"
    );

    wrapper.unmount();
  });

  it("uses 20 or 50 rows per page on mobile and keeps the result context together", async () => {
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: query === "(max-width: 680px)",
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn()
    }));
    selectedCustomerId.value = 1;
    const getConfigurationReport = vi.fn().mockResolvedValue({
      items: [],
      page: 1,
      page_size: 20,
      total: 28,
      fixture_count: 28,
      attention_fixture_count: 0,
      missing_configuration_count: 0,
      total_stock_qty: 0,
      customer_supplied_qty: 0,
      self_purchased_qty: 0,
      populated_columns: [],
      transaction_details: [],
      transaction_detail_count: 0
    });
    Object.assign(api, {
      getConfigurationReport,
      getConfigurationReportOptions: vi.fn().mockResolvedValue({
        fixtures: [],
        models: [],
        stations: [],
        water_statuses: []
      })
    });
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/search", component: InventoryRelationsPage }]
    });
    await router.push("/search?home_mode=report");
    await router.isReady();

    const wrapper = mount(InventoryRelationsPage, {
      global: { plugins: [router] }
    });
    await flushPromises();

    const pageSizeSelect = wrapper.find<HTMLSelectElement>('select[aria-label="每頁顯示筆數"]');
    expect(pageSizeSelect.element.value).toBe("20");
    expect(pageSizeSelect.findAll("option").map((option) => option.text())).toEqual([
      "20 筆",
      "50 筆"
    ]);
    expect(getConfigurationReport).toHaveBeenLastCalledWith(
      expect.objectContaining({ page_size: 20 })
    );
    expect(wrapper.find(".report-sticky-toolbar .report-summary").exists()).toBe(true);
    expect(wrapper.find(".report-sticky-toolbar .applied-filter-strip").exists()).toBe(true);

    await pageSizeSelect.setValue("50");
    await flushPromises();
    expect(getConfigurationReport).toHaveBeenLastCalledWith(
      expect.objectContaining({ page_size: 50 })
    );

    wrapper.unmount();
  });
});
