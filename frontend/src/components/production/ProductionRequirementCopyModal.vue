<script setup lang="ts">
import { computed, ref, watch } from "vue";

import UiModalShell from "@/components/common/UiModalShell.vue";
import type { FixtureRequirementListItem, MachineModel, ModelStation, Station } from "@/types";
import { calculateRequirementCopyPreview } from "@/utils/productionCopy";

const props = defineProps<{
  open: boolean;
  saving: boolean;
  sourceModelId: number | null;
  sourceModelCode: string;
  sourceStationId: number | null;
  sourceStationCode: string;
  models: MachineModel[];
  stations: Station[];
  mappings: ModelStation[];
  requirements: FixtureRequirementListItem[];
}>();

const emit = defineEmits<{
  close: [];
  submit: [
    payload: {
      targetModelId: number;
      targetStationId: number;
      overwriteExisting: boolean;
    }
  ];
}>();

const targetModelId = ref<number | null>(null);
const targetStationId = ref<number | null>(null);
const overwriteExisting = ref(false);

const sourceRows = computed(() =>
  props.requirements.filter(
    (row) => row.model_id === props.sourceModelId && row.station_id === props.sourceStationId
  )
);
const targetRows = computed(() =>
  props.requirements.filter(
    (row) => row.model_id === targetModelId.value && row.station_id === targetStationId.value
  )
);
const targetIsMapped = computed(() =>
  props.mappings.some(
    (row) => row.model_id === targetModelId.value && row.station_id === targetStationId.value
  )
);
const sameSourceAndTarget = computed(
  () =>
    props.sourceModelId === targetModelId.value &&
    props.sourceStationId === targetStationId.value
);
const copyModeLabel = computed(() =>
  targetModelId.value !== null && targetModelId.value !== props.sourceModelId
    ? "跨機種複製"
    : "同機種站點複製"
);
const preview = computed(() =>
  calculateRequirementCopyPreview(sourceRows.value, targetRows.value, overwriteExisting.value)
);
const writeCount = computed(() => preview.value.createCount + preview.value.updateCount);
const canSubmit = computed(
  () =>
    !props.saving &&
    props.sourceModelId !== null &&
    props.sourceStationId !== null &&
    targetModelId.value !== null &&
    targetStationId.value !== null &&
    !sameSourceAndTarget.value &&
    sourceRows.value.length > 0 &&
    writeCount.value > 0
);

function pickDefaultStation(modelId: number | null): number | null {
  if (modelId === null) return null;
  const mappedStationIds = new Set(
    props.mappings.filter((row) => row.model_id === modelId).map((row) => row.station_id)
  );
  const mappedCandidate = props.stations.find(
    (station) =>
      mappedStationIds.has(station.id) &&
      !(modelId === props.sourceModelId && station.id === props.sourceStationId)
  );
  if (mappedCandidate) return mappedCandidate.id;
  return (
    props.stations.find(
      (station) => !(modelId === props.sourceModelId && station.id === props.sourceStationId)
    )?.id ?? null
  );
}

function resetForm(): void {
  targetModelId.value = props.sourceModelId;
  targetStationId.value = pickDefaultStation(targetModelId.value);
  overwriteExisting.value = false;
}

function handleTargetModelChange(event: Event): void {
  const value = Number.parseInt((event.target as HTMLSelectElement).value, 10);
  targetModelId.value = Number.isFinite(value) ? value : null;
  targetStationId.value = pickDefaultStation(targetModelId.value);
}

function handleTargetStationChange(event: Event): void {
  const value = Number.parseInt((event.target as HTMLSelectElement).value, 10);
  targetStationId.value = Number.isFinite(value) ? value : null;
}

function submitCopy(): void {
  if (!canSubmit.value || targetModelId.value === null || targetStationId.value === null) return;
  emit("submit", {
    targetModelId: targetModelId.value,
    targetStationId: targetStationId.value,
    overwriteExisting: overwriteExisting.value
  });
}

function closeModal(): void {
  if (!props.saving) emit("close");
}

watch(
  () => props.open,
  (open) => {
    if (open) resetForm();
  }
);
</script>

