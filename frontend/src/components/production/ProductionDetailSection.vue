<script setup lang="ts">
import UiFormActions from "@/components/UiFormActions.vue";
import UiSectionHeader from "@/components/UiSectionHeader.vue";
import type { Fixture, FixtureRequirementListItem, MachineModel, Station } from "@/types";

const props = defineProps<{
  detailMode: "mapping" | "requirements";
  loading: boolean;
  savingMapping: boolean;
  savingRequirement: boolean;
  editingMappingId: number | null;
  editingRequirementId: number | null;
  selectedModelCode: string;
  selectedStationCode: string;
  selectedModelStationRows: Array<{ id: number; model_id: number; modelCode: string; station_id: number; stationCode: string }>;
  selectedStationRequirementRows: FixtureRequirementListItem[];
  requirementNeedsMapping: boolean;
  mappingModelCodeInput: string;
  mappingStationCodeInput: string;
  requirementStationCodeInput: string;
  fixtureCodeInput: string;
  requiredQty: number;
  openAutocompleteKey: null | "mapping-model" | "mapping-station" | "requirement-station" | "fixture";
  filteredModelSuggestions: MachineModel[];
  filteredStationSuggestions: Station[];
  filteredRequirementStationSuggestions: Station[];
  filteredFixtureSuggestions: Fixture[];
  models: MachineModel[];
  stations: Station[];
  availableRequirementStations: Station[];
  fixtures: Fixture[];
  onOpenMappingBatchModal: () => void;
  onOpenRequirementBatchModal: () => void;
  onImportModelStationsCsv: (file: File) => void | Promise<void>;
  onImportFixtureRequirementsCsv: (file: File) => void | Promise<void>;
  onSaveMapping: () => void | Promise<void>;
  onResetMappingEditor: () => void;
  onStartEditMapping: (row: { id: number; model_id: number; station_id: number }) => void;
  onRemoveMapping: (id: number) => void | Promise<void>;
  onSaveRequirement: () => void | Promise<void>;
  onResetRequirementEditor: () => void;
  onStartEditRequirement: (row: { id: number; station_id: number; fixture_id: number; required_qty: number }) => void;
  onRemoveRequirement: (id: number) => void | Promise<void>;
  onOpenMappingPage: () => void;
  onMappingModelFocus: () => void;
  onMappingModelInput: (value: string) => void;
  onMappingModelBlur: () => void;
  onSelectModelSuggestion: (code: string) => void;
  onMappingStationFocus: () => void;
  onMappingStationInput: (value: string) => void;
  onMappingStationBlur: () => void;
  onSelectMappingStationSuggestion: (code: string) => void;
  onRequirementStationFocus: () => void;
  onRequirementStationInput: (value: string) => void;
  onRequirementStationBlur: () => void;
  onSelectRequirementStationSuggestion: (code: string) => void;
  onFixtureFocus: () => void;
  onFixtureInput: (value: string) => void;
  onFixtureBlur: () => void;
  onSelectFixtureSuggestion: (code: string) => void;
  onRequiredQtyChange: (value: number) => void;
}>();

function handleModelFileChange(event: Event): void {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) {
    return;
  }
  void props.onImportModelStationsCsv(file);
  (event.target as HTMLInputElement).value = "";
}

function handleRequirementFileChange(event: Event): void {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) {
    return;
  }
  void props.onImportFixtureRequirementsCsv(file);
  (event.target as HTMLInputElement).value = "";
}
</script>

