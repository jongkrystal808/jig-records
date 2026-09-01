<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";

import { api, fetchFixtureImageObjectUrl } from "@/api";
import { selectedCustomerId } from "@/appState";
import UiMultiSelect from "@/components/common/UiMultiSelect.vue";
import FixtureImageDialog from "@/components/inventory/FixtureImageDialog.vue";
import { pushToast } from "@/toastState";
import type { Fixture, FixtureImageBatchUploadItem } from "@/types";
import { completeBlobExport } from "@/utils/exportFeedback";
import { scrollReportResultsIntoView } from "@/utils/scrollReportResults";

const props = defineProps<{ workbenchLayout?: boolean }>();

const fixtures = ref<Fixture[]>([]);
const loading = ref(false);
const exporting = ref(false);
const keyword = ref("");
const imageStatus = ref<Array<"with-image" | "missing-image">>([]);
const imageStatusApiValue = computed<"all" | "with-image" | "missing-image">(
  () => (imageStatus.value.length === 1 ? imageStatus.value[0] : "all"),
);
const batchFiles = ref<File[]>([]);
const batchUploading = ref(false);
const singleUploadingId = ref<number | null>(null);
const batchResults = ref<FixtureImageBatchUploadItem[]>([]);
const batchInput = ref<HTMLInputElement | null>(null);
const previewFixture = ref<Fixture | null>(null);
const selectedFixtureId = ref<number | null>(null);
const selectedFixture = computed(
  () => fixtures.value.find((fixture) => fixture.id === selectedFixtureId.value) ?? null,
);
const selectedImageUrl = ref("");
const selectedImageLoading = ref(false);
const selectedImageFailed = ref(false);
let selectedImageRequestId = 0;
const resultsSection = ref<HTMLElement | null>(null);
const pageNumber = ref(1);
const pageSize = ref<50 | 100>(50);
const total = ref(0);
const totalPages = computed(() =>
  Math.max(1, Math.ceil(total.value / pageSize.value)),
);
let fixtureRequestId = 0;

async function loadFixtures(): Promise<void> {
  const requestId = ++fixtureRequestId;
  const customerId = selectedCustomerId.value;
  if (!customerId) {
    fixtures.value = [];
    total.value = 0;
    pageNumber.value = 1;
    loading.value = false;
    return;
  }
  loading.value = true;
  try {
    const result = await api.listFixturesPage(
      customerId,
      pageNumber.value,
      pageSize.value,
      keyword.value.trim(),
      "all",
      imageStatusApiValue.value,
    );
    if (requestId !== fixtureRequestId) return;
    fixtures.value = result.items;
    total.value = result.total;
    if (props.workbenchLayout) {
      const selectionStillVisible = result.items.some((fixture) => fixture.id === selectedFixtureId.value);
      if (!selectionStillVisible) selectedFixtureId.value = result.items[0]?.id ?? null;
    }
  } catch (error) {
    if (requestId !== fixtureRequestId) return;
    pushToast(
      error instanceof Error ? error.message : "載入圖片維護資料失敗",
      "error",
    );
  } finally {
    if (requestId === fixtureRequestId) loading.value = false;
  }
}

function releaseSelectedImage(): void {
  if (!selectedImageUrl.value) return;
  URL.revokeObjectURL(selectedImageUrl.value);
  selectedImageUrl.value = "";
}

async function loadSelectedImage(): Promise<void> {
  const requestId = ++selectedImageRequestId;
  releaseSelectedImage();
  selectedImageFailed.value = false;
  const fixture = selectedFixture.value;
  const customerId = selectedCustomerId.value;
  if (!props.workbenchLayout || !fixture?.has_image || !customerId) {
    selectedImageLoading.value = false;
    return;
  }
  selectedImageLoading.value = true;
  try {
    const objectUrl = await fetchFixtureImageObjectUrl(fixture.code, customerId);
    if (requestId !== selectedImageRequestId) {
      URL.revokeObjectURL(objectUrl);
      return;
    }
    selectedImageUrl.value = objectUrl;
  } catch {
    if (requestId === selectedImageRequestId) selectedImageFailed.value = true;
  } finally {
    if (requestId === selectedImageRequestId) selectedImageLoading.value = false;
  }
}

