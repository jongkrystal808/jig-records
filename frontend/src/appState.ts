import { ref } from "vue";

import type { AuthSession, Customer } from "@/types";

export const authSession = ref<AuthSession | null>(null);
export const customers = ref<Customer[]>([]);
export const selectedCustomerId = ref<number | null>(null);
export const globalFixtureKeyword = ref("");
export const pendingAutoTour = ref(false);
export const onboardingActive = ref(false);
export const onboardingStepIndex = ref(0);
export const onboardingSandboxMode = ref(false);

export function resetSession(): void {
  authSession.value = null;
  selectedCustomerId.value = null;
  globalFixtureKeyword.value = "";
  pendingAutoTour.value = false;
  onboardingActive.value = false;
  onboardingStepIndex.value = 0;
  onboardingSandboxMode.value = false;
}
