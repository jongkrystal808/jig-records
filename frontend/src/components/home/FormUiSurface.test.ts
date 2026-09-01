// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";

import { authSession, customers, selectedCustomerId } from "@/appState";
import FormUiSurface from "@/components/home/FormUiSurface.vue";
import type { AuthSession } from "@/types";

function session(role: "super_admin" | "admin" | "user" | "guest"): AuthSession {
  return {
    mode: role === "guest" ? "guest" : "user",
    user: role === "guest"
      ? null
      : {
          id: role === "admin" ? 1 : 2,
          username: role,
          email: null,
          display_name: role,
          role,
          is_active: true,
          allowed_customer_ids: [],
          created_at: "",
          updated_at: ""
        },
    display_name: role,
    token: "test-token",
    role
  };
}

function mountSurface(slots: Record<string, string> = {}) {
  return mount(FormUiSurface, {
    slots,
    global: {
      stubs: {
        InventoryRelationsPage: {
          name: "InventoryRelationsPage",
          props: {
            hideHeading: { type: Boolean, default: false },
            embeddedShell: { type: Boolean, default: false }
          },
          template: "<div data-testid='report-view'>report<slot name='between-filter-and-results' /></div>"
        },
        BatchImportPanel: {
          name: "BatchImportPanel",
          props: ["customerId", "title", "description", "hideFrame"],
          emits: ["draft-state-change"],
          template: "<div data-testid='inventory-view'>inventory<slot name='between-meta-and-grid' /></div>"
        },
        FormReportOperations: {
          name: "FormReportOperations",
          props: ["mode"],
          template: "<div data-testid='operation-view'>{{ mode }}<slot name='between-filter-and-results' /></div>"
        },
        FormAdminReports: {
          name: "FormAdminReports",
          props: ["mode"],
          emits: ["navigate"],
          template: "<div data-testid='admin-report-view'>{{ mode }}<slot name='between-filter-and-results' /></div>"
        },
        FormImageMaintenance: {
          name: "FormImageMaintenance",
          template: "<div data-testid='image-maintenance-view'>image<slot name='between-filter-and-results' /></div>"
        }
      }
    }
  });
}

afterEach(() => {
  authSession.value = null;
  customers.value = [];
  selectedCustomerId.value = null;
});

