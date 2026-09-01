// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "@/api";
import UiModalShell from "@/components/common/UiModalShell.vue";
import FormProductionPasteImport from "@/components/home/FormProductionPasteImport.vue";
import { confirmationState, settleConfirmation } from "@/confirmState";
import { toasts } from "@/toastState";

async function paste(wrapper: ReturnType<typeof mount>, value: string): Promise<void> {
  await wrapper.get("textarea").setValue(value);
  await flushPromises();
}

afterEach(() => {
  vi.restoreAllMocks();
  document.body.innerHTML = "";
  toasts.value = [];
});

describe("FormProductionPasteImport", () => {
  it("uses the shared modal shell for focus, Escape, and focus restoration", async () => {
    const trigger = document.createElement("button");
    trigger.textContent = "開啟產能貼上";
    document.body.append(trigger);
    trigger.focus();

    const wrapper = mount(FormProductionPasteImport, {
      attachTo: document.body,
      props: { open: true, view: "mappings", customerId: 9 }
    });
    await flushPromises();

    expect(wrapper.findComponent(UiModalShell).exists()).toBe(true);
    expect(document.activeElement).toBe(document.body.querySelector(".form-paste-box"));
    expect(trigger.hasAttribute("inert")).toBe(true);

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    expect(wrapper.emitted("close")).toHaveLength(1);

    await wrapper.setProps({ open: false });
    await flushPromises();
    expect(trigger.hasAttribute("inert")).toBe(false);
    expect(document.activeElement).toBe(trigger);
    wrapper.unmount();
  });

  it("previews and imports two-column model-station paste data", async () => {
    vi.spyOn(api, "previewModelStationsCsv").mockResolvedValue({
      rows: [
        { line: 2, model_code: "MODEL-A", station_code: "ST-01", fixture_code: null, incoming_required_qty: null, existing_required_qty: null, status: "new", message: "將新增機種站點綁定" },
        { line: 3, model_code: "MODEL-A", station_code: "ST-02", fixture_code: null, incoming_required_qty: null, existing_required_qty: null, status: "new", message: "將新增機種站點綁定" }
      ],
      new_count: 2,
      unchanged_count: 0,
      conflict_count: 0,
      error_count: 0
    });
    const importRows = vi.spyOn(api, "importModelStationsCsv").mockResolvedValue({
      imported_count: 2,
      created_count: 2,
      updated_count: 0,
      skipped_count: 0
    });
    const wrapper = mount(FormProductionPasteImport, {
      props: { open: true, view: "mappings", customerId: 9 },
      global: { stubs: { teleport: true } }
    });

    await paste(wrapper, "MODEL-A\tST-01\nMODEL-A\tST-02");
    expect(wrapper.text()).toContain("可匯入 2");
    await wrapper.get(".form-paste-actions .primary-btn").trigger("click");
    await flushPromises();
    expect(wrapper.text()).toContain("差異預覽");
    expect(wrapper.text()).toContain("新增 2");
    expect(importRows).not.toHaveBeenCalled();

    await wrapper.get(".form-paste-actions .primary-btn").trigger("click");
    await flushPromises();

    expect(importRows).toHaveBeenCalledWith(
      9,
      "model_code,station_code\nMODEL-A,ST-01\nMODEL-A,ST-02",
      "form-paste-model-stations.csv",
      false
    );
    expect(wrapper.emitted("imported")).toHaveLength(1);
    expect(wrapper.emitted("close")).toHaveLength(1);
    wrapper.unmount();
  });

  it("validates four-column fixture requirements before importing", async () => {
    vi.spyOn(api, "previewFixtureRequirementsCsv").mockResolvedValue({
      rows: [{
        line: 2,
        model_code: "MODEL-A",
        station_code: "ST-01",
        fixture_code: "FIX-01",
        incoming_required_qty: 2,
        existing_required_qty: 1,
        status: "conflict",
        message: "每站需求量將由 1 取代為 2"
      }],
      new_count: 0,
      unchanged_count: 0,
      conflict_count: 1,
      error_count: 0
    });
    const importRows = vi.spyOn(api, "importFixtureRequirementsCsv").mockResolvedValue({
      imported_count: 1,
      created_count: 0,
      updated_count: 1,
      skipped_count: 0
    });
    const wrapper = mount(FormProductionPasteImport, {
      props: { open: true, view: "requirements", customerId: 9 },
      global: { stubs: { teleport: true } }
    });

    await paste(wrapper, "MODEL-A\tST-01\tFIX-01\t0");
    expect(wrapper.text()).toContain("每站需求量必須是大於 0 的整數");
    await wrapper.get(".form-paste-actions .primary-btn").trigger("click");
    expect(importRows).not.toHaveBeenCalled();

    await paste(wrapper, "MODEL-A\tST-01\tFIX-01\t2");
    await wrapper.get(".form-paste-actions .primary-btn").trigger("click");
    await flushPromises();
    expect(wrapper.text()).toContain("待取代 1");
    expect(wrapper.text()).toContain("每站需求量將由 1 取代為 2");
    expect(importRows).not.toHaveBeenCalled();

    await wrapper.get(".form-paste-actions .primary-btn").trigger("click");
    await flushPromises();
    expect(confirmationState.title).toBe("是否直接取代既有綁定？");
    expect(confirmationState.message).toContain("MODEL-A / ST-01 / FIX-01：1 → 2");
    settleConfirmation(true);
    await flushPromises();

    expect(importRows).toHaveBeenCalledWith(
      9,
      "model_code,station_code,fixture_code,required_qty\nMODEL-A,ST-01,FIX-01,2",
      "form-paste-fixture-requirements.csv",
      true
    );
    wrapper.unmount();
  });
});
