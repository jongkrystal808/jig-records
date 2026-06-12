# Backend Map

這份文件回答兩件事：

- 每個後端模組負責什麼
- 每個資料表欄位目前被哪些前端頁面使用

## 架構順序

後端一條典型修改路徑是：

- `router`
  - HTTP API 入口
- `service`
  - 業務規則
- `repository`
  - 資料庫查寫
- `model`
  - ORM 資料表
- `schema`
  - request / response 驗證格式

## 入口與基礎層

- `backend/app/main.py`
  - 建立 FastAPI app
  - startup 建表
  - 執行 schema patch
  - 確保預設 `admin` 使用者存在
  - 掛載 `/api/v2`

- `backend/app/core/config.py`
  - 環境設定與 `settings`

- `backend/app/core/database.py`
  - `engine`
  - `SessionLocal`
  - `get_db`

- `backend/app/core/schema_patch.py`
  - 舊 DB 補欄位 / 補表保底
  - 改欄位後通常要同步補這裡

- `backend/app/routers/api.py`
  - 掛所有子 router

## Router / Service / Repository 對應

### Auth

- Router：`backend/app/routers/auth.py`
- Service：`backend/app/services/auth_service.py`
- Repository：`backend/app/repositories/master_repository.py`
- Model：`backend/app/models/master.py` 的 `User`
- Schema：`backend/app/schemas/auth.py`

#### 提供 API

- `POST /auth/login`
- `POST /auth/guest`
- `GET /auth/users`
- `POST /auth/users`
- `PUT /auth/users/{user_id}`
- `POST /auth/users/{user_id}/reset-password`

#### 前端入口

- `frontend/src/App.vue`
  - 登入
  - 訪客入口

- `frontend/src/pages/MasterPage.vue`
  - 使用者清單
  - 新增使用者
  - 編輯使用者
  - 停用使用者
  - 重設密碼

### Master

- Router：`backend/app/routers/master.py`
- Service：`backend/app/services/master_service.py`
- Repository：`backend/app/repositories/master_repository.py`
- Model：`backend/app/models/master.py`
- Schema：`backend/app/schemas/master.py`

#### 提供 API

- `GET /master/customers`
- `POST /master/customers`
- `GET /master/fixtures`
- `POST /master/fixtures`
- `PUT /master/fixtures/{fixture_id}`
- `GET /master/models`
- `POST /master/models`
- `PUT /master/models/{model_id}`
- `GET /master/stations`
- `POST /master/stations`
- `PUT /master/stations/{station_id}`
- `GET /master/owners`
- `POST /master/owners`
- `PUT /master/owners/{owner_id}`
- fixtures / models / stations 匯入匯出與範本

#### 前端入口

- `frontend/src/App.vue`
  - 客戶清單
  - 新增客戶

- `frontend/src/pages/MasterPage.vue`
  - 治具 / 機種 / 站點 / 負責人維護
  - 主資料匯入匯出

- `frontend/src/pages/InventoryPage.vue`
  - 治具下拉

- `frontend/src/pages/ProductionPage.vue`
  - 機種、站點、治具下拉

- `frontend/src/pages/WarehousePage.vue`
  - 治具工作區

### Inventory

- Router：`backend/app/routers/inventory.py`
- Service：`backend/app/services/inventory_service.py`
- Repository：`backend/app/repositories/inventory_repository.py`
- Model：`backend/app/models/inventory.py`
- Schema：`backend/app/schemas/inventory.py`

#### 提供 API

- `POST /inventory/receipts`
- `POST /inventory/returns`
- `GET /inventory/stock`
- `GET /inventory/alerts`
- `GET /inventory/transactions`
- `/inventory/transactions` 匯入匯出與範本
- 收退料批次貼上匯入仍沿用既有 `receipts` / `returns`
- 新治具建立沿用 `POST /master/fixtures`

#### 前端入口

- `frontend/src/pages/InventoryPage.vue`
  - 收料
  - 退料
  - 庫存總覽
  - 低水位提醒
  - 總檢視
  - CSV 匯入匯出
  - 批次貼上匯入
  - 新治具建立
  - 相似治具確認

