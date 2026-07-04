# Full Backend Landing Tasks

## Goal

將目前 UI 中仍是示意/半落地的區塊全部補齊成可用後端接口與資料流。
並新增「客戶切換入口」與「使用者登入 + 訪客入口」。

## Scope

### 0) 客戶切換與登入入口
- [x] `fixtures` 綁定 `customer_id`
- [x] 所有與治具相關列表/查詢 API 支援 `customer_id` 篩選
- [x] 前端新增全域客戶切換下拉
- [x] 前端在各模組請求帶入 `customer_id`
- [x] 新增 `users` 表（帳號、密碼雜湊、名稱、角色、啟用狀態）
- [x] 新增 `user_customers` 表，維護一般使用者可見客戶清單
- [x] 新增 `POST /auth/login`、`POST /auth/guest`、`GET /auth/users`
- [x] 前端新增登入頁，支援「帳密登入」與「訪客入口」
- [x] `admin` 可看全部客戶且可編輯全部資料
- [x] `guest` 可看全部客戶但不可編輯，且不可進入 `資料維護`
- [x] `user` 只能看授權客戶，客戶指派改由客戶分頁維護
- [x] `user` 可編輯授權客戶下的業務資料，但不可管理客戶與使用者

### 1) 資料維護停用能力一致化
- [x] `machine_models` 加入 `is_active`
- [x] `stations` 加入 `is_active`
- [x] 後端 `PUT` API 支援 `is_active`
- [x] 前端 `資料維護` 頁面可對治具/機種/站點執行停用

### 2) 儲位策略收斂
- [x] 治具儲位只保留 `fixtures.storage_location`
- [x] 移除 `warehouse_profiles`、`storage_locations`、`fixture_location_assignments`、`fixture_images`
- [x] 查詢與主檔統一使用文字儲位顯示

### 4) 產能頁目前開站數改為後端計算
- [x] `get_station_capacity` 以 `model_id + station_id` 為查詢範圍，回傳真實最大開站量
- [x] 前端 `產能` 頁改用 API 回傳值，移除 hardcoded `0`
- [x] `current_open_station_count` 已正式退場，不再出現在 production schema / API / frontend type
- [x] 產能頁改為只呈現「指定機種 + 指定站點」的單站獨立最大開站量語意

### 5) 查詢頁展示欄位去除示意值
- [x] 移除 `---` 類示意值
- [x] 交易/時間欄位改為實際資料或 `-`
- [x] 明確 fallback 規則（空值顯示 `-`）

### 6) Schema 演進機制（無 migration 下的保底）
- [x] 新增 startup schema patch（針對現有 DB 自動補欄位）
- [x] 補 `is_active` 新欄位 patch（model/station 等既有主檔）
- [x] 不破壞既有資料

## Validation Checklist

- [x] 可切換客戶後刷新各模組資料
- [x] 登入後可進入系統；訪客可直接進入
- [x] `python -m compileall backend/app` pass
- [x] `npm run build` pass
- [x] `master` 可新增/編輯/停用四類主檔
- [x] `production` 的目前開站數非固定值
- [x] `search` 不再出現示意字串 `---`

## Current Snapshot

- 目前 `App.vue` 已改為頂部 shell，不再使用左側常駐導覽；頂欄包含登入狀態、客戶切換、今日統計、全域 `收/退料` 與 `收退料資訊匯出` 入口，以及 `更多功能` 選單。
- 目前 shell 仍沒有桌面版 mini sidebar；手機版則維持漢堡選單 / overlay 導覽。
- `SearchWorkspacePage` 已新增固定的新手教學入口，首次登入也會自動啟動導覽。
- `SearchWorkspacePage` 的智慧提示已收斂為「相近編號」排序提示，不再混用 direct / related / identifier 類型提示。
- `MasterPage` 已有前端分頁；`SearchWorkspacePage` 目前仍沒有查詢結果分頁。
- `SearchWorkspacePage` 目前仍沒有可收合的篩選區。
- `npm run build` 目前可通過。
- `.venv\\Scripts\\python.exe -m pytest tests -q` 目前為 `4 passed, 1 failed`。
- 目前剩餘失敗案例在 `tests/test_inventory_and_production.py::test_inventory_capacity_and_search_flow`：測試資料使用 `identifier = "202606"`，但現行驗證仍限制「4 碼以內」，且 validation error payload 的 `ctx.error` 仍帶出未序列化的 `ValueError`。

