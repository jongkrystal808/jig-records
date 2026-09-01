# Backend Map

這份文件回答三件事：

- 後端各模組現在的責任分工
- 前端主要頁面各自依賴哪些後端 API / 資料表
- 改資料模型或啟動流程時最少要連動檢查哪些地方

補充：

- 近期 `AppTopbar` / `AppMobileDrawer` / `SearchHeroSection` / `InventoryOverviewPanel` / `MasterPage` / `MasterListPanel` 的 responsive、accessibility、互動優化都屬前端調整，不需要新增 backend API 或 schema 變更。
- 主資料唯讀摘要、全域系統確認視窗、登出 URL 導向、route dynamic import 與手機報表卡片拆分也都是前端責任，不需要新增 backend endpoint 或 schema。

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
  - 掛載 `auth` / `master` / `inventory` / `production` / `search` / `storage` / `audit`

- `backend/app/core/auth.py`
  - JWT session 解析
  - `read` / `write` / `manage` / `super_manage` 權限檢查
  - customer scope 驗證
  - 已登入 `super_admin` / `admin` / `user` 都依 `user_customers` 解析可見客戶
  - `manage` / `super_manage` 權限不會略過 customer scope；`guest` 仍為全客戶唯讀

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

- `backend/app/schemas/common.py`
  - `ORMModel` 提供 `from_attributes` 與共用日期序列化契約
  - schema 中的 `datetime` 在 JSON／FastAPI response model 一律輸出 `YYYY-MM-DD`；使用 Pydantic 2 `field_serializer`，不再依賴 deprecated `json_encoders`

- `backend/app/utils/identifier_rules.py`
  - `identifier` 寫入正規化與查詢解析的單一規則來源
  - 只有純數字且 `1-4` 碼會左補零並展開短碼相容查詢
  - 其餘值一律視為 legacy 原值放行 / 原值精確查詢

- `backend/app/models/production.py`
  - `FixtureRequirement.designated_mode` 與 `FixtureRequirementIdentifier` 保存機種／站點／治具需求的指定 identifier
  - 指定值只引用庫存 identifier 字串，不改寫交易或治具主檔

- `backend/app/services/production_service.py`
  - 儲存指定模式前驗證 identifier 屬於同客戶、同治具且仍有正庫存
  - 指定模式產能只加總所選 identifier；一般模式維持使用治具總庫存

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
- `POST /auth/password`（登入者輸入目前密碼後修改自己的密碼）
- `GET /auth/users`
- `GET /auth/users/form-export`（super-manage-only；依 Form 使用者關鍵字／狀態完整串流 CSV）
- `POST /auth/users`
- `PUT /auth/users/{user_id}`
- `POST /auth/users/{user_id}/reset-password`

#### 行為重點

- 僅 `super_admin` 可管理使用者與重設他人密碼；`admin` / `user` 可透過 `/auth/password` 修改自己的密碼
- `guest` 只會拿到 guest session，不可寫
- `UserCreate` / `UserUpdate` 的 `role` 僅接受 `super_admin`、`admin` 或 `user`；`guest` 不可建立為一般登入帳號，`write` guard 也會拒絕任何不合法的 signed-in role
- 系統阻止停用或降級最後一位啟用中的 `super_admin`；migration `0017_super_admin_role` 會把既有 bootstrap `admin` 帳號提升為 `super_admin`
- 密碼雜湊為 PBKDF2，並相容舊 sha256 資料
- `allowed_customer_ids` 是 user API 的正式客戶範圍契約；Modern 使用者編輯器可直接維護，更新省略此欄位時後端保留既有指派，Admin 也不具清空或全客戶 bypass 特例
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
- `GET /master/form-export`（fixture / model / station / customer / fixture-images；沿用 Form 篩選與 assigned-customer scope，完整串流 CSV）
- `GET /master/fixtures`
- `GET /master/fixtures/page`（Form UI server-side 關鍵字／狀態／圖片狀態篩選與 50／100 筆分頁）
- 圖片狀態篩選只掃描 customer-scoped／安全 legacy 圖片檔名，再把治具編號條件交給分頁 SQL；不先載入客戶的完整治具 ORM 清單
- `GET /master/customers/page`、`GET /auth/users/page`（Form UI 客戶／使用者關鍵字、狀態與分頁；客戶頁直接以 customer scope、關鍵字、offset/limit 在 SQL 執行，不先載入完整可見集合）
- 分頁使用者回應批次載入 `allowed_customer_ids` 與精簡 `allowed_customers`，避免逐列 N+1 查詢；Form UI 客戶權限選項另以 `/master/customers/page` 的 50 筆搜尋頁按需載入
- `GET /master/fixtures/quality`
- `POST /master/fixtures`
- `PUT /master/fixtures/{fixture_id}`
- `DELETE /master/fixtures/{fixture_id}?customer_id=...&delete_transactions=false`
- `DELETE /master/models/{model_id}?customer_id=...`
- `DELETE /master/stations/{station_id}?customer_id=...`
- `GET /master/fixtures/export`
- `GET /master/fixtures/template`
- `POST /master/fixtures/import`
- `POST /master/fixtures/{fixture_id}/image?customer_id=...`
- `POST /master/fixtures/images/batch?customer_id=...`
- `GET /master/fixtures/{fixture_code}/image?customer_id=...`
- `GET /master/models`
- `GET /master/models/page`（Form UI server-side 關鍵字／狀態篩選與分頁）
- `POST /master/models`
- `PUT /master/models/{model_id}`
- `GET /master/models/export`
- `GET /master/models/template`
- `POST /master/models/import`
- `GET /master/stations`
- `GET /master/stations/page`（Form UI server-side 關鍵字／狀態篩選與分頁）
- `POST /master/stations`
- `PUT /master/stations/{station_id}`
- `GET /master/stations/export`
- `GET /master/stations/template`
- `POST /master/stations/import`

