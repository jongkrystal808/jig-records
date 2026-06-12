# Frontend Map

這份文件回答兩件事：

- 每個頁面/按鈕對應哪個 API
- 要改畫面時應該進哪個檔案

## 入口檔

- `frontend/src/main.ts`
  - Vue 啟動入口
  - 掛載 `router` 與 `App.vue`

- `frontend/src/router/index.ts`
  - 路由表
  - `/search` -> `SearchWorkspacePage.vue`
  - `/inventory` -> `InventoryPage.vue`
  - `/master` -> `MasterPage.vue`
  - `/production` -> `ProductionPage.vue`

- `frontend/src/App.vue`
  - 全域 shell
  - 登入畫面
  - 頂欄
  - 左側導覽
  - 客戶切換
  - 新增客戶
  - 今日統計
  - 全域 toast 顯示
  - 固定 `1841 x 841` 畫布縮放

- `frontend/src/api.ts`
  - 前端所有 API 呼叫集中處

- `frontend/src/types.ts`
  - 前端型別定義

- `frontend/src/appState.ts`
  - 全域登入 session、客戶選擇

- `frontend/src/toastState.ts`
  - 全域 toast 狀態

- `frontend/src/styles.css`
  - 共用樣式骨架

## 全域 API 對應

### `frontend/src/App.vue`

- 登入按鈕
  - `api.login`

- 訪客入口按鈕
  - `api.guestEntry`

- 頁面初始化載入客戶
  - `api.listCustomers`

- 新增客戶按鈕
  - `api.createCustomer`

- 客戶切換後更新左側今日統計
  - `api.listAlerts`
  - `api.listTransactions`

### 畫面外觀與全域流程

- 如果你要改登入卡片、頂欄、側邊欄、客戶選擇位置
  - 改 `frontend/src/App.vue`

- 如果你要改全域 toast 顯示樣式
  - 改 `frontend/src/App.vue`
  - 補充邏輯在 `frontend/src/toastState.ts`

## 查詢頁

- 檔案：`frontend/src/pages/SearchWorkspacePage.vue`

### 主要功能

- 治具查詢
- 收料/退料記錄切換
- 機種查詢
- 右側圖片、儲位、最近異動

### API 對應

- 初始化載入
  - `api.listStock`
  - `api.listTransactions`
  - `api.listModels`

- 一般查詢按鈕
  - `api.globalSearch`

- 機種查詢按鈕
  - `api.getModelQuery`

- 常用機種快捷按鈕
  - `api.getModelQuery`

- 載入治具圖片
  - `api.listFixtureImages`
  - `GET /api/v2/warehouse/fixture-images/by-code/{fixture_code}`

- 補治具上下文
  - `api.globalSearch`

### 你要改什麼就去哪裡

- 改查詢模式 radio、搜尋框、查詢按鈕
  - `frontend/src/pages/SearchWorkspacePage.vue`

- 改查詢結果表格
  - `frontend/src/pages/SearchWorkspacePage.vue`

- 改右側圖片/儲位/最近異動
  - `frontend/src/pages/SearchWorkspacePage.vue`

## 收退料頁

- 檔案：`frontend/src/pages/InventoryPage.vue`

### 主要功能

- 收料 / 退料整合頁
- 依治具 `manage_type` 切 `datecode` / `serial`
- 庫存總覽
- 最近收/退料紀錄
- 低水位提醒
- 收退料總檢視
- CSV 匯入匯出
- 表格貼上批次匯入
- 新治具即時建立
- 相似治具確認與替換

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

- 總檢視查詢按鈕
  - `api.listTransactions`

- 總檢視重設按鈕
  - `api.listTransactions`

- 下載收退料範本
  - `api.downloadTransactionTemplateCsv`

- 匯入 CSV
  - `api.importTransactionsCsv`

- 批次貼上匯入
  - `api.listFixtures`
  - `api.createFixture`
  - `api.createReceipt`
  - `api.createReturn`

- 匯出總檢視 CSV
  - `api.exportTransactionsCsv`

### 你要改什麼就去哪裡

- 改收料/退料表單
  - `frontend/src/pages/InventoryPage.vue`

- 改 `datecode` / `serial` 顯示邏輯
  - `frontend/src/pages/InventoryPage.vue`

- 改交易總檢視篩選欄位
  - `frontend/src/pages/InventoryPage.vue`
  - `frontend/src/types.ts`
  - `frontend/src/api.ts`

## 資料維護頁

- 檔案：`frontend/src/pages/MasterPage.vue`

### 主要功能

- 治具
- 機種
- 站點
- 負責人
- 使用者
- CSV 匯入匯出

### Hero 區按鈕

- 下載範本
  - 治具：`api.downloadFixtureTemplateCsv`
  - 機種：`api.downloadModelTemplateCsv`
  - 站點：`api.downloadStationTemplateCsv`

- 匯入 CSV
  - 治具：`api.importFixturesCsv`
  - 機種：`api.importModelsCsv`
  - 站點：`api.importStationsCsv`