function validateImageFiles(files: File[]): boolean {
  if (files.length > 50) {
    pushToast("單次最多可選擇 50 張圖片。", "warning");
    return false;
  }
  const oversized = files.find((file) => file.size > 5 * 1024 * 1024);
  if (oversized) {
    pushToast(`圖片 ${oversized.name} 超過 5 MB。`, "warning");
    return false;
  }
  return true;
}

function updateBatchFiles(event: Event): void {
  const files = Array.from((event.target as HTMLInputElement).files ?? []);
  if (!validateImageFiles(files)) {
    batchFiles.value = [];
    if (batchInput.value) batchInput.value.value = "";
    return;
  }
  batchFiles.value = files;
  batchResults.value = [];
}

async function uploadBatch(): Promise<void> {
  const customerId = selectedCustomerId.value;
  if (!customerId || batchFiles.value.length === 0) {
    pushToast("請先選擇要上傳的圖片。", "warning");
    return;
  }
  batchUploading.value = true;
  try {
    const result = await api.uploadFixtureImagesBatch(
      customerId,
      batchFiles.value,
    );
    batchResults.value = result.results;
    batchFiles.value = [];
    if (batchInput.value) batchInput.value.value = "";
    await loadFixtures();
    pushToast(
      `圖片上傳完成：成功 ${result.uploaded_count} 張、失敗 ${result.failed_count} 張。`,
      result.failed_count ? "warning" : "success",
    );
  } catch (error) {
    pushToast(
      error instanceof Error ? error.message : "批次上傳治具圖片失敗",
      "error",
    );
  } finally {
    batchUploading.value = false;
  }
}

async function uploadSingle(fixture: Fixture, event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  const customerId = selectedCustomerId.value;
  if (!file || !customerId) return;
  if (!validateImageFiles([file])) {
    input.value = "";
    return;
  }
  singleUploadingId.value = fixture.id;
  try {
    await api.uploadFixtureImage(fixture.id, customerId, file);
    await loadFixtures();
    pushToast(`治具 ${fixture.code} 圖片已更新。`, "success");
  } catch (error) {
    pushToast(
      error instanceof Error ? error.message : "上傳治具圖片失敗",
      "error",
    );
  } finally {
    singleUploadingId.value = null;
    input.value = "";
  }
}

async function exportFilteredResults(): Promise<void> {
  const customerId = selectedCustomerId.value;
  if (!customerId) return;
  if (exporting.value) return;
  if (total.value === 0) {
    pushToast("目前沒有可匯出的資料。", "warning");
    return;
  }
  exporting.value = true;
  try {
    const response = await api.exportFormMasterCsv({
      entity: "fixture-images",
      customerId,
      keyword: keyword.value.trim(),
      imageStatus: imageStatusApiValue.value,
    });
    completeBlobExport(
      response,
      "form-fixture-images-filtered.csv",
      total.value,
    );
  } catch (error) {
    pushToast(
      error instanceof Error ? error.message : "匯出篩選結果失敗",
      "error",
    );
  } finally {
    exporting.value = false;
  }
}

async function applyImageFilters(): Promise<void> {
  pageNumber.value = 1;
  await loadFixtures();
  await nextTick();
  scrollReportResultsIntoView(resultsSection.value);
}

watch(
  selectedCustomerId,
  () => {
    batchFiles.value = [];
    batchResults.value = [];
    previewFixture.value = null;
    selectedFixtureId.value = null;
    pageNumber.value = 1;
    void loadFixtures();
  },
  { immediate: true },
);

watch(
  [selectedFixtureId, selectedCustomerId, () => selectedFixture.value?.has_image],
  () => void loadSelectedImage(),
  { immediate: true },
);

onBeforeUnmount(() => {
  selectedImageRequestId += 1;
  releaseSelectedImage();
});
</script>