### Fixture Storage Index

- Router：`backend/app/routers/storage.py`
- Service：`backend/app/services/storage_service.py`
- Repository：`backend/app/repositories/storage_repository.py`
- Model：`backend/app/models/storage.py`
- Schema：`backend/app/schemas/storage.py`
- Migration：`backend/alembic/versions/0019_fixture_storage_index.py`

#### API

- `GET /storage/overview?customer_id=...&keyword=...`
- `POST /storage/containers`
- `PUT /storage/containers/{container_id}?customer_id=...`
- `DELETE /storage/containers/{container_id}?customer_id=...`
- `POST /storage/codes/register`
- `PUT /storage/codes/organize`
- `GET /storage/fixtures/{fixture_id}/placements`
- `POST /storage/fixtures/{fixture_id}/sync`
- `PUT /storage/fixtures/{fixture_id}/placements`

#### 行為重點

- 治具新增、更新與 CSV 匯入會拆分半形／全形逗號儲位文字並同步位置索引
- 未知代碼自動建立為 customer-scoped `storage_codes`；代碼可稍後整理到 `storage_containers`
- 只有在治具需求關聯能唯一判定時，`T2` 類短碼才解析為完整 `model_id + station_id`
- 已知位置數量總和不可超過 `fixture_stock_summary.stock_qty`；空白數量保留為待分配
- 所有讀寫 API 都沿用 assigned-customer scope；guest 只能讀取
- storage overview 由 repository 以 `storage_codes + storage_containers + fixture_placements` 單次聚合取得代碼、容器與數量摘要；service 不再逐代碼查 container／placement。效能回歸測試固定驗證 30 個代碼仍最多 2 次 SQL

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

