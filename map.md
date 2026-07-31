# Project Map Index

這份文件是索引頁。實際查找請優先看：

- `frontend-map.md`
  - 前端頁面拆分
  - 共用元件 / 共用 CSS / API client 對應
  - 改哪個互動要進哪個 `.vue` / `.ts`

- `backend-map.md`
  - 後端 router / service / repository / model / schema 對應
  - 啟動 / bootstrap / migration 責任分工
  - 改 API / 欄位時需要連動的後端層

## 最快定位

### 前端

- 改全域 shell 協調
  - `frontend/src/App.vue`
  - 只保留 session、route、onboarding、release notice、global refresh orchestration

- 改登入畫面
  - `frontend/src/components/app/AppAuthScreen.vue`

- 改 topbar / customer picker / 今日摘要
  - `frontend/src/components/app/AppTopbar.vue`
  - 桌面版 `新手教學` 入口也在這裡
  - `1366px` 以下 compact header、click/tap popover、摘要可用性也在這裡
  - topbar 今日統計改接 `/inventory/dashboard-summary`，不再由前端用最近 200 筆交易推算
  - 低水位 popover 內直接開 `收 / 退料` 與訪客隱藏規則也在這裡

- 改手機版抽屜選單
  - `frontend/src/components/app/AppMobileDrawer.vue`
  - 手機版 `新手教學` 入口也在這裡
  - scroll / sticky header / overlay 無障礙名稱也在這裡

- 改全域收退料 / 匯出 modal
  - `frontend/src/components/app/AppGlobalModals.vue`
  - 批次 modal 的 preset fixture code 傳遞也在這裡
  - modal 關閉 / 轉總檢視前的草稿確認協調也在這裡

- 改版本公告 modal / 文案
  - `frontend/src/components/app/AppReleaseNoticeModal.vue`
  - `frontend/src/releaseNotice.ts`
  - 開關協調在 `frontend/src/App.vue`
  - 同版本只顯示一次的條件也在 `frontend/src/App.vue`

- 改全域 toast
  - `frontend/src/components/app/AppToastStack.vue`
  - 狀態在 `frontend/src/toastState.ts`

- 改查詢／報表雙模式首頁（`/search`）
  - `frontend/src/pages/SearchHomePage.vue`
  - 所有角色可切換查詢／報表；guest 預設報表，admin / user 初始預設查詢
  - 登入預設偏好、`home_mode` route state、切換前 dirty confirmation 都在這個 page

- 改首頁的庫存配置報表模式
  - `frontend/src/pages/InventoryRelationsPage.vue`
  - 正式資料由 master / inventory / production clients 組合
  - 客戶、關鍵字、治具、機種、站點、水位、儲位篩選與分頁都在這個 page
  - 篩選選擇順序、第一優先提示、下游選項聯動與 `priority` query 也在這個 page
  - 機種全部站點／指定單站最大開站數、治具代碼圖片預覽、表格欄位選擇與本機偏好、全部篩選結果 CSV 匯出都在這個 page
  - 今日／指定日期收退料模式、交易分頁 fixture code 回篩、瓶頸治具逐站展開也在這個 page
  - CSV quoting helper：`frontend/src/utils/csv.ts`
  - 收退料日期套用規則：`frontend/src/utils/reportTransactionFilters.ts`

- 改治具 / 機種詳細查詢（`/search` 查詢模式；`/search/detail` 相容入口）
  - `frontend/src/pages/SearchWorkspacePage.vue`
  - `frontend/src/components/search/SearchHeroSection.vue`
  - `frontend/src/components/search/SearchResultPanel.vue`
  - route query handoff、結果定位、與治具 / 機種編輯 draft 的 route leave / customer switch guard 都在這組檔案
  - `frontend/src/components/search/FixtureInfoPanel.vue`
  - `frontend/src/components/search/ModelInfoPanel.vue`
  - 治具 detail 的 `以此治具收 / 退料` 訪客隱藏規則也在這組檔案
  - 查詢 contract / lazy context：`frontend/src/api/searchClient.ts`
  - 查詢型別：`frontend/src/types.ts`
  - route query handoff（`mode` / `q` / `page` / `selected_id` / `detail`）：`frontend/src/pages/SearchWorkspacePage.vue`
  - fixture detail -> overview handoff 會依來源指回 `/search?home_mode=query...` 或 `/search/detail`

