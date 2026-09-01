// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

const { changeOwnPassword } = vi.hoisted(() => ({
  changeOwnPassword: vi.fn().mockResolvedValue(undefined)
}));
vi.mock("@/api", () => ({ api: { changeOwnPassword } }));
vi.mock("@/toastState", () => ({ pushToast: vi.fn() }));

import OwnPasswordChangeModal from "./OwnPasswordChangeModal.vue";

afterEach(() => {
  document.body.innerHTML = "";
  changeOwnPassword.mockClear();
});

describe("OwnPasswordChangeModal", () => {
  it("submits the current and confirmed new password", async () => {
    const wrapper = mount(OwnPasswordChangeModal, {
      attachTo: document.body,
      props: { open: true },
      global: { stubs: { Teleport: true } }
    });
    const inputs = wrapper.findAll("input");
    await inputs[0].setValue("old-secret");
    await inputs[1].setValue("new-secret");
    await inputs[2].setValue("new-secret");
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(changeOwnPassword).toHaveBeenCalledWith("old-secret", "new-secret");
    expect(wrapper.emitted("close")).toHaveLength(1);
    wrapper.unmount();
  });
});
