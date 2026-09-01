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
  - 負責 session、route、Modern／Form system surface、個人預設介面、onboarding、release notice、global refresh 與全域 modal orchestration

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

- 改全域確認視窗 / 未儲存離開提示
  - 狀態與 Promise 協調：`frontend/src/confirmState.ts`
  - dirty registry、客戶／介面／route／登出與 `beforeunload` 協調：`frontend/src/unsavedChangesGuard.ts`
  - 視窗、鍵盤與焦點行為：`frontend/src/components/common/SystemConfirmDialog.vue`
  - 掛載位置：`frontend/src/App.vue`
  - 功能頁請呼叫 `requestConfirmation()`，不要新增 `window.confirm`

- 改登入／登出 URL 或 route chunk 載入
  - `frontend/src/router/index.ts`
  - `frontend/src/pages/LoginRoutePage.vue`
  - session 清除與登入後導向：`frontend/src/App.vue`

- Modern／Form 全系統分離介面
  - system surface 控制器：`frontend/src/App.vue`
  - route-aware shells：`frontend/src/components/app/ModernSystemSurface.vue`、`frontend/src/components/app/FormSystemSurface.vue`
  - 入口切換：`frontend/src/components/home/HomeUiSurfaceSwitcher.vue`
  - Modern 首頁：`frontend/src/pages/SearchHomePage.vue` -> `frontend/src/components/home/ModernUiSurface.vue` + `frontend/src/styles/surfaces/modern.css`
  - Form shell：`frontend/src/components/home/FormUiSurface.vue` + `frontend/src/styles/surfaces/form.css`
    - 固定報表骨架與功能切換：`frontend/src/components/home/FormUiSurface.vue`
    - 完整文字／分組索引：`frontend/src/components/home/FormWorkspaceSwitcher.vue`
    - `篩選報表`：heading-less `frontend/src/pages/InventoryRelationsPage.vue`
    - `收退料匯入`：report-styled `frontend/src/components/inventory/BatchImportPanel.vue`
    - route dispatcher：`frontend/src/components/home/FormReportOperations.vue`
    - `收退料總檢視`：`frontend/src/components/home/FormTransactionOperations.vue`
    - `產能`：`frontend/src/components/home/FormProductionOperations.vue`
    - `資料維護`：`frontend/src/components/home/FormMasterDataOperations.vue`
    - `收退料帳目管理`／`治具資料品質`：`frontend/src/components/home/FormAdminReports.vue`
    - `圖片維護`：`frontend/src/components/home/FormImageMaintenance.vue`
    - 共用分頁驗證：`frontend/src/utils/formOperations.ts`
    - 共用匯出完成／空結果回饋：`frontend/src/utils/exportFeedback.ts`
    - 遠端候選：`frontend/src/components/home/FormRemoteAutocomplete.vue`
    - 產能貼上預覽：`frontend/src/components/home/FormProductionPasteImport.vue`
    - 使用者客戶權限複選：`frontend/src/components/home/FormUserCustomerScopePicker.vue`
    - 全域選單在 Form UI 透過 `frontend/src/appState.ts` 切換上述表格模式；原獨立 routes 保留
  - 所有角色可切換 Modern／Form；guest 預設 Form，super_admin / admin / user 初始預設 Modern
  - super_admin / admin / user 的登入預設偏好、`ui_surface` route state、舊 `home_mode` 相容與切換前 dirty confirmation 都由 `App.vue` 協調
  - 所有 feature routes 都由 Modern 或 Form shell 呈現，不再使用 `shared` surface
  - Form 模組 route 切換後的頂端定位：`frontend/src/router/index.ts` 的 `scrollBehavior`
  - 查詢工作台的輸入／已搜尋值／選中治具或機種由 `appState.ts` 暫存；切到 Form 報表時轉成精確 `fixture / model` 或關鍵字 `q`，切回 Modern 查詢時完整還原
  - 模式間 query 映射：`frontend/src/utils/searchHomeModeState.ts`

