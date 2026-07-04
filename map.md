# Project Map Index

這份文件是索引頁。實際查找請優先看：

- `frontend-map.md`
  - 前端頁面、互動、API 對應
  - 共用元件 / 共用工具
  - 改哪個畫面要進哪個 `.vue`

- `backend-map.md`
  - 後端 router / service / repository / model / schema 對應
  - 各資料表欄位目前的使用面
  - 改 API / 欄位時需要連動的後端層

## 最快定位

### 前端

- 改登入、訪客入口、topbar shell、customer picker、today summary、全域收退料 modal、收退料資訊匯出
  - `frontend/src/App.vue`

- 改查詢頁
  - `frontend/src/pages/SearchWorkspacePage.vue`

- 改收退料作業 / overview / 批次貼上匯入
  - `frontend/src/pages/InventoryPage.vue`

- 改資料維護頁
  - `frontend/src/pages/MasterPage.vue`

- 改產能頁
  - `frontend/src/pages/ProductionPage.vue`
  - `frontend/src/components/production/ProductionCapacityPanel.vue`

- 改前端 API 方法
  - `frontend/src/api.ts`

- 改前端資料型別
  - `frontend/src/types.ts`

- 改全域狀態
  - `frontend/src/appState.ts`

- 改新手導覽步驟 / 流程
  - `frontend/src/onboarding.ts`
  - `frontend/src/components/common/GuidedTour.vue`

- 改全域 toast
  - `frontend/src/toastState.ts`

- 改共用顯示 / 日期 / error parsing
  - `frontend/src/utils/display.ts`
  - `frontend/src/utils/date.ts`
  - `frontend/src/utils/apiError.ts`

### 後端

- 改登入 / 使用者 API
  - `backend/app/routers/auth.py`
  - `backend/app/services/auth_service.py`

- 改主資料 API
  - `backend/app/routers/master.py`
  - `backend/app/services/master_service.py`

- 改收退料 / 庫存 API
  - `backend/app/routers/inventory.py`
  - `backend/app/services/inventory_service.py`

- 改 production API
  - `backend/app/routers/production.py`
  - `backend/app/services/production_service.py`

- 改查詢 API
  - `backend/app/routers/search.py`

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

- 改 migration / 啟動兼容
  - `backend/alembic/versions/*.py`
  - `backend/app/core/migrations.py`
  - `backend/app/core/schema_patch.py`

## 常見修改路徑

- 改 API 欄位
  - 先看 `frontend/src/types.ts`
  - 再看 `frontend/src/api.ts`
  - 再看 `backend-map.md` 對應 model / schema / service

- 改 customer scope / 權限
  - 先看 `backend/app/core/auth.py`
  - 再看 `backend/app/routers/*`
  - 前端顯示面通常在 `frontend/src/App.vue` 與 `frontend/src/router/index.ts`

- 改 fixture / model / station 資料模型
  - 先看 `backend-map.md` 的資料表欄位使用面
  - 再同步 `frontend/src/types.ts`、`frontend/src/api.ts`、對應 page

- 改批次貼上匯入
  - inventory：`frontend/src/components/inventory/BatchImportPanel.vue`
  - production：`frontend/src/pages/ProductionPage.vue`
  - 如需新主檔建立，還要同步 `frontend/src/api.ts` 與 `backend/app/routers/master.py`

- 改收退料報表匯出 / preview
  - `frontend/src/components/inventory/InventoryExportPanel.vue`
  - `frontend/src/api.ts`
  - `backend/app/routers/inventory.py`
  - `backend/app/services/inventory_service.py`

## 編輯原則

- 前端只改 `.ts`、`.vue`、`.css`
- 不要改 `frontend/src/*.js`
- 不要改 `frontend/src/**/*.js.map`
- 不要改 `__pycache__`
- 如果有欄位或 API 變更，記得一起更新 `task.md`、`ARCHITECTURE.md`、map 文件