- `customers` / `users` 是 `super_manage` 權限；ledger / quality 維持 `manage`
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
- fixture image 採檔案式儲存，不走 DB 圖片表；正式路徑為 `FIXTURE_IMAGE_DIR/<customer_id>/<fixture_code>.<ext>`
- 圖片 GET 必填 `customer_id` 並套用 assigned-customer scope；舊平面檔只在治具代碼全系統唯一時相容讀取，跨客戶同碼時不會共用舊圖
- 治具更名的圖片搬移可在 DB transaction 失敗時回復；永久刪除完成後只清理該 customer 的圖片
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
- 退料可用量依 `fixture_id + identifier + ownership_type` 分類查核，不能用另一來源的餘額退料。
- 收退料寫入會先依 fixture id 固定順序取得 row lock；identifier/ownership ledger 與 stock summary 使用 locking read，批次每筆 flush 後才驗證下一筆，避免 MySQL 並行 lost update 與雙重超退。
- 批次貼上匯入前端仍走 `/receipts` / `/returns`
- 前端方格將固定的治具、identifier、數量欄序列化為 `fixture-code<TAB>identifier<TAB>quantity`，再沿用既有解析與 `/receipts` / `/returns`
- 前端顯示文案可將 `identifier` 呈現為 `datecode/編號`，但 backend API / schema / DB 欄位名仍維持 `identifier`
- CSV 匯入走 `/inventory/transactions/import`
- `POST /inventory/receipts`、`POST /inventory/returns` 與 CSV 匯入都以登入 session 的 `user_id` 決定操作人；payload `created_by`、CSV 同名欄位與舊 `operator_name` query 即使出現也不參與寫入。新交易同時保存 `actor_user_id` 與不可隨使用者改名而變動的 `created_by` 顯示名稱快照。
- `POST /inventory/receipts` 與 `POST /inventory/returns` 的 `transaction_no` 現在是明確必填；repository 不再自動產生 fallback 單號
- 交易歷史讀取模型 (`/inventory/transactions`、`/inventory/admin/transactions`、`/inventory/transactions/overview`) 仍容許 legacy `NULL / 空字串 transaction_no`，repository 讀取時會正規化成 `None`
- overview 查詢支援 `transaction_type` / `ownership_type` / `date_from` / `date_to` / `fixture_code` / `transaction_no` / `identifier` / `created_by`；`transaction_type` 與 `ownership_type` 可用重複 query key 複選，同一分類為 OR、跨分類為 AND，單一值請求仍相容
- `ownership_type` 可使用 `customer_supplied` 或 `self_purchased`；`/inventory/transactions`、overview 與 `/inventory/transactions/export` 都會在 item-level 套用來源條件，確保畫面與匯出結果一致
- `/inventory/transactions/export` 不接受結果筆數上限；後端以 keyset 分批讀取交易並串流 CSV，完整輸出符合客戶範圍與篩選條件的交易資料
- `backend/app/utils/csv_tools.py` 統一保護 CSV 字串欄位：以 `=`、`+`、`-`、`@` 起始的內容加上單引號前綴；transaction report 與 configuration report 的 XLSX renderer 套用相同規則，數值欄位維持數值型別
- `/inventory/transactions/overview` 直接回傳 item-level page contract：`items / page / page_size / total`
- overview 的 `fixture_code` filter 現在可接受逗號分隔的多關鍵字，供前端把頁內 fixture filter 與全域 fixture keyword 一起帶入
- 報表匯出支援 `summary|detail` 與 `xlsx|txt`
- 匯出 preview 由 `/inventory/transactions/export-report/preview` 提供
- 收退料報表與 preview 都支援 `ownership_type=customer_supplied|self_purchased`，並在 transaction item 層套用來源條件
- MySQL staging concurrency regression 位於 `backend/tests/test_inventory_concurrency_mysql.py`；只有設定 `MYSQL_STAGING_DATABASE_URL` 時執行，使用兩個獨立 session 驗證並行收料增量與超退拒絕，結束後清理測試資料。
- `BatchImportPanel` 預覽現在會同時使用：
  - `GET /inventory/stock`
  - `GET /inventory/identifier-stock-summary`
  顯示該 datecode 的總 `目前庫存` 與 `交易後庫存`
- 前端責任已拆分：`useInventoryBatchParser.ts` 負責解析與退料庫存預檢，`useInventoryBatchPreviewState.ts` 負責預覽／重複列合併，`useInventoryBatchSubmit.ts` 負責 receipts／returns 分組送出與重複單號確認
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
  - 預填 fixture shortcut 直接帶入方格空白列；快速新增與多列貼上使用同一個 grid editor
  - 新治具即時建立
  - 預覽表 `目前庫存` / `交易後庫存`
  - 同批重複 `fixture + identifier` 的逐列累計預覽
  - payload 組裝與送出生命週期位於 `frontend/src/composables/useInventoryBatchSubmit.ts`
  - submit 前相同 `fixture + identifier` 合併
  - 前端寫入前 `identifier` 正規化改走 `frontend/src/utils/identifier.ts`
  - 教學模式試跑

