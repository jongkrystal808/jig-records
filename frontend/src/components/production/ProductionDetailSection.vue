<script setup lang="ts">
import UiAutocompleteInput from "@/components/UiAutocompleteInput.vue";
import UiFormActions from "@/components/UiFormActions.vue";
import UiSectionHeader from "@/components/UiSectionHeader.vue";
import UiStatusPill from "@/components/UiStatusPill.vue";
import type { Fixture, FixtureRequirementListItem, Station } from "@/types";
import type { ProjectedStationCapacity } from "@/utils/productionCapacityPreview";

type StationWorkspaceRow = {
  id: number;
  model_id: number;
  modelCode: string;
  station_id: number;
  stationCode: string;
  stationName: string;
  maxOpenStationCount: number | null;
  bottleneckFixtureCode: string | null;
};

type RequirementWorkspaceRow = FixtureRequirementListItem & {
  stockQty: number;
  maxOpenStationCount: number;
  isBottleneck: boolean;
};

const props = defineProps<{
  canEdit: boolean;
  loading: boolean;
  savingMapping: boolean;
  savingRequirement: boolean;
  editingMappingId: number | null;
  editingRequirementId: number | null;
  selectedModelCode: string;
  selectedRequirementStationId: number | null;
  selectedStationCode: string;
  selectedStationName: string;
  stationCapacityCount: number | null;
  stationBottleneckFixtureCode: string;
  projectedCapacity: ProjectedStationCapacity | null;
  selectedFixtureAlreadyConfigured: boolean;
  selectedModelStationRows: StationWorkspaceRow[];
  selectedStationRequirementRows: RequirementWorkspaceRow[];
  sourceRequirementCount: number;
  mappingStationCodeInput: string;
  fixtureCodeInput: string;
  requiredQty: number;
  openAutocompleteKey: null | "mapping-model" | "mapping-station" | "requirement-station" | "fixture";
  filteredStationSuggestions: Station[];
  filteredFixtureSuggestions: Fixture[];
  onOpenMappingBatchModal: () => void;
  onOpenRequirementBatchModal: () => void;
  onOpenRequirementCopyModal: () => void;
  onImportModelStationsCsv: (file: File) => void | Promise<void>;
  onImportFixtureRequirementsCsv: (file: File) => void | Promise<void>;
  onSaveMapping: () => void | Promise<void>;
  onResetMappingEditor: () => void;
  onStartEditMapping: (row: { id: number; model_id: number; station_id: number }) => void;
  onRemoveMapping: (id: number) => void | Promise<void>;
  onSelectMappingStation: (stationId: number) => void;
  onSaveRequirement: () => void | Promise<void>;
  onResetRequirementEditor: () => void;
  onStartEditRequirement: (row: { id: number; station_id: number; fixture_id: number; required_qty: number }) => void;
  onRemoveRequirement: (id: number) => void | Promise<void>;
  onMappingStationFocus: () => void;
  onMappingStationInput: (value: string) => void;
  onMappingStationBlur: () => void;
  onSelectMappingStationSuggestion: (code: string) => void;
  onFixtureFocus: () => void;
  onFixtureInput: (value: string) => void;
  onFixtureBlur: () => void;
  onSelectFixtureSuggestion: (code: string) => void;
  onRequiredQtyChange: (value: number) => void;
}>();

function handleModelFileChange(event: Event): void {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  void props.onImportModelStationsCsv(file);
  input.value = "";
}

function handleRequirementFileChange(event: Event): void {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  void props.onImportFixtureRequirementsCsv(file);
  input.value = "";
}

function capacityTone(row: RequirementWorkspaceRow): "normal" | "warn" | "danger" {
  if (row.maxOpenStationCount <= 0) return "danger";
  return row.isBottleneck ? "warn" : "normal";
}

function capacityLabel(row: RequirementWorkspaceRow): string {
  if (row.maxOpenStationCount <= 0) return "無法開站";
  return row.isBottleneck ? "限制治具" : "供應正常";
}