- `frontend/src/App.vue`
  - 左側今日統計

- `frontend/src/pages/SearchWorkspacePage.vue`
  - 查詢頁 KPI
  - 最近異動
  - 收/退料記錄表

### Search

- Router：`backend/app/routers/search.py`
- Service：`backend/app/services/search_service.py`
- Repository：`backend/app/repositories/search_repository.py`
- Schema：`backend/app/schemas/search.py`

#### 提供 API

- `GET /search/global`

#### 前端入口

- `frontend/src/pages/SearchWorkspacePage.vue`
  - 一般查詢
  - 補治具上下文
  - 儲位與機種標籤資料來源

### Production

- Router：`backend/app/routers/production.py`
- Service：`backend/app/services/production_service.py`
- Repository：`backend/app/repositories/production_repository.py`
- Model：`backend/app/models/master.py` 的 `ModelStation`
- Model：`backend/app/models/production.py`
- Schema：`backend/app/schemas/production.py`

#### 提供 API

- `GET /production/model-stations`
- `POST /production/model-stations`
- `GET /production/capacity/stations/{station_id}`
- `GET /production/models/{model_id}/query`
- `POST /production/fixture-requirements`
- model-stations / fixture-requirements 匯入匯出與範本

#### 前端入口

- `frontend/src/pages/ProductionPage.vue`
  - Mapping
  - Requirement
  - Capacity
  - Model Query

- `frontend/src/pages/SearchWorkspacePage.vue`
  - 機種查詢

### Warehouse

- Router：`backend/app/routers/warehouse.py`
- Service：`backend/app/services/warehouse_service.py`
- Repository：`backend/app/repositories/warehouse_repository.py`
- Model：`backend/app/models/warehouse.py`
- Schema：`backend/app/schemas/warehouse.py`

#### 提供 API

- `GET /warehouse/profile`
- `PUT /warehouse/profile`
- `GET /warehouse/locations`
- `POST /warehouse/locations`
- `PUT /warehouse/locations/{location_id}`
- `GET /warehouse/location-assignments`
- `POST /warehouse/location-assignments`
- `DELETE /warehouse/location-assignments/{assignment_id}`
- `GET /warehouse/fixture-images`
- `GET /warehouse/fixture-images/by-code/{fixture_code}`
- `POST /warehouse/fixture-images`
- `PUT /warehouse/fixture-images/{image_id}`
- `POST /warehouse/fixture-images/{image_id}/set-main`
- `DELETE /warehouse/fixture-images/{image_id}`

#### 前端入口

- `frontend/src/pages/WarehousePage.vue`
  - 倉庫資料
  - 儲位主檔
  - 綁定
  - 圖片管理

- `frontend/src/pages/SearchWorkspacePage.vue`
  - 右側治具圖片
  - 右側儲位資訊

## 資料表欄位使用面

這段只列「目前前端有用到的欄位」，目的是讓你知道改欄位會影響哪些頁面。

### `customers`

- 檔案：`backend/app/models/master.py`
- 主要欄位：
  - `id`
  - `code`
  - `name`
- 前端使用頁面：
  - `frontend/src/App.vue`
    - 客戶切換下拉
    - 新增客戶表單

### `fixtures`

- 檔案：`backend/app/models/master.py`
- 主要欄位：
  - `id`
  - `customer_id`
  - `owner_id`
  - `code`
  - `name`
  - `manage_type`
  - `description`
  - `is_active`
- 前端使用頁面：
  - `frontend/src/pages/MasterPage.vue`
    - 治具主檔清單與詳細表單
  - `frontend/src/pages/InventoryPage.vue`
    - 治具下拉
    - `manage_type` 決定 `datecode` / `serial`
    - `is_active` 決定可選治具
  - `frontend/src/pages/ProductionPage.vue`
    - requirement 用治具下拉
  - `frontend/src/pages/WarehousePage.vue`
    - 治具工作區
  - `frontend/src/pages/SearchWorkspacePage.vue`
    - 透過查詢結果與 model query 間接顯示 `fixture_code` / `fixture_name`

