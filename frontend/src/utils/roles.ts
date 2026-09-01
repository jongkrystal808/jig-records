export type SignedInRole = "super_admin" | "admin" | "user";

export function canOperate(role: string | null | undefined): boolean {
  return role === "super_admin" || role === "admin" || role === "user";
}

export function canManageAdminReports(role: string | null | undefined): boolean {
  return role === "super_admin" || role === "admin";
}

export function canManageAccounts(role: string | null | undefined): boolean {
  return role === "super_admin";
}

export function roleLabel(role: string | null | undefined): string {
  if (role === "super_admin") return "超級管理員";
  if (role === "admin") return "管理員";
  if (role === "user") return "使用者";
  return "訪客";
}
