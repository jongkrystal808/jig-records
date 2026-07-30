# Frontend Map

這份文件回答三件事：

- 每個頁面 / 主要操作現在對應哪個 page 與拆分元件
- 要改畫面、互動或 API 時應該進哪個檔案
- 目前哪些共用元件 / 共用 CSS / API client 已經抽出

## 入口檔與全域骨架

- `frontend/src/main.ts`
  - Vue 啟動入口
  - 掛載 `router` 與 `App.vue`

- `frontend/src/router/index.ts`
  - 路由表
  - `/search` -> `SearchWorkspacePage.vue`
  - `/inventory` -> `InventoryPage.vue`
  - `/inventory/overview` -> `InventoryPage.vue`
  - `/master` -> redirect `/master/fixtures`
- `/master/fixtures` -> `MasterPage.vue`
- `/master/models` -> `MasterPage.vue`
- `/master/stations` -> `MasterPage.vue`
- `/master/customers` -> `MasterPage.vue`
- `/master/users` -> `MasterPage.vue`
- `/master/ledger` -> `MasterPage.vue`
- `/master/quality` -> `MasterPage.vue`
- `/production` -> `ProductionPage.vue`
- `/production/mapping` -> `ProductionPage.vue`
- `/production/requirements` -> `ProductionPage.vue`
- `/production` 目前是總覽模式；`/production/mapping` 與 `/production/requirements` 目前都進同一個 `產能設定` 工作區
- guest 進 `/master` 會被導回 `/search`

- `frontend/src/App.vue`
  - 全域 shell 協調器
  - 只保留 session、route、onboarding、release notice、topbar stats refresh、global modal open state
  - 從 `sessionStorage` 還原 session / current customer
  - customer switch confirm 與全域 batch shortcut request 協調
  - 今日收料 / 今日退料 / 低水位 / 最近收退料資料改由 backend dashboard summary API 載入
  - 不再直接承接整塊登入頁、topbar、drawer、toast template
  - 協調 onboarding 分類選單與 guided tour 播放
  - release notice 同版本只顯示一次

- `frontend/src/components/app/AppAuthScreen.vue`
  - 登入畫面
  - 訪客入口

- `frontend/src/components/app/AppTopbar.vue`
  - 頂部導覽列
  - customer picker
  - 今日收料 / 退料 / 低水位摘要
  - 上述統計與最近收 / 退料資料改由 backend dashboard summary API 提供
  - `1366px` 以下 compact header
  - click/tap popover 與 keyboard-accessible daily summary
  - 低水位 popover 的單筆 `收 / 退料` 快捷動作
  - 訪客不顯示會觸發收退料 modal 的快捷動作

- `frontend/src/components/app/AppMobileDrawer.vue`
  - 手機版抽屜選單
  - scrollable drawer
  - sticky header
  - overlay / picker accessibility naming

- `frontend/src/components/app/AppGlobalModals.vue`
  - 全域 `收 / 退料` modal
  - 全域 `匯出中心` modal
  - batch modal close / overview handoff 的事件轉發

- `frontend/src/components/app/AppReleaseNoticeModal.vue`
  - 版本公告 modal

- `frontend/src/components/app/AppToastStack.vue`
  - 全域 toast 顯示

- `frontend/src/appState.ts`
  - 全域登入 session
  - customer 選擇
  - onboarding 狀態
  - onboarding 分類選擇狀態
  - customer switch guard registry
  - 全域 batch modal shortcut request

- `frontend/src/onboarding.ts`
  - 新手導覽 flow 定義
  - 依頁面 / tab 分類的教學內容
  - 每一步對應 route / `data-tour` target / 文案 / 方向
  - 五張單一功能精簡教學，加上一張逐區說明主要按鈕的全系統詳細版

- `frontend/src/components/common/OnboardingFlowPicker.vue`
  - 新手教學分類選單
  - 完整詳細版固定置頂為推薦入口，精簡教學另列於下方

- `frontend/src/releaseNotice.ts`
  - 版本公告內容
  - `versionId` / 顯示標題 / 摘要 / highlight 文案
  - bump `versionId` 才會重新顯示新版提示

- `frontend/src/toastState.ts`
  - 全域 toast 狀態

- `frontend/src/styles.css`
  - 全域 CSS 變數
  - 共用按鈕、panel、modal、table、chip、summary、state utility

## API Client 結構