<template>
  <UiModalShell
    :open="open"
    labelled-by="production-copy-title"
    dialog-class="copy-modal"
    :close-on-backdrop="!saving"
    @close="closeModal"
  >
        <header class="copy-head">
          <div>
            <span class="mode-label">{{ copyModeLabel }}</span>
            <h2 id="production-copy-title">複製站點治具需求</h2>
            <p>從目前站點複製全部治具與每站需求量；預設不覆蓋目標既有資料。</p>
          </div>
          <button class="outline-btn" type="button" :disabled="saving" @click="closeModal">關閉</button>
        </header>

        <div class="copy-route">
          <div class="route-card source">
            <span>來源</span>
            <strong>{{ sourceModelCode || "-" }}</strong>
            <small>{{ sourceStationCode || "-" }} · {{ sourceRows.length }} 筆需求</small>
          </div>
          <span class="route-arrow" aria-hidden="true">→</span>
          <div class="route-card target">
            <span>目標</span>
            <strong>{{ models.find((row) => row.id === targetModelId)?.code || "請選機種" }}</strong>
            <small>{{ stations.find((row) => row.id === targetStationId)?.code || "請選站點" }}</small>
          </div>
        </div>

        <div class="copy-fields">
          <label>
            <span>目標機種</span>
            <select :value="targetModelId ?? ''" :disabled="saving" data-modal-initial-focus @change="handleTargetModelChange">
              <option value="" disabled>請選擇機種</option>
              <option v-for="model in models" :key="model.id" :value="model.id">
                {{ model.code }} - {{ model.name }}
              </option>
            </select>
          </label>
          <label>
            <span>目標站點</span>
            <select :value="targetStationId ?? ''" :disabled="saving" @change="handleTargetStationChange">
              <option value="" disabled>請選擇站點</option>
              <option v-for="station in stations" :key="station.id" :value="station.id">
                {{ station.code }} - {{ station.name }}
              </option>
            </select>
          </label>
        </div>

        <p v-if="sameSourceAndTarget" class="copy-message danger">來源與目標不能是同一個機種站點。</p>
        <p v-else-if="targetModelId !== null && targetStationId !== null" class="copy-message">
          {{
            targetIsMapped
              ? "目標站點已存在，將直接複製需求。"
              : "目標機種尚未加入此站點，複製時會自動建立站點設定。"
          }}
        </p>

        <div class="copy-preview" aria-label="複製預覽">
          <div>
            <span>來源需求</span>
            <strong>{{ preview.sourceCount }}</strong>
          </div>
          <div class="success">
            <span>新增</span>
            <strong>{{ preview.createCount }}</strong>
          </div>
          <div :class="{ warning: preview.conflictCount > 0 }">
            <span>既有衝突</span>
            <strong>{{ preview.conflictCount }}</strong>
          </div>
          <div v-if="overwriteExisting" class="warning">
            <span>更新</span>
            <strong>{{ preview.updateCount }}</strong>
          </div>
          <div>
            <span>跳過</span>
            <strong>{{ preview.skipCount }}</strong>
          </div>
        </div>

        <label class="overwrite-option">
          <input v-model="overwriteExisting" type="checkbox" :disabled="saving" />
          <span>
            <strong>覆蓋相同治具的需求量</strong>
            <small>只有數量不同的既有資料會被更新；完全相同的資料仍會跳過。</small>
          </span>
        </label>

        <p v-if="!sameSourceAndTarget && writeCount === 0" class="copy-message warning">
          目前沒有可新增的需求；如需同步不同數量，請勾選覆蓋選項。
        </p>

        <footer class="copy-actions">
          <button class="outline-btn" type="button" :disabled="saving" @click="closeModal">取消</button>
          <button class="primary-btn" type="button" :disabled="!canSubmit" @click="submitCopy">
            {{ saving ? "複製中..." : `複製 ${writeCount} 筆需求` }}
          </button>
        </footer>
  </UiModalShell>
</template>

<style scoped>
:global(.copy-modal) {
  width: min(720px, calc(100vw - 24px));
}

.copy-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.copy-head h2 {
  margin: 4px 0 0;
  color: #22314a;
  font-size: 20px;
}

.copy-head p {
  margin: 5px 0 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.55;
}

.mode-label {
  display: inline-flex;
  border-radius: 999px;
  padding: 3px 9px;
  background: var(--tone-info-soft);
  color: var(--tone-info);
  font-size: 11px;
  font-weight: 800;
}

.copy-route {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: center;
  gap: 10px;
  margin-top: 16px;
}

.route-card {
  display: grid;
  gap: 4px;
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 12px;
  background: #f8fbff;
}

.route-card span,
.route-card small {
  color: var(--muted);
  font-size: 11px;
}

.route-card strong {
  overflow: hidden;
  color: #273752;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.route-arrow {
  color: var(--tone-info);
  font-size: 24px;
  font-weight: 900;
}

.copy-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}

.copy-fields label {
  display: grid;
  gap: 6px;
  color: #465570;
  font-size: 12px;
  font-weight: 700;
}

.copy-fields select {
  width: 100%;
  min-height: 42px;
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  padding: 8px 10px;
  background: #fff;
  color: var(--text);
}

.copy-message {
  margin: 10px 0 0;
  border-radius: 9px;
  padding: 8px 10px;
  background: var(--tone-info-soft);
  color: var(--tone-info);
  font-size: 12px;
}

.copy-message.warning {
  background: var(--tone-warn-soft);
  color: var(--tone-warn);
}

.copy-message.danger {
  background: var(--tone-danger-soft);
  color: var(--tone-danger);
}

.copy-preview {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
  margin-top: 12px;
}

.copy-preview div {
  display: grid;
  gap: 3px;
  border-radius: 10px;
  padding: 9px;
  background: #f3f6fa;
  color: #56657f;
}

.copy-preview div.success {
  background: var(--tone-success-soft);
  color: var(--tone-success);
}

.copy-preview div.warning {
  background: var(--tone-warn-soft);
  color: var(--tone-warn);
}

.copy-preview span {
  font-size: 10px;
  font-weight: 700;
}

.copy-preview strong {
  font-size: 18px;
}

.overwrite-option {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-top: 12px;
  border: 1px solid var(--line);
  border-radius: 11px;
  padding: 10px;
  background: #fffdf8;
}

.overwrite-option input {
  width: 18px;
  height: 18px;
  margin: 1px 0 0;
}

.overwrite-option span {
  display: grid;
  gap: 3px;
}

.overwrite-option strong {
  color: #664a12;
  font-size: 12px;
}

.overwrite-option small {
  color: var(--muted);
  font-size: 11px;
  line-height: 1.45;
}

.copy-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

@media (max-width: 640px) {
  .copy-head,
  .copy-actions {
    align-items: stretch;
    flex-direction: column;
  }

  .copy-route,
  .copy-fields {
    grid-template-columns: 1fr;
  }

  .route-arrow {
    transform: rotate(90deg);
    justify-self: center;
  }

  .copy-preview {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
