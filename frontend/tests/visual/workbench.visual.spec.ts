import { expect, test, type Page, type Route } from "@playwright/test";

const customer = {
  id: 1,
  code: "VISUAL",
  name: "Visual Regression Customer",
  assigned_user_ids: []
};

const fixtures = Array.from({ length: 8 }, (_, index) => ({
  id: 101 + index,
  customer_id: 1,
  responsible_user_id: null,
  code: `FX-${String(index + 1).padStart(3, "0")}`,
  name: `Fixture ${index + 1}`,
  line_storage_location: `L-${index + 1}`,
  department_storage_location: "D-01",
  min_stock_qty: 2,
  description: null,
  is_active: true,
  has_image: false
}));

const models = Array.from({ length: 6 }, (_, index) => ({
  id: 201 + index,
  customer_id: 1,
  code: `MODEL-${String(index + 1).padStart(2, "0")}`,
  name: `Production model ${index + 1}`,
  is_active: true
}));

const transactionRows = Array.from({ length: 60 }, (_, index) => ({
  id: 1001 + index,
  transaction_type: index % 4 === 0 ? "return" : "receipt",
  transaction_no: `VIS-${String(index + 1).padStart(4, "0")}`,
  occurred_at: `2026-08-${String(25 - (index % 5)).padStart(2, "0")}T08:00:00Z`,
  created_by: index % 2 === 0 ? "Operator A" : "Operator B",
  fixture_id: fixtures[index % fixtures.length]!.id,
  fixture_code: fixtures[index % fixtures.length]!.code,
  fixture_name: fixtures[index % fixtures.length]!.name,
  ownership_type: index % 3 === 0 ? "self_purchased" : "customer_supplied",
  identifier: String(2200 + index),
  quantity: (index % 9) + 1,
  note: index === 0 ? "Visual regression fixture transaction" : null
}));

const ledgerRows = Array.from({ length: 12 }, (_, index) => ({
  id: 3001 + index,
  customer_id: 1,
  transaction_type: index % 4 === 0 ? "return" : "receipt",
  transaction_no: `LED-${String(index + 1).padStart(4, "0")}`,
  occurred_at: `2026-08-${String(25 - (index % 5)).padStart(2, "0")}T08:00:00Z`,
  created_by: index % 2 === 0 ? "Operator A" : "Operator B",
  note: index === 0 ? "工作台帳目檢視測試" : null,
  created_at: "2026-08-27T08:00:00Z",
  items: [
    {
      fixture_id: fixtures[index % fixtures.length]!.id,
      fixture_code: fixtures[index % fixtures.length]!.code,
      fixture_name: fixtures[index % fixtures.length]!.name,
      ownership_type: index % 3 === 0 ? "self_purchased" : "customer_supplied",
      identifier: String(2200 + index),
      quantity: (index % 5) + 1,
      note: index === 0 ? "首筆案件治具明細" : null
    }
  ]
}));

function fulfillJson(route: Route, body: unknown): Promise<void> {
  return route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify(body)
  });
}

