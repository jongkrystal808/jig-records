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

- 改手機版抽屜選單
  - `frontend/src/components/app/AppMobileDrawer.vue`

- 改全域收退料 / 匯出 modal
  - `frontend/src/components/app/AppGlobalModals.vue`

- 改版本公告 modal / 文案
  - `frontend/src/components/app/AppReleaseNoticeModal.vue`
  - `frontend/src/releaseNotice.ts`
  - 開關協調在 `frontend/src/App.vue`

- 改全域 toast
  - `frontend/src/components/app/AppToastStack.vue`
  - 狀態在 `frontend/src/toastState.ts`

- 改查詢頁
  - `frontend/src/pages/SearchWorkspacePage.vue`
  - `frontend/src/components/search/SearchHeroSection.vue`
  - `frontend/src/components/search/SearchResultPanel.vue`
  - `frontend/src/components/search/FixtureInfoPanel.vue`
  - `frontend/src/components/search/ModelInfoPanel.vue`
  - 查詢 contract / lazy context：`frontend/src/api/searchClient.ts`
  - 查詢型別：`frontend/src/types.ts`

- 改查詢頁最近收 / 退料治具快捷入口
  - 資料整理：`frontend/src/pages/SearchWorkspacePage.vue`
  - 顯示與點擊入口：`frontend/src/components/search/SearchHeroSection.vue`

- 改收退料作業 / overview
  - `frontend/src/pages/InventoryPage.vue`
  - `frontend/src/components/inventory/InventoryOperationBoard.vue`
  - `frontend/src/components/inventory/InventoryOverviewPanel.vue`

- 改批次貼上匯入
  - inventory：`frontend/src/components/inventory/BatchImportPanel.vue`
  - production：`frontend/src/components/production/ProductionBatchImportModal.vue`
  - production page orchestration：`frontend/src/pages/ProductionPage.vue`
  - inventory 的手動 `Tab` 鍵輸入行為也在 `BatchImportPanel.vue`

- 改收退料報表匯出
  - `frontend/src/components/inventory/InventoryExportPanel.vue`

- 改資料維護頁
  - `frontend/src/pages/MasterPage.vue`
  - `frontend/src/components/master/MasterListPanel.vue`
  - `frontend/src/components/master/MasterDetailPanel.vue`

- 改產能頁
  - `frontend/src/pages/ProductionPage.vue`
  - `frontend/src/components/production/ProductionHeaderSection.vue`
  - `frontend/src/components/production/ProductionDetailSection.vue`
  - `frontend/src/components/production/ProductionCapacityPanel.vue`

- 改前端 API 方法
  - 對外入口：`frontend/src/api.ts`
  - 內部分域：`frontend/src/api/*.ts`

- 改前端資料型別
  - `frontend/src/types.ts`

- 改全域狀態
  - `frontend/src/appState.ts`

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

- 改收退料 / 庫存 API
  - `backend/app/routers/inventory.py`
  - `backend/app/services/inventory_service.py`
  - `backend/app/repositories/inventory_repository.py`

- 改 production API
  - `backend/app/routers/production.py`
  - `backend/app/services/production_service.py`

- 改查詢 API
  - `backend/app/routers/search.py`
  - `backend/app/services/search_service.py`

- 改審計 API
  - `backend/app/routers/audit.py`
  - `backend/app/services/audit_service.py`

- 改資料表
  - `backend/app/models/*.py`

- 改後端 schema
  - `backend/app/schemas/*.py`

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
  - 如需新主檔建立，還要同步 `frontend/src/api/masterClient.ts` 與 `backend/app/routers/master.py`

- 改收退料報表匯出 / preview
  - `frontend/src/components/inventory/InventoryExportPanel.vue`
  - `frontend/src/api/inventoryClient.ts`
  - `backend/app/routers/inventory.py`
  - `backend/app/services/inventory_service.py`

- 改 `identifier`
  - 前端共用規則：`frontend/src/utils/identifier.ts`
  - 前端規則測試：`frontend/src/utils/identifier.test.ts`
  - 前端顯示與查詢輸入：`frontend/src/pages/InventoryPage.vue`、`frontend/src/components/inventory/InventoryExportPanel.vue`
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
