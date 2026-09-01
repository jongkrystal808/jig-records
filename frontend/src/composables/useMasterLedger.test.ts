// @vitest-environment jsdom

import { defineComponent, ref } from "vue";
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "@/api";
import { requestConfirmation } from "@/confirmState";
import { useMasterLedger } from "./useMasterLedger";

vi.mock("@/api", () => ({ api: {} }));
vi.mock("@/confirmState", () => ({ requestConfirmation: vi.fn().mockResolvedValue(true) }));
vi.mock("@/toastState", () => ({ pushToast: vi.fn() }));

afterEach(() => vi.clearAllMocks());

describe("useMasterLedger", () => {
  it("loads a customer-scoped page and centralizes fixture filtering", async () => {
    const listTransactionLedgerPage = vi.fn().mockResolvedValue({
      items: [
        {
          id: 7,
          customer_id: 3,
          transaction_type: "receipt",
          transaction_no: "R-007",
          occurred_at: "2026-08-04",
          created_by: "admin",
          note: null,
          created_at: "2026-08-04",
          items: []
        }
      ],
      page: 1,
      page_size: 12,
      total: 1
    });
    Object.assign(api, { listTransactionLedgerPage });
    const customerId = ref<number | null>(3);
    const host = defineComponent({
      setup() {
        return useMasterLedger({
          selectedCustomerId: customerId,
          canManage: () => true,
          reloadData: vi.fn().mockResolvedValue(undefined)
        });
      },
      template: "<div />"
    });
    const wrapper = mount(host);

    await (wrapper.vm as any).loadLedgerPage();
    expect(listTransactionLedgerPage).toHaveBeenLastCalledWith(1, 12, 3, {
      transaction_type: undefined,
      transaction_no: undefined,
      created_by: undefined,
      fixture_code: undefined
    });
    expect((wrapper.vm as any).selectedLedgerTransactionId).toBe(7);

    (wrapper.vm as any).focusFixtureInLedger("FX-001");
    await flushPromises();
    expect((wrapper.vm as any).ledgerFixtureCodeFilter).toBe("FX-001");
    expect(listTransactionLedgerPage).toHaveBeenLastCalledWith(
      1,
      12,
      3,
      expect.objectContaining({ fixture_code: "FX-001" })
    );
    wrapper.unmount();
  });

  it("returns to the previous page before reloading after the last case is reversed", async () => {
    const transaction = {
      id: 7,
      customer_id: 3,
      transaction_type: "receipt" as const,
      transaction_no: "R-007",
      occurred_at: "2026-08-24",
      created_by: "admin",
      note: null,
      created_at: "2026-08-24",
      items: []
    };
    const reloadData = vi.fn().mockResolvedValue(undefined);
    const reverseTransaction = vi.fn().mockResolvedValue({ transaction_no: "R-007", item_count: 1 });
    Object.assign(api, { reverseTransaction });
    vi.mocked(requestConfirmation).mockResolvedValueOnce(true).mockResolvedValueOnce(false);
    const host = defineComponent({
      setup() {
        return useMasterLedger({
          selectedCustomerId: ref<number | null>(3),
          canManage: () => true,
          reloadData
        });
      },
      template: "<div />"
    });
    const wrapper = mount(host);
    (wrapper.vm as any).ledgerPage = 2;
    (wrapper.vm as any).ledgerTransactions = [transaction];
    (wrapper.vm as any).selectedLedgerTransactionId = transaction.id;

    await (wrapper.vm as any).reverseSelectedLedgerTransaction();

    expect(reverseTransaction).toHaveBeenCalledWith(7, 3);
    expect((wrapper.vm as any).ledgerPage).toBe(1);
    expect(reloadData).toHaveBeenCalledWith({ preserveListPage: true, focusSelectedLedgerRow: true });
    wrapper.unmount();
  });
});
