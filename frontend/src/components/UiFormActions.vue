<script setup lang="ts">
withDefaults(
  defineProps<{
    editing?: boolean;
    saving?: boolean;
    submitLabel?: string;
    savingLabel?: string;
    cancelLabel?: string;
    deleteLabel?: string;
    showDelete?: boolean;
    showState?: boolean;
    stateText?: string;
  }>(),
  {
    editing: false,
    saving: false,
    submitLabel: "儲存",
    savingLabel: "處理中...",
    cancelLabel: "取消",
    deleteLabel: "刪除",
    showDelete: false,
    showState: true,
    stateText: ""
  }
);

defineEmits<{
  cancel: [];
  submit: [];
  delete: [];
}>();
</script>

<template>
  <div class="ui-form-actions">
    <div v-if="showState" class="state-row">
      <span class="state-pill" :class="{ editing }">{{ stateText || (editing ? "編輯模式" : "新增模式") }}</span>
    </div>
    <div class="button-row">
      <button class="outline-btn" type="button" @click="$emit('cancel')">{{ cancelLabel }}</button>
      <button v-if="showDelete" class="danger-btn" type="button" @click="$emit('delete')">{{ deleteLabel }}</button>
      <button class="primary-btn" type="submit" :disabled="saving">
        {{ saving ? savingLabel : submitLabel }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.ui-form-actions {
  display: grid;
  gap: 8px;
}

.state-row {
  display: flex;
  justify-content: flex-start;
}

.state-pill {
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
}

.state-pill.editing {
  border-color: #a9c3f9;
  background: #eef5ff;
  color: var(--blue);
}

.button-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.button-row button {
  flex: 1 1 120px;
}
</style>
