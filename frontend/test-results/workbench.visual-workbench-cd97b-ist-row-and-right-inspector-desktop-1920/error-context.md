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
    - link "JR Jig Record 回首頁" [ref=e7] [cursor=pointer]:
      - /url: /search
      - generic [ref=e8]: JR
      - generic [ref=e9]:
        - strong [ref=e10]: Jig Record
        - generic [ref=e11]: 回首頁
    - generic [ref=e12]:
      - button "治具收/退料" [ref=e13] [cursor=pointer]
      - button "匯出中心" [ref=e14] [cursor=pointer]
      - button "Workspace UI 教學" [ref=e15] [cursor=pointer]
    - region "UI 介面" [ref=e17]:
      - tablist "切換 Workspace 或 Form UI" [ref=e19]:
        - tab [selected] [ref=e20] [cursor=pointer]:
          - strong [ref=e21]: Workspace UI
        - tab [ref=e22] [cursor=pointer]:
          - strong [ref=e23]: Form UI
      - generic [ref=e26]:
        - generic [ref=e27]: 預設
        - combobox "登入後預設介面" [ref=e28] [cursor=pointer]:
          - option "Workspace UI" [selected]
          - option "Form UI"
    - generic [ref=e29]:
      - generic [ref=e30]:
        - generic [ref=e31]: 視覺測試管理員
        - button "今日收料 32" [ref=e33] [cursor=pointer]:
          - generic [ref=e34]: 今日收料
          - strong [ref=e35]: "32"
        - button "今日退料 8" [ref=e37] [cursor=pointer]:
          - generic [ref=e38]: 今日退料
          - strong [ref=e39]: "8"
        - button "低水位 2" [ref=e41] [cursor=pointer]:
          - generic [ref=e42]: 低水位
          - strong [ref=e43]: "2"
      - generic [ref=e44]:
        - combobox "選擇客戶" [ref=e46]:
          - option "VISUAL - Visual Regression Customer" [selected]
        - button "更多" [ref=e48] [cursor=pointer]
        - button "登出" [ref=e49] [cursor=pointer]
  - main [ref=e50]:
    - region "Workspace UI 系統介面" [ref=e51]:
      - generic [ref=e52]:
        - generic [ref=e53]:
          - article [ref=e54]:
            - generic [ref=e55]: 治具總數
            - strong [ref=e56]: "8"
            - paragraph [ref=e57]: 啟用 8
          - article [ref=e58]:
            - generic [ref=e59]: 機種總數
            - strong [ref=e60]: "6"
            - paragraph [ref=e61]: 啟用 6
          - article [ref=e62]:
            - generic [ref=e63]: 站點總數
            - strong [ref=e64]: "0"
            - paragraph [ref=e65]: 啟用 0
          - article [ref=e66]:
            - generic [ref=e67]: 客戶
            - strong [ref=e68]: "1"
            - paragraph [ref=e69]: 可見 1
          - article [ref=e70]:
            - generic [ref=e71]: 使用者
            - strong [ref=e72]: "0"
            - paragraph [ref=e73]: 啟用 0
        - generic [ref=e74]:
          - generic [ref=e75]:
            - generic [ref=e76]:
              - generic [ref=e77]: 資料維護
              - button "治具資訊" [ref=e78] [cursor=pointer]
              - button "機種資訊" [ref=e79] [cursor=pointer]
              - button "站點資訊" [ref=e80] [cursor=pointer]
            - generic [ref=e81]:
              - generic [ref=e82]: 系統管理
              - button "收退料帳目管理" [ref=e83] [cursor=pointer]
              - button "治具資料品質" [ref=e84] [cursor=pointer]
          - generic [ref=e86]:
            - button "開始新手導覽" [ref=e87] [cursor=pointer]
            - button "治具圖片上傳 檔名對應治具編號，最多 50 張 / 每張小於 5 MB" [ref=e88] [cursor=pointer]:
              - generic [ref=e89]: 治具圖片上傳
              - generic [ref=e90]: 檔名對應治具編號，最多 50 張 / 每張小於 5 MB
            - button "返回搜尋" [ref=e91] [cursor=pointer]
            - button "匯出 CSV" [ref=e92] [cursor=pointer]
            - button "更多操作" [ref=e94] [cursor=pointer]
        - generic [ref=e95]:
          - article [ref=e96]:
            - heading "治具清單" [level=2] [ref=e99]
            - generic [ref=e100]:
              - generic [ref=e101]: 第 1 / 1 頁，共 8 筆
              - generic [ref=e102]:
                - button "上一頁" [disabled] [ref=e103]
                - button "下一頁" [disabled] [ref=e104]
            - generic [ref=e105]:
              - textbox "搜尋治具編號 / 名稱" [ref=e106]
              - generic [ref=e107]:
                - generic [ref=e108]: 狀態
                - group "狀態複選" [ref=e109]:
                  - generic "全部狀態" [ref=e110] [cursor=pointer]
              - button "+ 新增治具" [ref=e114] [cursor=pointer]
            - table [ref=e116]:
              - rowgroup [ref=e117]:
                - row [ref=e118]:
                  - columnheader "治具編號" [ref=e119]
                  - columnheader "治具名稱" [ref=e120]
                  - columnheader "水位" [ref=e121]
                  - columnheader "產線儲位" [ref=e122]
                  - columnheader "部門儲位" [ref=e123]
                  - columnheader "狀態" [ref=e124]
              - rowgroup [ref=e125]:
                - row [ref=e126]:
                  - cell "FX-001" [ref=e127]
                  - cell "Fixture 1" [ref=e128]
                  - cell "2" [ref=e129]
                  - cell "L-1" [ref=e130]
                  - cell "D-01" [ref=e131]
                  - cell "啟用中" [ref=e132]
                - row [ref=e134]:
                  - cell "FX-002" [ref=e135]
                  - cell "Fixture 2" [ref=e136]
                  - cell "2" [ref=e137]
                  - cell "L-2" [ref=e138]
                  - cell "D-01" [ref=e139]
                  - cell "啟用中" [ref=e140]
                - row [ref=e142]:
                  - cell "FX-003" [ref=e143]
                  - cell "Fixture 3" [ref=e144]
                  - cell "2" [ref=e145]
                  - cell "L-3" [ref=e146]
                  - cell "D-01" [ref=e147]
                  - cell "啟用中" [ref=e148]
                - row [ref=e150]:
                  - cell "FX-004" [ref=e151]
                  - cell "Fixture 4" [ref=e152]
                  - cell "2" [ref=e153]
                  - cell "L-4" [ref=e154]
                  - cell "D-01" [ref=e155]
                  - cell "啟用中" [ref=e156]
                - row [ref=e158]:
                  - cell "FX-005" [ref=e159]
                  - cell "Fixture 5" [ref=e160]
                  - cell "2" [ref=e161]
                  - cell "L-5" [ref=e162]
                  - cell "D-01" [ref=e163]
                  - cell "啟用中" [ref=e164]
                - row [ref=e166]:
                  - cell "FX-006" [ref=e167]
                  - cell "Fixture 6" [ref=e168]
                  - cell "2" [ref=e169]
                  - cell "L-6" [ref=e170]
                  - cell "D-01" [ref=e171]
                  - cell "啟用中" [ref=e172]
                - row [ref=e174]:
                  - cell "FX-007" [ref=e175]
                  - cell "Fixture 7" [ref=e176]
                  - cell "2" [ref=e177]
                  - cell "L-7" [ref=e178]
                  - cell "D-01" [ref=e179]
                  - cell "啟用中" [ref=e180]
                - row [ref=e182]:
                  - cell "FX-008" [ref=e183]
                  - cell "Fixture 8" [ref=e184]
                  - cell "2" [ref=e185]
                  - cell "L-8" [ref=e186]
                  - cell "D-01" [ref=e187]
                  - cell "啟用中" [ref=e188]
          - article [ref=e191]:
            - generic [ref=e192]:
              - generic [ref=e193]:
                - heading "治具詳細資料" [level=2] [ref=e194]
                - paragraph [ref=e195]: 請先選擇資料
              - generic [ref=e197]:
                - button "新增" [ref=e198] [cursor=pointer]
                - button "編輯" [disabled] [ref=e199]
            - generic [ref=e201]:
              - generic [ref=e202]: ⌁
              - strong [ref=e203]: 尚未選擇資料
              - paragraph [ref=e204]: 請從左側清單選擇一筆治具，即可先查看摘要；需要修改時再按「編輯」。
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