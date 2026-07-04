# 2026-06 to 2026-07 Update

這份文件整理目前已確認的 2026 年 6 月與 7 月更新，來源包含：

- 本輪對話中已完成與已驗證的工作
- 目前專案程式碼狀態
- `task.md` 的 `Update Log`
- 已同步過的架構與 map 文件

## 2026-07 Update

時間範圍：2026-07-01 ~ 2026-07-04

### 本月重點

#### 1. 新手導覽與教學模式已落地

- 新增全域 `GuidedTour` 導覽元件，支援 spotlight 高亮與跨頁步驟導覽。
- 新增 `frontend/src/onboarding.ts`，集中定義導覽步驟、目標 selector、說明文案與 route。
- 首次登入後會自動啟動新手導覽，並以 session 級別避免同一輪重複播放。
- 搜尋首頁新增「開始新手教學」入口，可手動重新播放導覽。
- `MasterPage` 新增「開始新手導覽」按鈕，可從資料維護頁回到導覽起點。
- 導覽流程已涵蓋：搜尋首頁、收退料入口、收退料資訊匯出入口、收退料總檢視、資料維護、產能管理。

#### 2. 搜尋頁互動進一步收斂

- 搜尋頁保留雙模式：`治具` / `機種`。
- 原本混合 direct / related / identifier 的智慧提示，已收斂為「相近編號」提示。
- 相近編號提示目前採前端排序規則，不屬於後端 search API contract。
- 搜尋首頁新增固定浮動教學入口，方便重播導覽。

#### 3. Shell 與全域入口文件已同步到現況

- 文件已確認目前 shell 是 topbar，而不是舊版 sidebar-first 描述。
- topbar 現況已反映到文檔：登入狀態、客戶切換、今日收 / 退料統計、低水位統計、全域 `收/退料` modal、全域 `收退料資訊匯出` modal、`更多功能` 選單。

#### 4. 架構與索引文件已全面校正

本月已同步更新以下文件，避免文檔落後於實作：

- `task.md`
- `ARCHITECTURE.md`
- `frontend-map.md`
- `backend-map.md`
- `map.md`
- `ARCHITECTURE_LANDING.md`

同步內容包含：onboarding / guided tour、tutorial mode、topbar shell 現況、`InventoryExportPanel.vue`、inventory report export / preview、搜尋頁相近編號提示收斂、測試現況與剩餘失敗點。

### 驗證結果

#### Frontend

- `npm run build`：通過

#### Backend / Tests

- `.venv\\Scripts\\python.exe -m pytest tests -q`：目前為 `4 passed, 1 failed`
- 已確認 `requirements.txt` 原本就有 `openpyxl`，但本機 `.venv` 當時未安裝。
- 已補安裝 `openpyxl` 到目前虛擬環境，排除因缺套件導致 backend import 失敗的問題。

### 目前剩餘問題

- `tests/test_inventory_and_production.py::test_inventory_capacity_and_search_flow` 仍失敗。
- 測試資料使用 `identifier = "202606"`，但現行後端驗證仍限制 `identifier` 必須為 4 碼以內。
- validation error payload 的 `ctx.error` 仍帶出未序列化的 `ValueError`，進一步造成 JSON serialization failure。
- 搜尋頁目前仍沒有查詢結果分頁與可收合篩選區。
- 桌面版 mini sidebar 目前仍未保留。
- 最近異動摘要 API 雖保留，但首頁目前沒有渲染對應卡片。

## 2026-06 Update

時間範圍：2026-06-09 ~ 2026-06-27

### 本月重點

#### 1. Inventory / identifier 模型正式收斂

- 將 `datecode / serial_number` 對外概念統一為單一 `identifier`。
- 前端 API、型別與頁面已改為只收發 `identifier`，不再使用 `manage_type / serial_number`。
- 後端 inventory / master / search 的 schema、router、service、repository 已同步更新，不再對外暴露 legacy 欄位。
- 透過 Alembic `0006_identifier_cleanup` 正式移除 `manage_type / datecode / serial_number` 與 `fixture_serials`。
- 收退料總檢視、篩選欄位與表格文案統一改成 `識別碼`。

#### 2. Production 多機種共站模型定案

- `fixture_requirements` 正式定案為 `model_id + station_id + fixture_id`。
- 同一站點可被多機種共用，但每個機種的站點治具需求各自獨立。
- production 展開與計算邏輯收斂為：`機種 -> 機種已綁定站點 -> 該機種該站點的治具需求`。
- requirement 清單過濾修正為 `model_id + station_id`。
- 查詢頁治具關聯機種與站點詳細不再從站點反推機種。
- `current_open_station_count` 從 backend schema / service、frontend types / props / UI 中正式移除。
- `get_station_capacity` 的呈現語意調整為單站獨立最大開站量。

#### 3. Alembic migration 與啟動流程收斂

- 啟動流程正式收斂到 Alembic，startup 只做 `upgrade head`。
- 新增 `0002_schema_backfill` 作為 legacy DB backfill migration。
- 新增 `0004_model_station_scope`、`0005_remove_warehouse_tables`、`0006_identifier_cleanup`、`0007_user_customer_scope`、`0008_fixture_responsible_user`、`0009_remove_owners_and_scope_fixture_code`。
- 修正 `0004` revision id 過長造成 MySQL `alembic_version.version_num` 寫入失敗問題。
- 加上 legacy revision alias normalization 與舊 revision 自動正規化。
- Docker 環境已驗證 migration 可正常完成且 API / Web 可正常啟動。

