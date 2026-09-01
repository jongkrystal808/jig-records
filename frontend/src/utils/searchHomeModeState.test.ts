import { describe, expect, it } from "vitest";

import {
  buildQueryModeQuery,
  buildReportModeQuery,
  buildWorkbenchQueryModeQuery,
  readWorkbenchQueryModeState,
  type SearchWorkspaceHandoffState
} from "@/utils/searchHomeModeState";

function state(
  overrides: Partial<SearchWorkspaceHandoffState> = {}
): SearchWorkspaceHandoffState {
  return {
    mode: "fixture",
    fixtureSearchMode: "fixture",
    draftQuery: "C-00003",
    committedQuery: "C-00003",
    selectedResultId: 23,
    ...overrides
  };
}

describe("search home mode state", () => {
  it("maps a selected fixture or model to the exact report filter", () => {
    expect(buildReportModeQuery(state(), 2)).toEqual({
      ui_surface: "form",
      home_mode: "report",
      page: "1",
      customer: "2",
      fixture: "23"
    });
    expect(
      buildReportModeQuery(
        state({ mode: "model", selectedResultId: 8, draftQuery: "VPort", committedQuery: "VPort" }),
        2
      )
    ).toEqual({
      ui_surface: "form",
      home_mode: "report",
      page: "1",
      customer: "2",
      model: "8"
    });
  });

  it("uses the visible draft as a report keyword instead of a stale selection", () => {
    expect(
      buildReportModeQuery(state({ draftQuery: "C-00004" }), 2)
    ).toEqual({
      ui_surface: "form",
      home_mode: "report",
      page: "1",
      customer: "2",
      q: "C-00004"
    });
  });

  it("restores the committed query, selection, and newer input draft", () => {
    expect(
      buildQueryModeQuery(state({ draftQuery: "C-00004" }), 2)
    ).toEqual({
      ui_surface: "modern",
      home_mode: "query",
      customer: "2",
      mode: "fixture",
      fixture_search: "fixture",
      q: "C-00003",
      query_draft: "C-00004",
      selected_id: "23"
    });
  });

  it("maps Modern UI search state to the matching Workbench module", () => {
    expect(
      buildWorkbenchQueryModeQuery(
        state({ fixtureSearchMode: "identifier", draftQuery: "2204", committedQuery: "2204" }),
        2
      )
    ).toEqual({
      ui_surface: "workbench",
      home_mode: "query",
      customer: "2",
      workbench_mode: "fixture",
      fixture_search: "identifier",
      q: "2204",
      selected_id: "23"
    });

    expect(
      buildWorkbenchQueryModeQuery(
        state({ mode: "model", draftQuery: "AWK", committedQuery: "AWK" }),
        2
      )
    ).toMatchObject({ workbench_mode: "model", q: "AWK", selected_id: "23" });

    expect(
      buildWorkbenchQueryModeQuery(
        state({ mode: "fixture", draftQuery: "C-00003", committedQuery: "C-00003" }),
        2,
        "workspace"
      )
    ).toMatchObject({ ui_surface: "workspace", home_mode: "query", workbench_mode: "fixture" });
  });

  it("restores a Workbench fixture or model search before switching UI", () => {
    expect(readWorkbenchQueryModeState({
      workbench_mode: "fixture",
      fixture_search: "identifier",
      q: "2204",
      selected_id: "19"
    })).toEqual({
      mode: "fixture",
      fixtureSearchMode: "identifier",
      draftQuery: "2204",
      committedQuery: "2204",
      selectedResultId: 19
    });
    expect(readWorkbenchQueryModeState({ workbench_mode: "management" })).toBeNull();
  });
});
