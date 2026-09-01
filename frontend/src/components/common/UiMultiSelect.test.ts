// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import UiMultiSelect from "./UiMultiSelect.vue";

const options = [
  { value: "receipt", label: "收料" },
  { value: "return", label: "退料" },
  { value: "disabled", label: "停用項目", disabled: true }
];

describe("UiMultiSelect", () => {
  it("supports selecting multiple values and clearing them", async () => {
    const wrapper = mount(UiMultiSelect, {
      props: {
        modelValue: [],
        options,
        label: "作業類型"
      }
    });

    expect(wrapper.get("summary").text()).toContain("全部");
    const inputs = wrapper.findAll<HTMLInputElement>('input[type="checkbox"]');
    await inputs[0].setValue(true);
    await wrapper.setProps({ modelValue: ["receipt"] });
    await inputs[1].setValue(true);

    expect(wrapper.emitted("update:modelValue")).toEqual([
      [["receipt"]],
      [["receipt", "return"]]
    ]);

    await wrapper.setProps({ modelValue: ["receipt", "return"] });
    expect(wrapper.get("summary").text()).toContain("收料、退料");
    expect(wrapper.findAll(".ui-multi-select-option")[0].classes()).toContain("selected");
    expect(wrapper.findAll(".ui-multi-select-option")[1].classes()).toContain("selected");
    await wrapper.findAll("button")[1].trigger("click");
    expect(wrapper.emitted("change")?.at(-1)).toEqual([[]]);
  });

  it("selects every enabled option and respects the disabled state", async () => {
    const wrapper = mount(UiMultiSelect, {
      props: {
        modelValue: [],
        options,
        label: "作業類型"
      }
    });

    await wrapper.findAll("button")[0].trigger("click");
    expect(wrapper.emitted("update:modelValue")?.at(-1)).toEqual([["receipt", "return"]]);

    await wrapper.setProps({ disabled: true });
    await wrapper.get("summary").trigger("click");
    expect(wrapper.get("summary").attributes("aria-disabled")).toBe("true");
    expect(wrapper.findAll<HTMLInputElement>('input[type="checkbox"]').every((input) => input.element.disabled)).toBe(true);
  });
});