function previewTone(): string {
  if (!props.projectedCapacity || props.stationCapacityCount === null) return "neutral";
  if (props.projectedCapacity.maxOpenStationCount < props.stationCapacityCount) return "decrease";
  if (props.projectedCapacity.maxOpenStationCount > props.stationCapacityCount) return "increase";
  return "neutral";
}
</script>

<template>
  <section class="workspace-layout">
    <article class="panel station-workspace" data-tour="production-mapping-panel">
      <UiSectionHeader
        class="section-head"
        title="① 選擇站點"
        :description="`目前機種：${selectedModelCode || '-'}。點選站點後，在右側配置治具需求。`"
      >
        <template #actions>
          <span class="count-pill">{{ selectedModelStationRows.length }} 個站點</span>
        </template>
      </UiSectionHeader>

      <div v-if="canEdit" class="station-create-card">
        <div class="editor-title-row">
          <div>
            <strong>{{ editingMappingId === null ? "加入站點" : "更換站點" }}</strong>
            <span>機種已由上方選擇，不需要再次輸入。</span>
          </div>
          <button class="ghost-btn small" type="button" :disabled="loading || savingMapping" @click="onOpenMappingBatchModal">
            批次匯入
          </button>
          <input type="file" accept=".csv,text/csv" class="hidden-input" @change="handleModelFileChange" />
        </div>

        <form class="context-form" data-tour="production-mapping-form" @submit.prevent="onSaveMapping">
          <label class="context-field">
            <span>加入 {{ selectedModelCode || "目前機種" }} 的站點</span>
            <UiAutocompleteInput
              :model-value="mappingStationCodeInput"
              :disabled="loading || savingMapping || !selectedModelCode"
              placeholder="搜尋站點編號或名稱"
              :menu-open="openAutocompleteKey === 'mapping-station'"
              :suggestions="filteredStationSuggestions"
              @update:model-value="onMappingStationInput"
              @focus="onMappingStationFocus"
              @blur="onMappingStationBlur"
              @select="onSelectMappingStationSuggestion"
            />
          </label>
          <UiFormActions
            class="compact-actions"
            :editing="editingMappingId !== null"
            :saving="savingMapping"
            :submit-label="editingMappingId === null ? '加入站點' : '儲存變更'"
            saving-label="處理中..."
            cancel-label="取消"
            :show-delete="false"
            :show-state="false"
            @cancel="onResetMappingEditor"
          />
        </form>
      </div>
      <p v-else class="read-only-note">目前為訪客模式，可查看設定但不能修改。</p>

      <div class="station-list" data-tour="production-mapping-list" role="list" aria-label="目前機種的站點">
        <div
          v-for="item in selectedModelStationRows"
          :key="item.id"
          class="station-row"
          :class="{ selected: selectedRequirementStationId === item.station_id }"
          role="listitem"
        >
          <button
            class="station-select"
            type="button"
            :aria-pressed="selectedRequirementStationId === item.station_id"
            @click="onSelectMappingStation(item.station_id)"
          >
            <span class="station-identity">
              <strong>{{ item.stationCode }}</strong>
              <small>{{ item.stationName || "未命名站點" }}</small>
            </span>
            <span class="station-capacity">
              <small>最大開站</small>
              <strong v-if="item.maxOpenStationCount !== null">{{ item.maxOpenStationCount }}</strong>
              <em v-else>待配置</em>
            </span>
          </button>
          <div v-if="canEdit" class="row-actions">
            <button class="ghost-btn small" type="button" @click="onStartEditMapping(item)">編輯</button>
            <button class="danger-btn small" type="button" @click="onRemoveMapping(item.id)">刪除</button>
          </div>
        </div>

        <div v-if="!loading && selectedModelStationRows.length === 0" class="empty-state">
          <strong>此機種尚未設定站點</strong>
          <span v-if="canEdit">請從上方搜尋站點，建立第一個站點設定。</span>
          <span v-else>請由具編輯權限的人員建立站點設定。</span>
        </div>
      </div>
    </article>

    <article class="panel requirement-workspace" data-tour="production-requirement-panel">
      <template v-if="selectedRequirementStationId !== null">
        <UiSectionHeader
          class="section-head"
          :title="`② 配置 ${selectedStationCode} 的治具`"
          :description="selectedStationName || '每筆數量代表開一站需要幾套治具。'"
        >
          <template #actions>
            <div class="capacity-summary">
              <span>最大開站</span>
              <strong>{{ stationCapacityCount ?? 0 }}</strong>
              <small>{{ stationBottleneckFixtureCode ? `限制：${stationBottleneckFixtureCode}` : "尚無限制治具" }}</small>
            </div>
          </template>
        </UiSectionHeader>

        <div v-if="canEdit" class="requirement-editor">
          <div class="editor-title-row">
            <div>
              <strong>{{ editingRequirementId === null ? "加入治具需求" : "編輯治具需求" }}</strong>
              <span>站點已固定為 {{ selectedStationCode }}，只需選治具與每站數量。</span>
            </div>
            <div class="editor-buttons">
              <button
                class="ghost-btn small"
                type="button"
                :disabled="loading || savingRequirement || sourceRequirementCount === 0"
                @click="onOpenRequirementCopyModal"
              >
                複製此站設定
              </button>
              <button class="ghost-btn small" type="button" :disabled="loading || savingRequirement" @click="onOpenRequirementBatchModal">
                批次匯入
              </button>
            </div>
            <input type="file" accept=".csv,text/csv" class="hidden-input" @change="handleRequirementFileChange" />
          </div>

          <form class="requirement-form" data-tour="production-requirement-form" @submit.prevent="onSaveRequirement">
            <label class="context-field">
              <span>治具</span>
              <UiAutocompleteInput
                :model-value="fixtureCodeInput"
                :disabled="loading || savingRequirement"
                placeholder="搜尋治具編號或名稱"
                :menu-open="openAutocompleteKey === 'fixture'"
                :suggestions="filteredFixtureSuggestions"
                @update:model-value="onFixtureInput"
                @focus="onFixtureFocus"
                @blur="onFixtureBlur"
                @select="onSelectFixtureSuggestion"
              />
            </label>
            <label class="context-field quantity-field">
              <span>每站需求量</span>
              <input
                :value="requiredQty"
                type="number"
                min="1"
                :disabled="loading || savingRequirement"
                @input="onRequiredQtyChange(Number.parseInt(($event.target as HTMLInputElement).value, 10) || 1)"
              />
            </label>
            <UiFormActions
              class="compact-actions"
              :editing="editingRequirementId !== null"
              :saving="savingRequirement"
              :submit-label="editingRequirementId === null && !selectedFixtureAlreadyConfigured ? '加入治具' : '儲存變更'"
              saving-label="儲存中..."
              cancel-label="取消"
              :show-delete="false"
              :show-state="false"
              @cancel="onResetRequirementEditor"
            />
          </form>

          <p v-if="selectedFixtureAlreadyConfigured" class="existing-requirement-note">
            此站點已配置這支治具；儲存後會更新原本的每站需求量，不會建立重複資料。
          </p>

          <div v-if="projectedCapacity" class="capacity-preview" :class="previewTone()">
            <span>儲存後預估</span>
            <strong>{{ stationCapacityCount ?? 0 }} → {{ projectedCapacity.maxOpenStationCount }} 站</strong>
            <small>預估限制治具：{{ projectedCapacity.bottleneckFixtureCode || "-" }}</small>
          </div>
        </div>

        <div class="requirement-list-head">
          <div>
            <strong>正式需求清單</strong>
            <span>{{ selectedStationRequirementRows.length }} 筆治具</span>
          </div>
          <span class="context-chip">{{ selectedModelCode }} / {{ selectedStationCode }}</span>
        </div>

        <div class="table-scroll">
          <table class="mapping-table" data-tour="production-requirement-list">
            <thead>
              <tr>
                <th>治具</th>
                <th>治具名稱</th>
                <th>每站需求</th>
                <th>目前庫存</th>
                <th>可開站</th>
                <th>狀態</th>
                <th v-if="canEdit">動作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in selectedStationRequirementRows" :key="item.id">
                <td><strong>{{ item.fixture_code }}</strong></td>
                <td>{{ item.fixture_name || "-" }}</td>
                <td>{{ item.required_qty }}</td>
                <td>{{ item.stockQty }}</td>
                <td><strong>{{ item.maxOpenStationCount }}</strong></td>
                <td>
                  <UiStatusPill :label="capacityLabel(item)" :tone="capacityTone(item)" />
                </td>
                <td v-if="canEdit" class="table-actions">
                  <button class="ghost-btn small" type="button" @click="onStartEditRequirement(item)">編輯</button>
                  <button class="danger-btn small" type="button" @click="onRemoveRequirement(item.id)">刪除</button>
                </td>
              </tr>
              <tr v-if="!loading && selectedStationRequirementRows.length === 0">
                <td :colspan="canEdit ? 7 : 6" class="empty-cell">
                  此站點尚未設定治具需求。
                  <span v-if="canEdit">請從上方加入第一支治具。</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>

      <div v-else class="empty-state requirement-empty">
        <span class="step-number">②</span>
        <strong>請先選擇站點</strong>
        <span>從左側選擇一個站點後，這裡會顯示治具需求與產能預估。</span>
      </div>
    </article>
  </section>