- 匯出 CSV
  - 治具：`api.exportFixturesCsv`
  - 機種：`api.exportModelsCsv`
  - 站點：`api.exportStationsCsv`

- 匯出 JSON
  - 前端本地匯出，不打 API

### 頁面初始化

- `api.listFixtures`
- `api.listModels`
- `api.listStations`
- `api.listOwners`
- `api.listUsers`

### 各 tab API

- 治具 tab
  - 新增：`api.createFixture`
  - 更新：`api.updateFixture`
  - 停用：`api.updateFixture`

- 機種 tab
  - 新增：`api.createModel`
  - 更新：`api.updateModel`
  - 停用：`api.updateModel`

- 站點 tab
  - 新增：`api.createStation`
  - 更新：`api.updateStation`
  - 停用：`api.updateStation`

- 負責人 tab
  - 新增：`api.createOwner`
  - 更新：`api.updateOwner`
  - 停用：`api.updateOwner`

- 使用者 tab
  - 新增：`api.createUser`
  - 更新：`api.updateUser`
  - 停用：`api.updateUser`
  - 重設密碼：`api.resetUserPassword`

### 你要改什麼就去哪裡

- 改 tab、清單欄位、詳細表單
  - `frontend/src/pages/MasterPage.vue`

- 改主資料型別
  - `frontend/src/types.ts`

- 改主資料 API 名稱或參數
  - `frontend/src/api.ts`

## 產能頁

- 檔案：`frontend/src/pages/ProductionPage.vue`

### 主要功能

- Production 介面總覽
- Model-Station Mapping
- Fixture Requirement
- Station Capacity
- Model Query
- CSV 匯入匯出

### API 對應

- 初始化載入
  - `api.listModels`
  - `api.listStations`
  - `api.listFixtures`
  - `api.listModelStations`

- Model-Station Mapping 新增
  - `api.createModelStation`

- Model-Station Mapping 匯出
  - `api.exportModelStationsCsv`

- Model-Station Mapping 範本
  - `api.downloadModelStationTemplateCsv`

- Model-Station Mapping 匯入
  - `api.importModelStationsCsv`

- Fixture Requirement 儲存
  - `api.createFixtureRequirement`

- Fixture Requirement 匯出
  - `api.exportFixtureRequirementsCsv`

- Fixture Requirement 範本
  - `api.downloadFixtureRequirementTemplateCsv`

- Fixture Requirement 匯入
  - `api.importFixtureRequirementsCsv`

- Station Capacity 刷新
  - `api.getStationCapacity`

- Model Query 刷新
  - `api.getModelQuery`

### 你要改什麼就去哪裡

- 改 mapping 卡片
  - `frontend/src/pages/ProductionPage.vue`

- 改 requirement 卡片
  - `frontend/src/pages/ProductionPage.vue`

- 改 station capacity 或 model query 顯示欄位
  - `frontend/src/pages/ProductionPage.vue`

## 儲位 / 圖片頁

- 檔案：`frontend/src/pages/WarehousePage.vue`

### 主要功能

- 倉庫主卡
- 治具工作區
- 儲位綁定
- 治具圖片維護
- 儲位主檔維護

### API 對應

- 初始化載入
  - `api.listFixtures`
  - `api.listLocations`
  - `api.listLocationAssignments`
  - `api.listFixtureImages`
  - `api.getWarehouseProfile`

- 倉庫主卡儲存
  - `api.updateWarehouseProfile`

- 儲位新增
  - `api.createLocation`

- 儲位更新
  - `api.updateLocation`

- 儲位綁定
  - `api.createLocationAssignment`

- 解除綁定
  - `api.deleteLocationAssignment`

- 圖片新增
  - `api.createFixtureImage`

- 圖片更新
  - `api.updateFixtureImage`

- 設為主要圖片
  - `api.setMainFixtureImage`

- 刪除圖片
  - `api.deleteFixtureImage`

- 重新整理圖片
  - `api.listFixtureImages`

### 你要改什麼就去哪裡

- 改倉庫主卡
  - `frontend/src/pages/WarehousePage.vue`

- 改儲位綁定流程
  - `frontend/src/pages/WarehousePage.vue`

- 改圖片上傳/主圖/刪除流程
  - `frontend/src/pages/WarehousePage.vue`

## 前端常改支援檔

- `frontend/src/types.ts`
  - 前後端欄位不一致時先看這裡

- `frontend/src/api.ts`
  - API path、query string、payload 都在這裡

- `frontend/src/appState.ts`
  - 客戶切換、登入 session 共享狀態

- `frontend/src/toastState.ts`
  - 成功/失敗提示邏輯

## 不要改的前端檔案

- `frontend/src/*.js`
- `frontend/src/**/*.js`
- `frontend/src/*.js.map`
- `frontend/src/**/*.js.map`
- `frontend/tsconfig.*.tsbuildinfo`
