import type { AppUser, AuthSession } from "@/types";

import { request } from "@/api/core";

export const authApi = {
  login(payload: { username: string; password: string }) {
    return request<AuthSession>("/auth/login", { method: "POST", body: JSON.stringify(payload) }, false);
  },
  guestEntry() {
    return request<AuthSession>("/auth/guest", { method: "POST" }, false);
  },
  listUsers() {
    return request<AppUser[]>("/auth/users");
  },
  createUser(payload: { username: string; email?: string | null; password: string; display_name: string; role: string; is_active: boolean; allowed_customer_ids: number[] }) {
    return request<AppUser>("/auth/users", { method: "POST", body: JSON.stringify(payload) });
  },
  updateUser(userId: number, payload: { email?: string | null; display_name: string; role: string; is_active: boolean; allowed_customer_ids: number[] }) {
    return request<AppUser>(`/auth/users/${userId}`, { method: "PUT", body: JSON.stringify(payload) });
  },
  resetUserPassword(userId: number, password: string) {
    return request<void>(`/auth/users/${userId}/reset-password`, { method: "POST", body: JSON.stringify({ password }) });
  }
};
