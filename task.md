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
- [x] 新增 `POST /auth/login`、`POST /auth/guest`、`GET /auth/users`
- [x] 前端新增登入頁，支援「帳密登入」與「訪客入口」

### 1) 資料維護停用能力一致化
- [x] `machine_models` 加入 `is_active`
- [x] `stations` 加入 `is_active`
- [x] `owners` 加入 `is_active`
- [x] 後端 `PUT` API 支援 `is_active`
- [x] 前端 `資料維護` 頁面可對治具/機種/站點/負責人執行停用

### 2) Warehouse 倉庫主卡改為真實資料
- [x] 新增 `warehouse_profiles`（代碼、名稱、狀態、備註）
- [x] 新增 `GET /warehouse/profile`
- [x] 新增 `PUT /warehouse/profile`
- [x] 前端 `Warehouse 介面` 改為讀取/更新 profile

### 3) 儲位狀態改為正式欄位
- [x] `storage_locations` 加入 `is_active`
- [x] location create/update/list schema 帶入 `is_active`
- [x] 前端儲位狀態改為讀寫 `is_active`，移除 description 推測狀態

### 4) 產能頁目前開站數改為後端計算
- [x] `CapacityRead` 增加 `current_open_station_count`
- [x] `get_station_capacity` 回傳真實值（先以該站綁定機種數作為目前開站數）
- [x] 前端 `產能` 頁改用 API 回傳值，移除 hardcoded `0`

### 5) 查詢頁展示欄位去除示意值
- [x] 移除 `---` 類示意值
- [x] 交易/時間欄位改為實際資料或 `-`
- [x] 明確 fallback 規則（空值顯示 `-`）

### 6) Schema 演進機制（無 migration 下的保底）
- [x] 新增 startup schema patch（針對現有 DB 自動補欄位）
- [x] 補 `is_active` 新欄位 patch（model/station/owner/location）
- [x] 不破壞既有資料

## Validation Checklist

- [x] 可切換客戶後刷新各模組資料
- [x] 登入後可進入系統；訪客可直接進入
- [x] `python -m compileall backend/app` pass
- [x] `npm run build` pass
- [x] `master` 可新增/編輯/停用四類主檔
- [x] `warehouse` 可編輯倉庫主卡、儲位狀態、綁定解除、圖片操作
- [x] `production` 的目前開站數非固定值
- [x] `search` 不再出現示意字串 `---`

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
- [x] 治具儲位頁可直接填寫 / 維護治具儲位
- [x] 治具儲位頁可直接維護治具圖片

### 12) Review / Hardening Backlog
- [x] 密碼雜湊改為帶 salt 的 PBKDF2，並相容舊的 sha256 密碼資料
- [x] 治具 code lookup 補 customer scope，避免未來跨客戶查詢污染
- [x] 治具列表與匯出不再因讀取而自動建立 stock level
- [x] CSV 匯入改為批次原子操作，避免部分成功、部分失敗
- [x] 今日統計改用本地日期邏輯，並避免只看最近 50 筆
- [x] 忽略前端生成檔與 build 產物，降低 repo 雜訊
- [ ] 正式導入 Alembic migration，逐步移除 runtime schema patch
- [ ] 為登入 / 角色權限補上真正的後端授權機制
- [ ] 補上 backend 與 frontend 的測試覆蓋，至少涵蓋 auth / inventory / capacity / CSV

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
- [x] 讓查詢頁的篩選區可收合，預設只露出最常用條件
- [x] 調整收退料頁的常用操作優先順序，讓單筆新增、批次匯入、最近操作分區更清楚
- [x] 用更直觀的視覺方式呈現產能狀態，例如顏色、進度條、警示標籤
- [x] 讓資料維護頁的啟用 / 停用、可用 / 不可用狀態更一致、更容易辨識
- [x] 再整理一次手機版與小螢幕版布局，特別是 top nav、表格操作列、表單寬度

#### P2 - 次優先
- [x] 抽出日期格式化、欄位 fallback、狀態映射等共用工具，降低各頁重複邏輯
- [ ] 將 `InventoryPage`、`MasterPage`、`ProductionPage` 等大型頁面再拆小，降低後續維護成本
- [x] 補更完整的審計資訊，例如誰在什麼時間修改了哪些主資料
- [x] 若資料量持續增加，針對查詢與列表頁開始規劃分頁、索引與查詢效能優化
- [ ] 重新整理首頁資訊層級，讓客戶資訊、登入狀態、今日統計、導航區更清楚

### 14) 前端布局優化與 UX 深度改良 (針對 100% 縮放全可視化)

