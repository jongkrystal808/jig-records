// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import HomeUiSurfaceSwitcher from "./HomeUiSurfaceSwitcher.vue";

describe("HomeUiSurfaceSwitcher default surface", () => {
  it("lets a signed-in user choose a default independently from the active surface", async () => {
    const wrapper = mount(HomeUiSurfaceSwitcher, {
      props: {
        activeSurface: "workspace",
        preferredSurface: "workspace",
        isGuest: false,
        switching: false,
        compact: true
      }
    });

    const defaultPicker = wrapper.get<HTMLSelectElement>('select[aria-label="登入後預設介面"]');
    expect(defaultPicker.element.value).toBe("workspace");

    await defaultPicker.setValue("form");

    expect(wrapper.emitted("saveDefault")?.[0]).toEqual(["form"]);
  });

  it("keeps the account preference control unavailable to guests", () => {
    const wrapper = mount(HomeUiSurfaceSwitcher, {
      props: {
        activeSurface: "workspace",
        preferredSurface: "workspace",
        isGuest: true,
        switching: false,
        compact: true
      }
    });

    expect(wrapper.find('select[aria-label="登入後預設介面"]').exists()).toBe(false);
    expect(wrapper.text()).toContain("訪客預設");
    expect(wrapper.text()).toContain("Workspace UI");
  });

  it("only offers Workspace and Form surfaces", async () => {
    const wrapper = mount(HomeUiSurfaceSwitcher, {
      props: {
        activeSurface: "form",
        preferredSurface: "form",
        isGuest: false,
        switching: false,
        compact: true
      }
    });

    expect(wrapper.findAll('button[role="tab"]')).toHaveLength(2);
    expect(wrapper.text()).not.toContain("Modern UI");
    expect(wrapper.text()).not.toContain("工作台 UI");
    await wrapper.findAll('button[role="tab"]')[0].trigger("click");
    expect(wrapper.emitted("select")?.at(-1)).toEqual(["workspace"]);

    await wrapper.get<HTMLSelectElement>('select[aria-label="登入後預設介面"]').setValue("workspace");
    expect(wrapper.emitted("saveDefault")?.at(-1)).toEqual(["workspace"]);
  });
});
