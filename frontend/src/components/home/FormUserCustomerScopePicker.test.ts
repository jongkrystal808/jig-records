// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import FormUserCustomerScopePicker from "@/components/home/FormUserCustomerScopePicker.vue";

const customers = [
  { id: 1, code: "ALPHA", name: "Alpha 客戶", assigned_user_ids: [] },
  { id: 2, code: "BETA", name: "Beta 客戶", assigned_user_ids: [] },
  { id: 3, code: "GAMMA", name: "Gamma 客戶", assigned_user_ids: [] }
];

describe("FormUserCustomerScopePicker", () => {
  it("shows the selected count and supports individual multi-selection", async () => {
    const wrapper = mount(FormUserCustomerScopePicker, {
      props: { customers, modelValue: [1] }
    });

    expect(wrapper.text()).toContain("已選 1 個");
    expect(wrapper.findAll(".selected-chip")).toHaveLength(1);
    await wrapper.findAll("input[type='checkbox']")[1].setValue(true);

    expect(wrapper.emitted("update:modelValue")?.at(-1)).toEqual([[1, 2]]);
  });

  it("searches by code or name and can select all visible results", async () => {
    const wrapper = mount(FormUserCustomerScopePicker, {
      props: { customers, modelValue: [1] }
    });

    await wrapper.get("input[type='search']").setValue("beta");
    expect(wrapper.findAll(".customer-options label")).toHaveLength(1);
    expect(wrapper.text()).toContain("BETA");
    await wrapper.get(".scope-action").trigger("click");

    expect(wrapper.emitted("update:modelValue")?.at(-1)).toEqual([[1, 2]]);
  });

  it("removes selected chips and clears the full selection", async () => {
    const wrapper = mount(FormUserCustomerScopePicker, {
      props: { customers, modelValue: [1, 2] }
    });

    await wrapper.get("[aria-label='移除 ALPHA Alpha 客戶']").trigger("click");
    expect(wrapper.emitted("update:modelValue")?.at(-1)).toEqual([[2]]);

    await wrapper.get(".scope-action.danger").trigger("click");
    expect(wrapper.emitted("update:modelValue")?.at(-1)).toEqual([[]]);
  });
});