- 改首頁的庫存配置報表模式
  - `frontend/src/pages/InventoryRelationsPage.vue`
  - 手機報表摘要卡：`frontend/src/components/inventory/InventoryReportMobileCards.vue`
  - 報表頁仍透過既有全域收退料作業進入正式流程；共用 `BatchImportPanel.vue` 已改用試算表式方格輸入
  - 正式列資料、統計與聯動選項由 `inventoryClient.ts` 的 configuration-report API 載入；前端只保留當頁 50／100 筆
  - 治具狀態預設 `active`，可切 `inactive / all`；`fixture_status` 同步至 URL、後端頁面／選項／匯出 API
  - 客戶由共用頂欄 `AppTopbar.vue` 單一入口切換；關鍵字、治具、機種、站點、水位、儲位、交易方向／來源／日期的 draft、route state、paging query 與完整結果匯出集中在 `frontend/src/composables/useConfigurationReportState.ts`，頁面負責 API 載入與跨區呈現協調
  - 篩選選擇順序、可移除順位 chips、下游選項聯動與 `priority` query 也由 `useConfigurationReportState.ts` 管理
  - draft／applied 條件差異與尚未套用數量：`frontend/src/utils/reportFilterState.ts`
  - 低水位、未配置、今日收料、今日退料一鍵篩選卡已依需求取消；桌面與手機皆改由一般篩選區套用條件
  - 手機報表列改為治具摘要卡，桌面維持完整寬表；手機分頁為 20／50、桌面為 50／100，皆支援上一頁／下一頁與跳頁
  - 機種全部站點／指定單站最大開站數以站點摘要呈現，點擊後展開治具需求／庫存／可開站／瓶頸報表；圖片與欄位選擇仍由頁面／子元件協調，後端匯出生命週期位於 `useConfigurationReportState.ts`
  - `現場庫存／配置檢查／完整報表` 欄位預設與欄位順序：`frontend/src/utils/reportColumnPresets.ts`
  - 篩選後有效欄位與自動隱藏規則：`frontend/src/utils/reportVisibleColumns.ts`；後端 `populated_columns` 依完整篩選結果計算，不只看目前頁
  - 報表列的客供／自購庫存與可開站數由後端 configuration-report read model 回傳，可開站數先依完整 `model + station` 需求集合計算再套用報表篩選
  - 今日／指定日期收退料模式、客供／自購來源、日期 inline validation、applied filter 摘要與瓶頸治具逐站展開也在這個 page
  - 收退料篩選後的明細勾選與治具列下方交易表格在這個 page；完整結果及明細展開由後端匯出
  - 圖片 dialog focus trap 位於 `FixtureImageDialog.vue`／`UiModalShell.vue`，匯出完成回饋位於 `useConfigurationReportState.ts`；手機初次／套用後自動收合仍由頁面協調
  - 收退料日期套用規則：`frontend/src/utils/reportTransactionFilters.ts`
  - 當頁收退料明細分組：`frontend/src/utils/reportTransactionDetails.ts`
  - 報表 API：`backend/app/routers/inventory.py`、`backend/app/services/configuration_report_service.py`、`backend/app/repositories/configuration_report_repository.py`
  - 報表查詢索引 migration：`backend/alembic/versions/0015_configuration_report_indexes.py`

- 改治具收納與位置索引（`/storage`）
  - 頁面：`frontend/src/pages/StoragePage.vue`
  - API client：`frontend/src/api/storageClient.ts`
  - 型別：`frontend/src/types.ts` 的 `Storage*` / `FixturePlacement*`
  - 後端：`backend/app/routers/storage.py`、`services/storage_service.py`、`repositories/storage_repository.py`
  - 資料表：`backend/app/models/storage.py`
  - migration：`backend/alembic/versions/0019_fixture_storage_index.py`
  - 儲位文字自動同步入口：`backend/app/services/master_service.py`
  - overview 效能：`StorageRepository.list_code_overview_rows()` 以單一 grouped query 產出 container／placement 摘要；不要在 service 恢復逐 code 查詢

