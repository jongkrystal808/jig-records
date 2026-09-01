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
  - 所有大型 feature page 使用動態 import；只有進入對應路徑時才下載該頁 chunk
  - `/login` 使用輕量 `LoginRoutePage.vue`，實際登入畫面仍由 App shell 的 `AppAuthScreen.vue` 負責
  - `/search` -> Workspace UI 的三欄快速作業首頁
  - 登入後由 `App.vue` 的全域 `HomeUiSurfaceSwitcher.vue` 一次切換整個系統：
    - `Form UI` -> `FormSystemSurface.vue` 依目前 route 映射至 `FormUiSurface.vue` 工作區
    - `Workspace UI` -> `WorkspaceSystemSurface.vue`；全程使用 Modern 頂部欄，`/search`、`/inventory` 使用無重複版頭的 `WorkbenchUiSurface.vue` 快速作業，第四個分頁直接進入仍歸屬現場工作台的 `/inventory/overview` transaction-only 總檢視；資料維護與產能 route 承接完整維護頁面
      - 固定表頭／客戶／條件區／結果表格位置；`FormWorkspaceSwitcher.vue` 由各工作區插入條件區與表格之間，所有尺寸都直接顯示完整文字，並分為「日常作業／設定維護／系統管理」三組；窄版可橫向捲動
      - `篩選報表` -> heading-less `InventoryRelationsPage.vue`
      - `收退料匯入` -> report-styled `BatchImportPanel.vue`（super_admin / admin / user）；收／退料、單號、治具、來源、datecode／編號、數量與備註均直接在資料列編輯，功能索引位於表格上方
      - `收退料總檢視` -> `FormReportOperations.vue` 分派至 `FormTransactionOperations.vue`（所有角色）
      - `產能` -> `FormReportOperations.vue` 分派至 `FormProductionOperations.vue` requirement / mapping grid（super_admin / admin / user）
      - `資料維護` -> `FormReportOperations.vue` 分派至 `FormMasterDataOperations.vue`（super_admin / admin / user；customer / user 維護僅 super_admin）
      - `收退料帳目管理` -> `FormAdminReports.vue` ledger grid、案件詳細、重算與撤回（super_admin / admin）
      - `治具資料品質` -> `FormAdminReports.vue` quality filter、異常表格與列內修復（super_admin / admin）
      - `圖片維護` -> `FormImageMaintenance.vue` 圖片狀態篩選、預覽、單張替換與依治具編號檔名批次上傳（super_admin / admin / user）
      - 各 Form UI 模組結果工具列皆提供 `匯出篩選結果`；收退料／帳目、主資料、產能與圖片清單都以單一 backend filter export 請求下載完整結果，不由瀏覽器逐頁抓取。共用 `utils/exportFeedback.ts` 統一顯示 `已匯出 N 筆：檔名`、空結果警告，並在請求期間維持 loading／禁止重複點擊
      - 收退料總檢視與帳目管理不傳匯出筆數上限，直接下載後端完整串流的篩選結果 CSV
      - Form UI 在工作區模組或其產能／資料維護子頁路由切換後，由 router `scrollBehavior` 依目前介面狀態直接定位至目前模組／篩選條件頂端；判斷不依賴切換中的 DOM，也不沿用上一個模組的瀏覽器捲動位置。Modern UI 與非模組切換的既有位置仍保留
      - Form UI 各篩選模組按下 `套用條件` 後，由 `scrollReportResults.ts` 將結果工具列與表頭平滑定位至視窗中上方；使用者偏好減少動態效果時改為立即定位
    - 所有角色預設 Workspace UI；super_admin / admin / user 可在全域 compact 介面切換器選擇個人的登入預設為 Workspace UI 或 Form UI，偏好以帳號隔離存於瀏覽器；既有 Modern／工作台偏好會自動遷移為 Workspace
  - `/search/detail` -> `SearchWorkspacePage.vue`
  - `/inventory/filter-view`、`/inventory/relations` -> redirect `/search`
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
- `/master/images` -> `MasterPage.vue`（Modern UI 顯示治具維護；Form UI 映射圖片維護工作區）
- `/production` -> `ProductionPage.vue`
- `/production/mapping` -> `ProductionPage.vue`
- `/production/requirements` -> `ProductionPage.vue`
- `/storage` -> `StoragePage.vue`（所有介面共用的治具收納與位置索引；guest 唯讀）
- `/production` 目前是總覽模式；`/production/mapping` 與 `/production/requirements` 目前都進同一個 `產能設定` 工作區
- guest 進 `/master` 會被導回 `/search`

- `frontend/src/App.vue`
  - 全域 shell 協調器
  - 只保留 session、route、onboarding、topbar stats refresh、global modal open state
  - 從 `sessionStorage` 還原 session / current customer
  - 擁有全域 Workspace / Form UI 狀態與個人預設值；未儲存內容由 `unsavedChangesGuard.ts` 統一攔截客戶切換、介面切換、route、登出及 `beforeunload`
  - customer switch confirm 與全域 batch shortcut request 協調
  - 今日收料 / 今日退料 / 低水位 / 最近收退料資料改由 backend dashboard summary API 載入
  - 不再直接承接整塊登入頁、topbar、drawer、toast template
  - 協調 onboarding 分類選單與 guided tour 播放
  - 登出會清除 session 後以 `router.replace` 導回 `/login`，不保留原本受保護頁面的 URL
  - token 過期事件會導回 `/login`；重新登入後消耗 transport 保存的原始 full path 並返回原頁
  - 掛載全域 `SystemConfirmDialog.vue`，承接所有需要確認的跨頁／危險操作

