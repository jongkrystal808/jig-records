<script setup lang="ts">
import { computed, onBeforeUnmount, ref, useAttrs, useId, watch } from "vue";

defineOptions({ inheritAttrs: false });

export type FormAutocompleteOption = {
  id: number;
  code: string;
  name: string;
};

const props = withDefaults(defineProps<{
  modelValue: string;
  options: FormAutocompleteOption[];
  inputLabel?: string;
  placeholder?: string;
  loading?: boolean;
  disabled?: boolean;
}>(), {
  placeholder: "輸入編號或名稱",
  loading: false,
  disabled: false
});

const emit = defineEmits<{
  "update:modelValue": [value: string];
  search: [value: string];
  select: [option: FormAutocompleteOption];
}>();

const attrs = useAttrs();
const input = ref<HTMLInputElement | null>(null);
const open = ref(false);
const activeIndex = ref(-1);
const listboxId = `form-autocomplete-${useId()}`;
let blurTimer: number | undefined;

const visibleOptions = computed(() => props.options.slice(0, 20));
const resolvedInputLabel = computed(() => props.inputLabel || String(attrs["aria-label"] || "選擇項目"));
const activeDescendant = computed(() => activeIndex.value >= 0
  ? `${listboxId}-option-${activeIndex.value}`
  : undefined
);

function optionLabel(option: FormAutocompleteOption): string {
  return `${option.code}－${option.name}`;
}

function exactOption(value: string): FormAutocompleteOption | undefined {
  const normalized = value.trim().toLowerCase();
  if (!normalized) return undefined;
  return visibleOptions.value.find((option) =>
    [option.code, option.name, optionLabel(option)].some((candidate) => candidate.toLowerCase() === normalized)
  );
}

function requestOptions(value = props.modelValue): void {
  open.value = true;
  emit("search", value);
}

function updateValue(event: Event): void {
  const value = (event.target as HTMLInputElement).value;
  activeIndex.value = -1;
  emit("update:modelValue", value);
  requestOptions(value);
}

function selectOption(option: FormAutocompleteOption): void {
  window.clearTimeout(blurTimer);
  emit("update:modelValue", optionLabel(option));
  emit("select", option);
  open.value = false;
  activeIndex.value = -1;
}

function handleBlur(): void {
  blurTimer = window.setTimeout(() => {
    const exact = exactOption(props.modelValue);
    if (exact) selectOption(exact);
    else open.value = false;
  }, 120);
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key === "ArrowDown") {
    event.preventDefault();
    if (!open.value) requestOptions();
    activeIndex.value = Math.min(activeIndex.value + 1, visibleOptions.value.length - 1);
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    activeIndex.value = Math.max(activeIndex.value - 1, 0);
  } else if (event.key === "Enter" && open.value) {
    const option = visibleOptions.value[activeIndex.value] ?? exactOption(props.modelValue);
    if (option) {
      event.preventDefault();
      selectOption(option);
    }
  } else if (event.key === "Escape") {
    open.value = false;
    activeIndex.value = -1;
  }
}

watch(visibleOptions, (options) => {
  if (activeIndex.value >= options.length) activeIndex.value = options.length - 1;
});

onBeforeUnmount(() => window.clearTimeout(blurTimer));
</script>

<template>
  <div class="remote-autocomplete">
    <input
      ref="input"
      type="text"
      role="combobox"
      autocomplete="off"
      :value="modelValue"
      :placeholder="placeholder"
      :aria-label="resolvedInputLabel"
      :aria-expanded="open"
      :aria-controls="listboxId"
      :aria-activedescendant="activeDescendant"
      :disabled="disabled"
      @focus="requestOptions()"
      @input="updateValue"
      @blur="handleBlur"
      @keydown="handleKeydown"
    />
    <div v-if="open" :id="listboxId" class="autocomplete-menu" role="listbox" :aria-label="`${resolvedInputLabel}選項`">
      <button
        v-for="(option, index) in visibleOptions"
        :id="`${listboxId}-option-${index}`"
        :key="option.id"
        class="autocomplete-option"
        :class="{ active: activeIndex === index }"
        type="button"
        role="option"
        :aria-selected="activeIndex === index"
        @mousedown.prevent="selectOption(option)"
      >
        <strong>{{ option.code }}</strong>
        <span>{{ option.name }}</span>
      </button>
      <p v-if="loading" class="autocomplete-state" role="status">搜尋中...</p>
      <p v-else-if="visibleOptions.length === 0" class="autocomplete-state">找不到符合資料</p>
    </div>
  </div>
</template>

<style scoped>
.remote-autocomplete { position: relative; width: 100%; min-width: 0; }
.remote-autocomplete > input { width: 100%; min-width: 0; min-height: 34px; padding: 0 9px; border: 1px solid var(--line-strong); border-radius: 5px; outline: none; color: var(--text); background: #fff; font: inherit; }
.remote-autocomplete > input:focus { border-color: var(--tone-info); box-shadow: 0 0 0 3px var(--tone-info-soft); }
.autocomplete-menu { position: absolute; z-index: 30; top: calc(100% + 3px); left: 0; width: max(100%, 260px); max-height: 240px; padding: 4px; overflow-y: auto; border: 1px solid var(--line-strong); border-radius: 7px; background: #fff; box-shadow: 0 12px 30px rgba(28, 47, 84, 0.18); }
.autocomplete-option { display: grid; grid-template-columns: minmax(90px, auto) minmax(0, 1fr); gap: 8px; width: 100%; padding: 7px 8px; border: 0; border-radius: 5px; color: var(--text); background: transparent; font: inherit; text-align: left; cursor: pointer; }
.autocomplete-option:hover, .autocomplete-option.active { background: #edf5ff; }
.autocomplete-option strong, .autocomplete-option span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.autocomplete-option strong { color: #285d9b; font-size: .73rem; }
.autocomplete-option span { color: var(--muted); font-size: .7rem; }
.autocomplete-state { margin: 0; padding: 9px; color: var(--muted); font-size: .7rem; text-align: center; }
@media (max-width: 620px) { .autocomplete-menu { width: 100%; } }
</style>