## Phase 0-4 Approved Update

### Shell / Navigation

- [x] 側邊欄改為頂部欄
- [x] 頂部欄常駐顯示：登入者 / 登入登出、目前客戶 / 切換客戶、今日收退料總數、低水位提醒
- [x] 頂部欄新增 `收/退料` 按鈕，開啟全域 Modal
- [x] 頂部欄新增 `更多功能` 下拉，包含 `收退料總檢視 / 資料維護 / 產能管理`
- [x] Logo 可點擊回 `/search`
- [x] `MasterPage` 新增 `返回搜尋` 按鈕
- [x] `ProductionPage` 新增 `返回搜尋` 按鈕
- [x] 手機版 shell 改為常駐漢堡按鈕 + 目前客戶名稱，其餘收進選單

### Search Page

- [x] 拆出 `FixtureInfoPanel.vue` / `ModelInfoPanel.vue`，純展示、只吃 props
- [x] 拆出 `FixtureEditForm.vue` / `ModelEditForm.vue`，供搜尋頁內嵌編輯使用
- [x] 搜尋頁新增區塊勾選顯示 chip 列，並以 localStorage 分開記住治具 / 機種偏好
- [x] 全部取消勾選時擋住，至少保留一個區塊
- [x] 新增 `資料維護` 勾選項，勾上後出現 `編輯` 分頁
- [x] `資料維護` 勾選狀態也要記住在 localStorage
- [x] 查無結果時顯示 `找不到，新增一筆？`，並可直接打開建立流程
- [x] 機種搜尋結果提供輕量入口跳轉既有 `ProductionPage`，並帶入該機種預選
- [x] 編輯分頁首次 lazy load 時顯示共用小型 inline spinner

### Inventory / Global Modal

- [x] 抽出 `BatchImportPanel.vue` 共用元件
- [x] `/inventory` 與全域 Modal 共用同一份批次匯入 UI / 資料流
- [x] 全域 Modal 只含批次貼上匯入，不含庫存總覽 / 低水位 / 最近紀錄
- [x] Modal 成功送出後不自動關閉，僅清空輸入框

### Master / Production Scope

- [ ] `MasterPage` 的治具 / 機種頁籤收斂為：CSV 匯入匯出、瀏覽停用項目、建立全新項目
- [ ] `MasterPage` 的站點 / 客戶 / 使用者維持現狀單頁表單
- [x] `ProductionPage` 內部結構維持不動，只新增搜尋頁導入入口

### Loading

- [x] 新增一個共用小型 inline spinner
- [x] spinner 先套用於：搜尋頁編輯分頁 lazy load、收退料 Modal 資料載入

## To Update

### 7) 收退料頁布局與總覽
- [x] 收退料操作區與目前庫存總覽改為並列布局
- [x] 新增「收 / 退料總檢視」頁面
- [x] 收退料操作區移除單筆手動表單，只保留批次貼上匯入
- [x] 總檢視移除「全部查詢 / 序號查詢」模式切換，統一為單一主查詢頁
- [x] 總檢視支援篩選：收退料類型、日期區間、治具編號、單號、識別碼、操作人員
- [x] 總檢視匯出 CSV 直接吃目前主頁面篩選條件
- [x] 總檢視移除下載範本與 CSV 匯入入口

### 8) 匯入匯出與範本下載
- [x] 收退料支援批次貼上匯入
- [x] 批次貼上匯入支援自定義單號，並套用到整批交易
- [x] 治具資料維護支援匯出 / 匯入 / 匯入範本
- [x] 站點資料維護支援匯出 / 匯入 / 匯入範本
- [x] 機種資料維護支援匯出 / 匯入 / 匯入範本
- [x] 機種綁站點 / 綁治具資料維護支援匯出 / 匯入 / 匯入範本