describe("FormUiSurface", () => {
  it("hosts system controls in the report heading after the Form topbar is removed", async () => {
    authSession.value = session("user");
    customers.value = [
      { id: 27, code: "TEST", name: "test_customer", assigned_user_ids: [] },
      { id: 28, code: "MOXA", name: "moxa", assigned_user_ids: [] }
    ];
    selectedCustomerId.value = 27;
    const wrapper = mountSurface({
      "ui-switcher": '<div data-testid="heading-ui-switcher">Modern / Form</div>',
      "heading-actions": '<button data-testid="heading-onboarding">新手教學</button>',
      "account-action": '<button data-testid="heading-logout">登出</button>'
    });

    expect(wrapper.find(".form-system-heading [data-testid='heading-ui-switcher']").exists()).toBe(true);
    expect(wrapper.find(".form-heading-side [data-testid='heading-onboarding']").exists()).toBe(true);
    expect(wrapper.find(".form-session-tools [data-testid='heading-logout']").exists()).toBe(true);
    expect(wrapper.get(".form-heading-title h1").text()).toBe("篩選報表");
    expect(wrapper.get(".form-current-user").text()).toContain("user");
    expect(wrapper.get(".form-current-user").text()).toContain("使用者");
    expect(wrapper.get(".form-scope-badge label > span").text()).toBe("目前客戶 1 / 2");

    await wrapper.get(".form-scope-badge select").setValue("28");
    expect(wrapper.emitted("update:selectedCustomerId")?.[0]).toEqual([28]);

    await wrapper.get('[aria-label="切換到下一個客戶"]').trigger("click");
    expect(wrapper.emitted("update:selectedCustomerId")?.[1]).toEqual([28]);
  });

  it("keeps one report frame while switching its table fields", async () => {
    authSession.value = session("user");
    selectedCustomerId.value = 27;
    const wrapper = mountSurface();

    expect(wrapper.find("[data-testid='report-view']").exists()).toBe(true);
    expect(wrapper.find("[data-testid='inventory-view']").exists()).toBe(false);

    const reportPage = wrapper.getComponent({ name: "InventoryRelationsPage" });
    expect(reportPage.props("hideHeading")).toBe(true);
    expect(reportPage.props("embeddedShell")).toBe(true);
    expect(wrapper.findAll(".form-workspace-tab")).toHaveLength(6);
    expect(wrapper.findAll(".form-workspace-group-label").map((node) => node.text())).toEqual([
      "日常作業",
      "設定維護"
    ]);
    expect(wrapper.get("[data-workspace='inventory-overview']").text()).toBe("收退料總檢視");
    expect(wrapper.get("[data-workspace='report']").attributes("aria-selected")).toBe("true");

    await wrapper.get("[data-workspace='import']").trigger("click");
    await flushPromises();

    const batchPanel = wrapper.getComponent({ name: "BatchImportPanel" });
    expect(wrapper.get(".form-heading-title h1").text()).toBe("收退料匯入");
    expect(batchPanel.props("customerId")).toBe(27);
    expect(wrapper.find("[data-testid='inventory-view']").isVisible()).toBe(true);
    expect(wrapper.find("[data-testid='report-view']").exists()).toBe(true);
    expect(wrapper.find("[data-testid='report-view']").isVisible()).toBe(false);

    batchPanel.vm.$emit("draft-state-change", {
      hasPendingDraft: true,
      pendingRowCount: 3,
      promptMessage: ""
    });
    await flushPromises();
    expect(wrapper.text()).toContain("收退料匯入尚有 3 筆未送出");

    await wrapper.get("[data-workspace='inventory-overview']").trigger("click");
    await flushPromises();
    expect(wrapper.get(".form-heading-title h1").text()).toBe("收退料總檢視");
    expect(wrapper.find("[data-testid='report-view']").exists()).toBe(true);
    expect(wrapper.find("[data-testid='inventory-view']").exists()).toBe(true);
    expect(wrapper.get(".form-batch-workspace").attributes("style")).toContain("display: none");
    const operationPage = wrapper.getComponent({ name: "FormReportOperations" });
    expect(operationPage.props("mode")).toBe("transactions");
    expect(wrapper.text()).toContain("transactions");

    await wrapper.get("[data-workspace='production']").trigger("click");
    await flushPromises();
    expect(wrapper.get(".form-heading-title h1").text()).toBe("產能");
    expect(operationPage.props("mode")).toBe("production");
    expect(wrapper.text()).toContain("production");

    await wrapper.get("[data-workspace='master']").trigger("click");
    await flushPromises();
    expect(wrapper.get(".form-heading-title h1").text()).toBe("資料維護");
    expect(operationPage.props("mode")).toBe("master");
    expect(wrapper.text()).toContain("master");
    expect(wrapper.find("[data-testid='report-view']").exists()).toBe(true);

    await wrapper.get("[data-workspace='image']").trigger("click");
    await flushPromises();
    expect(wrapper.get(".form-heading-title h1").text()).toBe("圖片維護");
    expect(wrapper.find("[data-testid='image-maintenance-view']").isVisible()).toBe(true);

    await wrapper.get("[data-workspace='report']").trigger("click");
    await flushPromises();
    expect(wrapper.get(".form-heading-title h1").text()).toBe("篩選報表");
    expect(wrapper.get("[data-workspace='report']").attributes("aria-selected")).toBe("true");
    expect(wrapper.find("[data-testid='report-view']").exists()).toBe(true);
  });

  it("keeps guest sessions on the report and read-only transaction overview", async () => {
    authSession.value = session("guest");
    const wrapper = mountSurface();

    expect(wrapper.findAll(".form-workspace-tab")).toHaveLength(2);
    expect(wrapper.findAll(".form-workspace-group-label").map((node) => node.text())).toEqual(["日常作業"]);
    expect(wrapper.text()).not.toContain("收退料匯入");
    expect(wrapper.find("[data-workspace='master']").exists()).toBe(false);
    expect(wrapper.text()).toContain("收退料總檢視");
    expect(wrapper.find("[data-testid='report-view']").exists()).toBe(true);
    expect(wrapper.find("[data-testid='inventory-view']").exists()).toBe(false);

    await wrapper.get("[data-workspace='inventory-overview']").trigger("click");
    await flushPromises();
    expect(wrapper.getComponent({ name: "FormReportOperations" }).props("mode")).toBe("transactions");
    expect(wrapper.find("[data-testid='report-view']").exists()).toBe(true);
  });

  it("adds ledger and fixture quality workspaces for admins only", async () => {
    authSession.value = session("admin");
    selectedCustomerId.value = 27;
    const wrapper = mountSurface();

    expect(wrapper.findAll(".form-workspace-tab")).toHaveLength(8);
    expect(wrapper.findAll(".form-workspace-group-label").map((node) => node.text())).toEqual([
      "日常作業",
      "設定維護",
      "系統管理"
    ]);
    expect(wrapper.find("[data-workspace='ledger']").exists()).toBe(true);
    expect(wrapper.find("[data-workspace='quality']").exists()).toBe(true);

    await wrapper.get("[data-workspace='ledger']").trigger("click");
    await flushPromises();
    expect(wrapper.get(".form-heading-title h1").text()).toBe("收退料帳目管理");
    expect(wrapper.getComponent({ name: "FormAdminReports" }).props("mode")).toBe("ledger");

    await wrapper.get("[data-workspace='quality']").trigger("click");
    await flushPromises();
    expect(wrapper.getComponent({ name: "FormAdminReports" }).props("mode")).toBe("quality");
    expect(wrapper.get(".form-heading-title h1").text()).toBe("治具資料品質");

    wrapper.unmount();
  });
});
