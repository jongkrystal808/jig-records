<script setup lang="ts">
import type { ToastItem } from "@/toastState";

defineProps<{
  toasts: ToastItem[];
}>();

const emit = defineEmits<{
  dismiss: [toastId: number];
}>();

// Keep toast rendering out of App.vue so the shell page only coordinates global state.
</script>

<template>
  <section class="toast-stack" aria-live="polite">
    <article v-for="toast in toasts" :key="toast.id" class="toast-card" :class="toast.tone">
      <span>{{ toast.message }}</span>
      <button class="toast-close" type="button" @click="emit('dismiss', toast.id)">x</button>
    </article>
  </section>
</template>

<style scoped>
.toast-stack {
  position: fixed;
  top: 78px;
  right: 16px;
  z-index: 80;
  display: grid;
  gap: 8px;
  width: 320px;
}

.toast-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: var(--shadow);
  padding: 11px 12px;
  color: #20304f;
  font-size: 12px;
}

.toast-card.success {
  border-color: #b8e2cb;
  background: #f4fff8;
  color: #18643f;
}

.toast-card.error {
  border-color: #f1c3c3;
  background: #fff6f6;
  color: #a53636;
}

.toast-card.warning {
  border-color: #f3dbab;
  background: #fffaf0;
  color: #9d6706;
}

.toast-card.info {
  border-color: #c8daf7;
  background: #f5f9ff;
  color: #255ebd;
}

.toast-close {
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: inherit;
  font-weight: 700;
}

@media (max-width: 720px) {
  .toast-stack {
    left: 10px;
    right: 10px;
    width: auto;
    top: auto;
    bottom: 10px;
  }
}
</style>
