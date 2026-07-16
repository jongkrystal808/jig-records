<script setup lang="ts">
defineProps<{
  modelValue: string;
  disabled?: boolean;
  placeholder?: string;
  menuOpen: boolean;
  suggestions: Array<{ id: number; code: string }>;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string];
  focus: [];
  blur: [];
  select: [code: string];
}>();
</script>

<template>
  <div class="autocomplete-field">
    <input
      :value="modelValue"
      :disabled="disabled"
      :placeholder="placeholder"
      autocomplete="off"
      spellcheck="false"
      @focus="emit('focus')"
      @click="emit('focus')"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      @blur="emit('blur')"
    />
    <div v-if="menuOpen" class="autocomplete-menu">
      <button
        v-for="suggestion in suggestions"
        :key="suggestion.id"
        class="autocomplete-option"
        type="button"
        @mousedown.prevent="emit('select', suggestion.code)"
      >
        {{ suggestion.code }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.autocomplete-field {
  position: relative;
}

.autocomplete-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  z-index: 20;
  display: grid;
  max-height: 220px;
  overflow: auto;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 16px 34px rgba(17, 24, 39, 0.12);
}

.autocomplete-option {
  border: 0;
  border-bottom: 1px solid rgba(220, 227, 238, 0.9);
  background: #fff;
  padding: 9px 12px;
  text-align: left;
  color: #31435e;
  font: inherit;
  cursor: pointer;
}

.autocomplete-option:last-child {
  border-bottom: none;
}

.autocomplete-option:hover {
  background: #f3f7ff;
}

input {
  width: 100%;
  min-height: 36px;
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  padding: 8px 10px;
  background: #fff;
  font: inherit;
}
</style>
