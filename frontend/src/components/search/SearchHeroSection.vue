<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";

type SearchMode = "fixture" | "model";

type SearchChip = {
  key: string;
  label: string;
};

type RecentFixtureShortcut = {
  fixtureCode: string;
  transactionType: "receipt" | "return";
  occurredAt: string;
};

const RECENT_SHORTCUT_PREVIEW_COUNT = 5;

const props = defineProps<{
  mode: SearchMode;
  queryDraft: string;
  hasActiveQuery: boolean;
  recentFixtureShortcuts: RecentFixtureShortcut[];
  sectionChips: SearchChip[];
  activeSectionKeys: string[];
}>();

const emit = defineEmits<{
  "update:mode": [value: SearchMode];
  "update:queryDraft": [value: string];
  submit: [];
  clear: [];
  applyRecentFixtureShortcut: [fixtureCode: string];
  toggleSection: [mode: SearchMode, key: string];
}>();

// Keep the search landing shell in one component so the page only owns query state and result data.
// Shortcut expansion stays local here because it is presentational state, not search state.
const recentShortcutExpanded = ref(false);
const queryInput = ref<HTMLInputElement | null>(null);
const visibleRecentFixtureShortcuts = computed(() =>
  recentShortcutExpanded.value ? props.recentFixtureShortcuts : props.recentFixtureShortcuts.slice(0, RECENT_SHORTCUT_PREVIEW_COUNT)
);
const hiddenRecentShortcutCount = computed(() => Math.max(props.recentFixtureShortcuts.length - RECENT_SHORTCUT_PREVIEW_COUNT, 0));

function focusQueryInput(): void {
  queryInput.value?.focus();
}

function handleClear(): void {
  emit("clear");
  void nextTick(() => {
    focusQueryInput();
  });
}

watch(
  () => props.recentFixtureShortcuts,
  () => {
    recentShortcutExpanded.value = false;
  }
);
</script>

<template>
  <section class="hero-card" :class="{ idle: !hasActiveQuery }">
    <div class="hero-copy">
      <span class="eyebrow">Search Workspace</span>
      <h1>治具 / 機種查詢</h1>
    </div>

    <div class="search-toolbar">
      <div class="mode-switch" data-tour="search-mode-switch">
        <button class="mode-btn" :class="{ active: mode === 'fixture' }" type="button" @click="emit('update:mode', 'fixture')">治具</button>
        <button class="mode-btn" :class="{ active: mode === 'model' }" type="button" @click="emit('update:mode', 'model')">機種</button>
      </div>
      <label class="query-field" data-tour="search-query-field">
        <div class="query-input-shell">
          <input
            ref="queryInput"
            :value="queryDraft"
            :placeholder="mode === 'fixture' ? '請輸入治具編號 / 名稱,例如 C-00003' : '請輸入機種編號 / 名稱,例如 VPort-254'"
            autocomplete="off"
            spellcheck="false"
            @input="emit('update:queryDraft', ($event.target as HTMLInputElement).value)"
            @keydown.enter.prevent="emit('submit')"
            @keydown.esc.prevent="handleClear"
          />
          <button
            v-if="queryDraft.trim().length > 0"
            class="query-clear-btn"
            type="button"
            aria-label="清空搜尋欄"
            title="清空搜尋欄"
            @click="handleClear"
          >
            ×
          </button>
        </div>
      </label>
    </div>

    <div v-if="recentFixtureShortcuts.length > 0" class="shortcut-panel">
      <div class="smart-hint-head">
        <strong>最近收 / 退料治具</strong>
        <div class="shortcut-head-actions">
          <span>{{ recentFixtureShortcuts.length }} 筆</span>
          <button
            v-if="hiddenRecentShortcutCount > 0 || recentShortcutExpanded"
            class="shortcut-toggle-btn"
            type="button"
            @click="recentShortcutExpanded = !recentShortcutExpanded"
          >
            {{ recentShortcutExpanded ? "收合" : `顯示更多（+${hiddenRecentShortcutCount}）` }}
          </button>
        </div>
      </div>
      <div class="shortcut-row">
        <button
          v-for="shortcut in visibleRecentFixtureShortcuts"
          :key="`${shortcut.fixtureCode}-${shortcut.transactionType}-${shortcut.occurredAt}`"
          class="shortcut-chip"
          type="button"
          @click="emit('applyRecentFixtureShortcut', shortcut.fixtureCode)"
        >
          <span class="shortcut-chip-badge" :class="shortcut.transactionType">
            {{ shortcut.transactionType === "receipt" ? "收" : "退" }}
          </span>
          <strong>{{ shortcut.fixtureCode }}</strong>
        </button>
      </div>
    </div>

    <div class="chip-row" data-tour="search-section-chips">
      <button
        v-for="chip in sectionChips"
        :key="`${mode}-${chip.key}`"
        class="chip-toggle"
        :class="{ active: activeSectionKeys.includes(chip.key) }"
        type="button"
        @click="emit('toggleSection', mode, chip.key)"
      >
        {{ chip.label }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.hero-card {
  display: grid;
  gap: 12px;
  padding: 16px;
  position: relative;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 20px;
  background:
    radial-gradient(circle at 0% 0%, color-mix(in srgb, var(--blue) 16%, transparent), transparent 30%),
    radial-gradient(circle at 100% 0%, color-mix(in srgb, var(--blue) 8%, transparent), transparent 26%),
    linear-gradient(180deg, #ffffff 0%, color-mix(in srgb, var(--blue-soft) 50%, white) 100%);
  box-shadow: var(--shadow);
}

.hero-card::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 4px;
  background: linear-gradient(180deg, var(--blue) 0%, color-mix(in srgb, var(--blue) 55%, white) 100%);
}

.hero-card > * {
  position: relative;
  z-index: 1;
}

.hero-card.idle {
  justify-items: center;
  text-align: center;
  padding: 30px 24px 26px;
}

.hero-card.idle .hero-copy,
.hero-card.idle .search-toolbar,
.hero-card.idle .chip-row {
  width: min(760px, 100%);
}

.hero-card.idle .mode-switch,
.hero-card.idle .chip-row {
  justify-content: center;
}

.eyebrow {
  color: var(--blue);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h1 {
  margin: 4px 0 0;
  color: #22314a;
  font-size: 24px;
}

.hero-copy p {
  margin: 4px 0 0;
  max-width: 640px;
  color: #5d6d89;
  font-size: 12px;
  line-height: 1.6;
}

.search-toolbar {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 12px;
}

.hero-card.idle .search-toolbar {
  align-items: end;
}

.mode-switch {
  display: inline-flex;
  gap: 4px;
  padding: 4px;
  border: 1px solid color-mix(in srgb, var(--blue) 18%, var(--line));
  border-radius: 999px;
  background: color-mix(in srgb, var(--blue-soft) 68%, white);
}

.mode-btn {
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: #5b677d;
  padding: 8px 14px;
  min-height: 36px;
  font-weight: 800;
}

.mode-btn.active {
  background: #fff;
  color: var(--tone-info);
  box-shadow: 0 6px 16px color-mix(in srgb, var(--blue) 18%, transparent);
}

.query-field {
  display: grid;
  gap: 6px;
}

.query-input-shell {
  position: relative;
}

.query-field input {
  width: 100%;
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  padding: 9px 72px 9px 10px;
  background: #fff;
  font: inherit;
}

.query-field input:focus {
  outline: none;
  border-color: var(--blue);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--blue-soft) 88%, white);
}

