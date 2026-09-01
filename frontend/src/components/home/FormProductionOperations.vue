<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, reactive, ref, watch } from "vue";

import { api } from "@/api";
import { selectedCustomerId } from "@/appState";
import { requestConfirmation } from "@/confirmState";
import { pushToast } from "@/toastState";
import FormProductionPasteImport from "@/components/home/FormProductionPasteImport.vue";
import FormRemoteAutocomplete, {
  type FormAutocompleteOption,
} from "@/components/home/FormRemoteAutocomplete.vue";
import type {
  Fixture,
  FixtureRequirementListItem,
  MachineModel,
  ModelStation,
  ModelStationListItem,
  Station,
} from "@/types";
import { completeBlobExport } from "@/utils/exportFeedback";
import {
  formOperationError,
  productionMappingValidationMessage,
  productionRequirementValidationMessage,
} from "@/utils/formOperations";
import { scrollReportResultsIntoView } from "@/utils/scrollReportResults";
import { pageAfterItemRemoval } from "@/utils/pagination";
import type { FormProductionView } from "@/components/home/FormReportOperations.vue";
import { setUnsavedChangesGuard } from "@/unsavedChangesGuard";

type ProductionOptionField =
  | "filter-model"
  | "filter-station"
  | "draft-model"
  | "draft-station"
  | "draft-fixture";

const props = defineProps<{
  requestedView?: FormProductionView;
  workbenchLayout?: boolean;
}>();
const emit = defineEmits<{ viewChange: [view: FormProductionView] }>();

const loading = ref(false);
const saving = ref(false);
const exporting = ref(false);
const pasteOpen = ref(false);
const keyword = ref("");
const resultsSection = ref<HTMLElement | null>(null);
const requirements = ref<FixtureRequirementListItem[]>([]);
const mappings = ref<ModelStationListItem[]>([]);
const view = ref<FormProductionView>(props.requestedView ?? "requirements");
const modelId = ref<number | null>(null);
const stationId = ref<number | null>(null);
const modelQuery = ref("");
const stationQuery = ref("");
const draftModelQuery = ref("");
const draftStationQuery = ref("");
const fixtureQuery = ref("");
const filterModelOptions = ref<MachineModel[]>([]);
const filterStationOptions = ref<Station[]>([]);
const draftModelOptions = ref<MachineModel[]>([]);
const draftStationOptions = ref<Station[]>([]);
const draftFixtureOptions = ref<Fixture[]>([]);
const adding = ref(false);
const editingId = ref<number | null>(null);
const draft = reactive({
  model_id: null as number | null,
  station_id: null as number | null,
  fixture_id: null as number | null,
  required_qty: 1,
});
const pageNumber = ref(1);
const pageSize = ref<50 | 100>(50);
const total = ref(0);
const optionSearchTimers: Partial<Record<ProductionOptionField, number>> = {};
const optionRequestIds: Record<ProductionOptionField, number> = {
  "filter-model": 0,
  "filter-station": 0,
  "draft-model": 0,
  "draft-station": 0,
  "draft-fixture": 0,
};
const optionLoading = reactive<Record<ProductionOptionField, boolean>>({
  "filter-model": false,
  "filter-station": false,
  "draft-model": false,
  "draft-station": false,
  "draft-fixture": false,
});

const hasUnsavedRow = computed(() => adding.value || editingId.value !== null);
const totalPages = computed(() =>
  Math.max(1, Math.ceil(total.value / pageSize.value)),
);

async function load(): Promise<void> {
  const customerId = selectedCustomerId.value;
  if (!customerId) {
    requirements.value = [];
    mappings.value = [];
    total.value = 0;
    return;
  }
  loading.value = true;
  try {
    const result =
      view.value === "requirements"
        ? await api.listFixtureRequirementsPage(
            customerId,
            pageNumber.value,
            pageSize.value,
            modelId.value,
            stationId.value,
            keyword.value.trim(),
          )
        : await api.listModelStationsPage(
            customerId,
            pageNumber.value,
            pageSize.value,
            modelId.value,
            stationId.value,
            keyword.value.trim(),
          );
    if (view.value === "requirements") {
      requirements.value = result.items as FixtureRequirementListItem[];
      mappings.value = [];
    } else {
      mappings.value = result.items as ModelStationListItem[];
      requirements.value = [];
    }
    total.value = result.total;
  } catch (error) {
    pushToast(formOperationError(error, "載入產能資料失敗"), "error");
  } finally {
    loading.value = false;
  }
}

