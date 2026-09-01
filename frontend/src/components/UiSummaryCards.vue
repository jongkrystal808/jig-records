<script setup lang="ts">
import { computed } from "vue";

type SummaryCardTone = "normal" | "success" | "warn" | "danger" | "muted";

type SummaryCard = {
  label: string;
  value: number | string;
  meta?: string;
  tone?: SummaryCardTone | string;
  emphasis?: boolean;
  action?: string;
  selected?: boolean;
  disabled?: boolean;
  ariaLabel?: string;
};

const props = withDefaults(
  defineProps<{
    cards: SummaryCard[];
    variant?: "default" | "compact";
    desktopColumns?: number;
    tabletColumns?: number;
    mobileColumns?: number;
  }>(),
  {
    variant: "default",
    desktopColumns: 4,
    tabletColumns: 2,
    mobileColumns: 1
  }
);

const emit = defineEmits<{
  action: [action: string];
}>();

// Centralize summary-card rendering so pages only maintain data, not duplicate layout/CSS.
const gridStyle = computed(() => ({
  "--summary-columns-desktop": `repeat(${props.desktopColumns}, minmax(0, 1fr))`,
  "--summary-columns-tablet": `repeat(${props.tabletColumns}, minmax(0, 1fr))`,
  "--summary-columns-mobile": `repeat(${props.mobileColumns}, minmax(0, 1fr))`
}));
</script>

<template>
  <section class="ui-summary-cards" :class="variant" :style="gridStyle">
    <component
      :is="card.action ? 'button' : 'article'"
      v-for="card in cards"
      :key="card.label"
      class="summary-card"
      :class="[
        card.tone ?? 'normal',
        {
          emphasis: card.emphasis,
          actionable: Boolean(card.action),
          selected: card.selected
        }
      ]"
      :type="card.action ? 'button' : undefined"
      :disabled="card.action ? card.disabled : undefined"
      :aria-label="card.action ? card.ariaLabel ?? card.label : undefined"
      :aria-pressed="card.action ? Boolean(card.selected) : undefined"
      @click="card.action && emit('action', card.action)"
    >
      <span>{{ card.label }}</span>
      <strong>{{ card.value }}</strong>
      <p v-if="card.meta">{{ card.meta }}</p>
    </component>
  </section>
</template>

<style scoped>
.ui-summary-cards {
  display: grid;
  grid-template-columns: var(--summary-columns-desktop);
  gap: 8px;
  min-width: 0;
}

.summary-card {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
  padding: 9px 10px;
  display: grid;
  gap: 4px;
  min-width: 0;
  color: inherit;
  font: inherit;
  text-align: left;
}

.summary-card.actionable {
  width: 100%;
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
}

.summary-card.actionable:hover:not(:disabled) {
  border-color: #8eb5ee;
  box-shadow: 0 6px 16px rgba(43, 99, 177, 0.12);
  transform: translateY(-1px);
}

.summary-card.actionable:focus-visible {
  outline: 3px solid rgba(55, 122, 226, 0.24);
  outline-offset: 2px;
}

.summary-card.actionable.selected {
  border-color: #4e89e7;
  background: #edf4ff;
  box-shadow: inset 3px 0 0 #4e89e7;
}

.summary-card.actionable:disabled {
  cursor: not-allowed;
  opacity: 0.52;
}

.summary-card span {
  color: var(--muted);
  font-size: 12px;
}

.summary-card strong {
  color: #22314a;
  font-size: 20px;
  line-height: 1.1;
}

.summary-card p {
  margin: 0;
  color: #5d6d89;
  font-size: 12px;
}

.ui-summary-cards.compact .summary-card {
  background: #f8fafe;
  padding: 10px 12px;
}

.ui-summary-cards.compact .summary-card span {
  font-weight: 700;
}

.ui-summary-cards.compact .summary-card strong {
  font-size: 18px;
}

.summary-card.emphasis {
  border-color: rgba(224, 142, 31, 0.2);
  background: linear-gradient(180deg, rgba(224, 142, 31, 0.08) 0%, rgba(224, 142, 31, 0.04) 100%);
}

.summary-card.success strong {
  color: var(--green);
}

.summary-card.warn strong {
  color: var(--orange);
}

.summary-card.danger strong {
  color: var(--red);
}

.summary-card.muted strong {
  color: #5d6d89;
}

@media (max-width: 1200px) {
  .ui-summary-cards {
    grid-template-columns: var(--summary-columns-tablet);
  }
}

@media (max-width: 640px) {
  .ui-summary-cards {
    grid-template-columns: var(--summary-columns-mobile);
  }

  .ui-summary-cards.compact .summary-card {
    min-height: 78px;
    padding: 9px 10px;
  }

  .ui-summary-cards.compact .summary-card span {
    font-size: 11px;
  }

  .ui-summary-cards.compact .summary-card strong {
    font-size: 17px;
  }
}
</style>