- 改治具 / 機種詳細查詢（`/search` 查詢模式；`/search/detail` 相容入口）
  - `frontend/src/pages/SearchWorkspacePage.vue`
  - `frontend/src/components/search/SearchHeroSection.vue`
  - 空白查詢治具總覽：`frontend/src/components/search/FixtureOverviewPanel.vue`
  - `frontend/src/components/search/SearchResultPanel.vue`
  - route query handoff、結果定位與治具／機種編輯 draft 都在這組檔案；跨 route／客戶／介面／登出與重新整理防護由 `frontend/src/unsavedChangesGuard.ts` 統一協調
  - `frontend/src/components/search/FixtureInfoPanel.vue`
  - `frontend/src/components/search/ModelInfoPanel.vue`
  - 治具 detail 的 `以此治具收 / 退料` 訪客隱藏規則也在這組檔案
  - 查詢 contract / lazy context：`frontend/src/api/searchClient.ts`
  - 查詢型別：`frontend/src/types.ts`
  - route query handoff（`mode` / `q` / `page` / `selected_id` / `detail`）：`frontend/src/pages/SearchWorkspacePage.vue`
  - fixture detail -> overview handoff 會依來源指回 `/search?ui_surface=modern&home_mode=query...` 或 `/search/detail`

- 改詳細查詢頁最近收 / 退料治具快捷入口
  - 資料整理：`frontend/src/pages/SearchWorkspacePage.vue`
  - 顯示與點擊入口：`frontend/src/components/search/SearchHeroSection.vue`
  - 搜尋完成後自動定位結果區：`frontend/src/pages/SearchWorkspacePage.vue`
  - 搜尋 CTA、近期治具初始 5 筆／展開最多 20 筆、hero idle 留白也在這組檔案

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
  - inventory grid 的手動 `Tab` 鍵輸入行為位於 `InventoryBatchEntryGrid.vue`
  - 貼上列解析、相似治具比對、退料 `identifier` 庫存預檢與逐列錯誤位於 `frontend/src/composables/useInventoryBatchParser.ts`
  - ready／exception 分組、同批重複合併、`目前庫存`／`交易後庫存` 預覽位於 `frontend/src/composables/useInventoryBatchPreviewState.ts`
  - 收／退料分組送出、409 重複單號確認、失敗後重載庫存摘要與 toast 位於 `frontend/src/composables/useInventoryBatchSubmit.ts`
  - 方格元件：`frontend/src/components/inventory/InventoryBatchEntryGrid.vue`；快速新增、Excel 多列貼上、列增刪共用同一介面
  - 貼上格式辨識：`frontend/src/utils/inventoryBatchClipboard.ts`；支援標準三欄、治具＋流水號合併欄、Markdown pipe 表格、直式配對與含額外欄位的標題表格
  - 預填單一治具會帶入方格空白列；submit 前重複 `fixture + identifier` 合併由 `useInventoryBatchPreviewState.ts` 計算
  - `ownership_type` 由整批 `來源` 控制；不提供逐列切換，且清空 / 重開後會回 `客供`
  - `transaction_no` 前後端都必填；backend 不再自動補單號
  - 舊交易歷史若缺 `transaction_no`，讀取 response 仍容許 `null`，前端顯示為 `（無單號）`
  - 全域 modal 草稿的 `sessionStorage` 暫存 / 恢復也在 `BatchImportPanel.vue`
  - inventory preview 純計算 helper：`frontend/src/utils/inventoryBatchPreview.ts`
  - 退料真正的庫存檢核與逐筆錯誤訊息 fallback 在 `backend/app/services/inventory_service.py`

- 改全域匯出中心
  - `frontend/src/components/app/ExportCenterPanel.vue`
  - dataset list 會依目前角色隱藏僅限 `admin` / `super_admin` 的 `治具資料品質`