### 9) 治具主檔擴充
- [x] 治具主檔新增「庫存水位」欄位（可選填）
- [x] 治具主檔新增「負責人」欄位（可選填）
- [x] 負責人來源改為「該客戶已指派使用者」
- [x] 治具命名規則改為：不可符號開頭，其餘不限制

### 10) 收退料資料模型調整
- [x] 治具主檔不再提供使用者維護 `manage_type`
- [x] 治具主檔不再區分 `客供 / 自購`
- [x] `客供 / 自購` 改為收退料交易明細欄位 `ownership_type`
- [x] `datecode` / `serial` 概念已統一為單一 `identifier`
- [x] 收退料查詢、匯出、展示、批次匯入都只使用單一 `identifier`
- [x] 收退料流程需檢核並展示 `ownership_type`

#### 10.1) 模型定案

- `material_transactions`
  - `customer_id`
  - `transaction_type`
  - `transaction_no`
  - `occurred_at`
  - `created_by`
  - `note`
- `material_transaction_items`
  - `fixture_id`
  - `ownership_type`
  - `identifier`
  - `quantity`
  - `note`

#### 10.2) 前端流程定案

- 收退料頁不再提供單筆表單，統一由批次貼上匯入處理
- 每筆貼上資料都必須包含 `治具編號 + 識別碼 + 數量`
- `identifier` 不限制英數格式，由使用者自定義
- 所有收退料明細都必填 `ownership_type`

### 11) 儲位與圖片整合
- [x] 治具主檔可直接填寫 / 維護文字儲位
- [x] 查詢頁可依治具代碼讀取檔案式圖片預覽

### 12) Review / Hardening Backlog
- [x] 密碼雜湊改為帶 salt 的 PBKDF2，並相容舊的 sha256 密碼資料
- [x] 治具 code lookup 補 customer scope，避免未來跨客戶查詢污染
- [x] 治具列表與匯出不再因讀取而自動建立 stock level
- [x] CSV 匯入改為批次原子操作，避免部分成功、部分失敗
- [x] 今日統計改用本地日期邏輯，並避免只看最近 50 筆
- [x] 忽略前端生成檔與 build 產物，降低 repo 雜訊
- [x] 正式導入 Alembic migration，逐步移除 runtime schema patch
- [x] 為登入 / 角色權限補上真正的後端授權機制
- [x] 補上 backend 與 frontend 的測試覆蓋，至少涵蓋 auth / inventory / capacity / CSV

### 13) 優先級優化待辦

#### P0 - 高優先
- [x] 正式導入 Alembic migration，建立可追蹤的資料庫版本管理流程，逐步移除 runtime schema patch
- [x] 為登入 / 角色權限補上真正的後端授權機制，明確區分可讀、可寫、可管理操作
- [x] 補上 backend 與 frontend 的測試覆蓋，至少涵蓋 auth / inventory / capacity / CSV / production 主流程
- [x] 清理 `frontend/src` 與專案內的生成檔、`*.js`、`*.map`、`dist` 類產物，避免 source tree 混入 build artifacts
- [x] 統一 API 錯誤處理與回傳格式，避免前後端對錯誤訊息的解讀不一致

#### P1 - 中優先
- [x] 統一各頁面的表單編輯體驗，讓新增 / 編輯 / 取消編輯的操作邏輯一致
- [x] 強化錯誤提示內容，讓使用者知道是欄位驗證失敗、權限不足、還是後端查詢失敗
- [x] 補齊 loading / empty / no-result 狀態，特別是查詢頁與維護頁
- [x] 統一表格操作列的按鈕順序與樣式，例如編輯、刪除、停用的排列方式
- [x] 抽出共用 UI 元件，像是區塊卡片、操作列、確認對話框、表單標題
- [ ] 讓查詢頁的篩選區可收合，預設只露出最常用條件
- [x] 調整收退料頁的常用操作優先順序，讓單筆新增、批次匯入、最近操作分區更清楚
- [x] 用更直觀的視覺方式呈現產能狀態，例如顏色、進度條、警示標籤
- [x] 讓資料維護頁的啟用 / 停用、可用 / 不可用狀態更一致、更容易辨識
- [x] 再整理一次手機版與小螢幕版布局，特別是 top nav、表格操作列、表單寬度