- `frontend/src/api.ts`
  - 對外穩定入口
  - 保持 `import { api } from "@/api"` 不變
  - 只做 barrel 聚合

- `frontend/src/api/core.ts`
  - transport
  - headers
  - query string
  - response / error handling

- `frontend/src/api/authClient.ts`
  - auth / user 相關 API

- `frontend/src/api/masterClient.ts`
  - fixture / model / station / customer 相關 API

- `frontend/src/api/inventoryClient.ts`
  - stock / alert / receipt / return / transaction / export 相關 API

- `frontend/src/api/productionClient.ts`
  - model-station / fixture requirement / capacity / model query

- `frontend/src/api/searchClient.ts`
  - global search

- `frontend/src/api/auditClient.ts`
  - audit log

- `frontend/src/api/mediaClient.ts`
  - fixture image URL 與 blob fetch

## 共用元件 / 共用工具

- `frontend/src/components/common/GuidedTour.vue`
  - 全域導覽浮層
  - spotlight 目標高亮
  - route-aware step 流程
  - 依實際卡片高度定位，避免固定高度造成偏移

- `frontend/src/components/common/InlineSpinner.vue`
  - 小型 inline loading indicator

- `frontend/src/components/UiFormActions.vue`
  - 新增 / 編輯 / 取消 / 停用動作列

- `frontend/src/components/UiSectionHeader.vue`
  - panel 標題列

- `frontend/src/components/UiSplitDetailLayout.vue`
  - summary rail + detail scroll 的共用殼層

- `frontend/src/components/UiStatusPill.vue`
  - 主資料 / 狀態標籤顯示

- `frontend/src/components/UiSummaryCards.vue`
  - 摘要卡片列

- `frontend/src/utils/date.ts`
  - 本地日期 key / 顯示輔助

- `frontend/src/utils/apiError.ts`
  - API error message 解析

- `frontend/src/utils/display.ts`
  - fallback text / ownership label / stock status label 等顯示工具

- `frontend/src/utils/identifier.ts`
  - 前端 `identifier` 共用規則
  - 短純數字補零
  - legacy 值原樣保留
  - 保留 query helper，避免 UI 端再次手寫同語意判斷

## 全域流程 API 對應

### `frontend/src/App.vue`

- 登入按鈕
  - `api.login`

- 訪客入口按鈕
  - `api.guestEntry`

- 初始化 / session 恢復後載入 customer
  - `api.listCustomers`

- customer 切換後更新 topbar summary
  - `api.listDashboardSummary`

- 全域收退料 modal
  - `AppGlobalModals.vue`
  - 內部共用 `BatchImportPanel.vue`

- 全域匯出中心 modal
  - `AppGlobalModals.vue`
  - 內部共用 `ExportCenterPanel.vue`

- 版本公告 modal
  - `AppReleaseNoticeModal.vue`
  - 文案定義在 `releaseNotice.ts`

### 改全域畫面時去哪裡

- 改 session 恢復、route 轉向、onboarding 狀態、topbar refresh orchestration
  - `frontend/src/App.vue`

- 改登入卡片
  - `frontend/src/components/app/AppAuthScreen.vue`

- 改頂部導覽、customer picker、today summary
  - `frontend/src/components/app/AppTopbar.vue`
  - compact header / click popover / topbar a11y 也在這裡

- 改手機版選單
  - `frontend/src/components/app/AppMobileDrawer.vue`
  - drawer scroll / sticky header / overlay a11y 也在這裡

- 改全域收退料 / 匯出 modal
  - `frontend/src/components/app/AppGlobalModals.vue`

- 改版本公告顯示條件 / 文案
  - `frontend/src/App.vue`
  - `frontend/src/components/app/AppReleaseNoticeModal.vue`
  - `frontend/src/releaseNotice.ts`
  - `frontend/src/App.vue` 負責「同版本只顯示一次」的開關條件

- 改全域 toast UI
  - `frontend/src/components/app/AppToastStack.vue`
  - 狀態邏輯在 `frontend/src/toastState.ts`

## 查詢頁

- page：`frontend/src/pages/SearchWorkspacePage.vue`
- 子元件：
  - `frontend/src/components/search/SearchHeroSection.vue`
  - `frontend/src/components/search/SearchResultPanel.vue`
  - `frontend/src/components/search/FixtureInfoPanel.vue`
  - `frontend/src/components/search/ModelInfoPanel.vue`
  - `frontend/src/components/search/FixtureEditForm.vue`
  - `frontend/src/components/search/ModelEditForm.vue`

