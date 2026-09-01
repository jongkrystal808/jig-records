# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: workbench.visual.spec.ts >> workbench combined transaction overview matches the approved responsive baseline
- Location: tests\visual\workbench.visual.spec.ts:181:1

# Error details

```
Error: expect(locator).toHaveText(expected) failed

Locator:  locator('.workbench-mode-tabs [role="tab"]').last()
Expected: "管理後臺"
Received: "收／退料總檢視"
Timeout:  5000ms

Call log:
  - Expect "toHaveText" with timeout 5000ms
  - waiting for locator('.workbench-mode-tabs [role="tab"]').last()
    13 × locator resolved to <button class="" role="tab" type="button" data-v-dbc6f529="" aria-selected="false" data-tour="workspace-overview-entry">收／退料總檢視</button>
       - unexpected value "收／退料總檢視"

```

```yaml
- tab "收／退料總檢視"
```

# Test source

```ts
  86  |       display_name: isAdmin ? "視覺測試管理員" : "視覺測試訪客",
  87  |       token: "visual-test-token",
  88  |       role: requestedRole
  89  |     }));
  90  |     sessionStorage.setItem("jig-record-customer-id", "1");
  91  |   }, role);
  92  | 
  93  |   await page.route("**/api/v2/**", async (route) => {
  94  |     const url = new URL(route.request().url());
  95  |     if (url.pathname.endsWith("/inventory/configuration-report/options")) {
  96  |       return fulfillJson(route, { fixtures: [], models: [], stations: [], water_statuses: [] });
  97  |     }
  98  |     if (url.pathname.endsWith("/inventory/configuration-report")) {
  99  |       return fulfillJson(route, {
  100 |         items: [], page: 1, page_size: 50, total: 0,
  101 |         fixture_count: 0, attention_fixture_count: 0, missing_configuration_count: 0,
  102 |         total_stock_qty: 0, customer_supplied_qty: 0, self_purchased_qty: 0,
  103 |         populated_columns: [], transaction_details: [], transaction_detail_count: 0
  104 |       });
  105 |     }
  106 |     if (url.pathname.endsWith("/master/customers")) return fulfillJson(route, [customer]);
  107 |     if (url.pathname.endsWith("/master/fixtures/page")) {
  108 |       return fulfillJson(route, { items: fixtures, page: 1, page_size: 50, total: fixtures.length });
  109 |     }
  110 |     if (url.pathname.endsWith("/master/fixtures")) return fulfillJson(route, fixtures);
  111 |     if (url.pathname.endsWith("/master/models")) return fulfillJson(route, models);
  112 |     if (url.pathname.endsWith("/search/global")) {
  113 |       const identifierMode = url.searchParams.get("fixture_search_mode") === "identifier";
  114 |       return fulfillJson(route, {
  115 |         items: [{
  116 |           entity_type: "fixture",
  117 |           title: fixtures[0]!.code,
  118 |           subtitle: fixtures[0]!.name,
  119 |           reference_id: fixtures[0]!.id,
  120 |           is_active: true,
  121 |           stock_qty: 12,
  122 |           stock_status: "normal",
  123 |           location_code: "L-1 / D-01",
  124 |           matched_identifier: identifierMode ? "2204" : null
  125 |         }],
  126 |         page: 1,
  127 |         page_size: 20,
  128 |         total: 1,
  129 |         has_more: false
  130 |       });
  131 |     }
  132 |     if (url.pathname.endsWith(`/search/fixtures/${fixtures[0]!.id}/context`)) {
  133 |       return fulfillJson(route, {
  134 |         fixture: fixtures[0],
  135 |         stock: {
  136 |           fixture_id: fixtures[0]!.id,
  137 |           fixture_code: fixtures[0]!.code,
  138 |           fixture_name: fixtures[0]!.name,
  139 |           stock_qty: 12,
  140 |           customer_supplied_qty: 7,
  141 |           self_purchased_qty: 5,
  142 |           min_stock_qty: 2,
  143 |           stock_status: "normal",
  144 |           last_transaction_at: "2026-08-25T08:00:00Z"
  145 |         },
  146 |         identifier_rows: [{ fixture_id: fixtures[0]!.id, identifier: "2204", stock_qty: 12, customer_supplied_qty: 7, self_purchased_qty: 5 }],
  147 |         related_models: [],
  148 |         station_rows: [],
  149 |         transactions: []
  150 |       });
  151 |     }
  152 |     if (url.pathname.endsWith("/inventory/transactions/overview")) {
  153 |       const pageNumber = Number(url.searchParams.get("page") ?? "1");
  154 |       const pageSize = Number(url.searchParams.get("page_size") ?? "50");
  155 |       const start = (pageNumber - 1) * pageSize;
  156 |       return fulfillJson(route, {
  157 |         items: transactionRows.slice(start, start + pageSize),
  158 |         page: pageNumber,
  159 |         page_size: pageSize,
  160 |         total: transactionRows.length
  161 |       });
  162 |     }
  163 |     if (url.pathname.endsWith("/inventory/admin/transactions")) {
  164 |       return fulfillJson(route, { items: ledgerRows, page: 1, page_size: 12, total: ledgerRows.length });
  165 |     }
  166 |     if (url.pathname.endsWith("/inventory/dashboard-summary")) {
  167 |       return fulfillJson(route, {
  168 |         today_receipt_qty: 32,
  169 |         today_return_qty: 8,
  170 |         low_stock_count: 2,
  171 |         low_stock_preview_entries: [],
  172 |         has_more_low_stock_entries: false,
  173 |         recent_receipt_entries: [],
  174 |         recent_return_entries: []
  175 |       });
  176 |     }
  177 |     return fulfillJson(route, []);
  178 |   });
  179 | }
  180 | 
  181 | test("workbench combined transaction overview matches the approved responsive baseline", async ({ page }, testInfo) => {
  182 |   await installDeterministicApi(page);
  183 |   await page.goto("/search?ui_surface=workbench&workbench_mode=transaction&transaction_type=receipt&customer=1");
  184 |   await page.locator(".workbench-ui").waitFor();
  185 |   await expect(page.locator('.workbench-mode-tabs [role="tab"]')).toHaveCount(4);
> 186 |   await expect(page.locator('.workbench-mode-tabs [role="tab"]').last()).toHaveText("管理後臺");
      |                                                                          ^ Error: expect(locator).toHaveText(expected) failed
  187 |   await expect(page.locator(".workbench-recent-table tbody tr")).toHaveCount(50);
  188 |   await expect(page.locator(".workbench-table-pager")).toContainText("第 1 / 2 頁");
  189 | 
  190 |   const horizontalOverflow = await page.evaluate(() =>
  191 |     Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth)
  192 |   );
  193 |   expect(horizontalOverflow, `${testInfo.project.name} must not overflow the page horizontally`).toBeLessThanOrEqual(1);
  194 | 
  195 |   await expect(page).toHaveScreenshot("workbench-receipt.png", { fullPage: false });
  196 | 
  197 |   await page.getByRole("tab", { name: "管理後臺", exact: true }).click();
  198 |   await expect(page.locator('[data-tour="workbench-management-launcher"]')).toBeVisible();
  199 |   await expect(page.locator('[data-tour="workbench-management-launcher"]')).toContainText("匯出中心");
  200 |   const managementOverflow = await page.evaluate(() =>
  201 |     Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth)
  202 |   );
  203 |   expect(managementOverflow, `${testInfo.project.name} management launcher must not overflow horizontally`).toBeLessThanOrEqual(1);
  204 | });
  205 | 
  206 | test("workbench keeps fixture and identifier lookup as explicit URL-backed modes", async ({ page }, testInfo) => {
  207 |   await installDeterministicApi(page);
  208 |   await page.goto("/search?ui_surface=workbench&workbench_mode=fixture&fixture_search=identifier&q=2204&selected_id=101&customer=1");
  209 |   await page.locator(".workbench-ui").waitFor();
  210 |   await expect(page.getByRole("button", { name: "Datecode／序號", exact: true })).toHaveAttribute("aria-pressed", "true");
  211 |   await expect(page.locator(".workbench-query-form input")).toHaveValue("2204");
  212 |   await expect(page.locator(".workbench-results")).toContainText("2204");
  213 |   await expect(page.locator(".workbench-detail")).toContainText("FX-001");
  214 |   await expect(page.locator(".toast-card.error")).toHaveCount(0);
  215 | 
  216 |   const horizontalOverflow = await page.evaluate(() =>
  217 |     Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth)
  218 |   );
  219 |   expect(horizontalOverflow, `${testInfo.project.name} identifier search must not overflow horizontally`).toBeLessThanOrEqual(1);
  220 |   await expect(page).toHaveScreenshot("workbench-identifier-search.png", { fullPage: false });
  221 | });
  222 | 
  223 | test("workbench management uses left navigation, full results, and right tools", async ({ page }, testInfo) => {
  224 |   await installDeterministicApi(page, "admin");
  225 |   await page.goto("/inventory/overview?ui_surface=workbench&customer=1");
  226 |   await page.locator(".workbench-management-ui").waitFor();
  227 |   await expect(page.locator(".workbench-management-columns > .workbench-panel")).toHaveCount(3);
  228 |   await expect(page.locator(".workbench-management-detail")).toContainText("篩選條件");
  229 |   await expect(page.locator(".workbench-management-detail")).not.toContainText("操作角色");
  230 |   await expect(page.locator(".workbench-management-results .filter-panel")).toHaveCount(0);
  231 | 
  232 |   const layout = await page.evaluate(() => {
  233 |     const panels = Array.from(document.querySelectorAll<HTMLElement>(".workbench-management-columns > .workbench-panel"));
  234 |     return {
  235 |       lefts: panels.map((panel) => Math.round(panel.getBoundingClientRect().left)),
  236 |       widths: panels.map((panel) => Math.round(panel.getBoundingClientRect().width)),
  237 |       overflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth)
  238 |     };
  239 |   });
  240 |   expect(layout.lefts[0], `${testInfo.project.name} navigation should be first`).toBeLessThan(layout.lefts[1]!);
  241 |   expect(layout.lefts[1], `${testInfo.project.name} results should be centered`).toBeLessThan(layout.lefts[2]!);
  242 |   expect(layout.widths[1], `${testInfo.project.name} result panel should receive the most width`).toBeGreaterThan(layout.widths[2]!);
  243 |   expect(layout.widths[2], `${testInfo.project.name} tool panel must remain usable`).toBeGreaterThanOrEqual(250);
  244 |   expect(layout.overflow, `${testInfo.project.name} management page must not overflow horizontally`).toBeLessThanOrEqual(1);
  245 | 
  246 |   await expect(page).toHaveScreenshot("workbench-management-overview.png", { fullPage: false });
  247 | });
  248 | 
  249 | test("workbench image maintenance uses a selected list row and right inspector", async ({ page }, testInfo) => {
  250 |   await installDeterministicApi(page, "admin");
  251 |   await page.goto("/master/images?ui_surface=workbench&customer=1");
  252 |   await page.locator(".workbench-management-ui").waitFor();
  253 |   await expect(page.locator("tbody tr.workbench-image-row")).toHaveCount(fixtures.length);
  254 |   await expect(page.locator("tbody tr.workbench-image-row.selected")).toHaveCount(1);
  255 |   await expect(page.locator(".workbench-management-detail")).toContainText("SELECTED FIXTURE");
  256 |   await expect(page.locator(".workbench-management-detail")).toContainText("尚無圖片");
  257 |   await expect(page.locator(".workbench-management-results thead th")).toHaveCount(4);
  258 |   await page.locator(".workbench-filter-toggle").click();
  259 |   await expect(page.locator(".workbench-management-detail .form-image-filters")).toBeHidden();
  260 |   await expect(page.locator(".workbench-filter-toggle")).toHaveAttribute("aria-expanded", "false");
  261 |   await page.locator(".workbench-filter-toggle").click();
  262 | 
  263 |   const overflow = await page.evaluate(() => Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth));
  264 |   expect(overflow, `${testInfo.project.name} image maintenance must not overflow horizontally`).toBeLessThanOrEqual(1);
  265 |   await expect(page).toHaveScreenshot("workbench-image-maintenance.png", { fullPage: false });
  266 | });
  267 | 
  268 | test("workbench ledger keeps the case list central and details in right tools", async ({ page }, testInfo) => {
  269 |   await installDeterministicApi(page, "admin");
  270 |   await page.goto("/master/ledger?ui_surface=workbench&customer=1");
  271 |   await page.locator(".workbench-management-ui").waitFor();
  272 |   await expect(page.locator(".workbench-management-results .workbench-ledger-table tbody tr")).toHaveCount(ledgerRows.length);
  273 |   await expect(page.locator(".workbench-management-results .workbench-ledger-detail")).toHaveCount(0);
  274 |   await expect(page.locator(".workbench-management-detail .workbench-ledger-side")).toContainText("LED-0001");
  275 |   await expect(page.locator(".workbench-management-detail .workbench-ledger-item-list > article")).toHaveCount(1);
  276 | 
  277 |   const typeSelect = page.locator('.workbench-management-detail details[aria-label="作業類型複選"]');
  278 |   await typeSelect.locator("summary").click();
  279 |   await expect(typeSelect.locator(".ui-multi-select-option")).toHaveCount(2);
  280 |   await expect(typeSelect.locator('.ui-multi-select-option input[type="checkbox"]').first()).toHaveCSS("clip-path", "inset(50%)");
  281 |   await expect(page).toHaveScreenshot("workbench-ledger-multiselect-open.png", { fullPage: false });
  282 |   await typeSelect.locator("summary").click();
  283 | 
  284 |   const overflow = await page.evaluate(() => Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth));
  285 |   expect(overflow, `${testInfo.project.name} ledger must not overflow horizontally`).toBeLessThanOrEqual(1);
  286 |   await expect(page).toHaveScreenshot("workbench-ledger-management.png", { fullPage: false });
```