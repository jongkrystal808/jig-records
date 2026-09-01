// @vitest-environment jsdom

import { computed, ref } from "vue";
import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "@/api";
import { useProductionBatchImport } from "@/composables/useProductionBatchImport";
import { confirmationState, settleConfirmation } from "@/confirmState";
import type { ProductionRequirementBatchRow } from "@/utils/productionBatchImport";

const readyEntity = (kind: "station" | "fixture", code: string, id: number) => ({
  kind,
  label: kind === "station" ? "站點" : "治具",
  inputCode: code,
  resolvedId: id,
  resolvedCode: code,
  suggestedId: null,
  suggestedCode: "",
  status: "ready" as const,
  message: null,
  note: null
});

afterEach(() => {
  vi.restoreAllMocks();
  if (confirmationState.open) settleConfirmation(false);
});

describe("useProductionBatchImport conflict confirmation", () => {
  it("does not replace changed requirements until the user explicitly confirms", async () => {
    vi.spyOn(api, "previewFixtureRequirementsCsv").mockResolvedValue({
      rows: [{
        line: 2,
        model_code: "MODEL-A",
        station_code: "ST-01",
        fixture_code: "FIX-01",
        incoming_required_qty: 4,
        existing_required_qty: 2,
        status: "conflict",
        message: "每站需求量將由 2 取代為 4"
      }],
      new_count: 0,
      unchanged_count: 0,
      conflict_count: 1,
      error_count: 0
    });
    const importRows = vi.spyOn(api, "importFixtureRequirementsCsv").mockResolvedValue({
      imported_count: 1,
      created_count: 0,
      updated_count: 1,
      skipped_count: 0
    });
    const onImported = vi.fn().mockResolvedValue(undefined);
    const batch = useProductionBatchImport({
      models: ref([]),
      stations: ref([]),
      fixtures: ref([]),
      selectedCustomerId: ref(9),
      selectedModelCode: computed(() => "MODEL-A"),
      onImported
    });
    batch.requirementBatchRows.value = [{
      lineNo: 1,
      raw: "ST-01,FIX-01,4",
      station: readyEntity("station", "ST-01", 1),
      fixture: readyEntity("fixture", "FIX-01", 2),
      quantity: 4,
      status: "ready",
      message: null,
      note: null
    } satisfies ProductionRequirementBatchRow];

    const cancelled = batch.submitRequirementBatchImport();
    await vi.waitFor(() => expect(confirmationState.open).toBe(true));
    expect(confirmationState.message).toContain("MODEL-A / ST-01 / FIX-01：2 → 4");
    settleConfirmation(false);
    await cancelled;
    expect(importRows).not.toHaveBeenCalled();

    const confirmed = batch.submitRequirementBatchImport();
    await vi.waitFor(() => expect(confirmationState.open).toBe(true));
    settleConfirmation(true);
    await confirmed;
    expect(importRows).toHaveBeenCalledWith(
      9,
      "model_code,station_code,fixture_code,required_qty\nMODEL-A,ST-01,FIX-01,4",
      "batch-fixture-requirements.csv",
      true
    );
    expect(onImported).toHaveBeenCalledOnce();
  });
});
