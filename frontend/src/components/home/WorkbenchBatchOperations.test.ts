// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import WorkbenchBatchOperations from "./WorkbenchBatchOperations.vue";

describe("WorkbenchBatchOperations", () => {
  it("wraps the shared batch logic in a Workbench-native workflow", () => {
    const wrapper = mount(WorkbenchBatchOperations, {
      props: { customerId: 7, initialMode: "return", presetFixtureCode: "FX-007" },
      global: {
        stubs: {
          BatchImportPanel: {
            props: ["customerId", "initialMode", "presetFixtureCode", "showModeSwitch", "hideFrame"],
            template: '<div data-testid="batch-core" :data-mode="initialMode" :data-fixture="presetFixtureCode" :data-mixed="showModeSwitch" :data-frameless="hideFrame" />'
          }
        }
      }
    });

    expect(wrapper.attributes("data-workbench-component")).toBe("batch-operations");
    expect(wrapper.text()).toContain("批次收退料工作區");
    expect(wrapper.text()).toContain("輸入或貼上");
    expect(wrapper.get('[data-testid="batch-core"]').attributes()).toMatchObject({
      "data-mode": "return",
      "data-fixture": "FX-007",
      "data-mixed": "true",
      "data-frameless": "true"
    });
  });
});