<template>
  <section class="single-panel-layout">
    <article v-if="detailMode === 'mapping'" class="panel detail-panel" data-tour="production-mapping-panel">
      <UiSectionHeader class="section-head" title="Model-Station Mapping">
        <template #actions>
          <div class="toolbar-actions">
          <span class="editor-state-pill" :class="{ editing: editingMappingId !== null }">
            {{ editingMappingId === null ? "新增機種站點對應" : "編輯機種站點對應" }}
          </span>
          <button class="ghost-btn" type="button" :disabled="loading || savingMapping" @click="onOpenMappingBatchModal">批次貼上匯入</button>
          <input type="file" accept=".csv,text/csv" class="hidden-input" @change="handleModelFileChange" />
          </div>
        </template>
      </UiSectionHeader>
      <form class="inline-form three" data-tour="production-mapping-form" @submit.prevent="onSaveMapping">
        <div class="autocomplete-field">
          <input
            :value="mappingModelCodeInput"
            :disabled="loading || savingMapping"
            placeholder="輸入機種代碼"
            autocomplete="off"
            spellcheck="false"
            @focus="onMappingModelFocus"
            @click="onMappingModelFocus"
            @input="onMappingModelInput(($event.target as HTMLInputElement).value)"
            @blur="onMappingModelBlur"
          />
          <div v-if="openAutocompleteKey === 'mapping-model'" class="autocomplete-menu">
            <button v-for="model in filteredModelSuggestions" :key="`mapping-model-${model.id}`" class="autocomplete-option" type="button" @mousedown.prevent="onSelectModelSuggestion(model.code)">
              {{ model.code }}
            </button>
          </div>
        </div>
        <div class="autocomplete-field">
          <input
            :value="mappingStationCodeInput"
            :disabled="loading || savingMapping"
            placeholder="輸入站點代碼"
            autocomplete="off"
            spellcheck="false"
            @focus="onMappingStationFocus"
            @click="onMappingStationFocus"
            @input="onMappingStationInput(($event.target as HTMLInputElement).value)"
            @blur="onMappingStationBlur"
          />
          <div v-if="openAutocompleteKey === 'mapping-station'" class="autocomplete-menu">
            <button v-for="station in filteredStationSuggestions" :key="`mapping-station-${station.id}`" class="autocomplete-option" type="button" @mousedown.prevent="onSelectMappingStationSuggestion(station.code)">
              {{ station.code }}
            </button>
          </div>
        </div>
        <UiFormActions
          class="form-actions-full"
          :editing="editingMappingId !== null"
          :saving="savingMapping"
          submit-label="新增 / 更新"
          saving-label="處理中..."
          cancel-label="取消"
          :show-delete="false"
          :show-state="false"
          @cancel="onResetMappingEditor"
        />
      </form>
      <div class="sub-head">
        <h3>目前機種：{{ selectedModelCode || "-" }}</h3>
        <span>{{ selectedModelStationRows.length }} 筆站點</span>
      </div>
      <table class="mapping-table" data-tour="production-mapping-list">
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
              <button class="ghost-btn small" type="button" @click="onStartEditMapping(item)">編輯</button>
              <button class="danger-btn small" type="button" @click="onRemoveMapping(item.id)">刪除</button>
            </td>
          </tr>
          <tr v-if="!loading && selectedModelStationRows.length === 0">
            <td colspan="3" class="empty-cell">此機種尚未綁定站點。</td>
          </tr>
        </tbody>
      </table>
    </article>

    <article v-else class="panel detail-panel" data-tour="production-requirement-panel">
      <UiSectionHeader class="section-head" title="Fixture Requirement">
        <template #actions>
          <div class="toolbar-actions">
          <span class="editor-state-pill" :class="{ editing: editingRequirementId !== null }">
            {{ editingRequirementId === null ? "新增治具需求" : "編輯治具需求" }}
          </span>
          <button class="ghost-btn" type="button" :disabled="loading || savingRequirement" @click="onOpenRequirementBatchModal">批次貼上匯入</button>
          <input type="file" accept=".csv,text/csv" class="hidden-input" @change="handleRequirementFileChange" />
          </div>
        </template>
      </UiSectionHeader>
      <div v-if="requirementNeedsMapping" class="dependency-callout">
        <div>
          <strong>請先建立機種站點對應</strong>
          <p>目前機種 {{ selectedModelCode || "-" }} 尚未綁定任何站點。治具需求必須先依附在 Mapping 的站點上，請先完成站點對應再回來設定。</p>
        </div>
        <button class="primary-btn dependency-callout-btn" type="button" @click="onOpenMappingPage">前往 Mapping</button>
      </div>
      <form class="inline-form four" data-tour="production-requirement-form" @submit.prevent="onSaveRequirement">
        <div class="autocomplete-field">
          <input
            :value="requirementStationCodeInput"
            :disabled="loading || savingRequirement || requirementNeedsMapping"
            :placeholder="requirementNeedsMapping ? '請先建立此機種的站點對應' : '輸入站點代碼'"
            autocomplete="off"
            spellcheck="false"
            @focus="onRequirementStationFocus"
            @click="onRequirementStationFocus"
            @input="onRequirementStationInput(($event.target as HTMLInputElement).value)"
            @blur="onRequirementStationBlur"
          />
          <div v-if="openAutocompleteKey === 'requirement-station'" class="autocomplete-menu">
            <button v-for="station in filteredRequirementStationSuggestions" :key="`req-station-${station.id}`" class="autocomplete-option" type="button" @mousedown.prevent="onSelectRequirementStationSuggestion(station.code)">
              {{ station.code }}
            </button>
          </div>
        </div>
        <div class="autocomplete-field">
          <input
            :value="fixtureCodeInput"
            :disabled="loading || savingRequirement"
            placeholder="輸入治具代碼"
            autocomplete="off"
            spellcheck="false"
            @focus="onFixtureFocus"
            @click="onFixtureFocus"
            @input="onFixtureInput(($event.target as HTMLInputElement).value)"
            @blur="onFixtureBlur"
          />
          <div v-if="openAutocompleteKey === 'fixture'" class="autocomplete-menu">
            <button v-for="fixture in filteredFixtureSuggestions" :key="`req-fixture-${fixture.id}`" class="autocomplete-option" type="button" @mousedown.prevent="onSelectFixtureSuggestion(fixture.code)">
              {{ fixture.code }}
            </button>
          </div>
        </div>
        <input :value="requiredQty" type="number" min="1" :disabled="loading || savingRequirement" @input="onRequiredQtyChange(Number.parseInt(($event.target as HTMLInputElement).value, 10) || 1)" />
        <UiFormActions
          class="form-actions-full"
          :editing="editingRequirementId !== null"
          :saving="savingRequirement"
          submit-label="儲存 / 更新"
          saving-label="儲存中..."
          cancel-label="取消"
          :show-delete="false"
          :show-state="false"
          @cancel="onResetRequirementEditor"
        />
      </form>
      <div class="sub-head">
        <h3>目前站點：{{ selectedStationCode || "-" }}</h3>
        <span>{{ selectedStationRequirementRows.length }} 筆治具</span>
      </div>
      <table class="mapping-table" data-tour="production-requirement-list">
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
              <button class="ghost-btn small" type="button" @click="onStartEditRequirement(item)">編輯</button>
              <button class="danger-btn small" type="button" @click="onRemoveRequirement(item.id)">刪除</button>
            </td>
          </tr>
          <tr v-if="!loading && selectedStationRequirementRows.length === 0">
            <td colspan="5" class="empty-cell">此站點尚未設定治具需求。</td>
          </tr>
        </tbody>
      </table>
    </article>
  </section>
