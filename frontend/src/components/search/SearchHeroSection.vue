<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { currentReleaseNotice } from "@/releaseNotice";

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
const hasReleaseNotice = computed(() => currentReleaseNotice.highlights.length > 0);
const showRecentShortcutContent = computed(() => !props.hasActiveQuery || recentShortcutExpanded.value);

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

watch(
  () => props.hasActiveQuery,
  (hasActiveQuery) => {
    if (hasActiveQuery) {
      recentShortcutExpanded.value = false;
    }
  }
);
</script>

<template>
  <section class="hero-card" :class="{ idle: !hasActiveQuery }">
    <div class="hero-head">
      <div class="hero-copy">
        <span class="eyebrow">Search Workspace</span>
        <h1>治具 / 機種查詢</h1>
      </div>
      <div v-if="hasReleaseNotice" class="release-notice-anchor">
        <button
          class="release-notice-trigger"
          type="button"
          aria-label="查看更新內容"
          title="查看更新內容"
        >
          i
        </button>
        <div class="release-notice-popover" role="note">
          <div class="release-notice-head">
            <span class="release-notice-version">{{ currentReleaseNotice.versionLabel }}</span>
            <strong>{{ currentReleaseNotice.title }}</strong>
          </div>
          <p>{{ currentReleaseNotice.summary }}</p>
          <ul>
            <li v-for="highlight in currentReleaseNotice.highlights" :key="highlight">
              {{ highlight }}
            </li>
          </ul>
        </div>
      </div>
    </div>

    <div class="search-toolbar">
      <div class="mode-switch" data-tour="search-mode-switch">
        <button class="mode-btn" :class="{ active: mode === 'fixture' }" type="button" :aria-pressed="mode === 'fixture'" @click="emit('update:mode', 'fixture')">治具</button>
        <button class="mode-btn" :class="{ active: mode === 'model' }" type="button" :aria-pressed="mode === 'model'" @click="emit('update:mode', 'model')">機種</button>
      </div>
      <label class="query-field" data-tour="search-query-field">
        <div class="query-input-shell">
          <input
            ref="queryInput"
            :value="queryDraft"
            :aria-label="mode === 'fixture' ? '搜尋治具編號或名稱' : '搜尋機種編號或名稱'"
            :placeholder="mode === 'fixture' ? '請輸入治具編號 / 名稱,例如 C-00003' : '請輸入機種編號 / 名稱,例如 VPort-254'"
            autocomplete="off"
            spellcheck="false"
            @input="emit('update:queryDraft', ($event.target as HTMLInputElement).value)"
            @keydown.enter.prevent="emit('submit')"
            @keydown.esc.prevent="handleClear"
          />
          <button class="query-submit-btn" type="button" @click="emit('submit')">搜尋</button>
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
          <button class="shortcut-toggle-btn" type="button" @click="recentShortcutExpanded = !recentShortcutExpanded">
            {{ showRecentShortcutContent ? "收合" : `展開近期治具（${recentFixtureShortcuts.length}）` }}
          </button>
        </div>
      </div>
      <div v-if="showRecentShortcutContent" class="shortcut-row">
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
  overflow: visible;
  border: 1px solid var(--line);
  border-radius: 20px;
  background:
    radial-gradient(circle at 0% 0%, color-mix(in srgb, var(--blue) 16%, transparent), transparent 30%),
    radial-gradient(circle at 100% 0%, color-mix(in srgb, var(--blue) 8%, transparent), transparent 26%),
    linear-gradient(180deg, #ffffff 0%, color-mix(in srgb, var(--blue-soft) 50%, white) 100%);
  box-shadow: var(--shadow);
}

.hero-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
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

.hero-card.idle .hero-head {
  width: min(760px, 100%);
}

.hero-card.idle .mode-switch,
.hero-card.idle .chip-row {
  justify-content: center;
}

.hero-card.idle .hero-head {
  align-items: flex-start;
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

.release-notice-anchor {
  position: relative;
  flex: 0 0 auto;
  z-index: 20;
}

.release-notice-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: 1px solid color-mix(in srgb, var(--blue) 20%, var(--line));
  border-radius: 999px;
  background: color-mix(in srgb, var(--blue-soft) 78%, white);
  color: var(--tone-info);
  font-size: 14px;
  font-weight: 900;
  line-height: 1;
  box-shadow: 0 8px 20px color-mix(in srgb, var(--blue) 12%, transparent);
}

.release-notice-trigger:focus-visible {
  outline: none;
  border-color: var(--blue);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--blue-soft) 88%, white);
}

.release-notice-popover {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  z-index: 30;
  width: min(360px, calc(100vw - 40px));
  padding: 12px 14px;
  border: 1px solid color-mix(in srgb, var(--blue) 16%, var(--line));
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 18px 40px rgba(34, 49, 74, 0.16);
  opacity: 0;
  pointer-events: none;
  transform: translateY(-4px);
  transition: opacity 140ms ease, transform 140ms ease;
}

.release-notice-anchor:hover .release-notice-popover,
.release-notice-anchor:focus-within .release-notice-popover {
  opacity: 1;
  pointer-events: auto;
  transform: translateY(0);
}

.release-notice-head {
  display: grid;
  gap: 2px;
  margin-bottom: 8px;
}

.release-notice-version {
  color: var(--blue);
  font-size: 11px;
  font-weight: 800;
}

.release-notice-head strong {
  color: #22314a;
  font-size: 14px;
}

.release-notice-popover p {
  margin: 0 0 8px;
  color: #5d6d89;
  font-size: 12px;
  line-height: 1.6;
}

.release-notice-popover ul {
  margin: 0;
  padding-left: 18px;
  color: #22314a;
  display: grid;
  gap: 6px;
  font-size: 12px;
  line-height: 1.6;
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
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
}

.query-field input {
  width: 100%;
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  min-height: 44px;
  padding: 9px 46px 9px 12px;
  background: #fff;
  font: inherit;
}

.query-field input:focus {
  outline: none;
  border-color: var(--blue);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--blue-soft) 88%, white);
}

.query-submit-btn {
  border: 1px solid #2f6ee5;
  border-radius: 12px;
  background: linear-gradient(180deg, #4b89ff 0%, #2f6ee5 100%);
  color: #fff;
  min-height: 44px;
  padding: 0 18px;
  font: inherit;
  font-weight: 800;
  white-space: nowrap;
}

.query-clear-btn {
  position: absolute;
  top: 50%;
  right: 98px;
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
  .hero-head {
    align-items: flex-start;
  }

  .search-toolbar {
    grid-template-columns: 1fr;
  }

  .query-input-shell {
    grid-template-columns: 1fr;
  }

  .query-clear-btn {
    right: 8px;
  }

  .query-submit-btn {
    width: 100%;
  }
}
</style>
