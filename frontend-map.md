# Frontend Map

這份文件回答三件事：

- 每個頁面 / 主要操作對應哪個 API
- 要改畫面或互動時應該進哪個檔案
- 目前有哪些共用元件 / 共用工具已經抽出

## 入口檔與全域骨架

- `frontend/src/main.ts`
  - Vue 啟動入口
  - 掛載 `router` 與 `App.vue`

- `frontend/src/router/index.ts`
  - 路由表
  - `/search` -> `SearchWorkspacePage.vue`
  - `/inventory` -> `InventoryPage.vue`
  - `/inventory/overview` -> `InventoryPage.vue`
  - `/master` -> `MasterPage.vue`
  - `/production` -> `ProductionPage.vue`
  - `/production/mapping` -> `ProductionPage.vue`
  - `/production/requirements` -> `ProductionPage.vue`
  - guest 進 `/master` 會被導回 `/search`

- `frontend/src/App.vue`
  - 全域 shell
  - 登入畫面 / 訪客入口
  - 頂部導覽列
  - customer picker
  - 今日收料 / 退料 / 低水位統計
  - 全域 `收/退料` modal
  - 全域 `收退料資訊匯出` modal
  - `更多功能` 選單
  - 首次登入自動新手導覽
  - 全域 toast 顯示
  - session / customer 的 sessionStorage 持久化
  - 手機版選單 overlay 開關

- `frontend/src/api.ts`
  - 前端所有 API 呼叫集中處

- `frontend/src/types.ts`
  - 前端型別定義

- `frontend/src/appState.ts`
  - 全域登入 session
  - customer 選擇
  - onboarding 狀態

- `frontend/src/onboarding.ts`
  - 新手導覽步驟定義
  - 每一步對應 route / `data-tour` target / 文案 / 方向

- `frontend/src/toastState.ts`
  - 全域 toast 狀態

- `frontend/src/styles.css`
  - 全域 CSS 變數與共用基底樣式

## 共用元件 / 工具

- `frontend/src/components/common/GuidedTour.vue`
  - 全域導覽浮層
  - spotlight 目標高亮
  - route-aware step 流程

- `frontend/src/components/common/InlineSpinner.vue`
  - 小型 inline loading indicator

- `frontend/src/components/UiFormActions.vue`
  - 新增 / 編輯 / 取消 / 停用動作列

- `frontend/src/components/UiStatusPill.vue`
  - 主資料 / 狀態標籤顯示

- `frontend/src/components/inventory/BatchImportPanel.vue`
  - 共用批次貼上匯入元件
  - `/inventory` 與全域 modal 共用
  - 支援 tutorial mode 教學試跑

- `frontend/src/components/inventory/InventoryExportPanel.vue`
  - 收退料報表匯出面板
  - 匯出前 preview / 報表類型 / 格式選擇

- `frontend/src/components/production/ProductionCapacityPanel.vue`
  - 產能視覺化區塊

- `frontend/src/components/search/FixtureInfoPanel.vue`
  - 治具查詢展示面板

- `frontend/src/components/search/ModelInfoPanel.vue`
  - 機種查詢展示面板

- `frontend/src/components/search/FixtureEditForm.vue`
  - 搜尋頁中的治具編輯表單

- `frontend/src/components/search/ModelEditForm.vue`
  - 搜尋頁中的機種編輯表單

- `frontend/src/utils/date.ts`
  - 本地日期 key / 顯示輔助

- `frontend/src/utils/apiError.ts`
  - API error message 解析

- `frontend/src/utils/display.ts`
  - fallback text / ownership label / stock status label 等顯示工具

## 全域流程 API 對應

### `frontend/src/App.vue`

- 登入按鈕
  - `api.login`

- 訪客入口按鈕
  - `api.guestEntry`

- 初始化 / session 恢復後載入 customer
  - `api.listCustomers`

- customer 切換後更新 today summary
  - `api.listAlerts`
  - `api.listTransactions`

- 全域收退料 modal
  - 內部共用 `BatchImportPanel.vue`

- 全域收退料匯出 modal
  - 內部共用 `InventoryExportPanel.vue`

### 改全域畫面時去哪裡

- 改頂部導覽、登入卡片、customer picker、全域 modal、更多功能選單
  - `frontend/src/App.vue`

