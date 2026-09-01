import type { LocationQuery, LocationQueryRaw } from "vue-router";

export type SearchWorkspaceMode = "fixture" | "model";
export type FixtureSearchMode = "fixture" | "identifier";

export type SearchWorkspaceHandoffState = {
  mode: SearchWorkspaceMode;
  fixtureSearchMode: FixtureSearchMode;
  draftQuery: string;
  committedQuery: string;
  selectedResultId: number | null;
};

function customerQuery(customerId: number | null): LocationQueryRaw {
  return customerId ? { customer: String(customerId) } : {};
}

export function buildReportModeQuery(
  state: SearchWorkspaceHandoffState | null,
  customerId: number | null
): LocationQueryRaw {
  const query: LocationQueryRaw = {
    ui_surface: "form",
    home_mode: "report",
    page: "1",
    ...customerQuery(customerId)
  };
  if (!state) return query;

  const draftQuery = state.draftQuery.trim();
  const committedQuery = state.committedQuery.trim();
  const selectionMatchesVisibleQuery =
    Boolean(state.selectedResultId) &&
    Boolean(committedQuery) &&
    draftQuery === committedQuery;

  if (selectionMatchesVisibleQuery && state.selectedResultId) {
    query[state.mode === "fixture" ? "fixture" : "model"] =
      String(state.selectedResultId);
    return query;
  }

  const keyword = draftQuery || committedQuery;
  if (keyword) query.q = keyword;
  return query;
}

export function buildQueryModeQuery(
  state: SearchWorkspaceHandoffState | null,
  customerId: number | null
): LocationQueryRaw {
  const query: LocationQueryRaw = {
    ui_surface: "modern",
    home_mode: "query",
    ...customerQuery(customerId)
  };
  if (!state) return query;

  query.mode = state.mode;
  if (state.mode === "fixture") query.fixture_search = state.fixtureSearchMode;
  const draftQuery = state.draftQuery.trim();
  const committedQuery = state.committedQuery.trim();
  if (committedQuery) query.q = committedQuery;
  if (draftQuery && draftQuery !== committedQuery) query.query_draft = draftQuery;
  if (committedQuery && state.selectedResultId) {
    query.selected_id = String(state.selectedResultId);
  }
  return query;
}

export function buildWorkbenchQueryModeQuery(
  state: SearchWorkspaceHandoffState | null,
  customerId: number | null,
  surface: "workbench" | "workspace" = "workbench"
): LocationQueryRaw {
  const query: LocationQueryRaw = {
    ui_surface: surface,
    home_mode: "query",
    workbench_mode: state?.mode ?? "fixture",
    ...customerQuery(customerId)
  };
  if (!state) return query;

  if (state.mode === "fixture") query.fixture_search = state.fixtureSearchMode;
  const keyword = state.draftQuery.trim() || state.committedQuery.trim();
  if (keyword) query.q = keyword;
  if (state.committedQuery.trim() && state.selectedResultId) {
    query.selected_id = String(state.selectedResultId);
  }
  return query;
}

function routeQueryString(value: LocationQuery[string]): string {
  return typeof value === "string" ? value : "";
}

export function readWorkbenchQueryModeState(
  query: LocationQuery
): SearchWorkspaceHandoffState | null {
  const requestedMode = routeQueryString(query.workbench_mode);
  if (requestedMode !== "fixture" && requestedMode !== "model") return null;

  const keyword = routeQueryString(query.q);
  const selectedId = Number.parseInt(routeQueryString(query.selected_id), 10);
  return {
    mode: requestedMode,
    fixtureSearchMode: query.fixture_search === "identifier" ? "identifier" : "fixture",
    draftQuery: keyword,
    committedQuery: keyword,
    selectedResultId: Number.isFinite(selectedId) ? selectedId : null
  };
}
