<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "@/api";
import { globalFixtureKeyword, selectedCustomerId } from "@/appState";
import ProductionBatchImportModal from "@/components/production/ProductionBatchImportModal.vue";
import ProductionDetailSection from "@/components/production/ProductionDetailSection.vue";
import ProductionHeaderSection from "@/components/production/ProductionHeaderSection.vue";
import { useProductionBatchImport } from "@/composables/useProductionBatchImport";
import { useProductionEditorState } from "@/composables/useProductionEditorState";
import { pushToast } from "@/toastState";
import type { Fixture, FixtureRequirementListItem, MachineModel, ModelQuery, ModelQueryStationRequirement, ModelStation, Station, StationCapacity } from "@/types";
import { formatLocalDate } from "@/utils/date";
import { matchesFixtureKeywords, parseFixtureKeywords } from "@/utils/fixtureSearch";
import ProductionCapacityPanel from "@/components/production/ProductionCapacityPanel.vue";

const route = useRoute();
const router = useRouter();

const models = ref<MachineModel[]>([]);
const stations = ref<Station[]>([]);
const fixtures = ref<Fixture[]>([]);
const mappings = ref<ModelStation[]>([]);
const fixtureRequirements = ref<FixtureRequirementListItem[]>([]);
const modelQuery = ref<ModelQuery | null>(null);
const stationCapacity = ref<StationCapacity | null>(null);

const loading = ref(false);
const loadedAt = ref("");
const updatedAt = ref("");
const bottleneckHighlightTrigger = ref(0);

function nowString(): string {
  return formatLocalDate(new Date());
}

function touchUpdatedAt(): void {
  updatedAt.value = nowString();
}

const selectedModel = computed(() => models.value.find((row) => row.id === modelId.value) ?? null);
const selectedStation = computed(() => stations.value.find((row) => row.id === requirementStationId.value) ?? null);
const selectedModelCode = computed(() => selectedModel.value?.code ?? "");
const modelMap = computed(() => new Map(models.value.map((row) => [row.id, row.code])));
const stationMap = computed(() => new Map(stations.value.map((row) => [row.id, row.code])));
const globalFixtureKeywords = computed(() => parseFixtureKeywords(globalFixtureKeyword.value));
const mappingRows = computed(() =>
  mappings.value.map((row) => ({
    id: row.id,
    model_id: row.model_id,
    modelCode: modelMap.value.get(row.model_id) ?? `model ${row.model_id}`,
    station_id: row.station_id,
    stationCode: stationMap.value.get(row.station_id) ?? `station ${row.station_id}`
  }))
);
const selectedModelStationRows = computed(() => mappingRows.value.filter((row) => row.model_id === modelId.value));
const selectedModelStationIds = computed(() => new Set(selectedModelStationRows.value.map((row) => row.station_id)));
const availableRequirementStations = computed(() =>
  stations.value
    .filter((row) => selectedModelStationIds.value.has(row.id))
    .slice()
    .sort((a, b) => a.code.localeCompare(b.code))
);
const selectedStationId = computed(() => requirementStationId.value);
const selectedStationCode = computed(() => selectedStation.value?.code ?? "");
const selectedStationRequirementRows = computed(() =>
  fixtureRequirements.value.filter(
    (row) =>
      row.model_id === modelId.value &&
      row.station_id === requirementStationId.value &&
      matchesFixtureKeywords(row.fixture_code, globalFixtureKeywords.value)
  )
);
const selectedStationQueryRows = computed<ModelQueryStationRequirement[]>(() => {
  if (!modelQuery.value || requirementStationId.value === null) {
    return [];
  }
  return modelQuery.value.station_requirements.filter(
    (row) =>
      row.station_id === requirementStationId.value &&
      matchesFixtureKeywords(row.fixture_code, globalFixtureKeywords.value)
  );
});
const currentStationHasBottleneck = computed(() => selectedStationQueryRows.value.some((row) => row.stock_status !== "normal"));
const stationConstraintTitle = computed(() => (currentStationHasBottleneck.value ? "瓶頸治具" : "目前限制治具"));
const stationConstraintHint = computed(() => {
  if (!stationCapacity.value?.bottleneck_fixture_code) {
    return "目前沒有可顯示的限制治具";
  }
  return currentStationHasBottleneck.value ? "點一下，定位到下方證據列" : "目前無瓶頸，治具供應充足";
});
const displayedModelQuery = computed(() => {
  if (!modelQuery.value || globalFixtureKeywords.value.length === 0) {
    return modelQuery.value;
  }
  return {
    ...modelQuery.value,
    fixtures: modelQuery.value.fixtures.filter((row) => matchesFixtureKeywords(row.fixture_code, globalFixtureKeywords.value))
  };
});
const detailMode = computed<"overview" | "mapping" | "requirements">(() => {
  if (route.name === "production-mapping") return "mapping";
  if (route.name === "production-requirements") return "requirements";
  return "overview";
});
const isMainOverview = computed(() => detailMode.value === "overview");
const detailPanelMode = computed<"mapping" | "requirements">(() => (detailMode.value === "requirements" ? "requirements" : "mapping"));
const mappingSummaryText = computed(() => {
  const currentModelCode = selectedModel.value?.code || "-";
  return `目前機種：${currentModelCode} / ${selectedModelStationRows.value.length} 筆站點`;
});
const requirementSummaryText = computed(() => {
  const currentStationCode = selectedStation.value?.code || "-";
  return `目前站點：${currentStationCode} / ${selectedStationRequirementRows.value.length} 筆治具`;
});
const requirementNeedsMapping = computed(() => selectedModelStationRows.value.length === 0);