<template>
  <div class="report-workspace form-image-workspace">
    <div class="report-main-column">
      <Teleport defer to="#workbench-management-tools" :disabled="!workbenchLayout">
      <section
        class="filter-panel workbench-side-section"
        data-tour="form-image-filters"
        aria-label="圖片維護條件"
      >
        <div class="filter-panel-title">
          <div><strong>篩選條件</strong><span>圖片維護</span></div>
          <div class="filter-panel-title-actions">
            <button
              class="text-button"
              type="button"
              :disabled="loading"
              @click="loadFixtures"
            >
              重新整理
            </button>
            <button
              class="primary-btn btn-sm"
              type="button"
              :disabled="loading"
              @click="applyImageFilters"
            >
              套用條件
            </button>
          </div>
        </div>
        <div class="form-image-filters">
          <label
            ><span>治具</span
            ><input v-model="keyword" placeholder="治具編號／名稱"
          /></label>
          <UiMultiSelect
            v-model="imageStatus"
            label="圖片狀態"
            placeholder="全部狀態"
            :options="[
              { value: 'with-image', label: '已有圖片' },
              { value: 'missing-image', label: '尚無圖片' },
            ]"
          />
        </div>
      </section>
      </Teleport>

      <Teleport v-if="workbenchLayout" defer to="#workbench-management-tools">
        <section v-if="selectedFixture" class="workbench-side-section workbench-image-inspector" aria-label="個別治具圖片維護">
          <header class="workbench-side-section-heading">
            <div><span>SELECTED FIXTURE</span><strong>{{ selectedFixture.code }}</strong><small>{{ selectedFixture.name || "未命名治具" }}</small></div>
          </header>
          <div class="workbench-image-preview" :class="{ empty: !selectedFixture.has_image || selectedImageFailed }">
            <span v-if="selectedImageLoading">圖片載入中…</span>
            <img v-else-if="selectedImageUrl" :src="selectedImageUrl" :alt="`${selectedFixture.code} ${selectedFixture.name} 治具圖片`" />
            <div v-else>
              <strong>{{ selectedImageFailed ? "圖片載入失敗" : "尚無圖片" }}</strong>
              <span>可直接在下方選擇檔案建立圖片。</span>
            </div>
          </div>
          <div class="workbench-side-actions">
            <button v-if="selectedFixture.has_image" class="outline-btn" type="button" @click="previewFixture = selectedFixture">放大查看</button>
            <label class="primary-btn image-file-picker" :class="{ disabled: singleUploadingId !== null }">
              {{ singleUploadingId === selectedFixture.id ? "上傳中..." : selectedFixture.has_image ? "替換圖片" : "上傳圖片" }}
              <input type="file" accept="image/png,image/jpeg,image/webp,image/gif" :disabled="singleUploadingId !== null" @change="uploadSingle(selectedFixture, $event)" />
            </label>
          </div>
        </section>
        <section class="workbench-side-section workbench-side-editor" aria-label="圖片上傳工具">
          <header class="workbench-side-section-heading"><div><span>UPLOAD</span><strong>批次上傳圖片</strong></div></header>
          <p class="workbench-side-help">以治具編號作為檔名；單次最多 50 張，每張小於 5 MB。</p>
          <div class="workbench-side-actions vertical">
            <label class="outline-btn image-file-picker" :class="{ disabled: loading || batchUploading }">
              {{ batchFiles.length ? `已選 ${batchFiles.length} 張圖片` : "選擇批次圖片" }}
              <input ref="batchInput" type="file" accept="image/png,image/jpeg,image/webp,image/gif" multiple :disabled="loading || batchUploading" @change="updateBatchFiles" />
            </label>
            <button v-if="batchFiles.length" class="primary-btn" type="button" :disabled="batchUploading" @click="uploadBatch">{{ batchUploading ? "上傳中..." : `開始上傳 ${batchFiles.length} 張` }}</button>
          </div>
          <div v-if="batchResults.length" class="batch-result-summary" role="status">
            <span v-for="result in batchResults" :key="`${result.file_name}-${result.fixture_id}`" :class="result.success ? 'success' : 'failed'">{{ result.file_name }}：{{ result.message }}</span>
          </div>
        </section>
      </Teleport>

      <slot name="between-filter-and-results" />

      <section
        ref="resultsSection"
        class="report-section"
        data-tour="form-image-results"
        aria-label="圖片維護結果"
      >
        <div class="report-toolbar">
          <div class="report-summary">
            <strong>{{ total }}</strong
            ><span>筆治具</span>
          </div>
          <div class="form-image-actions">
            <button
              class="outline-btn"
              type="button"
              :disabled="exporting"
              @click="exportFilteredResults"
            >
              {{ exporting ? "匯出中..." : "匯出篩選結果" }}
            </button>
            <label
              v-if="!workbenchLayout"
              class="outline-btn image-file-picker"
              :class="{ disabled: loading || batchUploading }"
            >
              {{
                batchFiles.length
                  ? `已選 ${batchFiles.length} 張圖片`
                  : "選擇批次圖片"
              }}
              <input
                ref="batchInput"
                type="file"
                accept="image/png,image/jpeg,image/webp,image/gif"
                multiple
                :disabled="loading || batchUploading"
                @change="updateBatchFiles"
              />
            </label>
            <button
              v-if="!workbenchLayout && batchFiles.length"
              class="primary-btn"
              type="button"
              :disabled="batchUploading"
              @click="uploadBatch"
            >
              {{
                batchUploading
                  ? "上傳中..."
                  : `開始上傳 ${batchFiles.length} 張`
              }}
            </button>
            <label class="page-size-inline"
              >每頁<select
                v-model="pageSize"
                @change="
                  pageNumber = 1;
                  loadFixtures();
                "
              >
                <option :value="50">50</option>
                <option :value="100">100</option>
              </select></label
            >
          </div>
        </div>

        <p v-if="!workbenchLayout" class="image-upload-hint">
          批次上傳時請以治具編號作為檔名；單次最多 50 張，每張小於 5
          MB。個別治具也可直接選檔替換。
        </p>

        <div
          v-if="!workbenchLayout && batchResults.length"
          class="batch-result-summary"
          role="status"
        >
          <span
            v-for="result in batchResults"
            :key="`${result.file_name}-${result.fixture_id}`"
            :class="result.success ? 'success' : 'failed'"
            >{{ result.file_name }}：{{ result.message }}</span
          >
        </div>

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>治具編號</th>
                <th>治具名稱</th>
                <th>圖片狀態</th>
                <th v-if="!workbenchLayout">預覽</th>
                <th>圖片維護</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loading">
                <td :colspan="workbenchLayout ? 4 : 5">載入中...</td>
              </tr>
              <tr v-else-if="fixtures.length === 0">
                <td :colspan="workbenchLayout ? 4 : 5">目前沒有符合條件的治具。</td>
              </tr>
              <tr
                v-for="fixture in fixtures"
                v-else
                :key="fixture.id"
                :class="{ 'workbench-image-row': workbenchLayout, selected: workbenchLayout && selectedFixtureId === fixture.id }"
                :aria-selected="workbenchLayout ? selectedFixtureId === fixture.id : undefined"
                :tabindex="workbenchLayout ? 0 : undefined"
                @click="workbenchLayout && (selectedFixtureId = fixture.id)"
                @keydown.enter.prevent="workbenchLayout && (selectedFixtureId = fixture.id)"
                @keydown.space.prevent="workbenchLayout && (selectedFixtureId = fixture.id)"
              >
                <td>{{ fixture.code }}</td>
                <td>{{ fixture.name || "—" }}</td>
                <td v-if="!workbenchLayout">
                  <span
                    class="status-pill"
                    :class="fixture.has_image ? 'normal' : 'muted'"
                    >{{ fixture.has_image ? "已有圖片" : "尚無圖片" }}</span
                  >
                </td>
                <td>
                  <button
                    class="text-button"
                    type="button"
                    :disabled="!fixture.has_image"
                    @click="previewFixture = fixture"
                  >
                    {{ fixture.has_image ? "查看圖片" : "尚無圖片" }}
                  </button>
                </td>
                <td>
                  <button
                    v-if="workbenchLayout"
                    class="text-button"
                    type="button"
                    @click="selectedFixtureId = fixture.id"
                  >
                    {{ selectedFixtureId === fixture.id ? "已選取" : "選取維護" }}
                  </button>
                  <label
                    v-else
                    class="text-button row-image-picker"
                    :class="{ disabled: singleUploadingId === fixture.id }"
                  >
                    {{
                      singleUploadingId === fixture.id
                        ? "上傳中..."
                        : fixture.has_image
                          ? "替換圖片"
                          : "上傳圖片"
                    }}
                    <input
                      type="file"
                      accept="image/png,image/jpeg,image/webp,image/gif"
                      :disabled="singleUploadingId !== null"
                      @change="uploadSingle(fixture, $event)"
                    />
                  </label>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="form-image-pager">
          <button
            class="outline-btn btn-sm"
            type="button"
            :disabled="pageNumber <= 1 || loading"
            @click="
              pageNumber -= 1;
              loadFixtures();
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
              loadFixtures();
            "
          >
            下一頁
          </button>
        </div>
      </section>
    </div>

    <FixtureImageDialog
      :open="Boolean(previewFixture)"
      :fixture-code="previewFixture?.code ?? ''"
      :fixture-name="previewFixture?.name ?? ''"
      :customer-id="selectedCustomerId"
      @close="previewFixture = null"
    />
  </div>