- `frontend/src/components/app/ExportCenterPanel.vue`
  - 全域匯出中心
  - dataset / format / range 選擇
  - 前端會先依 session role 隱藏僅限 `admin` / `super_admin` 的 `治具資料品質` 匯出，避免一般使用者撞到 `GET /master/fixtures/quality` 的 `manage` 權限邊界
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
- `GET /production/form-export`（requirements / mappings；沿用 customer + model + station + keyword 篩選，完整串流 CSV）
- `GET /production/model-stations/page`（Form UI join 後的機種／站點名稱、篩選與分頁）
- `POST /production/model-stations`
- `PUT /production/model-stations/{row_id}`
- `DELETE /production/model-stations/{row_id}`
- `GET /production/model-stations/export`
- `GET /production/model-stations/template`
- `POST /production/model-stations/import/preview`（逐列回傳 new / unchanged / error 與摘要計數）
- `POST /production/model-stations/import`
- `GET /production/fixture-requirements`
- `GET /production/fixture-requirements/page`（Form UI join 後的需求、目前庫存、篩選與分頁）
- `POST /production/fixture-requirements`
- `POST /production/fixture-requirements/copy`
- `PUT /production/fixture-requirements/{requirement_id}`
- `DELETE /production/fixture-requirements/{requirement_id}`
- `GET /production/fixture-requirements/export`
- `GET /production/fixture-requirements/template`
- `POST /production/fixture-requirements/import/preview`（並列既有／匯入需求量，逐列回傳 new / unchanged / conflict / error）
- `POST /production/fixture-requirements/import`
- `GET /production/capacity/stations/{station_id}`
- `GET /production/models/{model_id}/query`

#### 行為重點

- requirement scope 定案為 `model_id + station_id + fixture_id`
- 同一站點可被多機種共用
- capacity 查詢必須帶 `model_id`
- `current_open_station_count` 已退場
- `get_model_query` 的 `max_open_station_count` 以瓶頸站點最小值為準
- station capacity 與 model query 共用 model-scoped requirement projection；fixture、stock summary、stock level 與 designated stock 在固定批次查詢中取得，不再逐站／逐 requirement 查詢。效能回歸測試以 25 筆需求驗證 model query 最多 5 次 SQL
- production 頁有兩套前端批次貼上匯入流程：mapping 與 requirement
- production import 預覽先在 service 依客戶範圍比對正式資料；requirement 的相同 `model + station + fixture` 若數量不同標記為 conflict。import 預設 `overwrite_existing=false`，衝突只略過；只有 UI 明確確認並送出 `overwrite_existing=true` 才更新數量，未出現在匯入內容的其他綁定不會刪除
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

首頁 `/search` 報表模式的 `InventoryRelationsPage.vue` 使用獨立的 inventory 報表 read model：

- Router：`backend/app/routers/inventory.py`
- Service：`backend/app/services/configuration_report_service.py`
- Repository：`backend/app/repositories/configuration_report_repository.py`
- Schema：`backend/app/schemas/inventory.py`
- `GET /inventory/configuration-report`（server-side 篩選、排序與分頁；手機提供每頁 20／50、桌面 50／100，API 上限 200；包含低水位／未配置、來源庫存統計及每個機種站點的可開站數；`fixture_status`、`water_status`、`configuration_status`、`transaction_type`、`ownership_type` 支援重複 query key 複選；fixture 預設 active，舊 `fixture_status=all` 仍相容；固定回傳關聯明細列）
- `GET /inventory/configuration-report/options`（依 `priority` 與 `fixture_status` 回傳聯動治具／機種／站點／水位選項）
- `GET /inventory/configuration-report/export`（目前完整關聯明細篩選結果的 CSV／XLSX，支援可見欄位與收退料明細）
- `/production/models/{model_id}/query`（報表選機種＋全部站點時取得所有 mapped station capacity）
- `/production/capacity/stations/{station_id}?model_id=...`（報表指定單一站點時取得該站 capacity）
- `/master/fixtures/{fixture_code}/image?customer_id=...`（點擊報表治具代碼時載入 customer-scoped 圖片）

報表 repository 以 SQL union 組成 configured／unbound／unconfigured 關聯明細；目前沒有 fixture／model／station 主要實體 projection，也不接受 `report_dimension`，因此同一治具有多個 model/station 關聯時會依配置列重複呈現。可開站數在篩選前以 `model_id + station_id` window 依完整需求集合計算。收退料方向、日期與客供／自購來源皆在資料庫篩選，前端不再逐頁抓取完整 transaction overview。page response 另以完整篩選集合計算 `populated_columns`，供前端穩定隱藏整欄無資料的欄位，不會因分頁改變判斷。`0015_configuration_report_indexes.py` 補上 report transaction lookup 的複合索引。

