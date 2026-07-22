# Frontend Map

這份文件回答三件事：

- 每個頁面 / 主要操作現在對應哪個 page 與拆分元件
- 要改畫面、互動或 API 時應該進哪個檔案
- 目前哪些共用元件 / 共用 CSS / API client 已經抽出

## 入口檔與全域骨架

- `frontend/src/main.ts`
  - Vue 啟動入口
  - 掛載 `router` 與 `App.vue`

- `frontend/src/router/index.ts`
  - 路由表
  - `/search` -> `SearchWorkspacePage.vue`
  - `/inventory` -> `InventoryPage.vue`
  - `/inventory/overview` -> `InventoryPage.vue`
  - `/master` -> redirect `/master/fixtures`
- `/master/fixtures` -> `MasterPage.vue`
- `/master/models` -> `MasterPage.vue`
- `/master/stations` -> `MasterPage.vue`
- `/master/customers` -> `MasterPage.vue`
- `/master/users` -> `MasterPage.vue`
- `/master/ledger` -> `MasterPage.vue`
- `/master/quality` -> `MasterPage.vue`
  - `/production` -> `ProductionPage.vue`
  - `/production/mapping` -> `ProductionPage.vue`
  - `/production/requirements` -> `ProductionPage.vue`
  - guest 進 `/master` 會被導回 `/search`

- `frontend/src/App.vue`
  - 全域 shell 協調器
  - 只保留 session、route、onboarding、release notice、topbar stats refresh、global modal open state
  - 不再直接承接整塊登入頁、topbar、drawer、toast template
  - 協調 onboarding 分類選單與 guided tour 播放
  - release notice 同版本只顯示一次

- `frontend/src/components/app/AppAuthScreen.vue`
  - 登入畫面
  - 訪客入口

- `frontend/src/components/app/AppTopbar.vue`
  - 頂部導覽列
  - customer picker
  - 今日收料 / 退料 / 低水位摘要

- `frontend/src/components/app/AppMobileDrawer.vue`
  - 手機版抽屜選單

- `frontend/src/components/app/AppGlobalModals.vue`
  - 全域 `收 / 退料` modal
  - 全域 `收退料資訊匯出` modal

- `frontend/src/components/app/AppReleaseNoticeModal.vue`
  - 版本公告 modal

- `frontend/src/components/app/AppToastStack.vue`
  - 全域 toast 顯示

- `frontend/src/appState.ts`
  - 全域登入 session
  - customer 選擇
  - onboarding 狀態
  - onboarding 分類選擇狀態

- `frontend/src/onboarding.ts`
  - 新手導覽 flow 定義
  - 依頁面 / tab 分類的教學內容
  - 每一步對應 route / `data-tour` target / 文案 / 方向

- `frontend/src/components/common/OnboardingFlowPicker.vue`
  - 新手教學分類選單

- `frontend/src/releaseNotice.ts`
  - 版本公告內容
  - `versionId` / 顯示標題 / 摘要 / highlight 文案
  - bump `versionId` 才會重新顯示新版提示

- `frontend/src/toastState.ts`
  - 全域 toast 狀態

- `frontend/src/styles.css`
  - 全域 CSS 變數
  - 共用按鈕、panel、modal、table、chip、summary、state utility

## API Client 結構

- `frontend/src/api.ts`
  - 對外穩定入口
  - 保持 `import { api } from "@/api"` 不變
  - 只做 barrel 聚合

- `frontend/src/api/core.ts`
  - transport
  - headers
  - query string
  - response / error handling

- `frontend/src/api/authClient.ts`
  - auth / user 相關 API

- `frontend/src/api/masterClient.ts`
  - fixture / model / station / customer 相關 API

- `frontend/src/api/inventoryClient.ts`
  - stock / alert / receipt / return / transaction / export 相關 API

- `frontend/src/api/productionClient.ts`
  - model-station / fixture requirement / capacity / model query

- `frontend/src/api/searchClient.ts`
  - global search

