// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { describe, expect, it } from "vitest";

import FormSystemSurface from "@/components/app/FormSystemSurface.vue";

async function mountAt(path: string) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      "/search",
      "/inventory",
      "/inventory/overview",
      "/production/mapping",
      "/production/requirements",
      "/master/fixtures",
      "/master/models",
      "/master/images"
    ].map((routePath) => ({ path: routePath, component: { template: "<div />" } }))
  });
  await router.push(path);
  await router.isReady();
  return {
    router,
    wrapper: mount(FormSystemSurface, {
      global: { plugins: [router], stubs: { FormUiSurface: true } }
    })
  };
}

describe("FormSystemSurface", () => {
  it("maps existing production routes to the Form production workspace", async () => {
    const { wrapper } = await mountAt("/production/mapping");
    const surface = wrapper.findComponent({ name: "FormUiSurface" });
    expect(surface.props("workspace")).toBe("production");
    expect(surface.props("productionView")).toBe("mappings");
  });

  it("maps master routes and navigates workspace changes with stable URLs", async () => {
    const { router, wrapper } = await mountAt("/master/models");
    const surface = wrapper.findComponent({ name: "FormUiSurface" });
    expect(surface.props("workspace")).toBe("master");
    expect(surface.props("masterView")).toBe("model");

    surface.vm.$emit("workspaceChange", "image");
    await flushPromises();
    expect(router.currentRoute.value.path).toBe("/master/images");
  });
});