const {
  modelId,
  mappingStationId,
  requirementStationId,
  fixtureId,
  requiredQty,
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
} = useProductionEditorState({
  models,
  stations,
  fixtures,
  availableRequirementStations,
  selectedModel,
  selectedStation
});

const {
  showMappingBatchModal,
  showRequirementBatchModal,
  mappingBatchText,
  requirementBatchText,
  mappingBatchRows,
  requirementBatchRows,
  mappingReadyRows,
  mappingPendingRows,
  mappingErrorRows,
  requirementReadyRows,
  requirementPendingRows,
  requirementErrorRows,
  savingMapping,
  savingRequirement,
  clearMappingBatchImport,
  clearRequirementBatchImport,
  skipMappingBatchRow,
  skipRequirementBatchRow,
  acceptSimilarEntity,
  rejectSimilarEntity,
  createEntityForBatch,
  syncMappingRowAfterEntityChange,
  syncRequirementRowAfterEntityChange,
  submitMappingBatchImport,
  submitRequirementBatchImport
} = useProductionBatchImport({
  models,
  stations,
  fixtures,
  selectedCustomerId,
  selectedModelCode,
  onImported: async () => {
    await loadData(false);
    await Promise.all([refreshCapacity(), refreshModelQuery()]);
  }
});

function parseRouteModelId(): number | null {
  const raw = Array.isArray(route.query.model_id) ? route.query.model_id[0] : route.query.model_id;
  if (typeof raw !== "string" || raw.trim().length === 0) {
    return null;
  }
  const parsed = Number.parseInt(raw, 10);
  return Number.isFinite(parsed) ? parsed : null;
}

function applyRouteModelSelection(): void {
  const routeModelId = parseRouteModelId();
  if (routeModelId === null) {
    return;
  }
  const match = models.value.find((row) => row.id === routeModelId);
  if (match) {
    modelId.value = match.id;
  }
}

function openMappingPage(): void {
  if (detailMode.value !== "mapping" && hasUnsavedRequirementChanges.value && !window.confirm("目前 Requirement 表單有未儲存的修改，切換到 Mapping 後將會捨棄。要繼續嗎？")) {
    return;
  }
  router.push({ name: "production-mapping" });
}

function openRequirementPage(): void {
  if (detailMode.value !== "requirements" && hasUnsavedMappingChanges.value && !window.confirm("目前 Mapping 表單有未儲存的修改，切換到 Requirement 後將會捨棄。要繼續嗎？")) {
    return;
  }
  router.push({ name: "production-requirements" });
}

function closeDetailPage(): void {
  router.push({ name: "production" });
}

function focusBottleneckEvidence(): void {
  if (!stationCapacity.value?.bottleneck_fixture_code || !currentStationHasBottleneck.value) {
    return;
  }
  bottleneckHighlightTrigger.value += 1;
}