- 改詳細查詢頁最近收 / 退料治具快捷入口
  - 資料整理：`frontend/src/pages/SearchWorkspacePage.vue`
  - 顯示與點擊入口：`frontend/src/components/search/SearchHeroSection.vue`
  - 搜尋完成後自動定位結果區：`frontend/src/pages/SearchWorkspacePage.vue`
  - 搜尋 CTA、近期治具自動收合、hero idle 留白也在這組檔案

- 改收退料作業 / overview
  - `frontend/src/pages/InventoryPage.vue`
  - `frontend/src/components/inventory/InventoryOperationBoard.vue`
  - `frontend/src/components/inventory/InventoryOverviewPanel.vue`
  - overview 主篩選 / 進階篩選 / 分頁 / `return_to` back flow 也在這組檔案

- 改批次貼上匯入
  - inventory：`frontend/src/components/inventory/BatchImportPanel.vue`
  - production：`frontend/src/components/production/ProductionBatchImportModal.vue`
  - production page orchestration：`frontend/src/pages/ProductionPage.vue`
  - production batch composable：`frontend/src/composables/useProductionBatchImport.ts`
  - production editor/autocomplete composable：`frontend/src/composables/useProductionEditorState.ts`
  - production batch pure helper / 規則：`frontend/src/utils/productionBatchImport.ts`
  - production station-availability helper：`frontend/src/utils/productionStations.ts`
  - production / 其他表單可共用的 autocomplete UI：`frontend/src/components/UiAutocompleteInput.vue`
  - inventory 的手動 `Tab` 鍵輸入行為也在 `BatchImportPanel.vue`
  - 退料解析時的 `identifier` 庫存預檢、逐列錯誤標記、送出失敗 toast 也在 `BatchImportPanel.vue`
  - 送出失敗後重新載入 identifier 庫存摘要、避免預覽沿用舊庫存快照的流程也在 `BatchImportPanel.vue`
  - `目前庫存` / `交易後庫存` 預覽與同批逐列累計也在 `BatchImportPanel.vue`
  - 預填單一治具快捷列與 submit 前重複 `fixture + identifier` 合併也在 `BatchImportPanel.vue`
  - 有預填治具時預設走快速模式，批次貼上 textarea 改成按需展開
  - `ownership_type` 由整批 `來源` 控制；不提供逐列切換，且清空 / 重開後會回 `客供`
  - `transaction_no` 前後端都必填；backend 不再自動補單號
  - 舊交易歷史若缺 `transaction_no`，讀取 response 仍容許 `null`，前端顯示為 `（無單號）`
  - 全域 modal 草稿的 `sessionStorage` 暫存 / 恢復也在 `BatchImportPanel.vue`
  - inventory preview 純計算 helper：`frontend/src/utils/inventoryBatchPreview.ts`
  - 退料真正的庫存檢核與逐筆錯誤訊息 fallback 在 `backend/app/services/inventory_service.py`

- 改全域匯出中心
  - `frontend/src/components/app/ExportCenterPanel.vue`
  - dataset list 會依目前角色隱藏 admin-only 的 `治具資料品質`

- 改資料維護頁
  - `frontend/src/pages/MasterPage.vue`
  - `frontend/src/components/master/MasterListPanel.vue`
  - `frontend/src/components/master/MasterDetailPanel.vue`
  - admin 收退料帳目管理：`frontend/src/components/master/TransactionAccountListPanel.vue`
  - admin 收退料帳目案件詳細 / 撤回 / 重算：`frontend/src/components/master/TransactionAccountDetailPanel.vue`
- admin 治具資料品質：`frontend/src/components/master/FixtureQualityPanel.vue`
  - `沒有儲位 / 沒有最低水位` 已支援表格內直接編輯與更新
  - `沒有任何機種關聯` 會導向 `產能管理 -> 治具需求`