### `machine_models`

- 檔案：`backend/app/models/master.py`
- 主要欄位：
  - `id`
  - `code`
  - `name`
  - `is_active`
- 前端使用頁面：
  - `frontend/src/pages/MasterPage.vue`
    - 機種主檔
  - `frontend/src/pages/ProductionPage.vue`
    - model 下拉
    - mapping / query
  - `frontend/src/pages/SearchWorkspacePage.vue`
    - 機種查詢
    - 常用機種按鈕

### `stations`

- 檔案：`backend/app/models/master.py`
- 主要欄位：
  - `id`
  - `code`
  - `name`
  - `is_active`
- 前端使用頁面：
  - `frontend/src/pages/MasterPage.vue`
    - 站點主檔
  - `frontend/src/pages/ProductionPage.vue`
    - mapping / requirement / capacity

### `owners`

- 檔案：`backend/app/models/master.py`
- 主要欄位：
  - `id`
  - `name`
  - `is_active`
- 前端使用頁面：
  - `frontend/src/pages/MasterPage.vue`
    - 負責人主檔
    - 治具詳細表單的負責人下拉

### `users`

- 檔案：`backend/app/models/master.py`
- 主要欄位：
  - `id`
  - `username`
  - `password_hash`
  - `display_name`
  - `role`
  - `is_active`
  - `created_at`
  - `updated_at`
- 前端使用頁面：
  - `frontend/src/App.vue`
    - 登入後顯示 `display_name`
  - `frontend/src/pages/MasterPage.vue`
    - 使用者清單
    - 使用者建立/更新/停用/重設密碼
- 備註：
  - `password_hash` 沒有直接回前端，只在後端使用

### `model_stations`

- 檔案：`backend/app/models/master.py`
- 主要欄位：
  - `id`
  - `model_id`
  - `station_id`
- 前端使用頁面：
  - `frontend/src/pages/ProductionPage.vue`
    - Mapping 清單與新增

### `material_transactions`

- 檔案：`backend/app/models/inventory.py`
- 主要欄位：
  - `id`
  - `customer_id`
  - `transaction_type`
  - `transaction_no`
  - `occurred_at`
  - `created_by`
  - `note`
- 前端使用頁面：
  - `frontend/src/pages/InventoryPage.vue`
    - 收料紀錄
    - 退料紀錄
    - 總檢視
  - `frontend/src/pages/SearchWorkspacePage.vue`
    - 收料/退料紀錄
    - 最近異動
  - `frontend/src/App.vue`
    - 左側今日收退料統計

### `material_transaction_items`

- 檔案：`backend/app/models/inventory.py`
- 主要欄位：
  - `transaction_id`
  - `fixture_id`
  - `manage_type`
  - `ownership_type`
  - `datecode`
  - `serial_number`
  - `quantity`
  - `note`
- 前端使用頁面：
  - `frontend/src/pages/InventoryPage.vue`
    - 收退料送出 payload
    - 總檢視明細
  - `frontend/src/pages/SearchWorkspacePage.vue`
    - 最近異動
    - 收退料紀錄列表

### `fixture_stock_levels`

- 檔案：`backend/app/models/inventory.py`
- 主要欄位：
  - `fixture_id`
  - `min_stock_qty`
  - `warning_threshold`
  - `alert_enabled`
- 前端使用頁面：
  - `frontend/src/pages/MasterPage.vue`
    - 治具最低庫存欄位
  - `frontend/src/pages/InventoryPage.vue`
    - 低水位提醒
  - `frontend/src/pages/ProductionPage.vue`
    - model query 顯示最低水位
  - `frontend/src/pages/SearchWorkspacePage.vue`
    - model query 顯示最低水位
- 備註：
  - `warning_threshold`、`alert_enabled` 目前沒有直接前端入口

### `fixture_stock_summary`

- 檔案：`backend/app/models/inventory.py`
- 主要欄位：
  - `fixture_id`
  - `stock_qty`
  - `returned_qty`
  - `last_transaction_at`
  - `stock_status`