function clearOptions(): void {
  filterModelOptions.value = [];
  filterStationOptions.value = [];
  draftModelOptions.value = [];
  draftStationOptions.value = [];
  draftFixtureOptions.value = [];
  (Object.keys(optionRequestIds) as ProductionOptionField[]).forEach(
    (field) => {
      optionRequestIds[field] += 1;
      optionLoading[field] = false;
      const timer = optionSearchTimers[field];
      if (timer !== undefined) window.clearTimeout(timer);
      delete optionSearchTimers[field];
    },
  );
}

function resetDraft(): void {
  adding.value = false;
  editingId.value = null;
  draft.model_id = modelId.value;
  draft.station_id = stationId.value;
  draft.fixture_id = null;
  draft.required_qty = 1;
  draftModelQuery.value = modelId.value ? modelQuery.value : "";
  draftStationQuery.value = stationId.value ? stationQuery.value : "";
  fixtureQuery.value = "";
  draftModelOptions.value = [];
  draftStationOptions.value = [];
  draftFixtureOptions.value = [];
}

function startAdd(): void {
  resetDraft();
  adding.value = true;
}

function editRequirement(row: FixtureRequirementListItem): void {
  adding.value = false;
  editingId.value = row.id;
  Object.assign(draft, {
    model_id: row.model_id,
    station_id: row.station_id,
    fixture_id: row.fixture_id,
    required_qty: row.required_qty,
  });
  draftModelQuery.value = row.model_code;
  draftStationQuery.value = row.station_code;
  fixtureQuery.value = `${row.fixture_code}－${row.fixture_name}`;
}

function editMapping(row: ModelStationListItem): void {
  adding.value = false;
  editingId.value = row.id;
  Object.assign(draft, {
    model_id: row.model_id,
    station_id: row.station_id,
    fixture_id: null,
    required_qty: 1,
  });
  draftModelQuery.value = row.model_code;
  draftStationQuery.value = row.station_code;
}

async function loadOptions(
  field: ProductionOptionField,
  value: string,
): Promise<void> {
  const customerId = selectedCustomerId.value;
  if (!customerId) return;
  const requestId = ++optionRequestIds[field];
  optionLoading[field] = true;
  try {
    if (field === "draft-fixture") {
      const result = await api.listFixturesPage(
        customerId,
        1,
        20,
        value.trim(),
        "active",
      );
      if (requestId === optionRequestIds[field])
        draftFixtureOptions.value = result.items;
    } else if (field === "filter-model" || field === "draft-model") {
      const result = await api.listModelsPage(
        customerId,
        1,
        20,
        value.trim(),
        "active",
      );
      if (requestId === optionRequestIds[field]) {
        if (field === "filter-model") filterModelOptions.value = result.items;
        else draftModelOptions.value = result.items;
      }
    } else {
      const result = await api.listStationsPage(
        customerId,
        1,
        20,
        value.trim(),
        "active",
      );
      if (requestId === optionRequestIds[field]) {
        if (field === "filter-station")
          filterStationOptions.value = result.items;
        else draftStationOptions.value = result.items;
      }
    }
  } catch (error) {
    if (requestId === optionRequestIds[field])
      pushToast(formOperationError(error, "搜尋選項失敗"), "error");
  } finally {
    if (requestId === optionRequestIds[field]) optionLoading[field] = false;
  }
}

function searchOptions(field: ProductionOptionField, value: string): void {
  const existing = optionSearchTimers[field];
  if (existing !== undefined) window.clearTimeout(existing);
  optionSearchTimers[field] = window.setTimeout(
    () => void loadOptions(field, value),
    250,
  );
}

function updateOptionQuery(field: ProductionOptionField, value: string): void {
  if (field === "filter-model") {
    modelQuery.value = value;
    modelId.value = null;
  } else if (field === "filter-station") {
    stationQuery.value = value;
    stationId.value = null;
  } else if (field === "draft-model") {
    draftModelQuery.value = value;
    draft.model_id = null;
  } else if (field === "draft-station") {
    draftStationQuery.value = value;
    draft.station_id = null;
  } else {
    fixtureQuery.value = value;
    draft.fixture_id = null;
  }
}