- route 對應：`/master/fixtures`、`/master/models`、`/master/stations`、`/master/customers`、`/master/users`、`/master/ledger`、`/master/quality`
  - admin 主資料永久刪除（治具 / 機種 / 站點）：`MasterPage.vue`、`MasterDetailPanel.vue`、`frontend/src/api/masterClient.ts`
  - 保留歷史時前端交易型別允許 `fixture_id: null`：`frontend/src/types.ts`
  - master 響應式雙欄 breakpoint、手機 `list -> detail` 流程在 `MasterPage.vue`
  - master 清單列鍵盤可操作與 focus 樣式在 `MasterListPanel.vue`

- 改產能頁
  - `frontend/src/pages/ProductionPage.vue`
  - `ProductionPage.vue` 目前負責 overview/configure route sync、`model_id` / `return_to` query 保留、以及未儲存離頁 guard
  - `frontend/src/components/production/ProductionHeaderSection.vue`
  - `frontend/src/components/production/ProductionDetailSection.vue`
  - `frontend/src/components/production/ProductionRequirementCopyModal.vue`
  - `frontend/src/components/production/ProductionCapacityPanel.vue`
  - `frontend/src/utils/productionStations.ts`
  - `frontend/src/utils/productionCapacityPreview.ts`
  - `frontend/src/utils/productionCopy.ts`
  - configure UI 是 `機種 -> 站點 -> 治具需求` 的 master-detail 工作區；權限顯示、站點整列選取、儲存前產能預估及同／跨機種複製集中在上述 page / detail / copy modal / helper
  - 複製 API：`POST /api/v2/production/fixture-requirements/copy`；預設跳過衝突，明確覆蓋才更新，未綁定目標站點會自動補 mapping

- 改前端 API 方法
  - 對外入口：`frontend/src/api.ts`
  - 內部分域：`frontend/src/api/*.ts`

- 改前端資料型別
  - `frontend/src/types.ts`

- 改全域狀態
  - `frontend/src/appState.ts`
  - session / customer 還原、customer switch guard、全域 batch modal shortcut request 也在這裡

- 改新手導覽步驟 / 流程
  - `frontend/src/onboarding.ts`
  - `frontend/src/components/common/GuidedTour.vue`
  - `frontend/src/components/common/OnboardingFlowPicker.vue`

- 改共用顯示 / 日期 / error parsing
  - `frontend/src/utils/display.ts`
  - `frontend/src/utils/identifier.ts`
  - `frontend/src/utils/date.ts`
  - `frontend/src/utils/apiError.ts`

- 改共用 UI 元件 / 共用樣式
  - 元件：`frontend/src/components/Ui*.vue`
  - CSS utility：`frontend/src/styles.css`
  - `Production` 的 autocomplete 欄位已收斂到 `frontend/src/components/UiAutocompleteInput.vue`

### 後端

- 改啟動 / bootstrap 路徑
  - launcher：`main.py`
  - bootstrap：`backend/app/bootstrap.py`
  - FastAPI app：`backend/app/main.py`
  - migration gate / offline compat：`backend/app/core/migrations.py`、`backend/app/tools/migration_check.py`

- 改登入 / 使用者 API
  - `backend/app/routers/auth.py`
  - `backend/app/services/auth_service.py`

- 改主資料 API
  - `backend/app/routers/master.py`
  - `backend/app/services/master_service.py`
  - `GET /master/fixtures/quality` 也在這組
  - admin 治具永久刪除：`DELETE /master/fixtures/{fixture_id}`
  - 刪除 orchestration：`backend/app/services/master_service.py`、`backend/app/repositories/master_repository.py`
  - 收/退料歷史保留或刪除：`backend/app/repositories/inventory_repository.py`、`backend/app/models/inventory.py`
  - schema migration：`backend/alembic/versions/0014_fixture_deletion.py`

