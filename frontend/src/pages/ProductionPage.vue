<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter, type LocationQueryRaw } from "vue-router";

import { api } from "@/api";
import { authSession, globalFixtureKeyword, selectedCustomerId, setCustomerSwitchGuard } from "@/appState";
import ProductionBatchImportModal from "@/components/production/ProductionBatchImportModal.vue";
import ProductionDetailSection from "@/components/production/ProductionDetailSection.vue";
import ProductionHeaderSection from "@/components/production/ProductionHeaderSection.vue";
import ProductionRequirementCopyModal from "@/components/production/ProductionRequirementCopyModal.vue";
import { useProductionBatchImport } from "@/composables/useProductionBatchImport";
import { useProductionEditorState } from "@/composables/useProductionEditorState";
import { requestConfirmation } from "@/confirmState";
import { pushToast } from "@/toastState";
import type { Fixture, FixtureRequirementListItem, IdentifierStockSummary, MachineModel, ModelQuery, ModelQueryStationRequirement, ModelStation, Station, StationCapacity, StockSummary } from "@/types";
import { formatLocalDate } from "@/utils/date";
import { matchesFixtureKeywords, parseFixtureKeywords } from "@/utils/fixtureSearch";
import { getAvailableRequirementStations } from "@/utils/productionStations";
import { calculateProjectedStationCapacity } from "@/utils/productionCapacityPreview";
import ProductionCapacityPanel from "@/components/production/ProductionCapacityPanel.vue";

const route = useRoute();
const router = useRouter();

const models = ref<MachineModel[]>([]);
const stations = ref<Station[]>([]);
const fixtures = ref<Fixture[]>([]);
const mappings = ref<ModelStation[]>([]);
const fixtureRequirements = ref<FixtureRequirementListItem[]>([]);
const stockRows = ref<StockSummary[]>([]);
const identifierStockRows = ref<IdentifierStockSummary[]>([]);
let identifierStockRequestId = 0;
const modelQuery = ref<ModelQuery | null>(null);
const stationCapacity = ref<StationCapacity | null>(null);