#### P2 - 次優先
- [x] 抽出日期格式化、欄位 fallback、狀態映射等共用工具，降低各頁重複邏輯
- [ ] 將 `InventoryPage`、`MasterPage`、`ProductionPage` 等大型頁面再拆小，降低後續維護成本
- [x] 補更完整的審計資訊，例如誰在什麼時間修改了哪些主資料
- [x] 若資料量持續增加，針對查詢與列表頁開始規劃分頁、索引與查詢效能優化
- [x] 重新整理首頁資訊層級，讓客戶資訊、登入狀態、今日統計、導航區更清楚

### 14) 前端布局優化與 UX 深度改良 (針對 100% 縮放全可視化)

#### P0 - 核心空間優化 (解決 50% 縮放問題)
- [x] **重構主布局柵格**：將 `.inventory-board` 從固定的 `minmax` 寬度改為動態 `1fr` 彈性布局，確保內容依視窗寬度自適應。
- [ ] **實作收納式側邊欄**：左側選單支援桌面版 Mini 模式（目前只有手機/平板 overlay 開關），為操作區爭取 10-15% 的水平寬度。
- [x] **表單 Inline 化**：將收退料單筆表單從「標籤在上、輸入在下」改為「標籤與輸入框左右併排」，大幅減少垂直高度消耗。
- [x] **批次匯入 Modal 化**：將「批次貼上解析」功能移至全螢幕或大型對話框 (Modal) 中處理，避免解析後的大型表格撐開主頁面布局。
- [x] **移除頂欄**：登入狀態、客戶選擇、時間、登出全部集中到側邊欄
- [x] **新增客戶入口搬移**：從頂欄移至 `資料維護` 分頁

#### P1 - 圖片紅框/橘框針對性改良
- [x] **操作區 Segmented Control**：收/退料切換改用分段選擇器 (Segmented Control)，減少按鈕佔位並提升視覺直覺度。
- [x] **批次確認流程簡化**：優化「待確認/待新增」行的按鈕群，改用 Icon 按鈕或精簡的動作選單，避免表格橫向過度撐開。
- [x] **庫存狀態視覺化**：現有庫存列表引入微型進度條或顏色條，取代純文字水位描述。
- [x] **統計小卡整合**：將散落的統計數據 (今日收/退/低水位) 整合至頁面頂部的一列式摘要列 (Summary Row)，釋放右側縱向空間。

#### P2 - 細節 hardening
- [x] **全局字體大小微調**：針對工業管理場景，將表格預設字體微調至 12px，並減少單元格 `padding`，提升資訊密度。
- [ ] **自動對焦優化**：舊的單筆表單已移除；若要補齊，目前應改為批次匯入 modal 的首欄自動對焦。

### 15) 查詢頁重構

- [x] 查詢頁改為雙模式：`治具` / `機種`
- [x] 固定統計方格：治具種類總數、治具總數、機種總數、站點總數
- [x] 治具查詢只顯示：
  - 治具庫存總量
  - 治具圖片
  - 儲位
  - 最低水位
  - 相關收退料記錄
  - 使用到該治具的機種
  - 使用到該治具的站點總數
- [x] 治具查詢提供 `查看詳細` 展開站點清單
- [x] 機種查詢只顯示：
  - 相關治具
  - 相關站點
  - 每個站點最大開站量
- [x] 機種查詢提供 `查看詳細` 展開每站治具需求明細與最大開站量表格
- [x] 查詢頁改成內容區內滾動，避免資訊超出視窗
- [x] 查詢頁移除重複治具資訊欄位
- [x] 查詢頁治具主檔展示移除 `manage_type`
- [x] 查詢頁治具關聯機種改為直接使用 `fixture_requirements.model_id`，不再從站點反推機種
- [x] 查詢頁治具站點詳細改為顯示 `機種 + 站點 + 所需數量`

