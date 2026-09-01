// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import MasterReadonlySummary from "./MasterReadonlySummary.vue";

describe("MasterReadonlySummary", () => {
  it("prompts for a selection when no master row is selected", () => {
    const wrapper = mount(MasterReadonlySummary, {
      props: { fields: [], entityLabel: "治具", onEdit: vi.fn() }
    });

    expect(wrapper.text()).toContain("尚未選擇資料");
    expect(wrapper.text()).toContain("請從左側清單選擇一筆治具");
    expect(wrapper.find(".primary-btn").exists()).toBe(false);
  });

  it("shows read-only values and enters editing only from the edit action", async () => {
    const onEdit = vi.fn();
    const wrapper = mount(MasterReadonlySummary, {
      props: {
        fields: [
          { label: "治具編號", value: "JIG-001" },
          { label: "狀態", value: "啟用中" }
        ],
        entityLabel: "治具",
        onEdit
      }
    });

    expect(wrapper.get("dl").text()).toContain("JIG-001");
    expect(wrapper.find("input").exists()).toBe(false);

    await wrapper.get(".primary-btn").trigger("click");
    expect(onEdit).toHaveBeenCalledOnce();
  });
});