async function installDeterministicApi(page: Page, role: "guest" | "admin" = "guest"): Promise<void> {
  await page.addInitScript((requestedRole) => {
    const isAdmin = requestedRole === "admin";
    sessionStorage.setItem("jig-record-session", JSON.stringify({
      mode: isAdmin ? "user" : "guest",
      user: isAdmin ? {
        id: 1, username: "visual-admin", email: null, display_name: "視覺測試管理員",
        role: "admin", is_active: true, allowed_customer_ids: [1], created_at: "2026-08-27", updated_at: "2026-08-27"
      } : null,
      display_name: isAdmin ? "視覺測試管理員" : "視覺測試訪客",
      token: "visual-test-token",
      role: requestedRole
    }));
    sessionStorage.setItem("jig-record-customer-id", "1");
  }, role);

  await page.route("**/api/v2/**", async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith("/inventory/configuration-report/options")) {
      return fulfillJson(route, { fixtures: [], models: [], stations: [], water_statuses: [] });
    }
    if (url.pathname.endsWith("/inventory/configuration-report")) {
      return fulfillJson(route, {
        items: [], page: 1, page_size: 50, total: 0,
        fixture_count: 0, attention_fixture_count: 0, missing_configuration_count: 0,
        total_stock_qty: 0, customer_supplied_qty: 0, self_purchased_qty: 0,
        populated_columns: [], transaction_details: [], transaction_detail_count: 0
      });
    }
    if (url.pathname.endsWith("/master/customers")) return fulfillJson(route, [customer]);
    if (url.pathname.endsWith("/master/fixtures/page")) {
      return fulfillJson(route, { items: fixtures, page: 1, page_size: 50, total: fixtures.length });
    }
    if (url.pathname.endsWith("/master/fixtures")) return fulfillJson(route, fixtures);
    if (url.pathname.endsWith("/master/models")) return fulfillJson(route, models);
    if (url.pathname.endsWith("/search/global")) {
      const identifierMode = url.searchParams.get("fixture_search_mode") === "identifier";
      return fulfillJson(route, {
        items: [{
          entity_type: "fixture",
          title: fixtures[0]!.code,
          subtitle: fixtures[0]!.name,
          reference_id: fixtures[0]!.id,
          is_active: true,
          stock_qty: 12,
          stock_status: "normal",
          location_code: "L-1 / D-01",
          matched_identifier: identifierMode ? "2204" : null
        }],
        page: 1,
        page_size: 20,
        total: 1,
        has_more: false
      });
    }
    if (url.pathname.endsWith(`/search/fixtures/${fixtures[0]!.id}/context`)) {
      return fulfillJson(route, {
        fixture: fixtures[0],
        stock: {
          fixture_id: fixtures[0]!.id,
          fixture_code: fixtures[0]!.code,
          fixture_name: fixtures[0]!.name,
          stock_qty: 12,
          customer_supplied_qty: 7,
          self_purchased_qty: 5,
          min_stock_qty: 2,
          stock_status: "normal",
          last_transaction_at: "2026-08-25T08:00:00Z"
        },
        identifier_rows: [{ fixture_id: fixtures[0]!.id, identifier: "2204", stock_qty: 12, customer_supplied_qty: 7, self_purchased_qty: 5 }],
        related_models: [],
        station_rows: [],
        transactions: []
      });
    }
    if (url.pathname.endsWith("/inventory/transactions/overview")) {
      const pageNumber = Number(url.searchParams.get("page") ?? "1");
      const pageSize = Number(url.searchParams.get("page_size") ?? "50");
      const start = (pageNumber - 1) * pageSize;
      return fulfillJson(route, {
        items: transactionRows.slice(start, start + pageSize),
        page: pageNumber,
        page_size: pageSize,
        total: transactionRows.length
      });
    }
    if (url.pathname.endsWith("/inventory/admin/transactions")) {
      return fulfillJson(route, { items: ledgerRows, page: 1, page_size: 12, total: ledgerRows.length });
    }
    if (url.pathname.endsWith("/inventory/dashboard-summary")) {
      return fulfillJson(route, {
        today_receipt_qty: 32,
        today_return_qty: 8,
        low_stock_count: 2,
        low_stock_preview_entries: [],
        has_more_low_stock_entries: false,
        recent_receipt_entries: [],
        recent_return_entries: []
      });
    }
    return fulfillJson(route, []);
  });
}

async function expectNoPageOverflow(page: Page, label: string): Promise<void> {
  const horizontalOverflow = await page.evaluate(() =>
    Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth)
  );
  expect(horizontalOverflow, `${label} must not overflow the page horizontally`).toBeLessThanOrEqual(1);
}

test("Workspace transaction operation matches the approved responsive baseline", async ({ page }, testInfo) => {
  await installDeterministicApi(page);
  await page.goto("/search?ui_surface=workspace&workbench_mode=transaction&transaction_type=receipt&customer=1");
  await page.getByRole("region", { name: "Workspace UI 快速作業" }).waitFor();
  await expect(page.locator('.workbench-mode-tabs [role="tab"]')).toHaveCount(4);
  await expect(page.locator('.workbench-mode-tabs [role="tab"]').last()).toHaveText("收／退料總檢視");
  await expect(page.locator(".workbench-recent-table tbody tr")).toHaveCount(50);
  await expect(page.locator(".workbench-table-pager")).toContainText("第 1 / 2 頁");
  await expectNoPageOverflow(page, `${testInfo.project.name} Workspace transaction operation`);

  await expect(page).toHaveScreenshot("workspace-transaction-operation.png", { fullPage: false });

  await page.getByRole("tab", { name: "收／退料總檢視", exact: true }).click();
  await expect(page).toHaveURL(/\/inventory\/overview\?.*ui_surface=workspace/);
});

