import { ref } from "vue";

import { requestConfirmation } from "@/confirmState";

export type UnsavedChangesContext = "customer" | "surface" | "route" | "logout";

export const unsavedChangesGuards = ref<Record<string, string>>({});

let routeNavigationBypassCount = 0;

export function setUnsavedChangesGuard(key: string, active: boolean, message: string): void {
  if (active) {
    unsavedChangesGuards.value = { ...unsavedChangesGuards.value, [key]: message };
    return;
  }
  if (!(key in unsavedChangesGuards.value)) return;
  const nextGuards = { ...unsavedChangesGuards.value };
  delete nextGuards[key];
  unsavedChangesGuards.value = nextGuards;
}

export function clearUnsavedChangesGuards(): void {
  unsavedChangesGuards.value = {};
  routeNavigationBypassCount = 0;
}

export function unsavedChangesMessages(): string[] {
  return [...new Set(Object.values(unsavedChangesGuards.value))];
}

export function hasUnsavedChanges(): boolean {
  return unsavedChangesMessages().length > 0;
}

const CONTEXT_COPY: Record<UnsavedChangesContext, { action: string; title: string; confirmLabel: string }> = {
  customer: { action: "切換客戶", title: "切換客戶？", confirmLabel: "切換並捨棄" },
  surface: { action: "切換系統介面", title: "切換系統介面？", confirmLabel: "切換並捨棄" },
  route: { action: "離開目前頁面", title: "離開目前頁面？", confirmLabel: "離開並捨棄" },
  logout: { action: "登出", title: "登出並捨棄草稿？", confirmLabel: "登出並捨棄" }
};

export async function confirmUnsavedChanges(
  context: UnsavedChangesContext,
  options: { title?: string } = {}
): Promise<boolean> {
  const messages = unsavedChangesMessages();
  if (messages.length === 0) return true;
  const copy = CONTEXT_COPY[context];
  return requestConfirmation(
    `${copy.action}後，以下未儲存內容會遺失：\n- ${messages.join("\n- ")}\n\n要繼續嗎？`,
    {
      title: options.title ?? copy.title,
      confirmLabel: copy.confirmLabel,
      tone: "danger"
    }
  );
}

export function allowNextRouteNavigation(): void {
  routeNavigationBypassCount += 1;
}

export function consumeRouteNavigationBypass(): boolean {
  if (routeNavigationBypassCount <= 0) return false;
  routeNavigationBypassCount -= 1;
  return true;
}

export function handleUnsavedChangesBeforeUnload(event: BeforeUnloadEvent): void {
  if (!hasUnsavedChanges()) return;
  event.preventDefault();
  event.returnValue = "";
}

export function installUnsavedChangesBeforeUnloadGuard(): () => void {
  window.addEventListener("beforeunload", handleUnsavedChangesBeforeUnload);
  return () => window.removeEventListener("beforeunload", handleUnsavedChangesBeforeUnload);
}