- `frontend/src/components/app/AppAuthScreen.vue`
  - 登入畫面
  - 訪客入口

- `frontend/src/components/app/AppTopbar.vue`
  - 頂部導覽列
  - customer picker
  - 今日收料 / 退料 / 低水位摘要
  - 上述統計與最近收 / 退料資料改由 backend dashboard summary API 提供
  - 寬螢幕 topbar 維持單列且不把更多／登出換到第二排；`1600px` 以下使用 compact header，保留選單、目前客戶與收／退料快捷鍵，低頻操作仍進 drawer
  - Workspace 的「更多」與手機 drawer 不重複列出收／退料總檢視；該入口統一由快速作業第四分頁提供
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
  - 全域匯出 modal
  - 兩者共用 `UiModalShell.vue` 的 dialog 語意、focus trap、Esc、背景 inert 與焦點還原

- `frontend/src/components/common/UiModalShell.vue`
  - 共用 modal accessibility shell
  - 支援 `dialog`／`alertdialog`、modal stack、初始焦點、Tab 循環、Esc、背景 inert 與 return focus
  - `SystemConfirmDialog.vue`、`AppGlobalModals.vue`、`OnboardingFlowPicker.vue`、`GuidedTour.vue`、`AppReleaseNoticeModal.vue`、production modal，以及獨立的 Master 品質快速修正／永久刪除元件共用
  - 全域 `匯出中心` modal
  - batch modal close / overview handoff 的事件轉發

- `frontend/src/components/app/AppReleaseNoticeModal.vue`
  - 版本公告 modal

- `frontend/src/components/app/AppToastStack.vue`
  - 全域 toast 顯示
  - 關閉按鈕具備 `aria-label="關閉通知"`

- `frontend/src/confirmState.ts`
  - Promise-based 全域確認狀態與 resolve 協調
  - 新確認會安全取消尚未完成的舊確認

- `frontend/src/components/common/SystemConfirmDialog.vue`
  - 統一取代原生 `window.confirm`
  - 支援一般／危險語意、Esc、背景取消、焦點進入及 Tab focus trap

- `frontend/src/appState.ts`
  - 全域登入 session
  - customer 選擇
  - onboarding 狀態
  - onboarding 分類選擇狀態
  - customer switch guard registry
  - 全域 batch modal shortcut request

- `frontend/src/components/production/ProductionDetailSection.vue`
  - 機種／站點／治具需求編輯器的指定模式開關
  - 依所選治具列出正庫存 identifier，顯示可用數量並支援多選

- `frontend/src/onboarding.ts`
  - 新手導覽 flow 定義
  - 依 Modern UI / Form UI / 工作台 UI surface 與頁面 / tab 分類的教學內容
  - 每一步對應 route / `data-tour` target / 文案 / 方向
  - Workspace 依目前 route 重用快速作業或完整維護教學；guest 只看到符合唯讀權限的流程。Form 完整詳細版會逐一標示每個工作區按鈕，再切到對應 route 顯示到達頁；Admin 專屬步驟只對 Admin 播放

- `frontend/src/components/common/OnboardingFlowPicker.vue`
  - 只顯示目前教學入口所屬 UI 的新手教學分類
  - 完整詳細版固定置頂為推薦入口，精簡教學另列於下方

- `frontend/src/releaseNotice.ts`
  - 版本公告內容
  - `versionId` / 顯示標題 / 摘要 / highlight 文案
  - 目前公告版本為 `2026-08-24`，涵蓋 Form 全系統介面、後端分頁／正式匯出與產能貼上預覽

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
  - authenticated `401` 統一清 session、單次提示並發出 session-expired 導頁事件

- `frontend/src/sessionExpiry.ts`
  - 保存／驗證／消耗 token 過期前的內部 return path
  - 共用 session-expired 事件名稱與提示文案

- `frontend/src/api/authClient.ts`
  - auth / user 相關 API
  - user update 可帶 `allowed_customer_ids` 調整客戶範圍；Modern 一般編輯與啟停會送回既有值，避免非權限欄位操作清空指派

- `frontend/src/api/masterClient.ts`
  - fixture / model / station / customer 相關 API

- `frontend/src/api/inventoryClient.ts`
  - stock / alert / receipt / return / transaction / export 相關 API

- `frontend/src/api/productionClient.ts`
- `frontend/src/api/storageClient.ts`
  - 收納處、位置編號整理、治具位置／數量分配 API
  - model-station / fixture requirement / capacity / model query

- `frontend/src/api/searchClient.ts`
  - global search

- `frontend/src/api/auditClient.ts`
  - audit log

- `frontend/src/api/mediaClient.ts`
  - customer-scoped fixture image URL、blob fetch、單張與批次上傳

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
  - 本地日期 key / 顯示輔助；所有 user-facing 日期固定輸出 `YYYY-MM-DD`，來源即使包含 timestamp 也不顯示時分秒

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

- 查詢首頁版本公告
  - `SearchHeroSection.vue` 負責預設收合的明確展開按鈕
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
  - `frontend/src/components/search/SearchHeroSection.vue`
  - `frontend/src/releaseNotice.ts`

