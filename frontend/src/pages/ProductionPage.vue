<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "@/api";
import { globalFixtureKeyword, selectedCustomerId } from "@/appState";
import ProductionBatchImportModal from "@/components/production/ProductionBatchImportModal.vue";
import ProductionDetailSection from "@/components/production/ProductionDetailSection.vue";
import ProductionHeaderSection from "@/components/production/ProductionHeaderSection.vue";
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

const modelId = ref<number | null>(null);
const mappingStationId = ref<number | null>(null);
const requirementStationId = ref<number | null>(null);
const preferredRequirementStationCode = ref("");
const fixtureId = ref<number | null>(null);
const requiredQty = ref(1);
const mappingModelCodeInput = ref("");
const mappingStationCodeInput = ref("");
const requirementStationCodeInput = ref("");
const fixtureCodeInput = ref("");

const savingMapping = ref(false);
const savingRequirement = ref(false);
const loading = ref(false);
const loadedAt = ref("");
const updatedAt = ref("");
const bottleneckHighlightTrigger = ref(0);
const editingMappingId = ref<number | null>(null);
const editingRequirementId = ref<number | null>(null);
const showMappingBatchModal = ref(false);
const showRequirementBatchModal = ref(false);
const openAutocompleteKey = ref<null | "mapping-model" | "mapping-station" | "requirement-station" | "fixture">(null);
const mappingBatchText = ref("");
const requirementBatchText = ref("");
type BatchRowStatus = "ready" | "needs-confirm" | "needs-add" | "skipped" | "error";
type BatchEntityKind = "model" | "station" | "fixture";

type BatchEntityResolution = {
  kind: BatchEntityKind;
  label: string;
  inputCode: string;
  resolvedId: number | null;
  resolvedCode: string;
  suggestedId: number | null;
  suggestedCode: string;
  status: Exclude<BatchRowStatus, "error">;
  message: string | null;
  note: string | null;
};

type MappingBatchRow = {
  lineNo: number;
  raw: string;
  model: BatchEntityResolution;
  station: BatchEntityResolution;
  status: BatchRowStatus;
  message: string | null;
  note: string | null;
};

type RequirementBatchRow = {
  lineNo: number;
  raw: string;
  station: BatchEntityResolution;
  fixture: BatchEntityResolution;
  quantity: number;
  status: BatchRowStatus;
  message: string | null;
  note: string | null;
};

const mappingBatchRows = ref<MappingBatchRow[]>([]);
const requirementBatchRows = ref<RequirementBatchRow[]>([]);

function nowString(): string {
  return formatLocalDate(new Date());
}

function touchUpdatedAt(): void {
  updatedAt.value = nowString();
}

const selectedModel = computed(() => models.value.find((row) => row.id === modelId.value) ?? null);
const selectedStation = computed(() => stations.value.find((row) => row.id === requirementStationId.value) ?? null);
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
const mappingReadyRows = computed(() => mappingBatchRows.value.filter((row) => row.status === "ready"));
const mappingPendingRows = computed(() => mappingBatchRows.value.filter((row) => row.status === "needs-confirm" || row.status === "needs-add"));
const mappingErrorRows = computed(() => mappingBatchRows.value.filter((row) => row.status === "error"));
const requirementReadyRows = computed(() => requirementBatchRows.value.filter((row) => row.status === "ready"));
const requirementPendingRows = computed(() => requirementBatchRows.value.filter((row) => row.status === "needs-confirm" || row.status === "needs-add"));
const requirementErrorRows = computed(() => requirementBatchRows.value.filter((row) => row.status === "error"));
const filteredModelSuggestions = computed(() => filterCodeSuggestions(models.value, mappingModelCodeInput.value));
const filteredStationSuggestions = computed(() => filterCodeSuggestions(stations.value, mappingStationCodeInput.value));
const filteredRequirementStationSuggestions = computed(() => filterCodeSuggestions(availableRequirementStations.value, requirementStationCodeInput.value));
const filteredFixtureSuggestions = computed(() => filterCodeSuggestions(fixtures.value, fixtureCodeInput.value));
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

function normalizeLookupText(value: string): string {
  return value.trim().toLowerCase();
}

function normalizeEditorText(value: string | null | undefined): string {
  return (value ?? "").trim();
}

const mappingEditorBaseline = computed(() => ({
  modelCode: normalizeEditorText(selectedModel.value?.code),
  stationCode: normalizeEditorText(stations.value.find((row) => row.id === mappingStationId.value)?.code)
}));
const mappingEditorCurrent = computed(() => ({
  modelCode: normalizeEditorText(mappingModelCodeInput.value),
  stationCode: normalizeEditorText(mappingStationCodeInput.value)
}));
const hasUnsavedMappingChanges = computed(() => JSON.stringify(mappingEditorCurrent.value) !== JSON.stringify(mappingEditorBaseline.value));
const requirementEditorBaseline = computed(() => ({
  stationCode: normalizeEditorText(selectedStation.value?.code),
  fixtureCode: normalizeEditorText(fixtures.value.find((row) => row.id === fixtureId.value)?.code),
  requiredQty: requiredQty.value
}));
const requirementEditorCurrent = computed(() => ({
  stationCode: normalizeEditorText(requirementStationCodeInput.value),
  fixtureCode: normalizeEditorText(fixtureCodeInput.value),
  requiredQty: requiredQty.value
}));
const hasUnsavedRequirementChanges = computed(() => JSON.stringify(requirementEditorCurrent.value) !== JSON.stringify(requirementEditorBaseline.value));

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