</template>

<style scoped>
.workspace-layout {
  display: grid;
  grid-template-columns: minmax(280px, 0.78fr) minmax(520px, 1.62fr);
  gap: 10px;
  min-height: 0;
}

.panel {
  border: 1px solid var(--line);
  border-radius: 14px;
  background: #fff;
  padding: 12px;
  min-width: 0;
  min-height: 0;
  overflow: auto;
}

.station-workspace,
.requirement-workspace {
  display: grid;
  gap: 12px;
  align-content: start;
}

.section-head {
  margin-bottom: 0;
}

.count-pill,
.context-chip {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  border-radius: 999px;
  padding: 4px 10px;
  background: var(--tone-info-soft);
  color: var(--tone-info);
  font-size: 11px;
  font-weight: 800;
}

.station-create-card,
.requirement-editor {
  border: 1px solid #dbe5f4;
  border-radius: 12px;
  background: #f8fbff;
  padding: 10px;
  display: grid;
  gap: 10px;
}

.editor-title-row,
.requirement-list-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.editor-title-row > div,
.requirement-list-head > div {
  display: grid;
  gap: 2px;
}

.editor-title-row > .editor-buttons {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.editor-title-row strong,
.requirement-list-head strong {
  color: #22314a;
  font-size: 13px;
}

.editor-title-row span,
.requirement-list-head span,
.read-only-note {
  color: var(--muted);
  font-size: 11px;
  line-height: 1.4;
}

.context-form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
  align-items: end;
}

