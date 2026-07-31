# Backend Map

這份文件回答三件事：

- 後端各模組現在的責任分工
- 前端主要頁面各自依賴哪些後端 API / 資料表
- 改資料模型或啟動流程時最少要連動檢查哪些地方

補充：

- 近期 `AppTopbar` / `AppMobileDrawer` / `SearchHeroSection` / `InventoryOverviewPanel` / `MasterPage` / `MasterListPanel` 的 responsive、accessibility、互動優化都屬前端調整，不需要新增 backend API 或 schema 變更。

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
  - 已登入 `admin` / `user` 都依 `user_customers` 解析可見客戶
  - `manage` 權限不會略過 customer scope；`guest` 仍為全客戶唯讀

- `backend/app/core/database.py`
  - `engine`
  - `SessionLocal`
  - `get_db`

- `backend/app/core/migrations.py`
  - Alembic upgrade 執行
  - runtime migration gate 檢查
  - fail-loud compatibility report 組裝
  - explicit offline compat fix helper
  - structured gate outcome logging: `passed` / `blocked` / `compat_fixes_applied`
  - Alembic URL 寫入 ConfigParser 前會 escape `%`，支援 percent-encoded 密碼

- `backend/app/core/logging.py`
  - backend app logger 初始化
  - standalone CLI 補 stdout handler
  - 有既有 handler 時只把 `backend.app` logger 拉到 `INFO`
  - `logs/audit.log` rotating file handler 初始化
  - request / domain audit file log 共用寫入入口

- `backend/app/core/audit_logging.py`
  - FastAPI request-level audit middleware
  - 每次 request 寫入 `request_audit`
  - 記錄 actor / request / response / error metadata

- `backend/app/core/schema_patch.py`
  - legacy DB runtime patch 保底
  - 現在只保留 `0002_schema_backfill` 的歷史 backfill 依賴，不是 runtime startup patch 機制

- `backend/app/tools/migration_check.py`
  - 離線 migration compatibility 檢查入口
  - 可顯式套用 `alembic_version` 相容修補
  - 給 fail-loud startup 錯誤訊息作為人工處理入口

- `MIGRATION_GATE_RUNBOOK.md`
  - 環境掃描、部署前確認、部署後 log 驗證流程

- `MIGRATION_ENVIRONMENT_INVENTORY.md`
  - 各部署環境 revision / gate 狀態 / deploy 次數台帳模板

- `backend/app/core/errors.py`
  - FastAPI error handler 註冊
  - `RequestValidationError` payload 序列化保底

- `backend/app/utils/identifier_rules.py`
  - `identifier` 寫入正規化與查詢解析的單一規則來源
  - 只有純數字且 `1-4` 碼會左補零並展開短碼相容查詢
  - 其餘值一律視為 legacy 原值放行 / 原值精確查詢

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
- 前端 onboarding 目前已拆成多個可選 flow；backend 仍不需要新增 tutorial router

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
- `GET /master/fixtures/quality`
- `POST /master/fixtures`
- `PUT /master/fixtures/{fixture_id}`
- `DELETE /master/fixtures/{fixture_id}?customer_id=...&delete_transactions=false`
- `DELETE /master/models/{model_id}?customer_id=...`
- `DELETE /master/stations/{station_id}?customer_id=...`
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

### Inventory Admin Ledger

- Router：`backend/app/routers/inventory.py`
- Service：`backend/app/services/inventory_service.py`
- Repository：`backend/app/repositories/inventory_repository.py`
- Schema：`backend/app/schemas/inventory.py`

#### API

- `GET /inventory/dashboard-summary`
- `GET /inventory/admin/transactions`
- `DELETE /inventory/admin/transactions/{transaction_id}`
- `POST /inventory/admin/recalculate`

#### 行為重點

