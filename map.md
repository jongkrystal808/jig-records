# Project Map Index

這份是索引頁。實際查找請優先看：

- `frontend-map.md`
  - 前端頁面、按鈕、API 對應
  - 全域狀態、路由、樣式入口
  - 哪個畫面要改哪個 `.vue`

- `backend-map.md`
  - 後端 router / service / repository / model / schema 對應
  - 各資料表欄位目前被哪些頁面使用
  - 改欄位時需要連動的後端層

## 最快定位

- 改登入、客戶切換、頂欄、側邊欄：`frontend/src/App.vue`
- 改查詢頁：`frontend/src/pages/SearchWorkspacePage.vue`
- 改收退料頁：`frontend/src/pages/InventoryPage.vue`
- 改資料維護頁：`frontend/src/pages/MasterPage.vue`
- 改產能頁：`frontend/src/pages/ProductionPage.vue`
- 改儲位/圖片頁：`frontend/src/pages/WarehousePage.vue`
- 改前端 API 方法：`frontend/src/api.ts`
- 改前端資料型別：`frontend/src/types.ts`

- 改登入/使用者 API：`backend/app/routers/auth.py`
- 改主資料 API：`backend/app/routers/master.py`
- 改收退料/庫存 API：`backend/app/routers/inventory.py`
- 改查詢 API：`backend/app/routers/search.py`
- 改產能 API：`backend/app/routers/production.py`
- 改儲位/圖片 API：`backend/app/routers/warehouse.py`

- 改資料表：`backend/app/models/*.py`
- 改後端驗證 schema：`backend/app/schemas/*.py`
- 改資料查寫：`backend/app/repositories/*.py`
- 改業務規則：`backend/app/services/*.py`
- 改舊 DB 補欄位：`backend/app/core/schema_patch.py`

## 編輯原則

- 前端只改 `.ts`、`.vue`
- 不要改 `frontend/src/*.js`
- 不要改 `frontend/src/**/*.js.map`
- 不要改 `__pycache__`

## 建議使用方式

- 先到 `frontend-map.md` 找頁面與按鈕
- 再到 `backend-map.md` 找對應 API 與資料表
- 如果是欄位調整，直接看 `backend-map.md` 的「資料表欄位使用面」
