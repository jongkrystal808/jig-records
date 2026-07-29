import { ref } from "vue";

import type { OnboardingFlowId } from "@/onboarding";
import type { AuthSession, Customer } from "@/types";

const SESSION_KEY = "jig-record-session";
const CUSTOMER_KEY = "jig-record-customer-id";

function readPersistedSession(): AuthSession | null {
  if (typeof window === "undefined") {
    return null;
  }
  const raw = window.sessionStorage.getItem(SESSION_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as AuthSession;
  } catch {
    window.sessionStorage.removeItem(SESSION_KEY);
    return null;
  }
}

function readPersistedCustomerId(): number | null {
  if (typeof window === "undefined") {
    return null;
  }
  const raw = window.sessionStorage.getItem(CUSTOMER_KEY);
  if (!raw) {
    return null;
  }
  const parsed = Number(raw);
  if (!Number.isFinite(parsed)) {
    window.sessionStorage.removeItem(CUSTOMER_KEY);
    return null;
  }
  return parsed;
}

export const authSession = ref<AuthSession | null>(readPersistedSession());
export const customers = ref<Customer[]>([]);
export const selectedCustomerId = ref<number | null>(readPersistedCustomerId());
export const globalFixtureKeyword = ref("");
export const pendingAutoTour = ref(false);
export const onboardingPickerOpen = ref(false);
export const onboardingActive = ref(false);
export const onboardingFlowId = ref<OnboardingFlowId | null>(null);
export const onboardingStepIndex = ref(0);
export const onboardingSandboxMode = ref(false);
export const inventoryBatchShortcutFixtureCode = ref("");
export const inventoryBatchShortcutRequestId = ref(0);
export const customerSwitchGuards = ref<Record<string, string>>({});

export function requestInventoryBatchOpen(fixtureCode?: string): void {
  inventoryBatchShortcutFixtureCode.value = (fixtureCode ?? "").trim().toUpperCase();
  inventoryBatchShortcutRequestId.value += 1;
}

export function setCustomerSwitchGuard(key: string, active: boolean, message: string): void {
  if (active) {
    customerSwitchGuards.value = {
      ...customerSwitchGuards.value,
      [key]: message
    };
    return;
  }

  if (!(key in customerSwitchGuards.value)) {
    return;
  }

  const nextGuards = { ...customerSwitchGuards.value };
  delete nextGuards[key];
  customerSwitchGuards.value = nextGuards;
}

export function resetSession(): void {
  authSession.value = null;
  selectedCustomerId.value = null;
  globalFixtureKeyword.value = "";
  pendingAutoTour.value = false;
  onboardingPickerOpen.value = false;
  onboardingActive.value = false;
  onboardingFlowId.value = null;
  onboardingStepIndex.value = 0;
  onboardingSandboxMode.value = false;
  inventoryBatchShortcutFixtureCode.value = "";
  inventoryBatchShortcutRequestId.value = 0;
  customerSwitchGuards.value = {};
}