- 改全域 toast UI
  - `frontend/src/components/app/AppToastStack.vue`
  - 狀態邏輯在 `frontend/src/toastState.ts`

## Workspace／Form 全系統介面

- 系統殼層：`frontend/src/App.vue`
- 所有角色都可用置於頂部導覽列正中央的全域 `HomeUiSurfaceSwitcher.vue` 切換；切換同時套用查詢、收退料、產能、主檔、帳目、品質與圖片維護：
  - Workspace UI：`WorkspaceSystemSurface.vue` 以 Modern 頂部欄承載混合流程；快速作業 route async 載入 `WorkbenchUiSurface.vue` 並關閉其內嵌版頭，收／退料總檢視雖由 transaction-only `WorkbenchManagementSurface.vue` 承載三欄結果與篩選，但路由、區域語意及教學皆歸屬現場工作台；資料與產能 route 使用完整維護頁面，互動產生的 query 會持續保存 `ui_surface=workspace`
  - Form UI：`FormSystemSurface.vue` 將目前 route 映射至 `FormUiSurface.vue`，後者以 `styles/surfaces/form.css` 固定頁面表頭、客戶、條件區及結果表格位置；`FormWorkspaceSwitcher.vue` 統一插在條件區與 table 之間，以完整文字分組呈現「日常作業／設定維護／系統管理」
  - Workspace 快速作業以 `WorkbenchUiSurface.vue` 與 `styles/surfaces/workbench.css` 實作；PC／Notebook 固定為左側輸入／中間結果／右側圖片與關聯資訊，Tablet 改為左側操作＋中間結果雙欄，詳情置於下方。四個分頁為收料／退料、查詢治具、查詢機種、收／退料總檢視；最後一頁直接導向 Workspace 的工作台版總檢視。治具或機種查詢完成後，右側展示欄只對 `admin`／`super_admin` 顯示筆型 Edit 入口，原地展開與資料維護相同的可編輯欄位；儲存後同步刷新目前查詢、庫存／產能摘要及 route 狀態，草稿則納入共用未儲存內容保護
  - Workspace 搜尋把模組、搜尋子模式、關鍵字、頁碼、選取結果及詳細分頁寫入 route query；使用者送出搜尋、切換模組或選取結果時建立 history entry，瀏覽器上一頁／下一頁會重跑並還原相應狀態
  - Workspace 頂部工具列提供 `Workspace UI 教學` 入口；快速作業 route 顯示三欄操作教學，完整維護 route 顯示對應頁面教學
  - 工作台單筆收料與退料已合併成同一個 `收料／退料` tab，表單內用方向切換保留目前輸入；正式 identifier 正規化、重複單號確認與後端權限不變。`WorkbenchBatchOperations.vue` 在中間結果欄提供工作台專用的批次標題、三步驟提示與尺寸邊界，再掛載共享 `BatchImportPanel.vue` 的解析、例外預覽與送出流程；同一資料方格可混合收料／退料並帶入目前治具。批次方格使用中間欄緊湊欄寬、受控垂直高度、水平捲動與 sticky 送出工具列。治具查詢結果保存正式 `related_models / station_rows`，機種結果保存 `query.fixtures`；在治具與機種分頁互切時，左欄會建立可關閉的關聯搜尋建議並列出可直接查詢的目標，不以代碼相似度猜測關聯。機種產能仍依正式 `model + station` 計算，將最低開站數排在第一列並標示目前瓶頸站點及治具
  - 工作台的收退料總檢視、產能設定、資料維護（含圖片）、Admin 收退料帳目管理與 Admin 治具資料品質 route 使用 `WorkbenchManagementSurface.vue`。日常工作台的管理分頁為上述 route 與匯出中心的角色感知入口：guest 只保留收退料總檢視與角色可用匯出，user 增加產能／主資料，admin 顯示全部五個模組。管理殼層固定採左側模組導覽、中間結果、右側篩選／編輯工具；原本右側的角色、範圍與靜態提示已移除。收退料總檢視及各維護模組的篩選移至右欄，產能與主資料新增／編輯、品質儲位／水位修正也只在右欄展開。圖片維護的中間清單會自動選取第一筆並縮成四個必要欄位，右欄依選取治具顯示圖片預覽、單張替換及批次上傳。帳目管理的中間面板只顯示完整案件清單，選取案件的摘要、明細、重算與撤回全部放入右欄。帳目與品質由 `WorkbenchAdminOperations.vue` 提供工作台專用結果，並重用既有 composable、API 及應用程式確認流程；不渲染 `FormAdminReports.vue`。1024 以上維持三欄且訪客導航縮窄；長備註預設省略並可點擊展開。guest 只顯示可讀的收退料總檢視，user 不能直接進入 Admin 帳目／品質 route
  - 工作台管理右側標題提供「收合篩選／展開篩選」，只隱藏條件欄位並保留篩選標題、套用／清除與後續詳細／編輯工具。共用 `UiMultiSelect.vue` 的下拉選項以純文字呈現，已選項使用文字與淡色背景區分；隱藏的原生 checkbox 仍保留鍵盤及無障礙操作。
  - `playwright.config.ts` 與 `tests/visual/workbench.visual.spec.ts` 使用確定性 API mock，在 1024×900、1366×900、1920×1080 三個 project 比對 Workbench 合併收退料、純 Datecode／序號查詢、管理三欄、圖片維護、帳目管理及帳目收合狀態截圖，檢查面板順序、結果欄寬、右側工具可用寬度及整頁不得水平溢位；`npm run test:visual` 驗證 baseline，`npm run test:visual:update` 只在人工批准新版面時更新
  - Form UI 不渲染 application topbar；精簡版頭的 H1 與說明文字會依目前工作區動態顯示。Workspace UI 使用完整 topbar，並提供自己的 Workspace UI 教學入口
  - Form UI 所有篩選條件區的重新整理、重設、清除與套用按鈕使用和報表工具列一致的扁平純色／細框樣式，不使用漸層、浮起陰影或大圓角
  - Workspace 與 Form 共用 `UiMultiSelect.vue`：作業類型、來源、治具狀態、水位、配置狀態、品質問題、圖片狀態等可組合條件可複選；同一分類內採 OR、不同分類間採 AND
  - `FormReportOperations.vue` 只負責依 route 工作區分派領域元件與轉送 view 事件；Form 與 Workspace 完整維護編輯器共同使用 `utils/formOperations.ts` 的驗證規則
  - 報表的治具列在 super_admin / admin / user 角色下提供 `FixtureReportRowActions.vue` 更多操作：快速收料／退料送入全域批次列；編輯治具與查看產能會切到 Workspace 完整維護頁並聚焦原資料
  - Form UI 定位為快速操作介面；工具列與資料列的「前往完整維護」會切換至 Workspace UI 並盡可能保留 entity id
  - 三個 Form 領域元件以相同 filter-panel / report-section 骨架呈現收退料明細、產能需求／mapping、治具／機種／站點／客戶／使用者；治具、機種、站點與產能 read model 使用後端 50／100 筆分頁，切換主資料類型時只載入目前資料集。產能進頁只讀目前結果頁，不預抓三份 master options；`FormRemoteAutocomplete.vue` 在聚焦／輸入後以 debounce 呼叫後端搜尋，每次最多呈現 20 筆機種／站點／治具，並忽略過期回應。產能工具列的 `FormProductionPasteImport.vue` 在機種站點表接受 `model_code + station_code` 兩欄貼上，在治具需求表接受 `model_code + station_code + fixture_code + required_qty` 四欄貼上。送出前呼叫後端差異預覽，分類新增／相同／待取代／錯誤並並列既有與匯入需求量；只有使用者在應用程式確認框明確選擇「直接取代」才更新差異數量，未貼上的其他綁定不刪除；使用者維護列直接使用分頁 user response 的授權客戶摘要顯示名稱，新增與編輯時 `FormUserCustomerScopePicker.vue` 才以 50 筆後端搜尋頁載入選項，可逐筆勾選、全選搜尋結果、移除或清除多個 `allowed_customer_ids`，並顯示已選數量且至少須選一個客戶；`FormAdminReports.vue` 以相同骨架承接 admin 帳目管理與治具資料品質，帳目清單／案件詳細及品質摘要／異常清單均使用 Form UI 的扁平藍色表頭、分隔線與列式欄位；`FormImageMaintenance.vue` 將既有治具圖片上傳入口納入相同骨架，圖片狀態清單使用後端 50／100 筆分頁，並提供預覽、單張替換與依治具編號檔名批次上傳；Form 結果表以頁面作垂直捲動，只保留表格水平溢位，避免雙層垂直捲軸；新增與編輯直接在 table row 內切換成輸入欄位