function downloadCsv(filename: string, content: string): void {
  const blob = new Blob(["\ufeff", content], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}


async function loadData(showLoading = true): Promise<void> {
  if (showLoading) {
    loading.value = true;
  }
  try {
    modelQuery.value = null;
    stationCapacity.value = null;
    const customerId = selectedCustomerId.value ?? undefined;
    const [modelRows, stationRows, fixtureRows, mappingRows, requirementRows] = await Promise.all([
      customerId ? api.listModels(customerId) : Promise.resolve([]),
      customerId ? api.listStations(customerId) : Promise.resolve([]),
      api.listFixtures(customerId),
      customerId ? api.listModelStations(customerId) : Promise.resolve([]),
      customerId ? api.listFixtureRequirements(customerId) : Promise.resolve([])
    ]);
    models.value = modelRows;
    stations.value = stationRows;
    fixtures.value = fixtureRows;
    mappings.value = mappingRows;
    fixtureRequirements.value = requirementRows;

    modelId.value = modelRows.find((row) => row.id === modelId.value)?.id ?? modelRows[0]?.id ?? null;
    applyRouteModelSelection();
    mappingStationId.value = stationRows.find((row) => row.id === mappingStationId.value)?.id ?? stationRows[0]?.id ?? null;
    fixtureId.value = fixtureRows.find((row) => row.id === fixtureId.value)?.id ?? fixtureRows[0]?.id ?? null;
    syncRequirementStationSelection();
    if (editingMappingId.value !== null && !mappingRows.some((row) => row.id === editingMappingId.value)) {
      resetMappingEditorWithoutPrompt();
    }
    if (editingRequirementId.value !== null && !requirementRows.some((row) => row.id === editingRequirementId.value)) {
      resetRequirementEditorWithoutPrompt();
    }

    if (!loadedAt.value) loadedAt.value = nowString();
    touchUpdatedAt();
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "載入失敗", "error");
  } finally {
    if (showLoading) {
      loading.value = false;
    }
  }
}

async function saveMapping(): Promise<void> {
  if (!ensureMappingSelections()) return;
  savingMapping.value = true;
  try {
    if (!selectedCustomerId.value) {
      pushToast("請先選擇客戶。", "warning");
      return;
    }
    const currentModelId = modelId.value as number;
    const currentStationId = mappingStationId.value as number;
    const payload = { customer_id: selectedCustomerId.value, model_id: currentModelId, station_id: currentStationId };
    if (editingMappingId.value === null) {
      await api.createModelStation(payload);
      pushToast("Model-Station Mapping 已新增", "success");
    } else {
      await api.updateModelStation(editingMappingId.value, payload);
      resetMappingEditorWithoutPrompt();
      pushToast("Model-Station Mapping 已更新", "success");
    }
    await loadData(false);
    await Promise.all([refreshCapacity(), refreshModelQuery()]);
  } catch (err) {
    pushToast(err instanceof Error ? err.message : editingMappingId.value === null ? "新增 mapping 失敗" : "更新 mapping 失敗", "error");
  } finally {
    savingMapping.value = false;
  }
}

