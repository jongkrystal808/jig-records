import { reactive } from "vue";

export type ConfirmationTone = "default" | "danger";

export type ConfirmationOptions = {
  title?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: ConfirmationTone;
};

export const confirmationState = reactive({
  open: false,
  title: "請確認",
  message: "",
  confirmLabel: "確定",
  cancelLabel: "取消",
  tone: "default" as ConfirmationTone
});

let pendingResolver: ((confirmed: boolean) => void) | null = null;

export function requestConfirmation(
  message: string,
  options: ConfirmationOptions = {}
): Promise<boolean> {
  if (pendingResolver) {
    pendingResolver(false);
    pendingResolver = null;
  }
  Object.assign(confirmationState, {
    open: true,
    title: options.title ?? "請確認",
    message,
    confirmLabel: options.confirmLabel ?? "確定",
    cancelLabel: options.cancelLabel ?? "取消",
    tone: options.tone ?? "default"
  });
  return new Promise((resolve) => {
    pendingResolver = resolve;
  });
}

export function settleConfirmation(confirmed: boolean): void {
  confirmationState.open = false;
  const resolver = pendingResolver;
  pendingResolver = null;
  resolver?.(confirmed);
}