- dashboard summary 會直接回傳 `today_receipt_qty / today_return_qty / low_stock_count / recent_receipt_entries / recent_return_entries`
- topbar 今日統計不再依賴前端抓最近 200 筆交易後自行過濾
- 帳目管理清單以 transaction 為單位分頁，response 為 `items / page / page_size / total`
- `fixture_code` / `transaction_no` / `created_by` / `transaction_type` 都由後端過濾，不再只依賴前端對最近 200 筆做搜尋
- transaction-id 分頁子查詢以 `material_transactions.id desc` 排序，避免 MySQL 在 `DISTINCT id` 查詢上使用 `occurred_at` 排序時拋出 `500`
- detail payload 直接內含 transaction items，前端選取案件後不需要再額外打一支 detail API

#### 行為重點

- `customers` / `users` 是 `manage` 權限
- `fixtures` / `models` / `stations` 是 `write` 權限
- 治具永久刪除限定 `manage`（admin），且 admin 必須已透過 `user_customers` 指派到目標客戶
- `delete_transactions=false`：保留 transaction item，將 `fixture_id` 設為 `NULL` 並保存治具 code/name snapshot
- `delete_transactions=true`：只刪除該治具 item；混合交易保留其他 item，空交易才刪除 parent
- 刪除流程由 `MasterService` 在單一 transaction 內協調 inventory history、requirements、stock level/summary、capacity cache 與 audit
- 機種永久刪除同樣限定 `manage`（admin），並會同步刪除相關 `model_stations`、`fixture_requirements`、受影響 `machine_capacity_summary`
- 站點永久刪除同樣限定 `manage`（admin），並會同步刪除相關 `model_stations`、`fixture_requirements`、該站點 `machine_capacity_summary`
- 機種/站點刪除 response 會回傳實際刪除的 mapping / requirement / capacity summary 筆數
- `fixtures.code` 的 `(customer_id, code)` 唯一鍵在刪除後可重新使用
- 回傳 `FixtureDeleteRead` 提供受影響 item/transaction/requirement 數量
- `fixtures.code` 使用 `(customer_id, code)` 唯一鍵
- `fixtures.responsible_user_id` 候選名單來自該客戶已指派使用者
- fixture image 採檔案式讀取，不走 DB 圖片表
- admin 可用 `GET /master/fixtures/quality` 檢查名稱、儲位、圖片、水位、機種關聯與 identifier/summary 庫存一致性
- 品質報表目前只回傳資料與 issue code；問題類型對應的跳轉規則與列內修正互動由前端 `FixtureQualityPanel.vue` 決定
- 前端對 `missing_storage_location` / `missing_min_stock_qty` 已改成列內直接更新；送回既有 `PUT /master/fixtures/{fixture_id}`，並以 `line_storage_location` / `department_storage_location` 兩個欄位分開提交，規則為「分開填寫，只填一個也可」
- `missing_storage_location` 只在 `line_storage_location` 與 `department_storage_location` 都缺時才成立；只填其中一欄不再被報成缺儲位

#### 前端入口

- `frontend/src/components/app/AppTopbar.vue`
  - customer list / current customer picker

- `frontend/src/pages/MasterPage.vue`
  - fixture / model / station / customer / user 維護
  - admin 治具資料品質檢查
  - `/master/*` route-to-tab 同步
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
  - 接收其他頁面帶入的 `mode` / `q` route query

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
- `GET /inventory/transactions/overview`
- `GET /inventory/transactions/export`
- `GET /inventory/transactions/export-report`
- `GET /inventory/transactions/export-report/preview`
- `GET /inventory/transactions/template`
- `POST /inventory/transactions/import`

#### 行為重點

- 交易明細正式使用單一 `identifier`
- `identifier` 寫入與查詢共用 `backend/app/utils/identifier_rules.py`
- 純數字且 `1-4` 碼寫入前會左補零為 `4` 碼
- 純數字且長度大於 `4` 碼會視為 legacy 值原樣寫入
- 含非數字的值也視為 legacy 值原樣寫入
- 查詢 / 匯出篩選相容舊資料
  - `1-4` 碼純數字會同時匹配不同 padding 寬度的 legacy 值
  - 其餘輸入值會以原值精確查詢