async function removeMapping(rowId: number): Promise<void> {
  if (!selectedCustomerId.value) {
    pushToast("請先選擇客戶。", "warning");
    return;
  }
  if (!window.confirm("確定要刪除這筆機種站點對應嗎？")) return;
  try {
    await api.deleteModelStation(rowId, selectedCustomerId.value);
    if (editingMappingId.value === rowId) resetMappingEditorWithoutPrompt();
    await loadData(false);
    await Promise.all([refreshCapacity(), refreshModelQuery()]);
    pushToast("Mapping 已刪除", "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "刪除 mapping 失敗", "error");
  }
}

async function saveRequirement(): Promise<void> {
  if (!ensureRequirementSelections()) return;
  savingRequirement.value = true;
  try {
    if (!selectedCustomerId.value) {
      pushToast("請先選擇客戶。", "warning");
      return;
    }
    const currentModelId = modelId.value;
    if (currentModelId === null) {
      pushToast("請先選擇機種。", "warning");
      return;
    }
    if (!hasValidRequirementStationSelection()) {
      pushToast("請先替目前機種建立站點對應，再設定該站點的治具需求。", "warning");
      return;
    }
    const currentStationId = requirementStationId.value as number;
    const currentFixtureId = fixtureId.value as number;
    const payload = {
      customer_id: selectedCustomerId.value,
      model_id: currentModelId,
      station_id: currentStationId,
      fixture_id: currentFixtureId,
      required_qty: requiredQty.value
    };
    if (editingRequirementId.value === null) {
      await api.createFixtureRequirement(payload);
      pushToast("Fixture Requirement 已儲存", "success");
    } else {
      await api.updateFixtureRequirement(editingRequirementId.value, payload);
      resetRequirementEditorWithoutPrompt();
      pushToast("Fixture Requirement 已更新", "success");
    }
    await loadData(false);
    await Promise.all([refreshCapacity(), refreshModelQuery()]);
    touchUpdatedAt();
  } catch (err) {
    pushToast(err instanceof Error ? err.message : editingRequirementId.value === null ? "儲存 requirement 失敗" : "更新 requirement 失敗", "error");
  } finally {
    savingRequirement.value = false;
  }
}

async function removeRequirement(requirementId: number): Promise<void> {
  if (!selectedCustomerId.value) {
    pushToast("請先選擇客戶。", "warning");
    return;
  }
  if (!window.confirm("確定要刪除這筆站點治具需求嗎？")) return;
  try {
    await api.deleteFixtureRequirement(requirementId, selectedCustomerId.value);
    if (editingRequirementId.value === requirementId) resetRequirementEditorWithoutPrompt();
    await loadData(false);
    await Promise.all([refreshCapacity(), refreshModelQuery()]);
    pushToast("Requirement 已刪除", "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "刪除 requirement 失敗", "error");
  }
}

async function refreshCapacity(): Promise<void> {
  if (!hasValidRequirementStationSelection()) {
    stationCapacity.value = null;
    return;
  }
  try {
    stationCapacity.value = await api.getStationCapacity(
      requirementStationId.value!,
      modelId.value!,
      selectedCustomerId.value ?? undefined
    );
    touchUpdatedAt();
  } catch (err) {
    stationCapacity.value = null;
    pushToast(err instanceof Error ? err.message : "刷新 capacity 失敗", "error");
  }
}

async function refreshModelQuery(): Promise<void> {
  if (modelId.value === null) {
    modelQuery.value = null;
    return;
  }
  try {
    modelQuery.value = await api.getModelQuery(
      modelId.value!,
      undefined,
      selectedCustomerId.value ?? undefined
    );
    touchUpdatedAt();
  } catch (err) {
    modelQuery.value = null;
    pushToast(err instanceof Error ? err.message : "刷新 model query 失敗", "error");
  }
}

async function exportModelStationsCsv(): Promise<void> {
  try {
    if (!selectedCustomerId.value) {
      pushToast("請先選擇客戶。", "warning");
      return;
    }
    downloadCsv("model-stations.csv", await api.exportModelStationsCsv(selectedCustomerId.value ?? undefined));
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "匯出 mapping 失敗", "error");
  }
}

async function downloadModelStationTemplate(): Promise<void> {
  try {
    downloadCsv("model-stations-template.csv", await api.downloadModelStationTemplateCsv());
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "下載 mapping 範本失敗", "error");
  }
}

async function importModelStationsCsv(source: Event | File): Promise<void> {
  const input = source instanceof File ? null : (source.target as HTMLInputElement | null);
  const file = source instanceof File ? source : (input?.files?.[0] ?? null);
  if (!file) return;
  try {
    if (!selectedCustomerId.value) {
      pushToast("請先選擇客戶。", "warning");
      return;
    }
    const result = await api.importModelStationsCsv(selectedCustomerId.value ?? undefined, await file.text(), file.name);
    await loadData(false);
    pushToast(`匯入 mapping 完成，共 ${result.imported_count} 筆。`, "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "匯入 mapping 失敗", "error");
  } finally {
    if (input) {
      input.value = "";
    }
  }
}

async function exportFixtureRequirementsCsv(): Promise<void> {
  try {
    if (!selectedCustomerId.value) {
      pushToast("請先選擇客戶。", "warning");
      return;
    }
    downloadCsv("fixture-requirements.csv", await api.exportFixtureRequirementsCsv(selectedCustomerId.value ?? undefined));
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "匯出 requirement 失敗", "error");
  }
}

async function downloadFixtureRequirementTemplate(): Promise<void> {
  try {
    downloadCsv("fixture-requirements-template.csv", await api.downloadFixtureRequirementTemplateCsv());
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "下載 requirement 範本失敗", "error");
  }
}