### 目前責任分工

- `SearchWorkspacePage.vue`
  - mode / query state
  - route query handoff (`mode` / `q` / `page` / `selected_id` / `detail`)
  - paginated global search state
  - load more / selected result state
    - 最近收 / 退料治具快捷入口資料整理
  - fixture / model result 組裝與排序承接
  - fixture / model context lazy fetch
  - in-context edit dirty state / route leave / browser unload / customer switch guard
  - fixture detail -> inventory overview / batch modal handoff
    - overview handoff 只帶 `fixture_code` 與 `return_to`
  - 開啟 onboarding 分類選單
  - 搜尋結果自動 scroll 進第一屏
  - idle hero 不再使用固定 viewport-height 垂直置中

- `SearchHeroSection.vue`
  - 查詢首頁 hero shell
  - mode switch
  - smart hints
  - smart hints 收合 / 展開
  - 最近收 / 退料治具快捷入口
  - onboarding 入口
  - 明確 `搜尋` CTA
  - 查詢後自動收合近期治具
  - 搜尋欄 / mode switch 無障礙語意

- `SearchResultPanel.vue`
  - 查詢結果外層殼層

- `FixtureInfoPanel.vue`
  - 治具 detail
  - 圖片、identifier stock、transaction context
  - 單治具 `收 / 退料` 與完整歷史跳轉動作
  - 訪客不顯示 `以此治具收 / 退料`

- `ModelInfoPanel.vue`
  - 機種 detail
  - station / fixture requirement / stock context

### 主要功能

- 雙模式查詢：`治具` / `機種`
- fixture detail
- model detail
- fixture 圖片預覽
- datecode/編號庫存摘要（先依客供 / 自購分組，再於各來源區塊列出編號與數量；不在每個編號後重複來源）
- transaction context
- 最近收 / 退料治具快捷入口點擊後，搜尋完成會自動捲動到結果區
- 區塊 chip 顯示切換與 localStorage 記憶
- 最近收 / 退料治具快捷入口
- 首頁固定「開始新手教學」入口

### API 對應

- 初始化載入
  - `api.listFixtures`
  - `api.listStock`
  - `api.listTransactions`
  - `api.listIdentifierStockSummary`
  - `api.listModels`
  - `api.listStations`
  - `api.listFixtureRequirements`

- fixture / 一般查詢
  - `api.globalSearch`

- model query
  - `api.getModelQuery`

- fixture 圖片
  - `fixtureImageUrlByCode`
  - `fetchFixtureImageObjectUrl`
  - `GET /api/v2/master/fixtures/{fixture_code}/image`

### 改查詢頁時去哪裡

- 改查詢 state、route query handoff、load more、快捷入口資料來源、selected context 載入、section persistence、搜尋後結果區自動定位
  - `frontend/src/pages/SearchWorkspacePage.vue`
  - 搜尋頁治具 / 機種內嵌編輯 draft 的 route leave、browser unload、customer switch guard 也在這裡

- 改首頁 hero、快捷入口、onboarding 按鈕
  - `frontend/src/components/search/SearchHeroSection.vue`
  - 搜尋 CTA、近期治具自動收合也在這裡

- 改查詢結果外殼與版面
  - `frontend/src/components/search/SearchResultPanel.vue`

- 改查詢 API contract 或 context 載入方法
  - `frontend/src/api/searchClient.ts`
  - `frontend/src/types.ts`

- 改治具 / 機種 detail
  - `frontend/src/components/search/FixtureInfoPanel.vue`
  - `frontend/src/components/search/ModelInfoPanel.vue`

- 改 fixture 圖片 URL 或載入策略
  - `frontend/src/api/mediaClient.ts`
  - `frontend/src/pages/SearchWorkspacePage.vue`

## 收退料頁

- page：`frontend/src/pages/InventoryPage.vue`
- 子元件：
  - `frontend/src/components/inventory/InventoryOperationBoard.vue`
  - `frontend/src/components/inventory/InventoryOverviewPanel.vue`
  - `frontend/src/components/inventory/BatchImportPanel.vue`
  - `frontend/src/components/app/ExportCenterPanel.vue`

### 目前責任分工

- `InventoryPage.vue`
  - 初始化資料載入
  - route mode 切換
  - operation metrics / overview filters / export orchestration
  - overview route query sync（filters / page / page_size / `return_to`）