- 改新手導覽步驟、導覽文案、目標 selector
  - `frontend/src/onboarding.ts`
  - `frontend/src/components/common/GuidedTour.vue`
  - 各頁面上的 `data-tour` 標記

- 改全域共享狀態
  - `frontend/src/appState.ts`

- 改全域 toast 樣式
  - `frontend/src/App.vue`
  - 狀態邏輯在 `frontend/src/toastState.ts`

## 查詢頁

- 檔案：`frontend/src/pages/SearchWorkspacePage.vue`

### 主要功能

- 雙模式查詢：`治具` / `機種`
- 固定 KPI 方格
- fixture detail
- model detail
- fixture 圖片預覽
- 識別碼庫存摘要
- transaction context
- 內容區內滾動
- 首頁固定「開始新手教學」入口
- 相近編號提示排序
- 區塊 chip 顯示切換與 localStorage 記憶

### 目前未落地

- 查詢結果分頁
- 可收合篩選區

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

- 改模式切換 / 關鍵字輸入 / chip 區 / onboarding 入口
  - `frontend/src/pages/SearchWorkspacePage.vue`

- 改相近編號提示排序規則
  - `frontend/src/pages/SearchWorkspacePage.vue`

- 改 fixture detail / model detail / transaction 表格
  - `frontend/src/pages/SearchWorkspacePage.vue`
  - `frontend/src/components/search/*.vue`

- 改 fixture 圖片 URL 或載入策略
  - `frontend/src/api.ts`
  - `frontend/src/pages/SearchWorkspacePage.vue`

## 收退料頁

- 檔案：`frontend/src/pages/InventoryPage.vue`

### 主要功能

- `receipt` / `return` segmented control
- 操作頁與 overview 頁共用同一支 page
- 內嵌共用 `BatchImportPanel`
- 新治具即時建立
- 相似治具確認 / 替換
- 庫存總覽
- 低水位提醒
- 最近收退料紀錄
- 收退料總檢視
- overview 交易 CSV 匯出
- onboarding 教學模式下的 sandbox 試跑

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

- 送出退料
  - `api.createReturn`

- overview 查詢
  - `api.listTransactions`

- overview 匯出 CSV
  - `api.exportTransactionsCsv`

- 批次貼上匯入內的新治具建立
  - `api.createFixture`

### 改收退料頁時去哪裡

- 改批次貼上解析規則 / 相似治具比對 / 匯入預覽表 / tutorial mode
  - `frontend/src/components/inventory/BatchImportPanel.vue`

- 改 `/inventory` 與 `/inventory/overview` 路由切換、總覽區塊、頁內篩選欄位
  - `frontend/src/pages/InventoryPage.vue`

- 改交易篩選欄位或 payload
  - `frontend/src/pages/InventoryPage.vue`
  - `frontend/src/types.ts`
  - `frontend/src/api.ts`

- 改全域收退料匯出互動
  - `frontend/src/components/inventory/InventoryExportPanel.vue`
  - `frontend/src/api.ts`

- 改 `identifier` / `ownership_type` 顯示文案
  - `frontend/src/utils/display.ts`
  - `frontend/src/pages/InventoryPage.vue`

## 資料維護頁

- 檔案：`frontend/src/pages/MasterPage.vue`

### 主要功能

- fixture / model / station / customer / user 五個 tab
- tab 清單分頁
- 狀態篩選 / 關鍵字搜尋
- fixture 維護 `responsible_user_id` / `min_stock_qty` / `storage_location`
- customer 維護 `assigned_user_ids`
- user 建立 / 更新 / 停用 / 重設密碼
- fixture / model / station CSV 匯入匯出 / 範本下載
- 從資料維護頁重新啟動新手導覽

### 頁面初始化

- `api.listFixtures`
- `api.listModels`
- `api.listStations`
- `api.listCustomers`
- `api.listCustomerUsers`
- `api.listUsers`

### 各 tab API

- fixture tab
  - 新增：`api.createFixture`
  - 更新：`api.updateFixture`
  - 停用：`api.updateFixture`
  - 匯出：`api.exportFixturesCsv`
  - 匯入：`api.importFixturesCsv`
  - 範本：`api.downloadFixtureTemplateCsv`