#### 4. 客戶權限與治具責任人模型落地

- 一般使用者的客戶可見範圍改由 `user_customers` 管理。
- 客戶可見範圍維護入口從使用者分頁移到客戶分頁，改由 `assigned_user_ids` 管理。
- 治具負責人收斂為該客戶已指派使用者。
- `owners` 資料表移除，責任人正式收斂為 `fixtures.responsible_user_id`。
- 治具代碼唯一鍵正式收斂為 `(customer_id, code)`，允許不同客戶使用相同治具代碼。
- 密碼雜湊升級為 PBKDF2，並保留舊 sha256 密碼相容性。

#### 5. Search Workspace 重構成雙模式查詢

- 查詢頁重構為 `治具 / 機種` 兩種模式。
- 新增固定統計方格與內容區內滾動。
- 移除右側重複治具資訊區塊。
- 查詢頁 fixture detail / model detail 依新資料模型與關聯邏輯重新收斂。
- 後續曾規劃篩選區可收合，但目前程式碼中尚未保留這個互動。

#### 6. Inventory / Master / Production UI 持續收斂

- 收退料頁移除手動表單，只保留批次貼上匯入。
- 批次貼上匯入支援自定義單號，並套用到整批交易。
- 收退料總檢視移除下載範本與 CSV 匯入入口，收斂為單一主查詢頁。
- 收退料頁主布局調整為頂部摘要列 + 左中右三欄配置，並把批次匯入改為 modal。
- 收退料操作區改成 segmented control，補上庫存水位條與批次行動作精簡。
- `MasterPage` 清單補上分頁。
- `ProductionPage` 的 Station Capacity 改為進度條 + 狀態標籤呈現。
- `ProductionPage` 的 Station Capacity / Model Query 區塊拆成獨立元件。
- `MasterPage`、`ProductionPage` 補上 loading / empty state。
- 主資料啟用 / 停用 / 恢復使用流程已補齊，狀態篩選也套用到 `治具 / 機種 / 站點 / 使用者`。

#### 7. 共用元件、測試與工具層補強

- 抽出 `UiFormActions`、`StatusPill` 等共用元件。
- 補上前端日期格式化、API error parsing、顯示 fallback 等共用 util。
- 前端新增 Vitest 測試骨架與共用 helper 測試。
- backend unittest 擴充到 auth / role、API error payload、inventory、production、migration preflight 等流程。
- `auth` 的資料庫依賴改為 lazy import，避免 service test 被 MySQL driver 綁死。

#### 8. Audit 與文件現況校正

- 新增 `audit_logs` 與 `/audit/logs`，將主資料異動、使用者更新與匯入事件納入審計記錄。
- audit API 已可用，但首頁沒有渲染最近異動卡片。
- 6 月底已開始校正文檔，確認 `ARCHITECTURE.md` 與 `task.md` 不再把「最近異動側欄卡片」與「桌面 mini sidebar」誤寫成已落地現況。

### 驗證結果

- 多次驗證 `npm run build` 通過。
- 多次驗證 `python -m compileall backend/app` 通過。
- Docker compose 環境已驗證 API 與 Web 可正常重建與啟動。
- 6 月底已記錄 pytest 尚有 1 個失敗，集中在 `identifier` 驗證與 validation error 序列化。

### 6 月涉及的主要檔案類型

#### 前端

- `frontend/src/pages/SearchWorkspacePage.vue`
- `frontend/src/pages/InventoryPage.vue`
- `frontend/src/pages/MasterPage.vue`
- `frontend/src/pages/ProductionPage.vue`
- `frontend/src/components/production/ProductionCapacityPanel.vue`
- `frontend/src/components/UiFormActions.vue`
- `frontend/src/components/UiStatusPill.vue`
- `frontend/src/utils/date.ts`
- `frontend/src/utils/apiError.ts`
- `frontend/src/utils/display.ts`

#### 後端

- `backend/app/routers/*.py`
- `backend/app/services/*.py`
- `backend/app/repositories/*.py`
- `backend/app/schemas/*.py`
- `backend/app/models/*.py`
- `backend/alembic/versions/*.py`
- `backend/app/core/auth.py`
- `backend/app/core/migrations.py`
- `backend/app/core/schema_patch.py`

### 總結

2026 年 6 月是這個專案從「功能堆疊」走向「模型與流程定案」的月份，核心成果是：

- inventory 正式從多種識別概念收斂到單一 `identifier`
- production 正式定案多機種共站的 requirement 模型
- migration、權限、客戶 scope、治具責任人等基礎規則落地
- 查詢頁、收退料頁、資料維護頁、產能頁的 UI 與資料流開始進入可維護狀態

## 總覽總結

- 2026-06 主要完成資料模型、migration、權限、查詢與主流程 UI 的定案與收斂。
- 2026-07 目前主要完成 onboarding / tutorial mode 落地，以及文檔與索引的大規模同步。
- 目前最值得優先處理的剩餘問題，仍是 inventory 測試中的 `identifier` 驗證規則與 validation error serialization 問題。