- `InventoryOperationBoard.vue`
  - 收料 / 退料操作視圖
  - KPI cards（含總庫存、客供庫存、自購庫存）
  - 現有庫存與低水位表格顯示總庫存 / 客供 / 自購拆分
  - 嵌入 `BatchImportPanel.vue`

- `InventoryOverviewPanel.vue`
  - overview 篩選
  - 交易表格
  - 主篩選 / 進階篩選切換
  - 進階篩選可依來源選擇全部 / 客供 / 自購
  - `4 / 3 / 2 / 1` 欄 responsive filter layout
  - page / page size / jump pager
  - `返回來源` 按鈕

- `BatchImportPanel.vue`
  - 批次貼上解析
  - 重複交易確認提示
  - 貼上欄支援手動輸入 `Tab` 分隔資料
  - `transaction_no` 在前端與 backend contract 都維持必填，不使用 backend 自動補號
  - 歷史交易若缺 `transaction_no`，清單 / 詳細 / 搜尋預覽 / 總檢視統一顯示 `（無單號）`
  - 整批 `來源` 選擇（`客供` 預設 / `自購`）
  - 預填治具快捷列
  - 預填治具入口預設先走快速輸入，批次貼上框改成手動展開
  - 新治具建立
  - 相似治具確認 / 替換
  - 依 datecode 總量顯示 `目前庫存` / `交易後庫存` 預覽
  - `來源` 用於交易分類；退料預檢不額外增加來源限制
  - 同批重複 `治具 + datecode/編號` 的逐列累計庫存預覽
  - submit 前相同 `fixture + identifier` ready 列合併
  - tutorial sandbox 試跑
  - 寫入前 `identifier` 正規化改走 `frontend/src/utils/identifier.ts`
  - 前端對使用者顯示 `datecode/編號` 文案
  - customer switch guard
  - global modal draft state emit
  - `sessionStorage` draft persist / restore（modal 使用）
  - draft restore 不保留上一次的 `自購` 選擇，重開後回 `客供`

- `ExportCenterPanel.vue`
  - 統一資料集選擇
  - role-aware dataset filtering（guest / user 不顯示 `治具資料品質`）
  - 收退料明細的自定義條件可依來源選擇全部 / 客供 / 自購
  - onboarding 進入匯出進階篩選步驟時會自動展開明細與自定義條件
  - 匯出格式 / 範圍選擇
  - 收退料條件篩選
  - 匯出欄位預覽
  - 收退料 `xlsx` / `txt`，其餘資料 `csv`

### 路由模式

- `/inventory`
  - operation-first

- `/inventory/overview`
  - overview-first

### API 對應

- 初始化載入
  - `api.listFixtures`
  - `api.listStock`
  - `api.listAlerts`
  - `api.listTransactions`

- 送出收料
  - `api.createReceipt`
  - `api.createReceiptWithOptions`

- 送出退料
  - `api.createReturn`
  - `api.createReturnWithOptions`

- overview 查詢
  - `api.listTransactionOverviewPage`

- overview 匯出 CSV
  - `api.exportTransactionsCsv`

- 報表 preview / 匯出
  - `api.previewTransactionReportExport`
  - `api.exportTransactionReport`

- 批次貼上匯入內的新治具建立
  - `api.createFixture`

- 批次預覽庫存資料
  - `api.listStock`
  - `api.listIdentifierStockSummary`
  - 兩者都包含 `stock_qty / customer_supplied_qty / self_purchased_qty`

### 改收退料頁時去哪裡

- 改 page route mode、data refresh、overview filter state
  - `frontend/src/pages/InventoryPage.vue`
  - route query / pager / `return_to` 也在這裡

- 改操作頁 KPI / frame / layout
  - `frontend/src/components/inventory/InventoryOperationBoard.vue`

- 改 overview 篩選欄位與交易表格
  - `frontend/src/components/inventory/InventoryOverviewPanel.vue`
  - 主篩選 / 進階篩選與 responsive 欄位配置也在這裡

- 改批次貼上解析規則 / `Tab` 鍵輸入行為 / 相似治具比對 / 匯入預覽表 / 重複交易確認提示 / tutorial mode
  - `frontend/src/components/inventory/BatchImportPanel.vue`
  - preview 純計算 helper：`frontend/src/utils/inventoryBatchPreview.ts`

- 改匯出中心互動 / preview / radio 選擇樣式
  - `frontend/src/components/app/ExportCenterPanel.vue`
  - `frontend/src/api/inventoryClient.ts`

