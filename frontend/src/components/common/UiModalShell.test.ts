// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";

import UiModalShell from "./UiModalShell.vue";

afterEach(() => {
  document.body.innerHTML = "";
});

describe("UiModalShell", () => {
  it("applies dialog semantics, inerts the background, and restores focus", async () => {
    const trigger = document.createElement("button");
    trigger.textContent = "開啟";
    document.body.append(trigger);
    trigger.focus();

    const wrapper = mount(UiModalShell, {
      attachTo: document.body,
      props: {
        open: true,
        labelledBy: "modal-title"
      },
      slots: {
        default: `
          <h2 id="modal-title">測試視窗</h2>
          <button data-modal-initial-focus>關閉</button>
          <button>確認</button>
        `
      }
    });
    await wrapper.vm.$nextTick();

    const dialog = document.body.querySelector<HTMLElement>('[role="dialog"]');
    const initialFocus = dialog?.querySelector<HTMLElement>("[data-modal-initial-focus]");
    expect(dialog?.getAttribute("aria-modal")).toBe("true");
    expect(dialog?.getAttribute("aria-labelledby")).toBe("modal-title");
    expect(trigger.hasAttribute("inert")).toBe(true);
    expect(document.activeElement).toBe(initialFocus);

    await wrapper.setProps({ open: false });
    await wrapper.vm.$nextTick();
    expect(trigger.hasAttribute("inert")).toBe(false);
    expect(document.activeElement).toBe(trigger);
    wrapper.unmount();
  });

  it("traps Tab in the top modal and closes with Escape", async () => {
    const wrapper = mount(UiModalShell, {
      attachTo: document.body,
      props: {
        open: true,
        labelledBy: "keyboard-modal-title"
      },
      slots: {
        default: `
          <h2 id="keyboard-modal-title">鍵盤測試</h2>
          <button data-modal-initial-focus>第一個</button>
          <button class="last-control">最後一個</button>
        `
      }
    });
    await wrapper.vm.$nextTick();

    const first = document.body.querySelector<HTMLElement>("[data-modal-initial-focus]");
    const last = document.body.querySelector<HTMLElement>(".last-control");
    last?.focus();
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Tab", bubbles: true }));
    expect(document.activeElement).toBe(first);

    first?.focus();
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Tab", shiftKey: true, bubbles: true }));
    expect(document.activeElement).toBe(last);

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    expect(wrapper.emitted("close")).toHaveLength(1);
    wrapper.unmount();
  });

  it("lets only the last nested modal handle Escape", async () => {
    const lower = mount(UiModalShell, {
      attachTo: document.body,
      props: { open: true, labelledBy: "lower-title" },
      slots: { default: '<h2 id="lower-title">下層</h2><button>關閉下層</button>' }
    });
    const upper = mount(UiModalShell, {
      attachTo: document.body,
      props: { open: true, labelledBy: "upper-title", dialogRole: "alertdialog" },
      slots: { default: '<h2 id="upper-title">上層</h2><button data-modal-initial-focus>取消</button>' }
    });
    await upper.vm.$nextTick();

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));

    expect(upper.emitted("close")).toHaveLength(1);
    expect(lower.emitted("close")).toBeUndefined();
    upper.unmount();
    lower.unmount();
  });
});