- `frontend/src/api/auditClient.ts`
  - audit log

- `frontend/src/api/mediaClient.ts`
  - fixture image URL 與 blob fetch

## 共用元件 / 共用工具

- `frontend/src/components/common/GuidedTour.vue`
  - 全域導覽浮層
  - spotlight 目標高亮
  - route-aware step 流程
  - 依實際卡片高度定位，避免固定高度造成偏移

- `frontend/src/components/common/InlineSpinner.vue`
  - 小型 inline loading indicator

- `frontend/src/components/UiFormActions.vue`
  - 新增 / 編輯 / 取消 / 停用動作列

- `frontend/src/components/UiSectionHeader.vue`
  - panel 標題列

- `frontend/src/components/UiSplitDetailLayout.vue`
  - summary rail + detail scroll 的共用殼層

- `frontend/src/components/UiStatusPill.vue`
  - 主資料 / 狀態標籤顯示

- `frontend/src/components/UiSummaryCards.vue`
  - 摘要卡片列

- `frontend/src/utils/date.ts`
  - 本地日期 key / 顯示輔助

- `frontend/src/utils/apiError.ts`
  - API error message 解析

- `frontend/src/utils/display.ts`
  - fallback text / ownership label / stock status label 等顯示工具

- `frontend/src/utils/identifier.ts`
  - 前端 `identifier` 共用規則
  - 短純數字補零
  - legacy 值原樣保留
  - 保留 query helper，避免 UI 端再次手寫同語意判斷

## 全域流程 API 對應

### `frontend/src/App.vue`

- 登入按鈕
  - `api.login`

- 訪客入口按鈕
  - `api.guestEntry`

- 初始化 / session 恢復後載入 customer
  - `api.listCustomers`

- customer 切換後更新 topbar summary
  - `api.listAlerts`
  - `api.listTransactions`

- 全域收退料 modal
  - `AppGlobalModals.vue`
  - 內部共用 `BatchImportPanel.vue`

- 全域收退料匯出 modal
  - `AppGlobalModals.vue`
  - 內部共用 `InventoryExportPanel.vue`

- 版本公告 modal
  - `AppReleaseNoticeModal.vue`
  - 文案定義在 `releaseNotice.ts`

### 改全域畫面時去哪裡

- 改 session 恢復、route 轉向、onboarding 狀態、topbar refresh orchestration
  - `frontend/src/App.vue`

- 改登入卡片
  - `frontend/src/components/app/AppAuthScreen.vue`

- 改頂部導覽、customer picker、today summary
  - `frontend/src/components/app/AppTopbar.vue`

- 改手機版選單
  - `frontend/src/components/app/AppMobileDrawer.vue`

- 改全域收退料 / 匯出 modal
  - `frontend/src/components/app/AppGlobalModals.vue`

- 改版本公告顯示條件 / 文案
  - `frontend/src/App.vue`
  - `frontend/src/components/app/AppReleaseNoticeModal.vue`
  - `frontend/src/releaseNotice.ts`
  - `frontend/src/App.vue` 負責「同版本只顯示一次」的開關條件

- 改全域 toast UI
  - `frontend/src/components/app/AppToastStack.vue`
  - 狀態邏輯在 `frontend/src/toastState.ts`

## 查詢頁

- page：`frontend/src/pages/SearchWorkspacePage.vue`
- 子元件：
  - `frontend/src/components/search/SearchHeroSection.vue`
  - `frontend/src/components/search/SearchResultPanel.vue`
  - `frontend/src/components/search/FixtureInfoPanel.vue`
  - `frontend/src/components/search/ModelInfoPanel.vue`
  - `frontend/src/components/search/FixtureEditForm.vue`
  - `frontend/src/components/search/ModelEditForm.vue`

### 目前責任分工