## 資料維護頁

- page：`frontend/src/pages/MasterPage.vue`
- 子元件：
  - `frontend/src/components/master/MasterListPanel.vue`
  - `frontend/src/components/master/MasterDetailPanel.vue`
  - `frontend/src/components/master/FixtureQualityPanel.vue`

### 目前責任分工

- `MasterPage.vue`
  - route-driven tab state
  - 初始化載入
  - CRUD orchestration
  - import / export / template download
  - summary metrics
  - admin ledger server-side paging / filter orchestration
  - admin 治具資料品質報表
  - 治具資料品質列內更新 `儲位 / 最低水位`
  - quality `stock_mismatch` -> ledger 預填治具篩選
  - admin 主資料永久刪除 dialog state 與送出 orchestration
  - 刪除完成後重載 fixtures / quality / models / stations 並清除選取
  - `1100px` 以上維持 list/detail 雙欄
  - 手機版 `清單 -> 明細` 流程切換

- `MasterListPanel.vue`
  - tab 清單
  - 搜尋 / 篩選
  - 分頁列表
  - 頁數提示 / 總筆數 / 翻頁動作固定在表格上方
  - row focus / `Enter` / `Space` keyboard interaction

- `MasterDetailPanel.vue`
  - fixture / model / station / customer / user detail form
  - admin-only 主資料永久刪除入口（治具 / 機種 / 站點）
  - 透過 props 將刪除請求交回 `MasterPage.vue`

### 主要功能

- fixture / model / station / customer / user / ledger / quality tab
- tab 清單分頁
- 狀態篩選 / 關鍵字搜尋
- fixture 維護 `responsible_user_id` / `min_stock_qty` / `storage_location`
- customer 維護 `assigned_user_ids`
- user 建立 / 更新 / 停用 / 重設密碼
- fixture / model / station CSV 匯入匯出 / 範本下載
- 從資料維護頁重新啟動新手導覽

- admin 可永久刪除治具，並選擇保留或刪除該治具的收/退料紀錄
- admin 也可永久刪除機種與站點，刪除前會提示關聯 `mapping / requirement / capacity summary` 將一併刪除
- 保留歷史為預設建議選項；刪除歷史不影響混合交易中的其他治具明細
- `治具資料品質` 中的 `沒有儲位 / 沒有最低水位` 已改成表格內直接編輯與送出，不再先開彈窗
- 儲位輸入規則改為 `產線儲位`、`部門儲位` 分欄維護；品質頁固定提示為「產線儲位、部門儲位分開填寫，只填一個也可」
- `治具資料品質` 中的 `沒有任何機種關聯` 會跳到 `產能管理 -> 治具需求`
### API 對應

- 頁面初始化
  - `api.getFixtureQualityReport`
  - `api.listFixtures`
  - `api.listModels`
  - `api.listStations`
  - `api.listCustomers`
  - `api.listCustomerUsers`
  - `api.listUsers`

- fixture tab
  - `api.createFixture`
  - `api.updateFixture`
  - `api.exportFixturesCsv`
  - `api.importFixturesCsv`
  - `api.downloadFixtureTemplateCsv`

- model tab
  - `api.createModel`
  - `api.updateModel`
  - `api.deleteModel`
  - `api.exportModelsCsv`
  - `api.importModelsCsv`
  - `api.downloadModelTemplateCsv`

- station tab
  - `api.createStation`
  - `api.updateStation`
  - `api.deleteStation`
  - `api.exportStationsCsv`
  - `api.importStationsCsv`
  - `api.downloadStationTemplateCsv`

- customer tab
  - `api.createCustomer`
  - `api.updateCustomer`
  - `api.listCustomerUsers`
  - `api.listUsers`

- user tab
  - `api.createUser`
  - `api.updateUser`
  - `api.resetUserPassword`

### 權限行為

- `guest` 不可進這頁
- `user` 可維護 fixture / model / station
- customer / user / ledger / quality tab 實際上是 admin 能力
- 治具永久刪除只對 `admin` 顯示，前端以 `canManageUsers` 控制入口
- 後端仍以 `manage` 權限作為真正授權邊界，不能只依賴前端隱藏按鈕
- admin 也必須選到已透過 `user_customers` 指派的客戶，否則後端會拒絕

### 改資料維護頁時去哪裡