function syncMappingModelSelection(): void {
  const match = findCodeMatch(models.value, mappingModelCodeInput.value);
  if (match) modelId.value = match.id;
}

function syncMappingStationSelection(): void {
  const match = findCodeMatch(stations.value, mappingStationCodeInput.value);
  if (match) mappingStationId.value = match.id;
}

function syncRequirementStationInput(): void {
  const match = findCodeMatch(availableRequirementStations.value, requirementStationCodeInput.value);
  if (match) requirementStationId.value = match.id;
}

function syncFixtureSelection(): void {
  const match = findCodeMatch(fixtures.value, fixtureCodeInput.value);
  if (match) fixtureId.value = match.id;
}

function openAutocomplete(
  key: "mapping-model" | "mapping-station" | "requirement-station" | "fixture",
  rows: Array<{ code: string }>,
  value: string
): void {
  openAutocompleteKey.value = hasExactCodeMatch(rows, value) ? key : null;
}

function showAutocompleteOnInput(key: "mapping-model" | "mapping-station" | "requirement-station" | "fixture"): void {
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

function openMappingModelAutocomplete(): void {
  openAutocomplete("mapping-model", models.value, mappingModelCodeInput.value);
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
  openAutocomplete("mapping-station", stations.value, mappingStationCodeInput.value);
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
  openAutocomplete("requirement-station", availableRequirementStations.value, requirementStationCodeInput.value);
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
  openAutocomplete("fixture", fixtures.value, fixtureCodeInput.value);
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

function updateRequiredQty(value: number): void {
  requiredQty.value = value;
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

function ensureMappingSelections(): boolean {
  syncMappingModelSelection();
  syncMappingStationSelection();
  if (!modelId.value) {
    pushToast("請輸入有效的機種代碼。", "warning");
    return false;
  }
  if (!mappingStationId.value) {
    pushToast("請輸入有效的站點代碼。", "warning");
    return false;
  }
  return true;
}

function ensureRequirementSelections(): boolean {
  syncRequirementStationInput();
  syncFixtureSelection();
  if (!requirementStationId.value) {
    pushToast("請輸入有效的站點代碼。", "warning");
    return false;
  }
  if (!fixtureId.value) {
    pushToast("請輸入有效的治具代碼。", "warning");
    return false;
  }
  return true;
}

function resetMappingEditor(): void {
  if (hasUnsavedMappingChanges.value && !window.confirm("目前 Mapping 表單有未儲存的修改，重載後將會捨棄。要繼續嗎？")) {
    return;
  }
  resetMappingEditorWithoutPrompt();
}

function resetMappingEditorWithoutPrompt(): void {
  editingMappingId.value = null;
  mappingModelCodeInput.value = selectedModel.value?.code ?? "";
  mappingStationCodeInput.value = stations.value.find((row) => row.id === mappingStationId.value)?.code ?? "";
}

function resetRequirementEditor(): void {
  if (hasUnsavedRequirementChanges.value && !window.confirm("目前 Requirement 表單有未儲存的修改，重載後將會捨棄。要繼續嗎？")) {
    return;
  }
  resetRequirementEditorWithoutPrompt();
}

function resetRequirementEditorWithoutPrompt(): void {
  editingRequirementId.value = null;
  requirementStationCodeInput.value = selectedStation.value?.code ?? "";
  fixtureCodeInput.value = fixtures.value.find((row) => row.id === fixtureId.value)?.code ?? "";
  requiredQty.value = 1;
}

function startEditMapping(row: { id: number; model_id: number; station_id: number }): void {
  if (editingMappingId.value !== row.id && hasUnsavedMappingChanges.value && !window.confirm("目前 Mapping 表單有未儲存的修改，切換編輯對象後將會捨棄。要繼續嗎？")) {
    return;
  }
  modelId.value = row.model_id;
  mappingStationId.value = row.station_id;
  editingMappingId.value = row.id;
}

function startEditRequirement(row: { id: number; station_id: number; fixture_id: number; required_qty: number }): void {
  if (editingRequirementId.value !== row.id && hasUnsavedRequirementChanges.value && !window.confirm("目前 Requirement 表單有未儲存的修改，切換編輯對象後將會捨棄。要繼續嗎？")) {
    return;
  }
  requirementStationId.value = row.station_id;
  fixtureId.value = row.fixture_id;
  requiredQty.value = row.required_qty;
  editingRequirementId.value = row.id;
}

function updateSelectedStationId(stationId: number | null): void {
  requirementStationId.value = stationId;
}

function focusBottleneckEvidence(): void {
  if (!stationCapacity.value?.bottleneck_fixture_code || !currentStationHasBottleneck.value) {
    return;
  }
  bottleneckHighlightTrigger.value += 1;
}

function downloadCsv(filename: string, content: string): void {
  const blob = new Blob([content], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function splitBatchCells(line: string): string[] {
  const trimmed = line.trim();
  if (!trimmed) return [];
  if (trimmed.includes("\t")) return trimmed.split("\t").map((cell) => cell.trim()).filter(Boolean);
  if (trimmed.includes("|")) return trimmed.split("|").map((cell) => cell.trim()).filter(Boolean);
  if (/[;,，；]/.test(trimmed)) return trimmed.split(/[;,，；]/).map((cell) => cell.trim()).filter(Boolean);
  return trimmed.split(/\s+/).map((cell) => cell.trim()).filter(Boolean);
}

function groupBatchCells(cells: string[], expectedSize: number): string[][] {
  if (cells.length <= expectedSize) return [cells];
  if (cells.length % expectedSize !== 0) return [cells];

  const groups: string[][] = [];
  for (let index = 0; index < cells.length; index += expectedSize) {
    groups.push(cells.slice(index, index + expectedSize));
  }
  return groups;
}

function normalizeBatchText(value: string): string {
  return value.replace(/\u00a0/g, " ").trim();
}

function normalizeCode(value: string): string {
  return normalizeBatchText(value).toUpperCase();
}

function isHeaderLikeLine(line: string, keywords: string[]): boolean {
  const normalized = normalizeBatchText(line).toLowerCase();
  if (!normalized) return true;
  return keywords.some((keyword) => normalized.includes(keyword.toLowerCase()));
}

function commonPrefixLength(left: string, right: string): number {
  const maxLength = Math.min(left.length, right.length);
  let index = 0;
  while (index < maxLength && left[index] === right[index]) {
    index += 1;
  }
  return index;
}

function levenshteinDistance(left: string, right: string): number {
  const a = left.toUpperCase();
  const b = right.toUpperCase();
  const previous = Array.from({ length: b.length + 1 }, (_, index) => index);
  for (let i = 1; i <= a.length; i += 1) {
    const current = [i];
    for (let j = 1; j <= b.length; j += 1) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      current[j] = Math.min(current[j - 1] + 1, previous[j] + 1, previous[j - 1] + cost);
    }
    previous.splice(0, previous.length, ...current);
  }
  return previous[b.length] ?? 0;
}

function makeEntityResolution(kind: BatchEntityKind, label: string, inputCode: string): BatchEntityResolution {
  return {
    kind,
    label,
    inputCode,
    resolvedId: null,
    resolvedCode: "",
    suggestedId: null,
    suggestedCode: "",
    status: "needs-add",
    message: null,
    note: null
  };
}

function setEntityReady(entity: BatchEntityResolution, id: number, code: string, note: string): void {
  entity.resolvedId = id;
  entity.resolvedCode = code;
  entity.suggestedId = null;
  entity.suggestedCode = "";
  entity.status = "ready";
  entity.message = null;
  entity.note = note;
}

function getCollectionByKind(kind: BatchEntityKind): Array<MachineModel | Station | Fixture> {
  if (kind === "model") return models.value;
  if (kind === "station") return stations.value;
  return fixtures.value;
}

function findExactEntity(kind: BatchEntityKind, code: string): MachineModel | Station | Fixture | undefined {
  const target = normalizeCode(code);
  return getCollectionByKind(kind).find((row) => normalizeCode(row.code) === target);
}

function findEntityById(kind: BatchEntityKind, entityId: number): MachineModel | Station | Fixture | undefined {
  return getCollectionByKind(kind).find((row) => row.id === entityId);
}

function findSimilarEntity(kind: BatchEntityKind, code: string): MachineModel | Station | Fixture | undefined {
  const target = normalizeCode(code);
  let best: { row: MachineModel | Station | Fixture; distance: number; prefix: number } | null = null;

  for (const row of getCollectionByKind(kind)) {
    const candidate = normalizeCode(row.code);
    const prefix = commonPrefixLength(target, candidate);
    const distance = levenshteinDistance(target, candidate);
    if (prefix < 3 && distance > 2) continue;
    if (
      best === null ||
      distance < best.distance ||
      (distance === best.distance && prefix > best.prefix) ||
      (distance === best.distance && prefix === best.prefix && candidate.length < normalizeCode(best.row.code).length)
    ) {
      best = { row, distance, prefix };
    }
  }

  return best && best.distance <= 2 ? best.row : undefined;
}

function resolveEntity(kind: BatchEntityKind, label: string, code: string): BatchEntityResolution {
  const entity = makeEntityResolution(kind, label, code);
  const normalized = normalizeBatchText(code);
  if (!normalized) {
    entity.status = "needs-add";
    entity.message = `缺少${label}編號`;
    return entity;
  }

  const exact = findExactEntity(kind, normalized);
  if (exact) {
    setEntityReady(entity, exact.id, exact.code, `已對應現有${label}`);
    return entity;
  }

  const similar = findSimilarEntity(kind, normalized);
  if (similar) {
    entity.suggestedId = similar.id;
    entity.suggestedCode = similar.code;
    entity.status = "needs-confirm";
    entity.message = `可能是 ${similar.code}，請先確認是否為同一個${label}`;
    return entity;
  }

  entity.status = "needs-add";
  entity.message = `找不到${label} ${normalized}，可新增或跳過`;
  return entity;
}

function syncMappingBatchRow(row: MappingBatchRow): void {
  const entities = [row.model, row.station];
  if (entities.some((entity) => entity.status === "skipped")) {
    row.status = "skipped";
    row.message = "已跳過";
    row.note = null;
    return;
  }
  const pendingConfirm = entities.find((entity) => entity.status === "needs-confirm");
  if (pendingConfirm) {
    row.status = "needs-confirm";
    row.message = pendingConfirm.message;
    row.note = pendingConfirm.note;
    return;
  }
  const pendingAdd = entities.find((entity) => entity.status === "needs-add");
  if (pendingAdd) {
    row.status = "needs-add";
    row.message = pendingAdd.message;
    row.note = pendingAdd.note;
    return;
  }
  row.status = "ready";
  row.message = null;
  row.note = "已完成機種 / 站點確認";
}

function syncRequirementBatchRow(row: RequirementBatchRow): void {
  if (!Number.isFinite(row.quantity) || row.quantity <= 0) {
    row.status = "error";
    row.message = "數量必須是大於 0 的整數";
    row.note = null;
    return;
  }
  const entities = [row.station, row.fixture];
  if (entities.some((entity) => entity.status === "skipped")) {
    row.status = "skipped";
    row.message = "已跳過";
    row.note = null;
    return;
  }
  const pendingConfirm = entities.find((entity) => entity.status === "needs-confirm");
  if (pendingConfirm) {
    row.status = "needs-confirm";
    row.message = pendingConfirm.message;
    row.note = pendingConfirm.note;
    return;
  }
  const pendingAdd = entities.find((entity) => entity.status === "needs-add");
  if (pendingAdd) {
    row.status = "needs-add";
    row.message = pendingAdd.message;
    row.note = pendingAdd.note;
    return;
  }
  row.status = "ready";
  row.message = null;
  row.note = "已完成站點 / 治具確認";
}

function toCsvCell(value: string): string {
  const normalized = value.replace(/"/g, "\"\"");
  return /[",\n]/.test(normalized) ? `"${normalized}"` : normalized;
}

function toCsv(headers: string[], rows: string[][]): string {
  return [headers.join(","), ...rows.map((row) => row.map(toCsvCell).join(","))].join("\n");
}

function parseMappingBatchText(text: string): MappingBatchRow[] {
  const lines = text
    .replace(/\r/g, "")
    .split("\n")
    .map((line) => normalizeBatchText(line))
    .filter(Boolean)
    .filter((line) => !isHeaderLikeLine(line, ["model_code", "station_code", "機種", "站點"]));

  const rows: MappingBatchRow[] = [];
  for (const line of lines) {
    const groups = groupBatchCells(splitBatchCells(line), 2);
    for (const cells of groups) {
      const modelCode = cells[0] ?? "";
      const stationCode = cells[1] ?? "";
      const row: MappingBatchRow = {
        lineNo: rows.length + 1,
        raw: cells.join(","),
        model: resolveEntity("model", "機種", modelCode),
        station: resolveEntity("station", "站點", stationCode),
        status: "error",
        message: null,
        note: null
      };
      if (!modelCode || !stationCode) {
        row.status = "error";
        row.message = "每筆必須包含機種與站點";
        rows.push(row);
        continue;
      }
      syncMappingBatchRow(row);
      rows.push(row);
    }
  }

  return rows;
}

function parseRequirementBatchText(text: string): RequirementBatchRow[] {
  const lines = text
    .replace(/\r/g, "")
    .split("\n")
    .map((line) => normalizeBatchText(line))
    .filter(Boolean)
    .filter((line) => !isHeaderLikeLine(line, ["station_code", "fixture_code", "required_qty", "站點", "治具", "數量"]));

  const rows: RequirementBatchRow[] = [];
  for (const line of lines) {
    const groups = groupBatchCells(splitBatchCells(line), 3);
    for (const cells of groups) {
      const stationCode = cells[0] ?? "";
      const fixtureCode = cells[1] ?? "";
      const quantityText = cells[2] ?? "";
      const quantity = /^\d+$/.test(quantityText) ? Number.parseInt(quantityText, 10) : 0;
      const row: RequirementBatchRow = {
        lineNo: rows.length + 1,
        raw: cells.join(","),
        station: resolveEntity("station", "站點", stationCode),
        fixture: resolveEntity("fixture", "治具", fixtureCode),
        quantity,
        status: "error",
        message: null,
        note: null
      };
      if (!stationCode || !fixtureCode || !quantityText) {
        row.status = "error";
        row.message = "每筆必須包含站點、治具與數量";
        rows.push(row);
        continue;
      }
      syncRequirementBatchRow(row);
      rows.push(row);
    }
  }

  return rows;
}

function refreshMappingBatchPreview(): void {
  mappingBatchRows.value = parseMappingBatchText(mappingBatchText.value);
}

function refreshRequirementBatchPreview(): void {
  requirementBatchRows.value = parseRequirementBatchText(requirementBatchText.value);
}

function skipMappingBatchRow(row: MappingBatchRow): void {
  row.model.status = "skipped";
  row.station.status = "skipped";
  syncMappingBatchRow(row);
}

function skipRequirementBatchRow(row: RequirementBatchRow): void {
  row.station.status = "skipped";
  row.fixture.status = "skipped";
  syncRequirementBatchRow(row);
}

function acceptSimilarEntity(entity: BatchEntityResolution): void {
  const target = entity.suggestedId ? findEntityById(entity.kind, entity.suggestedId) : undefined;
  if (!target) {
    entity.status = "needs-add";
    entity.message = `找不到建議${entity.label}，請改用新增或略過`;
    entity.suggestedId = null;
    entity.suggestedCode = "";
    return;
  }
  setEntityReady(entity, target.id, target.code, `已替換為 ${target.code}`);
}

function rejectSimilarEntity(entity: BatchEntityResolution): void {
  entity.status = "needs-add";
  entity.message = `若不是 ${entity.suggestedCode}，可直接新增或略過`;
}

async function createEntityForBatch(entity: BatchEntityResolution): Promise<void> {
  if (!selectedCustomerId.value || !entity.inputCode) {
    pushToast("請先選擇客戶。", "warning");
    return;
  }

  try {
    if (entity.kind === "model") {
      const created = await api.createModel({ customer_id: selectedCustomerId.value, code: entity.inputCode, name: entity.inputCode });
      models.value = [...models.value.filter((row) => row.id !== created.id), created];
      setEntityReady(entity, created.id, created.code, "已新增機種並加入匯入清單");
      pushToast(`已新增機種：${created.code}`, "success");
      return;
    }
    if (entity.kind === "station") {
      const created = await api.createStation({ customer_id: selectedCustomerId.value, code: entity.inputCode, name: entity.inputCode });
      stations.value = [...stations.value.filter((row) => row.id !== created.id), created];
      setEntityReady(entity, created.id, created.code, "已新增站點並加入匯入清單");
      pushToast(`已新增站點：${created.code}`, "success");
      return;
    }
    const created = await api.createFixture({
      customer_id: selectedCustomerId.value,
      code: entity.inputCode,
      name: entity.inputCode,
      storage_location: null,
      min_stock_qty: 0,
      description: "由 production 批次匯入建立"
    });
    fixtures.value = [...fixtures.value.filter((row) => row.id !== created.id), created];
    setEntityReady(entity, created.id, created.code, "已新增治具並加入匯入清單");
    pushToast(`已新增治具：${created.code}`, "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : `新增${entity.label}失敗`, "error");
  }
}

function syncMappingRowAfterEntityChange(row: MappingBatchRow): void {
  syncMappingBatchRow(row);
}

function syncRequirementRowAfterEntityChange(row: RequirementBatchRow): void {
  syncRequirementBatchRow(row);
}

function clearMappingBatchImport(): void {
  mappingBatchText.value = "";
  mappingBatchRows.value = [];
}

function clearRequirementBatchImport(): void {
  requirementBatchText.value = "";
  requirementBatchRows.value = [];
}

function syncRequirementStationSelection(): void {
  const availableStations = availableRequirementStations.value;
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
  return availableRequirementStations.value.some((row) => row.id === requirementStationId.value);
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

async function submitMappingBatchImport(): Promise<void> {
  if (!selectedCustomerId.value) {
    pushToast("請先選擇客戶。", "warning");
    return;
  }
  if (mappingBatchRows.value.length === 0) {
    pushToast("請先貼上機種 / 站點資料。", "warning");
    return;
  }
  if (mappingPendingRows.value.length > 0) {
    pushToast("還有待確認的機種 / 站點列，請先完成同一 / 新增 / 略過。", "warning");
    return;
  }
  if (mappingErrorRows.value.length > 0) {
    pushToast("表格中有錯誤列，請先修正後再匯入。", "warning");
    return;
  }

  savingMapping.value = true;
  try {
    const rows = mappingReadyRows.value.map((row) => [row.model.resolvedCode, row.station.resolvedCode]);
    const csv = toCsv(["model_code", "station_code"], rows);
    const result = await api.importModelStationsCsv(selectedCustomerId.value, csv, "batch-model-stations.csv");
    showMappingBatchModal.value = false;
    clearMappingBatchImport();
    await loadData(false);
    await Promise.all([refreshCapacity(), refreshModelQuery()]);
    pushToast(`批次貼上匯入 Mapping 完成，共 ${result.imported_count} 筆。`, "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "批次匯入 mapping 失敗", "error");
  } finally {
    savingMapping.value = false;
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

async function submitRequirementBatchImport(): Promise<void> {
  if (!selectedCustomerId.value) {
    pushToast("請先選擇客戶。", "warning");
    return;
  }
  if (!selectedModel.value?.code) {
    pushToast("請先選擇機種。", "warning");
    return;
  }
  if (requirementBatchRows.value.length === 0) {
    pushToast("請先貼上站點 / 治具 / 數量資料。", "warning");
    return;
  }
  if (requirementPendingRows.value.length > 0) {
    pushToast("還有待確認的站點 / 治具列，請先完成同一 / 新增 / 略過。", "warning");
    return;
  }
  if (requirementErrorRows.value.length > 0) {
    pushToast("表格中有錯誤列，請先修正後再匯入。", "warning");
    return;
  }

  savingRequirement.value = true;
  try {
    const rows = requirementReadyRows.value.map((row) => [
      selectedModel.value!.code,
      row.station.resolvedCode,
      row.fixture.resolvedCode,
      String(row.quantity)
    ]);
    const csv = toCsv(["model_code", "station_code", "fixture_code", "required_qty"], rows);
    const result = await api.importFixtureRequirementsCsv(selectedCustomerId.value, csv, "batch-fixture-requirements.csv");
    showRequirementBatchModal.value = false;
    clearRequirementBatchImport();
    await loadData(false);
    await Promise.all([refreshCapacity(), refreshModelQuery()]);
    pushToast(`批次貼上匯入 Requirement 完成，共 ${result.imported_count} 筆。`, "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "批次匯入 requirement 失敗", "error");
  } finally {
    savingRequirement.value = false;
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

watch(modelId, (value) => {
  mappingModelCodeInput.value = models.value.find((row) => row.id === value)?.code ?? "";
});

watch(mappingStationId, (value) => {
  mappingStationCodeInput.value = stations.value.find((row) => row.id === value)?.code ?? "";
});

watch(requirementStationId, (value) => {
  const selectedCode = availableRequirementStations.value.find((row) => row.id === value)?.code ?? stations.value.find((row) => row.id === value)?.code ?? "";
  requirementStationCodeInput.value = selectedCode;
  if (selectedCode) {
    preferredRequirementStationCode.value = selectedCode;
  }
});

watch(fixtureId, (value) => {
  fixtureCodeInput.value = fixtures.value.find((row) => row.id === value)?.code ?? "";
});

watch(
  requirementStationId,
  async () => {
    await refreshCapacity();
    await refreshModelQuery();
  },
  { flush: "post" }
);

watch(mappingBatchText, () => {
  refreshMappingBatchPreview();
});

watch(requirementBatchText, () => {
  refreshRequirementBatchPreview();
});

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

.page-head-actions {
  display: flex;
  justify-content: flex-end;
}

.row,
.right-stack {
  display: grid;
  gap: 8px;
  min-height: 0;
}

.page-tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--line);
  padding-bottom: 0;
}

.page-tab {
  border: none;
  background: transparent;
  padding: 9px 14px;
  font-size: 13px;
  font-weight: 700;
  color: var(--muted);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 0.15s ease, border-color 0.15s ease;
}

.page-tab:hover {
  color: #344563;
}

.page-tab.active {
  color: var(--blue);
  border-bottom-color: var(--blue);
}

.filter-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.filter-group,
.result-group {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
  padding: 10px 12px;
  display: grid;
  gap: 8px;
  align-content: start;
}

.result-group {
  background: linear-gradient(180deg, #f8fbff 0%, #f2f7ff 100%);
}

.filter-row-label {
  color: var(--muted);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.filter-fields,
.result-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.filter-fields {
  grid-template-columns: minmax(0, 280px);
}

.filter-field {
  display: grid;
  gap: 4px;
}

.filter-field span {
  color: var(--muted);
  font-size: 11px;
}

.filter-field select {
  min-height: 34px;
  padding-block: 5px;
}

.filter-row-meta {
  margin: 0;
  color: #5d6d89;
  font-size: 11px;
  line-height: 1.25;
}

.result-stat {
  display: grid;
  gap: 2px;
}

.result-stat-action {
  border: 1px solid #d7e2f5;
  border-radius: 12px;
  background: #fff;
  padding: 10px 12px;
  text-align: left;
  cursor: pointer;
  transition: transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
}

.result-stat-action:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: #bfd0ef;
  box-shadow: 0 8px 18px rgba(47, 110, 229, 0.1);
}

.result-stat-action:disabled {
  cursor: default;
  opacity: 0.7;
}

.result-stat span {
  color: var(--muted);
  font-size: 11px;
  line-height: 1.2;
}

.result-stat strong {
  color: #22314a;
  font-size: 18px;
  line-height: 1.15;
}

.result-stat.alert strong {
  color: #c24b4b;
}

.result-stat small {
  color: #5d6d89;
  font-size: 11px;
  line-height: 1.25;
}

.panel {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
}

.loading-banner,
.empty-cell {
  padding: 12px 14px;
  border-top: 1px solid var(--line);
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

.single-panel-layout {
  display: grid;
  min-height: 0;
}

.detail-panel {
  min-height: 0;
}

.panel {
  padding: 10px;
  min-width: 0;
  overflow-x: auto;
  overflow-y: auto;
}

.panel h2 {
  margin: 0;
  font-size: 16px;
  color: #222e45;
}

.dependency-callout {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
  padding: 14px 16px;
  border: 1px solid rgba(224, 138, 30, 0.24);
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(255, 248, 237, 0.95) 0%, rgba(255, 252, 246, 0.92) 100%);
}

.dependency-callout strong {
  display: block;
  color: #8f4b00;
  font-size: 14px;
}

.dependency-callout p {
  margin: 4px 0 0;
  color: #6f5a33;
  font-size: 12px;
  line-height: 1.55;
}

.dependency-callout-btn {
  width: auto;
  flex-shrink: 0;
}

.section-head p {
  margin: 3px 0 0;
  color: var(--muted);
  font-size: 12px;
}

.overview-table,
.query-table,
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

.overview-table th,
.overview-table td,
.query-table th,
.query-table td,
.mapping-table th,
.mapping-table td {
  border-bottom: 1px solid var(--line);
  border-right: 1px solid rgba(220, 227, 238, 0.9);
  padding: 8px 10px;
  text-align: left;
  font-size: 12px;
  vertical-align: middle;
}

.compact-query-table th,
.compact-query-table td {
  padding: 7px 10px;
  font-size: 12px;
}

.overview-table th:last-child,
.overview-table td:last-child,
.query-table th:last-child,
.query-table td:last-child,
.mapping-table th:last-child,
.mapping-table td:last-child {
  border-right: none;
}

.overview-table tr:last-child td,
.query-table tr:last-child td,
.mapping-table tr:last-child td {
  border-bottom: none;
}

.overview-table thead th,
.query-table thead th,
.mapping-table thead th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: #f7f9fd;
  color: #52607b;
  font-weight: 700;
}

.overview-table tbody tr:nth-child(even),
.query-table tbody tr:nth-child(even),
.mapping-table tbody tr:nth-child(even) {
  background: #fcfdff;
}

.overview-table tbody tr:hover,
.query-table tbody tr:hover,
.mapping-table tbody tr:hover {
  background: #f3f7ff;
}

.model-cell {
  color: #2f6ee5;
  font-weight: 700;
}

.running {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #1f9f5e;
  font-weight: 700;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #27b56a;
}

.inline-form {
  display: grid;
  gap: 8px;
}

.inline-form.three {
  grid-template-columns: 1fr 1fr 120px;
}

.inline-form.four {
  grid-template-columns: 1fr 1.2fr 120px 120px;
}

.autocomplete-field {
  position: relative;
}

.autocomplete-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  z-index: 20;
  max-height: 220px;
  overflow-y: auto;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #fff;
  box-shadow: 0 14px 28px rgba(28, 47, 84, 0.14);
}

.autocomplete-option {
  width: 100%;
  border: 0;
  border-bottom: 1px solid var(--line);
  background: #fff;
  color: #22314a;
  padding: 8px 10px;
  text-align: left;
  font: inherit;
  cursor: pointer;
}

.autocomplete-option:last-child {
  border-bottom: 0;
}

.autocomplete-option:hover {
  background: #f6f9ff;
}

.form-actions-full {
  grid-column: 1 / -1;
}

select,
input {
  width: 100%;
  border: 1px solid var(--line-strong);
  border-radius: 8px;
  padding: 6px 10px;
  font: inherit;
  background: #fff;
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

.primary-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.mapping-list {
  margin: 8px 0 0;
  padding-left: 18px;
  color: #586887;
  font-size: 12px;
}

.mapping-list li {
  margin: 5px 0;
}

.sub-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin: 10px 0 8px;
}

.sub-head h3 {
  margin: 0;
  font-size: 13px;
  color: #2a3956;
}

.sub-head span {
  color: var(--muted);
  font-size: 12px;
}

.capacity-box {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 10px;
  align-items: stretch;
}

.capacity-left {
  display: grid;
  gap: 10px;
}

.capacity-meter {
  display: grid;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 10px;
  background: linear-gradient(180deg, #f8fbff 0%, #f3f7ff 100%);
  border: 1px solid #dde8fb;
}

.capacity-meter-track {
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
  background: #dfe8f8;
}

.capacity-meter-fill {
  height: 100%;
  border-radius: inherit;
  transition: width 0.2s ease;
}

.capacity-meter-fill.good {
  background: linear-gradient(90deg, #39c37a 0%, #1f9b5a 100%);
}

.capacity-meter-fill.warn {
  background: linear-gradient(90deg, #f4c14b 0%, #ea9f2f 100%);
}

.capacity-meter-fill.danger {
  background: linear-gradient(90deg, #f16d6d 0%, #d94d4d 100%);
}

.capacity-meter-fill.idle {
  background: linear-gradient(90deg, #aeb9cc 0%, #8f9bb3 100%);
}

.capacity-meter-meta {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  color: #5c6983;
  font-size: 12px;
}

.query-inline {
  margin-top: 10px;
  border-top: 1px solid var(--line);
  padding-top: 10px;
  display: grid;
  gap: 8px;
}

.compact-head {
  margin-bottom: 0;
}

.capacity-left p {
  margin: 6px 0;
  color: #5c6983;
  font-size: 13px;
}

.capacity-right {
  border-left: 1px solid var(--line);
  padding-left: 14px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  align-content: center;
}

.capacity-right span {
  color: #6a7893;
  font-size: 12px;
  display: block;
  margin-bottom: 6px;
}

.capacity-right strong {
  color: #25334d;
  font-size: 20px;
}

.capacity-right strong.ok {
  font-size: 18px;
  color: #1d9c58;
}

.capacity-right strong.warn {
  font-size: 18px;
  color: #b97a10;
}

.capacity-right strong.danger {
  font-size: 18px;
  color: #c44747;
}

.head-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.section-head h2 {
  margin-bottom: 0;
}
.toolbar-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.editor-state-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid #d7e0ef;
  background: #f6f8fc;
  color: #51617c;
  font-size: 11px;
  font-weight: 700;
  min-height: 32px;
}

.editor-state-pill.editing {
  border-color: #a9c3f9;
  background: #eef5ff;
  color: var(--blue);
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

.table-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.hidden-input {
  display: none;
}

.meta {
  margin: 0 0 8px;
  color: #7b879f;
  font-size: 12px;
}

.query-table tbody tr:nth-child(even) {
  background: #fcfdff;
}

.query-table tbody tr:hover {
  background: #f3f7ff;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 74px;
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 700;
}

.status-pill.normal {
  color: #1f9b5a;
  background: #e1f6e8;
}

.status-pill.low_stock,
.status-pill.out_of_stock {
  color: #cc4c4c;
  background: #fdeaea;
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

.danger-btn {
  border: 1px solid #e2a0a0;
  border-radius: 8px;
  background: linear-gradient(180deg, #ff7a72 0%, #e95d57 100%);
  color: #fff;
  font-weight: 700;
  padding: 7px 10px;
  min-height: 32px;
  cursor: pointer;
}

.danger-btn:hover {
  border-color: #d97c7c;
  box-shadow: 0 10px 22px rgba(233, 93, 87, 0.2);
}

.danger-btn.small {
  padding: 5px 8px;
  min-height: 28px;
}

.ghost-btn.small {
  padding: 5px 8px;
  min-height: 28px;
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

@media (max-width: 1200px) {
  .top-grid,
  .single-panel-layout,
  .capacity-box,
  .inline-form.three,
  .inline-form.four {
    grid-template-columns: 1fr;
  }

  .filter-row {
    grid-template-columns: 1fr;
  }

  .section-head {
    flex-direction: column;
    align-items: stretch;
  }

  .capacity-right {
    border-left: none;
    border-top: 1px solid #e3e8f0;
    padding-left: 0;
    padding-top: 14px;
  }
}

@media (max-width: 900px) {
  .production-page {
    padding: 8px;
  }

  .filter-fields,
  .result-fields {
    grid-template-columns: 1fr;
  }

  .panel {
    padding: 12px;
  }

  .capacity-box {
    gap: 10px;
  }

  .capacity-right {
    grid-template-columns: 1fr;
  }

  .inline-form.three,
  .inline-form.four {
    grid-template-columns: 1fr;
  }

  .dependency-callout {
    flex-direction: column;
    align-items: stretch;
  }

  .dependency-callout-btn {
    width: 100%;
  }

  .toolbar-actions {
    width: 100%;
  }

  .toolbar-actions button {
    flex: 1 1 120px;
  }

}

@media (max-width: 640px) {
  .page-tabs {
    overflow-x: auto;
  }

  .top-grid {
    gap: 10px;
  }

  .section-head,
  .head-row {
    flex-direction: column;
    align-items: stretch;
  }

  .query-table th,
  .query-table td {
    white-space: nowrap;
  }

  .capacity-right strong {
    font-size: 20px;
  }
}
</style>
