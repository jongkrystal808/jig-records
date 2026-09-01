# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: workbench.visual.spec.ts >> workbench image maintenance uses a selected list row and right inspector
- Location: tests\visual\workbench.visual.spec.ts:249:1

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.waitFor: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('.workbench-management-ui') to be visible

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
    - button "收／退料" [ref=e17] [cursor=pointer]
    - region "UI 介面" [ref=e19]:
      - tablist "切換 Workspace 或 Form UI" [ref=e21]:
        - tab [selected] [ref=e22] [cursor=pointer]:
          - strong [ref=e23]: Workspace UI
        - tab [ref=e24] [cursor=pointer]:
          - strong [ref=e25]: Form UI
      - generic [ref=e28]:
        - generic [ref=e29]: 預設
        - combobox "登入後預設介面" [ref=e30] [cursor=pointer]:
          - option "Workspace UI" [selected]
          - option "Form UI"
  - main [ref=e31]:
    - region "Workspace UI 系統介面" [ref=e32]:
      - generic [ref=e33]:
        - generic [ref=e34]:
          - article [ref=e35]:
            - generic [ref=e36]: 治具總數
            - strong [ref=e37]: "8"
            - paragraph [ref=e38]: 啟用 8
          - article [ref=e39]:
            - generic [ref=e40]: 機種總數
            - strong [ref=e41]: "6"
            - paragraph [ref=e42]: 啟用 6
          - article [ref=e43]:
            - generic [ref=e44]: 站點總數
            - strong [ref=e45]: "0"
            - paragraph [ref=e46]: 啟用 0
          - article [ref=e47]:
            - generic [ref=e48]: 客戶
            - strong [ref=e49]: "1"
            - paragraph [ref=e50]: 可見 1
          - article [ref=e51]:
            - generic [ref=e52]: 使用者
            - strong [ref=e53]: "0"
            - paragraph [ref=e54]: 啟用 0
        - generic [ref=e55]:
          - generic [ref=e56]:
            - generic [ref=e57]:
              - generic [ref=e58]: 資料維護
              - button "治具資訊" [ref=e59] [cursor=pointer]
              - button "機種資訊" [ref=e60] [cursor=pointer]
              - button "站點資訊" [ref=e61] [cursor=pointer]
            - generic [ref=e62]:
              - generic [ref=e63]: 系統管理
              - button "收退料帳目管理" [ref=e64] [cursor=pointer]
              - button "治具資料品質" [ref=e65] [cursor=pointer]
          - generic [ref=e67]:
            - button "開始新手導覽" [ref=e68] [cursor=pointer]
            - button "治具圖片上傳 檔名對應治具編號，最多 50 張 / 每張小於 5 MB" [ref=e69] [cursor=pointer]:
              - generic [ref=e70]: 治具圖片上傳
              - generic [ref=e71]: 檔名對應治具編號，最多 50 張 / 每張小於 5 MB
            - button "返回搜尋" [ref=e72] [cursor=pointer]
            - button "匯出 CSV" [ref=e73] [cursor=pointer]
            - button "更多操作" [ref=e75] [cursor=pointer]
        - article [ref=e77]:
          - heading "治具清單" [level=2] [ref=e80]
          - generic [ref=e81]:
            - generic [ref=e82]: 第 1 / 1 頁，共 8 筆
            - generic [ref=e83]:
              - button "上一頁" [disabled] [ref=e84]
              - button "下一頁" [disabled] [ref=e85]
          - generic [ref=e86]:
            - textbox "搜尋治具編號 / 名稱" [ref=e87]
            - generic [ref=e88]:
              - generic [ref=e89]: 狀態
              - group "狀態複選" [ref=e90]:
                - generic "全部狀態" [ref=e91] [cursor=pointer]
            - button "+ 新增治具" [ref=e95] [cursor=pointer]
          - table [ref=e97]:
            - rowgroup [ref=e98]:
              - row [ref=e99]:
                - columnheader "治具編號" [ref=e100]
                - columnheader "治具名稱" [ref=e101]
                - columnheader "水位" [ref=e102]
                - columnheader "產線儲位" [ref=e103]
                - columnheader "部門儲位" [ref=e104]
                - columnheader "狀態" [ref=e105]
            - rowgroup [ref=e106]:
              - row [ref=e107]:
                - cell "FX-001" [ref=e108]
                - cell "Fixture 1" [ref=e109]
                - cell "2" [ref=e110]
                - cell "L-1" [ref=e111]
                - cell "D-01" [ref=e112]
                - cell "啟用中" [ref=e113]
              - row [ref=e115]:
                - cell "FX-002" [ref=e116]
                - cell "Fixture 2" [ref=e117]
                - cell "2" [ref=e118]
                - cell "L-2" [ref=e119]
                - cell "D-01" [ref=e120]
                - cell "啟用中" [ref=e121]
              - row [ref=e123]:
                - cell "FX-003" [ref=e124]
                - cell "Fixture 3" [ref=e125]
                - cell "2" [ref=e126]
                - cell "L-3" [ref=e127]
                - cell "D-01" [ref=e128]
                - cell "啟用中" [ref=e129]
              - row [ref=e131]:
                - cell "FX-004" [ref=e132]
                - cell "Fixture 4" [ref=e133]
                - cell "2" [ref=e134]
                - cell "L-4" [ref=e135]
                - cell "D-01" [ref=e136]
                - cell "啟用中" [ref=e137]
              - row [ref=e139]:
                - cell "FX-005" [ref=e140]
                - cell "Fixture 5" [ref=e141]
                - cell "2" [ref=e142]
                - cell "L-5" [ref=e143]
                - cell "D-01" [ref=e144]
                - cell "啟用中" [ref=e145]
              - row [ref=e147]:
                - cell "FX-006" [ref=e148]
                - cell "Fixture 6" [ref=e149]
                - cell "2" [ref=e150]
                - cell "L-6" [ref=e151]
                - cell "D-01" [ref=e152]
                - cell "啟用中" [ref=e153]
              - row [ref=e155]:
                - cell "FX-007" [ref=e156]
                - cell "Fixture 7" [ref=e157]
                - cell "2" [ref=e158]
                - cell "L-7" [ref=e159]
                - cell "D-01" [ref=e160]
                - cell "啟用中" [ref=e161]
              - row [ref=e163]:
                - cell "FX-008" [ref=e164]
                - cell "Fixture 8" [ref=e165]
                - cell "2" [ref=e166]
                - cell "L-8" [ref=e167]
                - cell "D-01" [ref=e168]
                - cell "啟用中" [ref=e169]
```

# Test source

```ts
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
> 252 |   await page.locator(".workbench-management-ui").waitFor();
      |                                                  ^ Error: locator.waitFor: Test timeout of 30000ms exceeded.
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