- 改 page tab orchestration、summary、CSV 流程、品質報表跳轉
  - `frontend/src/pages/MasterPage.vue`
  - 治具刪除 dialog 與刪除後 refresh 也在此檔
  - master responsive breakpoint 與手機 `list -> detail` 流程也在此檔

- 改列表、搜尋、分頁欄位
  - `frontend/src/components/master/MasterListPanel.vue`
  - 主資料清單的頁數提示 / 總筆數 / 翻頁動作目前在表格上方
  - 鍵盤列選取 / focus 樣式也在此檔

- 改 detail 編輯表單
  - `frontend/src/components/master/MasterDetailPanel.vue`
  - admin-only 永久刪除按鈕與危險區塊也在此檔

- 改帳目管理清單的頁數提示 / 總筆數 / 翻頁動作
  - `frontend/src/components/master/TransactionAccountListPanel.vue`
  - 後端篩選欄位：單號 / 操作人 / 治具 / 類型

- 改治具資料品質表、問題篩選、CSV 匯出、列內更新、問題類型跳轉規則
  - `frontend/src/components/master/FixtureQualityPanel.vue`
  - `frontend/src/pages/MasterPage.vue`

- 改治具刪除 API payload / response
  - `frontend/src/api/masterClient.ts`
  - `frontend/src/types.ts`（保留歷史時 `fixture_id` 可為 `null`）

## 產能頁

- page：`frontend/src/pages/ProductionPage.vue`
- 子元件：
  - `frontend/src/components/production/ProductionHeaderSection.vue`
  - `frontend/src/components/production/ProductionDetailSection.vue`
  - `frontend/src/components/production/ProductionCapacityPanel.vue`
  - `frontend/src/components/production/ProductionBatchImportModal.vue`
  - `frontend/src/components/production/ProductionRequirementCopyModal.vue`
- 支援 helper：
  - `frontend/src/utils/productionStations.ts`
  - `frontend/src/utils/productionCapacityPreview.ts`
  - `frontend/src/utils/productionCopy.ts`

### 目前責任分工

- `ProductionPage.vue`
  - 初始化資料載入
  - overview / configure route orchestration
  - `model_id` / `return_to` query sync
  - customer switch / route leave / browser unload unsaved-change guard
  - dirty-state 排除自動繼承的機種 / 站點 context，只追蹤使用者可儲存的站點、治具與數量欄位
  - 站點設定 / 治具需求 CRUD
  - CSV import / export
  - 批次匯入解析與缺資料補建
  - 治具需求建立時不要求使用者先手動建立 mapping；後端會自動補底層關係
  - 同機種站點／跨機種整組需求複製 orchestration，成功後切換到目標機種與站點
  - 可選站點收斂到目前機種已綁定站點
  - route-level back flow 與 `model_id` replace sync

- `ProductionHeaderSection.vue`
  - 頁首導覽、動態返回按鈕與 overview/configure 模式切換

- `ProductionDetailSection.vue`
  - 響應式 master-detail 工作區：左側站點、右側治具需求
  - mapping 清單整列選站後同步 requirement station
  - child editor 沿用目前機種 / 站點，不再重複輸入 context
  - guest 只顯示唯讀內容，不渲染新增、編輯、刪除或批次匯入操作

- `ProductionCapacityPanel.vue`
  - 站點總覽、station capacity 視覺化、瓶頸明細 drill-down
  - 尚未建立治具需求的 mapped station 仍保留在總覽並標示待配置

- `productionCapacityPreview.ts`
  - 依目前站點需求、庫存與表單草稿計算儲存後預估最大開站數 / 限制治具
  - 純函式，後端 capacity API 仍是儲存後的 authoritative result

- `ProductionBatchImportModal.vue`
  - 兩種 production 批次匯入 modal shell

- `ProductionRequirementCopyModal.vue`
  - 同機種站點複製與跨機種複製共用視窗
  - 顯示來源／目標、mapping 狀態、新增／衝突／更新／跳過預覽
  - 預設不覆蓋；使用者需明確勾選後才允許更新不同數量

- `productionCopy.ts`
  - 純函式計算複製預覽與安全衝突結果

- `productionStations.ts`
  - 依 `model_stations` 推導目前機種可用站點
  - 保證站點預設值與下拉來源不會落到未映射站點

### 主要功能

