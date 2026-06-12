<script setup lang="ts">
withDefaults(
  defineProps<{
    label: string;
    tone?: "active" | "inactive" | "normal" | "warn" | "danger" | "muted";
  }>(),
  {
    tone: "muted"
  }
);
</script>

<template>
  <span class="ui-status-pill" :class="tone">{{ label }}</span>
</template>

<style scoped>
.ui-status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 64px;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.ui-status-pill.active,
.ui-status-pill.normal {
  color: var(--green);
  background: var(--green-soft);
}

.ui-status-pill.warn {
  color: var(--orange);
  background: var(--orange-soft);
}

.ui-status-pill.danger,
.ui-status-pill.inactive {
  color: var(--red);
  background: var(--red-soft);
}

.ui-status-pill.muted {
  color: #66748d;
  background: #edf1f7;
}
</style>