.requirement-form {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(110px, 0.32fr) auto;
  gap: 8px;
  align-items: end;
}

.context-field {
  display: grid;
  gap: 5px;
  min-width: 0;
}

.context-field > span {
  color: #53627b;
  font-size: 11px;
  font-weight: 700;
}

.quantity-field input {
  width: 100%;
  min-height: 36px;
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  padding: 8px 10px;
  background: #fff;
  font: inherit;
}

.compact-actions {
  align-self: end;
}

.station-list {
  display: grid;
  gap: 7px;
}

.station-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 6px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
  padding: 5px;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
}

.station-row:hover {
  border-color: #bfd0ef;
}

.station-row.selected {
  border-color: #8fb2f7;
  background: #f1f6ff;
  box-shadow: inset 4px 0 0 var(--blue);
}

.station-select {
  border: 0;
  background: transparent;
  padding: 7px 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  min-width: 0;
  text-align: left;
  cursor: pointer;
}

.station-identity,
.station-capacity {
  display: grid;
  gap: 2px;
}

.station-identity {
  min-width: 0;
}

.station-identity strong {
  color: #22314a;
  font-size: 13px;
}

.station-identity small,
.station-capacity small {
  color: var(--muted);
  font-size: 10px;
}

.station-capacity {
  text-align: right;
  flex: 0 0 auto;
}

