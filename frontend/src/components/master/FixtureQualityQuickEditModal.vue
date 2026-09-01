<script setup lang="ts">
import UiModalShell from "@/components/common/UiModalShell.vue";
import type { Fixture, MachineModel, Station } from "@/types";

type FixtureQuickEditForm = {
  code: string;
  name: string;
  responsible_user_id: number | null;
  line_storage_location: string;
  department_storage_location: string;
  min_stock_qty: number;
  description: string;
  is_active: boolean;
};

const props = defineProps<{
  open: boolean;
  busy: boolean;
  issueCode: string | null;
  fixture: Fixture | null;
  models: MachineModel[];
  stationOptions: Station[];
  imageUrl: string;
  imageFile: File | null;
  quickEditSaving: boolean;
  relationSaving: boolean;
  imageUploading: boolean;
  title: string;
}>();

const emit = defineEmits<{
  close: [];
  imageChange: [event: Event];
  imageInput: [input: HTMLInputElement | null];
  openLedger: [];
  saveFixture: [];
  saveRelation: [];
  uploadImage: [];
}>();

const form = defineModel<FixtureQuickEditForm>("form", { required: true });
const relationModelId = defineModel<number | null>("relationModelId", { required: true });
const relationStationId = defineModel<number | null>("relationStationId", { required: true });
const relationRequiredQty = defineModel<number>("relationRequiredQty", { required: true });

function captureImageInput(element: unknown): void {
  emit("imageInput", element instanceof HTMLInputElement ? element : null);
}
</script>

<template>
  <UiModalShell
    :open="props.open"
    labelled-by="quality-issue-title"
    layer-class="quality-issue-backdrop"
    dialog-class="quality-issue-dialog"
    :close-on-backdrop="!props.busy"
    @close="emit('close')"
  >
    <header class="quality-issue-head">
      <div>
        <p class="fixture-delete-eyebrow">治具資料品質</p>
        <h3 id="quality-issue-title">{{ props.title }}</h3>
      </div>
      <button class="fixture-delete-close" type="button" :disabled="props.busy" aria-label="關閉" @click="emit('close')">×</button>
    </header>

    <div class="quality-issue-body">
      <p class="quality-issue-intro">點擊品質問題後可直接在這裡修正，不需要先跳頁。</p>

      <label v-if="props.issueCode === 'missing_name'" class="quality-field">
        <span>治具名稱 *</span>
        <input v-model="form.name" data-modal-initial-focus />
      </label>

      <template v-else-if="props.issueCode === 'missing_storage_and_min_stock'">
        <label class="quality-field">
          <span>產線儲位</span>
          <input v-model="form.line_storage_location" placeholder="A-01-03" data-modal-initial-focus />
        </label>
        <label class="quality-field">
          <span>部門儲位</span>
          <input v-model="form.department_storage_location" placeholder="RD-SHELF-3" />
        </label>
        <label class="quality-field">
          <span>最低水位</span>
          <input v-model.number="form.min_stock_qty" type="number" min="0" />
        </label>
      </template>

      <template v-else-if="props.issueCode === 'missing_model_relation'">
        <p class="quality-helper">直接補上第一筆機種 / 站點 / 治具需求；若缺少 mapping，會一併建立。</p>
        <label class="quality-field">
          <span>機種 *</span>
          <select v-model="relationModelId" data-modal-initial-focus>
            <option :value="null">請選擇機種</option>
            <option v-for="row in props.models" :key="row.id" :value="row.id">{{ row.code }} / {{ row.name }}</option>
          </select>
        </label>
        <label class="quality-field">
          <span>站點 *</span>
          <select v-model="relationStationId">
            <option :value="null">請選擇站點</option>
            <option v-for="row in props.stationOptions" :key="row.id" :value="row.id">{{ row.code }} / {{ row.name }}</option>
          </select>
        </label>
        <label class="quality-field">
          <span>需求數量 *</span>
          <input v-model.number="relationRequiredQty" type="number" min="1" />
        </label>
      </template>

      <template v-else-if="props.issueCode === 'missing_image'">
        <p class="quality-helper">直接上傳治具圖片；成功後會即時刷新品質結果。</p>
        <div v-if="props.imageUrl" class="quality-image-preview">
          <img :src="props.imageUrl" :alt="`${props.fixture?.code || 'fixture'} image`" />
        </div>
        <label class="quality-field">
          <span>選擇圖片 *</span>
          <input :ref="captureImageInput" type="file" accept="image/png,image/jpeg,image/webp,image/gif" data-modal-initial-focus @change="emit('imageChange', $event)" />
        </label>
        <p class="quality-helper">支援 PNG / JPG / WEBP / GIF，大小上限 5 MB。</p>
      </template>

      <template v-else-if="props.issueCode === 'stock_mismatch'">
        <p class="quality-helper">這個異常來自交易明細與庫存摘要不一致，不是治具主檔欄位缺漏。請到收退料帳目管理做重算或撤回；這裡先不自動跳頁。</p>
        <button class="outline-btn" type="button" data-modal-initial-focus @click="emit('openLedger')">前往收退料帳目管理</button>
      </template>
    </div>

    <footer class="quality-issue-actions">
      <button class="outline-btn" type="button" :disabled="props.busy" @click="emit('close')">關閉</button>
      <button
        v-if="props.issueCode === 'missing_name' || props.issueCode === 'missing_storage_and_min_stock'"
        class="fixture-delete-confirm"
        type="button"
        :disabled="props.quickEditSaving"
        @click="emit('saveFixture')"
      >
        {{ props.quickEditSaving ? "儲存中..." : "直接更新治具" }}
      </button>
      <button
        v-else-if="props.issueCode === 'missing_image'"
        class="fixture-delete-confirm"
        type="button"
        :disabled="props.imageUploading || !props.imageFile"
        @click="emit('uploadImage')"
      >
        {{ props.imageUploading ? "上傳中..." : "上傳圖片" }}
      </button>
      <button
        v-else-if="props.issueCode === 'missing_model_relation'"
        class="fixture-delete-confirm"
        type="button"
        :disabled="props.relationSaving"
        @click="emit('saveRelation')"
      >
        {{ props.relationSaving ? "建立中..." : "建立第一筆關聯" }}
      </button>
    </footer>
  </UiModalShell>
</template>
