# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: workbench.visual.spec.ts >> workbench ledger keeps the case list central and details in right tools
- Location: tests\visual\workbench.visual.spec.ts:268:1

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
            - button "返回搜尋" [ref=e88] [cursor=pointer]
            - button "匯出 CSV" [disabled] [ref=e89]
            - button "更多操作" [ref=e91] [cursor=pointer]
        - generic [ref=e92]:
          - article [ref=e93]:
            - generic [ref=e95]:
              - heading "收退料帳目管理" [level=2] [ref=e96]
              - paragraph [ref=e97]: 共 12 筆案件
            - generic [ref=e98]:
              - generic [ref=e99]: 第 1 / 1 頁，共 12 筆案件
              - generic [ref=e100]:
                - generic [ref=e101]:
                  - generic [ref=e102]: 每頁
                  - combobox "每頁" [ref=e103]:
                    - option "12" [selected]
                    - option "25"
                    - option "50"
                - button "上一頁" [disabled] [ref=e104]
                - button "下一頁" [disabled] [ref=e105]
            - generic [ref=e106]:
              - textbox "搜尋單號" [ref=e107]
              - textbox "搜尋操作人" [ref=e108]
              - textbox "搜尋治具編號" [ref=e109]
              - generic [ref=e110]:
                - generic [ref=e111]: 類型
                - group "類型複選" [ref=e112]:
                  - generic "全部帳目" [ref=e113] [cursor=pointer]
            - table [ref=e118]:
              - rowgroup [ref=e119]:
                - row [ref=e120]:
                  - columnheader "單號" [ref=e121]
                  - columnheader "類型" [ref=e122]
                  - columnheader "日期" [ref=e123]
                  - columnheader "操作人" [ref=e124]
                  - columnheader "筆數" [ref=e125]
                  - columnheader "總數量" [ref=e126]
              - rowgroup [ref=e127]:
                - row [selected] [ref=e128]:
                  - cell "LED-0001" [ref=e129]
                  - cell "退料" [ref=e130]
                  - cell "2026-08-25" [ref=e132]
                  - cell "Operator A" [ref=e133]
                  - cell "1" [ref=e134]
                  - cell "1" [ref=e135]
                - row [ref=e136]:
                  - cell "LED-0002" [ref=e137]
                  - cell "收料" [ref=e138]
                  - cell "2026-08-24" [ref=e140]
                  - cell "Operator B" [ref=e141]
                  - cell "1" [ref=e142]
                  - cell "2" [ref=e143]
                - row [ref=e144]:
                  - cell "LED-0003" [ref=e145]
                  - cell "收料" [ref=e146]
                  - cell "2026-08-23" [ref=e148]
                  - cell "Operator A" [ref=e149]
                  - cell "1" [ref=e150]
                  - cell "3" [ref=e151]
                - row [ref=e152]:
                  - cell "LED-0004" [ref=e153]
                  - cell "收料" [ref=e154]
                  - cell "2026-08-22" [ref=e156]
                  - cell "Operator B" [ref=e157]
                  - cell "1" [ref=e158]
                  - cell "4" [ref=e159]
                - row [ref=e160]:
                  - cell "LED-0005" [ref=e161]
                  - cell "退料" [ref=e162]
                  - cell "2026-08-21" [ref=e164]
                  - cell "Operator A" [ref=e165]
                  - cell "1" [ref=e166]
                  - cell "5" [ref=e167]
                - row [ref=e168]:
                  - cell "LED-0006" [ref=e169]
                  - cell "收料" [ref=e170]
                  - cell "2026-08-25" [ref=e172]
                  - cell "Operator B" [ref=e173]
                  - cell "1" [ref=e174]
                  - cell "1" [ref=e175]
                - row [ref=e176]:
                  - cell "LED-0007" [ref=e177]
                  - cell "收料" [ref=e178]
                  - cell "2026-08-24" [ref=e180]
                  - cell "Operator A" [ref=e181]
                  - cell "1" [ref=e182]
                  - cell "2" [ref=e183]
                - row [ref=e184]:
                  - cell "LED-0008" [ref=e185]
                  - cell "收料" [ref=e186]
                  - cell "2026-08-23" [ref=e188]
                  - cell "Operator B" [ref=e189]
                  - cell "1" [ref=e190]
                  - cell "3" [ref=e191]
                - row [ref=e192]:
                  - cell "LED-0009" [ref=e193]
                  - cell "退料" [ref=e194]
                  - cell "2026-08-22" [ref=e196]
                  - cell "Operator A" [ref=e197]
                  - cell "1" [ref=e198]
                  - cell "4" [ref=e199]
                - row [ref=e200]:
                  - cell "LED-0010" [ref=e201]
                  - cell "收料" [ref=e202]
                  - cell "2026-08-21" [ref=e204]
                  - cell "Operator B" [ref=e205]
                  - cell "1" [ref=e206]
                  - cell "5" [ref=e207]
                - row [ref=e208]:
                  - cell "LED-0011" [ref=e209]
                  - cell "收料" [ref=e210]
                  - cell "2026-08-25" [ref=e212]
                  - cell "Operator A" [ref=e213]
                  - cell "1" [ref=e214]
                  - cell "1" [ref=e215]
                - row [ref=e216]:
                  - cell "LED-0012" [ref=e217]
                  - cell "收料" [ref=e218]
                  - cell "2026-08-24" [ref=e220]
                  - cell "Operator B" [ref=e221]
                  - cell "1" [ref=e222]
                  - cell "2" [ref=e223]
          - article [ref=e224]:
            - generic [ref=e225]:
              - generic [ref=e226]:
                - heading "案件詳細" [level=2] [ref=e227]
                - paragraph [ref=e228]: LED-0001
              - generic [ref=e230]:
                - button "重載" [ref=e231] [cursor=pointer]
                - button "一鍵重算" [ref=e232] [cursor=pointer]
                - button "撤回此案件" [ref=e233] [cursor=pointer]
            - generic [ref=e234]:
              - generic [ref=e235]:
                - generic [ref=e236]: 類型
                - strong [ref=e237]: 退料
              - generic [ref=e238]:
                - generic [ref=e239]: 日期
                - strong [ref=e240]: 2026-08-25
              - generic [ref=e241]:
                - generic [ref=e242]: 操作人
                - strong [ref=e243]: Operator A
              - generic [ref=e244]:
                - generic [ref=e245]: 明細筆數
                - strong [ref=e246]: "1"
              - generic [ref=e247]:
                - generic [ref=e248]: 總數量
                - strong [ref=e249]: "1"
            - generic [ref=e250]:
              - generic [ref=e251]: 案件備註
              - textbox "案件備註" [disabled] [ref=e252]: 工作台帳目檢視測試
            - table [ref=e254]:
              - rowgroup [ref=e255]:
                - row [ref=e256]:
                  - columnheader "治具 ID" [ref=e257]
                  - columnheader "治具編號" [ref=e258]
                  - columnheader "識別碼" [ref=e259]
                  - columnheader "數量" [ref=e260]
                  - columnheader "歸屬" [ref=e261]
                  - columnheader "備註" [ref=e262]
              - rowgroup [ref=e263]:
                - row [ref=e264]:
                  - cell "101" [ref=e265]
                  - cell "FX-001" [ref=e266]
                  - cell "2200" [ref=e267]
                  - cell "1" [ref=e268]
                  - cell "自購" [ref=e269]
                  - cell "首筆案件治具明細" [ref=e270]
```

# Test source

```ts
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
> 271 |   await page.locator(".workbench-management-ui").waitFor();
      |                                                  ^ Error: locator.waitFor: Test timeout of 30000ms exceeded.
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