- 改收退料 / 庫存 API
  - `backend/app/routers/inventory.py`
  - `backend/app/services/inventory_service.py`
  - `backend/app/repositories/inventory_repository.py`
  - `/transactions/overview` 分頁 detail-row contract 也在這組檔案
  - 撤回案件 / 全量重算 inventory state 也在這組檔案

- 改 production API
  - `backend/app/routers/production.py`
  - `backend/app/services/production_service.py`

- 改查詢 API
  - `backend/app/routers/search.py`
  - `backend/app/services/search_service.py`

- 改審計 API
  - `backend/app/routers/audit.py`
  - `backend/app/services/audit_service.py`
  - request-level audit middleware：`backend/app/core/audit_logging.py`
  - file logger / `logs/audit.log`：`backend/app/core/logging.py`

- 改資料表
  - `backend/app/models/*.py`

- 改後端 schema
  - `backend/app/schemas/*.py`
  - inventory 管理回傳型別：`backend/app/schemas/inventory.py`

- 改資料查寫
  - `backend/app/repositories/*.py`

- 改權限 / customer scope
  - `backend/app/core/auth.py`

- 改 migration / DB 相容
  - `backend/alembic/versions/*.py`
  - `backend/app/core/migrations.py`
  - `backend/app/core/schema_patch.py`

- 改錯誤序列化 / validation handler
  - `backend/app/core/errors.py`

## 常見修改路徑

- 改 API 欄位
  - 先看 `frontend/src/types.ts`
  - 再看 `frontend/src/api.ts`
  - 再看 `frontend-map.md` 與 `backend-map.md` 的對應 router / service / schema

- 改 domain API 方法
  - 外部呼叫面不變：`import { api } from "@/api"`
  - 內部實作請進 `frontend/src/api/authClient.ts`、`masterClient.ts`、`inventoryClient.ts`、`productionClient.ts`、`searchClient.ts`、`auditClient.ts`
  - transport / error handling 在 `frontend/src/api/core.ts`

- 改頁面視覺與互動
  - 先看 page 容器
  - 再看對應的拆分元件
  - 共用樣式優先放 `frontend/src/styles.css`
  - 共用外殼優先放 `frontend/src/components/Ui*.vue`

- 改批次貼上匯入
  - inventory：`frontend/src/components/inventory/BatchImportPanel.vue`
  - production：`frontend/src/pages/ProductionPage.vue` + `frontend/src/components/production/ProductionBatchImportModal.vue`
  - production domain 邏輯：`frontend/src/composables/useProductionBatchImport.ts`
  - production editor/autocomplete 邏輯：`frontend/src/composables/useProductionEditorState.ts`
  - production 純解析 / 相似比對規則：`frontend/src/utils/productionBatchImport.ts`
  - production autocomplete 共用 UI：`frontend/src/components/UiAutocompleteInput.vue`
  - 如需新主檔建立，還要同步 `frontend/src/api/masterClient.ts` 與 `backend/app/routers/master.py`
  - 若是退料貼上預覽要先擋 `datecode/編號` 無庫存，還要同步看 `frontend/src/api/inventoryClient.ts` 的 `listIdentifierStockSummary()` 與 `backend/app/services/inventory_service.py`

- 改收退料帳目管理 / 撤回 / 重算
  - `frontend/src/pages/MasterPage.vue`
  - `frontend/src/components/master/TransactionAccountListPanel.vue`
  - `frontend/src/components/master/TransactionAccountDetailPanel.vue`
  - `frontend/src/api/inventoryClient.ts`
  - `frontend/src/types.ts`
  - `backend/app/routers/inventory.py`
  - `backend/app/services/inventory_service.py`
  - `backend/app/repositories/inventory_repository.py`
  - ledger 已改成 transaction-level server-side paging/filter；品質頁 stock mismatch 跳入會預填治具篩選
  - admin ledger transaction 分頁在 backend 以 `transaction id desc` 排序，避免 MySQL 對 `DISTINCT id + ORDER BY occurred_at` 報錯
  - `backend/app/repositories/inventory_repository.py`
  - `backend/app/schemas/inventory.py`


