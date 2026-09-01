import { computed, ref, watch, type ComputedRef, type Ref } from "vue";

import { requestConfirmation } from "@/confirmState";
import { pushToast } from "@/toastState";
import type { Fixture, MachineModel, Station } from "@/types";
import {
  productionMappingValidationMessage,
  productionRequirementValidationMessage
} from "@/utils/formOperations";

type AutocompleteKey = null | "mapping-model" | "mapping-station" | "requirement-station" | "fixture";

type UseProductionEditorStateOptions = {
  models: Ref<MachineModel[]>;
  stations: Ref<Station[]>;
  fixtures: Ref<Fixture[]>;
  availableRequirementStations: ComputedRef<Station[]>;
  selectedModel: ComputedRef<MachineModel | null>;
  selectedStation: ComputedRef<Station | null>;
};

function normalizeLookupText(value: string): string {
  return value.trim().toLowerCase();
}

function normalizeEditorText(value: string | null | undefined): string {
  return (value ?? "").trim();
}

function filterCodeSuggestions<T extends { code: string }>(rows: T[], keyword: string): T[] {
  const normalized = normalizeLookupText(keyword);
  if (!normalized) return rows.slice(0, 20);
  return rows.filter((row) => row.code.toLowerCase().includes(normalized)).slice(0, 20);
}

function hasExactCodeMatch<T extends { code: string }>(rows: T[], value: string): boolean {
  const normalized = normalizeLookupText(value);
  return !!normalized && rows.some((row) => row.code.toLowerCase() === normalized);
}

function findCodeMatch<T extends { id: number; code: string }>(rows: T[], value: string): T | null {
  const normalized = normalizeLookupText(value);
  if (!normalized) return null;
  const exact = rows.find((row) => row.code.toLowerCase() === normalized);
  if (exact) return exact;
  const startsWithMatches = rows.filter((row) => row.code.toLowerCase().startsWith(normalized));
  if (startsWithMatches.length === 1) return startsWithMatches[0];
  return null;
}

