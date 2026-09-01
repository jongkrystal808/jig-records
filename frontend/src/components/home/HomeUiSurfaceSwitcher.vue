<script setup lang="ts">
import type { HomeUiSurface } from "@/utils/uiSurface";

defineProps<{
  activeSurface: HomeUiSurface;
  preferredSurface: HomeUiSurface;
  isGuest: boolean;
  switching: boolean;
  compact?: boolean;
}>();

const emit = defineEmits<{
  select: [surface: HomeUiSurface];
  saveDefault: [surface: HomeUiSurface];
}>();

function updateDefaultSurface(event: Event): void {
  const value = (event.target as HTMLSelectElement).value;
  if (value === "form" || value === "workspace") {
    emit("saveDefault", value);
  }
}
</script>

<template>
  <section class="ui-surface-switcher" :class="{ compact }" aria-label="UI 介面" :aria-busy="switching">
    <div>
      <span class="surface-switcher-label">切換整個系統介面</span>
      <div
        class="home-mode-tabs"
        :class="{ 'is-form': activeSurface === 'form' }"
        data-tour="home-mode-switch"
        role="tablist"
        aria-label="切換 Workspace 或 Form UI"
      >
        <button
          type="button"
          role="tab"
          :aria-selected="activeSurface === 'workspace'"
          :class="{ active: activeSurface === 'workspace' }"
          :disabled="switching"
          @click="emit('select', 'workspace')"
        >
          <strong>Workspace UI</strong>
          <span>快速作業與完整管理</span>
        </button>
        <button
          type="button"
          role="tab"
          :aria-selected="activeSurface === 'form'"
          :class="{ active: activeSurface === 'form' }"
          :disabled="switching"
          @click="emit('select', 'form')"
        >
          <strong>Form UI</strong>
          <span>表格式操作與資料維護</span>
        </button>
      </div>
    </div>

    <div class="surface-switcher-side">
      <span class="shared-surface-note">套用到查詢、收退料、產能與資料維護</span>
      <div v-if="isGuest" class="home-mode-preference guest">
        <span>訪客預設</span>
        <strong>Workspace UI</strong>
      </div>
      <div v-else class="home-mode-preference">
        <label class="default-surface-field">
          <span>
            <span class="default-label-full">登入後預設</span>
            <span class="default-label-compact">預設</span>
          </span>
          <select
            :value="preferredSurface"
            :disabled="switching"
            aria-label="登入後預設介面"
            @change="updateDefaultSurface"
          >
            <option value="workspace">Workspace UI</option>
            <option value="form">Form UI</option>
          </select>
        </label>
      </div>
    </div>
  </section>
</template>

<style scoped>
.ui-surface-switcher {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 14px;
  padding: 12px clamp(12px, 2vw, 28px) 0;
}

.ui-surface-switcher.compact {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0;
}

.ui-surface-switcher.compact .surface-switcher-label,
.ui-surface-switcher.compact .home-mode-tabs button span {
  display: none;
}

.ui-surface-switcher.compact .surface-switcher-side {
  display: block;
}

.ui-surface-switcher.compact .shared-surface-note,
.ui-surface-switcher.compact .home-mode-preference.guest {
  display: none;
}

.ui-surface-switcher.compact .home-mode-tabs {
  grid-template-columns: repeat(2, minmax(96px, 1fr));
  border-radius: 999px;
  background: #edf3fb;
}

.ui-surface-switcher.compact .home-mode-tabs::before {
  border-radius: 999px;
}

.ui-surface-switcher.compact .home-mode-tabs button {
  display: block;
  min-height: 36px;
  padding: 5px 12px;
  border-radius: 999px;
  text-align: center;
  white-space: nowrap;
}

.ui-surface-switcher.compact .home-mode-tabs strong {
  font-size: 0.76rem;
}

.surface-switcher-label {
  display: block;
  margin: 0 0 5px 4px;
  color: #6a7890;
  font-size: 0.66rem;
  font-weight: 800;
  letter-spacing: 0.04em;
}

.home-mode-tabs {
  position: relative;
  display: inline-grid;
  grid-template-columns: repeat(2, minmax(150px, 1fr));
  gap: 4px;
  padding: 4px;
  border: 1px solid #c8d7ea;
  border-radius: 11px;
  background: #edf3fb;
  isolation: isolate;
}