### 16) Production 多機種共站模型定案
- [x] `fixture_requirements` 正式改為 `model_id + station_id + fixture_id`
- [x] 同一站點可被多機種共用，但每個機種在該站點的治具需求各自獨立
- [x] `get_station_capacity` 強制要求 `model_id`
- [x] `get_model_query` 支援 `station_id`
- [x] `Fixture Requirement` create/update/import/export 全面帶入 `model_id`
- [x] 產能頁站點下拉只顯示當前機種已綁定站點
- [x] 切換機種後，站點選擇會自動收斂到該機種可用站點
- [x] 查詢頁與產能頁已移除 `station -> model` 執行期反推邏輯

### 17) 新手導覽 / 教學模式

- [x] 新增全域 `GuidedTour` 浮層元件，支援 spotlight、高亮目標與逐步導覽
- [x] 首次登入後自動啟動新手導覽，並以 sessionStorage 記住本次 session 已看過
- [x] 搜尋首頁新增固定「開始新手教學」入口，可隨時重播
- [x] 導覽步驟已涵蓋：搜尋首頁、收退料入口、匯出入口、總檢視、資料維護、產能管理
- [x] 收退料批次匯入元件新增 `tutorialMode`，教學模式下可自動帶入試跑資料
- [x] 教學模式送出收 / 退料時不寫入正式資料，只清空畫面並提示試跑完成
- [x] `MasterPage` 新增「開始新手導覽」按鈕，可從資料維護頁回到導覽起點

### 18) Migration / 啟動穩定性修補
- [x] 新增 Alembic migration `0004_model_station_scope`
- [x] 新增 Alembic migration `0005_remove_warehouse_tables`
- [x] 新增 Alembic migration `0006_identifier_cleanup`
- [x] 新增 Alembic migration `0007_user_customer_scope`
- [x] 新增 Alembic migration `0008_fixture_responsible_user`
- [x] 新增 Alembic migration `0009_remove_owners_and_scope_fixture_code`
- [x] 修正舊 revision id 過長導致 `alembic_version.version_num` 寫入失敗問題
- [x] 啟動前自動放寬 MySQL/MariaDB `alembic_version.version_num` 欄位
- [x] 啟動前自動將舊 revision id `0004_model_station_fixture_requirements` 正規化為 `0004_model_station_scope`
- [x] `fixtures.code` 改為 `(customer_id, code)` 唯一鍵，允許不同客戶使用相同治具代碼
- [x] 舊 `owners` 資料表正式移除，責任人收斂為 `fixtures.responsible_user_id`
- [x] Docker 環境已驗證 migration 可正常完成且 API 可正常啟動

### 19) 測試補強
- [x] 新增 migration preflight 測試
- [x] 新增 production service 測試，覆蓋同站點多機種共用情境
- [x] 新增 production API 測試，驗證同站點多機種共用時 capacity / query 不互相污染
- [x] 新增 auth / customer scope 測試，驗證 `admin` / `guest` / `user` 三種角色行為

### 20) 角色與客戶權限定案
- [x] `admin` 不限制客戶可視範圍，且可編輯全部資料
- [x] `guest` 不限制客戶可視範圍，但只能讀取
- [x] `guest` 不顯示 `資料維護` 導航，且不可直接進入 `/master`
- [x] `user` 可先建立帳號，再由客戶分頁指派可見客戶
- [x] `user` 可編輯 `fixtures / models / stations`
- [x] `user` 不可管理 `customers / users`
- [x] 所有 customer-scoped API 對 `user` 強制檢查 `customer_id`
- [x] 使用者分頁不再維護客戶勾選；改由客戶分頁維護 `assigned_user_ids`
- [x] 客戶已指派使用者同時作為該客戶治具的負責人候選名單
- [x] 負責人分頁已移除

## Update Log

### 2026-07-04