export function useProductionEditorState(options: UseProductionEditorStateOptions) {
  const modelId = ref<number | null>(null);
  const mappingStationId = ref<number | null>(null);
  const requirementStationId = ref<number | null>(null);
  const preferredRequirementStationCode = ref("");
  const fixtureId = ref<number | null>(null);
  const requiredQty = ref(1);
  const designatedMode = ref(false);
  const designatedIdentifiers = ref<string[]>([]);
  const mappingModelCodeInput = ref("");
  const mappingStationCodeInput = ref("");
  const requirementStationCodeInput = ref("");
  const fixtureCodeInput = ref("");
  const editingMappingId = ref<number | null>(null);
  const editingRequirementId = ref<number | null>(null);
  const openAutocompleteKey = ref<AutocompleteKey>(null);

  const mappingEditorBaseline = ref({
    stationCode: ""
  });
  const mappingEditorCurrent = computed(() => ({
    stationCode: normalizeEditorText(mappingStationCodeInput.value)
  }));
  const hasUnsavedMappingChanges = computed(() => JSON.stringify(mappingEditorCurrent.value) !== JSON.stringify(mappingEditorBaseline.value));

  const requirementEditorBaseline = ref({
    fixtureCode: "",
    requiredQty: 1,
    designatedMode: false,
    designatedIdentifiers: [] as string[]
  });
  const requirementEditorCurrent = computed(() => ({
    fixtureCode: normalizeEditorText(fixtureCodeInput.value),
    requiredQty: requiredQty.value,
    designatedMode: designatedMode.value,
    designatedIdentifiers: [...designatedIdentifiers.value].sort()
  }));
  const hasUnsavedRequirementChanges = computed(() => JSON.stringify(requirementEditorCurrent.value) !== JSON.stringify(requirementEditorBaseline.value));

  const filteredModelSuggestions = computed(() => filterCodeSuggestions(options.models.value, mappingModelCodeInput.value));
  const filteredStationSuggestions = computed(() => filterCodeSuggestions(options.stations.value, mappingStationCodeInput.value));
  const filteredRequirementStationSuggestions = computed(() => filterCodeSuggestions(options.availableRequirementStations.value, requirementStationCodeInput.value));
  const filteredFixtureSuggestions = computed(() => filterCodeSuggestions(options.fixtures.value, fixtureCodeInput.value));

  function syncMappingModelSelection(): void {
    const match = findCodeMatch(options.models.value, mappingModelCodeInput.value);
    if (match) modelId.value = match.id;
  }

  function syncMappingStationSelection(): void {
    const match = findCodeMatch(options.stations.value, mappingStationCodeInput.value);
    if (match) mappingStationId.value = match.id;
  }

  function syncRequirementStationInput(): void {
    const match = findCodeMatch(options.availableRequirementStations.value, requirementStationCodeInput.value);
    if (match) requirementStationId.value = match.id;
  }

  function syncFixtureSelection(): void {
    const match = findCodeMatch(options.fixtures.value, fixtureCodeInput.value);
    if (match) {
      if (fixtureId.value !== match.id) designatedIdentifiers.value = [];
      fixtureId.value = match.id;
    }
  }

  function openAutocomplete(key: Exclude<AutocompleteKey, null>, rows: Array<{ code: string }>, value: string): void {
    openAutocompleteKey.value = hasExactCodeMatch(rows, value) ? key : null;
  }

  function showAutocompleteOnInput(key: Exclude<AutocompleteKey, null>): void {
    openAutocompleteKey.value = key;
  }

  function closeAutocompleteSoon(): void {
    window.setTimeout(() => {
      openAutocompleteKey.value = null;
    }, 120);
  }

  function selectModelSuggestion(code: string): void {
    mappingModelCodeInput.value = code;
    syncMappingModelSelection();
    openAutocompleteKey.value = null;
  }

  function selectMappingStationSuggestion(code: string): void {
    mappingStationCodeInput.value = code;
    syncMappingStationSelection();
    openAutocompleteKey.value = null;
  }

  function selectRequirementStationSuggestion(code: string): void {
    requirementStationCodeInput.value = code;
    syncRequirementStationInput();
    openAutocompleteKey.value = null;
  }

  function selectFixtureSuggestion(code: string): void {
    fixtureCodeInput.value = code;
    syncFixtureSelection();
    openAutocompleteKey.value = null;
  }

  function updateModelId(value: number | null): void {
    modelId.value = value;
  }

  function updateSelectedStationId(stationId: number | null): void {
    requirementStationId.value = stationId;
  }

  function updateRequiredQty(value: number): void {
    requiredQty.value = value;
  }

  function updateDesignatedMode(value: boolean): void {
    designatedMode.value = value;
    if (!value) designatedIdentifiers.value = [];
  }

  function updateDesignatedIdentifiers(value: string[]): void {
    designatedIdentifiers.value = [...new Set(value)];
  }

  function openMappingModelAutocomplete(): void {
    openAutocomplete("mapping-model", options.models.value, mappingModelCodeInput.value);
  }

  function handleMappingModelInput(value: string): void {
    mappingModelCodeInput.value = value;
    syncMappingModelSelection();
    showAutocompleteOnInput("mapping-model");
  }

  function blurMappingModelAutocomplete(): void {
    syncMappingModelSelection();
    closeAutocompleteSoon();
  }

  function openMappingStationAutocomplete(): void {
    openAutocomplete("mapping-station", options.stations.value, mappingStationCodeInput.value);
  }

  function handleMappingStationInput(value: string): void {
    mappingStationCodeInput.value = value;
    syncMappingStationSelection();
    showAutocompleteOnInput("mapping-station");
  }

  function blurMappingStationAutocomplete(): void {
    syncMappingStationSelection();
    closeAutocompleteSoon();
  }

  function openRequirementStationAutocomplete(): void {
    openAutocomplete("requirement-station", options.availableRequirementStations.value, requirementStationCodeInput.value);
  }

  function handleRequirementStationInput(value: string): void {
    requirementStationCodeInput.value = value;
    syncRequirementStationInput();
    showAutocompleteOnInput("requirement-station");
  }

  function blurRequirementStationAutocomplete(): void {
    syncRequirementStationInput();
    closeAutocompleteSoon();
  }

  function openFixtureAutocomplete(): void {
    openAutocomplete("fixture", options.fixtures.value, fixtureCodeInput.value);
  }

  function handleFixtureInput(value: string): void {
    fixtureCodeInput.value = value;
    syncFixtureSelection();
    showAutocompleteOnInput("fixture");
  }

  function blurFixtureAutocomplete(): void {
    syncFixtureSelection();
    closeAutocompleteSoon();
  }

  function ensureMappingSelections(): boolean {
    syncMappingModelSelection();
    syncMappingStationSelection();
    const message = productionMappingValidationMessage(modelId.value, mappingStationId.value);
    if (message) {
      pushToast(message, "warning");
      return false;
    }
    return true;
  }

  function ensureRequirementSelections(): boolean {
    syncRequirementStationInput();
    syncFixtureSelection();
    const message = productionRequirementValidationMessage(
      requirementStationId.value,
      fixtureId.value,
      requiredQty.value
    );
    if (message) {
      pushToast(message, "warning");
      return false;
    }
    if (designatedMode.value && designatedIdentifiers.value.length === 0) {
      pushToast("指定模式至少需要選擇一個有庫存的 identifier。", "warning");
      return false;
    }
    return true;
  }

  async function resetMappingEditor(): Promise<boolean> {
    if (
      hasUnsavedMappingChanges.value &&
      !(await requestConfirmation(
        "目前站點設定表單有未儲存的修改，重載後將會捨棄。要繼續嗎？",
        { title: "捨棄站點修改？", confirmLabel: "捨棄並重載", tone: "danger" }
      ))
    ) {
      return false;
    }
    resetMappingEditorWithoutPrompt();
    return true;
  }

  function resetMappingEditorWithoutPrompt(): void {
    editingMappingId.value = null;
    mappingModelCodeInput.value = options.selectedModel.value?.code ?? "";
    mappingStationId.value = null;
    mappingStationCodeInput.value = "";
    mappingEditorBaseline.value = {
      stationCode: ""
    };
  }

  async function resetRequirementEditor(): Promise<boolean> {
    if (
      hasUnsavedRequirementChanges.value &&
      !(await requestConfirmation(
        "目前治具需求表單有未儲存的修改，重載後將會捨棄。要繼續嗎？",
        { title: "捨棄治具需求修改？", confirmLabel: "捨棄並重載", tone: "danger" }
      ))
    ) {
      return false;
    }
    resetRequirementEditorWithoutPrompt();
    return true;
  }

  function resetRequirementEditorWithoutPrompt(): void {
    editingRequirementId.value = null;
    requirementStationCodeInput.value = options.selectedStation.value?.code ?? "";
    fixtureId.value = null;
    fixtureCodeInput.value = "";
    requiredQty.value = 1;
    designatedMode.value = false;
    designatedIdentifiers.value = [];
    requirementEditorBaseline.value = {
      fixtureCode: "",
      requiredQty: 1,
      designatedMode: false,
      designatedIdentifiers: []
    };
  }

  async function startEditMapping(row: { id: number; model_id: number; station_id: number }): Promise<boolean> {
    if (
      editingMappingId.value !== row.id &&
      hasUnsavedMappingChanges.value &&
      !(await requestConfirmation(
        "目前站點設定表單有未儲存的修改，切換編輯對象後將會捨棄。要繼續嗎？",
        { title: "切換站點編輯？", confirmLabel: "切換並捨棄", tone: "danger" }
      ))
    ) {
      return false;
    }
    modelId.value = row.model_id;
    mappingStationId.value = row.station_id;
    mappingModelCodeInput.value = options.models.value.find((item) => item.id === row.model_id)?.code ?? "";
    mappingStationCodeInput.value = options.stations.value.find((item) => item.id === row.station_id)?.code ?? "";
    editingMappingId.value = row.id;
    mappingEditorBaseline.value = {
      stationCode: normalizeEditorText(mappingStationCodeInput.value)
    };
    return true;
  }

  async function startEditRequirement(row: { id: number; station_id: number; fixture_id: number; required_qty: number; designated_mode?: boolean; designated_identifiers?: string[] }): Promise<boolean> {
    if (
      editingRequirementId.value !== row.id &&
      hasUnsavedRequirementChanges.value &&
      !(await requestConfirmation(
        "目前治具需求表單有未儲存的修改，切換編輯對象後將會捨棄。要繼續嗎？",
        { title: "切換治具需求編輯？", confirmLabel: "切換並捨棄", tone: "danger" }
      ))
    ) {
      return false;
    }
    requirementStationId.value = row.station_id;
    fixtureId.value = row.fixture_id;
    requiredQty.value = row.required_qty;
    designatedMode.value = row.designated_mode ?? false;
    designatedIdentifiers.value = [...(row.designated_identifiers ?? [])];
    requirementStationCodeInput.value =
      options.availableRequirementStations.value.find((item) => item.id === row.station_id)?.code ??
      options.stations.value.find((item) => item.id === row.station_id)?.code ??
      "";
    fixtureCodeInput.value = options.fixtures.value.find((item) => item.id === row.fixture_id)?.code ?? "";
    editingRequirementId.value = row.id;
    requirementEditorBaseline.value = {
      fixtureCode: normalizeEditorText(fixtureCodeInput.value),
      requiredQty: row.required_qty,
      designatedMode: row.designated_mode ?? false,
      designatedIdentifiers: [...(row.designated_identifiers ?? [])].sort()
    };
    return true;
  }

  function syncRequirementStationSelection(): void {
    const availableStations = options.availableRequirementStations.value;
    const availableStationIds = new Set(availableStations.map((row) => row.id));
    if (!availableStationIds.size) {
      requirementStationId.value = null;
      return;
    }

    if (requirementStationId.value !== null && availableStationIds.has(requirementStationId.value)) {
      return;
    }

    const preferredCode = normalizeLookupText(preferredRequirementStationCode.value);
    if (preferredCode) {
      const matchedStation = availableStations.find((row) => normalizeLookupText(row.code) === preferredCode);
      if (matchedStation) {
        requirementStationId.value = matchedStation.id;
        return;
      }
    }

    requirementStationId.value = availableStations[0]?.id ?? null;
  }

  function hasValidRequirementStationSelection(): boolean {
    if (modelId.value === null || requirementStationId.value === null) {
      return false;
    }
    return options.availableRequirementStations.value.some((row) => row.id === requirementStationId.value);
  }

  watch(modelId, (value) => {
    mappingModelCodeInput.value = options.models.value.find((row) => row.id === value)?.code ?? "";
  });

  watch(mappingStationId, (value) => {
    mappingStationCodeInput.value = options.stations.value.find((row) => row.id === value)?.code ?? "";
  });

  watch(requirementStationId, (value) => {
    const selectedCode =
      options.availableRequirementStations.value.find((row) => row.id === value)?.code ??
      options.stations.value.find((row) => row.id === value)?.code ??
      "";
    requirementStationCodeInput.value = selectedCode;
    if (selectedCode) {
      preferredRequirementStationCode.value = selectedCode;
    }
  });

  watch(fixtureId, (value) => {
    fixtureCodeInput.value = options.fixtures.value.find((row) => row.id === value)?.code ?? "";
  });

  return {
    modelId,
    mappingStationId,
    requirementStationId,
    preferredRequirementStationCode,
    fixtureId,
    requiredQty,
    designatedMode,
    designatedIdentifiers,
    mappingModelCodeInput,
    mappingStationCodeInput,
    requirementStationCodeInput,
    fixtureCodeInput,
    editingMappingId,
    editingRequirementId,
    openAutocompleteKey,
    filteredModelSuggestions,
    filteredStationSuggestions,
    filteredRequirementStationSuggestions,
    filteredFixtureSuggestions,
    hasUnsavedMappingChanges,
    hasUnsavedRequirementChanges,
    updateModelId,
    updateSelectedStationId,
    updateRequiredQty,
    updateDesignatedMode,
    updateDesignatedIdentifiers,
    openMappingModelAutocomplete,
    handleMappingModelInput,
    blurMappingModelAutocomplete,
    selectModelSuggestion,
    openMappingStationAutocomplete,
    handleMappingStationInput,
    blurMappingStationAutocomplete,
    selectMappingStationSuggestion,
    openRequirementStationAutocomplete,
    handleRequirementStationInput,
    blurRequirementStationAutocomplete,
    selectRequirementStationSuggestion,
    openFixtureAutocomplete,
    handleFixtureInput,
    blurFixtureAutocomplete,
    selectFixtureSuggestion,
    ensureMappingSelections,
    ensureRequirementSelections,
    resetMappingEditor,
    resetMappingEditorWithoutPrompt,
    resetRequirementEditor,
    resetRequirementEditorWithoutPrompt,
    startEditMapping,
    startEditRequirement,
    syncRequirementStationSelection,
    hasValidRequirementStationSelection
  };
}