以下 Search module 服務所有角色在 `/search` 的查詢模式，以及相容入口 `/search/detail` 的分頁搜尋與 lazy context。

- Router：`backend/app/routers/search.py`
- Service：`backend/app/services/search_service.py`
- Repository：`backend/app/repositories/search_repository.py` 主查詢，並協同 `master_repository.py` / `inventory_repository.py` / `production_repository.py`
- Schema：`backend/app/schemas/search.py`

#### API

- `GET /auth/preferences/model-shortcuts?customer_id=...`：列出登入使用者在指定客戶的機種查詢次數、最近查詢時間與釘選狀態
- `POST /auth/preferences/model-shortcuts/{model_id}/query?customer_id=...`：由後端受控流程累加使用次數並更新最近查詢時間
- `PUT /auth/preferences/model-shortcuts/{model_id}/pin?customer_id=...`：設定登入使用者自己的釘選狀態
- 三支 preference API 都要求已登入的 `admin`／`user` 並沿用 `user_customers` 客戶範圍；guest 不可寫入

- `GET /search/global`
- `GET /search/fixtures/overview`
- `GET /search/fixtures/{fixture_id}/context`
- `GET /search/models/{model_id}/context`

#### 行為重點

- `GET /search/global` 支援 `entity_type`、`fixture_search_mode=fixture|identifier`、`page`、`page_size`；`fixture_search_mode` 只在 `entity_type=fixture` 時生效，預設為 `fixture`
- `GET /search/fixtures/overview` 回傳 customer-scoped 的分頁治具簡略總覽，沿用 search page contract 並包含庫存、庫存狀態與合併儲位文字
- global search response 是有上限的 page contract：`items / total / page / page_size / has_more`
- fixture 搜尋分成明確模式：`fixture` 只查 fixture code / name / storage location；`identifier` 只以完整 transaction identifier 定位關聯治具。identifier 命中後，fixture context 只載入總覽所需資料與該 identifier 的交易項目，不會覆蓋一般治具編號搜尋
- 排序規則集中在 `search_repository.py`，目前是 active first + exact/prefix/contains ranking
- fixture 側 related models 直接來自 `fixture_requirements.model_id`
- 不再從 station 反推 model
- fixture / model detail context 改走獨立 lazy endpoint
- fixture detail 只保留近期交易預覽；完整歷史改由前端轉跳 `/inventory/overview`，handoff 不會再從預覽交易反推 `date_from / date_to`
- 搜尋頁的「相近編號」提示排序與「最近收 / 退料治具快捷入口」屬於前端行為，不是 search API contract

#### 前端入口

- `frontend/src/pages/SearchWorkspacePage.vue`
  - route：`/search/detail`
  - 空白查詢預設載入簡略治具總清單
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
  - `actor_user_id`（登入使用者 FK；無法可靠歸屬的 legacy 交易可為 `NULL`）
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
    - 治具最低庫存 editor state
  - `frontend/src/composables/useMasterCrudActions.ts`
    - 治具最低庫存新增／更新 payload
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
- repo 的目前 Alembic head 是 `0016_user_model_shortcuts`；它新增 `user_model_shortcuts`，以 `user_id + customer_id + model_id` 唯一約束保存跨裝置機種捷徑偏好。`0015_configuration_report_indexes` 仍負責報表交易篩選複合索引；上列既有目標環境實機驗證不代表 source head。
- customer scope 的權威行為在 `backend/app/core/auth.py`：已登入 admin 不具全客戶 bypass，需有 `user_customers` 指派。
- `App.vue` 目前沒有渲染 audit 摘要區塊，因此 `/audit/logs` 雖保留，但不是首頁主流程的一部分。
- migration/schema patch 的退場方向是三段式：
  - 先保留觀測與離線 compat 工具
  - 再用 runtime fail-loud gate 阻止低於 `0011_search_indexes` 的環境自動啟動
  - 最後再移除 `schema_patch.py` 與 legacy revision normalization
- 目前 repo 只補到 structured startup log 與離線掃描工具；所有已知環境的 inventory 盤點與 `N` 次連續通過統計仍需由運維流程補齊。
- Docker 測試環境已完成一次真實驗證：`fixture_m_lite_api` 的 `docker logs` 可直接看到 `migration_runtime_gate`，且 `source=app_startup`、`outcome=passed`。
