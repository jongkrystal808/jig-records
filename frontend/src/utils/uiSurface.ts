import type { LocationQueryRaw } from "vue-router";

export type HomeUiSurface = "form" | "workspace";
export type LegacyUiSurface = "modern" | "workbench";
export type AppUiSurface = HomeUiSurface;

export const UI_SURFACE_SESSION_KEY = "app-ui-surface-current";

function firstQueryValue(value: unknown): string {
  if (typeof value === "string") return value;
  if (Array.isArray(value) && typeof value[0] === "string") return value[0];
  return "";
}

export function homeModeForSurface(surface: HomeUiSurface | LegacyUiSurface): "query" | "report" {
  return surface === "form" ? "report" : "query";
}

export function resolveHomeUiSurface(
  surfaceValue: unknown,
  legacyHomeModeValue?: unknown
): HomeUiSurface | null {
  const surface = firstQueryValue(surfaceValue);
  if (surface === "form" || surface === "workspace") return surface;
  if (surface === "modern" || surface === "workbench") return "workspace";

  const legacyMode = firstQueryValue(legacyHomeModeValue);
  if (legacyMode === "query") return "workspace";
  if (legacyMode === "report") return "form";
  return null;
}

export function readSessionUiSurface(): HomeUiSurface | null {
  if (typeof window === "undefined") return null;
  try {
    const value = window.sessionStorage.getItem(UI_SURFACE_SESSION_KEY);
    if (value === "form" || value === "workspace") return value;
    if (value === "modern" || value === "workbench") return "workspace";
    return null;
  } catch {
    return null;
  }
}

export function uiSurfaceRouteQuery(surface: HomeUiSurface | LegacyUiSurface): LocationQueryRaw {
  return {
    ui_surface: surface,
    home_mode: homeModeForSurface(surface)
  };
}

export function resolveAppUiSurface(
  _path: string,
  surfaceValue: unknown,
  legacyHomeModeValue: unknown,
  fallback: HomeUiSurface
): AppUiSurface {
  return resolveHomeUiSurface(surfaceValue, legacyHomeModeValue) ?? fallback;
}
