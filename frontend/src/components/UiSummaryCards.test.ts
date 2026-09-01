// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import UiSummaryCards from "./UiSummaryCards.vue";

describe("UiSummaryCards", () => {
  it("renders actionable cards as accessible toggle buttons", async () => {
    const wrapper = mount(UiSummaryCards, {
      props: {
        cards: [
          {
            label: "未配置",
            value: 7,
            meta: "缺少治具配置",
            action: "unconfigured",
            selected: true,
            ariaLabel: "一鍵篩選未配置資料"
          }
        ]
      }
    });

    const button = wrapper.get('button[aria-label="一鍵篩選未配置資料"]');
    expect(button.attributes("aria-pressed")).toBe("true");

    await button.trigger("click");

    expect(wrapper.emitted("action")).toEqual([["unconfigured"]]);
  });

  it("keeps non-action summaries as articles", () => {
    const wrapper = mount(UiSummaryCards, {
      props: {
        cards: [{ label: "總庫存", value: 120 }]
      }
    });

    expect(wrapper.find("article").exists()).toBe(true);
    expect(wrapper.find("button").exists()).toBe(false);
  });
});
