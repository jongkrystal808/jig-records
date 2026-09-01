// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import SearchHeroSection from "./SearchHeroSection.vue";

const recentFixtureShortcuts = [
  ...Array.from({ length: 20 }, (_, index) => ({
    fixtureCode: `FX-${String(index + 1).padStart(3, "0")}`,
    transactionType: index % 2 === 0 ? "receipt" as const : "return" as const,
    occurredAt: `2026-08-24T${String(8 + (index % 10)).padStart(2, "0")}:00:00`
  }))
];

function mountHero() {
  return mount(SearchHeroSection, {
    props: {
      mode: "fixture",
      fixtureSearchMode: "fixture",
      queryDraft: "",
      hasActiveQuery: false,
      recentFixtureShortcuts,
      sectionChips: [{ key: "overview", label: "總覽" }],
      activeSectionKeys: ["overview"]
    }
  });
}

describe("SearchHeroSection", () => {
  it("keeps the release notice collapsed until the user opens it", async () => {
    const wrapper = mountHero();
    const trigger = wrapper.get('button[aria-label="查看更新內容"]');

    expect(trigger.attributes("aria-expanded")).toBe("false");
    expect(wrapper.find("#search-release-notice").exists()).toBe(false);

    await trigger.trigger("click");
    expect(trigger.attributes("aria-expanded")).toBe("true");
    expect(wrapper.get("#search-release-notice").text()).toContain("2026-08-25");

    await trigger.trigger("keydown", { key: "Escape" });
    expect(wrapper.find("#search-release-notice").exists()).toBe(false);
  });

  it("renders recent fixture shortcuts in one reusable row and emits selection", async () => {
    const wrapper = mountHero();

    expect(wrapper.get(".shortcut-row").classes()).toContain("shortcut-row");
    await wrapper.get(".shortcut-chip").trigger("click");
    expect(wrapper.emitted("applyRecentFixtureShortcut")?.[0]).toEqual(["FX-001"]);
  });

  it("shows five recent fixtures first, then expands and collapses with matching labels", async () => {
    const wrapper = mountHero();
    const toggle = wrapper.get(".shortcut-toggle-btn");

    expect(wrapper.findAll(".shortcut-chip")).toHaveLength(5);
    expect(toggle.text()).toBe("展開全部（20）");
    expect(toggle.attributes("aria-expanded")).toBe("false");

    await toggle.trigger("click");
    expect(wrapper.findAll(".shortcut-chip")).toHaveLength(20);
    expect(toggle.text()).toBe("收合為 5 筆");
    expect(toggle.attributes("aria-expanded")).toBe("true");

    await toggle.trigger("click");
    expect(wrapper.findAll(".shortcut-chip")).toHaveLength(5);
    expect(toggle.text()).toBe("展開全部（20）");
  });
});