- model tab
  - 新增：`api.createModel`
  - 更新：`api.updateModel`
  - 停用：`api.updateModel`
  - 匯出：`api.exportModelsCsv`
  - 匯入：`api.importModelsCsv`
  - 範本：`api.downloadModelTemplateCsv`

- station tab
  - 新增：`api.createStation`
  - 更新：`api.updateStation`
  - 停用：`api.updateStation`
  - 匯出：`api.exportStationsCsv`
  - 匯入：`api.importStationsCsv`
  - 範本：`api.downloadStationTemplateCsv`

- customer tab
  - 新增：`api.createCustomer`
  - 更新：`api.updateCustomer`
  - 顯示責任人候選：`api.listCustomerUsers`
  - 實際指派清單來源：`api.listUsers`

- user tab
  - 新增：`api.createUser`
  - 更新：`api.updateUser`
  - 停用：`api.updateUser`
  - 重設密碼：`api.resetUserPassword`

### 權限行為

- `guest` 不可進這頁
- `user` 可維護 fixture / model / station
- customer / user tab 實際上是 admin 能力

### 改資料維護頁時去哪裡

- 改 tab、列表欄位、詳細編輯表單、導覽啟動按鈕
  - `frontend/src/pages/MasterPage.vue`

- 改主資料型別
  - `frontend/src/types.ts`

- 改主資料 API path / payload
  - `frontend/src/api.ts`

## 產能頁

- 檔案：`frontend/src/pages/ProductionPage.vue`

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
  - 新增：`api.createModelStation`
  - 更新：`api.updateModelStation`
  - 刪除：`api.deleteModelStation`
  - 匯出：`api.exportModelStationsCsv`
  - 匯入：`api.importModelStationsCsv`
  - 範本：`api.downloadModelStationTemplateCsv`

- fixture requirement
  - 新增：`api.createFixtureRequirement`
  - 更新：`api.updateFixtureRequirement`
  - 刪除：`api.deleteFixtureRequirement`
  - 匯出：`api.exportFixtureRequirementsCsv`
  - 匯入：`api.importFixtureRequirementsCsv`
  - 範本：`api.downloadFixtureRequirementTemplateCsv`

- capacity
  - `api.getStationCapacity`

- model query
  - `api.getModelQuery`

- 批次貼上匯入缺資料時建立新主檔
  - `api.createModel`
  - `api.createStation`
  - `api.createFixture`

### 改產能頁時去哪裡

- 改 mapping / requirement 編輯流程
  - `frontend/src/pages/ProductionPage.vue`

- 改 capacity 視覺化
  - `frontend/src/components/production/ProductionCapacityPanel.vue`
  - `frontend/src/pages/ProductionPage.vue`

- 改 model query 欄位
  - `frontend/src/pages/ProductionPage.vue`
  - `frontend/src/types.ts`

## 前端常改支援檔

- `frontend/src/types.ts`
  - 欄位不一致時先看這裡

- `frontend/src/api.ts`
  - API path / query string / payload / response parsing

- `frontend/src/appState.ts`
  - customer 切換、登入 session、onboarding 共享狀態

- `frontend/src/onboarding.ts`
  - 導覽步驟定義與跨頁流程

- `frontend/src/toastState.ts`
  - 成功 / 失敗提示

- `frontend/src/utils/apiError.ts`
  - 後端 error payload 轉可讀訊息

- `frontend/src/utils/date.ts`
  - 本地日期判斷

- `frontend/src/utils/display.ts`
  - fallback 與狀態文字映射

## 現況提醒

- `api.listAuditLogs` 仍存在於 `frontend/src/api.ts`，但目前 `App.vue` 沒有渲染最近異動區塊。
- shell 目前沒有 desktop compact / mini mode，只有 mobile overlay 開關。
- 搜尋頁目前沒有查詢結果分頁，也沒有可收合篩選區。
- 教學模式屬於前端 sandbox 流程，不會呼叫額外的 backend tutorial API。

## 不要改的前端檔案

- `frontend/src/*.js`
- `frontend/src/**/*.js`
- `frontend/src/*.js.map`
- `frontend/src/**/*.js.map`
- `frontend/tsconfig.*.tsbuildinfo`
- `frontend/dist`
- `__pycache__`
