<script setup lang="ts">
import UiModalShell from "@/components/common/UiModalShell.vue";
import type { ConfirmationTone } from "@/confirmState";

defineProps<{
  open: boolean;
  title: string;
  message: string;
  confirmLabel: string;
  cancelLabel: string;
  tone: ConfirmationTone;
}>();

const emit = defineEmits<{
  confirm: [];
  cancel: [];
}>();
</script>

<template>
  <UiModalShell
    :open="open"
    labelled-by="system-confirm-title"
    described-by="system-confirm-message"
    dialog-role="alertdialog"
    layer-class="confirm-layer"
    :dialog-class="`confirm-dialog ${tone}`"
    @close="emit('cancel')"
  >
    <span class="confirm-kicker">{{ tone === "danger" ? "需要特別確認" : "系統確認" }}</span>
    <h2 id="system-confirm-title">{{ title }}</h2>
    <p id="system-confirm-message">{{ message }}</p>
    <div class="confirm-actions">
      <button class="cancel-button" data-modal-initial-focus type="button" @click="emit('cancel')">
        {{ cancelLabel }}
      </button>
      <button class="confirm-button" type="button" @click="emit('confirm')">
        {{ confirmLabel }}
      </button>
    </div>
  </UiModalShell>
</template>

<style scoped>
:deep(.confirm-layer) {
  z-index: 220;
  padding: 16px;
  background: rgba(15, 31, 52, 0.52);
}

:deep(.confirm-dialog) {
  width: min(460px, 100%);
  padding: 22px;
  border: 1px solid #c8d7ea;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 24px 70px rgba(16, 36, 64, 0.3);
}

:deep(.confirm-dialog.danger) {
  border-color: #e5b7b4;
}

.confirm-kicker {
  color: #2f6ee5;
  font-size: 11px;
  font-weight: 850;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

:deep(.confirm-dialog.danger) .confirm-kicker {
  color: #b33d38;
}

:deep(.confirm-dialog) h2 {
  margin: 7px 0 9px;
  color: #20304f;
  font-size: 21px;
}

:deep(.confirm-dialog) p {
  margin: 0;
  color: #5b6b84;
  font-size: 14px;
  line-height: 1.65;
  white-space: pre-line;
}

.confirm-actions {
  display: flex;
  justify-content: flex-end;
  gap: 9px;
  margin-top: 20px;
}

.confirm-actions button {
  min-height: 38px;
  padding: 7px 16px;
  border-radius: 9px;
  font: inherit;
  font-weight: 800;
  cursor: pointer;
}

.cancel-button {
  border: 1px solid #bac8da;
  color: #52627a;
  background: #fff;
}

.confirm-button {
  border: 1px solid #2f6ee5;
  color: #fff;
  background: #2f6ee5;
}

:deep(.confirm-dialog.danger) .confirm-button {
  border-color: #bd3e3e;
  background: #bd3e3e;
}

@media (max-width: 560px) {
  :deep(.confirm-dialog) {
    padding: 18px;
  }

  .confirm-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
}
</style>
