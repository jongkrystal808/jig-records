import { ref } from "vue";

import type { AuthSession, Customer } from "@/types";

export const authSession = ref<AuthSession | null>(null);
export const customers = ref<Customer[]>([]);
export const selectedCustomerId = ref<number | null>(null);

export function resetSession(): void {
  authSession.value = null;
  selectedCustomerId.value = null;
}