.station-capacity strong {
  color: var(--blue);
  font-size: 16px;
}

.station-capacity em {
  color: var(--muted);
  font-size: 11px;
  font-style: normal;
  font-weight: 700;
}

.row-actions,
.table-actions {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.capacity-summary {
  display: grid;
  grid-template-columns: auto auto;
  align-items: baseline;
  gap: 2px 8px;
  min-width: 130px;
}

.capacity-summary span,
.capacity-summary small {
  color: var(--muted);
  font-size: 10px;
}

.capacity-summary strong {
  color: var(--blue);
  font-size: 22px;
}

.capacity-summary small {
  grid-column: 1 / -1;
}

.capacity-preview {
  display: grid;
  grid-template-columns: auto auto 1fr;
  gap: 8px;
  align-items: center;
  border-radius: 10px;
  padding: 8px 10px;
  background: var(--tone-info-soft);
  color: var(--tone-info);
}

.existing-requirement-note {
  margin: 0;
  border-radius: 9px;
  padding: 7px 9px;
  background: var(--tone-warn-soft);
  color: var(--tone-warn);
  font-size: 11px;
  line-height: 1.45;
}

.capacity-preview.decrease {
  background: var(--tone-danger-soft);
  color: var(--tone-danger);
}

.capacity-preview.increase {
  background: var(--tone-success-soft);
  color: var(--tone-success);
}

.capacity-preview span,
.capacity-preview small {
  font-size: 11px;
}

.capacity-preview strong {
  font-size: 14px;
}

.capacity-preview small {
  text-align: right;
}

.table-scroll {
  min-width: 0;
  overflow-x: auto;
}

.mapping-table {
  width: 100%;
  min-width: 720px;
  border-collapse: separate;
  border-spacing: 0;
  border: 1px solid var(--line);
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
}

.mapping-table th,
.mapping-table td {
  border-bottom: 1px solid var(--line);
  padding: 8px 10px;
  text-align: left;
  font-size: 12px;
  vertical-align: middle;
}

.mapping-table thead th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: #f7f9fd;
  color: #52607b;
  font-weight: 700;
}

.mapping-table tbody tr:last-child td {
  border-bottom: none;
}

.mapping-table tbody tr:hover {
  background: #f7faff;
}

.empty-state {
  min-height: 120px;
  border: 1px dashed #cbd7e8;
  border-radius: 12px;
  background: #fafcff;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 6px;
  padding: 20px;
  text-align: center;
}

.empty-state strong {
  color: #2b3a55;
}

.empty-state span {
  color: var(--muted);
  font-size: 12px;
}

.requirement-empty {
  min-height: 300px;
}

.step-number {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: 999px;
  background: var(--tone-info-soft);
  color: var(--tone-info) !important;
  font-size: 18px !important;
  font-weight: 800;
}

.read-only-note {
  margin: 0;
  border-radius: 10px;
  padding: 9px 10px;
  background: #f4f6f9;
}

.hidden-input {
  display: none;
}

.empty-cell {
  padding: 14px;
  color: var(--muted);
  background: #f8fbff;
  text-align: center;
}

.empty-cell span {
  display: block;
  margin-top: 3px;
}

@media (max-width: 1100px) {
  .workspace-layout {
    grid-template-columns: 1fr;
    overflow-y: auto;
  }

  .panel {
    overflow: visible;
  }
}

@media (max-width: 720px) {
  .context-form,
  .requirement-form {
    grid-template-columns: 1fr;
  }

  .compact-actions {
    width: 100%;
  }

  .editor-title-row,
  .requirement-list-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .station-row {
    grid-template-columns: 1fr;
  }

  .row-actions {
    padding: 0 8px 6px;
  }

  .capacity-preview {
    grid-template-columns: 1fr;
  }

  .capacity-preview small {
    text-align: left;
  }
}
</style>