function selectOption(
  field: ProductionOptionField,
  option: FormAutocompleteOption,
): void {
  const label = `${option.code}－${option.name}`;
  if (field === "filter-model") {
    modelQuery.value = label;
    modelId.value = option.id;
  } else if (field === "filter-station") {
    stationQuery.value = label;
    stationId.value = option.id;
  } else if (field === "draft-model") {
    draftModelQuery.value = label;
    draft.model_id = option.id;
  } else if (field === "draft-station") {
    draftStationQuery.value = label;
    draft.station_id = option.id;
  } else {
    fixtureQuery.value = label;
    draft.fixture_id = option.id;
  }
}

async function saveRow(): Promise<void> {
  const customerId = selectedCustomerId.value;
  const mappingMessage = productionMappingValidationMessage(
    draft.model_id,
    draft.station_id,
  );
  if (!customerId) {
    pushToast("請先選擇客戶。", "warning");
    return;
  }
  if (mappingMessage) {
    pushToast(mappingMessage, "warning");
    return;
  }
  if (view.value === "requirements") {
    const requirementMessage = productionRequirementValidationMessage(
      draft.station_id,
      draft.fixture_id,
      draft.required_qty,
    );
    if (requirementMessage) {
      pushToast(requirementMessage, "warning");
      return;
    }
  }
  saving.value = true;
  try {
    if (view.value === "requirements") {
      const payload = {
        customer_id: customerId,
        model_id: draft.model_id as number,
        station_id: draft.station_id as number,
        fixture_id: draft.fixture_id as number,
        required_qty: draft.required_qty,
      };
      if (editingId.value)
        await api.updateFixtureRequirement(editingId.value, payload);
      else await api.createFixtureRequirement(payload);
    } else {
      const payload = {
        customer_id: customerId,
        model_id: draft.model_id as number,
        station_id: draft.station_id as number,
      };
      if (editingId.value)
        await api.updateModelStation(editingId.value, payload);
      else await api.createModelStation(payload);
    }
    pushToast(
      editingId.value ? "產能資料已更新。" : "產能資料已新增。",
      "success",
    );
    resetDraft();
    await load();
  } catch (error) {
    pushToast(formOperationError(error, "儲存產能資料失敗"), "error");
  } finally {
    saving.value = false;
  }
}

async function deleteRow(
  row: FixtureRequirementListItem | ModelStation,
): Promise<void> {
  const label = view.value === "requirements" ? "治具需求" : "機種站點對應";
  if (
    !(await requestConfirmation(`確定刪除這筆${label}？`, {
      title: `刪除${label}？`,
      confirmLabel: "刪除",
      tone: "danger",
    }))
  )
    return;
  try {
    if (view.value === "requirements")
      await api.deleteFixtureRequirement(
        row.id,
        selectedCustomerId.value ?? undefined,
      );
    else
      await api.deleteModelStation(
        row.id,
        selectedCustomerId.value ?? undefined,
      );
    const currentPageItemCount =
      view.value === "requirements"
        ? requirements.value.length
        : mappings.value.length;
    pageNumber.value = pageAfterItemRemoval(
      pageNumber.value,
      currentPageItemCount,
    );
    await load();
    pushToast(`${label}已刪除。`, "success");
  } catch (error) {
    pushToast(formOperationError(error, `刪除${label}失敗`), "error");
  }
}

async function exportResults(): Promise<void> {
  const customerId = selectedCustomerId.value;
  if (!customerId) return;
  if (exporting.value) return;
  if (total.value === 0) {
    pushToast("目前沒有可匯出的資料。", "warning");
    return;
  }
  exporting.value = true;
  try {
    const response = await api.exportFormProductionCsv({
      entity: view.value,
      customerId,
      modelId: modelId.value,
      stationId: stationId.value,
      keyword: keyword.value.trim(),
    });
    completeBlobExport(
      response,
      view.value === "requirements"
        ? "form-requirements-filtered.csv"
        : "form-model-stations-filtered.csv",
      total.value,
    );
  } catch (error) {
    pushToast(formOperationError(error, "匯出篩選結果失敗"), "error");
  } finally {
    exporting.value = false;
  }
}

