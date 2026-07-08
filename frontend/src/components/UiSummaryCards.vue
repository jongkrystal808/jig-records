<script setup lang="ts">
import { computed } from "vue";

type SummaryCardTone = "normal" | "success" | "warn" | "danger" | "muted";

type SummaryCard = {
  label: string;
  value: number | string;
  meta?: string;
  tone?: SummaryCardTone | string;
  emphasis?: boolean;
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

// Centralize summary-card rendering so pages only maintain data, not duplicate layout/CSS.
const gridStyle = computed(() => ({
  "--summary-columns-desktop": `repeat(${props.desktopColumns}, minmax(0, 1fr))`,
  "--summary-columns-tablet": `repeat(${props.tabletColumns}, minmax(0, 1fr))`,
  "--summary-columns-mobile": `repeat(${props.mobileColumns}, minmax(0, 1fr))`
}));
</script>

<template>
  <section class="ui-summary-cards" :class="variant" :style="gridStyle">
    <article v-for="card in cards" :key="card.label" class="summary-card" :class="[card.tone ?? 'normal', { emphasis: card.emphasis }]">
      <span>{{ card.label }}</span>
      <strong>{{ card.value }}</strong>
      <p v-if="card.meta">{{ card.meta }}</p>
    </article>
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