- `SearchWorkspacePage.vue`
  - mode / query state
  - route query handoff (`mode` / `q`)
  - paginated global search state
  - load more / selected result state
    - 最近收 / 退料治具快捷入口資料整理
  - fixture / model result 組裝與排序承接
  - fixture / model context lazy fetch
  - fixture 完整交易歷史的額外延遲載入
  - 開啟 onboarding 分類選單

- `SearchHeroSection.vue`
  - 查詢首頁 hero shell
  - mode switch
  - smart hints
  - smart hints 收合 / 展開
  - 最近收 / 退料治具快捷入口
  - onboarding 入口

- `SearchResultPanel.vue`
  - 查詢結果外層殼層

- `FixtureInfoPanel.vue`
  - 治具 detail
  - 圖片、identifier stock、transaction context

- `ModelInfoPanel.vue`
  - 機種 detail
  - station / fixture requirement / stock context

### 主要功能

- 雙模式查詢：`治具` / `機種`
- fixture detail
- model detail
- fixture 圖片預覽
- datecode/編號庫存摘要
- transaction context
- 最近收 / 退料治具快捷入口點擊後，搜尋完成會自動捲動到結果區
- 區塊 chip 顯示切換與 localStorage 記憶
- 最近收 / 退料治具快捷入口
- 首頁固定「開始新手教學」入口

### API 對應

- 初始化載入
  - `api.listFixtures`
  - `api.listStock`
  - `api.listTransactions`
  - `api.listIdentifierStockSummary`
  - `api.listModels`
  - `api.listStations`
  - `api.listFixtureRequirements`

- fixture / 一般查詢
  - `api.globalSearch`

- model query
  - `api.getModelQuery`

- fixture 圖片
  - `fixtureImageUrlByCode`
  - `fetchFixtureImageObjectUrl`
  - `GET /api/v2/master/fixtures/{fixture_code}/image`

### 改查詢頁時去哪裡

- 改查詢 state、route query handoff、load more、快捷入口資料來源、selected context 載入、section persistence、搜尋後結果區自動定位
  - `frontend/src/pages/SearchWorkspacePage.vue`

- 改首頁 hero、快捷入口、onboarding 按鈕
  - `frontend/src/components/search/SearchHeroSection.vue`

- 改查詢結果外殼與版面
  - `frontend/src/components/search/SearchResultPanel.vue`

- 改查詢 API contract 或 context 載入方法
  - `frontend/src/api/searchClient.ts`
  - `frontend/src/types.ts`

- 改治具 / 機種 detail
  - `frontend/src/components/search/FixtureInfoPanel.vue`
  - `frontend/src/components/search/ModelInfoPanel.vue`

- 改 fixture 圖片 URL 或載入策略
  - `frontend/src/api/mediaClient.ts`
  - `frontend/src/pages/SearchWorkspacePage.vue`

## 收退料頁

- page：`frontend/src/pages/InventoryPage.vue`
- 子元件：
  - `frontend/src/components/inventory/InventoryOperationBoard.vue`
  - `frontend/src/components/inventory/InventoryOverviewPanel.vue`
  - `frontend/src/components/inventory/BatchImportPanel.vue`
  - `frontend/src/components/inventory/InventoryExportPanel.vue`

### 目前責任分工

- `InventoryPage.vue`
  - 初始化資料載入
  - route mode 切換
  - operation metrics / overview filters / export orchestration

- `InventoryOperationBoard.vue`
  - 收料 / 退料操作視圖
  - KPI cards
  - 嵌入 `BatchImportPanel.vue`

- `InventoryOverviewPanel.vue`
  - overview 篩選
  - 交易表格
  - 匯出入口

- `BatchImportPanel.vue`
  - 批次貼上解析
  - 重複交易確認提示
  - 貼上欄支援手動輸入 `Tab` 分隔資料
  - 新治具建立
  - 相似治具確認 / 替換
  - `目前庫存` / `交易後庫存` 預覽
  - 同批重複 `治具 + datecode/編號` 的逐列累計庫存預覽
  - tutorial sandbox 試跑
  - 寫入前 `identifier` 正規化改走 `frontend/src/utils/identifier.ts`
  - 前端對使用者顯示 `datecode/編號` 文案

