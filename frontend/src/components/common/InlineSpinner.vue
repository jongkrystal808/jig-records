<script setup lang="ts">
defineProps<{
  label?: string;
}>();
</script>

<template>
  <span class="inline-spinner" role="status" aria-live="polite">
    <span class="inline-spinner-dot" aria-hidden="true"></span>
    <span>{{ label ?? "載入中..." }}</span>
  </span>
</template>

<style scoped>
.inline-spinner {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #5d6d89;
  font-size: 12px;
  font-weight: 700;
}

.inline-spinner-dot {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(47, 110, 229, 0.18);
  border-top-color: #2f6ee5;
  border-radius: 999px;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
