// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";

import SystemConfirmDialog from "./SystemConfirmDialog.vue";

afterEach(() => {
  document.body.innerHTML = "";
});

describe("SystemConfirmDialog", () => {
  it("renders an accessible alert dialog and focuses cancel", async () => {
    const wrapper = mount(SystemConfirmDialog, {
      attachTo: document.body,
      props: {
        open: true,
        title: "刪除資料？",
        message: "此動作不可復原。",
        confirmLabel: "刪除",
        cancelLabel: "取消",
        tone: "danger"
      }
    });

    await wrapper.vm.$nextTick();

    const dialog = document.body.querySelector('[role="alertdialog"]');
    const cancel = document.body.querySelector<HTMLButtonElement>(".cancel-button");
    expect(dialog?.getAttribute("aria-modal")).toBe("true");
    expect(document.activeElement).toBe(cancel);

    cancel?.click();
    expect(wrapper.emitted("cancel")).toHaveLength(1);
    wrapper.unmount();
  });
});
