# Backend Map

這份文件回答三件事：

- 後端各模組現在的責任分工
- 前端主要頁面各自依賴哪些後端 API / 資料表
- 改資料模型或啟動流程時最少要連動檢查哪些地方

## 後端請求路徑

一條典型後端變更路徑是：

- `router`
  - HTTP API 入口
  - 權限依賴、query/path 參數、HTTP error mapping

- `service`
  - 業務規則
  - 審計寫入
  - 交易與跨 repository 協調

- `repository`
  - SQLAlchemy 查詢與寫入

- `model`
  - ORM 資料表定義

- `schema`
  - request / response 驗證格式

## 基礎入口與核心層

- `main.py`
  - 本機 / image 啟動 launcher
  - 依 `BOOTSTRAP_BEFORE_RUN` 決定是否先做 bootstrap
  - 預設會先跑 migration 與 default user 初始化，再起 `uvicorn`

- `backend/app/bootstrap.py`
  - `bootstrap_application()`
  - 專責 migration 與 default admin 建立
  - 可獨立 CLI 執行

- `backend/app/main.py`
  - 建立 FastAPI app
  - 註冊 error handlers
  - 提供 `/health`
  - 掛載 `/api/v2`
  - 不再在 app startup 內直接跑 migration / bootstrap

- `backend/app/routers/api.py`
  - 掛載 `auth` / `master` / `inventory` / `production` / `search` / `audit`

- `backend/app/core/auth.py`
  - JWT session 解析
  - `read` / `write` / `manage` 權限檢查
  - customer scope 驗證

- `backend/app/core/database.py`
  - `engine`
  - `SessionLocal`
  - `get_db`

- `backend/app/core/migrations.py`
  - Alembic upgrade 執行
  - version table 相容檢查
  - legacy revision normalization

- `backend/app/core/schema_patch.py`
  - legacy DB runtime patch 保底
  - 現在只保留相容用途，不是主 migration 機制

- `backend/app/core/errors.py`
  - FastAPI error handler 註冊
  - `RequestValidationError` payload 序列化保底

## Router / Service / Repository / Model 對應

### Auth

- Router：`backend/app/routers/auth.py`
- Service：`backend/app/services/auth_service.py`
- Repository：`backend/app/repositories/master_repository.py`
- Model：`backend/app/models/master.py` 的 `User` / `UserCustomer`
- Schema：`backend/app/schemas/auth.py`

#### API

- `POST /auth/login`
- `POST /auth/guest`
- `GET /auth/users`
- `POST /auth/users`
- `PUT /auth/users/{user_id}`
- `POST /auth/users/{user_id}/reset-password`

#### 行為重點

- `admin` 可管理使用者
- `guest` 只會拿到 guest session，不可寫
- 密碼雜湊為 PBKDF2，並相容舊 sha256 資料
- `allowed_customer_ids` 仍會出現在 user API payload，但實際 customer 指派入口已移到 customer tab
- onboarding / guided tour 沒有獨立後端 API，完全由前端 shell 控制

#### 前端入口

- `frontend/src/App.vue`
  - 登入
  - 訪客入口
  - session 持久化 / 登出

- `frontend/src/pages/MasterPage.vue`
  - 使用者清單
  - 新增 / 編輯 / 停用使用者
  - 重設密碼

### Master

- Router：`backend/app/routers/master.py`
- Service：`backend/app/services/master_service.py`
- Repository：`backend/app/repositories/master_repository.py`
- Model：`backend/app/models/master.py`
- Schema：`backend/app/schemas/master.py`

#### API

- `GET /master/customers`
- `POST /master/customers`
- `PUT /master/customers/{customer_id}`
- `GET /master/customers/{customer_id}/users`
- `GET /master/fixtures`
- `POST /master/fixtures`
- `PUT /master/fixtures/{fixture_id}`
- `GET /master/fixtures/export`
- `GET /master/fixtures/template`
- `POST /master/fixtures/import`
- `GET /master/fixtures/{fixture_code}/image`
- `GET /master/models`
- `POST /master/models`
- `PUT /master/models/{model_id}`
- `GET /master/models/export`
- `GET /master/models/template`
- `POST /master/models/import`
- `GET /master/stations`
- `POST /master/stations`
- `PUT /master/stations/{station_id}`
- `GET /master/stations/export`
- `GET /master/stations/template`
- `POST /master/stations/import`

#### 行為重點