- `ownership_type` 在 transaction item 層
- 庫存來源算法固定為：
  - `customer_supplied_qty = 客供收料 - 客供退料`
  - `self_purchased_qty = 自購收料 - 自購退料`
  - `stock_qty = customer_supplied_qty + self_purchased_qty`
- `/inventory/stock`、`/inventory/alerts`、`/inventory/identifier-stock-summary` 都回傳總庫存、客供庫存與自購庫存。
- 客供 / 自購收料在作業上分開，且 datecode 不跨來源重複；退料可用量維持以 `fixture_id + identifier` 總量查核。
- 批次貼上匯入前端仍走 `/receipts` / `/returns`
- 前端批次貼上欄允許直接插入 literal `Tab`，組成 `fixture-code<TAB>identifier<TAB>quantity` 後再由前端解析並送到 `/receipts` / `/returns`
- 前端顯示文案可將 `identifier` 呈現為 `datecode/編號`，但 backend API / schema / DB 欄位名仍維持 `identifier`
- CSV 匯入走 `/inventory/transactions/import`
- `POST /inventory/receipts` 與 `POST /inventory/returns` 的 `transaction_no` 現在是明確必填；repository 不再自動產生 fallback 單號
- 交易歷史讀取模型 (`/inventory/transactions`、`/inventory/admin/transactions`、`/inventory/transactions/overview`) 仍容許 legacy `NULL / 空字串 transaction_no`，repository 讀取時會正規化成 `None`
- overview 查詢支援 `transaction_type` / `ownership_type` / `date_from` / `date_to` / `fixture_code` / `transaction_no` / `identifier` / `created_by`
- `ownership_type` 可使用 `customer_supplied` 或 `self_purchased`，直接在 item-level 查詢套用，確保分頁 `total` 與結果一致
- `/inventory/transactions/overview` 直接回傳 item-level page contract：`items / page / page_size / total`
- overview 的 `fixture_code` filter 現在可接受逗號分隔的多關鍵字，供前端把頁內 fixture filter 與全域 fixture keyword 一起帶入
- 報表匯出支援 `summary|detail` 與 `xlsx|txt`
- 匯出 preview 由 `/inventory/transactions/export-report/preview` 提供
- 收退料報表與 preview 都支援 `ownership_type=customer_supplied|self_purchased`，並在 transaction item 層套用來源條件
- `BatchImportPanel` 預覽現在會同時使用：
  - `GET /inventory/stock`
  - `GET /inventory/identifier-stock-summary`
  顯示該 datecode 的總 `目前庫存` 與 `交易後庫存`
- onboarding 教學模式不會新增後端 tutorial endpoint；只是前端不真正送出 `/receipts` 或 `/returns`

- 被刪治具若選擇保留歷史，交易查詢與匯出以 `deleted_fixture_code` / `deleted_fixture_name` fallback 顯示
- 保留歷史的 orphan item 不納入目前庫存與 fixture 聚合，但仍受 parent transaction 的 customer scope 保護
#### 前端入口

- `frontend/src/pages/InventoryPage.vue`
  - 收料 / 退料主作業
  - 內嵌批次貼上匯入
  - 庫存總覽
  - 低水位提醒
  - 收退料總檢視
  - overview 分頁 detail-row query

- `frontend/src/components/inventory/BatchImportPanel.vue`
  - 批次貼上匯入
  - 手動 `Tab` 分隔輸入
  - `ownership_type` 由整批 `來源` 控制，送出時統一套用到所有 items
  - 預填 fixture shortcut
  - 預填 fixture shortcut 入口預設進 quick-entry，batch paste editor 改為按需展開
  - 新治具即時建立
  - 預覽表 `目前庫存` / `交易後庫存`
  - 同批重複 `fixture + identifier` 的逐列累計預覽
  - submit 前相同 `fixture + identifier` 合併
  - 前端寫入前 `identifier` 正規化改走 `frontend/src/utils/identifier.ts`
  - 教學模式試跑

