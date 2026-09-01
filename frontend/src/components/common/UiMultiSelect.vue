<script setup lang="ts">
import { computed } from "vue";

export type UiMultiSelectOption = {
  value: string;
  label: string;
  disabled?: boolean;
};

const props = withDefaults(defineProps<{
  modelValue: string[];
  options: UiMultiSelectOption[];
  label: string;
  placeholder?: string;
  disabled?: boolean;
}>(), {
  placeholder: "全部",
  disabled: false
});

const emit = defineEmits<{
  "update:modelValue": [value: string[]];
  change: [value: string[]];
}>();

const selectedLabels = computed(() => props.options
  .filter((option) => props.modelValue.includes(option.value))
  .map((option) => option.label));
const summary = computed(() => {
  if (!selectedLabels.value.length) return props.placeholder;
  if (selectedLabels.value.length <= 2) return selectedLabels.value.join("、");
  return `已選 ${selectedLabels.value.length} 項`;
});

function updateOption(value: string, checked: boolean): void {
  const next = checked
    ? [...new Set([...props.modelValue, value])]
    : props.modelValue.filter((item) => item !== value);
  emit("update:modelValue", next);
  emit("change", next);
}

function selectAll(): void {
  const next = props.options.filter((option) => !option.disabled).map((option) => option.value);
  emit("update:modelValue", next);
  emit("change", next);
}

function clear(): void {
  emit("update:modelValue", []);
  emit("change", []);
}
</script>

<template>
  <div class="ui-multi-select" :class="{ disabled }">
    <span class="ui-multi-select-label">{{ label }}</span>
    <details :aria-label="`${label}複選`">
      <summary :aria-disabled="disabled" @click="disabled && $event.preventDefault()">
        <span>{{ summary }}</span>
        <small v-if="modelValue.length">{{ modelValue.length }} 項</small>
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="m6 8 4 4 4-4" /></svg>
      </summary>
      <div class="ui-multi-select-popover">
        <div class="ui-multi-select-actions">
          <button type="button" :disabled="disabled" @click="selectAll">全選</button>
          <button type="button" :disabled="disabled || !modelValue.length" @click="clear">清除</button>
        </div>
        <label
          v-for="option in options"
          :key="option.value"
          class="ui-multi-select-option"
          :class="{ selected: modelValue.includes(option.value) }"
        >
          <input
            type="checkbox"
            :checked="modelValue.includes(option.value)"
            :disabled="disabled || option.disabled"
            @change="updateOption(option.value, ($event.target as HTMLInputElement).checked)"
          />
          <span>{{ option.label }}</span>
        </label>
      </div>
    </details>
  </div>
</template>

<style scoped>
.ui-multi-select {
  position: relative;
  display: grid;
  min-width: 0;
  gap: 6px;
}

.ui-multi-select-label {
  color: var(--muted, #697791);
  font-size: 12px;
  font-weight: 700;
}

details { position: relative; }

summary {
  display: flex;
  min-height: 38px;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid var(--line-strong, #c8d1df);
  border-radius: 8px;
  background: var(--panel, #fff);
  color: var(--text, #24324a);
  cursor: pointer;
  list-style: none;
}

summary::-webkit-details-marker { display: none; }
summary > span { min-width: 0; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
summary small { color: var(--blue, #2f6ee5); font-size: 11px; white-space: nowrap; }
summary svg { width: 16px; height: 16px; fill: none; stroke: currentColor; stroke-width: 1.8; transition: transform .16s ease; }
details[open] summary svg { transform: rotate(180deg); }
details[open] summary { border-color: color-mix(in srgb, var(--blue, #2f6ee5) 58%, white); box-shadow: 0 0 0 3px color-mix(in srgb, var(--blue, #2f6ee5) 12%, transparent); }

.ui-multi-select-popover {
  position: absolute;
  z-index: 45;
  top: calc(100% + 6px);
  left: 0;
  min-width: 100%;
  width: max-content;
  max-width: min(320px, 85vw);
  padding: 8px;
  border: 1px solid var(--line-strong, #c8d1df);
  border-radius: 10px;
  background: var(--panel, #fff);
  box-shadow: 0 14px 34px rgba(30, 45, 70, .18);
}

.ui-multi-select-actions { display: flex; justify-content: flex-end; gap: 6px; padding: 0 0 6px; border-bottom: 1px solid var(--line, #e3e7ee); }
.ui-multi-select-actions button { padding: 4px 7px; border: 0; background: transparent; color: var(--blue, #2f6ee5); font: inherit; font-size: 12px; cursor: pointer; }
.ui-multi-select-option { position: relative; display: flex; min-height: 34px; align-items: center; padding: 5px 7px; border-radius: 6px; cursor: pointer; }
.ui-multi-select-option:hover { background: var(--blue-soft, #eef4ff); }
.ui-multi-select-option.selected { color: var(--blue, #2f6ee5); background: var(--blue-soft, #eef4ff); font-weight: 800; }
.ui-multi-select-option:focus-within { outline: 2px solid color-mix(in srgb, var(--blue, #2f6ee5) 55%, transparent); outline-offset: 1px; }
.ui-multi-select-option input {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  white-space: nowrap;
}
.disabled { opacity: .58; }
.disabled summary { cursor: not-allowed; }
</style>