- `customers` / `users` 是 `manage` 權限
- `fixtures` / `models` / `stations` 是 `write` 權限
- `fixtures.code` 使用 `(customer_id, code)` 唯一鍵
- `fixtures.responsible_user_id` 候選名單來自該客戶已指派使用者
- fixture image 採檔案式讀取，不走 DB 圖片表

#### 前端入口

- `frontend/src/components/app/AppTopbar.vue`
  - customer list / current customer picker

- `frontend/src/pages/MasterPage.vue`
  - fixture / model / station / customer / user 維護
  - 主資料 CSV 匯入匯出

- `frontend/src/pages/InventoryPage.vue`
  - fixture 清單
  - 批次匯入時的新治具建立

- `frontend/src/pages/ProductionPage.vue`
  - model / station / fixture 下拉
  - production 批次匯入時的新機種 / 新站點 / 新治具建立

- `frontend/src/pages/SearchWorkspacePage.vue`
  - fixture 圖片載入
  - fixture / model lookup 基礎資料

### Inventory

- Router：`backend/app/routers/inventory.py`
- Service：`backend/app/services/inventory_service.py`
- Repository：`backend/app/repositories/inventory_repository.py`
- Model：`backend/app/models/inventory.py`
- Schema：`backend/app/schemas/inventory.py`

#### API

- `POST /inventory/receipts`
- `POST /inventory/returns`
- `GET /inventory/stock`
- `GET /inventory/alerts`
- `GET /inventory/identifier-stock-summary`
- `GET /inventory/transactions`
- `GET /inventory/transactions/export`
- `GET /inventory/transactions/export-report`
- `GET /inventory/transactions/export-report/preview`
- `GET /inventory/transactions/template`
- `POST /inventory/transactions/import`

#### 行為重點

- 交易明細正式使用單一 `identifier`
- 寫入規格是 `1-4` 位數字，寫入前左補零
- 查詢規格相容舊資料
  - `1-4` 位數字會同時匹配不同 padding 寬度的 legacy 值
  - 非 `1-4` 位數字輸入會當 legacy identifier/datecode 原值查詢
- `ownership_type` 在 transaction item 層
- 批次貼上匯入前端仍走 `/receipts` / `/returns`
- CSV 匯入走 `/inventory/transactions/import`
- overview 查詢支援 `transaction_type` / `date_from` / `date_to` / `fixture_code` / `transaction_no` / `identifier` / `created_by`
- 報表匯出支援 `summary|detail` 與 `xlsx|txt`
- 匯出 preview 由 `/inventory/transactions/export-report/preview` 提供
- onboarding 教學模式不會新增後端 tutorial endpoint；只是前端不真正送出 `/receipts` 或 `/returns`

#### 前端入口

- `frontend/src/pages/InventoryPage.vue`
  - 收料 / 退料主作業
  - 內嵌批次貼上匯入
  - 庫存總覽
  - 低水位提醒
  - 收退料總檢視
  - overview 交易 CSV 匯出

- `frontend/src/components/inventory/BatchImportPanel.vue`
  - 批次貼上匯入
  - 新治具即時建立
  - 教學模式試跑

- `frontend/src/components/inventory/InventoryExportPanel.vue`
  - 報表 preview
  - `xlsx` / `txt` 匯出
  - `identifier` 相容查詢輸入

- `frontend/src/components/app/AppTopbar.vue`
  - 今日收料 / 今日退料 / 低水位統計

- `frontend/src/components/app/AppGlobalModals.vue`
  - 全域收退料 modal
  - 全域收退料匯出 modal

- `frontend/src/pages/SearchWorkspacePage.vue`
  - 收退料記錄
  - fixture context
  - identifier stock context
  - 最近收 / 退料治具快捷入口的資料來源

### Production

- Router：`backend/app/routers/production.py`
- Service：`backend/app/services/production_service.py`
- Repository：`backend/app/repositories/production_repository.py`
- Model：`backend/app/models/master.py` 的 `ModelStation`
- Model：`backend/app/models/production.py` 的 `FixtureRequirement` / `MachineCapacitySummary`
- Schema：`backend/app/schemas/production.py`

#### API

- `GET /production/model-stations`
- `POST /production/model-stations`
- `PUT /production/model-stations/{row_id}`
- `DELETE /production/model-stations/{row_id}`
- `GET /production/model-stations/export`
- `GET /production/model-stations/template`
- `POST /production/model-stations/import`
- `GET /production/fixture-requirements`
- `POST /production/fixture-requirements`
- `PUT /production/fixture-requirements/{requirement_id}`
- `DELETE /production/fixture-requirements/{requirement_id}`
- `GET /production/fixture-requirements/export`
- `GET /production/fixture-requirements/template`
- `POST /production/fixture-requirements/import`
- `GET /production/capacity/stations/{station_id}`
- `GET /production/models/{model_id}/query`

