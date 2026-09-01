// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";

import { searchWorkspaceHandoffState } from "@/appState";
import SearchHomePage from "@/pages/SearchHomePage.vue";

afterEach(() => {
  searchWorkspaceHandoffState.value = null;
});

describe("SearchHomePage", () => {
  it("is the Modern UI route content and retains report handoff context globally", () => {
    const wrapper = mount(SearchHomePage, {
      global: { stubs: { ModernUiSurface: true } }
    });
    const surface = wrapper.findComponent({ name: "ModernUiSurface" });

    surface.vm.$emit("reportContextChange", {
      mode: "fixture",
      draftQuery: "C-00003",
      committedQuery: "C-00003",
      selectedResultId: 23
    });

    expect(searchWorkspaceHandoffState.value).toEqual({
      mode: "fixture",
      draftQuery: "C-00003",
      committedQuery: "C-00003",
      selectedResultId: 23
    });
  });
});
