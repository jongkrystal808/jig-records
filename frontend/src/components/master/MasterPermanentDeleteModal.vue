<script setup lang="ts">
import UiModalShell from "@/components/common/UiModalShell.vue";

export type MasterDeleteTargetType = "fixture" | "model" | "station";

const props = defineProps<{
  open: boolean;
  deleting: boolean;
  targetType: MasterDeleteTargetType | null;
  title: string;
  intro: string;
}>();

const emit = defineEmits<{
  close: [];
  confirm: [];
}>();

const deleteFixtureTransactions = defineModel<boolean>("deleteFixtureTransactions", { required: true });
</script>

<template>
  <UiModalShell
    :open="props.open"
    labelled-by="fixture-delete-title"
    dialog-role="alertdialog"
    layer-class="fixture-delete-backdrop"
    dialog-class="fixture-delete-dialog"
    :close-on-backdrop="!props.deleting"
    @close="emit('close')"
  >
    <header class="fixture-delete-dialog-head">
      <div>
        <p class="fixture-delete-eyebrow">Admin only</p>
        <h3 id="fixture-delete-title">{{ props.title }}</h3>
      </div>
      <button class="fixture-delete-close" type="button" :disabled="props.deleting" aria-label="關閉" @click="emit('close')">×</button>
    </header>
    <p class="fixture-delete-intro">{{ props.intro }}</p>

    <div v-if="props.targetType === 'fixture'" class="fixture-delete-options">
      <label :class="{ selected: !deleteFixtureTransactions }">
        <input v-model="deleteFixtureTransactions" type="radio" :value="false" />
        <span>
          <strong>保留收退料記錄（建議）</strong>
          <small>歷史明細會保留刪除當下的治具編號與名稱，仍可查詢及匯出。</small>
        </span>
      </label>

      <label :class="{ selected: deleteFixtureTransactions }">
        <input v-model="deleteFixtureTransactions" type="radio" :value="true" />
        <span>
          <strong>一併刪除相關記錄</strong>
          <small>只刪除此治具的明細；案件若還有其他治具會保留，沒有其他明細才刪除整張案件。</small>
        </span>
      </label>
    </div>

    <p v-if="deleteFixtureTransactions" class="fixture-delete-warning">相關收退料明細將永久刪除，且無法透過帳目管理復原。</p>
    <p v-else-if="props.targetType === 'model' || props.targetType === 'station'" class="fixture-delete-warning">將一併刪除關聯資料，且無法復原。</p>

    <footer class="fixture-delete-dialog-actions">
      <button class="outline-btn" type="button" :disabled="props.deleting" data-modal-initial-focus @click="emit('close')">取消</button>
      <button class="fixture-delete-confirm" type="button" :disabled="props.deleting" @click="emit('confirm')">
        {{ props.deleting ? "刪除中..." : "確認永久刪除" }}
      </button>
    </footer>
  </UiModalShell>
</template>
