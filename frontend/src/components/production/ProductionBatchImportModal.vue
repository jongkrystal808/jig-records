<script setup lang="ts">
defineProps<{
  open: boolean;
  title: string;
  description: string;
  text: string;
  placeholder: string;
  saving: boolean;
  submitLabel: string;
  readyCount: number;
  pendingCount: number;
  errorCount: number;
}>();

const emit = defineEmits<{
  close: [];
  clear: [];
  submit: [];
  "update:text": [value: string];
}>();

// Keep the shared batch-import modal shell outside ProductionPage so the page only owns parsing and submit logic.
</script>

<template>
  <teleport to="body">
    <div v-if="open" class="ui-modal-backdrop" @click.self="emit('close')">
      <div class="ui-modal-card ui-modal-card--compact">
        <div class="ui-section-head">
          <div>
            <h2>{{ title }}</h2>
            <p>{{ description }}</p>
          </div>
          <button class="outline-btn" type="button" @click="emit('close')">關閉</button>
        </div>
        <textarea
          :value="text"
          class="batch-paste-box"
          :placeholder="placeholder"
          @input="emit('update:text', ($event.target as HTMLTextAreaElement).value)"
        ></textarea>
        <div class="batch-modal-actions">
          <button class="outline-btn" type="button" @click="emit('clear')">清空</button>
          <button class="primary-btn" type="button" :disabled="saving" @click="emit('submit')">
            {{ saving ? "匯入中..." : submitLabel }}
          </button>
        </div>
        <div class="batch-meta">可匯入 {{ readyCount }} / 待確認 {{ pendingCount }} / 錯誤 {{ errorCount }}</div>
        <div class="batch-table-wrap">
          <slot />
        </div>
      </div>
    </div>
  </teleport>
</template>

<style scoped>
.ui-section-head h2 {
  margin: 0;
  color: #22314a;
  font-size: 18px;
}

.ui-section-head p {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.55;
}

.batch-paste-box {
  width: 100%;
  min-height: 260px;
  margin-top: 8px;
  border: 1px solid var(--line-strong);
  border-radius: 12px;
  padding: 12px;
  font: inherit;
  line-height: 1.6;
  resize: vertical;
  background: #fff;
}

.batch-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}

.batch-meta {
  margin-top: 10px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}

.batch-table-wrap {
  margin-top: 10px;
  max-height: 360px;
  overflow: auto;
}

@media (max-width: 720px) {
  .ui-section-head {
    align-items: flex-start;
  }

  .batch-modal-actions {
    flex-direction: column;
  }
}
</style>
