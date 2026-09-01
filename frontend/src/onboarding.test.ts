import { describe, expect, it } from "vitest";

import {
  getOnboardingFlow,
  onboardingFlows,
  onboardingSurfaceForFlow,
  onboardingVariantForFlow
} from "@/onboarding";

describe("onboarding flows", () => {
  it("keeps every flow and step id unique", () => {
    const flowIds = onboardingFlows.map((flow) => flow.id);
    const stepIds = onboardingFlows.flatMap((flow) => flow.steps.map((step) => step.id));

    expect(new Set(flowIds).size).toBe(flowIds.length);
    expect(new Set(stepIds).size).toBe(stepIds.length);
  });

  it("includes the inventory source selector in the concise workflow", () => {
    const flow = getOnboardingFlow("inventory-workflow");

    expect(flow?.steps.some((step) => step.id === "inventory-source")).toBe(true);
    expect(flow?.steps.find((step) => step.id === "overview-filters")?.description).toContain("客供／自購");
    expect(flow?.steps.find((step) => step.id === "inventory-export-filters")?.description).toContain("客供／自購");
  });

  it("provides a seven-step guest quick flow that covers both query and report modes", () => {
    const flow = getOnboardingFlow("guest-search-report");
    const modes = new Set(flow?.steps.map((step) => step.query?.home_mode).filter(Boolean));

    expect(flow?.guestOnly).toBe(true);
    expect(flow?.steps).toHaveLength(7);
    expect(modes).toEqual(new Set(["query", "report"]));
    expect(flow?.steps.some((step) => step.id === "guest-report-capacity")).toBe(true);
    expect(flow?.steps.some((step) => step.id === "guest-report-results")).toBe(true);
  });

  it("provides a dedicated report tutorial for signed-in users", () => {
    const flow = getOnboardingFlow("report-basics");
    const stepIds = new Set(flow?.steps.map((step) => step.id));

    expect(flow?.guestOnly).not.toBe(true);
    expect(flow?.steps).toHaveLength(7);
    expect(flow?.steps.every((step) => step.route === "/search")).toBe(true);
    expect(flow?.steps.every((step) => step.query?.home_mode === "report")).toBe(true);
    for (const stepId of [
      "report-filter-basics",
      "report-apply-filters",
      "report-capacity",
      "report-columns",
      "report-export",
      "report-results"
    ]) {
      expect(stepIds.has(stepId)).toBe(true);
    }
  });

  it("provides a complete guest-only readonly guide without protected routes", () => {
    const flow = getOnboardingFlow("guest-readonly-guide");
    const routes = flow?.steps.map((step) => step.route) ?? [];

    expect(flow?.guestOnly).toBe(true);
    expect(flow?.requiresInventoryAccess).not.toBe(true);
    expect(flow?.requiresMasterAccess).not.toBe(true);
    expect(flow?.requiresAdminAccess).not.toBe(true);
    expect(flow?.steps.length).toBeGreaterThan(7);
    expect(routes).toContain("/inventory/overview");
    expect(routes.some((route) => route === "/inventory" || route.startsWith("/master") || route.startsWith("/production"))).toBe(false);
    expect(flow?.steps.every((step) => step.route && step.target && step.title && step.description)).toBe(true);
  });

  it("provides a complete detailed guide with all major button groups", () => {
    const flow = getOnboardingFlow("system-detailed-guide");
    const stepIds = new Set(flow?.steps.map((step) => step.id));

    expect(flow?.requiresInventoryAccess).toBe(true);
    expect(flow?.requiresMasterAccess).toBe(true);
    for (const stepId of [
      "detailed-primary-actions",
      "detailed-report-mode",
      "detailed-report-filters",
      "detailed-report-apply",
      "detailed-report-columns",
      "detailed-report-export",
      "detailed-report-results",
      "detailed-export-dataset",
      "detailed-export-filters",
      "detailed-export-source",
      "detailed-export-actions",
      "detailed-status-actions",
      "detailed-search-controls",
      "detailed-inventory-actions",
      "detailed-overview-advanced",
      "detailed-overview-pager",
      "detailed-master-form-actions",
      "detailed-production-requirements"
    ]) {
      expect(stepIds.has(stepId)).toBe(true);
    }
    expect(flow?.steps.every((step) => step.route && step.target && step.title && step.description)).toBe(true);
  });

  it("keeps Modern UI and Form UI tutorials in separate concise and detailed groups", () => {
    const formGuestFlows = onboardingFlows.filter((flow) => flow.guestOnly && onboardingSurfaceForFlow(flow) === "form");
    const formSignedInFlows = onboardingFlows.filter((flow) => !flow.guestOnly && onboardingSurfaceForFlow(flow) === "form");
    const modernFlows = onboardingFlows.filter((flow) => onboardingSurfaceForFlow(flow) === "modern");

    expect(new Set(formGuestFlows.map(onboardingVariantForFlow))).toEqual(new Set(["concise", "detailed"]));
    expect(new Set(formSignedInFlows.map(onboardingVariantForFlow))).toEqual(new Set(["concise", "detailed"]));
    expect(new Set(modernFlows.map(onboardingVariantForFlow))).toEqual(new Set(["concise", "detailed"]));
    expect(formGuestFlows.concat(formSignedInFlows).every((flow) =>
      flow.steps.every((step) => step.query?.ui_surface === "form")
    )).toBe(true);
  });

  it("documents the Form UI customer access multi-select for Super Admin", () => {
    const flow = getOnboardingFlow("form-admin-user-access");
    const description = flow?.steps.map((step) => step.description).join(" ") ?? "";

    expect(flow?.requiresSuperAdminAccess).toBe(true);
    expect(onboardingSurfaceForFlow(flow!)).toBe("form");
    expect(description).toContain("逐筆勾選");
    expect(description).toContain("全選目前搜尋結果");
    expect(flow?.steps.some((step) => step.note?.text.includes("至少必須保留一個客戶"))).toBe(true);
  });

  it("walks through every Form UI workspace button and its destination page", () => {
    const flow = getOnboardingFlow("form-detailed-guide");
    const targets = new Set(flow?.steps.map((step) => step.target));
    const routes = new Set(flow?.steps.map((step) => step.route));

    for (const workspace of ["report", "import", "inventory-overview", "production", "master", "image", "ledger", "quality"]) {
      expect(targets.has(`[data-tour='form-workspace-${workspace}']`)).toBe(true);
    }
    for (const route of [
      "/search",
      "/inventory",
      "/inventory/overview",
      "/production/mapping",
      "/production/requirements",
      "/master/fixtures",
      "/master/images",
      "/master/ledger",
      "/master/quality"
    ]) {
      expect(routes.has(route)).toBe(true);
    }
    expect(new Set(flow?.steps.filter((step) => step.requiresAdminAccess).map((step) => step.id)))
      .toEqual(new Set([
        "form-detail-ledger-entry",
        "form-detail-ledger-page",
        "form-detail-quality-entry",
        "form-detail-quality-page"
      ]));
    expect(new Set(flow?.steps.filter((step) => step.requiresSuperAdminAccess).map((step) => step.id)))
      .toEqual(new Set([
        "form-detail-master-customers",
        "form-detail-master-users",
        "form-detail-master-user-scope"
      ]));
  });

  it("explains production station binding, fixture binding, capacity, and both paste formats", () => {
    const flow = getOnboardingFlow("form-detailed-guide");
    const productionSteps = flow?.steps.filter((step) => step.id.includes("production")) ?? [];
    const copy = productionSteps.map((step) => `${step.title} ${step.description}`).join(" ");

    expect(copy).toContain("把站點綁到機種");
    expect(copy).toContain("綁定站點所需治具");
    expect(copy).toContain("此治具可支援站數");
    expect(productionSteps.filter((step) => step.target === "[data-tour='form-production-paste-import']")).toHaveLength(2);
    expect(productionSteps.flatMap((step) => step.example ?? []).map((example) => example.value))
      .toEqual(expect.arrayContaining([
        "MODEL-A<TAB>STATION-01",
        "MODEL-A<TAB>STATION-01<TAB>FIXTURE-001<TAB>2"
      ]));
  });

  it("details Form report filtering, result controls, columns, images, export, and pagination", () => {
    const flow = getOnboardingFlow("form-detailed-guide");
    const reportSteps = flow?.steps.filter((step) => step.id.startsWith("form-detail-report-")) ?? [];
    const ids = new Set(reportSteps.map((step) => step.id));
    const copy = reportSteps.map((step) => `${step.title} ${step.description}`).join(" ");

    for (const id of [
      "form-detail-report-filters",
      "form-detail-report-linked-fields",
      "form-detail-report-transaction-filters",
      "form-detail-report-actions",
      "form-detail-report-summary",
      "form-detail-report-columns",
      "form-detail-report-results",
      "form-detail-report-export-pagination"
    ]) expect(ids.has(id)).toBe(true);
    expect(copy).toContain("最大開站數");
    expect(copy).toContain("治具代碼可開啟圖片預覽");
    expect(copy).toContain("XLSX 或 CSV");
  });

  it("details Form receipt-return entry, paste formats, preview resolution, and safe submission", () => {
    const flow = getOnboardingFlow("form-detailed-guide");
    const importSteps = flow?.steps.filter((step) => step.id.startsWith("form-detail-import")) ?? [];
    const ids = new Set(importSteps.map((step) => step.id));
    const examples = importSteps.flatMap((step) => step.example ?? []).map((example) => example.value);

    for (const id of [
      "form-detail-import-mode-transaction",
      "form-detail-import-fixture-ownership",
      "form-detail-import-identifier-quantity",
      "form-detail-import-grid",
      "form-detail-import-preview",
      "form-detail-import-actions"
    ]) expect(ids.has(id)).toBe(true);
    expect(importSteps.filter((step) => step.route === "/inventory").every((step) => step.sandboxMode)).toBe(true);
    expect(examples).toEqual(expect.arrayContaining([
      "FIXTURE-001<TAB>2608<TAB>5<TAB>首批入庫",
      "receipt<TAB>TX-001<TAB>FIXTURE-001<TAB>2608<TAB>5<TAB>customer_supplied<TAB>首批入庫"
    ]));
  });

  it("details every Form master table and keeps customer/user steps Super-Admin-only", () => {
    const flow = getOnboardingFlow("form-detailed-guide");
    const masterSteps = flow?.steps.filter((step) => step.id.startsWith("form-detail-master")) ?? [];
    const ids = new Set(masterSteps.map((step) => step.id));

    for (const id of [
      "form-detail-master-toolbar",
      "form-detail-master-fixtures",
      "form-detail-master-models",
      "form-detail-master-stations",
      "form-detail-master-customers",
      "form-detail-master-users",
      "form-detail-master-user-scope"
    ]) expect(ids.has(id)).toBe(true);
    expect(masterSteps.find((step) => step.id === "form-detail-master-customers")?.requiresSuperAdminAccess).toBe(true);
    expect(masterSteps.find((step) => step.id === "form-detail-master-users")?.requiresSuperAdminAccess).toBe(true);
    expect(masterSteps.find((step) => step.id === "form-detail-master-user-scope")?.requiresSuperAdminAccess).toBe(true);
  });
});
