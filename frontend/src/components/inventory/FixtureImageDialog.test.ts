// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchFixtureImageObjectUrl } from "@/api";
import FixtureImageDialog from "./FixtureImageDialog.vue";

vi.mock("@/api", () => ({ fetchFixtureImageObjectUrl: vi.fn() }));

afterEach(() => {
  document.body.innerHTML = "";
  vi.restoreAllMocks();
});

describe("FixtureImageDialog", () => {
  it("owns authenticated image loading and releases the object URL when closed", async () => {
    vi.mocked(fetchFixtureImageObjectUrl).mockResolvedValue("blob:fixture-image");
    const revokeObjectURL = vi.fn();
    Object.defineProperty(URL, "revokeObjectURL", {
      value: revokeObjectURL,
      configurable: true
    });
    const wrapper = mount(FixtureImageDialog, {
      attachTo: document.body,
      props: {
        open: true,
        fixtureCode: "FX-001",
        fixtureName: "測試治具",
        customerId: 3
      }
    });
    await flushPromises();

    expect(fetchFixtureImageObjectUrl).toHaveBeenCalledWith("FX-001", 3);
    expect(document.body.querySelector("img")?.getAttribute("src")).toBe("blob:fixture-image");

    await wrapper.setProps({ open: false });
    await flushPromises();
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:fixture-image");
    wrapper.unmount();
  });
});