- `InventoryExportPanel.vue`
  - 報表類型 / 匯出範圍選擇
  - preview
  - `xlsx` / `txt` 匯出
  - `identifier` 查詢輸入與相容文案
  - UI 顯示名稱改為 `datecode/編號`

### 路由模式

- `/inventory`
  - operation-first

- `/inventory/overview`
  - overview-first

### API 對應

- 初始化載入
  - `api.listFixtures`
  - `api.listStock`
  - `api.listAlerts`
  - `api.listTransactions`

- 送出收料
  - `api.createReceipt`
  - `api.createReceiptWithOptions`

- 送出退料
  - `api.createReturn`
  - `api.createReturnWithOptions`

- overview 查詢
  - `api.listTransactions`

- overview 匯出 CSV
  - `api.exportTransactionsCsv`

- 報表 preview / 匯出
  - `api.previewTransactionReportExport`
  - `api.exportTransactionReport`

- 批次貼上匯入內的新治具建立
  - `api.createFixture`

- 批次預覽庫存資料
  - `api.listStock`
  - `api.listIdentifierStockSummary`

### 改收退料頁時去哪裡

- 改 page route mode、data refresh、overview filter state
  - `frontend/src/pages/InventoryPage.vue`

- 改操作頁 KPI / frame / layout
  - `frontend/src/components/inventory/InventoryOperationBoard.vue`

- 改 overview 篩選欄位與交易表格
  - `frontend/src/components/inventory/InventoryOverviewPanel.vue`

- 改批次貼上解析規則 / `Tab` 鍵輸入行為 / 相似治具比對 / 匯入預覽表 / 重複交易確認提示 / tutorial mode
  - `frontend/src/components/inventory/BatchImportPanel.vue`
  - preview 純計算 helper：`frontend/src/utils/inventoryBatchPreview.ts`

- 改匯出面板互動 / preview / radio 選擇樣式
  - `frontend/src/components/inventory/InventoryExportPanel.vue`
  - `frontend/src/api/inventoryClient.ts`

## 資料維護頁

- page：`frontend/src/pages/MasterPage.vue`
- 子元件：
  - `frontend/src/components/master/MasterListPanel.vue`
  - `frontend/src/components/master/MasterDetailPanel.vue`
  - `frontend/src/components/master/FixtureQualityPanel.vue`

### 目前責任分工

- `MasterPage.vue`
  - route-driven tab state
  - 初始化載入
  - CRUD orchestration
  - import / export / template download
  - summary metrics
  - admin 治具資料品質報表
  - admin 主資料永久刪除 dialog state 與送出 orchestration
  - 刪除完成後重載 fixtures / quality / models / stations 並清除選取

- `MasterListPanel.vue`
  - tab 清單
  - 搜尋 / 篩選
  - 分頁列表
  - 頁數提示 / 總筆數 / 翻頁動作固定在表格上方

- `MasterDetailPanel.vue`
  - fixture / model / station / customer / user detail form
  - admin-only 主資料永久刪除入口（治具 / 機種 / 站點）
  - 透過 props 將刪除請求交回 `MasterPage.vue`

### 主要功能

- fixture / model / station / customer / user / ledger / quality tab
- tab 清單分頁
- 狀態篩選 / 關鍵字搜尋
- fixture 維護 `responsible_user_id` / `min_stock_qty` / `storage_location`
- customer 維護 `assigned_user_ids`
- user 建立 / 更新 / 停用 / 重設密碼
- fixture / model / station CSV 匯入匯出 / 範本下載
- 從資料維護頁重新啟動新手導覽

- admin 可永久刪除治具，並選擇保留或刪除該治具的收/退料紀錄
- admin 也可永久刪除機種與站點，刪除前會提示關聯 `mapping / requirement / capacity summary` 將一併刪除
- 保留歷史為預設建議選項；刪除歷史不影響混合交易中的其他治具明細
### API 對應