async function importFixtureRequirementsCsv(source: Event | File): Promise<void> {
  const input = source instanceof File ? null : (source.target as HTMLInputElement | null);
  const file = source instanceof File ? source : (input?.files?.[0] ?? null);
  if (!file) return;
  try {
    if (!selectedCustomerId.value) {
      pushToast("請先選擇客戶。", "warning");
      return;
    }
    const result = await api.importFixtureRequirementsCsv(selectedCustomerId.value ?? undefined, await file.text(), file.name);
    await loadData(false);
    await Promise.all([refreshCapacity(), refreshModelQuery()]);
    pushToast(`匯入 requirement 完成，共 ${result.imported_count} 筆。`, "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "匯入 requirement 失敗", "error");
  } finally {
    if (input) {
      input.value = "";
    }
  }
}

watch(
  [modelId, availableRequirementStations],
  async () => {
    syncRequirementStationSelection();
    await refreshCapacity();
    await refreshModelQuery();
  },
  { flush: "post" }
);

watch(
  requirementStationId,
  async () => {
    await refreshCapacity();
    await refreshModelQuery();
  },
  { flush: "post" }
);

watch(selectedCustomerId, async () => {
  await loadData();
  await Promise.all([refreshCapacity(), refreshModelQuery()]);
});

watch(
  () => route.query.model_id,
  async () => {
    applyRouteModelSelection();
    await Promise.all([refreshCapacity(), refreshModelQuery()]);
  }
);

onMounted(async () => {
  await loadData();
  await Promise.all([refreshCapacity(), refreshModelQuery()]);
});
</script>

<template>
  <div class="production-page">
    <ProductionHeaderSection
      :models="models"
      :model-id="modelId"
      :loading="loading"
      :saving-mapping="savingMapping"
      :loaded-at="loadedAt"
      :updated-at="updatedAt"
      :station-capacity="stationCapacity"
      :current-station-has-bottleneck="currentStationHasBottleneck"
      :station-constraint-title="stationConstraintTitle"
      :station-constraint-hint="stationConstraintHint"
      :is-main-overview="isMainOverview"
      :detail-mode="detailMode"
      @back="router.push({ name: 'search' })"
      @open-overview="closeDetailPage"
      @open-mapping="openMappingPage"
      @open-requirements="openRequirementPage"
      @focus-bottleneck="focusBottleneckEvidence"
      @update:model-id="updateModelId"
    />

    <section v-if="isMainOverview" class="top-grid">
      <ProductionCapacityPanel
        class="overview-capacity-panel"
        :loading="loading"
        :selected-model-code="selectedModel?.code || ''"
        :selected-station-code="selectedStation?.code || ''"
        :selected-station-id="requirementStationId"
        :station-capacity="stationCapacity"
        :model-query="displayedModelQuery"
        :selected-station-query-rows="selectedStationQueryRows"
        :highlight-fixture-code="stationCapacity?.bottleneck_fixture_code || ''"
        :highlight-trigger="bottleneckHighlightTrigger"
        @refresh-capacity="refreshCapacity"
        @refresh-model-query="refreshModelQuery"
        @update:selected-station-id="updateSelectedStationId"
      />
    </section>

    <ProductionDetailSection
      v-else
      :detail-mode="detailPanelMode"
      :loading="loading"
      :saving-mapping="savingMapping"
      :saving-requirement="savingRequirement"
      :editing-mapping-id="editingMappingId"
      :editing-requirement-id="editingRequirementId"
      :selected-model-code="selectedModel?.code || ''"
      :selected-station-code="selectedStationCode"
      :selected-model-station-rows="selectedModelStationRows"
      :selected-station-requirement-rows="selectedStationRequirementRows"
      :requirement-needs-mapping="requirementNeedsMapping"
      :mapping-model-code-input="mappingModelCodeInput"
      :mapping-station-code-input="mappingStationCodeInput"
      :requirement-station-code-input="requirementStationCodeInput"
      :fixture-code-input="fixtureCodeInput"
      :required-qty="requiredQty"
      :open-autocomplete-key="openAutocompleteKey"
      :filtered-model-suggestions="filteredModelSuggestions"
      :filtered-station-suggestions="filteredStationSuggestions"
      :filtered-requirement-station-suggestions="filteredRequirementStationSuggestions"
      :filtered-fixture-suggestions="filteredFixtureSuggestions"
      :models="models"
      :stations="stations"
      :available-requirement-stations="availableRequirementStations"
      :fixtures="fixtures"
      :on-open-mapping-batch-modal="() => (showMappingBatchModal = true)"
      :on-open-requirement-batch-modal="() => (showRequirementBatchModal = true)"
      :on-import-model-stations-csv="importModelStationsCsv"
      :on-import-fixture-requirements-csv="importFixtureRequirementsCsv"
      :on-save-mapping="saveMapping"
      :on-reset-mapping-editor="resetMappingEditor"
      :on-start-edit-mapping="startEditMapping"
      :on-remove-mapping="removeMapping"
      :on-save-requirement="saveRequirement"
      :on-reset-requirement-editor="resetRequirementEditor"
      :on-start-edit-requirement="startEditRequirement"
      :on-remove-requirement="removeRequirement"
      :on-open-mapping-page="openMappingPage"
      :on-mapping-model-focus="openMappingModelAutocomplete"
      :on-mapping-model-input="handleMappingModelInput"
      :on-mapping-model-blur="blurMappingModelAutocomplete"
      :on-select-model-suggestion="selectModelSuggestion"
      :on-mapping-station-focus="openMappingStationAutocomplete"
      :on-mapping-station-input="handleMappingStationInput"
      :on-mapping-station-blur="blurMappingStationAutocomplete"
      :on-select-mapping-station-suggestion="selectMappingStationSuggestion"
      :on-requirement-station-focus="openRequirementStationAutocomplete"
      :on-requirement-station-input="handleRequirementStationInput"
      :on-requirement-station-blur="blurRequirementStationAutocomplete"
      :on-select-requirement-station-suggestion="selectRequirementStationSuggestion"
      :on-fixture-focus="openFixtureAutocomplete"
      :on-fixture-input="handleFixtureInput"
      :on-fixture-blur="blurFixtureAutocomplete"
      :on-select-fixture-suggestion="selectFixtureSuggestion"
      :on-required-qty-change="updateRequiredQty"
    />

    <ProductionBatchImportModal
      :open="showMappingBatchModal"
      title="批次貼上匯入 Model-Station Mapping"
      description="每行一筆：`機種編號,站點編號`。若找不到會先比對相似資料，再讓你確認、替換或新增。"
      :text="mappingBatchText"
      placeholder="例如：&#10;EDS,EDS_T1&#10;EDS,EDS_T2"
      :saving="savingMapping"
      submit-label="匯入 Mapping"
      :ready-count="mappingReadyRows.length"
      :pending-count="mappingPendingRows.length"
      :error-count="mappingErrorRows.length"
      @close="showMappingBatchModal = false"
      @clear="clearMappingBatchImport"
      @submit="submitMappingBatchImport"
      @update:text="mappingBatchText = $event"
    >
      <table class="mapping-table batch-preview-table">
              <thead>
                <tr>
                  <th>行</th>
                  <th>原始機種</th>
                  <th>使用機種</th>
                  <th>原始站點</th>
                  <th>使用站點</th>
                  <th>狀態 / 操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in mappingBatchRows" :key="`mapping-batch-${row.lineNo}-${row.raw}`">
                  <td>{{ row.lineNo }}</td>
                  <td>{{ row.model.inputCode || "-" }}</td>
                  <td>{{ row.model.resolvedCode || row.model.suggestedCode || "-" }}</td>
                  <td>{{ row.station.inputCode || "-" }}</td>
                  <td>{{ row.station.resolvedCode || row.station.suggestedCode || "-" }}</td>
                  <td>
                    <div class="batch-cell-stack">
                      <span v-if="row.status === 'ready'" class="batch-status ready">已確認</span>
                      <span v-else-if="row.status === 'needs-confirm'" class="batch-status warn">待確認</span>
                      <span v-else-if="row.status === 'needs-add'" class="batch-status warn">待新增</span>
                      <span v-else-if="row.status === 'skipped'" class="batch-status muted">已跳過</span>
                      <span v-else class="batch-status error">錯誤</span>
                      <span v-if="row.message || row.note" class="batch-row-note">{{ row.message || row.note }}</span>
                      <div class="batch-row-actions">
                        <template v-if="row.model.status === 'needs-confirm'">
                          <button class="ghost-btn batch-action-btn" type="button" @click="acceptSimilarEntity(row.model); syncMappingRowAfterEntityChange(row)">機種同一</button>
                          <button class="primary-btn batch-action-btn" type="button" @click="rejectSimilarEntity(row.model); syncMappingRowAfterEntityChange(row)">新增機種</button>
                          <button class="ghost-btn batch-action-btn" type="button" @click="skipMappingBatchRow(row)">略過</button>
                        </template>
                        <template v-else-if="row.model.status === 'needs-add'">
                          <button class="primary-btn batch-action-btn" type="button" @click="createEntityForBatch(row.model).then(() => syncMappingRowAfterEntityChange(row))">新增機種</button>
                          <button class="ghost-btn batch-action-btn" type="button" @click="skipMappingBatchRow(row)">略過</button>
                        </template>
                        <template v-else-if="row.station.status === 'needs-confirm'">
                          <button class="ghost-btn batch-action-btn" type="button" @click="acceptSimilarEntity(row.station); syncMappingRowAfterEntityChange(row)">站點同一</button>
                          <button class="primary-btn batch-action-btn" type="button" @click="rejectSimilarEntity(row.station); syncMappingRowAfterEntityChange(row)">新增站點</button>
                          <button class="ghost-btn batch-action-btn" type="button" @click="skipMappingBatchRow(row)">略過</button>
                        </template>
                        <template v-else-if="row.station.status === 'needs-add'">
                          <button class="primary-btn batch-action-btn" type="button" @click="createEntityForBatch(row.station).then(() => syncMappingRowAfterEntityChange(row))">新增站點</button>
                          <button class="ghost-btn batch-action-btn" type="button" @click="skipMappingBatchRow(row)">略過</button>
                        </template>
                        <template v-else-if="row.status === 'skipped'">
                          <span class="batch-inline-hint">已排除，不會送出</span>
                        </template>
                        <template v-else-if="row.status === 'error'">
                          <span class="batch-inline-hint">請修正後再匯入</span>
                        </template>
                      </div>
                    </div>
                  </td>
                </tr>
                <tr v-if="mappingBatchRows.length === 0">
                  <td colspan="6" class="empty-cell">貼上表格後會自動解析並顯示預覽</td>
                </tr>
              </tbody>
      </table>
    </ProductionBatchImportModal>

    <ProductionBatchImportModal
      :open="showRequirementBatchModal"
      title="批次貼上匯入 Fixture Requirement"
      description="每行一筆：`站點編號,治具編號,數量`。若找不到會先比對相似資料，再讓你確認、替換或新增。"
      :text="requirementBatchText"
      placeholder="例如：&#10;EDS_T1,test001,1&#10;EDS_T1,test002,10"
      :saving="savingRequirement"
      submit-label="匯入 Requirement"
      :ready-count="requirementReadyRows.length"
      :pending-count="requirementPendingRows.length"
      :error-count="requirementErrorRows.length"
      @close="showRequirementBatchModal = false"
      @clear="clearRequirementBatchImport"
      @submit="submitRequirementBatchImport"
      @update:text="requirementBatchText = $event"
    >
      <table class="mapping-table batch-preview-table">
              <thead>
                <tr>
                  <th>行</th>
                  <th>原始站點</th>
                  <th>使用站點</th>
                  <th>原始治具</th>
                  <th>使用治具</th>
                  <th>數量</th>
                  <th>狀態 / 操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in requirementBatchRows" :key="`requirement-batch-${row.lineNo}-${row.raw}`">
                  <td>{{ row.lineNo }}</td>
                  <td>{{ row.station.inputCode || "-" }}</td>
                  <td>{{ row.station.resolvedCode || row.station.suggestedCode || "-" }}</td>
                  <td>{{ row.fixture.inputCode || "-" }}</td>
                  <td>{{ row.fixture.resolvedCode || row.fixture.suggestedCode || "-" }}</td>
                  <td>{{ row.quantity || "-" }}</td>
                  <td>
                    <div class="batch-cell-stack">
                      <span v-if="row.status === 'ready'" class="batch-status ready">已確認</span>
                      <span v-else-if="row.status === 'needs-confirm'" class="batch-status warn">待確認</span>
                      <span v-else-if="row.status === 'needs-add'" class="batch-status warn">待新增</span>
                      <span v-else-if="row.status === 'skipped'" class="batch-status muted">已跳過</span>
                      <span v-else class="batch-status error">錯誤</span>
                      <span v-if="row.message || row.note" class="batch-row-note">{{ row.message || row.note }}</span>
                      <div class="batch-row-actions">
                        <template v-if="row.station.status === 'needs-confirm'">
                          <button class="ghost-btn batch-action-btn" type="button" @click="acceptSimilarEntity(row.station); syncRequirementRowAfterEntityChange(row)">站點同一</button>
                          <button class="primary-btn batch-action-btn" type="button" @click="rejectSimilarEntity(row.station); syncRequirementRowAfterEntityChange(row)">新增站點</button>
                          <button class="ghost-btn batch-action-btn" type="button" @click="skipRequirementBatchRow(row)">略過</button>
                        </template>
                        <template v-else-if="row.station.status === 'needs-add'">
                          <button class="primary-btn batch-action-btn" type="button" @click="createEntityForBatch(row.station).then(() => syncRequirementRowAfterEntityChange(row))">新增站點</button>
                          <button class="ghost-btn batch-action-btn" type="button" @click="skipRequirementBatchRow(row)">略過</button>
                        </template>
                        <template v-else-if="row.fixture.status === 'needs-confirm'">
                          <button class="ghost-btn batch-action-btn" type="button" @click="acceptSimilarEntity(row.fixture); syncRequirementRowAfterEntityChange(row)">治具同一</button>
                          <button class="primary-btn batch-action-btn" type="button" @click="rejectSimilarEntity(row.fixture); syncRequirementRowAfterEntityChange(row)">新增治具</button>
                          <button class="ghost-btn batch-action-btn" type="button" @click="skipRequirementBatchRow(row)">略過</button>
                        </template>
                        <template v-else-if="row.fixture.status === 'needs-add'">
                          <button class="primary-btn batch-action-btn" type="button" @click="createEntityForBatch(row.fixture).then(() => syncRequirementRowAfterEntityChange(row))">新增治具</button>
                          <button class="ghost-btn batch-action-btn" type="button" @click="skipRequirementBatchRow(row)">略過</button>
                        </template>
                        <template v-else-if="row.status === 'skipped'">
                          <span class="batch-inline-hint">已排除，不會送出</span>
                        </template>
                        <template v-else-if="row.status === 'error'">
                          <span class="batch-inline-hint">請修正後再匯入</span>
                        </template>
                      </div>
                    </div>
                  </td>
                </tr>
                <tr v-if="requirementBatchRows.length === 0">
                  <td colspan="7" class="empty-cell">貼上表格後會自動解析並顯示預覽</td>
                </tr>
              </tbody>
      </table>
    </ProductionBatchImportModal>

  </div>
</template>

<style scoped>
.production-page {
  height: 100%;
  overflow: hidden;
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
  gap: 8px;
  padding: 8px;
  background: #fff;
}

.empty-cell {
  padding: 12px 14px;
  color: #56657f;
  background: #f8fbff;
  text-align: center;
}

.top-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 8px;
  min-height: 0;
}

