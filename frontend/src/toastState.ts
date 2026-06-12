import { ref } from "vue";

export type ToastTone = "success" | "error" | "warning" | "info";

export interface ToastItem {
  id: number;
  message: string;
  tone: ToastTone;
}

export const toasts = ref<ToastItem[]>([]);

let nextToastId = 1;

export function pushToast(message: string, tone: ToastTone = "info", durationMs = 3200): void {
  const id = nextToastId++;
  toasts.value = [...toasts.value, { id, message, tone }];
  window.setTimeout(() => dismissToast(id), durationMs);
}

export function dismissToast(id: number): void {
  toasts.value = toasts.value.filter((toast) => toast.id !== id);
}
