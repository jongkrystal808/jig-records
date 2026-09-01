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
        role: "admin",
        surface: "modern",
        flows: [
          {
            id: "search-basics",
            sectionLabel: "首頁查詢",
            label: "查詢工作台",
            summary: "基本操作",
            stepCount: 4,
            disabled: false,
            disabledReason: "",
            variant: "concise"
          },
          {
            id: "system-detailed-guide",
            sectionLabel: "完整詳細版",
            label: "全系統按鈕與操作說明",
            summary: "詳細操作",
            stepCount: 33,
            disabled: false,
            disabledReason: "",
            variant: "detailed"
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

  it("shows quick, complete readonly, and login-only guidance for guests", () => {
    const wrapper = mount(OnboardingFlowPicker, {
      props: {
        open: true,
        role: "guest",
        surface: "modern",
        flows: [
          {
            id: "guest-search-report",
            sectionLabel: "訪客首頁",
            label: "查詢工作台與庫存配置報表",
            summary: "快速操作",
            stepCount: 7,
            disabled: false,
            disabledReason: "",
            variant: "concise"
          },
          {
            id: "guest-readonly-guide",
            sectionLabel: "完整唯讀教學",
            label: "訪客可查看功能完整說明",
            summary: "完整唯讀操作",
            stepCount: 18,
            disabled: false,
            disabledReason: "",
            variant: "detailed"
          }
        ]
      }
    });

    const text = document.body.textContent ?? "";
    const headings = Array.from(document.body.querySelectorAll(".flow-card h3")).map((element) => element.textContent);

    expect(headings).toEqual(["訪客可查看功能完整說明", "查詢工作台與庫存配置報表"]);
    expect(text).toContain("開始完整唯讀教學");
    expect(text).toContain("快速認識目前介面的查詢與報表");
    expect(text).toContain("需 User / Admin");
    expect(text).toContain("Admin / Super Admin");

    wrapper.unmount();
  });

  it("labels the Form UI picker and finds its detailed flow by variant", () => {
    const wrapper = mount(OnboardingFlowPicker, {
      props: {
        open: true,
        role: "admin",
        surface: "form",
        flows: [
          {
            id: "form-quick-guide",
            sectionLabel: "Form UI 精簡版",
            label: "快速導覽",
            summary: "快速操作",
            stepCount: 6,
            disabled: false,
            disabledReason: "",
            variant: "concise"
          },
          {
            id: "form-detailed-guide",
            sectionLabel: "Form UI 完整詳細版",
            label: "完整操作",
            summary: "完整操作說明",
            stepCount: 15,
            disabled: false,
            disabledReason: "",
            variant: "detailed"
          }
        ]
      }
    });

    expect(document.body.textContent).toContain("Form UI 新手教學");
    expect(Array.from(document.body.querySelectorAll(".flow-card h3")).map((element) => element.textContent))
      .toEqual(["完整操作", "快速導覽"]);
    wrapper.unmount();
  });

  it("labels the Workbench UI picker independently from Form UI", () => {
    const wrapper = mount(OnboardingFlowPicker, {
      props: {
        open: true,
        role: "admin",
        surface: "workbench",
        flows: [
          {
            id: "workbench-quick-guide",
            sectionLabel: "工作台 UI 精簡版",
            label: "工作台快速導覽",
            summary: "快速操作",
            stepCount: 6,
            disabled: false,
            disabledReason: "",
            variant: "concise"
          }
        ]
      }
    });

    expect(document.body.textContent).toContain("工作台 UI 新手教學");
    expect(document.body.textContent).toContain("工作台快速導覽");
    wrapper.unmount();
  });
});