- 逐治具計算欄統一稱為「此治具可支援站數」，完整站點產能仍取同一 `model + station` 全部治具結果的最小值；分頁刪除或帳目撤回目前頁最後一筆時，會先退回前一頁再重新載入
- `InventoryRelationsPage.vue` 在 Form frame 內隱藏重複 heading 並保持掛載，因此原報表條件與頁碼可保留；匯入草稿也保持掛載。guest 只可使用報表與唯讀收退料總檢視
  - Form UI 啟用時，全域選單與工作區索引都導向原本的 `/inventory`、`/production`、`/master` routes；route path 仍可作書籤，Form 殼層只改呈現方式
- Workspace 與 Form 各自具有容器與樣式邊界；Modern／工作台不再是可選 system surface
- 所有角色首次進入預設 Workspace UI
- super_admin / admin / user 可把目前 surface 設為個人登入後預設，依 `authSession.user.id` 保存於 `localStorage`
- `ui_surface=workspace|form` 保存明確介面；舊的 `modern`／`workbench` 值會遷移至 Workspace，既有 `home_mode=query|report` 仍可讀取
- Form 列內編輯與 Modern 編輯器都登記至 `unsavedChangesGuard.ts`；客戶切換、介面切換、route、登出會使用應用程式確認框，重新整理或關閉分頁使用瀏覽器 `beforeunload` 警告
- `SearchWorkspacePage.vue` 以 `report-context-change` 回報查詢類型、可見輸入、已執行文字與選中 ID；`appState.ts` 保存這份狀態，`App.vue` 在 system surfaces 間轉換 route query；切入工作台時以 `workbench_mode=fixture` 接續搜尋入口
- 查詢結果切到報表時，選中治具映射為 `fixture`、選中機種映射為 `model`；若可見輸入已修改但尚未重新搜尋，則映射為報表 `q`，避免沿用舊選取
- 切回查詢時以 `mode / q / query_draft / selected_id` 還原輸入框、已執行查詢及選取
- 模式狀態轉換規則：`frontend/src/utils/searchHomeModeState.ts`

