import { describe, expect, it } from "vitest";

import {
  resolveAppUiSurface,
  resolveHomeUiSurface,
  uiSurfaceRouteQuery
} from "@/utils/uiSurface";

describe("ui surface routing", () => {
  it("resolves explicit surfaces and legacy home modes", () => {
    expect(resolveHomeUiSurface("modern", "report")).toBe("workspace");
    expect(resolveHomeUiSurface("workbench", "report")).toBe("workspace");
    expect(resolveHomeUiSurface("workspace", "report")).toBe("workspace");
    expect(resolveHomeUiSurface(undefined, "query")).toBe("workspace");
    expect(resolveHomeUiSurface(undefined, "report")).toBe("form");
  });

  it("applies the selected surface to every system route", () => {
    expect(resolveAppUiSurface("/master", "form", "report", "workspace")).toBe("form");
    expect(resolveAppUiSurface("/search/detail", undefined, undefined, "form")).toBe("form");
    expect(resolveAppUiSurface("/production", undefined, undefined, "workspace")).toBe("workspace");
    expect(resolveAppUiSurface("/inventory", "workbench", "query", "workspace")).toBe("workspace");
    expect(resolveAppUiSurface("/production", "workspace", "query", "workspace")).toBe("workspace");
  });

  it("builds compatible surface and legacy mode query state", () => {
    expect(uiSurfaceRouteQuery("modern")).toEqual({
      ui_surface: "modern",
      home_mode: "query"
    });
    expect(uiSurfaceRouteQuery("form")).toEqual({
      ui_surface: "form",
      home_mode: "report"
    });
    expect(uiSurfaceRouteQuery("workbench")).toEqual({
      ui_surface: "workbench",
      home_mode: "query"
    });
    expect(uiSurfaceRouteQuery("workspace")).toEqual({
      ui_surface: "workspace",
      home_mode: "query"
    });
  });
});
