// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { api } from "@/api";
import { authSession, customers, selectedCustomerId } from "@/appState";
import WorkbenchUiSurface from "./WorkbenchUiSurface.vue";

vi.mock("@/api", () => ({
  api: {
    listFixtures: vi.fn(),
    listModels: vi.fn(),
    listCustomerUsers: vi.fn(),
    listTransactionOverviewPage: vi.fn(),
    listModelShortcutPreferences: vi.fn(),
    recordModelShortcutQuery: vi.fn(),
    setModelShortcutPin: vi.fn(),
    globalSearch: vi.fn(),
    getFixtureSearchContext: vi.fn(),
    getModelSearchContext: vi.fn(),
    updateFixture: vi.fn(),
    updateModel: vi.fn(),
    createReceiptWithOptions: vi.fn(),
    createReturnWithOptions: vi.fn()
  },
  fetchFixtureImageObjectUrl: vi.fn()
}));

vi.mock("@/toastState", () => ({ pushToast: vi.fn() }));
vi.mock("@/confirmState", () => ({ requestConfirmation: vi.fn().mockResolvedValue(true) }));

describe("WorkbenchUiSurface", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
    authSession.value = {
      mode: "guest",
      user: null,
      display_name: "訪客",
      token: "guest-token",
      role: "guest"
    };
    customers.value = [{ id: 1, code: "TEST", name: "Test", assigned_user_ids: [] }];
    selectedCustomerId.value = 1;
    vi.mocked(api.listFixtures).mockResolvedValue([{
      id: 11,
      customer_id: 1,
      responsible_user_id: null,
      code: "L-00143",
      name: "線材治具",
      line_storage_location: "A-01",
      department_storage_location: "D-02",
      min_stock_qty: 2,
      description: null,
      is_active: true,
      has_image: false
    }]);
    vi.mocked(api.listModels).mockResolvedValue([]);
    vi.mocked(api.listCustomerUsers).mockResolvedValue([]);
    vi.mocked(api.listTransactionOverviewPage).mockResolvedValue({ items: [], page: 1, page_size: 50, total: 0 });
    vi.mocked(api.listModelShortcutPreferences).mockResolvedValue([]);
    vi.mocked(api.globalSearch).mockResolvedValue({
      items: [{
        entity_type: "fixture",
        title: "L-00143",
        subtitle: "線材治具",
        reference_id: 11,
        is_active: true,
        stock_qty: 5,
        stock_status: "normal"
      }],
      page: 1,
      page_size: 20,
      total: 1,
      has_more: false
    });
    vi.mocked(api.getFixtureSearchContext).mockResolvedValue({
      fixture: {
        id: 11,
        customer_id: 1,
        responsible_user_id: null,
        code: "L-00143",
        name: "線材治具",
        line_storage_location: "A-01",
        department_storage_location: "D-02",
        min_stock_qty: 2,
        description: null,
        is_active: true,
        has_image: false
      },
      stock: {
        fixture_id: 11,
        fixture_code: "L-00143",
        fixture_name: "線材治具",
        stock_qty: 5,
        customer_supplied_qty: 3,
        self_purchased_qty: 2,
        min_stock_qty: 2,
        stock_status: "normal",
        last_transaction_at: null
      },
      identifier_rows: [{ fixture_id: 11, identifier: "2204", stock_qty: 5, customer_supplied_qty: 3, self_purchased_qty: 2 }],
      related_models: [],
      station_rows: [],
      transactions: []
    });
    vi.mocked(api.updateFixture).mockResolvedValue({
      id: 11,
      customer_id: 1,
      responsible_user_id: null,
      code: "L-00143",
      name: "線材治具",
      line_storage_location: "A-01",
      department_storage_location: "D-02",
      min_stock_qty: 2,
      description: null,
      is_active: true,
      has_image: false
    });
  });

  it("lets admin edit fixture fields directly from Workspace details", async () => {
    authSession.value = {
      mode: "user",
      user: {
        id: 7,
        username: "admin",
        email: null,
        display_name: "Admin",
        role: "admin",
        is_active: true,
        allowed_customer_ids: [1],
        created_at: "2026-08-27",
        updated_at: "2026-08-27"
      },
      display_name: "Admin",
      token: "admin-token",
      role: "admin"
    };
    vi.mocked(api.listCustomerUsers).mockResolvedValue([authSession.value.user!]);
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/search", component: { template: "<div />" } }]
    });
    await router.push("/search?ui_surface=workspace&workbench_mode=fixture&customer=1");
    await router.isReady();

    const wrapper = mount(WorkbenchUiSurface, {
      props: { surface: "workspace", showHeader: false },
      global: { plugins: [router] }
    });
    await flushPromises();
    await wrapper.get('input[placeholder="例如 L-00143"]').setValue("L-00143");
    await wrapper.get("form.workbench-query-form").trigger("submit");
    await flushPromises();

    await wrapper.get('[aria-label="編輯治具資料"]').trigger("click");
    await flushPromises();
    expect(api.listCustomerUsers).toHaveBeenCalledWith(1);
    expect(wrapper.get(".workbench-inline-editor").text()).toContain("資料維護");

    const editorInputs = wrapper.findAll(".workbench-inline-editor input");
    await editorInputs[1]!.setValue("更新後治具");
    vi.mocked(api.getFixtureSearchContext).mockResolvedValueOnce({
      fixture: {
        id: 11,
        customer_id: 1,
        responsible_user_id: null,
        code: "L-00143",
        name: "更新後治具",
        line_storage_location: "A-01",
        department_storage_location: "D-02",
        min_stock_qty: 2,
        description: null,
        is_active: true,
        has_image: false
      },
      stock: {
        fixture_id: 11,
        fixture_code: "L-00143",
        fixture_name: "更新後治具",
        stock_qty: 5,
        customer_supplied_qty: 3,
        self_purchased_qty: 2,
        min_stock_qty: 2,
        stock_status: "normal",
        last_transaction_at: null
      },
      identifier_rows: [],
      related_models: [],
      station_rows: [],
      transactions: []
    });
    await wrapper.get(".workbench-inline-editor").trigger("submit");
    await flushPromises();

    expect(api.updateFixture).toHaveBeenCalledWith(11, expect.objectContaining({
      customer_id: 1,
      code: "L-00143",
      name: "更新後治具",
      line_storage_location: "A-01",
      department_storage_location: "D-02",
      min_stock_qty: 2,
      is_active: true
    }));
    expect(wrapper.find(".workbench-inline-editor").exists()).toBe(false);
    expect(wrapper.text()).toContain("更新後治具");
  });

  it("does not expose Workspace inline editing to regular users", async () => {
    authSession.value = {
      mode: "user",
      user: {
        id: 8,
        username: "operator",
        email: null,
        display_name: "Operator",
        role: "user",
        is_active: true,
        allowed_customer_ids: [1],
        created_at: "2026-08-27",
        updated_at: "2026-08-27"
      },
      display_name: "Operator",
      token: "user-token",
      role: "user"
    };
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/search", component: { template: "<div />" } }]
    });
    await router.push("/search?ui_surface=workspace&workbench_mode=fixture&customer=1");
    await router.isReady();
    const wrapper = mount(WorkbenchUiSurface, {
      props: { surface: "workspace", showHeader: false },
      global: { plugins: [router] }
    });
    await flushPromises();
    await wrapper.get('input[placeholder="例如 L-00143"]').setValue("L-00143");
    await wrapper.get("form.workbench-query-form").trigger("submit");
    await flushPromises();

    expect(wrapper.find('[aria-label="編輯治具資料"]').exists()).toBe(false);
    expect(api.listCustomerUsers).not.toHaveBeenCalled();
  });

  it("keeps fixture search and guest receipt mode inside the three-column workbench", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/search", component: { template: "<div />" } },
        { path: "/inventory", component: { template: "<div />" } }
      ]
    });
    await router.push("/search?ui_surface=workbench&workbench_mode=fixture");
    await router.isReady();

    const wrapper = mount(WorkbenchUiSurface, { global: { plugins: [router] } });
    await flushPromises();
    await wrapper.get('input[placeholder="例如 L-00143"]').setValue("L-00143");
    await wrapper.get("form.workbench-query-form").trigger("submit");
    await flushPromises();

    expect(wrapper.text()).toContain("L-00143 · 線材治具");
    expect(wrapper.text()).toContain("5 pcs");
    expect(wrapper.text()).toContain("A-01");
    expect(router.currentRoute.value.query.fixture_search).toBe("fixture");
    expect(router.currentRoute.value.query.selected_id).toBe("11");

    await wrapper.get('[role="tab"][aria-selected="false"]').trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe("/search");
    expect(router.currentRoute.value.query.workbench_mode).toBe("transaction");
    expect(router.currentRoute.value.query.transaction_type).toBe("receipt");
    expect(router.currentRoute.value.query.customer).toBe("1");
    expect(router.currentRoute.value.query.q).toBe("L-00143");
    expect(wrapper.get(".workbench-primary").attributes("disabled")).toBeDefined();
  });

  it("separates identifier lookup and restores prior search state with browser back", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/search", component: { template: "<div />" } }]
    });
    await router.push("/search?ui_surface=workbench&workbench_mode=fixture&fixture_search=fixture&customer=1");
    await router.isReady();
    const wrapper = mount(WorkbenchUiSurface, { global: { plugins: [router] } });
    await flushPromises();

    await wrapper.get('input[placeholder="例如 L-00143"]').setValue("L-00143");
    await wrapper.get("form.workbench-query-form").trigger("submit");
    await flushPromises();

    vi.mocked(api.globalSearch).mockResolvedValue({
      items: [{
        entity_type: "fixture",
        title: "L-00143",
        subtitle: "線材治具",
        reference_id: 11,
        is_active: true,
        matched_identifier: "2204"
      }],
      page: 1,
      page_size: 20,
      total: 1,
      has_more: false
    });
    await wrapper.findAll(".workbench-search-kind button")[1].trigger("click");
    await flushPromises();
    await wrapper.get('input[placeholder*="只輸入 Datecode"]').setValue("2204");
    await wrapper.get("form.workbench-query-form").trigger("submit");
    await flushPromises();

    expect(api.globalSearch).toHaveBeenLastCalledWith({
      q: "2204",
      customerId: 1,
      entityType: "fixture",
      fixtureSearchMode: "identifier",
      pageSize: 20
    });
    expect(router.currentRoute.value.query.q).toBe("2204");
    expect(router.currentRoute.value.query.fixture_search).toBe("identifier");
    expect(router.currentRoute.value.query.selected_id).toBe("11");

    router.back();
    await flushPromises();
    expect(router.currentRoute.value.query.q).toBe("L-00143");
    expect(router.currentRoute.value.query.fixture_search).toBe("identifier");

    router.back();
    await flushPromises();
    expect(router.currentRoute.value.query.q).toBe("L-00143");
    expect(router.currentRoute.value.query.fixture_search).toBe("fixture");
    expect(wrapper.get('input[placeholder="例如 L-00143"]').element).toHaveProperty("value", "L-00143");
  });

  it("keeps a not-found query visible in the result and detail panels", async () => {
    vi.mocked(api.globalSearch).mockResolvedValue({
      items: [],
      page: 1,
      page_size: 20,
      total: 0,
      has_more: false
    });
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/search", component: { template: "<div />" } }]
    });
    await router.push("/search?ui_surface=workbench&workbench_mode=fixture&customer=1");
    await router.isReady();
    const wrapper = mount(WorkbenchUiSurface, { global: { plugins: [router] } });
    await flushPromises();
    const resultPanel = wrapper.get(".workbench-results").element as HTMLElement;
    resultPanel.getBoundingClientRect = vi.fn().mockReturnValue({
      top: 1200,
      bottom: 1600,
      left: 0,
      right: 800,
      width: 800,
      height: 400,
      x: 0,
      y: 1200,
      toJSON: () => ({})
    });
    resultPanel.scrollIntoView = vi.fn();

    await wrapper.get('input[placeholder="例如 L-00143"]').setValue("UNKNOWN");
    await wrapper.get("form.workbench-query-form").trigger("submit");
    await flushPromises();

    expect(wrapper.get('[data-workbench-empty-state="not-found"]').text()).toContain("找不到「UNKNOWN」");
    expect(wrapper.get(".workbench-clear-search").text()).toBe("清除搜尋");
    expect(wrapper.get('[data-workbench-detail-state="not-found"]').text()).toContain("查無結果");
    expect(router.currentRoute.value.query.q).toBe("UNKNOWN");
    expect(router.currentRoute.value.query.customer).toBe("1");
    expect(resultPanel.scrollIntoView).toHaveBeenCalledWith({ behavior: "smooth", block: "start" });
  });

  it("combines receipt and return in one transaction panel", async () => {
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
        created_at: "2026-08-27",
        updated_at: "2026-08-27"
      },
      display_name: "Operator",
      token: "user-token",
      role: "user"
    };
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/search", component: { template: "<div />" } },
        { path: "/inventory", component: { template: "<div />" } }
      ]
    });
    await router.push("/inventory?ui_surface=workbench&workbench_mode=transaction&transaction_type=receipt&customer=1");
    await router.isReady();
    const wrapper = mount(WorkbenchUiSurface, { global: { plugins: [router] } });
    await flushPromises();

    expect(wrapper.findAll('.workbench-mode-tabs [role="tab"]')).toHaveLength(4);
    expect(wrapper.get('.workbench-mode-tabs [aria-selected="true"]').text()).toBe("收料／退料");
    expect(wrapper.get('[role="radiogroup"]').text()).toContain("收料入庫");
    expect(wrapper.get('[role="radiogroup"]').text()).toContain("退料出庫");

    const directionButtons = wrapper.findAll('[role="radiogroup"] [role="radio"]');
    await directionButtons[1]!.trigger("click");
    await wrapper.get('input[placeholder="輸入單號"]').setValue("RET-001");
    await wrapper.get('input[placeholder="掃描或輸入治具編號"]').setValue("L-00143");
    await wrapper.get('input[placeholder="短數字會自動補至 4 碼"]').setValue("12");
    await wrapper.get("form.workbench-form").trigger("submit");
    await flushPromises();

    expect(router.currentRoute.value.query.transaction_type).toBe("return");
    expect(api.createReturnWithOptions).toHaveBeenCalled();
    expect(api.createReceiptWithOptions).not.toHaveBeenCalled();
  });

  it("uses relevant model shortcuts and identifies the model bottleneck", async () => {
    vi.mocked(api.listModels).mockResolvedValue([{
      id: 21,
      customer_id: 1,
      code: "AWK-1137C",
      name: "Wireless model",
      is_active: true
    }]);
    vi.mocked(api.globalSearch).mockResolvedValue({
      items: [{ entity_type: "model", title: "AWK-1137C", subtitle: "Wireless model", reference_id: 21, is_active: true }],
      page: 1,
      page_size: 20,
      total: 1,
      has_more: false
    });
    vi.mocked(api.getModelSearchContext).mockResolvedValue({
      model: { id: 21, customer_id: 1, code: "AWK-1137C", name: "Wireless model", is_active: true },
      query: {
        model_id: 21,
        model_code: "AWK-1137C",
        model_name: "Wireless model",
        max_open_station_count: 1,
        station_count: 1,
        fixture_type_count: 1,
        total_stock_qty: 1,
        stations: [{ station_id: 31, station_code: "T1_RF", station_name: "RF station", max_open_station_count: 1, bottleneck_fixture_code: "S-00098" }],
        station_requirements: [{
          station_id: 31,
          station_code: "T1_RF",
          fixture_id: 41,
          fixture_code: "S-00098",
          fixture_name: "RF fixture",
          required_qty: 2,
          designated_mode: true,
          designated_identifiers: ["DC-01", "SN-008"],
          stock_qty: 2,
          max_open_station_count: 1,
          stock_status: "normal"
        }],
        fixtures: []
      }
    });
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/search", component: { template: "<div />" } }]
    });
    await router.push("/search?ui_surface=workbench&workbench_mode=model&customer=1");
    await router.isReady();
    const wrapper = mount(WorkbenchUiSurface, { global: { plugins: [router] } });
    await flushPromises();

    expect(wrapper.text()).toContain("機種捷徑");
    expect(wrapper.text()).not.toContain("最近收退料治具");
    await wrapper.get('[aria-label="查詢機種 AWK-1137C Wireless model"]').trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("整機瓶頸產能");
    expect(wrapper.get(".workbench-bottleneck-callout").text()).toContain("T1_RF");
    expect(wrapper.get(".workbench-bottleneck-callout").text()).toContain("S-00098");
    expect(wrapper.get(".workbench-bottleneck-row").text()).toContain("目前瓶頸");
    expect(wrapper.get(".workbench-designated-notice").text()).toContain("只採計列出的 identifier");
    expect(wrapper.get(".workbench-designated-cell").text()).toContain("指定模式");
    expect(wrapper.get(".workbench-designated-cell").text()).toContain("DC-01、SN-008");
    expect(wrapper.text()).toContain("最近查詢");
  });

  it("opens batch receipt inside the middle workbench panel", async () => {
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
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/search", component: { template: "<div />" } },
        { path: "/inventory", component: { template: "<div />" } }
      ]
    });
    await router.push("/search?ui_surface=workbench&workbench_mode=fixture");
    await router.isReady();

    const wrapper = mount(WorkbenchUiSurface, {
      global: {
        plugins: [router],
        stubs: {
          WorkbenchBatchOperations: {
            props: ["initialMode", "showModeSwitch", "presetFixtureCode"],
            template: '<div data-testid="embedded-batch">{{ initialMode }} · {{ showModeSwitch }} · {{ presetFixtureCode }}</div>'
          }
        }
      }
    });
    await flushPromises();
    const transactionTab = wrapper.findAll('[role="tab"]').find((tab) => tab.text() === "收料／退料");
    expect(transactionTab).toBeDefined();
    await transactionTab!.trigger("click");
    await flushPromises();
    await wrapper.get(".workbench-secondary").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe("/inventory");
    expect(wrapper.get('[data-testid="embedded-batch"]').text()).toContain("receipt");
    expect(wrapper.get(".workbench-results-heading").text()).toContain("批次收退料");
    expect(wrapper.get(".workbench-results").classes()).toContain("is-batch-open");

    await wrapper.get(".workbench-panel-back").trigger("click");
    expect(wrapper.find('[data-testid="embedded-batch"]').exists()).toBe(false);
  });

  it("paginates recent work rows at fifty items and keeps operator metadata", async () => {
    const makeRows = (start: number, count: number) => Array.from({ length: count }, (_, index) => ({
      id: start + index,
      transaction_type: "receipt" as const,
      transaction_no: "RCV-99",
      occurred_at: "2026-08-25T08:00:00Z",
      created_by: "Operator A",
      fixture_id: 100 + start + index,
      fixture_code: `FX-${String(start + index).padStart(3, "0")}`,
      fixture_name: `Fixture ${start + index}`,
      ownership_type: "customer_supplied" as const,
      identifier: String(start + index).padStart(4, "0"),
      quantity: 1,
      note: null
    }));
    vi.mocked(api.listTransactionOverviewPage)
      .mockResolvedValueOnce({ items: makeRows(1, 50), page: 1, page_size: 50, total: 60 })
      .mockResolvedValueOnce({ items: makeRows(51, 10), page: 2, page_size: 50, total: 60 });
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/search", component: { template: "<div />" } },
        { path: "/inventory", component: { template: "<div />" } }
      ]
    });
    await router.push("/search?ui_surface=workbench&workbench_mode=transaction&transaction_type=receipt&customer=1");
    await router.isReady();
    const wrapper = mount(WorkbenchUiSurface, { global: { plugins: [router] } });
    await flushPromises();

    expect(wrapper.findAll(".workbench-recent-table tbody tr")).toHaveLength(50);
    expect(wrapper.get(".workbench-table-pager").text()).toContain("第 1 / 2 頁");
    expect(wrapper.text()).toContain("Operator A");
    await wrapper.findAll(".workbench-table-pager button")[1]!.trigger("click");
    await flushPromises();
    expect(wrapper.findAll(".workbench-recent-table tbody tr")).toHaveLength(10);
    expect(api.listTransactionOverviewPage).toHaveBeenLastCalledWith(2, 50, 1);
  });

  it("syncs signed-in model pins through the preference API", async () => {
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
    vi.mocked(api.listModels).mockResolvedValue([{
      id: 21,
      customer_id: 1,
      code: "AWK-1137C",
      name: "Wireless model",
      is_active: true
    }]);
    vi.mocked(api.listModelShortcutPreferences).mockResolvedValue([{
      model_id: 21,
      model_code: "AWK-1137C",
      query_count: 3,
      last_queried_at: "2026-08-25T08:00:00Z",
      pinned: false
    }]);
    vi.mocked(api.setModelShortcutPin).mockResolvedValue({
      model_id: 21,
      model_code: "AWK-1137C",
      query_count: 3,
      last_queried_at: "2026-08-25T08:00:00Z",
      pinned: true
    });
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/search", component: { template: "<div />" } }]
    });
    await router.push("/search?ui_surface=workbench&workbench_mode=model&customer=1");
    await router.isReady();
    const wrapper = mount(WorkbenchUiSurface, { global: { plugins: [router] } });
    await flushPromises();

    await wrapper.get('[aria-label="釘選 AWK-1137C"]').trigger("click");
    await flushPromises();

    expect(api.listModelShortcutPreferences).toHaveBeenCalledWith(1);
    expect(api.setModelShortcutPin).toHaveBeenCalledWith(1, 21, true);
    expect(wrapper.text()).toContain("已釘選");
  });

  it("shows role-aware management entries and opens the export center from the quick panel", async () => {
    authSession.value = {
      mode: "user",
      user: {
        id: 1,
        username: "admin",
        email: null,
        display_name: "Admin",
        role: "admin",
        is_active: true,
        allowed_customer_ids: [1],
        created_at: "2026-08-27",
        updated_at: "2026-08-27"
      },
      display_name: "Admin",
      token: "admin-token",
      role: "admin"
    };
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/search", component: { template: "<div />" } },
        { path: "/master/quality", component: { template: "<div />" } }
      ]
    });
    await router.push("/search?ui_surface=workbench&workbench_mode=fixture&customer=1");
    await router.isReady();
    const wrapper = mount(WorkbenchUiSurface, { global: { plugins: [router] } });
    await flushPromises();

    const managementTab = wrapper.findAll('[role="tab"]').find((tab) => tab.text() === "管理後臺");
    expect(managementTab).toBeDefined();
    await managementTab!.trigger("click");
    await flushPromises();

    const launcher = wrapper.get('[data-tour="workbench-management-launcher"]');
    expect(launcher.text()).toContain("收退料總檢視");
    expect(launcher.text()).toContain("產能設定");
    expect(launcher.text()).toContain("資料維護");
    expect(launcher.text()).toContain("收退料帳目管理");
    expect(launcher.text()).toContain("治具資料品質");
    expect(launcher.text()).toContain("匯出中心");

    const exportButton = launcher.findAll("button").find((button) => button.text().includes("匯出中心"));
    await exportButton!.trigger("click");
    expect(wrapper.emitted("openExport")).toHaveLength(1);

    const qualityButton = launcher.findAll("button").find((button) => button.text().includes("治具資料品質"));
    await qualityButton!.trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.path).toBe("/master/quality");
    expect(router.currentRoute.value.query.ui_surface).toBe("workbench");
  });

  it("keeps guest management shortcuts read-only and scoped", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/search", component: { template: "<div />" } }]
    });
    await router.push("/search?ui_surface=workbench&workbench_mode=management&customer=1");
    await router.isReady();
    const wrapper = mount(WorkbenchUiSurface, { global: { plugins: [router] } });
    await flushPromises();

    const launcher = wrapper.get('[data-tour="workbench-management-launcher"]');
    expect(launcher.text()).toContain("收退料總檢視");
    expect(launcher.text()).toContain("匯出中心");
    expect(launcher.text()).not.toContain("產能設定");
    expect(launcher.text()).not.toContain("資料維護");
    expect(launcher.text()).not.toContain("收退料帳目管理");
    expect(launcher.text()).not.toContain("治具資料品質");
  });

  it("offers bidirectional related searches when switching fixture and model tabs", async () => {
    const relatedModel = {
      id: 21,
      customer_id: 1,
      code: "AWK-1137C",
      name: "Wireless model",
      is_active: true
    };
    vi.mocked(api.listModels).mockResolvedValue([relatedModel]);
    vi.mocked(api.getFixtureSearchContext).mockResolvedValue({
      fixture: {
        id: 11,
        customer_id: 1,
        responsible_user_id: null,
        code: "L-00143",
        name: "線材治具",
        line_storage_location: "A-01",
        department_storage_location: "D-02",
        min_stock_qty: 2,
        description: null,
        is_active: true,
        has_image: false
      },
      stock: null,
      identifier_rows: [],
      related_models: [relatedModel],
      station_rows: [{
        model_id: 21,
        model_code: "AWK-1137C",
        model_name: "Wireless model",
        station_id: 31,
        station_code: "T1_RF",
        station_name: "RF station",
        required_qty: 1
      }],
      transactions: []
    });
    vi.mocked(api.getModelSearchContext).mockResolvedValue({
      model: relatedModel,
      query: {
        model_id: 21,
        model_code: "AWK-1137C",
        model_name: "Wireless model",
        max_open_station_count: 5,
        station_count: 1,
        fixture_type_count: 1,
        total_stock_qty: 5,
        stations: [],
        station_requirements: [],
        fixtures: [{
          fixture_id: 11,
          fixture_code: "L-00143",
          fixture_name: "線材治具",
          stock_qty: 5,
          min_stock_qty: 2,
          required_per_station: 1,
          max_open_station_count: 5,
          stock_status: "normal"
        }]
      }
    });
    vi.mocked(api.globalSearch).mockImplementation(async ({ entityType }) => ({
      items: entityType === "model"
        ? [{ entity_type: "model", title: "AWK-1137C", subtitle: "Wireless model", reference_id: 21, is_active: true }]
        : [{ entity_type: "fixture", title: "L-00143", subtitle: "線材治具", reference_id: 11, is_active: true }],
      page: 1,
      page_size: 20,
      total: 1,
      has_more: false
    }));
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/search", component: { template: "<div />" } }]
    });
    await router.push("/search?ui_surface=workbench&workbench_mode=fixture&customer=1");
    await router.isReady();
    const wrapper = mount(WorkbenchUiSurface, { global: { plugins: [router] } });
    await flushPromises();

    await wrapper.get('input[placeholder="例如 L-00143"]').setValue("L-00143");
    await wrapper.get("form.workbench-query-form").trigger("submit");
    await flushPromises();
    const modelTab = wrapper.findAll('[role="tab"]').find((tab) => tab.text() === "查詢機種");
    await modelTab!.trigger("click");
    await flushPromises();

    expect(wrapper.get('[data-tour="workbench-related-search-suggestion"]').text()).toContain("治具 L-00143");
    expect(wrapper.get('[data-tour="workbench-related-search-suggestion"]').text()).toContain("AWK-1137C");
    await wrapper.get('[aria-label="查詢機種 AWK-1137C Wireless model"]').trigger("click");
    await flushPromises();
    expect(api.globalSearch).toHaveBeenLastCalledWith({ q: "AWK-1137C", customerId: 1, entityType: "model", fixtureSearchMode: undefined, pageSize: 20 });
    expect(wrapper.text()).toContain("整機瓶頸產能");

    const fixtureTab = wrapper.findAll('[role="tab"]').find((tab) => tab.text() === "查詢治具");
    await fixtureTab!.trigger("click");
    await flushPromises();
    expect(wrapper.get('[data-tour="workbench-related-search-suggestion"]').text()).toContain("機種 AWK-1137C");
    await wrapper.get('[aria-label="查詢治具 L-00143 線材治具"]').trigger("click");
    await flushPromises();
    expect(api.globalSearch).toHaveBeenLastCalledWith({ q: "L-00143", customerId: 1, entityType: "fixture", fixtureSearchMode: "fixture", pageSize: 20 });
  });

  it("replaces the Workspace management tab with the transaction overview", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/search", component: { template: "<div />" } },
        { path: "/inventory/overview", component: { template: "<div />" } }
      ]
    });
    await router.push("/search?ui_surface=workspace&workbench_mode=fixture&customer=1");
    await router.isReady();
    const wrapper = mount(WorkbenchUiSurface, {
      props: { surface: "workspace", showHeader: false },
      global: { plugins: [router] }
    });
    await flushPromises();

    expect(wrapper.find(".workbench-header").exists()).toBe(false);
    const overviewTab = wrapper.findAll('[role="tab"]').find((tab) => tab.text() === "收／退料總檢視");
    expect(overviewTab).toBeDefined();
    expect(wrapper.text()).not.toContain("管理後臺");
    await overviewTab!.trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe("/inventory/overview");
    expect(router.currentRoute.value.query.ui_surface).toBe("workspace");
  });
});
