// @vitest-environment jsdom

import { afterEach, describe, expect, it } from "vitest";

import { authSession } from "@/appState";
import router, { FORM_WORKSPACE_SCROLL_POSITION } from "@/router";
import { UI_SURFACE_SESSION_KEY } from "@/utils/uiSurface";
import { allowNextRouteNavigation } from "@/unsavedChangesGuard";

const savedPosition = { left: 0, top: 760 };

async function resolveScroll(toPath: string, fromPath: string) {
  const scrollBehavior = router.options.scrollBehavior;
  if (!scrollBehavior) throw new Error("Router scrollBehavior is not configured");
  type ScrollParameters = Parameters<typeof scrollBehavior>;
  return scrollBehavior(
    router.resolve(toPath) as ScrollParameters[0],
    router.resolve(fromPath) as ScrollParameters[1],
    savedPosition
  );
}

afterEach(() => {
  window.sessionStorage.clear();
  authSession.value = null;
});

describe("Form workspace scroll behavior", () => {
  it("moves a Form module switch to the module and filter top without DOM detection", async () => {
    window.sessionStorage.setItem(UI_SURFACE_SESSION_KEY, "form");

    await expect(resolveScroll("/inventory", "/search")).resolves.toEqual(
      FORM_WORKSPACE_SCROLL_POSITION
    );
  });

  it("also resets nested production and master view navigation", async () => {
    window.sessionStorage.setItem(UI_SURFACE_SESSION_KEY, "form");

    await expect(resolveScroll("/production/mapping", "/production/requirements")).resolves.toEqual(
      FORM_WORKSPACE_SCROLL_POSITION
    );
    await expect(resolveScroll("/master/models", "/master/fixtures")).resolves.toEqual(
      FORM_WORKSPACE_SCROLL_POSITION
    );
  });

  it("preserves the browser position when Form UI is not active", async () => {
    window.sessionStorage.setItem(UI_SURFACE_SESSION_KEY, "modern");
    await expect(resolveScroll("/inventory", "/search")).resolves.toEqual(savedPosition);
  });

  it("lets an explicit Modern UI route override a stale Form session", async () => {
    window.sessionStorage.setItem(UI_SURFACE_SESSION_KEY, "form");

    await expect(
      resolveScroll("/inventory?ui_surface=modern", "/search?ui_surface=form")
    ).resolves.toEqual(savedPosition);
  });
});

describe("Workbench guest route guards", () => {
  it("returns protected Workbench routes to the Workbench overview", async () => {
    authSession.value = {
      mode: "guest",
      user: null,
      display_name: "訪客",
      token: "guest-token",
      role: "guest"
    };
    await router.push("/inventory/overview?ui_surface=workbench&home_mode=query&customer=2");
    await router.push("/production/requirements?ui_surface=workbench&home_mode=query&customer=2");

    expect(router.currentRoute.value.path).toBe("/inventory/overview");
    expect(router.currentRoute.value.query.ui_surface).toBe("workbench");
    expect(router.currentRoute.value.query.customer).toBe("2");
  });

  it("keeps Admin-only Workbench reports inaccessible to regular users", async () => {
    authSession.value = {
      mode: "user",
      user: {
        id: 7,
        username: "operator",
        email: null,
        display_name: "Operator",
        role: "user",
        is_active: true,
        allowed_customer_ids: [2],
        created_at: "",
        updated_at: ""
      },
      display_name: "Operator",
      token: "user-token",
      role: "user"
    };
    await router.push("/inventory/overview?ui_surface=workbench&customer=2");
    await router.push("/master/ledger?ui_surface=workbench&customer=2");

    expect(router.currentRoute.value.path).toBe("/inventory/overview");
    expect(router.currentRoute.value.query.ui_surface).toBe("workbench");
    expect(router.currentRoute.value.query.customer).toBe("2");
  });
});

describe("management role route guards", () => {
  it("keeps account management exclusive to Super Admin", async () => {
    authSession.value = {
      mode: "user",
      user: {
        id: 8,
        username: "ordinary-admin",
        email: null,
        display_name: "Ordinary Admin",
        role: "admin",
        is_active: true,
        allowed_customer_ids: [2],
        created_at: "",
        updated_at: ""
      },
      display_name: "Ordinary Admin",
      token: "admin-token",
      role: "admin"
    };
    allowNextRouteNavigation();
    await router.push("/search");
    allowNextRouteNavigation();
    await router.push("/master/users");
    expect(router.currentRoute.value.path).toBe("/master/fixtures");

    authSession.value = {
      ...authSession.value,
      role: "super_admin",
      user: { ...authSession.value.user!, role: "super_admin" }
    };
    allowNextRouteNavigation();
    await router.push("/master/users");
    expect(router.currentRoute.value.path).toBe("/master/users");
  });
});