- 前端使用頁面：
  - `frontend/src/pages/InventoryPage.vue`
    - 現有治具庫存
    - 低水位提醒
    - KPI
  - `frontend/src/pages/SearchWorkspacePage.vue`
    - 查詢結果
    - KPI
    - 右側狀態
  - `frontend/src/pages/ProductionPage.vue`
    - model query 顯示庫存與狀態
- 備註：
  - `returned_qty`、`last_transaction_at` 目前沒有獨立欄位顯示

### `fixture_serials`

- 檔案：`backend/app/models/inventory.py`
- 主要欄位：
  - `id`
  - `fixture_id`
  - `serial_no`
- 前端使用頁面：
  - 沒有獨立維護頁
  - 間接影響：
    - `frontend/src/pages/InventoryPage.vue`
      - serial 類收退料
    - `frontend/src/pages/SearchWorkspacePage.vue`
      - serial 查詢結果

### `fixture_requirements`

- 檔案：`backend/app/models/production.py`
- 主要欄位：
  - `id`
  - `station_id`
  - `fixture_id`
  - `required_qty`
- 前端使用頁面：
  - `frontend/src/pages/ProductionPage.vue`
    - requirement 建立
    - model query 結果
  - `frontend/src/pages/SearchWorkspacePage.vue`
    - 機種查詢的可開站量換算

### `machine_capacity_summary`

- 檔案：`backend/app/models/production.py`
- 主要欄位：
  - `station_id`
  - `max_open_station_count`
  - `bottleneck_fixture_code`
- 前端使用頁面：
  - `frontend/src/pages/ProductionPage.vue`
    - station capacity
  - `frontend/src/pages/SearchWorkspacePage.vue`
    - 機種查詢的可開站量相關顯示

### `warehouse_profiles`

- 檔案：`backend/app/models/warehouse.py`
- 主要欄位：
  - `id`
  - `code`
  - `name`
  - `is_active`
  - `note`
  - `created_at`
  - `updated_at`
- 前端使用頁面：
  - `frontend/src/pages/WarehousePage.vue`
    - 倉庫主卡

### `storage_locations`

- 檔案：`backend/app/models/warehouse.py`
- 主要欄位：
  - `id`
  - `code`
  - `area`
  - `rack`
  - `layer`
  - `description`
  - `image_path`
  - `is_active`
- 前端使用頁面：
  - `frontend/src/pages/WarehousePage.vue`
    - 儲位主檔
    - 綁定下拉
  - `frontend/src/pages/SearchWorkspacePage.vue`
    - 右側儲位顯示
- 備註：
  - `image_path` 目前沒有在前端顯示

### `fixture_location_assignments`

- 檔案：`backend/app/models/warehouse.py`
- 主要欄位：
  - `id`
  - `fixture_id`
  - `location_id`
  - `created_at`
- 前端使用頁面：
  - `frontend/src/pages/WarehousePage.vue`
    - 綁定清單
    - 目前儲位摘要
  - `frontend/src/pages/SearchWorkspacePage.vue`
    - 右側儲位顯示

### `fixture_images`

- 檔案：`backend/app/models/warehouse.py`
- 主要欄位：
  - `id`
  - `fixture_id`
  - `image_path`
  - `thumbnail_path`
  - `is_main`
  - `created_at`
- 前端使用頁面：
  - `frontend/src/pages/WarehousePage.vue`
    - 圖片清單
    - 編輯
    - 主圖
    - 刪除
  - `frontend/src/pages/SearchWorkspacePage.vue`
    - 右側圖片預覽

## 改欄位時的最小連動清單

如果你改任何資料表欄位，最少要檢查：

- `backend/app/models/*.py`
- `backend/app/schemas/*.py`
- `backend/app/repositories/*.py`
- `backend/app/services/*.py`
- `backend/app/routers/*.py`
- `backend/app/core/schema_patch.py`
- `frontend/src/types.ts`
- `frontend/src/api.ts`
- 對應頁面的 `.vue`