</template>

<style scoped>
.single-panel-layout {
  display: grid;
  min-height: 0;
}

.detail-panel {
  min-height: 0;
}

.panel {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
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

.section-head {
  margin-bottom: 8px;
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
  display: grid;
  max-height: 220px;
  overflow: auto;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 16px 34px rgba(17, 24, 39, 0.12);
}

.autocomplete-option {
  border: 0;
  border-bottom: 1px solid rgba(220, 227, 238, 0.9);
  background: #fff;
  padding: 9px 12px;
  text-align: left;
  color: #31435e;
  font: inherit;
  cursor: pointer;
}

.autocomplete-option:last-child {
  border-bottom: none;
}

.autocomplete-option:hover {
  background: #f3f7ff;
}

.sub-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin: 10px 0 8px;
}

.sub-head h3 {
  margin: 0;
  color: #22314a;
  font-size: 14px;
}

.sub-head span {
  color: var(--muted);
  font-size: 12px;
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

.table-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.hidden-input {
  display: none;
}

.empty-cell {
  padding: 12px 14px;
  border-top: 1px solid var(--line);
  color: #56657f;
  background: #f8fbff;
  text-align: center;
}

input {
  width: 100%;
  min-height: 36px;
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  padding: 8px 10px;
  background: #fff;
  font: inherit;
}

@media (max-width: 1200px) {
  .single-panel-layout,
  .inline-form.three,
  .inline-form.four {
    grid-template-columns: 1fr;
  }

  .section-head {
    flex-direction: column;
    align-items: stretch;
  }
}

@media (max-width: 900px) {
  .panel {
    padding: 12px;
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
</style>