#### 行為重點

- requirement scope 定案為 `model_id + station_id + fixture_id`
- 同一站點可被多機種共用
- capacity 查詢必須帶 `model_id`
- `current_open_station_count` 已退場
- `get_model_query` 的 `max_open_station_count` 以瓶頸站點最小值為準
- production 頁有兩套前端批次貼上匯入流程：mapping 與 requirement

#### 前端入口

- `frontend/src/pages/ProductionPage.vue`
  - model-station mapping
  - fixture requirement
  - station capacity
  - model query
  - CSV 與貼上匯入

- `frontend/src/components/production/ProductionCapacityPanel.vue`
  - capacity 視覺化顯示

- `frontend/src/pages/SearchWorkspacePage.vue`
  - model query / fixture-to-model context

### Search

- Router：`backend/app/routers/search.py`
- Service：`backend/app/services/search_service.py`
- Repository：`backend/app/repositories/master_repository.py` / `inventory_repository.py` / `production_repository.py` 協同使用
- Schema：`backend/app/schemas/search.py`

#### API

- `GET /search/global`

#### 行為重點

- query 支援 fixture code / name、model、station、storage location、identifier transaction context
- fixture 側 related models 直接來自 `fixture_requirements.model_id`
- 不再從 station 反推 model
- 搜尋頁的「相近編號」提示排序與「最近收 / 退料治具快捷入口」屬於前端行為，不是 search API contract

#### 前端入口

- `frontend/src/pages/SearchWorkspacePage.vue`
  - 雙模式查詢：治具 / 機種
  - fixture detail / model detail
  - fixture 圖片與 transaction context

### Audit

- Router：`backend/app/routers/audit.py`
- Service：`backend/app/services/audit_service.py`
- Model：`backend/app/models/inventory.py` 的 `AuditLog`
- Schema：`backend/app/schemas/audit.py`

#### API

- `GET /audit/logs`

#### 行為重點

- 限 `read` 權限
- 受 customer scope 保護
- 目前主要記錄主資料異動、使用者異動、匯入事件

#### 前端入口

- `frontend/src/api/auditClient.ts`
  - `listAuditLogs`

- 備註：
  - 目前 `App.vue` 沒有渲染 audit 摘要區塊

## 主要資料表欄位使用面

這段只列目前前端真的有用到或 API contract 已正式暴露的欄位。

### `customers`

- 檔案：`backend/app/models/master.py`
- 主要欄位：
  - `id`
  - `code`
  - `name`
- API contract：
  - `assigned_user_ids`
- 前端使用：
  - `frontend/src/components/app/AppTopbar.vue`
    - customer picker
  - `frontend/src/pages/MasterPage.vue`
    - customer tab
    - 指派使用者

### `users`

- 檔案：`backend/app/models/master.py`
- 主要欄位：
  - `id`
  - `username`
  - `display_name`
  - `role`
  - `is_active`
  - `created_at`
  - `updated_at`
- 前端使用：
  - `frontend/src/components/app/AppTopbar.vue`
    - 顯示登入者名稱
  - `frontend/src/pages/MasterPage.vue`
    - user tab
    - customer tab 的指派候選人
- 備註：
  - `password_hash` 不回前端

### `user_customers`

- 檔案：`backend/app/models/master.py`
- 主要欄位：
  - `user_id`
  - `customer_id`
- 前端使用：
  - 不直接顯示資料表本身
  - 透過 customer tab 的 `assigned_user_ids` 間接維護
  - 透過 auth scope 間接影響所有 customer-scoped API

### `fixtures`

- 檔案：`backend/app/models/master.py`
- 主要欄位：
  - `id`
  - `customer_id`
  - `responsible_user_id`
  - `code`
  - `name`
  - `line_storage_location`
  - `department_storage_location`
  - `storage_location`
  - `min_stock_qty`
  - `description`
  - `is_active`
- 前端使用：
  - `frontend/src/pages/MasterPage.vue`
    - fixture 主檔
    - responsible user 維護
  - `frontend/src/pages/InventoryPage.vue`
    - 批次匯入 / 庫存總覽 / overview fixture context
  - `frontend/src/pages/ProductionPage.vue`
    - requirement fixture 選擇
    - production 批次匯入建立新治具
  - `frontend/src/pages/SearchWorkspacePage.vue`
    - fixture 查詢結果 / 圖片 / 儲位

### `machine_models`