- 頁面初始化
  - `api.getFixtureQualityReport`
  - `api.listFixtures`
  - `api.listModels`
  - `api.listStations`
  - `api.listCustomers`
  - `api.listCustomerUsers`
  - `api.listUsers`

- fixture tab
  - `api.createFixture`
  - `api.updateFixture`
  - `api.exportFixturesCsv`
  - `api.importFixturesCsv`
  - `api.downloadFixtureTemplateCsv`

- model tab
  - `api.createModel`
  - `api.updateModel`
  - `api.deleteModel`
  - `api.exportModelsCsv`
  - `api.importModelsCsv`
  - `api.downloadModelTemplateCsv`

- station tab
  - `api.createStation`
  - `api.updateStation`
  - `api.deleteStation`
  - `api.exportStationsCsv`
  - `api.importStationsCsv`
  - `api.downloadStationTemplateCsv`

- customer tab
  - `api.createCustomer`
  - `api.updateCustomer`
  - `api.listCustomerUsers`
  - `api.listUsers`

- user tab
  - `api.createUser`
  - `api.updateUser`
  - `api.resetUserPassword`

### 權限行為

- `guest` 不可進這頁
- `user` 可維護 fixture / model / station
- customer / user / ledger / quality tab 實際上是 admin 能力
- 治具永久刪除只對 `admin` 顯示，前端以 `canManageUsers` 控制入口
- 後端仍以 `manage` 權限作為真正授權邊界，不能只依賴前端隱藏按鈕
- admin 也必須選到已透過 `user_customers` 指派的客戶，否則後端會拒絕

### 改資料維護頁時去哪裡

- 改 page tab orchestration、summary、CSV 流程、品質報表跳轉
  - `frontend/src/pages/MasterPage.vue`
  - 治具刪除 dialog 與刪除後 refresh 也在此檔

- 改列表、搜尋、分頁欄位
  - `frontend/src/components/master/MasterListPanel.vue`
  - 主資料清單的頁數提示 / 總筆數 / 翻頁動作目前在表格上方

- 改 detail 編輯表單
  - `frontend/src/components/master/MasterDetailPanel.vue`
  - admin-only 永久刪除按鈕與危險區塊也在此檔

- 改帳目管理清單的頁數提示 / 總筆數 / 翻頁動作
  - `frontend/src/components/master/TransactionAccountListPanel.vue`

- 改治具資料品質表、問題篩選、CSV 匯出、點回治具編輯、問題類型跳轉規則
  - `frontend/src/components/master/FixtureQualityPanel.vue`
  - `frontend/src/pages/MasterPage.vue`

- 改治具刪除 API payload / response
  - `frontend/src/api/masterClient.ts`
  - `frontend/src/types.ts`（保留歷史時 `fixture_id` 可為 `null`）

## 產能頁

- page：`frontend/src/pages/ProductionPage.vue`
- 子元件：
  - `frontend/src/components/production/ProductionHeaderSection.vue`
  - `frontend/src/components/production/ProductionDetailSection.vue`
  - `frontend/src/components/production/ProductionCapacityPanel.vue`
  - `frontend/src/components/production/ProductionBatchImportModal.vue`

### 目前責任分工

- `ProductionPage.vue`
  - 初始化資料載入
  - route tab orchestration
  - mapping / requirement CRUD
  - CSV import / export
  - 批次匯入解析與缺資料補建

- `ProductionHeaderSection.vue`
  - 頁首導覽與統計

- `ProductionDetailSection.vue`
  - mapping / requirement / query 操作區

- `ProductionCapacityPanel.vue`
  - station capacity 視覺化

- `ProductionBatchImportModal.vue`
  - 兩種 production 批次匯入 modal shell

### 主要功能