test("Workspace fixture identifier lookup keeps its URL-backed state", async ({ page }, testInfo) => {
  await installDeterministicApi(page);
  await page.goto("/search?ui_surface=workspace&workbench_mode=fixture&fixture_search=identifier&q=2204&selected_id=101&customer=1");
  await page.getByRole("region", { name: "Workspace UI 快速作業" }).waitFor();
  await expect(page.getByRole("button", { name: "Datecode／序號", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".workbench-query-form input")).toHaveValue("2204");
  await expect(page.locator(".workbench-results")).toContainText("2204");
  await expect(page.locator(".workbench-detail")).toContainText("FX-001");
  await expect(page.locator(".toast-card.error")).toHaveCount(0);
  await expectNoPageOverflow(page, `${testInfo.project.name} Workspace identifier search`);

  await expect(page).toHaveScreenshot("workspace-identifier-search.png", { fullPage: false });
});

test("Workspace transaction overview uses the current compact navigation and filter layout", async ({ page }, testInfo) => {
  await installDeterministicApi(page, "admin");
  await page.goto("/inventory/overview?ui_surface=workspace&customer=1");
  await page.getByRole("region", { name: "現場工作台收退料總檢視" }).waitFor();
  await expect(page.locator(".workbench-management-columns > .workbench-panel")).toHaveCount(3);
  await expect(page.locator(".workbench-management-detail")).toContainText("篩選條件");
  await expect(page.locator(".workbench-management-nav > .workbench-panel-heading")).toHaveCount(0);
  await expect(page.locator('.workbench-management-nav [role="tab"]')).toHaveCount(4);

  const layout = await page.evaluate(() => {
    const panels = Array.from(document.querySelectorAll<HTMLElement>(".workbench-management-columns > .workbench-panel"));
    return {
      display: getComputedStyle(document.querySelector<HTMLElement>(".workbench-management-columns")!).display,
      lefts: panels.map((panel) => Math.round(panel.getBoundingClientRect().left)),
      widths: panels.map((panel) => Math.round(panel.getBoundingClientRect().width)),
      overflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth)
    };
  });
  if (testInfo.project.name === "mobile-390") {
    expect(layout.display).toBe("flex");
    expect(layout.widths[0], "mobile navigation should use the available row width").toBeGreaterThan(320);
  } else {
    expect(layout.lefts[0], `${testInfo.project.name} navigation should be first`).toBeLessThan(layout.lefts[1]!);
    expect(layout.lefts[1], `${testInfo.project.name} results should be centered`).toBeLessThan(layout.lefts[2]!);
    expect(layout.widths[0], `${testInfo.project.name} navigation should stay compact`).toBeLessThan(170);
    expect(layout.widths[1], `${testInfo.project.name} result panel should receive the most width`).toBeGreaterThan(layout.widths[0]!);
    expect(layout.widths[2], `${testInfo.project.name} tool panel must remain usable`).toBeGreaterThanOrEqual(250);
  }
  expect(layout.overflow, `${testInfo.project.name} management page must not overflow horizontally`).toBeLessThanOrEqual(1);

  await expect(page).toHaveScreenshot("workspace-transaction-overview.png", { fullPage: false });
});

test("Workspace master fixture maintenance uses the current list and detail flow", async ({ page }, testInfo) => {
  await installDeterministicApi(page, "admin");
  await page.goto("/master/fixtures?ui_surface=workspace&customer=1");
  await page.locator(".master-shell").waitFor();
  const fixtureList = page.locator('[data-tour="detailed-master-list"]');
  await expect(fixtureList.getByRole("heading", { name: "治具清單" })).toBeVisible();
  await expect(fixtureList.locator("tbody tr")).toHaveCount(fixtures.length);
  await fixtureList.locator("tbody tr").first().click();
  const fixtureDetail = page.locator('[data-tour="detailed-master-detail"]');
  await expect(fixtureDetail).toContainText("FX-001");
  await expect(fixtureDetail).toContainText("Fixture 1");
  await expectNoPageOverflow(page, `${testInfo.project.name} Workspace master fixtures`);

  await expect(page).toHaveScreenshot("workspace-master-fixtures.png", { fullPage: false });
});

test("Workspace ledger uses the current master list and case detail layout", async ({ page }, testInfo) => {
  await installDeterministicApi(page, "admin");
  await page.goto("/master/ledger?ui_surface=workspace&customer=1");
  await page.locator(".master-shell").waitFor();
  const ledgerList = page.locator('[data-tour="master-ledger-list"]');
  const ledgerDetail = page.locator('[data-tour="master-ledger-detail"]');
  await expect(ledgerList.locator("tbody tr")).toHaveCount(ledgerRows.length);
  await expect(ledgerDetail).toContainText("LED-0001");
  await expect(ledgerDetail.locator("tbody tr")).toHaveCount(1);

  const typeSelect = page.locator('[data-tour="master-ledger-filters"] details[aria-label="類型複選"]');
  await typeSelect.locator("summary").click();
  await expect(typeSelect.locator(".ui-multi-select-option")).toHaveCount(2);
  await expect(typeSelect.locator('.ui-multi-select-option input[type="checkbox"]').first()).toHaveCSS("clip-path", "inset(50%)");
  await expectNoPageOverflow(page, `${testInfo.project.name} Workspace ledger`);
  await expect(page).toHaveScreenshot("workspace-ledger.png", { fullPage: false });
});
