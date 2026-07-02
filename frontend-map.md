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
  - guest 進 `/master` 會被導回 `/search`

- `frontend/src/App.vue`
  - 全域 shell
  - 登入畫面 / 訪客入口
  - 左側導覽
  - customer picker
  - 全域治具搜尋
  - today summary
  - 全域 toast 顯示
  - session / customer / 全域治具搜尋的 sessionStorage 持久化
  - 手機版側欄 overlay 開關

- `frontend/src/api.ts`
  - 前端所有 API 呼叫集中處

- `frontend/src/types.ts`
  - 前端型別定義

- `frontend/src/appState.ts`
  - 全域登入 session
  - customer 選擇

- `frontend/src/toastState.ts`
  - 全域 toast 狀態

- `frontend/src/styles.css`
  - 全域 CSS 變數與共用基底樣式

## 共用元件 / 工具

- `frontend/src/components/UiFormActions.vue`
  - 新增 / 編輯 / 取消 / 停用動作列

- `frontend/src/components/UiStatusPill.vue`
  - 主資料 / 狀態標籤顯示

- `frontend/src/components/production/ProductionCapacityPanel.vue`
  - 產能視覺化區塊

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

### 改全域畫面時去哪裡

- 改登入卡片 / 左側導覽 / customer picker / 全域治具搜尋 / today summary
  - `frontend/src/App.vue`

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

- 常用機種快捷按鈕
  - `api.getModelQuery`

- fixture 圖片
  - `fixtureImageUrlByCode`
  - `fetchFixtureImageObjectUrl`
  - `GET /api/v2/master/fixtures/{fixture_code}/image`

### 改查詢頁時去哪裡

- 改模式切換 / 篩選區 / 查詢按鈕
  - `frontend/src/pages/SearchWorkspacePage.vue`

- 改 fixture detail / model detail / transaction 表格
  - `frontend/src/pages/SearchWorkspacePage.vue`

- 改 fixture 圖片 URL 或載入策略
  - `frontend/src/api.ts`
  - `frontend/src/pages/SearchWorkspacePage.vue`

## 收退料頁

- 檔案：`frontend/src/pages/InventoryPage.vue`

### 主要功能

- `receipt` / `return` segmented control
- 操作頁與 overview 頁共用同一支 page
- 批次貼上匯入 modal
- 批次匯入 CSV 範本下載 / CSV 匯入
- 新治具即時建立
- 相似治具確認 / 替換
- 庫存總覽
- 低水位提醒
- 最近收退料紀錄
- 收退料總檢視
- overview 交易 CSV 匯出

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

- 批次匯入 CSV 範本下載
  - `api.downloadTransactionTemplateCsv`

- 批次匯入 CSV 匯入
  - `api.importTransactionsCsv`

- 批次貼上匯入內的新治具建立
  - `api.createFixture`

### 改收退料頁時去哪裡

- 改批次貼上解析規則 / 相似治具比對 / 匯入預覽表
  - `frontend/src/pages/InventoryPage.vue`

- 改交易篩選欄位或 payload
  - `frontend/src/pages/InventoryPage.vue`
  - `frontend/src/types.ts`
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
- `customer` / `user` tab 實際上是 admin 能力

### 改資料維護頁時去哪裡

- 改 tab、列表欄位、詳細編輯表單
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
  - customer 切換、登入 session 共享狀態

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
- 側欄目前沒有 desktop compact / mini mode，只有 mobile overlay 開關。

## 不要改的前端檔案

- `frontend/src/*.js`
- `frontend/src/**/*.js`
- `frontend/src/*.js.map`
- `frontend/src/**/*.js.map`
- `frontend/tsconfig.*.tsbuildinfo`
- `__pycache__`
