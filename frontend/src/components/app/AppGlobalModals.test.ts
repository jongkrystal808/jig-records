// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";

import AppGlobalModals from "./AppGlobalModals.vue";

afterEach(() => {
  document.body.innerHTML = "";
});

describe("AppGlobalModals", () => {
  it("opens receipt/return as a labelled dialog and handles Escape", async () => {
    const wrapper = mount(AppGlobalModals, {
      attachTo: document.body,
      props: {
        batchModalOpen: true,
        exportModalOpen: false,
        passwordModalOpen: false,
        customerId: 1,
        batchPresetFixtureCode: "FX-001",
        batchPresetMode: "return"
      },
      global: {
        stubs: {
          BatchImportPanel: {
            props: ["initialMode", "presetFixtureCode"],
            template: '<div data-test="batch-preset">{{ initialMode }}｜{{ presetFixtureCode }}</div>'
          },
          ExportCenterPanel: { template: "<div>匯出內容</div>" }
        }
      }
    });
    await wrapper.vm.$nextTick();

    const dialog = document.body.querySelector<HTMLElement>('[role="dialog"]');
    expect(dialog?.getAttribute("aria-modal")).toBe("true");
    expect(dialog?.getAttribute("aria-labelledby")).toBe("global-batch-modal-title");
    expect(document.activeElement?.textContent).toBe("關閉");
    expect(document.body.querySelector('[data-test="batch-preset"]')?.textContent).toBe("return｜FX-001");

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    expect(wrapper.emitted("closeBatch")).toHaveLength(1);
    wrapper.unmount();
  });

  it("opens export as a labelled dialog", async () => {
    const wrapper = mount(AppGlobalModals, {
      attachTo: document.body,
      props: {
        batchModalOpen: false,
        exportModalOpen: true,
        passwordModalOpen: false,
        customerId: 1
      },
      global: {
        stubs: {
          BatchImportPanel: { template: "<div>批次內容</div>" },
          ExportCenterPanel: {
            template: '<section><h2 id="global-export-modal-title">統一匯出中心</h2><button data-modal-initial-focus>關閉</button></section>'
          }
        }
      }
    });
    await wrapper.vm.$nextTick();

    const dialog = document.body.querySelector<HTMLElement>('[role="dialog"]');
    expect(dialog?.getAttribute("aria-labelledby")).toBe("global-export-modal-title");
    expect(document.activeElement?.textContent).toBe("關閉");
    wrapper.unmount();
  });
});
