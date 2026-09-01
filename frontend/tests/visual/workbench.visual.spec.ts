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

test("workbench combined transaction overview matches the approved responsive baseline", async ({ page }, testInfo) => {
  await installDeterministicApi(page);
  await page.goto("/search?ui_surface=workbench&workbench_mode=transaction&transaction_type=receipt&customer=1");
  await page.locator(".workbench-ui").waitFor();
  await expect(page.locator('.workbench-mode-tabs [role="tab"]')).toHaveCount(4);
  await expect(page.locator('.workbench-mode-tabs [role="tab"]').last()).toHaveText("管理後臺");
  await expect(page.locator(".workbench-recent-table tbody tr")).toHaveCount(50);
  await expect(page.locator(".workbench-table-pager")).toContainText("第 1 / 2 頁");

  const horizontalOverflow = await page.evaluate(() =>
    Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth)
  );
  expect(horizontalOverflow, `${testInfo.project.name} must not overflow the page horizontally`).toBeLessThanOrEqual(1);

  await expect(page).toHaveScreenshot("workbench-receipt.png", { fullPage: false });

  await page.getByRole("tab", { name: "管理後臺", exact: true }).click();
  await expect(page.locator('[data-tour="workbench-management-launcher"]')).toBeVisible();
  await expect(page.locator('[data-tour="workbench-management-launcher"]')).toContainText("匯出中心");
  const managementOverflow = await page.evaluate(() =>
    Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth)
  );
  expect(managementOverflow, `${testInfo.project.name} management launcher must not overflow horizontally`).toBeLessThanOrEqual(1);
});

test("workbench keeps fixture and identifier lookup as explicit URL-backed modes", async ({ page }, testInfo) => {
  await installDeterministicApi(page);
  await page.goto("/search?ui_surface=workbench&workbench_mode=fixture&fixture_search=identifier&q=2204&selected_id=101&customer=1");
  await page.locator(".workbench-ui").waitFor();
  await expect(page.getByRole("button", { name: "Datecode／序號", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".workbench-query-form input")).toHaveValue("2204");
  await expect(page.locator(".workbench-results")).toContainText("2204");
  await expect(page.locator(".workbench-detail")).toContainText("FX-001");
  await expect(page.locator(".toast-card.error")).toHaveCount(0);

  const horizontalOverflow = await page.evaluate(() =>
    Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth)
  );
  expect(horizontalOverflow, `${testInfo.project.name} identifier search must not overflow horizontally`).toBeLessThanOrEqual(1);
  await expect(page).toHaveScreenshot("workbench-identifier-search.png", { fullPage: false });
});

test("workbench management uses left navigation, full results, and right tools", async ({ page }, testInfo) => {
  await installDeterministicApi(page, "admin");
  await page.goto("/inventory/overview?ui_surface=workbench&customer=1");
  await page.locator(".workbench-management-ui").waitFor();
  await expect(page.locator(".workbench-management-columns > .workbench-panel")).toHaveCount(3);
  await expect(page.locator(".workbench-management-detail")).toContainText("篩選條件");
  await expect(page.locator(".workbench-management-detail")).not.toContainText("操作角色");
  await expect(page.locator(".workbench-management-results .filter-panel")).toHaveCount(0);

  const layout = await page.evaluate(() => {
    const panels = Array.from(document.querySelectorAll<HTMLElement>(".workbench-management-columns > .workbench-panel"));
    return {
      lefts: panels.map((panel) => Math.round(panel.getBoundingClientRect().left)),
      widths: panels.map((panel) => Math.round(panel.getBoundingClientRect().width)),
      overflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth)
    };
  });
  expect(layout.lefts[0], `${testInfo.project.name} navigation should be first`).toBeLessThan(layout.lefts[1]!);
  expect(layout.lefts[1], `${testInfo.project.name} results should be centered`).toBeLessThan(layout.lefts[2]!);
  expect(layout.widths[1], `${testInfo.project.name} result panel should receive the most width`).toBeGreaterThan(layout.widths[2]!);
  expect(layout.widths[2], `${testInfo.project.name} tool panel must remain usable`).toBeGreaterThanOrEqual(250);
  expect(layout.overflow, `${testInfo.project.name} management page must not overflow horizontally`).toBeLessThanOrEqual(1);

  await expect(page).toHaveScreenshot("workbench-management-overview.png", { fullPage: false });
});

test("workbench image maintenance uses a selected list row and right inspector", async ({ page }, testInfo) => {
  await installDeterministicApi(page, "admin");
  await page.goto("/master/images?ui_surface=workbench&customer=1");
  await page.locator(".workbench-management-ui").waitFor();
  await expect(page.locator("tbody tr.workbench-image-row")).toHaveCount(fixtures.length);
  await expect(page.locator("tbody tr.workbench-image-row.selected")).toHaveCount(1);
  await expect(page.locator(".workbench-management-detail")).toContainText("SELECTED FIXTURE");
  await expect(page.locator(".workbench-management-detail")).toContainText("尚無圖片");
  await expect(page.locator(".workbench-management-results thead th")).toHaveCount(4);
  await page.locator(".workbench-filter-toggle").click();
  await expect(page.locator(".workbench-management-detail .form-image-filters")).toBeHidden();
  await expect(page.locator(".workbench-filter-toggle")).toHaveAttribute("aria-expanded", "false");
  await page.locator(".workbench-filter-toggle").click();

  const overflow = await page.evaluate(() => Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth));
  expect(overflow, `${testInfo.project.name} image maintenance must not overflow horizontally`).toBeLessThanOrEqual(1);
  await expect(page).toHaveScreenshot("workbench-image-maintenance.png", { fullPage: false });
});

test("workbench ledger keeps the case list central and details in right tools", async ({ page }, testInfo) => {
  await installDeterministicApi(page, "admin");
  await page.goto("/master/ledger?ui_surface=workbench&customer=1");
  await page.locator(".workbench-management-ui").waitFor();
  await expect(page.locator(".workbench-management-results .workbench-ledger-table tbody tr")).toHaveCount(ledgerRows.length);
  await expect(page.locator(".workbench-management-results .workbench-ledger-detail")).toHaveCount(0);
  await expect(page.locator(".workbench-management-detail .workbench-ledger-side")).toContainText("LED-0001");
  await expect(page.locator(".workbench-management-detail .workbench-ledger-item-list > article")).toHaveCount(1);

  const typeSelect = page.locator('.workbench-management-detail details[aria-label="作業類型複選"]');
  await typeSelect.locator("summary").click();
  await expect(typeSelect.locator(".ui-multi-select-option")).toHaveCount(2);
  await expect(typeSelect.locator('.ui-multi-select-option input[type="checkbox"]').first()).toHaveCSS("clip-path", "inset(50%)");
  await expect(page).toHaveScreenshot("workbench-ledger-multiselect-open.png", { fullPage: false });
  await typeSelect.locator("summary").click();

  const overflow = await page.evaluate(() => Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth));
  expect(overflow, `${testInfo.project.name} ledger must not overflow horizontally`).toBeLessThanOrEqual(1);
  await expect(page).toHaveScreenshot("workbench-ledger-management.png", { fullPage: false });

  await page.locator(".workbench-filter-toggle").click();
  await expect(page.locator(".workbench-management-detail .workbench-admin-filter-grid")).toBeHidden();
  await expect(page.locator(".workbench-management-detail .workbench-ledger-side")).toBeVisible();
  await expect(page).toHaveScreenshot("workbench-ledger-management-collapsed.png", { fullPage: false });
});