- 檔案：`backend/app/models/master.py`
- 主要欄位：
  - `id`
  - `customer_id`
  - `code`
  - `name`
  - `is_active`
- 前端使用：
  - `frontend/src/pages/MasterPage.vue`
  - `frontend/src/pages/ProductionPage.vue`
  - `frontend/src/pages/SearchWorkspacePage.vue`

### `stations`

- 檔案：`backend/app/models/master.py`
- 主要欄位：
  - `id`
  - `customer_id`
  - `code`
  - `name`
  - `is_active`
- 前端使用：
  - `frontend/src/pages/MasterPage.vue`
  - `frontend/src/pages/ProductionPage.vue`
  - `frontend/src/pages/SearchWorkspacePage.vue` 的 model / station context

### `model_stations`

- 檔案：`backend/app/models/master.py`
- 主要欄位：
  - `id`
  - `model_id`
  - `station_id`
- 前端使用：
  - `frontend/src/pages/ProductionPage.vue`
    - mapping 清單
    - available requirement stations
    - station 下拉收斂

### `fixture_requirements`

- 檔案：`backend/app/models/production.py`
- 主要欄位：
  - `id`
  - `model_id`
  - `station_id`
  - `fixture_id`
  - `required_qty`
- 前端使用：
  - `frontend/src/pages/ProductionPage.vue`
    - requirement 清單 / 編輯 / 匯入匯出
    - capacity / model query
  - `frontend/src/pages/SearchWorkspacePage.vue`
    - fixture 關聯機種
    - model detail / station detail

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
- 前端使用：
  - `frontend/src/pages/InventoryPage.vue`
    - 最近紀錄
    - overview
  - `frontend/src/pages/SearchWorkspacePage.vue`
    - fixture transaction context
    - 最近收 / 退料治具快捷入口排序
  - `frontend/src/components/app/AppTopbar.vue`
    - today receipt / return summary

### `material_transaction_items`

- 檔案：`backend/app/models/inventory.py`
- 主要欄位：
  - `transaction_id`
  - `fixture_id`
  - `ownership_type`
  - `identifier`
  - `quantity`
  - `note`
- 前端使用：
  - `frontend/src/components/inventory/BatchImportPanel.vue`
    - 批次收退料 payload
  - `frontend/src/pages/InventoryPage.vue`
    - overview rows
  - `frontend/src/pages/SearchWorkspacePage.vue`
    - transaction rows
    - 最近收 / 退料治具快捷入口的 fixture code 來源

### `fixture_stock_levels`

- 檔案：`backend/app/models/inventory.py`
- 主要欄位：
  - `fixture_id`
  - `min_stock_qty`
  - `warning_threshold`
  - `alert_enabled`
- 前端使用：
  - `frontend/src/pages/MasterPage.vue`
    - 治具最低庫存
  - `frontend/src/pages/InventoryPage.vue`
    - 低水位提醒 / 水位條
  - `frontend/src/pages/ProductionPage.vue`
    - model query 明細
  - `frontend/src/pages/SearchWorkspacePage.vue`
    - fixture / model context
- 備註：
  - `warning_threshold`、`alert_enabled` 目前沒有獨立前端編輯入口

### `fixture_stock_summary`

- 檔案：`backend/app/models/inventory.py`
- 主要欄位：
  - `fixture_id`
  - `stock_qty`
  - `returned_qty`
  - `last_transaction_at`
  - `stock_status`
- 前端使用：
  - `frontend/src/pages/InventoryPage.vue`
    - 庫存總覽 / KPI / 水位條
  - `frontend/src/pages/SearchWorkspacePage.vue`
    - 查詢結果 / KPI
  - `frontend/src/pages/ProductionPage.vue`
    - model query / capacity context

### `identifier_stock_summary` API response

- 資料來源：
  - `backend/app/services/inventory_service.py`
  - `GET /inventory/identifier-stock-summary`
- 主要欄位：
  - `fixture_id`
  - `identifier`
  - `stock_qty`
- 前端使用：
  - `frontend/src/pages/SearchWorkspacePage.vue`
    - fixture 識別碼庫存標籤
    - model query 內的識別碼庫存摘要

## 現況提醒

- `InventoryService` 依賴 `openpyxl` 輸出 `xlsx` 報表；若環境沒安裝，backend import 與 pytest 會失敗。
- onboarding / guided tour 完全是前端功能，不要在 backend 補假的 tutorial router。
- `App.vue` 目前沒有渲染 audit 摘要區塊，因此 `/audit/logs` 雖保留，但不是首頁主流程的一部分。
