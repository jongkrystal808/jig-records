// @vitest-environment jsdom

import { shallowMount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { afterEach, describe, expect, it } from "vitest";

import { authSession } from "@/appState";
import SearchHomePage from "@/pages/SearchHomePage.vue";
import type { AuthSession } from "@/types";

function session(role: string): AuthSession {
  return {
    mode: role === "guest" ? "guest" : "user",
    user:
      role === "guest"
        ? null
        : {
            id: role === "admin" ? 1 : 2,
            username: `${role}-account`,
            email: null,
            display_name: role,
            role,
            is_active: true,
            allowed_customer_ids: [],
            created_at: "",
            updated_at: ""
          },
    display_name: role,
    token: "test-token",
    role
  };
}

async function mountHome(path = "/search") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/search", name: "search", component: SearchHomePage }]
  });
  await router.push(path);
  await router.isReady();
  return {
    router,
    wrapper: shallowMount(SearchHomePage, {
      global: {
        plugins: [router]
      }
    })
  };
}

afterEach(() => {
  authSession.value = null;
  window.localStorage.clear();
});

describe("SearchHomePage", () => {
  it("defaults guest sessions to the report and allows switching to query", async () => {
    authSession.value = session("guest");
    const { wrapper } = await mountHome();

    expect(wrapper.findComponent({ name: "InventoryRelationsPage" }).exists()).toBe(true);
    expect(wrapper.findComponent({ name: "SearchWorkspacePage" }).exists()).toBe(false);

    await wrapper.findAll(".home-mode-tabs button")[0].trigger("click");

    expect(wrapper.findComponent({ name: "SearchWorkspacePage" }).exists()).toBe(true);
    expect(wrapper.findComponent({ name: "InventoryRelationsPage" }).exists()).toBe(false);
  });

  it.each(["admin", "user"])("defaults %s sessions to query", async (role) => {
    authSession.value = session(role);
    const { wrapper } = await mountHome();

    expect(wrapper.findComponent({ name: "SearchWorkspacePage" }).exists()).toBe(true);
    expect(wrapper.findComponent({ name: "InventoryRelationsPage" }).exists()).toBe(false);
  });

  it("lets a signed-in user save report as their next-login default", async () => {
    authSession.value = session("user");
    const firstMount = await mountHome();

    await firstMount.wrapper.findAll(".home-mode-tabs button")[1].trigger("click");
    await firstMount.wrapper.find(".home-mode-preference button").trigger("click");
    firstMount.wrapper.unmount();

    const secondMount = await mountHome();

    expect(secondMount.wrapper.findComponent({ name: "InventoryRelationsPage" }).exists()).toBe(true);
    expect(secondMount.wrapper.find(".default-confirmation").text()).toContain("目前為預設");
  });

  it("honors an explicit homepage mode in the URL", async () => {
    authSession.value = session("guest");
    const { wrapper } = await mountHome("/search?home_mode=query");

    expect(wrapper.findComponent({ name: "SearchWorkspacePage" }).exists()).toBe(true);
  });
});