- 已重新同步 `task.md`、`ARCHITECTURE.md`、`frontend-map.md`、`backend-map.md`、`map.md`、`ARCHITECTURE_LANDING.md`，讓文件描述對齊目前 topbar shell、全域收退料/匯出 modal、onboarding 導覽與教學模式。
- 已在文件中補上 `GuidedTour`、`frontend/src/onboarding.ts`、`InventoryExportPanel.vue`、搜尋頁「相近編號」提示收斂等最新前端結構。
- 已確認 `requirements.txt` 原本就包含 `openpyxl`；本次已補安裝到目前 `.venv`，排除測試因缺套件而在 import 階段直接失敗的問題。
- 已重新驗證 `npm run build` 通過。
- 已重新驗證 `.venv\\Scripts\\python.exe -m pytest tests -q`，目前結果為 `4 passed, 1 failed`。
- 目前剩餘失敗案例集中在 `tests/test_inventory_and_production.py::test_inventory_capacity_and_search_flow`：`identifier = "202606"` 仍被限制為 4 碼內，且 validation error payload 的 `ctx.error` 仍含未序列化的 `ValueError`。

### 2026-06-27

- 已重新對照目前程式碼校正文檔，確認 `ARCHITECTURE.md` 與 `task.md` 不再把「最近異動側欄卡片」與「桌面 mini sidebar」視為已落地現況。
- 已補記目前測試現況：`.venv\\Scripts\\python.exe -m pytest tests -q` 尚有 1 個失敗案例，集中在 `identifier` 驗證與 validation error 序列化。

### 2026-06-20

- 已修正首頁左側側邊欄右側的白邊問題，收斂 scrollbar 預留空間與滾動區背景，避免主內容區左側出現視覺縫隙。
- 已將前端共用日期格式化工具統一為只顯示 `年月日`，不再顯示時分秒。
- 已將首頁側邊欄顯示文案由 `時間` 調整為 `日期`，並只呈現當日日期。
- 已將 `收退料總檢視`、`資料維護`、`查詢頁`、`產能頁` 中所有建立/更新/交易日期顯示統一改為 `年月日`。
- 已將後端 API 的 `datetime` 回應序列化統一收斂為 `YYYY-MM-DD`，避免前端再收到帶時分秒的日期字串。
- 已將收退料 CSV 匯出的 `occurred_at` 與範本日期格式統一改為 `YYYY-MM-DD`。
- 已將收退料建立交易與 CSV 匯入流程收斂為「只記錄日期」：即使輸入帶時分秒，也會在寫入前正規化為當日零點。
- 已補齊 `資料維護` 頁的停用資料恢復流程，`治具 / 機種 / 站點 / 使用者` 現在都可從停用狀態恢復使用。
- 已讓 `資料維護` 頁的狀態篩選一致套用到 `治具 / 機種 / 站點 / 使用者` 清單，便於找到停用資料後重新啟用。
- 已將 `資料維護` 頁底部動作按鈕改為依當前狀態動態顯示 `停用 / 恢復使用`，不再只有單向停用途徑。

### 2026-06-15

- 已將 production requirement 的正式資料模型定案為 `model_id + station_id + fixture_id`。
- 已將 production 展開與計算邏輯定案為：
  - `機種 -> 機種已綁定站點 -> 該機種該站點的治具需求`
- 已修正 production 頁站點選擇邏輯，切換機種後不再保留無效 `station_id`。
- 已修正 production 頁 requirement 清單過濾，改為 `model_id + station_id`，不再只看 `station_id`。
- 已修正查詢頁治具關聯機種與站點詳細，不再從站點反推機種。
- 已將 production capacity UI 改為單站獨立語意，不再展示誤導性的「目前開站 / 剩餘開站」資訊。
- 已將 `current_open_station_count` 從 backend schema / service、frontend types / page props / UI 中正式移除。
- 已修正 Alembic `0004` revision id 過長造成的 MySQL `alembic_version.version_num` 寫入失敗問題。
- 已將 migration revision 正式收斂為 `0004_model_station_scope`，並補上 legacy revision alias normalization。
- 已驗證 docker compose 下的 API 與 Web 可正常重建與啟動。
- 已修正批次收退料自定義單號不生效問題，後端現在會保留使用者輸入的 `transaction_no`。
- 已新增 migration 測試與 production API / service 測試，特別覆蓋「同站點多機種共用」情境。
- 已移除 warehouse 相關資料表，正式收斂為 `fixtures.storage_location` 單一文字儲位策略。
- 已新增 Alembic `0006_identifier_cleanup`，將 `material_transaction_items` 正式改為 `identifier` 欄位，並移除 legacy `manage_type / datecode / serial_number` 與 `fixture_serials`。
- 已將客戶可見範圍維護入口從使用者分頁移到客戶分頁，改由 `assigned_user_ids` 管理 `user_customers`。
- 已將治具負責人收斂為客戶已指派使用者，並移除前端負責人分頁與對應 API 使用。
- 已新增 Alembic `0007_user_customer_scope`，將一般使用者的客戶可見範圍正式落到 `user_customers`。
- 已新增 Alembic `0008_fixture_responsible_user`，在 `fixtures` 補上 `responsible_user_id`。
- 已新增 Alembic `0009_remove_owners_and_scope_fixture_code`，移除 `owners` 並將治具代碼唯一鍵收斂為 `(customer_id, code)`。