- `frontend/src/components/app/ExportCenterPanel.vue`
  - 全域匯出中心
  - dataset / format / range 選擇
  - 前端會先依 session role 隱藏 admin-only `治具資料品質` 匯出，避免一般使用者撞到 `GET /master/fixtures/quality` 的 `manage` 權限邊界
  - 收退料報表 preview 與 `xlsx` / `txt` 匯出

- `frontend/src/components/app/AppTopbar.vue`
  - 今日收料 / 今日退料 / 低水位統計
  - 上述統計資料由 `GET /inventory/dashboard-summary` 提供
  - 低水位快捷收退料入口（僅非 guest 顯示）

- `frontend/src/components/app/AppGlobalModals.vue`
  - 全域收退料 modal
  - 全域收退料匯出 modal
  - preset fixture code 傳入 `BatchImportPanel`

- `frontend/src/pages/SearchWorkspacePage.vue`
  - 收退料記錄
  - fixture context
  - identifier stock context
  - 最近收 / 退料治具快捷入口的資料來源
  - onboarding 分類入口
  - fixture detail 轉跳 `/inventory/overview`，handoff 只帶 `fixture_code` 與 `return_to`

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
- `POST /production/fixture-requirements/copy`
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
- frontend 目前會先依 `model_stations` 收斂可選站點；backend 仍以 `get_model_station(...)` 作最終防線，拒絕未映射的 `model_id + station_id`
- create / update requirement 時若底層 mapping 尚未存在，service 會先自動補建 `model_station`
- copy endpoint 以 `source model + source station` 複製整組需求到 `target model + target station`，同時支援同機種站點與跨機種流程
- copy 預設跳過目標既有治具；`overwrite_existing=true` 只更新數量不同的衝突資料，相同資料仍計入 skipped
- 目標 mapping 不存在時會在同一交易中建立；response 回傳 source / created / updated / skipped / mapping-created 計數並寫入單筆 copy audit

#### 前端入口

- `frontend/src/pages/ProductionPage.vue`
  - overview / configure route orchestration
  - model-station mapping
  - fixture requirement
  - same-model / cross-model requirement copy
  - station capacity
  - model query
  - CSV 與貼上匯入
  - `return_to` back flow 與 unsaved-change guards

- `frontend/src/components/production/ProductionCapacityPanel.vue`
  - capacity 視覺化顯示

- `frontend/src/utils/productionStations.ts`
  - 依 `model_stations` 推導目前機種可用站點
  - 避免前端預設站點打到未映射的 capacity query

- `frontend/src/pages/SearchWorkspacePage.vue`
  - model query / fixture-to-model context

### Search

首頁 `/search` 報表模式的 `InventoryRelationsPage.vue` 不走獨立 search aggregate API；它在目前客戶範圍內組合既有 master / inventory / production 端點：

- `/master/fixtures`、`/master/models`、`/master/stations`
- `/production/model-stations`、`/production/fixture-requirements`
- `/production/models/{model_id}/query`（報表選機種＋全部站點時取得所有 mapped station capacity）
- `/production/capacity/stations/{station_id}?model_id=...`（報表指定單一站點時取得該站 capacity）
- `/inventory/stock`、`/inventory/identifier-stock-summary`
- `/inventory/transactions/overview`（今日或指定日期收／退料篩選，前端逐頁取得符合的 fixture codes）
- `/master/fixtures/{fixture_code}/image`（點擊報表治具代碼時載入圖片）

以下 Search module 服務所有角色在 `/search` 的查詢模式，以及相容入口 `/search/detail` 的分頁搜尋與 lazy context。

