<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { api } from "@/api";
import { selectedCustomerId } from "@/appState";
import { pushToast } from "@/toastState";
import type { Fixture, FixtureRequirementListItem, MachineModel, ModelQuery, ModelStation, Station, StationCapacity } from "@/types";
import UiFormActions from "@/components/UiFormActions.vue";
import ProductionCapacityPanel from "@/components/production/ProductionCapacityPanel.vue";

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
const fixtureId = ref<number | null>(null);
const requiredQty = ref(1);

const savingMapping = ref(false);
const savingRequirement = ref(false);
const loading = ref(false);
const loadedAt = ref("");
const updatedAt = ref("");
const mappingImportInput = ref<HTMLInputElement | null>(null);
const requirementImportInput = ref<HTMLInputElement | null>(null);
const editingMappingId = ref<number | null>(null);
const editingRequirementId = ref<number | null>(null);

function nowString(): string {
  return new Date().toLocaleString("zh-TW", { hour12: false });
}

function touchUpdatedAt(): void {
  updatedAt.value = nowString();
}

const selectedModel = computed(() => models.value.find((row) => row.id === modelId.value) ?? null);
const selectedStation = computed(() => stations.value.find((row) => row.id === requirementStationId.value) ?? null);
const modelMap = computed(() => new Map(models.value.map((row) => [row.id, row.code])));
const stationMap = computed(() => new Map(stations.value.map((row) => [row.id, row.code])));
const capacityCurrentOpen = computed(() => stationCapacity.value?.current_open_station_count ?? 0);
const capacityMaxOpen = computed(() => stationCapacity.value?.max_open_station_count ?? 0);
const capacityUsagePercent = computed(() => {
  if (!capacityMaxOpen.value) return 0;
  return Math.min(100, Math.round((capacityCurrentOpen.value / capacityMaxOpen.value) * 100));
});
const capacityState = computed(() => {
  if (!capacityMaxOpen.value) return "idle";
  if (capacityUsagePercent.value >= 100) return "danger";
  if (capacityUsagePercent.value >= 80) return "warn";
  return "good";
});
const capacityRemaining = computed(() => Math.max(capacityMaxOpen.value - capacityCurrentOpen.value, 0));

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
const selectedStationRequirementRows = computed(() =>
  fixtureRequirements.value.filter((row) => row.station_id === requirementStationId.value)
);

function resetMappingEditor(): void {
  editingMappingId.value = null;
}

function resetRequirementEditor(): void {
  editingRequirementId.value = null;
}

function startEditMapping(row: { id: number; model_id: number; station_id: number }): void {
  modelId.value = row.model_id;
  mappingStationId.value = row.station_id;
  editingMappingId.value = row.id;
}

function startEditRequirement(row: { id: number; station_id: number; fixture_id: number; required_qty: number }): void {
  requirementStationId.value = row.station_id;
  fixtureId.value = row.fixture_id;
  requiredQty.value = row.required_qty;
  editingRequirementId.value = row.id;
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

async function loadData(): Promise<void> {
  loading.value = true;
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
    mappingStationId.value = stationRows.find((row) => row.id === mappingStationId.value)?.id ?? stationRows[0]?.id ?? null;
    requirementStationId.value = stationRows.find((row) => row.id === requirementStationId.value)?.id ?? stationRows[0]?.id ?? null;
    fixtureId.value = fixtureRows.find((row) => row.id === fixtureId.value)?.id ?? fixtureRows[0]?.id ?? null;
    if (editingMappingId.value !== null && !mappingRows.some((row) => row.id === editingMappingId.value)) {
      resetMappingEditor();
    }
    if (editingRequirementId.value !== null && !requirementRows.some((row) => row.id === editingRequirementId.value)) {
      resetRequirementEditor();
    }

    if (!loadedAt.value) loadedAt.value = nowString();
    touchUpdatedAt();
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "載入失敗", "error");
  } finally {
    loading.value = false;
  }
}

