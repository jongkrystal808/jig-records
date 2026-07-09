import { ref } from "vue";

import type { OnboardingFlowId } from "@/onboarding";
import type { AuthSession, Customer } from "@/types";

export const authSession = ref<AuthSession | null>(null);
export const customers = ref<Customer[]>([]);
export const selectedCustomerId = ref<number | null>(null);
export const globalFixtureKeyword = ref("");
export const pendingAutoTour = ref(false);
export const onboardingPickerOpen = ref(false);
export const onboardingActive = ref(false);
export const onboardingFlowId = ref<OnboardingFlowId | null>(null);
export const onboardingStepIndex = ref(0);
export const onboardingSandboxMode = ref(false);

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
}