- 改資料維護頁
  - `frontend/src/pages/MasterPage.vue`
  - Modern 清單也使用 active-tab server paging；搜尋／狀態條件由 page API 執行，quality 的完整關聯 context 只在進入 quality tab 後載入
  - `frontend/src/components/master/MasterListPanel.vue`
  - `frontend/src/components/master/MasterDetailPanel.vue`
  - 品質快速修正 modal：`frontend/src/components/master/FixtureQualityQuickEditModal.vue`
  - 永久刪除 modal：`frontend/src/components/master/MasterPermanentDeleteModal.vue`
  - 主資料新增／更新／啟停：`frontend/src/composables/useMasterCrudActions.ts`
  - 使用者新增／編輯在 `MasterDetailPanel.vue` 直接共用 `frontend/src/components/home/FormUserCustomerScopePicker.vue` 維護 `allowed_customer_ids`；啟停保留既有客戶範圍
  - 永久刪除／最後一頁退頁／重載：`frontend/src/composables/useMasterEntityDeletion.ts`
  - 唯讀摘要與未選資料狀態：`frontend/src/components/master/MasterReadonlySummary.vue`
  - 主資料預設不選第一筆；選取後先看摘要，明確按編輯才進表單
  - admin 收退料帳目管理：`frontend/src/components/master/TransactionAccountListPanel.vue`
  - admin 收退料帳目案件詳細 / 撤回 / 重算：`frontend/src/components/master/TransactionAccountDetailPanel.vue`
- admin 治具資料品質：`frontend/src/components/master/FixtureQualityPanel.vue`
  - `沒有儲位 / 沒有最低水位` 已支援表格內直接編輯與更新
  - `沒有任何機種關聯` 會導向 `產能管理 -> 治具需求`
- route 對應：`/master/fixtures`、`/master/models`、`/master/stations`、`/master/customers`、`/master/users`、`/master/ledger`、`/master/quality`
  - admin 主資料永久刪除（治具 / 機種 / 站點）：`MasterDetailPanel.vue` 提供入口、`MasterPermanentDeleteModal.vue` 呈現確認、`useMasterEntityDeletion.ts` 協調 API 與刪除後狀態、`frontend/src/api/masterClient.ts` 發送請求
  - 保留歷史時前端交易型別允許 `fixture_id: null`：`frontend/src/types.ts`
  - master 響應式雙欄 breakpoint、手機 `list -> detail` 流程在 `MasterPage.vue`
  - master 清單列鍵盤可操作與 focus 樣式在 `MasterListPanel.vue`

- 改產能頁
  - `frontend/src/pages/ProductionPage.vue`
  - mapping／requirement 以目前 model 的 page API 載入；單筆 CRUD patch 本地集合後只刷新一次 model query，批次匯入／複製才允許範圍重載
  - `ProductionPage.vue` 目前負責 overview/configure route sync 與 `model_id` / `return_to` query 保留；未儲存離頁由共用 `unsavedChangesGuard.ts` 協調
  - `InventoryRelationsPage.vue`、`MasterPage.vue`、`ProductionPage.vue` 的大型樣式分別位於 `frontend/src/styles/surfaces/inventory-relations.css`、`master.css`、`production.css`
  - `frontend/src/components/production/ProductionHeaderSection.vue`
  - `frontend/src/components/production/ProductionDetailSection.vue`
  - `frontend/src/components/production/ProductionRequirementCopyModal.vue`
  - `frontend/src/components/production/ProductionCapacityPanel.vue`
  - `frontend/src/utils/productionStations.ts`
  - `frontend/src/utils/productionCapacityPreview.ts`
  - `frontend/src/utils/productionCopy.ts`
  - configure UI 是 `機種 -> 站點 -> 治具需求` 的 master-detail 工作區；權限顯示、站點整列選取、儲存前產能預估及同／跨機種複製集中在上述 page / detail / copy modal / helper
  - `加入站點`／`加入治具需求` 表單預設收合，新增、編輯或教學對應步驟時再展開
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
  - 大型頁面 surface CSS：`frontend/src/styles/surfaces/inventory-relations.css`、`master.css`、`production.css`
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
  - Form 使用者分頁與授權客戶摘要：`GET /auth/users/page`（僅 `super_admin`）
  - 登入者修改自己的密碼：`POST /auth/password`

- 改主資料 API
  - `backend/app/routers/master.py`
  - `backend/app/services/master_service.py`
  - `GET /master/fixtures/quality` 也在這組
  - Form 分頁／autocomplete：`GET /master/customers/page`、`/fixtures/page`、`/models/page`、`/stations/page`
  - `admin` / `super_admin` 治具永久刪除：`DELETE /master/fixtures/{fixture_id}`
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
  - Form 結果分頁：`GET /production/model-stations/page`、`/fixture-requirements/page`
  - 貼上匯入預覽：`POST /production/model-stations/import/preview`、`/fixture-requirements/import/preview`