### 2026-06-12

- 已將側邊欄改回淺色系，保留清楚的 active 狀態與層次，但不再使用深色 sidebar。
- 已移除頂欄與左上角四個分頁切換按鈕。
- 已把已登入狀態、客戶選擇、時間、登出整合到側邊欄。
- 已把新增客戶功能移到 `資料維護` 分頁。
- 已把收退料操作區的手動表單移除，只保留批次貼上匯入。
- 已在批次貼上匯入加入自由輸入的單號欄位，並套用到整批收料 / 退料交易。
- 已把收退料總檢視的下載範本與匯入 CSV 入口移除。
- 已把收退料總檢視簡化成單一主查詢頁，移除 `序號查詢` 模式。
- 已把收退料總檢視的篩選與表格文案統一改成 `識別碼`。
- 已把 `manage_type` 從治具主檔維護與查詢展示中移除。
- 已把 `datecode / serial_number` 對外概念統一為單一 `identifier`。
- 已更新前端 API、型別與頁面，只收發 `identifier`，不再使用 `manage_type` / `serial_number`。
- 已更新後端 inventory / master / search 的 schema、router、service、repository，對外不再暴露 `manage_type` / `serial_number`。
- 已於後續 migration 正式移除 `manage_type / datecode / serial_number` 與 `fixture_serials`，資料庫也改成單一 `identifier`。
- 已重構查詢頁為 `治具 / 機種` 兩種模式，並加入固定統計方格。
- 已讓查詢頁改為面板內滾動，避免內容超出頁面高度。
- 已依圖片移除查詢頁右側重複的治具名稱卡片。
- 已驗證 `npm run build` 與 `python -m compileall backend/app` 通過。

### 2026-06-11

- 已將 `MasterPage` 與 `ProductionPage` 補上載入中提示與空狀態列，避免資料尚未載入或清單為空時畫面顯得像壞掉。
- 已將 `MasterPage` 的主要操作按鈕在載入中鎖定，降低切換客戶或重整時的誤操作。
- 已將 `ProductionPage` 的查詢/匯入/更新操作在載入與儲存中鎖定，避免表單與資料刷新互相打架。
- 當時曾規劃將 `SearchWorkspace` 的篩選區改成可收合；目前程式碼中尚未保留這個互動。
- 已把 `ProductionPage` 的 Station Capacity 改成進度條 + 狀態標籤呈現，讓產能是否接近上限更容易一眼看懂。
- 已將 `ProductionPage` 兩個表格的操作列包成一致的動作區塊，統一編輯 / 刪除的排列方式。
- 已將前端錯誤訊息解析強化為可讀的欄位驗證/後端錯誤訊息，避免只看到模糊的 request failed。
- 已在 `MasterPage` 的編輯區加上目前狀態徽章，讓資料維護頁的啟用 / 停用狀態更一致也更醒目。
- 已將收退料頁的批次匯入區收合為次要作業，並補上明確的優先級提示，讓單筆收退料與最近操作更突出。
- 已補上前端共用顯示工具，集中處理欄位 fallback 與狀態文字，減少頁面內重複字串與映射邏輯。
- 已抽出共用 `StatusPill` 元件，並在 `MasterPage`、`ProductionPage`、`InventoryPage` 內共用使用。
- 已抽出共用 `UiFormActions` 元件，讓主檔與產能頁的新增 / 編輯 / 取消 / 儲存動作列統一。
- 已新增 `audit_logs` 與 `/audit/logs`，將主資料異動、使用者更新與匯入事件納入審計記錄。
- 已完成 `audit_logs` 與 `/audit/logs` 後端能力；目前首頁側欄沒有渲染最近異動卡片。
- 已將全站主要按鈕配色統一為綠色儲存、灰色取消、紅色停用/刪除。
- 已將 `MasterPage` 清單補上分頁；`SearchWorkspace` 查詢結果目前尚未分頁。
- 已把 `ProductionPage` 的 Station Capacity / Model Query 區塊拆成獨立元件，降低單一頁面的程式碼密度。
- 目前首頁側欄支援 mobile overlay 開關；桌面版 mini mode 尚未保留。
- 已將收退料頁主布局改為頂部摘要列 + 左中右三欄配置，並把批次貼上匯入改為 modal。
- 已把收退料操作區改成 segmented control，並補上庫存水位條與批次行動作精簡。
- 已驗證 `frontend` 的 `npm run build` 通過。
- 已將前端表格與 body 字級微調至 12px，並略縮 cell padding，提升工業管理場景下的資訊密度。
- 舊的單筆表單自動聚焦調整不再適用，因目前流程已收斂為批次貼上匯入。

