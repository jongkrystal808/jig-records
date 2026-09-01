import { describe, expect, it } from "vitest";

import { canManageAccounts, canManageAdminReports, canOperate, roleLabel } from "./roles";

describe("role capabilities", () => {
  it("keeps daily operations available to every signed-in role", () => {
    expect(["super_admin", "admin", "user"].every(canOperate)).toBe(true);
    expect(canOperate("guest")).toBe(false);
  });

  it("separates account management from ledger and quality management", () => {
    expect(canManageAdminReports("super_admin")).toBe(true);
    expect(canManageAdminReports("admin")).toBe(true);
    expect(canManageAdminReports("user")).toBe(false);
    expect(canManageAccounts("super_admin")).toBe(true);
    expect(canManageAccounts("admin")).toBe(false);
  });

  it("labels the new role", () => {
    expect(roleLabel("super_admin")).toBe("超級管理員");
  });
});