.overview-capacity-panel {
  min-width: 0;
}

.mapping-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border: 1px solid var(--line);
  border-radius: 12px;
  overflow: hidden;
  min-width: 100%;
  background: #fff;
}

.mapping-table th,
.mapping-table td {
  border-bottom: 1px solid var(--line);
  border-right: 1px solid rgba(220, 227, 238, 0.9);
  padding: 8px 10px;
  text-align: left;
  font-size: 12px;
  vertical-align: middle;
}

.mapping-table th:last-child,
.mapping-table td:last-child {
  border-right: none;
}

.mapping-table tr:last-child td {
  border-bottom: none;
}

.mapping-table thead th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: #f7f9fd;
  color: #52607b;
  font-weight: 700;
}

.mapping-table tbody tr:nth-child(even) {
  background: #fcfdff;
}

.mapping-table tbody tr:hover {
  background: #f3f7ff;
}

.primary-btn {
  border: 1px solid var(--green);
  border-radius: 8px;
  background: linear-gradient(180deg, #4cc36b 0%, #2ea54e 100%);
  color: #fff;
  font-weight: 700;
  padding: 8px 14px;
  min-height: 36px;
  box-shadow: 0 8px 18px rgba(46, 165, 78, 0.18);
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
}

.batch-preview-table {
  min-width: 100%;
}

.batch-cell-stack {
  display: grid;
  gap: 6px;
}

.batch-status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 64px;
  width: fit-content;
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 700;
}

