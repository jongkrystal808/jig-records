import { describe, expect, it } from "vitest";

import { getOnboardingFlow, onboardingFlows } from "@/onboarding";

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

  it("provides a complete detailed guide with all major button groups", () => {
    const flow = getOnboardingFlow("system-detailed-guide");
    const stepIds = new Set(flow?.steps.map((step) => step.id));

    expect(flow?.requiresInventoryAccess).toBe(true);
    expect(flow?.requiresMasterAccess).toBe(true);
    for (const stepId of [
      "detailed-primary-actions",
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
});