## 庫存配置報表

- page：`frontend/src/pages/InventoryRelationsPage.vue`
- route：`/search` 的報表模式
- 報表頁不再內嵌 `InventorySheetInputMockup`；正式收退料操作仍走全域批次作業與 `/inventory`，此頁只保留收退料篩選、明細及匯出

### 目前責任分工

- `InventoryRelationsPage.vue` 保留報表／options API 請求與跨區狀態協調；`useConfigurationReportState.ts` 負責 route query、draft／applied filters、分頁 query 與完整結果匯出
- `InventoryReportFilters.vue` 負責條件表單、條件 chips 與產能結果呈現
- `InventoryReportResults.vue` 負責結果摘要、欄位選擇、桌面表格、手機卡片與分頁呈現
- `FixtureImageDialog.vue` 負責 customer-scoped 圖片 blob 載入、競態取消、object URL 清理，並沿用 `UiModalShell` 的鍵盤／焦點行為
- 以目前 `selectedCustomerId` 呼叫 `GET /inventory/configuration-report`，桌面只載入目前 50／100 筆、手機只載入 20／50 筆 server page 與後端統計
- 客戶只由共用頂欄 `AppTopbar.vue` 選擇；報表篩選區不再放第二個客戶下拉
- 治具、機種、站點都是一般聯動篩選器，空值分別代表全部治具、全部機種、全部站點；不提供另一組主檢視按鈕或「無」選項
- 報表固定使用關聯明細語意；同一治具有多個 model/station requirement 時會依配置列重複呈現
- 報表篩選：治具狀態（預設已啟用，可複選已停用）、關鍵字、治具、機種、站點、水位狀態（可複選）、儲位、配置狀態（可複選）、收退料方向、交易來源（可複選）與日期；聯動治具／機種／站點因產能上下文必須明確而維持單選
- 篩選依實際選擇順序聯動；第一個非空欄位優先，後續 select options 由先前條件縮限；完整順位以可移除 chips 呈現
- 高優先條件變更時，只清掉已不相容的下游 select，不反向改動第一條件
- draft 與 applied 條件分開呈現；有差異時顯示「有 N 個條件尚未套用」，表格仍標示上一輪已套用條件
- `套用條件` 後才更新表格與 URL；最大開站數只讀取 applied 機種／站點，任何新 draft 或無效日期都會清除舊產能結果
- route query 同步：`customer / q / fixture_status / fixture / model / station / water / storage / configuration / transaction_activity / transaction_ownership / transaction_date_from / transaction_date_to / priority / page / page_size`
- 桌面使用密集型 table、sticky header 與斑馬紋；桌面分頁支援每頁 50／100，手機預設 20 並提供 20／50，兩者都有上一頁／下一頁與直接跳頁
- 手機初次進入預設收合完整條件，只保留關鍵字、`更多條件` 與結果摘要；低水位、未配置、今日收料／退料一鍵卡已取消
- 手機結果改用治具摘要卡片，直接呈現庫存、機種、站點、需求、可開站與儲位，不依賴桌面寬表水平捲動
- 手機結果摘要與已套用條件固定在 topbar 下方；長摘要與條件 chips 以單列橫向滑動維持緊湊高度
- 手機卡片、欄位顯示與當頁收退料明細已抽到 `frontend/src/components/inventory/InventoryReportMobileCards.vue`
- 表格預設全欄顯示；欄位選擇器提供 `現場庫存`（總庫存、客供、自購、水位）、`配置檢查`（機種、站點、需求、可開站）及 `完整報表` 三組快速預設
- 預設套用後仍可用兩欄淡藍選項卡（手機為單欄）逐欄顯示／隱藏；至少保留一欄，偏好保存在 `localStorage`
- 欄位定義與預設集中在 `frontend/src/utils/reportColumnPresets.ts`
- page response 的 `populated_columns` 由後端依完整篩選結果計算；桌面、手機與匯出都透過 `frontend/src/utils/reportVisibleColumns.ts` 與使用者欄位偏好取交集，自動隱藏整欄無資料的欄位
- 欄位選擇器仍保存原始勾選偏好；目前被自動隱藏的欄位標示「無資料」，條件改變且重新有值時會自動恢復
- `匯出篩選結果` 由後端輸出 CSV 或 XLSX；涵蓋所有符合目前篩選的資料、不受當頁限制，但只包含目前可見欄位；完成提示含筆數、欄位數與檔名
- `計算最大開站數` 使用 `api.getModelQuery`：站點空值列出全部 mapped stations，指定站點只回單站；摘要點擊後以密集表格展開該站治具需求、庫存、可開站、狀態與瓶頸標示
- capacity 卡片預設收起瓶頸治具，以 `expandedBottleneckStationIds` 逐站控制展開
- 收退料篩選支援今日收／退、指定日期收／退與客供／自購來源；指定日期欄只在 range mode 啟用，缺值或反向區間會停用查詢並顯示 inline error；所有條件由 configuration-report API 在資料庫套用
- 收退料模式與日期 query 組裝：`frontend/src/utils/reportTransactionFilters.ts`
- 勾選「展示收／退料明細」後，API 只回傳當頁治具的符合明細；同一治具當頁首次出現處展開類型、來源、日期、單號、datecode／編號與數量
- 勾選明細後的後端匯出會附加六個交易欄位，涵蓋完整篩選結果且不因治具的多筆配置列重複交易；前端明細分組位於 `frontend/src/utils/reportTransactionDetails.ts`
- 治具代碼是圖片預覽按鈕，使用 `fetchFixtureImageObjectUrl` 載入 blob，對話框支援 loading / missing / Escape / backdrop close / focus trap / return focus
- 結果工具列下方顯示 applied filter chips 與尚未套用提示；手機初次進入及套用後自動收合 filter grid
- draft／applied 差異計數集中在 `frontend/src/utils/reportFilterState.ts`
- 以水位狀態呈現正常 / 低水位 / 缺料，以配置狀態呈現已配置 / 未配置 / 未綁定
- 報表本身維持唯讀，不顯示編輯與收退料動作
- 客戶切換時重新取得全部關聯資料