- 改查詢 API
  - `backend/app/routers/search.py`
  - `backend/app/services/search_service.py`
  - 空白查詢治具總覽：`GET /search/fixtures/overview`

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
  - `manage` 為 `admin` / `super_admin`，`super_manage` 僅 `super_admin`；兩者都不略過 `user_customers` 客戶範圍

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
  - 報表／Master／Production 頁面專屬樣式分別放在 `frontend/src/styles/surfaces/inventory-relations.css`、`master.css`、`production.css`
  - 共用外殼優先放 `frontend/src/components/Ui*.vue`

- 改批次貼上匯入
  - inventory：`frontend/src/components/inventory/BatchImportPanel.vue`
  - inventory 解析／退料預檢：`frontend/src/composables/useInventoryBatchParser.ts`
  - inventory 預覽／重複合併：`frontend/src/composables/useInventoryBatchPreviewState.ts`
  - inventory 分組送出／409 確認：`frontend/src/composables/useInventoryBatchSubmit.ts`
  - production：`frontend/src/pages/ProductionPage.vue` + `frontend/src/components/production/ProductionBatchImportModal.vue`
  - production domain 邏輯：`frontend/src/composables/useProductionBatchImport.ts`
  - production editor/autocomplete 邏輯：`frontend/src/composables/useProductionEditorState.ts`
  - production 純解析 / 相似比對規則：`frontend/src/utils/productionBatchImport.ts`
  - production autocomplete 共用 UI：`frontend/src/components/UiAutocompleteInput.vue`
  - Form production paste：`frontend/src/components/home/FormProductionPasteImport.vue`
  - Form production remote options：`frontend/src/components/home/FormRemoteAutocomplete.vue`
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
  - 前端 route/editor 綁定：`frontend/src/pages/MasterPage.vue`
  - 刪除入口：`frontend/src/components/master/MasterDetailPanel.vue`
  - 確認 modal：`frontend/src/components/master/MasterPermanentDeleteModal.vue`
  - API／退頁／重載協調：`frontend/src/composables/useMasterEntityDeletion.ts`
  - API client / type：`frontend/src/api/masterClient.ts`、`frontend/src/types.ts`
  - API 與業務 transaction：`backend/app/routers/master.py`、`backend/app/services/master_service.py`
  - 治具關聯資料刪除：`backend/app/repositories/master_repository.py`
  - 收退料 item 保留/刪除與歷史查詢：`backend/app/repositories/inventory_repository.py`
  - ORM / response schema：`backend/app/models/inventory.py`、`backend/app/schemas/inventory.py`、`backend/app/schemas/master.py`
  - DB migration：`backend/alembic/versions/0014_fixture_deletion.py`
  - 權限語意：僅 `manage`（admin / super_admin），且仍受 `user_customers` customer scope 限制
  - 保留模式以 code/name snapshot 顯示與匯出；刪除模式不會移除混合交易中的其他治具 item

- 改治具資料品質問題跳轉規則 / 列內更新
  - `frontend/src/components/master/FixtureQualityPanel.vue`
  - `frontend/src/components/master/FixtureQualityQuickEditModal.vue`
  - `frontend/src/composables/useMasterQuality.ts`
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
  - 空白查詢的 customer-scoped fixture overview 也沿用這組 router / service / repository

- 改新手教學入口位置 / shell 協調
  - `frontend/src/App.vue`
  - `frontend/src/components/app/AppTopbar.vue`
  - `frontend/src/components/app/AppMobileDrawer.vue`
  - `frontend/src/onboarding.ts`
  - 所有角色點擊後都先開啟 picker；guest 可選 7 步快速版或 18 步完整唯讀版
  - guest 的查詢＋報表流程、匯出／總檢視唯讀步驟與 `home_mode` step query 在 `frontend/src/onboarding.ts`
  - super_admin / admin / user 另有 7 步 `report-basics` 報表精簡教學，完整詳細版也包含相同核心報表流程
  - guest picker 會標示需登入角色、需 Admin 與僅 Super Admin 的登入後功能
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