#### P0 - 核心空間優化 (解決 50% 縮放問題)
- [x] **重構主布局柵格**：將 `.inventory-board` 從固定的 `minmax` 寬度改為動態 `1fr` 彈性布局，確保內容依視窗寬度自適應。
- [x] **實作收納式側邊欄**：左側選單支援 Mini 模式（僅顯示 Icon 或可完全收起），為操作區爭取 10-15% 的水平寬度。
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
- [x] **自動對焦優化**：單筆表單展開後，自動對焦至「治具編號」或「Datecode」欄位。

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

## Update Log


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

### 2026-06-10

- 已補上前端 Vitest 測試骨架，並新增共用 helper 的 unit tests。
- 已將前端日期格式化與 API 錯誤訊息解析抽成共用 util，減少重複邏輯。
- 已補上查詢頁與收退料頁的空狀態 / 載入狀態回饋，讓資料不足時的 UI 更清楚。
- 已將收退料頁的庫存列表補上空狀態提示。
- 已將收退料頁的左側操作區加寬，並把「最近收料 / 退料」區塊提前到批次匯入前面，降低使用時的垂直捲動壓力。
- 已補上 backend unittest，覆蓋 auth / role、API error payload、inventory、production 核心流程。
- 已將 frontend 測試擴充到共用 util 層，驗證日期格式化、API 錯誤解析與治具圖片 URL 組裝。

### 2026-06-11

- 已將 `MasterPage` 與 `ProductionPage` 補上載入中提示與空狀態列，避免資料尚未載入或清單為空時畫面顯得像壞掉。
- 已將 `MasterPage` 的主要操作按鈕在載入中鎖定，降低切換客戶或重整時的誤操作。
- 已將 `ProductionPage` 的查詢/匯入/更新操作在載入與儲存中鎖定，避免表單與資料刷新互相打架。
- 已把 `SearchWorkspace` 的篩選區改成可收合，縮小預設占用空間。
- 已把 `ProductionPage` 的 Station Capacity 改成進度條 + 狀態標籤呈現，讓產能是否接近上限更容易一眼看懂。
- 已將 `ProductionPage` 兩個表格的操作列包成一致的動作區塊，統一編輯 / 刪除的排列方式。
- 已將前端錯誤訊息解析強化為可讀的欄位驗證/後端錯誤訊息，避免只看到模糊的 request failed。
- 已在 `MasterPage` 的編輯區加上目前狀態徽章，讓資料維護頁的啟用 / 停用狀態更一致也更醒目。
- 已將收退料頁的批次匯入區收合為次要作業，並補上明確的優先級提示，讓單筆收退料與最近操作更突出。
- 已補上前端共用顯示工具，集中處理欄位 fallback 與狀態文字，減少頁面內重複字串與映射邏輯。
- 已抽出共用 `StatusPill` 元件，並在 `MasterPage`、`ProductionPage`、`InventoryPage` 內共用使用。
- 已抽出共用 `UiFormActions` 元件，讓主檔與產能頁的新增 / 編輯 / 取消 / 儲存動作列統一。
- 已新增 `audit_logs` 與 `/audit/logs`，將主資料異動、使用者更新與匯入事件納入審計記錄。
- 已在首頁側欄加入最近異動卡片，讓客戶資訊、登入狀態、今日統計與近期異動的層級更清楚。
- 已將全站主要按鈕配色統一為綠色儲存、灰色取消、紅色停用/刪除。
- 已將 `MasterPage` 清單與 `SearchWorkspace` 查詢結果補上分頁，開始處理高資料量下的列表效能。
- 已把 `ProductionPage` 的 Station Capacity / Model Query 區塊拆成獨立元件，降低單一頁面的程式碼密度。
- 已將首頁側欄補上收合 / 展開 mini mode，並將狀態記住於 session。
- 已將收退料頁主布局改為頂部摘要列 + 左中右三欄配置，並把批次貼上匯入改為 modal。
- 已把收退料操作區改成 segmented control，並補上庫存水位條與批次行動作精簡。
- 已驗證 `frontend` 的 `npm run build` 通過。
- 已將前端表格與 body 字級微調至 12px，並略縮 cell padding，提升工業管理場景下的資訊密度。
- 已讓收退料單筆表單在展開後自動聚焦到治具編號或 Datecode / 序號欄位，減少手動定位成本。

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
- 已保留資料庫內舊欄位作為相容層，避免直接破壞既有資料；目前統一發生在 UI 與 API surface。
- 已重構查詢頁為 `治具 / 機種` 兩種模式，並加入固定統計方格。
- 已讓查詢頁改為面板內滾動，避免內容超出頁面高度。
- 已依圖片移除查詢頁右側重複的治具名稱卡片。
- 已驗證 `npm run build` 與 `python -m compileall backend/app` 通過。