- 改治具永久刪除 / 被刪治具的收退料歷史
  - 前端流程：`frontend/src/pages/MasterPage.vue`
  - 刪除入口：`frontend/src/components/master/MasterDetailPanel.vue`
  - API client / type：`frontend/src/api/masterClient.ts`、`frontend/src/types.ts`
  - API 與業務 transaction：`backend/app/routers/master.py`、`backend/app/services/master_service.py`
  - 治具關聯資料刪除：`backend/app/repositories/master_repository.py`
  - 收退料 item 保留/刪除與歷史查詢：`backend/app/repositories/inventory_repository.py`
  - ORM / response schema：`backend/app/models/inventory.py`、`backend/app/schemas/inventory.py`、`backend/app/schemas/master.py`
  - DB migration：`backend/alembic/versions/0014_fixture_deletion.py`
  - 權限語意：僅 `manage`（admin），且仍受 `user_customers` customer scope 限制
  - 保留模式以 code/name snapshot 顯示與匯出；刪除模式不會移除混合交易中的其他治具 item

- 改治具資料品質問題跳轉規則 / 列內更新
  - `frontend/src/components/master/FixtureQualityPanel.vue`
  - `frontend/src/pages/MasterPage.vue`
  - `frontend/src/pages/SearchWorkspacePage.vue`

- 改全域匯出中心 / 收退料匯出條件
  - `frontend/src/components/app/ExportCenterPanel.vue`
  - `frontend/src/api/inventoryClient.ts`
  - `frontend/src/components/app/AppGlobalModals.vue`
  - `backend/app/routers/inventory.py`
  - `backend/app/services/inventory_service.py`

- 改 `identifier`
  - 前端共用規則：`frontend/src/utils/identifier.ts`
  - 前端規則測試：`frontend/src/utils/identifier.test.ts`
  - 前端顯示與查詢輸入：`frontend/src/pages/InventoryPage.vue`、`frontend/src/components/app/ExportCenterPanel.vue`
  - 前端顯示文字：`frontend/src/utils/display.ts`
  - 後端共用規則：`backend/app/utils/identifier_rules.py`
  - schema 套用點：`backend/app/schemas/inventory.py`
  - service / repository 查詢鏈：`backend/app/services/inventory_service.py`、`backend/app/repositories/inventory_repository.py`
  - 規則單元測試：`backend/tests/test_identifier_rules.py`
  - UI 可改叫 `datecode/編號`，但不要修改內部 `identifier` 欄位名

- 改搜尋排序 / 分頁 / lazy context
  - router：`backend/app/routers/search.py`
  - service：`backend/app/services/search_service.py`
  - repository：`backend/app/repositories/search_repository.py`
  - schema：`backend/app/schemas/search.py`
  - migration / index：`backend/alembic/versions/0011_search_indexes.py`

- 改新手教學入口位置 / shell 協調
  - `frontend/src/App.vue`
  - `frontend/src/components/app/AppTopbar.vue`
  - `frontend/src/components/app/AppMobileDrawer.vue`
  - `frontend/src/onboarding.ts`
  - guest 點擊後直接啟動、admin / user picker 分流在 `App.vue`
  - guest 的查詢＋報表合併流程、`home_mode` step query 在 `frontend/src/onboarding.ts`
  - guest production route guard：`frontend/src/router/index.ts`

- 改 migration compatibility / schema patch 退場
  - runtime gate：`backend/app/core/migrations.py`
  - logging bootstrap：`backend/app/core/logging.py`
  - historical backfill：`backend/app/core/schema_patch.py`
  - offline check tool：`backend/app/tools/migration_check.py`
  - operator runbook：`MIGRATION_GATE_RUNBOOK.md`
  - environment inventory：`MIGRATION_ENVIRONMENT_INVENTORY.md`

## 編輯原則

- 前端只改 `.ts`、`.vue`、`.css`
- 不要改 `frontend/src/*.js`
- 不要改 `frontend/src/**/*.js.map`
- 不要改 `__pycache__`
- 如果有欄位或 API 變更，記得一起更新 `task.md`、`ARCHITECTURE.md`、map 文件