- Router：`backend/app/routers/search.py`
- Service：`backend/app/services/search_service.py`
- Repository：`backend/app/repositories/search_repository.py` 主查詢，並協同 `master_repository.py` / `inventory_repository.py` / `production_repository.py`
- Schema：`backend/app/schemas/search.py`

#### API

- `GET /search/global`
- `GET /search/fixtures/{fixture_id}/context`
- `GET /search/models/{model_id}/context`

#### 行為重點

- `GET /search/global` 支援 `entity_type`、`page`、`page_size`
- global search response 是有上限的 page contract：`items / total / page / page_size / has_more`
- query 支援 fixture code / name、model、station、storage location
- 排序規則集中在 `search_repository.py`，目前是 active first + exact/prefix/contains ranking
- fixture 側 related models 直接來自 `fixture_requirements.model_id`
- 不再從 station 反推 model
- fixture / model detail context 改走獨立 lazy endpoint
- fixture detail 只保留近期交易預覽；完整歷史改由前端轉跳 `/inventory/overview`，handoff 不會再從預覽交易反推 `date_from / date_to`
- 搜尋頁的「相近編號」提示排序與「最近收 / 退料治具快捷入口」屬於前端行為，不是 search API contract

#### 前端入口

- `frontend/src/pages/SearchWorkspacePage.vue`
  - route：`/search/detail`
  - 雙模式查詢：治具 / 機種
  - load more 主結果分頁
  - fixture detail / model detail lazy 載入
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
- `AuditService.record()` 會同步寫 DB `audit_logs` 與 `logs/audit.log`
- 全域 request audit 不經 `/audit/logs` API 暴露，而是直接落檔到 `logs/audit.log`

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
  - `fixture_id`（nullable；治具刪除後可為 `NULL`）
  - `deleted_fixture_code`
  - `deleted_fixture_name`
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
- UI 文案若改成 `datecode/編號`，也不要回頭更名 backend 的 `identifier` 欄位契約。
- 查詢排序 contract 在 `backend/app/repositories/search_repository.py`；若要改搜尋結果優先順序，先改這裡與對應測試，不要只在前端重排。
- 搜尋頁效能目前依賴 `0011_search_indexes` 提供的名稱 / 儲位 / 交易時間索引。
- 如果要改 `identifier` 規則，優先改 `backend/app/utils/identifier_rules.py` 與 `backend/tests/test_identifier_rules.py`，不要把規則重新散回 schema / service。
- 若前端也需要改同語意規則，優先同步 `frontend/src/utils/identifier.ts` 與 `frontend/src/utils/identifier.test.ts`，不要回到元件內重寫 `padStart(4)`。
- `0014_fixture_deletion` 讓 transaction item 可保留被刪治具的 code/name snapshot；刪除治具不再被舊 FK 阻擋。
- 目標 MySQL 已驗證 revision `0014_fixture_deletion`、nullable FK、`ON DELETE SET NULL` 與 snapshot backfill。
- customer scope 的權威行為在 `backend/app/core/auth.py`：已登入 admin 不具全客戶 bypass，需有 `user_customers` 指派。
- `App.vue` 目前沒有渲染 audit 摘要區塊，因此 `/audit/logs` 雖保留，但不是首頁主流程的一部分。
- migration/schema patch 的退場方向是三段式：
  - 先保留觀測與離線 compat 工具
  - 再用 runtime fail-loud gate 阻止低於 `0011_search_indexes` 的環境自動啟動
  - 最後再移除 `schema_patch.py` 與 legacy revision normalization
- 目前 repo 只補到 structured startup log 與離線掃描工具；所有已知環境的 inventory 盤點與 `N` 次連續通過統計仍需由運維流程補齊。
- Docker 測試環境已完成一次真實驗證：`fixture_m_lite_api` 的 `docker logs` 可直接看到 `migration_runtime_gate`，且 `source=app_startup`、`outcome=passed`。
