// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";

import OnboardingFlowPicker from "@/components/common/OnboardingFlowPicker.vue";

afterEach(() => {
  document.body.innerHTML = "";
});

describe("OnboardingFlowPicker", () => {
  it("puts the complete detailed guide before concise tutorials", () => {
    const wrapper = mount(OnboardingFlowPicker, {
      props: {
        open: true,
        flows: [
          {
            id: "search-basics",
            sectionLabel: "首頁查詢",
            label: "查詢工作台",
            summary: "基本操作",
            stepCount: 4,
            disabled: false,
            disabledReason: ""
          },
          {
            id: "system-detailed-guide",
            sectionLabel: "完整詳細版",
            label: "全系統按鈕與操作說明",
            summary: "詳細操作",
            stepCount: 33,
            disabled: false,
            disabledReason: ""
          }
        ]
      }
    });

    const headings = Array.from(document.body.querySelectorAll(".flow-card h3")).map((element) => element.textContent);
    const buttons = Array.from(document.body.querySelectorAll(".flow-start-btn")).map((element) => element.textContent?.trim());

    expect(headings).toEqual(["全系統按鈕與操作說明", "查詢工作台"]);
    expect(buttons[0]).toBe("開始完整詳細版");

    wrapper.unmount();
  });
});
