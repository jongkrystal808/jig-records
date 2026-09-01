# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: workbench.visual.spec.ts >> workbench keeps fixture and identifier lookup as explicit URL-backed modes
- Location: tests\visual\workbench.visual.spec.ts:206:1

# Error details

```
Error: expect(page).toHaveScreenshot(expected) failed

  61536 pixels (ratio 0.07 of all image pixels) are different.

  Snapshot: workbench-identifier-search.png

Call log:
  - Expect "toHaveScreenshot(workbench-identifier-search.png)" with timeout 5000ms
    - verifying given screenshot expectation
  - taking page screenshot
    - disabled all CSS animations
  - waiting for fonts to load...
  - fonts loaded
  - 61536 pixels (ratio 0.07 of all image pixels) are different.
  - waiting 100ms before taking screenshot
  - taking page screenshot
    - disabled all CSS animations
  - waiting for fonts to load...
  - fonts loaded
  - captured a stable screenshot
  - 61536 pixels (ratio 0.07 of all image pixels) are different.

```

# Page snapshot

```yaml
- generic [ref=e4]:
  - banner [ref=e5]:
    - generic [ref=e6]:
      - button "選單" [ref=e7] [cursor=pointer]:
        - generic [ref=e8]: ☰
      - link "JR Jig Record 回首頁" [ref=e10] [cursor=pointer]:
        - /url: /search
        - generic [ref=e11]: JR
        - generic [ref=e12]:
          - strong [ref=e13]: Jig Record
          - generic [ref=e14]: 回首頁
      - generic [ref=e15]: VISUAL
    - region "UI 介面" [ref=e17]:
      - tablist "切換 Workspace 或 Form UI" [ref=e19]:
        - tab [selected] [ref=e20] [cursor=pointer]:
          - strong [ref=e21]: Workspace UI
        - tab [ref=e22] [cursor=pointer]:
          - strong [ref=e23]: Form UI
  - main [ref=e24]:
    - region "Workspace UI 系統介面" [ref=e25]:
      - region "Workspace UI 快速作業" [ref=e26]:
        - generic [ref=e27]:
          - complementary "工作台操作區" [ref=e28]:
            - generic [ref=e30]:
              - generic [ref=e31]: 快速作業
              - heading "查詢治具" [level=2] [ref=e32]
            - tablist "工作台作業模式" [ref=e33]:
              - tab "收料／退料" [ref=e34] [cursor=pointer]
              - tab "查詢治具" [selected] [ref=e35] [cursor=pointer]
              - tab "查詢機種" [ref=e36] [cursor=pointer]
              - tab "收／退料總檢視" [ref=e37] [cursor=pointer]
            - generic [ref=e38]:
              - generic "治具搜尋類型" [ref=e39]:
                - button "治具資料" [ref=e40] [cursor=pointer]
                - button "Datecode／序號" [pressed] [ref=e41] [cursor=pointer]
              - generic [ref=e42]:
                - generic [ref=e43]: Datecode／序號
                - textbox "Datecode／序號" [active] [ref=e44]:
                  - /placeholder: 只輸入 Datecode／序號，例如 2204
                  - text: "2204"
              - button "查詢 Datecode／序號" [ref=e45] [cursor=pointer]
            - region "最近收退料治具" [ref=e46]:
              - generic [ref=e47]:
                - heading "最近收退料治具" [level=3] [ref=e48]
                - generic [ref=e49]: 6 筆
              - generic [ref=e50]:
                - button "退料 FX-001 2200 1 pcs 2026-08-25" [ref=e51] [cursor=pointer]:
                  - generic [ref=e53]:
                    - strong [ref=e54]: FX-001
                    - generic [ref=e55]: 退料 · 自購 · Operator A
                    - generic [ref=e56]: 2200 · 2026-08-25
                  - generic [ref=e57]: 1 pcs
                - button "收料 FX-002 2201 2 pcs 2026-08-24" [ref=e58] [cursor=pointer]:
                  - generic [ref=e60]:
                    - strong [ref=e61]: FX-002
                    - generic [ref=e62]: 收料 · 客供 · Operator B
                    - generic [ref=e63]: 2201 · 2026-08-24
                  - generic [ref=e64]: 2 pcs
                - button "收料 FX-003 2202 3 pcs 2026-08-23" [ref=e65] [cursor=pointer]:
                  - generic [ref=e67]:
                    - strong [ref=e68]: FX-003
                    - generic [ref=e69]: 收料 · 客供 · Operator A
                    - generic [ref=e70]: 2202 · 2026-08-23
                  - generic [ref=e71]: 3 pcs
                - button "收料 FX-004 2203 4 pcs 2026-08-22" [ref=e72] [cursor=pointer]:
                  - generic [ref=e74]:
                    - strong [ref=e75]: FX-004
                    - generic [ref=e76]: 收料 · 自購 · Operator B
                    - generic [ref=e77]: 2203 · 2026-08-22
                  - generic [ref=e78]: 4 pcs
                - button "退料 FX-005 2204 5 pcs 2026-08-21" [ref=e79] [cursor=pointer]:
                  - generic [ref=e81]:
                    - strong [ref=e82]: FX-005
                    - generic [ref=e83]: 退料 · 客供 · Operator A
                    - generic [ref=e84]: 2204 · 2026-08-21
                  - generic [ref=e85]: 5 pcs
                - button "收料 FX-006 2205 6 pcs 2026-08-25" [ref=e86] [cursor=pointer]:
                  - generic [ref=e88]:
                    - strong [ref=e89]: FX-006
                    - generic [ref=e90]: 收料 · 客供 · Operator B
                    - generic [ref=e91]: 2205 · 2026-08-25
                  - generic [ref=e92]: 6 pcs
          - main [ref=e93]:
            - generic [ref=e94]:
              - generic [ref=e95]:
                - generic [ref=e96]: 查詢結果
                - heading "FX-001 · Fixture 1" [level=2] [ref=e97]
              - generic [ref=e98]: VISUAL
            - generic [ref=e99]:
              - article [ref=e100]:
                - generic [ref=e101]: 現有治具
                - strong [ref=e102]: 12 pcs
              - article [ref=e103]:
                - generic [ref=e104]: 客供／自購
                - strong [ref=e105]: 7／5
              - article [ref=e106]:
                - generic [ref=e107]: 庫存狀態
                - strong [ref=e108]: 正常
            - generic [ref=e109]:
              - generic [ref=e110]:
                - heading "Datecode／流水號庫存" [level=3] [ref=e111]
                - generic [ref=e112]: 1 筆
              - table [ref=e114]:
                - rowgroup [ref=e115]:
                  - row [ref=e116]:
                    - columnheader "識別碼" [ref=e117]
                    - columnheader "客供" [ref=e118]
                    - columnheader "自購" [ref=e119]
                    - columnheader "總數" [ref=e120]
                - rowgroup [ref=e121]:
                  - row [ref=e122]:
                    - cell "2204" [ref=e123]
                    - cell "7" [ref=e124]
                    - cell "5" [ref=e125]
                    - cell [ref=e126]:
                      - strong [ref=e127]: 12 pcs
            - generic [ref=e128]:
              - heading "收退料記錄" [level=3] [ref=e130]
              - table [ref=e132]:
                - rowgroup [ref=e133]:
                  - row [ref=e134]:
                    - columnheader "日期" [ref=e135]
                    - columnheader "類型" [ref=e136]
                    - columnheader "單號" [ref=e137]
                    - columnheader "識別碼" [ref=e138]
                    - columnheader "數量" [ref=e139]
                - rowgroup [ref=e140]:
                  - row [ref=e141]:
                    - cell "尚無收退料記錄。" [ref=e142]
          - complementary "治具與機種詳情" [ref=e143]:
            - generic [ref=e145]:
              - generic [ref=e146]: 現場資訊
              - heading "治具詳情" [level=2] [ref=e147]
            - generic [ref=e149]:
              - generic [ref=e150]: IMAGE
              - paragraph [ref=e151]: 目前沒有治具圖片
            - generic [ref=e152]:
              - generic [ref=e153]:
                - term [ref=e154]: 治具編號
                - definition [ref=e155]: FX-001
              - generic [ref=e156]:
                - term [ref=e157]: 治具名稱
                - definition [ref=e158]: Fixture 1
              - generic [ref=e159]:
                - term [ref=e160]: 線邊儲位
                - definition [ref=e161]: L-1
              - generic [ref=e162]:
                - term [ref=e163]: 部門儲位
                - definition [ref=e164]: D-01
            - generic [ref=e165]:
              - generic [ref=e166]:
                - heading "使用機種與站點" [level=3] [ref=e167]
                - generic [ref=e168]: "0"
              - paragraph [ref=e169]: 尚未配置使用機種。
```

# Test source

```ts
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
  186 |   await expect(page.locator('.workbench-mode-tabs [role="tab"]').last()).toHaveText("管理後臺");
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
> 220 |   await expect(page).toHaveScreenshot("workbench-identifier-search.png", { fullPage: false });
      |                      ^ Error: expect(page).toHaveScreenshot(expected) failed
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
  287 | 
  288 |   await page.locator(".workbench-filter-toggle").click();
  289 |   await expect(page.locator(".workbench-management-detail .workbench-admin-filter-grid")).toBeHidden();
  290 |   await expect(page.locator(".workbench-management-detail .workbench-ledger-side")).toBeVisible();
  291 |   await expect(page).toHaveScreenshot("workbench-ledger-management-collapsed.png", { fullPage: false });
  292 | });
  293 | 
```