async function applyFilters(): Promise<void> {
  pageNumber.value = 1;
  await load();
  await nextTick();
  scrollReportResultsIntoView(resultsSection.value);
}

function changeView(): void {
  emit("viewChange", view.value);
}

watch(
  selectedCustomerId,
  () => {
    pageNumber.value = 1;
    clearOptions();
    resetDraft();
    void load();
  },
  { immediate: true },
);
watch(
  () => props.requestedView,
  (requestedView) => {
    if (requestedView) view.value = requestedView;
  },
);
watch(view, () => {
  pageNumber.value = 1;
  resetDraft();
  void load();
});
watch(
  hasUnsavedRow,
  (value) => {
    setUnsavedChangesGuard(
      "form-production-grid",
      value,
      "產能表格內有尚未儲存的輸入列",
    );
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  clearOptions();
  setUnsavedChangesGuard(
    "form-production-grid",
    false,
    "產能表格內有尚未儲存的輸入列",
  );
});
</script>

<template>
  <div
    class="report-workspace form-operation-workspace"
    data-form-operation-domain="production"
  >
    <div class="report-main-column">
      <Teleport
        defer
        to="#workbench-management-tools"
        :disabled="!workbenchLayout"
      >
        <section
          class="filter-panel workbench-side-section"
          data-tour="form-operation-filters"
          aria-label="產能與配置條件"
        >
          <div class="filter-panel-title">
            <div>
              <strong>篩選條件</strong
              ><span>產能與配置｜依目前功能顯示適用欄位</span>
            </div>
            <div class="filter-panel-title-actions">
              <button
                class="text-button"
                type="button"
                :disabled="loading"
                @click="load"
              >
                重新整理</button
              ><button
                class="primary-btn btn-sm"
                type="button"
                :disabled="loading"
                @click="applyFilters"
              >
                套用條件
              </button>
            </div>
          </div>
          <div class="filter-grid form-operation-filters compact">
            <label data-tour="form-production-view-selector"
              ><span>資料表</span
              ><select v-model="view" @change="changeView">
                <option value="requirements">治具需求</option>
                <option value="mappings">機種站點</option>
              </select></label
            >
            <label
              ><span>機種</span
              ><FormRemoteAutocomplete
                :model-value="modelQuery"
                :options="filterModelOptions"
                :loading="optionLoading['filter-model']"
                input-label="篩選機種"
                placeholder="全部／輸入編號或名稱"
                @update:model-value="updateOptionQuery('filter-model', $event)"
                @search="searchOptions('filter-model', $event)"
                @select="selectOption('filter-model', $event)"
            /></label>
            <label
              ><span>站點</span
              ><FormRemoteAutocomplete
                :model-value="stationQuery"
                :options="filterStationOptions"
                :loading="optionLoading['filter-station']"
                input-label="篩選站點"
                placeholder="全部／輸入編號或名稱"
                @update:model-value="
                  updateOptionQuery('filter-station', $event)
                "
                @search="searchOptions('filter-station', $event)"
                @select="selectOption('filter-station', $event)"
            /></label>
            <label
              ><span>關鍵字</span
              ><input v-model="keyword" placeholder="機種、站點或治具"
            /></label>
          </div>
        </section>
      </Teleport>

      <Teleport
        v-if="workbenchLayout && hasUnsavedRow"
        defer
        to="#workbench-management-tools"
      >
        <section
          class="workbench-side-section workbench-side-editor"
          aria-label="產能設定編輯欄位"
        >
          <header class="workbench-side-section-heading">
            <div>
              <span>EDIT</span
              ><strong
                >{{ editingId ? "編輯" : "新增"
                }}{{
                  view === "requirements" ? "治具需求" : "機種站點"
                }}</strong
              >
            </div>
            <button class="text-button" type="button" @click="resetDraft">
              取消
            </button>
          </header>
          <div class="workbench-side-form">
            <label
              ><span>機種</span
              ><FormRemoteAutocomplete
                :model-value="draftModelQuery"
                :options="draftModelOptions"
                :loading="optionLoading['draft-model']"
                input-label="選擇機種"
                placeholder="輸入機種編號或名稱"
                @update:model-value="updateOptionQuery('draft-model', $event)"
                @search="searchOptions('draft-model', $event)"
                @select="selectOption('draft-model', $event)"
            /></label>
            <label
              ><span>站點</span
              ><FormRemoteAutocomplete
                :model-value="draftStationQuery"
                :options="draftStationOptions"
                :loading="optionLoading['draft-station']"
                input-label="選擇站點"
                placeholder="輸入站點編號或名稱"
                @update:model-value="updateOptionQuery('draft-station', $event)"
                @search="searchOptions('draft-station', $event)"
                @select="selectOption('draft-station', $event)"
            /></label>
            <label v-if="view === 'requirements'"
              ><span>治具</span
              ><FormRemoteAutocomplete
                :model-value="fixtureQuery"
                :options="draftFixtureOptions"
                :loading="optionLoading['draft-fixture']"
                input-label="選擇治具"
                placeholder="輸入治具編號或名稱"
                @update:model-value="updateOptionQuery('draft-fixture', $event)"
                @search="searchOptions('draft-fixture', $event)"
                @select="selectOption('draft-fixture', $event)"
            /></label>
            <label v-if="view === 'requirements'"
              ><span>每站需求量</span
              ><input v-model.number="draft.required_qty" type="number" min="1"
            /></label>
          </div>
          <div class="workbench-side-actions">
            <button
              class="primary-btn"
              type="button"
              :disabled="saving"
              @click="saveRow"
            >
              {{ saving ? "儲存中…" : "儲存變更" }}
            </button>
          </div>
        </section>
      </Teleport>

      <slot name="between-filter-and-results" />

      <section
        ref="resultsSection"
        class="report-section"
        data-tour="form-operation-results"
        aria-label="產能與配置結果表格"
      >
        <div class="report-toolbar">
          <div class="report-summary">
            <strong>{{ total }}</strong
            ><span>筆資料</span
            ><span v-if="hasUnsavedRow" class="form-draft-note"
              >表格內有未儲存列</span
            >
          </div>
          <div class="form-operation-toolbar-actions">
            <button
              class="outline-btn"
              type="button"
              :disabled="exporting"
              @click="exportResults"
            >
              {{ exporting ? "匯出中..." : "匯出篩選結果" }}
            </button>
            <button
              class="outline-btn"
              data-tour="form-production-paste-import"
              type="button"
              @click="pasteOpen = true"
            >
              貼上匯入
            </button>
            <button
              class="primary-btn"
              data-tour="form-production-add-row"
              type="button"
              :disabled="saving || adding"
              @click="startAdd"
            >
              ＋ 新增一列
            </button>
            <label class="page-size-inline"
              >每頁<select
                v-model="pageSize"
                @change="
                  pageNumber = 1;
                  load();
                "
              >
                <option :value="50">50</option>
                <option :value="100">100</option>
              </select></label
            >
          </div>
        </div>

        <div class="form-report-grid-wrap">
          <table
            v-if="view === 'requirements'"
            class="form-report-grid editable-grid"
            data-tour="form-production-requirements-table"
          >
            <thead>
              <tr>
                <th>機種</th>
                <th>站點</th>
                <th>治具</th>
                <th>治具名稱</th>
                <th>每站需求</th>
                <th>目前庫存</th>
                <th>此治具可支援站數</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="adding && !workbenchLayout" class="editing-row">
                <td>
                  <FormRemoteAutocomplete
                    :model-value="draftModelQuery"
                    :options="draftModelOptions"
                    :loading="optionLoading['draft-model']"
                    aria-label="選擇機種"
                    placeholder="輸入機種"
                    @update:model-value="
                      updateOptionQuery('draft-model', $event)
                    "
                    @search="searchOptions('draft-model', $event)"
                    @select="selectOption('draft-model', $event)"
                  />
                </td>
                <td>
                  <FormRemoteAutocomplete
                    :model-value="draftStationQuery"
                    :options="draftStationOptions"
                    :loading="optionLoading['draft-station']"
                    aria-label="選擇站點"
                    placeholder="輸入站點"
                    @update:model-value="
                      updateOptionQuery('draft-station', $event)
                    "
                    @search="searchOptions('draft-station', $event)"
                    @select="selectOption('draft-station', $event)"
                  />
                </td>
                <td colspan="2">
                  <FormRemoteAutocomplete
                    :model-value="fixtureQuery"
                    :options="draftFixtureOptions"
                    :loading="optionLoading['draft-fixture']"
                    aria-label="選擇治具"
                    placeholder="輸入治具編號或名稱"
                    @update:model-value="
                      updateOptionQuery('draft-fixture', $event)
                    "
                    @search="searchOptions('draft-fixture', $event)"
                    @select="selectOption('draft-fixture', $event)"
                  />
                </td>
                <td>
                  <input
                    v-model.number="draft.required_qty"
                    type="number"
                    min="1"
                  />
                </td>
                <td>—</td>
                <td>—</td>
                <td>
                  <button
                    class="primary-btn btn-sm"
                    type="button"
                    :disabled="saving"
                    @click="saveRow"
                  >
                    儲存</button
                  ><button
                    class="outline-btn btn-sm"
                    type="button"
                    @click="resetDraft"
                  >
                    取消
                  </button>
                </td>
              </tr>
              <tr
                v-for="row in requirements"
                :key="row.id"
                :class="{ 'editing-row': editingId === row.id }"
              >
                <template v-if="editingId === row.id && !workbenchLayout"
                  ><td>
                    <FormRemoteAutocomplete
                      :model-value="draftModelQuery"
                      :options="draftModelOptions"
                      :loading="optionLoading['draft-model']"
                      aria-label="選擇機種"
                      @update:model-value="
                        updateOptionQuery('draft-model', $event)
                      "
                      @search="searchOptions('draft-model', $event)"
                      @select="selectOption('draft-model', $event)"
                    />
                  </td>
                  <td>
                    <FormRemoteAutocomplete
                      :model-value="draftStationQuery"
                      :options="draftStationOptions"
                      :loading="optionLoading['draft-station']"
                      aria-label="選擇站點"
                      @update:model-value="
                        updateOptionQuery('draft-station', $event)
                      "
                      @search="searchOptions('draft-station', $event)"
                      @select="selectOption('draft-station', $event)"
                    />
                  </td>
                  <td colspan="2">
                    <FormRemoteAutocomplete
                      :model-value="fixtureQuery"
                      :options="draftFixtureOptions"
                      :loading="optionLoading['draft-fixture']"
                      aria-label="選擇治具"
                      @update:model-value="
                        updateOptionQuery('draft-fixture', $event)
                      "
                      @search="searchOptions('draft-fixture', $event)"
                      @select="selectOption('draft-fixture', $event)"
                    />
                  </td>
                  <td>
                    <input
                      v-model.number="draft.required_qty"
                      type="number"
                      min="1"
                    />
                  </td>
                  <td>{{ row.stock_qty ?? 0 }}</td>
                  <td>
                    {{
                      Math.floor(
                        (row.stock_qty ?? 0) / Math.max(1, draft.required_qty),
                      )
                    }}
                  </td>
                  <td>
                    <button
                      class="primary-btn btn-sm"
                      type="button"
                      @click="saveRow"
                    >
                      儲存</button
                    ><button
                      class="outline-btn btn-sm"
                      type="button"
                      @click="resetDraft"
                    >
                      取消
                    </button>
                  </td></template
                >
                <template v-else
                  ><td>{{ row.model_code }}</td>
                  <td>{{ row.station_code }}</td>
                  <td>{{ row.fixture_code }}</td>
                  <td>{{ row.fixture_name }}</td>
                  <td>{{ row.required_qty }}</td>
                  <td>{{ row.stock_qty ?? 0 }}</td>
                  <td>
                    {{ Math.floor((row.stock_qty ?? 0) / row.required_qty) }}
                  </td>
                  <td>
                    <button
                      class="text-button"
                      type="button"
                      @click="editRequirement(row)"
                    >
                      編輯</button
                    ><button
                      class="danger-text-button"
                      type="button"
                      @click="deleteRow(row)"
                    >
                      刪除
                    </button>
                  </td></template
                >
              </tr>
            </tbody>
          </table>

          <table
            v-else
            class="form-report-grid editable-grid"
            data-tour="form-production-mappings-table"
          >
            <thead>
              <tr>
                <th>機種編號</th>
                <th>機種名稱</th>
                <th>站點編號</th>
                <th>站點名稱</th>
                <th>狀態</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="adding && !workbenchLayout" class="editing-row">
                <td colspan="2">
                  <FormRemoteAutocomplete
                    :model-value="draftModelQuery"
                    :options="draftModelOptions"
                    :loading="optionLoading['draft-model']"
                    aria-label="選擇機種"
                    placeholder="輸入機種"
                    @update:model-value="
                      updateOptionQuery('draft-model', $event)
                    "
                    @search="searchOptions('draft-model', $event)"
                    @select="selectOption('draft-model', $event)"
                  />
                </td>
                <td colspan="2">
                  <FormRemoteAutocomplete
                    :model-value="draftStationQuery"
                    :options="draftStationOptions"
                    :loading="optionLoading['draft-station']"
                    aria-label="選擇站點"
                    placeholder="輸入站點"
                    @update:model-value="
                      updateOptionQuery('draft-station', $event)
                    "
                    @search="searchOptions('draft-station', $event)"
                    @select="selectOption('draft-station', $event)"
                  />
                </td>
                <td>新增</td>
                <td>
                  <button
                    class="primary-btn btn-sm"
                    type="button"
                    @click="saveRow"
                  >
                    儲存</button
                  ><button
                    class="outline-btn btn-sm"
                    type="button"
                    @click="resetDraft"
                  >
                    取消
                  </button>
                </td>
              </tr>
              <tr
                v-for="row in mappings"
                :key="row.id"
                :class="{ 'editing-row': editingId === row.id }"
              >
                <template v-if="editingId === row.id && !workbenchLayout"
                  ><td colspan="2">
                    <FormRemoteAutocomplete
                      :model-value="draftModelQuery"
                      :options="draftModelOptions"
                      :loading="optionLoading['draft-model']"
                      aria-label="選擇機種"
                      @update:model-value="
                        updateOptionQuery('draft-model', $event)
                      "
                      @search="searchOptions('draft-model', $event)"
                      @select="selectOption('draft-model', $event)"
                    />
                  </td>
                  <td colspan="2">
                    <FormRemoteAutocomplete
                      :model-value="draftStationQuery"
                      :options="draftStationOptions"
                      :loading="optionLoading['draft-station']"
                      aria-label="選擇站點"
                      @update:model-value="
                        updateOptionQuery('draft-station', $event)
                      "
                      @search="searchOptions('draft-station', $event)"
                      @select="selectOption('draft-station', $event)"
                    />
                  </td>
                  <td>修改中</td>
                  <td>
                    <button
                      class="primary-btn btn-sm"
                      type="button"
                      @click="saveRow"
                    >
                      儲存</button
                    ><button
                      class="outline-btn btn-sm"
                      type="button"
                      @click="resetDraft"
                    >
                      取消
                    </button>
                  </td></template
                ><template v-else
                  ><td>{{ row.model_code }}</td>
                  <td>{{ row.model_name }}</td>
                  <td>{{ row.station_code }}</td>
                  <td>{{ row.station_name }}</td>
                  <td><span class="status-pill normal">已配置</span></td>
                  <td>
                    <button
                      class="text-button"
                      type="button"
                      @click="editMapping(row)"
                    >
                      編輯</button
                    ><button
                      class="danger-text-button"
                      type="button"
                      @click="deleteRow(row)"
                    >
                      刪除
                    </button>
                  </td></template
                >
              </tr>
            </tbody>
          </table>
        </div>
        <div class="form-grid-pager">
          <button
            class="outline-btn btn-sm"
            type="button"
            :disabled="pageNumber <= 1 || loading"
            @click="
              pageNumber -= 1;
              load();
            "
          >
            上一頁</button
          ><span>第 {{ pageNumber }} / {{ totalPages }} 頁</span
          ><button
            class="outline-btn btn-sm"
            type="button"
            :disabled="pageNumber >= totalPages || loading"
            @click="
              pageNumber += 1;
              load();
            "
          >
            下一頁
          </button>
        </div>
      </section>
    </div>
    <FormProductionPasteImport
      :open="pasteOpen"
      :view="view"
      :customer-id="selectedCustomerId ?? undefined"
      @close="pasteOpen = false"
      @imported="load"
    />
  </div>
</template>