async function saveMapping(): Promise<void> {
  if (!modelId.value || !mappingStationId.value) return;
  savingMapping.value = true;
  try {
    if (!selectedCustomerId.value) {
      pushToast("請先選擇客戶。", "warning");
      return;
    }
    const payload = { customer_id: selectedCustomerId.value, model_id: modelId.value, station_id: mappingStationId.value };
    if (editingMappingId.value === null) {
      await api.createModelStation(payload);
      pushToast("Model-Station Mapping 已新增", "success");
    } else {
      await api.updateModelStation(editingMappingId.value, payload);
      resetMappingEditor();
      pushToast("Model-Station Mapping 已更新", "success");
    }
    await loadData();
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
    if (editingMappingId.value === rowId) resetMappingEditor();
    await loadData();
    await Promise.all([refreshCapacity(), refreshModelQuery()]);
    pushToast("Mapping 已刪除", "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "刪除 mapping 失敗", "error");
  }
}

async function saveRequirement(): Promise<void> {
  if (!requirementStationId.value || !fixtureId.value) return;
  savingRequirement.value = true;
  try {
    if (!selectedCustomerId.value) {
      pushToast("請先選擇客戶。", "warning");
      return;
    }
    const payload = {
      customer_id: selectedCustomerId.value,
      station_id: requirementStationId.value,
      fixture_id: fixtureId.value,
      required_qty: requiredQty.value
    };
    if (editingRequirementId.value === null) {
      await api.createFixtureRequirement(payload);
      pushToast("Fixture Requirement 已儲存", "success");
    } else {
      await api.updateFixtureRequirement(editingRequirementId.value, payload);
      resetRequirementEditor();
      pushToast("Fixture Requirement 已更新", "success");
    }
    await loadData();
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
    if (editingRequirementId.value === requirementId) resetRequirementEditor();
    await loadData();
    await Promise.all([refreshCapacity(), refreshModelQuery()]);
    pushToast("Requirement 已刪除", "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "刪除 requirement 失敗", "error");
  }
}

async function refreshCapacity(): Promise<void> {
  if (!requirementStationId.value) return;
  try {
    stationCapacity.value = await api.getStationCapacity(requirementStationId.value, selectedCustomerId.value ?? undefined);
    touchUpdatedAt();
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "刷新 capacity 失敗", "error");
  }
}

async function refreshModelQuery(): Promise<void> {
  if (!modelId.value) return;
  try {
    modelQuery.value = await api.getModelQuery(modelId.value, selectedCustomerId.value ?? undefined);
    touchUpdatedAt();
  } catch (err) {
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

function triggerModelStationImport(): void {
  mappingImportInput.value?.click();
}

async function importModelStationsCsv(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  try {
    if (!selectedCustomerId.value) {
      pushToast("請先選擇客戶。", "warning");
      return;
    }
    const result = await api.importModelStationsCsv(selectedCustomerId.value ?? undefined, await file.text(), file.name);
    await loadData();
    pushToast(`匯入 mapping 完成，共 ${result.imported_count} 筆。`, "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "匯入 mapping 失敗", "error");
  } finally {
    input.value = "";
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

function triggerFixtureRequirementImport(): void {
  requirementImportInput.value?.click();
}

async function importFixtureRequirementsCsv(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  try {
    if (!selectedCustomerId.value) {
      pushToast("請先選擇客戶。", "warning");
      return;
    }
    const result = await api.importFixtureRequirementsCsv(selectedCustomerId.value ?? undefined, await file.text(), file.name);
    await loadData();
    await Promise.all([refreshCapacity(), refreshModelQuery()]);
    pushToast(`匯入 requirement 完成，共 ${result.imported_count} 筆。`, "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "匯入 requirement 失敗", "error");
  } finally {
    input.value = "";
  }
}

watch(
  modelId,
  async () => {
    await refreshModelQuery();
  },
  { flush: "post" }
);

watch(
  requirementStationId,
  async () => {
    await refreshCapacity();
  },
  { flush: "post" }
);

watch(selectedCustomerId, async () => {
  await loadData();
  await Promise.all([refreshCapacity(), refreshModelQuery()]);
});

onMounted(async () => {
  await loadData();
  await Promise.all([refreshCapacity(), refreshModelQuery()]);
});
</script>

<template>
  <div class="production-page">
    <section class="summary-row">
      <article class="summary-card">
        <span>機種</span>
        <strong>{{ selectedModel?.code || "-" }}</strong>
        <p>建立時間 {{ loadedAt || "-" }}</p>
      </article>
      <article class="summary-card">
        <span>站點數</span>
        <strong>{{ stations.length }}</strong>
        <p>更新時間 {{ updatedAt || "-" }}</p>
      </article>
      <article class="summary-card">
        <span>治具種類</span>
        <strong>{{ fixtures.length }}</strong>
        <p>Mapping {{ mappings.length }} 筆</p>
      </article>
      <article class="summary-card">
        <span>瓶頸治具</span>
        <strong>{{ stationCapacity?.bottleneck_fixture_code || "-" }}</strong>
        <p>可開站 {{ stationCapacity?.max_open_station_count ?? 0 }}</p>
      </article>
    </section>

    <section class="top-grid">
      <ProductionCapacityPanel
        :loading="loading"
        :selected-model-code="selectedModel?.code || ''"
        :selected-station-code="selectedStation?.code || ''"
        :station-capacity="stationCapacity"
        :model-query="modelQuery"
        :capacity-current-open="capacityCurrentOpen"
        :capacity-max-open="capacityMaxOpen"
        :capacity-remaining="capacityRemaining"
        :capacity-usage-percent="capacityUsagePercent"
        :capacity-state="capacityState"
        @refresh-capacity="refreshCapacity"
        @refresh-model-query="refreshModelQuery"
      />

      <div class="right-stack">
        <article class="panel">
          <div class="section-head">
            <h2>Model-Station Mapping</h2>
            <div class="toolbar-actions">
              <button class="ghost-btn" type="button" :disabled="loading || savingMapping" @click="downloadModelStationTemplate">範本</button>
              <button class="ghost-btn" type="button" :disabled="loading || savingMapping" @click="triggerModelStationImport">匯入</button>
              <button class="ghost-btn" type="button" :disabled="loading || savingMapping" @click="exportModelStationsCsv">匯出</button>
              <input ref="mappingImportInput" type="file" accept=".csv,text/csv" class="hidden-input" @change="importModelStationsCsv" />
            </div>
          </div>
          <form class="inline-form three" @submit.prevent="saveMapping">
            <select v-model.number="modelId" :disabled="loading || savingMapping">
              <option v-for="model in models" :key="model.id" :value="model.id">{{ model.code }}</option>
            </select>
            <select v-model.number="mappingStationId" :disabled="loading || savingMapping">
              <option v-for="station in stations" :key="station.id" :value="station.id">{{ station.code }}</option>
            </select>
            <UiFormActions
              class="form-actions-full"
              :editing="editingMappingId !== null"
              :saving="loading || savingMapping"
              submit-label="新增 / 更新"
              saving-label="處理中..."
              cancel-label="取消"
              :show-delete="false"
              :state-text="editingMappingId === null ? '新增機種站點對應' : '編輯機種站點對應'"
              @cancel="resetMappingEditor"
            />
          </form>
          <div class="sub-head">
            <h3>目前機種：{{ selectedModel?.code || "-" }}</h3>
            <span>{{ selectedModelStationRows.length }} 筆站點</span>
          </div>
          <table class="mapping-table">
            <thead>
              <tr>
                <th>站點</th>
                <th>對應機種</th>
                <th>動作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in selectedModelStationRows" :key="item.id">
                <td>{{ item.stationCode }}</td>
                <td>{{ item.modelCode }}</td>
                <td class="table-actions">
                  <button class="ghost-btn small" type="button" @click="startEditMapping(item)">編輯</button>
                  <button class="danger-btn small" type="button" @click="removeMapping(item.id)">刪除</button>
                </td>
              </tr>
              <tr v-if="!loading && selectedModelStationRows.length === 0">
                <td colspan="3" class="empty-cell">此機種尚未綁定站點。</td>
              </tr>
            </tbody>
          </table>
        </article>

        <article class="panel">
          <div class="section-head">
            <h2>Fixture Requirement</h2>
            <div class="toolbar-actions">
              <button class="ghost-btn" type="button" :disabled="loading || savingRequirement" @click="downloadFixtureRequirementTemplate">範本</button>
              <button class="ghost-btn" type="button" :disabled="loading || savingRequirement" @click="triggerFixtureRequirementImport">匯入</button>
              <button class="ghost-btn" type="button" :disabled="loading || savingRequirement" @click="exportFixtureRequirementsCsv">匯出</button>
              <input ref="requirementImportInput" type="file" accept=".csv,text/csv" class="hidden-input" @change="importFixtureRequirementsCsv" />
            </div>
          </div>
          <form class="inline-form four" @submit.prevent="saveRequirement">
            <select v-model.number="requirementStationId" :disabled="loading || savingRequirement">
              <option v-for="station in stations" :key="`req-${station.id}`" :value="station.id">{{ station.code }}</option>
            </select>
            <select v-model.number="fixtureId" :disabled="loading || savingRequirement">
              <option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.code }}</option>
            </select>
            <input v-model.number="requiredQty" type="number" min="1" :disabled="loading || savingRequirement" />
            <UiFormActions
              class="form-actions-full"
              :editing="editingRequirementId !== null"
              :saving="loading || savingRequirement"
              submit-label="儲存 / 更新"
              saving-label="儲存中..."
              cancel-label="取消"
              :show-delete="false"
              :state-text="editingRequirementId === null ? '新增治具需求' : '編輯治具需求'"
              @cancel="resetRequirementEditor"
            />
          </form>
          <div class="sub-head">
            <h3>目前站點：{{ selectedStation?.code || "-" }}</h3>
            <span>{{ selectedStationRequirementRows.length }} 筆治具</span>
          </div>
          <table class="mapping-table">
            <thead>
              <tr>
                <th>站點</th>
                <th>治具</th>
                <th>治具名稱</th>
                <th>數量</th>
                <th>動作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in selectedStationRequirementRows" :key="item.id">
                <td>{{ item.station_code }}</td>
                <td>{{ item.fixture_code }}</td>
                <td>{{ item.fixture_name }}</td>
                <td>{{ item.required_qty }}</td>
                <td class="table-actions">
                  <button class="ghost-btn small" type="button" @click="startEditRequirement(item)">編輯</button>
                  <button class="danger-btn small" type="button" @click="removeRequirement(item.id)">刪除</button>
                </td>
              </tr>
              <tr v-if="!loading && selectedStationRequirementRows.length === 0">
                <td colspan="5" class="empty-cell">此站點尚未設定治具需求。</td>
              </tr>
            </tbody>
          </table>
        </article>
      </div>
    </section>

  </div>
</template>

<style scoped>
.production-page {
  height: 100%;
  overflow: hidden;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 8px;
  padding: 8px;
  background: #fff;
}

.row,
.right-stack {
  display: grid;
  gap: 8px;
  min-height: 0;
}

.summary-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.summary-card,
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

.summary-card {
  padding: 9px 10px;
  display: grid;
  gap: 4px;
}

.summary-card span {
  color: var(--muted);
  font-size: 12px;
}

.summary-card strong {
  color: #22314a;
  font-size: 20px;
}

.summary-card p {
  margin: 0;
  color: #5d6d89;
  font-size: 12px;
}

.top-grid {
  display: grid;
  grid-template-columns: 1.02fr 1fr;
  gap: 8px;
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
  border-radius: 10px;
  overflow: hidden;
  min-width: 100%;
}

.overview-table th,
.overview-table td,
.query-table th,
.query-table td,
.mapping-table th,
.mapping-table td {
  border-bottom: 1px solid var(--line);
  border-right: 1px solid var(--line);
  padding: 4px 8px;
  text-align: left;
  font-size: 12px;
}

.compact-query-table th,
.compact-query-table td {
  padding: 3px 6px;
  font-size: 11px;
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
  background: #f8fafe;
  color: #52607a;
  font-weight: 700;
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
  .summary-row,
  .top-grid,
  .capacity-box,
  .inline-form.three,
  .inline-form.four {
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

  .summary-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
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

  .toolbar-actions {
    width: 100%;
  }

  .toolbar-actions button {
    flex: 1 1 120px;
  }
}

@media (max-width: 640px) {
  .summary-row {
    grid-template-columns: 1fr;
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