- 站點設定（底層仍為 model-station mapping）
- Fixture Requirement
- Station Capacity
- Model Query
- 同機種站點治具需求複製
- 跨機種治具需求複製與目標站點自動加入
- Mapping / Requirement CSV 匯入匯出
- Mapping / Requirement 批次貼上匯入 modal
- 相似資料確認與即時建立新 model / station / fixture
- 直接在 `治具需求` 新增資料時，若底層 model-station 關係尚未存在，後端會自動補建

### API 對應

- 初始化載入
  - `api.listModels`
  - `api.listStations`
  - `api.listFixtures`
  - `api.listModelStations`
  - `api.listFixtureRequirements`

- mapping
  - `api.createModelStation`
  - `api.updateModelStation`
  - `api.deleteModelStation`
  - `api.exportModelStationsCsv`
  - `api.importModelStationsCsv`
  - `api.downloadModelStationTemplateCsv`

- fixture requirement
  - `api.createFixtureRequirement`
  - `api.updateFixtureRequirement`
  - `api.deleteFixtureRequirement`
  - `api.exportFixtureRequirementsCsv`
  - `api.importFixtureRequirementsCsv`
  - `api.downloadFixtureRequirementTemplateCsv`

- capacity
  - `api.getStationCapacity`

- model query
  - `api.getModelQuery`

- 批次貼上匯入缺資料時建立新主檔
  - `api.createModel`
  - `api.createStation`
  - `api.createFixture`

### 改產能頁時去哪裡

- 改 route / tab orchestration、批次匯入解析、資料刷新
  - `frontend/src/pages/ProductionPage.vue`
  - overview/configure 模式、`return_to` back flow、以及 unsaved guard 也在這裡

- 改頁首與摘要
  - `frontend/src/components/production/ProductionHeaderSection.vue`

- 改 mapping / requirement / query 主要操作區
  - `frontend/src/components/production/ProductionDetailSection.vue`

- 改 capacity 視覺化
  - `frontend/src/components/production/ProductionCapacityPanel.vue`

- 改 batch modal frame
  - `frontend/src/components/production/ProductionBatchImportModal.vue`

## 前端常改支援檔

- `frontend/src/types.ts`
  - 欄位不一致時先看這裡

- `frontend/src/appState.ts`
  - customer 切換、登入 session、onboarding 共享狀態
  - sessionStorage 還原
  - customer switch guard registry
  - `requestInventoryBatchOpen()` shortcut

- `frontend/src/onboarding.ts`
  - 導覽 flow 定義與跨頁流程
  - 目前共有六張教學卡：`查詢工作台`、`批次收 / 退料 & 收退料總檢視`、`治具 / 機種 / 站點主資料`、`產能設定與治具需求`、`全系統按鈕與操作說明`、`收退料帳目管理 / 治具資料品質`

- `frontend/src/components/common/OnboardingFlowPicker.vue`
  - 教學分類選單

- `frontend/src/toastState.ts`
  - 成功 / 失敗提示

- `frontend/src/styles.css`
  - 共用 CSS utility
  - 新元件優先吃這裡的按鈕、panel、modal、table、chip 樣式

- `frontend/src/utils/apiError.ts`
  - 後端 error payload 轉可讀訊息

- `frontend/src/utils/date.ts`
  - 本地日期判斷

- `frontend/src/utils/display.ts`
  - fallback 與狀態文字映射

- `frontend/src/utils/identifier.ts`
  - 前端 `identifier` 正規化 / 查詢 helper

- `frontend/src/utils/identifier.test.ts`
  - 前端 `identifier` helper 單元測試

## 現況提醒

- audit API 仍保留在 `api.listAuditLogs`，但首頁沒有 audit 摘要區塊。
- shell 目前沒有 desktop compact / mini sidebar。
- 搜尋頁主結果已改為 `page_size` 邊界 + `load more`；fixture / model context 不再首屏全量預載。
- 搜尋頁目前仍沒有可收合的篩選區。
- 教學模式屬於前端 sandbox 流程，不會呼叫額外的 backend tutorial API。
- 如果要改前端 `identifier` 規則，優先改 `frontend/src/utils/identifier.ts` 與 `frontend/src/utils/identifier.test.ts`，不要回到元件內重寫 `padStart(4)`。

## 不要改的前端檔案

- `frontend/src/*.js`
- `frontend/src/**/*.js`
- `frontend/src/*.js.map`
- `frontend/src/**/*.js.map`
- `frontend/tsconfig.*.tsbuildinfo`
- `frontend/dist`
- `__pycache__`