.batch-status.ready {
  color: var(--green);
  background: var(--green-soft);
}

.batch-status.warn {
  color: var(--orange);
  background: var(--orange-soft);
}

.batch-status.muted {
  color: #66748d;
  background: #edf1f7;
}

.batch-status.error {
  color: var(--red);
  background: var(--red-soft);
}

.batch-row-note {
  color: #607089;
  font-size: 11px;
  line-height: 1.4;
}

.batch-row-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.batch-action-btn {
  width: auto;
  min-height: 28px;
  padding: 5px 10px;
  font-size: 11px;
  border-radius: 999px;
}

.batch-action-btn.primary-btn {
  min-width: 84px;
}

.batch-action-btn.ghost-btn {
  min-width: 72px;
}

.batch-inline-hint {
  color: #74839b;
  font-size: 11px;
}

.ghost-btn {
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  padding: 8px 12px;
  min-height: 36px;
  background: linear-gradient(180deg, #ffffff 0%, #f7f9fd 100%);
  color: #5b677d;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease, filter 0.15s ease;
}

.primary-btn:hover,
.ghost-btn:hover {
  transform: translateY(-1px);
}

.primary-btn:hover {
  box-shadow: 0 10px 22px rgba(46, 165, 78, 0.24);
  filter: brightness(1.02);
}

.ghost-btn:hover {
  border-color: #c0cad9;
  box-shadow: 0 4px 12px rgba(28, 47, 84, 0.08);
}

.ghost-btn:disabled,
.primary-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.primary-btn:active,
.ghost-btn:active {
  transform: translateY(0);
}

@media (max-width: 640px) {
  .top-grid {
    gap: 10px;
  }
}
</style>
