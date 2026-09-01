// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { defineComponent } from "vue";
import { createMemoryHistory, createRouter, RouterView } from "vue-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "@/api";
import { selectedCustomerId } from "@/appState";

import SearchWorkspacePage from "./SearchWorkspacePage.vue";

vi.mock("@/api", () => ({
  api: {
    getFixtureOverview: vi.fn(),
    listCustomerUsers: vi.fn(),
    listTransactions: vi.fn(),
    globalSearch: vi.fn(),
    getFixtureSearchContext: vi.fn(),
    getModelSearchContext: vi.fn()
  },
  fetchFixtureImageObjectUrl: vi.fn().mockRejectedValue(new Error("fixture image missing"))
}));

vi.mock("@/appState", async () => {
  const { ref } = await import("vue");
  return {
    authSession: ref({ role: "user" }),
    selectedCustomerId: ref<number | null>(7),
    requestInventoryBatchOpen: vi.fn(),
    setCustomerSwitchGuard: vi.fn()
  };
});

vi.mock("@/confirmState", () => ({
  requestConfirmation: vi.fn().mockResolvedValue(true)
}));

vi.mock("@/toastState", () => ({
  pushToast: vi.fn()
}));

beforeEach(() => {
  selectedCustomerId.value = 7;
  vi.mocked(api.listCustomerUsers).mockResolvedValue([]);
  vi.mocked(api.listTransactions).mockResolvedValue([]);
  vi.mocked(api.getFixtureOverview).mockResolvedValue({
    items: [
      {
        entity_type: "fixture",
        title: "FX-001",
        subtitle: "Overview fixture",
        reference_id: 1,
        is_active: true,
        stock_qty: 5,
        stock_status: "normal",
        location_code: "LINE-A"
      }
    ],
    page: 1,
    page_size: 20,
    total: 1,
    has_more: false
  });
});

afterEach(() => {
  window.localStorage.clear();
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

async function mountSearch(path = "/search") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/search", name: "search", component: SearchWorkspacePage }]
  });
  await router.push(path);
  await router.isReady();
  const TestHost = defineComponent({
    components: { RouterView },
    template: "<RouterView />"
  });
  vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => {
    callback(0);
    return 1;
  });
  Object.defineProperty(window, "scrollTo", { configurable: true, value: vi.fn() });
  const wrapper = mount(TestHost, { global: { plugins: [router] } });
  await flushPromises();
  return { router, wrapper };
}

describe("SearchWorkspacePage fixture overview", () => {
  it("loads and displays the concise fixture overview when the query is empty", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/search", name: "search", component: SearchWorkspacePage }]
    });
    await router.push("/search");
    await router.isReady();

    const TestHost = defineComponent({
      components: { RouterView },
      template: "<RouterView />"
    });
    const wrapper = mount(TestHost, {
      global: { plugins: [router] }
    });
    await flushPromises();

    expect(api.getFixtureOverview).toHaveBeenCalledWith(7, 1, 20);
    const workspaceCard = wrapper.get(".search-workspace-card.idle");
    expect(workspaceCard.find(".hero-card").exists()).toBe(true);
    expect(workspaceCard.find(".search-workspace-overview .fixture-overview-panel").exists()).toBe(true);
    expect(wrapper.get(".fixture-overview-panel").text()).toContain("治具總清單");
    expect(wrapper.get(".fixture-overview-panel").text()).toContain("FX-001");
    expect(wrapper.find(".content-grid").exists()).toBe(false);

    wrapper.unmount();
  });

  it("stores search mode, value and selected result in URL and restores them with browser back", async () => {
    vi.mocked(api.globalSearch).mockImplementation(async ({ q }) => ({
      items: [{
        entity_type: "fixture",
        title: q,
        subtitle: `Fixture ${q}`,
        reference_id: q === "FX-002" ? 2 : 1,
        is_active: true,
        stock_qty: 1,
        stock_status: "normal"
      }],
      page: 1,
      page_size: 12,
      total: 1,
      has_more: false
    }));
    vi.mocked(api.getFixtureSearchContext).mockImplementation(async (fixtureId) => ({
      fixture: {
        id: fixtureId,
        customer_id: 7,
        responsible_user_id: null,
        code: fixtureId === 2 ? "FX-002" : "FX-001",
        name: `Fixture ${fixtureId}`,
        line_storage_location: null,
        department_storage_location: null,
        min_stock_qty: 0,
        description: null,
        is_active: true,
        has_image: false
      },
      stock: null,
      identifier_rows: [],
      related_models: [],
      station_rows: [],
      transactions: []
    }));
    const { router, wrapper } = await mountSearch("/search?ui_surface=modern&home_mode=query&customer=7");
    const input = wrapper.get<HTMLInputElement>('[data-tour="search-query-field"] input');

    await input.setValue("FX-001");
    await wrapper.get(".query-submit-btn").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query).toMatchObject({
      mode: "fixture",
      fixture_search: "fixture",
      q: "FX-001",
      selected_id: "1"
    });

    await input.setValue("FX-002");
    await wrapper.get(".query-submit-btn").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.q).toBe("FX-002");
    expect(router.currentRoute.value.query.selected_id).toBe("2");

    router.back();
    await flushPromises();
    expect(router.currentRoute.value.query.q).toBe("FX-001");
    expect(wrapper.get<HTMLInputElement>('[data-tour="search-query-field"] input').element.value).toBe("FX-001");
  });

  it("sends identifier-only searches through the explicit Datecode mode", async () => {
    vi.mocked(api.globalSearch).mockResolvedValue({
      items: [],
      page: 1,
      page_size: 12,
      total: 0,
      has_more: false
    });
    const { router, wrapper } = await mountSearch("/search?ui_surface=modern&home_mode=query&customer=7");

    await wrapper.findAll(".fixture-search-switch button")[1].trigger("click");
    const input = wrapper.get<HTMLInputElement>('[data-tour="search-query-field"] input');
    expect(input.attributes("placeholder")).toContain("只輸入 Datecode");
    await input.setValue("2204");
    await wrapper.get(".query-submit-btn").trigger("click");
    await flushPromises();

    expect(api.globalSearch).toHaveBeenLastCalledWith({
      q: "2204",
      customerId: 7,
      entityType: "fixture",
      fixtureSearchMode: "identifier",
      page: 1,
      pageSize: 12
    });
    expect(router.currentRoute.value.query.fixture_search).toBe("identifier");
    expect(router.currentRoute.value.query.q).toBe("2204");
  });
});