### 資料來源

- `api.listFixtures` / `api.listModels` / `api.listStations`
- `api.listModelStations` / `api.listFixtureRequirements`
- `api.listStock` / `api.listIdentifierStockSummary`
- `fetchFixtureImageObjectUrl`

### 關鍵規則

- 每筆 fixture requirement 形成一筆正式配置列。
- 沒有 requirement 的治具保留為 `未綁定` 列；已有 model-station 但沒有治具需求時保留為 `未配置` 列。
- 水位與儲位都由 fixture / stock 正式資料產生，不使用展示假值。

## 治具 / 機種詳細查詢

- route：日常入口為 `/search` 的查詢模式；`/search/detail` 保留相容入口
- `/search/detail` 用於舊連結、新手教學與既有跨頁返回流程，不再於 `更多功能` 重複列出

- page：`frontend/src/pages/SearchWorkspacePage.vue`
- 子元件：
  - `frontend/src/components/search/SearchHeroSection.vue`
  - `frontend/src/components/search/FixtureOverviewPanel.vue`
  - `frontend/src/components/search/SearchResultPanel.vue`
  - `frontend/src/components/search/FixtureInfoPanel.vue`
  - `frontend/src/components/search/ModelInfoPanel.vue`
  - `frontend/src/components/search/FixtureEditForm.vue`
  - `frontend/src/components/search/ModelEditForm.vue`

### 目前責任分工

- `SearchWorkspacePage.vue`
  - mode / query state
  - 空白查詢時的分頁式治具總覽 state；選取總覽列後交回既有治具詳細查詢
  - route query handoff (`mode` / `q` / `page` / `selected_id` / `detail`)
  - paginated global search state
  - load more / selected result state
    - 最近收 / 退料治具快捷入口資料整理
  - fixture / model result 組裝與排序承接
  - fixture / model context lazy fetch
  - in-context edit dirty state / route leave / browser unload / customer switch guard
  - fixture detail -> inventory overview / batch modal handoff
    - overview handoff 只帶 `fixture_code` 與指回 `/search/detail` 的 `return_to`
  - 開啟 onboarding 分類選單
  - 搜尋結果自動 scroll 進第一屏
  - idle hero 不再使用固定 viewport-height 垂直置中

- `SearchHeroSection.vue`
  - 查詢首頁 hero shell
  - mode switch
  - smart hints
  - smart hints 收合 / 展開
  - 最近收 / 退料治具快捷入口
  - 手機版更新公告預設收合；近期治具維持單列橫向滑動，初始顯示 5 筆與 `展開全部（N）`，展開後顯示最多 20 筆與 `收合為 5 筆`
  - onboarding 入口
  - 明確 `搜尋` CTA
  - 查詢後自動收合近期治具
  - 搜尋欄 / mode switch 無障礙語意

- `FixtureOverviewPanel.vue`
  - Modern UI 空白查詢的預設簡略治具總清單；與 `SearchHeroSection.vue` 共用 `SearchWorkspacePage.vue` 的單一查詢工作區外框，只以內部分隔線區分查詢控制與總清單
  - 桌面表格顯示編號、名稱、庫存、庫存狀態、儲位與啟用狀態；`680px` 以下改為整卡可點擊的 compact cards，只保留編號、名稱、庫存、狀態與儲位，無須橫向捲動即可進入治具詳細查詢
  - 桌面與手機都支援載入更多

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

- 無查詢條件時預設顯示客戶範圍內的簡略治具總清單，查詢控制與總清單呈現在同一張工作區卡片中
- 雙模式查詢：`治具` / `機種`
- 治具模式內再分成 `治具資料` 與 `Datecode／序號`：前者只查治具編號、名稱與儲位，後者只以完整 identifier 精確定位關聯治具並顯示含圖片的總覽與該編號收退料記錄，兩種結果不互相覆蓋
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
  - 讀取 helper 必須同時傳入目前 `customerId`
  - `GET /api/v2/master/fixtures/{fixture_code}/image?customer_id=...`

