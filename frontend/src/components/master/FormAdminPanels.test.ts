// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import FixtureQualityPanel from "./FixtureQualityPanel.vue";
import TransactionAccountDetailPanel from "./TransactionAccountDetailPanel.vue";
import TransactionAccountListPanel from "./TransactionAccountListPanel.vue";
import type { Fixture, FixtureQualityReport, MaterialTransaction } from "@/types";

const transaction: MaterialTransaction = {
  id: 41,
  customer_id: 7,
  transaction_type: "receipt",
  transaction_no: "REC-0041",
  occurred_at: "2026-08-11T08:30:00Z",
  created_by: "admin",
  note: "表單介面測試",
  created_at: "2026-08-11T08:30:00Z",
  items: [
    {
      fixture_id: 15,
      fixture_code: "FX-015",
      fixture_name: "測試治具",
      ownership_type: "self_purchased",
      identifier: "0831",
      quantity: 2,
      note: null
    }
  ]
};

const fixture: Fixture = {
  id: 15,
  customer_id: 7,
  responsible_user_id: null,
  code: "FX-015",
  name: "測試治具",
  line_storage_location: null,
  department_storage_location: null,
  min_stock_qty: 0,
  description: null,
  is_active: true,
  has_image: false
};

const qualityReport: FixtureQualityReport = {
  total_fixture_count: 1,
  problematic_fixture_count: 1,
  missing_name_count: 0,
  missing_storage_location_count: 1,
  missing_image_count: 1,
  missing_min_stock_qty_count: 1,
  missing_model_relation_count: 0,
  stock_mismatch_count: 0,
  rows: [
    {
      fixture_id: fixture.id,
      fixture_code: fixture.code,
      fixture_name: fixture.name,
      storage_location: null,
      min_stock_qty: 0,
      stock_qty: 2,
      identifier_stock_qty: 2,
      related_model_count: 1,
      has_image: false,
      issue_codes: ["missing_storage_location", "missing_min_stock_qty", "missing_image"]
    }
  ]
};

const ledgerCallbacks = {
  onTransactionNoChange: vi.fn(),
  onCreatedByChange: vi.fn(),
  onFixtureCodeChange: vi.fn(),
  onTransactionTypeChange: vi.fn(),
  onPageSizeChange: vi.fn(),
  onSelectRow: vi.fn(),
  onPreviousPage: vi.fn(),
  onNextPage: vi.fn()
};