.home-mode-tabs::before {
  content: "";
  position: absolute;
  z-index: 0;
  top: 4px;
  bottom: 4px;
  left: 4px;
  width: calc((100% - 12px) / 2);
  border: 1px solid #8db5ee;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 2px 7px rgba(40, 89, 148, 0.12);
  transform: translateX(0);
  transition: transform 240ms cubic-bezier(0.22, 1, 0.36, 1);
}

.home-mode-tabs.is-form::before {
  transform: translateX(calc(100% + 4px));
}

.home-mode-tabs button {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 1px;
  min-height: 46px;
  padding: 6px 16px;
  border: 1px solid transparent;
  border-radius: 8px;
  color: #61718a;
  background: transparent;
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition: color 180ms ease, transform 180ms ease;
}

.home-mode-tabs button:not(.active):not(:disabled):hover {
  color: #245c9f;
  background: rgba(255, 255, 255, 0.7);
}

.home-mode-tabs button.active {
  color: #235991;
}

.home-mode-tabs button:disabled {
  cursor: wait;
}

.home-mode-tabs button:focus-visible {
  outline: 3px solid rgba(47, 110, 229, 0.28);
  outline-offset: 1px;
}

.home-mode-tabs strong {
  font-size: 0.84rem;
}

.home-mode-tabs span {
  font-size: 0.67rem;
  font-weight: 650;
}

.surface-switcher-side {
  display: grid;
  justify-items: end;
  gap: 5px;
}

.shared-surface-note {
  color: #7a879c;
  font-size: 0.65rem;
  font-weight: 650;
}

.home-mode-preference {
  display: flex;
  align-items: center;
  gap: 9px;
  min-height: 34px;
  padding: 5px 7px 5px 11px;
  border: 1px solid #d2deed;
  border-radius: 9px;
  color: #61718a;
  background: #f8fafd;
  font-size: 0.7rem;
  font-weight: 700;
}

.home-mode-preference strong {
  color: #2b4f7d;
}

.default-surface-field {
  display: flex;
  align-items: center;
  gap: 7px;
}

.default-surface-field > span {
  white-space: nowrap;
}

.default-label-compact {
  display: none;
}

.default-surface-field select {
  min-height: 27px;
  padding: 4px 8px;
  border: 1px solid #8db5ee;
  border-radius: 6px;
  color: #245c9f;
  background: #fff;
  font: inherit;
  font-size: 0.68rem;
  font-weight: 800;
  cursor: pointer;
}

.default-surface-field select:hover:not(:disabled) {
  background: #edf5ff;
}

.default-surface-field select:focus-visible {
  outline: 3px solid rgba(47, 110, 229, 0.24);
  outline-offset: 1px;
}

.default-surface-field select:disabled {
  cursor: wait;
}

.home-mode-preference.guest {
  padding-right: 11px;
}

.ui-surface-switcher.compact .home-mode-preference {
  min-height: 36px;
  padding: 3px 5px 3px 8px;
  border-radius: 999px;
}

.ui-surface-switcher.compact .default-label-full {
  display: none;
}

.ui-surface-switcher.compact .default-label-compact {
  display: inline;
  font-size: 0.64rem;
}

.ui-surface-switcher.compact .default-surface-field {
  gap: 4px;
}

.ui-surface-switcher.compact .default-surface-field select {
  min-height: 28px;
  max-width: 86px;
  padding-inline: 6px;
  border-radius: 999px;
}

@media (prefers-reduced-motion: reduce) {
  .home-mode-tabs::before,
  .home-mode-tabs button {
    transition: none;
  }
}

@media (max-width: 680px) {
  .ui-surface-switcher {
    align-items: stretch;
    flex-direction: column;
    gap: 7px;
    padding: 9px 8px 0;
  }

  .home-mode-tabs {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    width: 100%;
  }

  .home-mode-tabs button {
    min-width: 0;
    padding-inline: 10px;
  }

  .surface-switcher-side {
    justify-items: stretch;
  }

  .shared-surface-note {
    padding-inline: 3px;
  }

  .home-mode-preference {
    justify-content: space-between;
  }

  .ui-surface-switcher.compact {
    align-items: center;
    flex-direction: row;
    padding: 0;
  }

  .ui-surface-switcher.compact .home-mode-tabs {
    grid-template-columns: repeat(2, minmax(84px, 1fr));
    width: auto;
  }

  .ui-surface-switcher.compact .home-mode-tabs button {
    min-height: 34px;
    padding-inline: 8px;
  }

  .ui-surface-switcher.compact .home-mode-tabs strong {
    font-size: 0.7rem;
  }
}
</style>