### 改詳細查詢頁時去哪裡

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
  - `InventoryBatchEntryGrid.vue`：收／退料、單號、治具 autocomplete、來源、datecode／編號、數量與備註的固定欄位方格
  - 快速新增與大量貼上共用方格；可逐格輸入、新增／刪除列，或從 Excel／其他表格貼上多列多欄
  - `utils/inventoryBatchClipboard.ts`：辨識標準三／四欄、第一欄合併「治具編號-datecode」的兩欄表格、Markdown pipe 表格、舊直式配對，以及依標題抽取治具編號、date code／流水碼、不良數量與不良現象（映射備註）的寬表格
  - 收／退料、單號與來源欄皆提供「全部套用」勾選框；勾選時跨列同步，取消後可逐列編輯，不同 `收／退料 + 單號` 會拆成不同交易送出
  - 備註按列儲存；方格內容序列化為批次草稿並沿用既有預覽、退料預檢與 receipts／returns API
  - 重複交易確認提示
  - `transaction_no` 在前端與 backend contract 都維持必填，不使用 backend 自動補號
  - 歷史交易若缺 `transaction_no`，清單 / 詳細 / 搜尋預覽 / 總檢視統一顯示 `（無單號）`
  - 每列 `來源` 選擇（`客供` 預設 / `自購`）與選填備註
  - 從治具入口預填時，方格空白列自動帶入該治具
  - 新治具建立
  - 相似治具確認 / 替換
  - 依 datecode 總量顯示 `目前庫存` / `交易後庫存` 預覽
  - `useInventoryBatchParser.ts`：貼上格式解析、治具比對與退料 identifier 庫存預檢
  - `useInventoryBatchPreviewState.ts`：ready／exception 分組、重複列合併與交易後庫存預覽
  - `useInventoryBatchSubmit.ts`：依收／退料及單號分組送出、409 重複單號確認與送出生命週期
  - `來源` 用於交易分類；退料預檢不額外增加來源限制
  - 同批重複 `治具 + datecode/編號` 的逐列累計庫存預覽
  - submit 前相同 `fixture + identifier + 來源 + 備註` ready 列合併
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
  - `frontend/src/components/master/MasterToolbar.vue`
  - `frontend/src/components/master/MasterListPanel.vue`
  - `frontend/src/components/master/MasterDetailPanel.vue`
  - `frontend/src/components/master/MasterReadonlySummary.vue`
  - `frontend/src/components/master/FixtureQualityPanel.vue`

### 目前責任分工

- `MasterPage.vue`
  - route-driven tab state
  - 初始化載入
  - editor mode、import / export 與跨區導覽協調
  - import / export / template download
  - summary metrics
  - customer scope 與 quality／ledger／production 的跨區導覽
  - `useMasterCrudActions.ts` 負責新增、更新與啟停 API 協調
  - `useMasterEntityDeletion.ts` 負責永久刪除、最後一筆退頁、重載與訊息；`MasterPermanentDeleteModal.vue` 負責 dialog 呈現
  - `FixtureQualityQuickEditModal.vue` 負責品質快速修正 dialog 呈現，狀態與 API 仍由 `useMasterQuality.ts` 管理
  - 初次載入不選第一筆；清單選取後先進 `summary`，明確按「編輯」才同步 form 並進 `edit`
  - `summary / edit / create` 模式與未儲存 guard
  - `1100px` 以上維持 list/detail 雙欄
  - 手機版 `清單 -> 明細` 流程切換
  - 手機 KPI 單列 compact chips、分組功能下拉選單與「更多操作」低頻工具收納
  - 手機明細模式隱藏 KPI／批次工具，只保留返回、目前項目與適用的編輯入口

- `MasterToolbar.vue`
  - 手機分組功能選單、桌面 tab、`更多操作` 與匯入／圖片 file input lifecycle
  - 只透過事件要求頁面切換 route、匯入、匯出、下載範本或啟動導覽

- `useMasterLedger.ts`
  - admin ledger server-side paging、篩選、選取、重算與沖銷確認流程
  - quality `stock_mismatch` 導覽後的治具篩選聚焦

- `useMasterQuality.ts`
  - admin 治具資料品質報表、問題篩選與 quick editor state
  - 列內更新 `儲位 / 最低水位`、機種關聯跳轉與 customer-scoped 圖片上傳／預覽
  - 共用品質表格只呈現 `治具編號 / 儲位 / 最低水位 / 機種關聯 / 圖片` 五欄；Form、Workbench 與品質 CSV 採用相同欄位集合

- `MasterListPanel.vue`
  - tab 清單
  - 搜尋 / 篩選
  - 分頁列表
  - 頁數提示 / 總筆數 / 翻頁動作固定在表格上方
  - row focus / `Enter` / `Space` keyboard interaction

- `MasterDetailPanel.vue`
  - fixture / model / station / customer / user 的 summary / detail form shell
  - `admin` / `super_admin` 主資料永久刪除入口（治具 / 機種 / 站點）
  - 透過 props 呼叫 `MasterPage.vue` 綁定的 `useMasterEntityDeletion.ts` action

- `MasterReadonlySummary.vue`
  - 未選資料空狀態
  - 已選主資料的唯讀欄位摘要
  - 明確「編輯這筆資料」入口

### 主要功能