.query-clear-btn {
  position: absolute;
  top: 50%;
  right: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid color-mix(in srgb, var(--blue) 18%, var(--line));
  border-radius: 999px;
  background: color-mix(in srgb, var(--blue-soft) 72%, white);
  color: var(--tone-info);
  width: 28px;
  height: 28px;
  padding: 0;
  font-size: 15px;
  font-weight: 800;
  line-height: 1;
  transform: translateY(calc(-56% - 3px));
}

.shortcut-panel {
  display: grid;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid color-mix(in srgb, var(--blue) 16%, var(--line));
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, color-mix(in srgb, var(--blue-soft) 42%, white) 100%);
}

.smart-hint-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.shortcut-head-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.smart-hint-head strong {
  color: #22314a;
  font-size: 12px;
}

.smart-hint-head span,
.shortcut-panel span {
  color: #5d6d89;
  font-size: 11px;
}

.shortcut-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}


.shortcut-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 32px;
  padding: 4px 10px;
  border: 1px solid color-mix(in srgb, var(--blue) 18%, var(--line));
  border-radius: 999px;
  background: #fff;
  color: #22314a;
}

.shortcut-chip strong {
  font-size: 11px;
}

.shortcut-toggle-btn {
  border: 1px solid color-mix(in srgb, var(--blue) 18%, var(--line));
  border-radius: 999px;
  background: color-mix(in srgb, var(--blue-soft) 72%, white);
  color: var(--tone-info);
  min-height: 30px;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 800;
}

.shortcut-chip-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  min-height: 18px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 800;
}

.shortcut-chip-badge.receipt {
  background: var(--action-in-soft);
  color: var(--action-in-strong);
}

.shortcut-chip-badge.return {
  background: var(--action-out-soft);
  color: var(--action-out-strong);
}

.chip-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.chip-toggle {
  border: 1px solid color-mix(in srgb, var(--blue) 18%, var(--line));
  border-radius: 999px;
  background: color-mix(in srgb, var(--blue-soft) 70%, white);
  color: color-mix(in srgb, var(--blue) 72%, var(--text));
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 700;
}

.chip-toggle.active {
  border-color: color-mix(in srgb, var(--blue) 26%, var(--line));
  background: color-mix(in srgb, var(--blue-soft) 92%, white);
  color: var(--tone-info);
}

@media (max-width: 960px) {
  .search-toolbar {
    grid-template-columns: 1fr;
  }
}
</style>
