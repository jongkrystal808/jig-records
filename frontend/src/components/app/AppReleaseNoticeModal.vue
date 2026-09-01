<script setup lang="ts">
import UiModalShell from "@/components/common/UiModalShell.vue";

defineProps<{
  open: boolean;
  versionLabel: string;
  title: string;
  summary: string;
  highlights: string[];
}>();

const emit = defineEmits<{
  close: [];
}>();

// Keep release-note presentation isolated so App.vue only decides when the notice should appear.
</script>

<template>
  <UiModalShell
    :open="open"
    labelled-by="release-notice-title"
    described-by="release-notice-summary"
    layer-class="release-modal-backdrop"
    dialog-class="ui-modal-card--narrow release-modal-card"
    @close="emit('close')"
  >
        <div class="release-head">
          <div>
            <span class="release-eyebrow">Release Note</span>
            <h2 id="release-notice-title">{{ title }}</h2>
            <p id="release-notice-summary">{{ summary }}</p>
          </div>
          <span class="release-version">{{ versionLabel }}</span>
        </div>

        <ul class="release-list">
          <li v-for="item in highlights" :key="item">{{ item }}</li>
        </ul>

        <div class="release-actions">
          <button class="primary-btn" type="button" data-modal-initial-focus @click="emit('close')">知道了</button>
        </div>
  </UiModalShell>
</template>

<style scoped>
:global(.release-modal-backdrop) {
  z-index: 140;
}

:global(.release-modal-card) {
  display: grid;
  gap: 16px;
}

.release-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.release-eyebrow {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--blue-soft) 84%, white);
  color: var(--tone-info);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.release-head h2 {
  margin: 8px 0 0;
  color: #22314a;
}

.release-head p {
  margin: 6px 0 0;
  color: #5d6d89;
  font-size: 12px;
  line-height: 1.6;
}

.release-version {
  color: #5d6d89;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.release-list {
  display: grid;
  gap: 8px;
  margin: 0;
  padding-left: 18px;
  color: #22314a;
}

.release-list li {
  line-height: 1.6;
}

.release-actions {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 720px) {
  .release-head {
    flex-direction: column;
  }

  .release-version {
    white-space: normal;
  }
}
</style>