- fixture / model / station / customer / user / ledger / quality tab；customer / user 僅 `super_admin` 可見，ledger / quality 則為 `admin` 與 `super_admin`
- tab 清單分頁
- 狀態篩選 / 關鍵字搜尋
- fixture 維護 `responsible_user_id` / `min_stock_qty` / `line_storage_location` / `department_storage_location`
- customer 維護 `assigned_user_ids`
- user 建立 / 更新 / 停用 / 重設密碼
- fixture / model / station CSV 匯入匯出 / 範本下載
- 從資料維護頁重新啟動新手導覽

- `admin` 與 `super_admin` 可永久刪除治具，並選擇保留或刪除該治具的收/退料紀錄
- `admin` 與 `super_admin` 也可永久刪除機種與站點，刪除前會提示關聯 `mapping / requirement / capacity summary` 將一併刪除
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
- customer / user tab 僅限 `super_admin`；ledger / quality tab 開放 `admin` 與 `super_admin`
- 主資料永久刪除只對 `admin` 與 `super_admin` 顯示，前端以獨立的 `canManageMasterEntities` 控制入口，不與使用者管理權限共用
- 後端以 `manage`（Admin 報表／治理）與 `super_manage`（客戶／使用者）作為真正授權邊界，不能只依賴前端隱藏按鈕
- `super_admin` 與 `admin` 也必須選到已透過 `user_customers` 指派的客戶，否則 customer-scoped 後端 API 會拒絕
- Modern、Form、Workbench 的帳號區皆提供修改自己密碼入口；需先驗證目前密碼

### 改資料維護頁時去哪裡

- 改 page tab orchestration、summary、CSV 流程或跨區導覽
  - `frontend/src/pages/MasterPage.vue`
  - master responsive breakpoint、editor mode 與手機 `list -> detail` 流程在此檔
  - 永久刪除確認 UI：`frontend/src/components/master/MasterPermanentDeleteModal.vue`
  - 永久刪除 API／刪除最後一筆退頁／refresh：`frontend/src/composables/useMasterEntityDeletion.ts`
  - 品質快速修正 UI：`frontend/src/components/master/FixtureQualityQuickEditModal.vue`

- 改手機／桌面 tab、更多操作、隱藏匯入或圖片輸入
  - `frontend/src/components/master/MasterToolbar.vue`

- 改列表、搜尋、分頁欄位
  - `frontend/src/components/master/MasterListPanel.vue`
  - 主資料清單的頁數提示 / 總筆數 / 翻頁動作目前在表格上方
  - 鍵盤列選取 / focus 樣式也在此檔

- 改 detail 編輯表單
  - `frontend/src/components/master/MasterDetailPanel.vue`
  - `admin` / `super_admin` 永久刪除按鈕與危險區塊也在此檔

- 改主資料新增／更新／啟停 API 協調
  - `frontend/src/composables/useMasterCrudActions.ts`

- 改未選資料提示 / 唯讀摘要欄位
  - `frontend/src/components/master/MasterReadonlySummary.vue`
  - summary 欄位資料組合仍在 `frontend/src/pages/MasterPage.vue`

- 改帳目管理清單的頁數提示 / 總筆數 / 翻頁動作
  - `frontend/src/components/master/TransactionAccountListPanel.vue`
  - 帳目載入、篩選、選取、重算與沖銷 orchestration：`frontend/src/composables/useMasterLedger.ts`
  - 後端篩選欄位：單號 / 操作人 / 治具 / 類型

- 改治具資料品質表、問題篩選、CSV 匯出、列內更新、問題類型跳轉規則
  - `frontend/src/components/master/FixtureQualityPanel.vue`
  - 品質報表與 quick editor orchestration：`frontend/src/composables/useMasterQuality.ts`

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
  - `加入站點` 與 `加入治具需求` 編輯器預設收合，點擊新增或既有列編輯時才展開；onboarding 走到表單步驟時會自動展開
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
  - 使用 `UiModalShell.vue` 管理目標機種初始焦點、Tab 循環、Esc、背景 inert 與關閉後焦點復原；儲存中拒絕關閉

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
  - super_admin / admin / user 維持分類選單；guest 可選 7 步 `guest-search-report` 快速教學或 18 步 `guest-readonly-guide` 完整唯讀教學
  - 兩個 guest 流程都以 step `query.home_mode` 在查詢與報表間切換；完整唯讀版另涵蓋匯出、即時狀態與收退料總檢視

- `frontend/src/components/common/OnboardingFlowPicker.vue`
  - 所有角色共用教學分類選單；guest 版顯示快速／完整唯讀兩種入口
  - guest 選單另列 `需登入角色`、`需 Admin` 與 `僅 Super Admin` 功能，避免把沒有入口誤認為系統缺漏

- `frontend/src/toastState.ts`
  - 成功 / 失敗提示

- `frontend/src/styles.css`
  - 共用 CSS utility
  - 新元件優先吃這裡的按鈕、panel、modal、table、chip 樣式

- `frontend/src/styles/surfaces/`
  - `inventory-relations.css`：`InventoryRelationsPage.vue` 的報表頁 global surface 樣式
  - `master.css`：`MasterPage.vue` 的 global surface 樣式，亦供 Teleport 的 Master modal class 使用
  - `production.css`：`ProductionPage.vue` 透過 `<style scoped src>` 載入，維持原 scoped 行為
  - `modern.css`、`form.css`、`workbench.css`：Modern／Form／工作台系統 surface 樣式；Workspace 組合既有 Modern chrome 與 Workbench 快速作業樣式

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
