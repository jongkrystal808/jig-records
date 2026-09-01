// @vitest-environment jsdom

import { defineComponent, ref } from "vue";
import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "@/api";
import { useMasterQuality } from "./useMasterQuality";
import type { Fixture } from "@/types";

vi.mock("@/api", () => ({ api: {}, fetchFixtureImageObjectUrl: vi.fn() }));
vi.mock("@/toastState", () => ({ pushToast: vi.fn() }));

afterEach(() => vi.clearAllMocks());

describe("useMasterQuality", () => {
  it("keeps inline quality repair customer-scoped and reloads the report", async () => {
    const fixture: Fixture = {
      id: 11,
      customer_id: 3,
      code: "FX-011",
      name: "治具十一",
      responsible_user_id: null,
      line_storage_location: null,
      department_storage_location: null,
      min_stock_qty: 0,
      description: null,
      is_active: true,
      has_image: false,
      created_at: "2026-08-04",
      updated_at: "2026-08-04"
    };
    const updateFixture = vi.fn().mockResolvedValue(fixture);
    Object.assign(api, { updateFixture });
    const reloadData = vi.fn().mockResolvedValue(undefined);
    const host = defineComponent({
      setup() {
        return useMasterQuality({
          fixtures: ref([fixture]),
          models: ref([]),
          stations: ref([]),
          selectedCustomerId: ref(3),
          reloadData,
          openRequirements: vi.fn().mockResolvedValue(undefined),
          openLedger: vi.fn().mockResolvedValue(undefined)
        });
      },
      template: "<div />"
    });
    const wrapper = mount(host);

    await (wrapper.vm as any).saveInlineQualityIssue(11, "LINE-A", "DEPT-B", 4);
    expect(updateFixture).toHaveBeenCalledWith(
      11,
      expect.objectContaining({
        customer_id: 3,
        line_storage_location: "LINE-A",
        department_storage_location: "DEPT-B",
        min_stock_qty: 4
      })
    );
    expect(reloadData).toHaveBeenCalledOnce();
    wrapper.unmount();
  });
});
