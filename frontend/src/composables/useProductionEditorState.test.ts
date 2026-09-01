// @vitest-environment jsdom

import { computed, nextTick, ref } from "vue";
import { afterEach, describe, expect, it } from "vitest";

import { useProductionEditorState } from "@/composables/useProductionEditorState";
import { toasts } from "@/toastState";
import type { Fixture, MachineModel, Station } from "@/types";

function createEditorState() {
  const models = ref<MachineModel[]>([
    { id: 1, customer_id: 1, code: "MODEL-A", name: "Model A", is_active: true },
    { id: 2, customer_id: 1, code: "MODEL-B", name: "Model B", is_active: true }
  ]);
  const stations = ref<Station[]>([
    { id: 10, customer_id: 1, code: "ST-01", name: "Station 1", is_active: true },
    { id: 20, customer_id: 1, code: "ST-02", name: "Station 2", is_active: true }
  ]);
  const fixtures = ref<Fixture[]>([
    {
      id: 100,
      customer_id: 1,
      responsible_user_id: null,
      code: "FX-01",
      name: "Fixture 1",
      line_storage_location: null,
      department_storage_location: null,
      description: null,
      is_active: true,
      min_stock_qty: 0,
      has_image: false
    }
  ]);
  const selectedModelId = ref<number | null>(1);
  const selectedStationId = ref<number | null>(10);
  const availableRequirementStations = computed(() => stations.value);
  const selectedModel = computed(
    () => models.value.find((row) => row.id === selectedModelId.value) ?? null
  );
  const selectedStation = computed(
    () => stations.value.find((row) => row.id === selectedStationId.value) ?? null
  );
  const state = useProductionEditorState({
    models,
    stations,
    fixtures,
    availableRequirementStations,
    selectedModel,
    selectedStation
  });
  return { state, selectedModelId, selectedStationId };
}

describe("useProductionEditorState dirty tracking", () => {
  afterEach(() => {
    toasts.value = [];
  });

  it("does not treat inherited model or station context as a user edit", async () => {
    const { state, selectedModelId, selectedStationId } = createEditorState();
    state.updateModelId(1);
    state.updateSelectedStationId(10);
    state.resetMappingEditorWithoutPrompt();
    state.resetRequirementEditorWithoutPrompt();

    selectedStationId.value = 20;
    state.updateSelectedStationId(20);
    selectedModelId.value = 2;
    state.updateModelId(2);
    await nextTick();

    expect(state.hasUnsavedMappingChanges.value).toBe(false);
    expect(state.hasUnsavedRequirementChanges.value).toBe(false);
  });

  it("still detects edits to fields the operator can save", () => {
    const { state } = createEditorState();
    state.updateModelId(1);
    state.updateSelectedStationId(10);
    state.resetMappingEditorWithoutPrompt();
    state.resetRequirementEditorWithoutPrompt();

    state.handleMappingStationInput("ST-02");
    expect(state.hasUnsavedMappingChanges.value).toBe(true);

    state.resetMappingEditorWithoutPrompt();
    state.handleFixtureInput("FX-01");
    expect(state.hasUnsavedRequirementChanges.value).toBe(true);
  });

  it("uses the shared production validation before saving a requirement", () => {
    const { state } = createEditorState();
    state.handleRequirementStationInput("ST-01");
    state.handleFixtureInput("FX-01");
    state.updateRequiredQty(0);

    expect(state.ensureRequirementSelections()).toBe(false);
    expect(toasts.value.at(-1)).toMatchObject({ message: "需求數量必須大於 0。", tone: "warning" });
  });

  it("requires at least one identifier when designated mode is enabled", () => {
    const { state } = createEditorState();
    state.handleRequirementStationInput("ST-01");
    state.handleFixtureInput("FX-01");
    state.updateRequiredQty(1);
    state.updateDesignatedMode(true);

    expect(state.ensureRequirementSelections()).toBe(false);
    expect(toasts.value.at(-1)).toMatchObject({
      message: "指定模式至少需要選擇一個有庫存的 identifier。",
      tone: "warning"
    });
  });
});
