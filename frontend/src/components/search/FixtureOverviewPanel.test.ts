// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import FixtureOverviewPanel from "./FixtureOverviewPanel.vue";

const rows = [
  {
    entity_type: "fixture" as const,
    title: "FX-001",
    subtitle: "Main fixture",
    reference_id: 1,
    is_active: true,
    stock_qty: 2,
    stock_status: "low_stock" as const,
    location_code: "LINE-A / DEPT-1",
    matched_identifier: null
  }
];

describe("FixtureOverviewPanel", () => {
  it("renders a concise fixture list and opens the selected fixture", async () => {
    const wrapper = mount(FixtureOverviewPanel, {
      props: {
        rows,
        total: 2,
        loading: false,
        loadingMore: false,
        hasMore: true,
        formatCount: (value: number) => String(value),
        stockTone: () => "warn"
      }
    });

    expect(wrapper.get("h2").text()).toBe("治具總清單");
    expect(wrapper.text()).toContain("FX-001");
    expect(wrapper.text()).toContain("低庫存");
    expect(wrapper.text()).toContain("LINE-A / DEPT-1");
    expect(wrapper.text()).toContain("已顯示 1 / 2 筆");

    await wrapper.get('button[aria-label="查看治具 FX-001"]').trigger("click");
    expect(wrapper.emitted("select")?.[0]).toEqual([rows[0]]);

    const mobileCard = wrapper.get('button[aria-label="查看治具 FX-001 詳情"]');
    expect(mobileCard.text()).toContain("Main fixture");
    expect(mobileCard.text()).toContain("目前庫存");
    expect(mobileCard.text()).toContain("LINE-A / DEPT-1");
    await mobileCard.trigger("click");
    expect(wrapper.emitted("select")?.[1]).toEqual([rows[0]]);

    await wrapper.findAll("button").at(-1)?.trigger("click");
    expect(wrapper.emitted("loadMore")).toHaveLength(1);
  });

  it("shows the empty overview state", () => {
    const wrapper = mount(FixtureOverviewPanel, {
      props: {
        rows: [],
        total: 0,
        loading: false,
        loadingMore: false,
        hasMore: false,
        formatCount: (value: number) => String(value),
        stockTone: () => "muted"
      }
    });

    expect(wrapper.text()).toContain("目前沒有治具資料");
  });
});
