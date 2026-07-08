<script setup lang="ts">
const props = defineProps<{
  title: string;
  description?: string;
}>();

// Keep panel heading structure in one place so page splits do not clone the same title/action markup.
</script>

<template>
  <div class="ui-section-header">
    <div class="ui-section-copy">
      <h2>{{ title }}</h2>
      <p v-if="description">{{ description }}</p>
      <slot />
    </div>
    <div v-if="$slots.actions" class="ui-section-actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<style scoped>
.ui-section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.ui-section-copy {
  min-width: 0;
}

.ui-section-copy h2 {
  margin: 0;
  color: #22314a;
  font-size: 15px;
}

.ui-section-copy p {
  margin: 3px 0 0;
  color: var(--muted);
  font-size: 12px;
}

.ui-section-actions {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  flex-wrap: wrap;
}

@media (max-width: 640px) {
  .ui-section-header {
    flex-direction: column;
  }

  .ui-section-actions {
    width: 100%;
  }
}
</style>