</template>

<style scoped>
.form-image-workspace {
  width: 100%;
}
.filter-panel {
  max-width: 1800px;
  margin: 0 auto 12px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--panel);
  box-shadow: 0 8px 24px rgba(28, 47, 84, 0.06);
  overflow: hidden;
}
.filter-panel-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 38px;
  padding: 7px 12px;
  border-bottom: 1px solid var(--line);
  background: var(--surface-secondary);
}
.filter-panel-title > div {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.filter-panel-title strong {
  font-size: 0.9rem;
}
.filter-panel-title span,
.image-upload-hint {
  color: var(--muted);
  font-size: 0.72rem;
}
.filter-panel-title-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 6px;
}
.form-image-filters {
  display: grid;
  grid-template-columns: minmax(260px, 2fr) minmax(190px, 1fr);
  gap: 9px 10px;
  padding: 10px 12px 12px;
}
.form-image-filters label {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 7px;
}
.form-image-filters label > span {
  color: #4f5f79;
  font-size: 0.73rem;
  font-weight: 700;
  white-space: nowrap;
}
.form-image-filters input,
.form-image-filters select {
  width: 100%;
  min-width: 0;
  min-height: 34px;
  padding: 0 9px;
  border: 1px solid var(--line-strong);
  border-radius: 5px;
  background: #fff;
  font: inherit;
}
.form-image-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
}
.page-size-inline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--muted);
  font-size: 0.72rem;
}
.page-size-inline select {
  min-height: 30px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
}
.form-image-pager {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding: 9px 12px;
  color: var(--muted);
  font-size: 0.75rem;
}
.table-wrap {
  width: 100%;
  min-height: min(58vh, 620px);
  overflow-x: auto;
  overflow-y: visible;
}
.image-file-picker,
.row-image-picker {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.image-file-picker input,
.row-image-picker input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}
.disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.image-upload-hint {
  margin: 0;
  padding: 8px 12px;
  border-bottom: 1px solid var(--line);
  background: #fbfcfe;
}
.batch-result-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--line);
  font-size: 0.7rem;
}
.batch-result-summary span {
  padding: 3px 7px;
  border-radius: 999px;
  background: #eef3f9;
}
.batch-result-summary .success {
  color: #276749;
  background: #e8f7ef;
}
.batch-result-summary .failed {
  color: #9c3f32;
  background: #fff0ed;
}
.workbench-image-preview {
  display: grid;
  min-height: 176px;
  max-height: 250px;
  place-items: center;
  overflow: hidden;
  margin: 10px 11px;
  border: 1px solid #cad8ea;
  border-radius: 12px;
  background:
    linear-gradient(45deg, #edf2f8 25%, transparent 25%),
    linear-gradient(-45deg, #edf2f8 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #edf2f8 75%),
    linear-gradient(-45deg, transparent 75%, #edf2f8 75%);
  background-position: 0 0, 0 8px, 8px -8px, -8px 0;
  background-size: 16px 16px;
}
.workbench-image-preview img {
  display: block;
  width: 100%;
  height: 100%;
  max-height: 250px;
  object-fit: contain;
}
.workbench-image-preview > span,
.workbench-image-preview > div {
  color: #60708a;
  font-size: 0.72rem;
  text-align: center;
}
.workbench-image-preview > div {
  display: grid;
  gap: 4px;
  padding: 20px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.9);
}
.workbench-image-preview > div strong {
  color: #344b6b;
  font-size: 0.84rem;
}
.workbench-image-row {
  cursor: pointer;
}
.workbench-image-row.selected {
  background: #edf3ff;
  box-shadow: inset 4px 0 0 #2f6ee5;
}
.workbench-image-row:focus-visible {
  outline: 2px solid #2f6ee5;
  outline-offset: -2px;
}
@media (max-width: 700px) {
  .form-image-filters {
    grid-template-columns: 1fr;
  }
  .form-image-filters label {
    grid-template-columns: 1fr;
    gap: 5px;
  }
  .filter-panel-title {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