### 2026-06-10

- 已補上前端 Vitest 測試骨架，並新增共用 helper 的 unit tests。
- 已將前端日期格式化與 API 錯誤訊息解析抽成共用 util，減少重複邏輯。
- 已補上查詢頁與收退料頁的空狀態 / 載入狀態回饋，讓資料不足時的 UI 更清楚。
- 已將收退料頁的庫存列表補上空狀態提示。
- 已將收退料頁的左側操作區加寬，並把「最近收料 / 退料」區塊提前到批次匯入前面，降低使用時的垂直捲動壓力。
- 已補上 backend unittest，覆蓋 auth / role、API error payload、inventory、production 核心流程。
- 已將 frontend 測試擴充到共用 util 層，驗證日期格式化、API 錯誤解析與治具圖片 URL 組裝。

### 2026-06-09

- 已將前一次 review 的改善項目整理進 `Review / Hardening Backlog`。
- 已完成密碼雜湊升級為 PBKDF2，並保留舊 sha256 密碼相容性。
- 已補上治具 code lookup 的 customer scope，降低跨客戶資料污染風險。
- 已將治具列表與匯出改為純讀取，避免 GET request 產生副作用。
- 已將 CSV 匯入調整為批次原子流程，避免部分成功、部分失敗。
- 已修正前端今日統計的本地日期判定，並提高取樣筆數。
- 已補上 `.gitignore` 對前端生成檔與 build 產物的忽略規則。
- 已驗證 `python -m compileall backend/app` 與 `npm run build` 通過。
- 已依圖片要求調整收退料操作區，移除管理型態欄位，並將來源預設改為客供。
- 已將收退料單筆表單改成預設收起，需時再手動展開填寫。
- 已依最新圖片進一步移除治具詳細資料中的管理類型欄位，並把收退料單筆輸入的可見 `Datecode / 序號` 標籤隱藏。
- 已為 `Fixture Requirement` 與 `Model-Station Mapping` 補上編輯功能，且編輯按鈕放在刪除前。
- 已將後續可做的 UI / 架構優化整理成 `P0 / P1 / P2` 三層優先級待辦。
- 已將前端 typecheck 改為 no-emit，避免 `vue-tsc` 再把 `.js` / `.map` 產物寫回 `frontend/src`。
- 已補上 backend service 的 unittest，覆蓋 `auth`、`production`、`inventory` 的核心流程。
- 已把 `auth` 的資料庫依賴改成 lazy import，讓 service 測試不再被 MySQL driver 綁死。
- 已正式把啟動流程收斂到 Alembic：startup 只做 `upgrade head`，並新增 `0002_schema_backfill` 作為 legacy DB 的 backfill migration。