const loading = ref(false);
const loadedAt = ref("");
const updatedAt = ref("");
const bottleneckHighlightTrigger = ref(0);
const hasMounted = ref(false);
const editorCustomerId = ref<number | null>(null);
const showRequirementCopyModal = ref(false);
const savingRequirementCopy = ref(false);
const routeFixtureKeyword = ref("");

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
const stationRecordMap = computed(() => new Map(stations.value.map((row) => [row.id, row])));
const stockMap = computed(() => new Map(stockRows.value.map((row) => [row.fixture_id, row])));
const modelQueryStationMap = computed(
  () => new Map((modelQuery.value?.stations ?? []).map((row) => [row.station_id, row]))
);
const globalFixtureKeywords = computed(() =>
  parseFixtureKeywords(routeFixtureKeyword.value || globalFixtureKeyword.value)
);
const mappingRows = computed(() =>
  mappings.value.map((row) => {
    const station = stationRecordMap.value.get(row.station_id);
    const capacity = modelQueryStationMap.value.get(row.station_id);
    return {
      id: row.id,
      model_id: row.model_id,
      modelCode: modelMap.value.get(row.model_id) ?? `model ${row.model_id}`,
      station_id: row.station_id,
      stationCode: station?.code ?? `station ${row.station_id}`,
      stationName: station?.name ?? "",
      maxOpenStationCount: capacity?.max_open_station_count ?? null,
      bottleneckFixtureCode: capacity?.bottleneck_fixture_code ?? null
    };
  })
);
const selectedModelStationRows = computed(() => mappingRows.value.filter((row) => row.model_id === modelId.value));
const availableRequirementStations = computed(() =>
  getAvailableRequirementStations(stations.value, mappings.value, modelId.value)
);
const selectedStationCode = computed(() => selectedStation.value?.code ?? "");
const selectedStationAllRequirementRows = computed(() =>
  fixtureRequirements.value.filter(
    (row) =>
      row.model_id === modelId.value &&
      row.station_id === requirementStationId.value
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
const selectedStationRequirementRows = computed(() => {
  const queryByFixtureId = new Map(selectedStationQueryRows.value.map((row) => [row.fixture_id, row]));
  return selectedStationAllRequirementRows.value
    .filter((row) => matchesFixtureKeywords(row.fixture_code, globalFixtureKeywords.value))
    .map((row) => {
      const queryRow = queryByFixtureId.get(row.fixture_id);
      const stockQty = queryRow?.stock_qty ?? stockMap.value.get(row.fixture_id)?.stock_qty ?? 0;
      const maxOpenStationCount = Math.floor(stockQty / row.required_qty);
      return {
        ...row,
        stockQty,
        maxOpenStationCount,
        isBottleneck: stationCapacity.value?.bottleneck_fixture_code === row.fixture_code
      };
    });
});
const canEditProduction = computed(() => authSession.value?.role !== "guest");
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
const detailMode = computed<"overview" | "configure">(() => {
  if (route.name === "production-mapping" || route.name === "production-requirements") return "configure";
  return "overview";
});
const isMainOverview = computed(() => detailMode.value === "overview");
const returnToPath = computed(() => {
  const raw = Array.isArray(route.query.return_to) ? route.query.return_to[0] : route.query.return_to;
  return typeof raw === "string" && raw.startsWith("/") ? raw : "/search";
});
const backLabel = computed(() => (returnToPath.value.startsWith("/search") ? "返回搜尋" : "返回來源"));
const {
  modelId,
  mappingStationId,
  requirementStationId,
  fixtureId,
  requiredQty,
  designatedMode,
  designatedIdentifiers,
  mappingStationCodeInput,
  fixtureCodeInput,
  editingMappingId,
  editingRequirementId,
  openAutocompleteKey,
  filteredStationSuggestions,
  filteredFixtureSuggestions,
  hasUnsavedMappingChanges,
  hasUnsavedRequirementChanges,
  updateModelId,
  updateSelectedStationId,
  updateRequiredQty,
  updateDesignatedMode,
  updateDesignatedIdentifiers,
  openMappingStationAutocomplete,
  handleMappingStationInput,
  blurMappingStationAutocomplete,
  selectMappingStationSuggestion,
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

const capacityPreviewStocks = computed(() => {
  const byFixture = new Map(stockRows.value.map((row) => [row.fixture_id, row.stock_qty]));
  for (const row of selectedStationQueryRows.value) byFixture.set(row.fixture_id, row.stock_qty);
  if (fixtureId.value !== null && designatedMode.value) {
    const selected = new Set(designatedIdentifiers.value);
    byFixture.set(
      fixtureId.value,
      identifierStockRows.value
        .filter((row) => selected.has(row.identifier))
        .reduce((sum, row) => sum + row.stock_qty, 0)
    );
  }
  return [...byFixture].map(([fixture_id, stock_qty]) => ({ fixture_id, stock_qty }));
});
const projectedCapacity = computed(() =>
  calculateProjectedStationCapacity({
    requirements: selectedStationAllRequirementRows.value,
    stocks: capacityPreviewStocks.value,
    fixtureId: fixtureId.value,
    fixtureCode: fixtureCodeInput.value,
    requiredQty: requiredQty.value,
    editingRequirementId: editingRequirementId.value
  })
);
const selectedFixtureAlreadyConfigured = computed(
  () =>
    editingRequirementId.value === null &&
    fixtureId.value !== null &&
    selectedStationAllRequirementRows.value.some((row) => row.fixture_id === fixtureId.value)
);

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

function parseRouteEntityId(key: "model_id" | "station_id" | "fixture_id"): number | null {
  const value = route.query[key];
  const raw = Array.isArray(value) ? value[0] : value;
  if (typeof raw !== "string" || raw.trim().length === 0) {
    return null;
  }
  const parsed = Number.parseInt(raw, 10);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

function applyRouteProductionSelection(): void {
  const routeModelId = parseRouteEntityId("model_id");
  if (routeModelId !== null) {
    const model = models.value.find((row) => row.id === routeModelId);
    if (model) modelId.value = model.id;
  }

  syncRequirementStationSelection();
  const routeStationId = parseRouteEntityId("station_id");
  if (
    routeStationId !== null &&
    availableRequirementStations.value.some((row) => row.id === routeStationId)
  ) {
    updateSelectedStationId(routeStationId);
  }

  const routeFixtureId = parseRouteEntityId("fixture_id");
  const fixture = fixtures.value.find((row) => row.id === routeFixtureId);
  routeFixtureKeyword.value = fixture?.code ?? "";
}

function buildProductionRouteQuery(): LocationQueryRaw {
  const query: LocationQueryRaw = {};
  for (const [key, value] of Object.entries(route.query)) {
    if (typeof value === "string") {
      query[key] = value;
      continue;
    }
    if (Array.isArray(value) && typeof value[0] === "string") {
      query[key] = value[0];
    }
  }
  if (modelId.value !== null) {
    query.model_id = String(modelId.value);
  } else {
    delete query.model_id;
  }
  return query;
}

function hasUnsavedProductionChanges(): boolean {
  return hasUnsavedRequirementChanges.value || hasUnsavedMappingChanges.value;
}

function openConfigurationPage(): void {
  void router.push({ name: "production-mapping", query: buildProductionRouteQuery() });
}

function closeDetailPage(): void {
  void router.push({ name: "production", query: buildProductionRouteQuery() });
}

async function handleBackNavigation(): Promise<void> {
  void router.push(returnToPath.value);
}

async function selectStationForRequirement(stationId: number): Promise<void> {
  if (stationId === requirementStationId.value) {
    return;
  }
  if (
    hasUnsavedRequirementChanges.value &&
    !(await requestConfirmation("目前治具需求表單有未儲存的修改，切換站點後會遺失。要繼續嗎？", {
      title: "切換站點？",
      confirmLabel: "捨棄並切換",
      tone: "danger"
    }))
  ) {
    return;
  }
  updateSelectedStationId(stationId);
  resetRequirementEditorWithoutPrompt();
}

async function selectModelForWorkspace(nextModelId: number | null): Promise<void> {
  if (nextModelId === modelId.value) {
    return;
  }
  if (
    hasUnsavedProductionChanges() &&
    !(await requestConfirmation("目前有未儲存的修改，切換機種後會遺失。要繼續嗎？", {
      title: "切換機種？",
      confirmLabel: "捨棄並切換",
      tone: "danger"
    }))
  ) {
    return;
  }
  updateModelId(nextModelId);
  resetMappingEditorWithoutPrompt();
  syncRequirementStationSelection();
  resetRequirementEditorWithoutPrompt();
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
    const shouldResetEditorContext =
      !hasMounted.value || editorCustomerId.value !== selectedCustomerId.value;
    modelQuery.value = null;
    stationCapacity.value = null;
    const customerId = selectedCustomerId.value ?? undefined;
    const [modelRows, stationRows, fixtureRows, mappingRows, requirementRows, inventoryRows] = await Promise.all([
      customerId ? api.listModels(customerId) : Promise.resolve([]),
      customerId ? api.listStations(customerId) : Promise.resolve([]),
      api.listFixtures(customerId),
      customerId ? api.listModelStations(customerId) : Promise.resolve([]),
      customerId ? api.listFixtureRequirements(customerId) : Promise.resolve([]),
      api.listStock(customerId)
    ]);
    models.value = modelRows;
    stations.value = stationRows;
    fixtures.value = fixtureRows;
    mappings.value = mappingRows;
    fixtureRequirements.value = requirementRows;
    stockRows.value = inventoryRows;

    modelId.value = modelRows.find((row) => row.id === modelId.value)?.id ?? modelRows[0]?.id ?? null;
    applyRouteProductionSelection();
    if (
      shouldResetEditorContext ||
      (editingMappingId.value !== null && !mappingRows.some((row) => row.id === editingMappingId.value))
    ) {
      resetMappingEditorWithoutPrompt();
    }
    if (
      shouldResetEditorContext ||
      (editingRequirementId.value !== null && !requirementRows.some((row) => row.id === editingRequirementId.value))
    ) {
      resetRequirementEditorWithoutPrompt();
    }
    editorCustomerId.value = selectedCustomerId.value;

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

async function loadIdentifierStocks(): Promise<void> {
  const requestId = ++identifierStockRequestId;
  const customerId = selectedCustomerId.value;
  const currentFixtureId = fixtureId.value;
  if (!customerId || currentFixtureId === null) {
    identifierStockRows.value = [];
    return;
  }
  try {
    const rows = await api.listIdentifierStockSummary(customerId, currentFixtureId);
    if (requestId === identifierStockRequestId) identifierStockRows.value = rows;
  } catch (err) {
    if (requestId === identifierStockRequestId) identifierStockRows.value = [];
    pushToast(err instanceof Error ? err.message : "載入 identifier 庫存失敗", "error");
  }
}

async function saveMapping(): Promise<void> {
  if (!canEditProduction.value) {
    pushToast("訪客模式只能查看產能設定。", "warning");
    return;
  }
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
      pushToast("站點設定已新增", "success");
    } else {
      await api.updateModelStation(editingMappingId.value, payload);
      pushToast("站點設定已更新", "success");
    }
    await loadData(false);
    updateSelectedStationId(currentStationId);
    resetMappingEditorWithoutPrompt();
    resetRequirementEditorWithoutPrompt();
    await Promise.all([refreshCapacity(), refreshModelQuery()]);
  } catch (err) {
    pushToast(err instanceof Error ? err.message : editingMappingId.value === null ? "新增站點設定失敗" : "更新站點設定失敗", "error");
  } finally {
    savingMapping.value = false;
  }
}

async function removeMapping(rowId: number): Promise<void> {
  if (!canEditProduction.value) {
    return;
  }
  if (!selectedCustomerId.value) {
    pushToast("請先選擇客戶。", "warning");
    return;
  }
  const mapping = mappings.value.find((row) => row.id === rowId);
  const affectedRequirementCount = mapping
    ? fixtureRequirements.value.filter(
        (row) => row.model_id === mapping.model_id && row.station_id === mapping.station_id
      ).length
    : 0;
  if (affectedRequirementCount > 0 && mapping) {
    await selectStationForRequirement(mapping.station_id);
    pushToast(`此站點仍有 ${affectedRequirementCount} 筆治具需求，請先從右側移除後再刪除站點。`, "warning");
    return;
  }
  if (
    !(await requestConfirmation("此站點目前沒有治具需求。確定要刪除這筆站點設定嗎？", {
      title: "刪除站點設定？",
      confirmLabel: "刪除",
      tone: "danger"
    }))
  ) return;
  try {
    await api.deleteModelStation(rowId, selectedCustomerId.value);
    if (editingMappingId.value === rowId) resetMappingEditorWithoutPrompt();
    await loadData(false);
    await Promise.all([refreshCapacity(), refreshModelQuery()]);
    pushToast("站點設定已刪除", "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "刪除站點設定失敗", "error");
  }
}

async function saveRequirement(): Promise<void> {
  if (!canEditProduction.value) {
    pushToast("訪客模式只能查看產能設定。", "warning");
    return;
  }
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
      pushToast("請先選擇有效的站點。", "warning");
      return;
    }
    const currentStationId = requirementStationId.value as number;
    const currentFixtureId = fixtureId.value as number;
    const payload = {
      customer_id: selectedCustomerId.value,
      model_id: currentModelId,
      station_id: currentStationId,
      fixture_id: currentFixtureId,
      required_qty: requiredQty.value,
      designated_mode: designatedMode.value,
      designated_identifiers: designatedMode.value ? designatedIdentifiers.value : []
    };
    const existingRequirement = fixtureRequirements.value.find(
      (row) =>
        row.model_id === currentModelId &&
        row.station_id === currentStationId &&
        row.fixture_id === currentFixtureId
    );
    const targetRequirementId = editingRequirementId.value ?? existingRequirement?.id ?? null;
    if (targetRequirementId === null) {
      await api.createFixtureRequirement(payload);
      pushToast("治具需求已加入", "success");
    } else {
      await api.updateFixtureRequirement(targetRequirementId, payload);
      pushToast(
        editingRequirementId.value === null ? "此治具已存在，需求數量已更新" : "治具需求已更新",
        "success"
      );
    }
    await loadData(false);
    updateSelectedStationId(currentStationId);
    resetRequirementEditorWithoutPrompt();
    await Promise.all([refreshCapacity(), refreshModelQuery()]);
    touchUpdatedAt();
  } catch (err) {
    pushToast(err instanceof Error ? err.message : editingRequirementId.value === null ? "儲存 requirement 失敗" : "更新 requirement 失敗", "error");
  } finally {
    savingRequirement.value = false;
  }
}

async function removeRequirement(requirementId: number): Promise<void> {
  if (!canEditProduction.value) {
    return;
  }
  if (!selectedCustomerId.value) {
    pushToast("請先選擇客戶。", "warning");
    return;
  }
  if (
    !(await requestConfirmation("確定要刪除這筆站點治具需求嗎？", {
      title: "刪除治具需求？",
      confirmLabel: "刪除",
      tone: "danger"
    }))
  ) return;
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

async function openRequirementCopyModal(): Promise<void> {
  if (!canEditProduction.value || modelId.value === null || requirementStationId.value === null) {
    return;
  }
  if (selectedStationAllRequirementRows.value.length === 0) {
    pushToast("目前站點沒有可複製的治具需求。", "warning");
    return;
  }
  if (
    hasUnsavedRequirementChanges.value &&
    !(await requestConfirmation("開啟複製流程會清除目前未儲存的治具需求表單。要繼續嗎？", {
      title: "開啟複製流程？",
      confirmLabel: "清除並繼續",
      tone: "danger"
    }))
  ) {
    return;
  }
  resetRequirementEditorWithoutPrompt();
  showRequirementCopyModal.value = true;
}

async function copyRequirementSettings(payload: {
  targetModelId: number;
  targetStationId: number;
  overwriteExisting: boolean;
}): Promise<void> {
  if (
    !selectedCustomerId.value ||
    modelId.value === null ||
    requirementStationId.value === null
  ) {
    pushToast("缺少來源機種、站點或客戶資料。", "warning");
    return;
  }
  savingRequirementCopy.value = true;
  const sourceModelId = modelId.value;
  const sourceStationId = requirementStationId.value;
  try {
    const result = await api.copyFixtureRequirements({
      customer_id: selectedCustomerId.value,
      source_model_id: sourceModelId,
      source_station_id: sourceStationId,
      target_model_id: payload.targetModelId,
      target_station_id: payload.targetStationId,
      overwrite_existing: payload.overwriteExisting
    });
    showRequirementCopyModal.value = false;
    await loadData(false);
    updateModelId(payload.targetModelId);
    updateSelectedStationId(payload.targetStationId);
    resetMappingEditorWithoutPrompt();
    resetRequirementEditorWithoutPrompt();
    await Promise.all([refreshCapacity(), refreshModelQuery()]);
    pushToast(
      `複製完成：新增 ${result.created_count}、更新 ${result.updated_count}、跳過 ${result.skipped_count}${
        result.mapping_created ? "，並已加入目標站點" : ""
      }。`,
      "success"
    );
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "複製站點治具需求失敗", "error");
  } finally {
    savingRequirementCopy.value = false;
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
    downloadCsv("station-settings.csv", await api.exportModelStationsCsv(selectedCustomerId.value ?? undefined));
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "匯出站點設定失敗", "error");
  }
}

async function downloadModelStationTemplate(): Promise<void> {
  try {
    downloadCsv("station-settings-template.csv", await api.downloadModelStationTemplateCsv());
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "下載站點設定範本失敗", "error");
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
    pushToast(`匯入站點設定完成，共 ${result.imported_count} 筆。`, "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "匯入站點設定失敗", "error");
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

watch([selectedCustomerId, fixtureId], loadIdentifierStocks, { immediate: true });

watch(
  () => hasUnsavedProductionChanges(),
  (value) => {
    setCustomerSwitchGuard("production-page", value, "產能頁有未儲存的修改");
  },
  { immediate: true }
);

watch(
  () => [route.query.model_id, route.query.station_id, route.query.fixture_id],
  async () => {
    applyRouteProductionSelection();
    await Promise.all([refreshCapacity(), refreshModelQuery()]);
  }
);

onMounted(async () => {
  await loadData();
  await Promise.all([refreshCapacity(), refreshModelQuery()]);
  hasMounted.value = true;
});

onBeforeUnmount(() => {
  setCustomerSwitchGuard("production-page", false, "產能頁有未儲存的修改");
});

watch(
  modelId,
  async () => {
    if (!hasMounted.value) {
      return;
    }
    const nextQuery = buildProductionRouteQuery();
    const currentModelId = Array.isArray(route.query.model_id) ? route.query.model_id[0] : route.query.model_id;
    const nextModelId = typeof nextQuery.model_id === "string" ? nextQuery.model_id : "";
    if ((currentModelId ?? "") === nextModelId) {
      return;
    }
    await router.replace({ name: route.name ?? "production", query: nextQuery });
  }
);

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
      :back-label="backLabel"
      @back="handleBackNavigation"
      @open-overview="closeDetailPage"
      @open-configure="openConfigurationPage"
      @focus-bottleneck="focusBottleneckEvidence"
      @update:model-id="selectModelForWorkspace"
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
        :available-stations="availableRequirementStations"
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
      :can-edit="canEditProduction"
      :loading="loading"
      :saving-mapping="savingMapping"
      :saving-requirement="savingRequirement"
      :editing-mapping-id="editingMappingId"
      :editing-requirement-id="editingRequirementId"
      :selected-model-code="selectedModel?.code || ''"
      :selected-requirement-station-id="requirementStationId"
      :selected-station-code="selectedStationCode"
      :selected-station-name="selectedStation?.name || ''"
      :station-capacity-count="stationCapacity?.max_open_station_count ?? null"
      :station-bottleneck-fixture-code="stationCapacity?.bottleneck_fixture_code || ''"
      :projected-capacity="projectedCapacity"
      :selected-fixture-already-configured="selectedFixtureAlreadyConfigured"
      :selected-model-station-rows="selectedModelStationRows"
      :selected-station-requirement-rows="selectedStationRequirementRows"
      :source-requirement-count="selectedStationAllRequirementRows.length"
      :mapping-station-code-input="mappingStationCodeInput"
      :fixture-code-input="fixtureCodeInput"
      :required-qty="requiredQty"
      :designated-mode="designatedMode"
      :designated-identifiers="designatedIdentifiers"
      :identifier-stock-rows="identifierStockRows"
      :open-autocomplete-key="openAutocompleteKey"
      :filtered-station-suggestions="filteredStationSuggestions"
      :filtered-fixture-suggestions="filteredFixtureSuggestions"
      :on-open-mapping-batch-modal="() => (showMappingBatchModal = true)"
      :on-open-requirement-batch-modal="() => (showRequirementBatchModal = true)"
      :on-open-requirement-copy-modal="openRequirementCopyModal"
      :on-import-model-stations-csv="importModelStationsCsv"
      :on-import-fixture-requirements-csv="importFixtureRequirementsCsv"
      :on-save-mapping="saveMapping"
      :on-reset-mapping-editor="resetMappingEditor"
      :on-start-edit-mapping="startEditMapping"
      :on-remove-mapping="removeMapping"
      :on-select-mapping-station="selectStationForRequirement"
      :on-save-requirement="saveRequirement"
      :on-reset-requirement-editor="resetRequirementEditor"
      :on-start-edit-requirement="startEditRequirement"
      :on-remove-requirement="removeRequirement"
      :on-mapping-station-focus="openMappingStationAutocomplete"
      :on-mapping-station-input="handleMappingStationInput"
      :on-mapping-station-blur="blurMappingStationAutocomplete"
      :on-select-mapping-station-suggestion="selectMappingStationSuggestion"
      :on-fixture-focus="openFixtureAutocomplete"
      :on-fixture-input="handleFixtureInput"
      :on-fixture-blur="blurFixtureAutocomplete"
      :on-select-fixture-suggestion="selectFixtureSuggestion"
      :on-required-qty-change="updateRequiredQty"
      :on-designated-mode-change="updateDesignatedMode"
      :on-designated-identifiers-change="updateDesignatedIdentifiers"
    />

    <ProductionRequirementCopyModal
      v-if="canEditProduction"
      :open="showRequirementCopyModal"
      :saving="savingRequirementCopy"
      :source-model-id="modelId"
      :source-model-code="selectedModelCode"
      :source-station-id="requirementStationId"
      :source-station-code="selectedStationCode"
      :models="models"
      :stations="stations"
      :mappings="mappings"
      :requirements="fixtureRequirements"
      @close="showRequirementCopyModal = false"
      @submit="copyRequirementSettings"
    />

    <ProductionBatchImportModal
      v-if="canEditProduction"
      :open="showMappingBatchModal"
      title="批次貼上匯入站點設定"
      description="每行一筆：`機種編號,站點編號`。若找不到會先比對相似資料，再讓你確認、替換或新增。"
      :text="mappingBatchText"
      placeholder="例如：&#10;EDS,EDS_T1&#10;EDS,EDS_T2"
      :saving="savingMapping"
      submit-label="匯入站點設定"
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
      v-if="canEditProduction"
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


<style scoped src="@/styles/surfaces/production.css"></style>