- Model-Station Mapping
- Fixture Requirement
- Station Capacity
- Model Query
- Mapping / Requirement CSV 匯入匯出
- Mapping / Requirement 批次貼上匯入 modal
- 相似資料確認與即時建立新 model / station / fixture

### API 對應

- 初始化載入
  - `api.listModels`
  - `api.listStations`
  - `api.listFixtures`
  - `api.listModelStations`
  - `api.listFixtureRequirements`

- mapping
  - `api.createModelStation`
  - `api.updateModelStation`
  - `api.deleteModelStation`
  - `api.exportModelStationsCsv`
  - `api.importModelStationsCsv`
  - `api.downloadModelStationTemplateCsv`

- fixture requirement
  - `api.createFixtureRequirement`
  - `api.updateFixtureRequirement`
  - `api.deleteFixtureRequirement`
  - `api.exportFixtureRequirementsCsv`
  - `api.importFixtureRequirementsCsv`
  - `api.downloadFixtureRequirementTemplateCsv`

- capacity
  - `api.getStationCapacity`

- model query
  - `api.getModelQuery`

- 批次貼上匯入缺資料時建立新主檔
  - `api.createModel`
  - `api.createStation`
  - `api.createFixture`

### 改產能頁時去哪裡

- 改 route / tab orchestration、批次匯入解析、資料刷新
  - `frontend/src/pages/ProductionPage.vue`

- 改頁首與摘要
  - `frontend/src/components/production/ProductionHeaderSection.vue`

- 改 mapping / requirement / query 主要操作區
  - `frontend/src/components/production/ProductionDetailSection.vue`

- 改 capacity 視覺化
  - `frontend/src/components/production/ProductionCapacityPanel.vue`

- 改 batch modal frame
  - `frontend/src/components/production/ProductionBatchImportModal.vue`

## 前端常改支援檔

- `frontend/src/types.ts`
  - 欄位不一致時先看這裡

- `frontend/src/appState.ts`
  - customer 切換、登入 session、onboarding 共享狀態

- `frontend/src/onboarding.ts`
  - 導覽 flow 定義與跨頁流程
  - 目前已合併成四張教學卡，包含 `批次收 / 退料 & 收退料總檢視`、`治具 / 機種 / 站點主資料`、`機種站點對應 & 站點治具需求`

- `frontend/src/components/common/OnboardingFlowPicker.vue`
  - 教學分類選單

- `frontend/src/toastState.ts`
  - 成功 / 失敗提示

- `frontend/src/styles.css`
  - 共用 CSS utility
  - 新元件優先吃這裡的按鈕、panel、modal、table、chip 樣式

- `frontend/src/utils/apiError.ts`
  - 後端 error payload 轉可讀訊息

- `frontend/src/utils/date.ts`
  - 本地日期判斷

- `frontend/src/utils/display.ts`
  - fallback 與狀態文字映射

- `frontend/src/utils/identifier.ts`
  - 前端 `identifier` 正規化 / 查詢 helper

- `frontend/src/utils/identifier.test.ts`
  - 前端 `identifier` helper 單元測試

## 現況提醒

- audit API 仍保留在 `api.listAuditLogs`，但首頁沒有 audit 摘要區塊。
- shell 目前沒有 desktop compact / mini sidebar。
- 搜尋頁主結果已改為 `page_size` 邊界 + `load more`；fixture / model context 不再首屏全量預載。
- 搜尋頁目前仍沒有可收合的篩選區。
- 教學模式屬於前端 sandbox 流程，不會呼叫額外的 backend tutorial API。
- 如果要改前端 `identifier` 規則，優先改 `frontend/src/utils/identifier.ts` 與 `frontend/src/utils/identifier.test.ts`，不要回到元件內重寫 `padStart(4)`。

## 不要改的前端檔案

- `frontend/src/*.js`
- `frontend/src/**/*.js`
- `frontend/src/*.js.map`
- `frontend/src/**/*.js.map`
- `frontend/tsconfig.*.tsbuildinfo`
- `frontend/dist`
- `__pycache__`
