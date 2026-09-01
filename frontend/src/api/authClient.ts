import type { AppUser, AuthSession, ModelShortcutPreference, PageResult } from "@/types";

import { request, requestBlob, setOptionalParam } from "@/api/core";

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
  listUsersPage(page = 1, pageSize = 50, keyword = "", statusFilter = "all") {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize), keyword, status_filter: statusFilter });
    return request<PageResult<AppUser>>(`/auth/users/page?${params.toString()}`);
  },
  exportFormUsersCsv(keyword = "", statusFilter: "all" | "active" | "inactive" = "all") {
    const params = new URLSearchParams();
    setOptionalParam(params, "keyword", keyword);
    setOptionalParam(params, "status_filter", statusFilter);
    return requestBlob(`/auth/users/form-export?${params.toString()}`);
  },
  createUser(payload: { username: string; email?: string | null; password: string; display_name: string; role: string; is_active: boolean; allowed_customer_ids: number[] }) {
    return request<AppUser>("/auth/users", { method: "POST", body: JSON.stringify(payload) });
  },
  updateUser(userId: number, payload: { email?: string | null; display_name: string; role: string; is_active: boolean; allowed_customer_ids?: number[] }) {
    return request<AppUser>(`/auth/users/${userId}`, { method: "PUT", body: JSON.stringify(payload) });
  },
  resetUserPassword(userId: number, password: string) {
    return request<void>(`/auth/users/${userId}/reset-password`, { method: "POST", body: JSON.stringify({ password }) });
  },
  changeOwnPassword(currentPassword: string, newPassword: string) {
    return request<void>("/auth/password", {
      method: "POST",
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
    });
  },
  listModelShortcutPreferences(customerId: number) {
    return request<ModelShortcutPreference[]>(`/auth/preferences/model-shortcuts?customer_id=${customerId}`);
  },
  recordModelShortcutQuery(customerId: number, modelId: number) {
    return request<ModelShortcutPreference>(
      `/auth/preferences/model-shortcuts/${modelId}/query?customer_id=${customerId}`,
      { method: "POST" }
    );
  },
  setModelShortcutPin(customerId: number, modelId: number, pinned: boolean) {
    return request<ModelShortcutPreference>(
      `/auth/preferences/model-shortcuts/${modelId}/pin?customer_id=${customerId}`,
      { method: "PUT", body: JSON.stringify({ pinned }) }
    );
  }
};