describe("Form admin panels", () => {
  it("renders the ledger list and detail as flat Form UI records", async () => {
    const list = mount(TransactionAccountListPanel, {
      props: {
        rows: [transaction],
        selectedTransactionId: transaction.id,
        loading: false,
        transactionNo: "",
        createdBy: "",
        fixtureCode: "",
        transactionType: [],
        page: 1,
        pageSize: 12,
        totalPages: 1,
        total: 1,
        embeddedForm: true,
        ...ledgerCallbacks
      }
    });
    const detail = mount(TransactionAccountDetailPanel, {
      props: {
        transaction,
        processing: false,
        embeddedForm: true,
        onReload: vi.fn(),
        onRecalculate: vi.fn(),
        onReverse: vi.fn()
      }
    });

    expect(list.find(".form-list-panel").exists()).toBe(true);
    expect(list.find(".form-data-table").exists()).toBe(true);
    expect(list.find(".panel-head").exists()).toBe(false);
    expect(list.get("tbody tr").attributes("aria-selected")).toBe("true");
    await list.get("tbody tr").trigger("keydown", { key: "Enter" });
    expect(ledgerCallbacks.onSelectRow).toHaveBeenCalledWith(transaction.id);

    expect(detail.find(".form-detail-panel").exists()).toBe(true);
    expect(detail.find(".form-detail-bar").text()).toContain("REC-0041");
    expect(detail.find(".form-summary-grid").exists()).toBe(true);
    expect(detail.find(".form-data-table").exists()).toBe(true);
  });

  it("renders the five quality fields and inline repair rows with the Form UI table variant", async () => {
    const wrapper = mount(FixtureQualityPanel, {
      props: {
        report: qualityReport,
        fixtures: [fixture],
        loading: false,
        inlineSavingFixtureId: null,
        embeddedForm: true,
        issueFilter: []
      }
    });

    expect(wrapper.find(".form-quality-panel").exists()).toBe(true);
    expect(wrapper.find(".form-quality-overview").exists()).toBe(true);
    expect(wrapper.find(".form-quality-table-wrap").exists()).toBe(true);
    expect(wrapper.find(".form-quality-table").exists()).toBe(true);
    expect(wrapper.find(".panel-head").exists()).toBe(false);
    expect(wrapper.findAll("thead th").map((cell) => cell.text())).toEqual([
      "治具編號",
      "儲位",
      "最低水位",
      "機種關聯",
      "圖片"
    ]);
    expect(wrapper.findAll(".inline-edit-input")).toHaveLength(3);
    await wrapper.get("button.issue-pill").trigger("click");
    expect(wrapper.emitted("openIssueEditor")).toEqual([[fixture.id, "missing_image"]]);
  });

  it("keeps the Modern UI presentation when the Form variant is not requested", () => {
    const wrapper = mount(TransactionAccountDetailPanel, {
      props: {
        transaction,
        processing: false,
        onReload: vi.fn(),
        onRecalculate: vi.fn(),
        onReverse: vi.fn()
      }
    });

    expect(wrapper.find(".form-detail-panel").exists()).toBe(false);
    expect(wrapper.find(".panel-head").exists()).toBe(true);
  });

  it("renders dedicated Workbench ledger and quality variants", () => {
    const list = mount(TransactionAccountListPanel, {
      props: {
        rows: [transaction], selectedTransactionId: transaction.id, loading: false,
        transactionNo: "", createdBy: "", fixtureCode: "", transactionType: [],
        page: 1, pageSize: 12, totalPages: 1, total: 1, embeddedWorkbench: true,
        ...ledgerCallbacks
      }
    });
    const detail = mount(TransactionAccountDetailPanel, {
      props: {
        transaction, processing: false, embeddedWorkbench: true,
        onReload: vi.fn(), onRecalculate: vi.fn(), onReverse: vi.fn()
      }
    });
    const quality = mount(FixtureQualityPanel, {
      props: {
        report: qualityReport, fixtures: [fixture], loading: false,
        inlineSavingFixtureId: null, embeddedWorkbench: true, issueFilter: []
      }
    });

    expect(list.find(".workbench-ledger-list").exists()).toBe(true);
    expect(list.find(".workbench-ledger-table").exists()).toBe(true);
    expect(detail.find(".workbench-ledger-detail").exists()).toBe(true);
    expect(detail.get(".workbench-ledger-detail-bar").text()).toContain("REC-0041");
    expect(detail.find(".workbench-ledger-summary").exists()).toBe(true);
    expect(quality.find(".workbench-quality-panel").exists()).toBe(true);
    expect(quality.find(".workbench-quality-overview").exists()).toBe(true);
    expect(quality.find(".workbench-quality-table").exists()).toBe(true);
    expect(quality.find(".form-quality-table").exists()).toBe(false);
  });

  it("moves Workbench quality repair inputs to the right tool panel", async () => {
    const toolPanel = document.createElement("div");
    toolPanel.id = "workbench-management-tools";
    document.body.appendChild(toolPanel);
    const quality = mount(FixtureQualityPanel, {
      attachTo: document.body,
      props: {
        report: qualityReport,
        fixtures: [fixture],
        loading: false,
        inlineSavingFixtureId: null,
        embeddedWorkbench: true,
        workbenchSideEditor: true,
        issueFilter: []
      }
    });

    expect(quality.findAll(".inline-edit-input")).toHaveLength(0);
    await quality.get('button.issue-pill').trigger("click");
    expect(toolPanel.textContent).toContain("FIX QUALITY");
    expect(toolPanel.textContent).toContain("產線儲位");
    expect(toolPanel.querySelectorAll("input")).toHaveLength(3);

    quality.unmount();
    toolPanel.remove();
  });

  it("renders a compact Workbench ledger inspector for the right panel", () => {
    const detail = mount(TransactionAccountDetailPanel, {
      props: {
        transaction,
        processing: false,
        embeddedWorkbench: true,
        workbenchSidePanel: true,
        onReload: vi.fn(),
        onRecalculate: vi.fn(),
        onReverse: vi.fn()
      }
    });

    expect(detail.find(".workbench-ledger-side").exists()).toBe(true);
    expect(detail.find(".workbench-side-summary").exists()).toBe(true);
    expect(detail.findAll(".workbench-ledger-item-list > article")).toHaveLength(1);
    expect(detail.find(".workbench-ledger-detail-table").exists()).toBe(false);
    expect(detail.text()).toContain("FX-015");
    expect(detail.text()).toContain("2 pcs");
  });
});
