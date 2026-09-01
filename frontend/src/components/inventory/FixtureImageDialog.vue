<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue";

import { fetchFixtureImageObjectUrl } from "@/api";
import UiModalShell from "@/components/common/UiModalShell.vue";

const props = defineProps<{
  open: boolean;
  fixtureCode: string;
  fixtureName: string;
  customerId: number | null;
}>();

const emit = defineEmits<{ close: [] }>();
const loading = ref(false);
const failed = ref(false);
const imageUrl = ref("");
let requestId = 0;

function releaseImageUrl(): void {
  if (!imageUrl.value) return;
  URL.revokeObjectURL(imageUrl.value);
  imageUrl.value = "";
}

async function loadImage(): Promise<void> {
  const currentRequestId = ++requestId;
  releaseImageUrl();
  failed.value = false;
  if (!props.open || !props.fixtureCode) {
    loading.value = false;
    return;
  }
  loading.value = true;
  try {
    if (props.customerId == null) throw new Error("customer_id is required");
    const objectUrl = await fetchFixtureImageObjectUrl(props.fixtureCode, props.customerId);
    if (currentRequestId !== requestId || !props.open) {
      URL.revokeObjectURL(objectUrl);
      return;
    }
    imageUrl.value = objectUrl;
  } catch {
    if (currentRequestId === requestId) failed.value = true;
  } finally {
    if (currentRequestId === requestId) loading.value = false;
  }
}

watch(
  () => [props.open, props.fixtureCode, props.customerId] as const,
  () => void loadImage(),
  { immediate: true }
);

onBeforeUnmount(() => {
  requestId += 1;
  releaseImageUrl();
});
</script>

<template>
  <UiModalShell
    :open="open"
    labelled-by="fixture-image-kicker fixture-image-title"
    described-by="fixture-image-description"
    layer-class="fixture-image-layer"
    dialog-class="fixture-image-dialog"
    @close="emit('close')"
  >
    <header>
      <div>
        <span id="fixture-image-kicker">治具圖片</span>
        <strong id="fixture-image-title">{{ fixtureCode }}</strong>
        <small>{{ fixtureName || "—" }}</small>
      </div>
      <button data-modal-initial-focus type="button" @click="emit('close')">關閉</button>
    </header>
    <div id="fixture-image-description" class="fixture-image-content">
      <span v-if="loading">圖片載入中…</span>
      <img
        v-else-if="imageUrl"
        :src="imageUrl"
        :alt="`${fixtureCode} ${fixtureName} 治具圖片`"
      />
      <div v-else class="fixture-image-empty">
        <strong>{{ failed ? "尚未建立圖片" : "無法顯示圖片" }}</strong>
        <span>請聯絡管理人員於治具主資料補上圖片。</span>
      </div>
    </div>
  </UiModalShell>
</template>

<style>
.fixture-image-layer {
  z-index: 145;
  padding: 18px;
}

.fixture-image-dialog {
  width: min(760px, 100%);
  max-height: min(760px, calc(100dvh - 36px));
  overflow: hidden;
  border: 1px solid #c5d5e9;
  border-radius: 13px;
  background: #fff;
  box-shadow: 0 24px 70px rgba(16, 36, 64, 0.3);
}

.fixture-image-dialog header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 12px 14px;
  border-bottom: 1px solid #d7e2ef;
  background: #f6f9fd;
}

.fixture-image-dialog header > div {
  display: grid;
  grid-template-columns: auto auto;
  align-items: baseline;
  gap: 2px 9px;
}

.fixture-image-dialog header span {
  grid-column: 1 / -1;
  color: #61718a;
  font-size: 0.68rem;
  font-weight: 750;
}

.fixture-image-dialog header strong {
  color: #245c9f;
  font-size: 0.95rem;
}

.fixture-image-dialog header small { color: #61718a; }

.fixture-image-dialog header button {
  min-height: 30px;
  padding: 4px 10px;
  border: 1px solid #a8bdd8;
  border-radius: 6px;
  color: #344b6b;
  background: #fff;
  font: inherit;
  font-size: 0.72rem;
  font-weight: 750;
  cursor: pointer;
}

.fixture-image-content {
  display: grid;
  min-height: 300px;
  max-height: calc(100dvh - 120px);
  place-items: center;
  overflow: auto;
  padding: 18px;
  background:
    linear-gradient(45deg, #f3f6fa 25%, transparent 25%),
    linear-gradient(-45deg, #f3f6fa 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #f3f6fa 75%),
    linear-gradient(-45deg, transparent 75%, #f3f6fa 75%);
  background-position: 0 0, 0 8px, 8px -8px, -8px 0;
  background-size: 16px 16px;
}

.fixture-image-content > span { color: #61718a; font-weight: 750; }

.fixture-image-content img {
  display: block;
  max-width: 100%;
  max-height: calc(100dvh - 160px);
  border-radius: 7px;
  object-fit: contain;
  box-shadow: 0 8px 24px rgba(31, 53, 82, 0.14);
}

.fixture-image-empty {
  display: grid;
  gap: 5px;
  padding: 30px;
  border-radius: 9px;
  color: #61718a;
  background: rgba(255, 255, 255, 0.92);
  text-align: center;
}

.fixture-image-empty strong { color: #344b6b; }
</style>
