// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import FormRemoteAutocomplete from "./FormRemoteAutocomplete.vue";

const options = [
  { id: 1, code: "FX-001", name: "治具一" },
  { id: 2, code: "FX-002", name: "治具二" }
];

describe("FormRemoteAutocomplete", () => {
  it("searches lazily and supports keyboard selection", async () => {
    const wrapper = mount(FormRemoteAutocomplete, {
      props: {
        modelValue: "",
        options,
        inputLabel: "選擇治具"
      }
    });
    const input = wrapper.get("input[role='combobox']");

    await input.trigger("focus");
    expect(wrapper.emitted("search")?.[0]).toEqual([""]);
    expect(wrapper.findAll("[role='option']")).toHaveLength(2);

    await input.setValue("FX-0");
    expect(wrapper.emitted("update:modelValue")?.at(-1)).toEqual(["FX-0"]);
    expect(wrapper.emitted("search")?.at(-1)).toEqual(["FX-0"]);

    await input.trigger("keydown", { key: "ArrowDown" });
    await input.trigger("keydown", { key: "Enter" });
    expect(wrapper.emitted("select")?.at(-1)).toEqual([options[0]]);
    expect(wrapper.emitted("update:modelValue")?.at(-1)).toEqual(["FX-001－治具一"]);
  });

  it("caps rendered results at twenty options", async () => {
    const wrapper = mount(FormRemoteAutocomplete, {
      props: {
        modelValue: "",
        options: Array.from({ length: 50 }, (_, index) => ({
          id: index + 1,
          code: `FX-${index + 1}`,
          name: `Fixture ${index + 1}`
        })),
        inputLabel: "選擇治具"
      }
    });

    await wrapper.get("input").trigger("focus");
    expect(wrapper.findAll("[role='option']")).toHaveLength(20);
  });
});
