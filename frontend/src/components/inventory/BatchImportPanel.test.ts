// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "@/api";
import BatchImportPanel from "./BatchImportPanel.vue";

vi.mock("@/api", () => ({
  api: {
    listFixtures: vi.fn(),
    listStock: vi.fn(),
    listIdentifierStockSummary: vi.fn(),
    createReceiptWithOptions: vi.fn(),
    createReturnWithOptions: vi.fn()
  }
}));

vi.mock("@/toastState", () => ({ pushToast: vi.fn() }));

const fixture = {
  id: 7,
  customer_id: 1,
  responsible_user_id: null,
  code: "FX-007",
  name: "測試治具",
  line_storage_location: null,
  department_storage_location: null,
  min_stock_qty: 0,
  description: null,
  is_active: true,
  has_image: false
};

afterEach(() => {
  window.sessionStorage.clear();
  vi.clearAllMocks();
});

describe("BatchImportPanel spreadsheet grid", () => {
  it("enters a row directly in the grid and submits it through the batch API", async () => {
    vi.mocked(api.listFixtures).mockResolvedValue([fixture]);
    vi.mocked(api.listStock).mockResolvedValue([
      {
        fixture_id: fixture.id,
        fixture_code: fixture.code,
        fixture_name: fixture.name,
        stock_qty: 3,
        customer_supplied_qty: 3,
        self_purchased_qty: 0,
        min_stock_qty: 0,
        stock_status: "normal",
        last_transaction_at: null
      }
    ]);
    vi.mocked(api.listIdentifierStockSummary).mockResolvedValue([]);
    vi.mocked(api.createReceiptWithOptions).mockResolvedValue(undefined);

    const wrapper = mount(BatchImportPanel, {
      props: {
        customerId: 1,
        hideFrame: true
      }
    });
    await flushPromises();

    expect(wrapper.get("#batch-grid-title").text()).toBe("收退料報表編輯區");
    const tableHead = wrapper.get(".batch-entry-grid thead");
    expect(tableHead.text()).toContain("收／退料");
    expect(tableHead.text()).toContain("單號");
    expect(tableHead.text()).toContain("來源");
    expect(tableHead.text()).toContain("備註");
    expect(tableHead.find(".batch-head").exists()).toBe(false);
    expect(tableHead.find('[data-tour="detailed-inventory-meta"]').exists()).toBe(false);
    expect(wrapper.find("textarea").exists()).toBe(false);
    expect(wrapper.findAll("datalist option").map((option) => option.attributes("value"))).toEqual([
      "FX-007"
    ]);

    const modeFields = wrapper.findAll<HTMLSelectElement>('[data-grid-column="mode"]');
    await modeFields[0].setValue("return");
    expect(modeFields[1].element.value).toBe("return");
    await modeFields[0].setValue("receipt");

    await wrapper.findAll<HTMLInputElement>('[data-grid-column="fixtureCode"]')[0].setValue("fx-007");
    await wrapper.findAll<HTMLInputElement>('[data-grid-column="identifier"]')[0].setValue("7");
    await wrapper.findAll<HTMLInputElement>('[data-grid-column="quantity"]')[0].setValue("2");
    await wrapper.findAll<HTMLSelectElement>('[data-grid-column="ownershipType"]')[0].setValue("self_purchased");
    await wrapper.findAll<HTMLInputElement>('[data-grid-column="note"]')[0].setValue("第一列備註");
    await flushPromises();

    expect(wrapper.text()).toContain("可直接送出 1 筆");
    expect(wrapper.findAll("button").some((button) => button.text().includes("匯出篩選結果") && !button.attributes("disabled"))).toBe(true);

    await wrapper.findAll<HTMLInputElement>('[data-grid-column="transactionNo"]')[0].setValue("RCV-QUICK-001");
    expect(wrapper.findAll<HTMLInputElement>('[data-grid-column="transactionNo"]')[1].element.value).toBe("RCV-QUICK-001");
    await wrapper.get("button[data-tour='inventory-submit-action']").trigger("click");
    await flushPromises();

    expect(api.createReceiptWithOptions).toHaveBeenCalledWith(
      expect.objectContaining({
        customer_id: 1,
        transaction_no: "RCV-QUICK-001",
        items: [
          {
            fixture_id: 7,
            ownership_type: "self_purchased",
            identifier: "0007",
            quantity: 2,
            note: "第一列備註"
          }
        ]
      }),
      { confirmDuplicate: false }
    );

    wrapper.unmount();
  });

  it("pastes an Excel-style range into the selected grid cell", async () => {
    vi.mocked(api.listFixtures).mockResolvedValue([fixture]);
    vi.mocked(api.listStock).mockResolvedValue([]);
    vi.mocked(api.listIdentifierStockSummary).mockResolvedValue([]);
    const wrapper = mount(BatchImportPanel, {
      props: { customerId: 1 }
    });
    await flushPromises();

    await wrapper.findAll<HTMLInputElement>('[data-grid-column="fixtureCode"]')[0].trigger("paste", {
      clipboardData: {
        getData: () => "FX-007\t7\t2\t接頭鬆脫\nFX-007\t8\t3\t電氣不穩定"
      }
    });
    await flushPromises();

    expect(wrapper.findAll<HTMLInputElement>('[data-grid-column="fixtureCode"]')[1].element.value).toBe("FX-007");
    expect(wrapper.findAll<HTMLInputElement>('[data-grid-column="identifier"]')[1].element.value).toBe("8");
    expect(wrapper.findAll<HTMLInputElement>('[data-grid-column="quantity"]')[1].element.value).toBe("3");
    expect(wrapper.findAll<HTMLInputElement>('[data-grid-column="note"]')[0].element.value).toBe("接頭鬆脫");
    expect(wrapper.findAll<HTMLInputElement>('[data-grid-column="note"]')[1].element.value).toBe("電氣不穩定");
    expect(wrapper.text()).toContain("可直接送出 2 筆");

    wrapper.unmount();
  });

  it("applies selected columns to all rows and separates unchecked transaction numbers", async () => {
    vi.mocked(api.listFixtures).mockResolvedValue([fixture]);
    vi.mocked(api.listStock).mockResolvedValue([]);
    vi.mocked(api.listIdentifierStockSummary).mockResolvedValue([]);
    vi.mocked(api.createReceiptWithOptions).mockResolvedValue(undefined);

    const wrapper = mount(BatchImportPanel, { props: { customerId: 1 } });
    await flushPromises();

    const applyAll = wrapper.findAll<HTMLInputElement>('.apply-all-control input[type="checkbox"]');
    expect(applyAll.map((checkbox) => checkbox.element.checked)).toEqual([true, true, false]);

    await wrapper.findAll<HTMLInputElement>('[data-grid-column="transactionNo"]')[0].setValue("RCV-A");
    await applyAll[1].setValue(false);
    await wrapper.findAll<HTMLInputElement>('[data-grid-column="transactionNo"]')[1].setValue("RCV-B");

    await applyAll[2].setValue(true);
    await wrapper.findAll<HTMLSelectElement>('[data-grid-column="ownershipType"]')[0].setValue("self_purchased");
    expect(wrapper.findAll<HTMLSelectElement>('[data-grid-column="ownershipType"]')[1].element.value).toBe("self_purchased");

    const fixtureFields = wrapper.findAll<HTMLInputElement>('[data-grid-column="fixtureCode"]');
    const identifierFields = wrapper.findAll<HTMLInputElement>('[data-grid-column="identifier"]');
    await fixtureFields[0].setValue("FX-007");
    await identifierFields[0].setValue("7");
    await fixtureFields[1].setValue("FX-007");
    await identifierFields[1].setValue("8");
    await flushPromises();

    await wrapper.get("button[data-tour='inventory-submit-action']").trigger("click");
    await flushPromises();

    expect(api.createReceiptWithOptions).toHaveBeenCalledTimes(2);
    expect(vi.mocked(api.createReceiptWithOptions).mock.calls.map(([payload]) => payload.transaction_no)).toEqual(["RCV-A", "RCV-B"]);
    expect(
      vi.mocked(api.createReceiptWithOptions).mock.calls.flatMap(([payload]) => payload.items.map((item) => item.ownership_type))
    ).toEqual(["self_purchased", "self_purchased"]);

    wrapper.unmount();
  });
});
