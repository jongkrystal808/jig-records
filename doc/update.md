# 2026-06 to 2026-09 Update

這份文件整理目前已確認的 2026 年 6 月至 8 月更新，來源包含：

- 本輪對話中已完成與已驗證的工作
- 目前專案程式碼狀態
- `task.md` 的 `Update Log`
- 已同步過的架構與 map 文件

## 2026-09 Update

### 2026-09-03 P2 後端查詢與執行效率改善

- 配置報表頁面移除未使用的重複 total count；欄位摘要、去重庫存總計與 transaction detail count 合併為單一 CTE 查詢，一般 page 固定最多 2 次 SQL。聯動治具／機種／站點／水位選項由 4 次大型 union 查詢收斂為 1 次共用 CTE 查詢。
- Dashboard 低庫存改為最多 20 筆的 bounded preview，完整警示筆數由同一查詢的 window count 取得，不再把所有低庫存資料載入 application memory。
- 客戶清單的 `assigned_user_ids` 改為當批 customer set 一次載入；25 筆客戶的 service 與 guest scope 清單皆固定最多 2 次 SQL。
- `main.py` 不再無條件啟用 uvicorn reload；預設只在 development 啟用，Docker 明確關閉，並提供 `UVICORN_WORKERS` 設定。`.env.example`、compose 與 Docker 操作文件已同步。
- 驗證：完整 backend suite `159 passed, 1 skipped, 4 subtests passed`；frontend `73` 個測試檔／`227 passed`；production build 與 `docker compose config --quiet` 通過。build 仍提示既有入口 chunk 約 `509.94 kB`，留待 P3 bundle 拆分處理。

### 2026-09-01 P1 查詢與頁面載入效能改善

- storage overview 移除逐 storage code 查 container／placement 的 N+1，改由 repository 單次 grouped projection；新增回歸測試，30 個 storage codes 的 overview 固定最多 2 次 SQL。
- production station capacity／model query 改用 model-scoped requirement projection，批量取得 fixture、stock summary、stock level、designated stock 與 identifiers；新增回歸測試，25 筆 requirements 的 model query 固定最多 5 次 SQL。
- Modern Production 單筆 mapping／requirement CRUD 改成本地集合 patch，完成後只刷新一次 authoritative model query；初始化關聯資料只載入目前機種的 100 筆 page，不再抓整個客戶的 mapping／requirement 全集。
- Modern Master 的 fixture／model／station／customer／user 清單改為 active-tab server-side paging，keyword／status 在 backend 篩選並以 250ms debounce 載入；ledger 與 quality 只在進入各自 tab 後載入，quality 所需完整關聯 context 不再拖慢其他 tab。
- 驗證：新增後端效能測試 `2 passed`；完整 backend suite `147 passed, 2 subtests passed`；frontend `73` 個測試檔／`227 passed`；production build 通過。

## 2026-08 Update

時間範圍：2026-08-03 ~ 2026-08-28

### 2026-08-28 搜尋 URL 狀態與純識別碼模式

- Modern 與工作台搜尋會把目前模組、搜尋子模式、關鍵字、頁碼／選取結果及詳細分頁寫入 URL；送出搜尋、切換模組、切換治具／Datecode 搜尋或選取結果會建立瀏覽器歷史，上一頁／下一頁可還原並重新載入當時狀態。
- 工作台與 Modern UI 互切時會映射目前治具／機種模式、關鍵字、選取結果與識別碼搜尋類型，不再一律強制回到工作台治具首頁。
- 治具搜尋新增 `治具資料` 與 `Datecode／序號` 明確切換；後端 `/search/global` 新增 `fixture_search_mode=fixture|identifier`。預設治具模式只查治具編號、名稱與儲位，純識別碼模式才查完整 transaction identifier，解決同文字 identifier 覆蓋治具編號結果。
- 新手教學、前後端架構文件與回歸測試同步更新。
- 驗證基準：backend `130 passed, 2 subtests passed`；frontend `69` 個測試檔／`211 passed`；production build 通過；1024／1366／1920 三尺寸共 `15` 個 Workbench 視覺案例通過，並完成實際瀏覽器的治具搜尋、純識別碼搜尋、模組切換與上一頁還原 trial run，console 無 error。

### 2026-08-28 工作台圖片與帳目管理最佳化

- 工作台管理右側面板新增「收合篩選／展開篩選」控制；收合時保留篩選標題及套用／清除動作，隱藏條件欄位，讓圖片預覽、帳目詳細或編輯器取得更多垂直空間。
- 共用複選下拉的選項不再顯示 checkbox 方框，畫面只保留可點擊文字；已選項以文字顏色、字重與淡色背景識別，隱藏的原生 checkbox 仍保留鍵盤操作與無障礙語意。
- 工作台圖片維護改為清單選取流程：目前頁會自動選取第一筆治具，中間表格只保留四個必要欄位，右側優先顯示所選治具、圖片預覽、放大查看及上傳／替換操作，批次上傳置於其後；Form UI 原有五欄表格與列內選檔維持不變。
- 工作台收退料帳目管理取消中央的案件／詳細雙欄巢狀配置；中間面板完整提供案件清單，右側依選取案件顯示摘要、備註、治具明細及重載／重算／撤回操作，讓列表在 PC、Notebook、Tablet 都取得更完整欄寬。
- 元件測試新增工作台圖片 inspector、帳目右側 compact detail、篩選收合與純文字複選驗證；三尺寸視覺回歸涵蓋圖片維護、帳目管理、複選展開及帳目篩選收合。驗證基準：frontend `69` 個測試檔／`206 passed`，production build 與 `12` 個 Playwright 視覺案例通過。

### 2026-08-27 工作台管理三欄操作重整

- `WorkbenchManagementSurface.vue` 固定為左側管理導覽、中間結果、右側篩選／編輯工具；移除右欄原有的角色、資料範圍、模組說明與靜態提示，讓三個面板都承載實際操作。
- 收退料總檢視篩選移到最右面板；產能與資料維護的篩選及新增／編輯欄位也移到右欄，表格列維持只讀資料呈現。Form UI 原有列內編輯不變。
- `/master/images` 納入工作台資料維護子分頁，右欄承接圖片狀態篩選、批次上傳及選定治具的單張替換；治具資料品質的問題篩選與儲位／最低水位修正同樣集中到右欄。
- 管理工作台在 1024、1366、1920 寬度維持三欄，中央結果取得最大寬度且右側工具保留可操作尺寸；視覺回歸新增管理總檢視基準與面板幾何／水平溢位檢查。
- 驗證基準：frontend `69` 個測試檔／`203 passed`；production build 通過；三種尺寸共 `6` 個 Playwright 視覺案例通過，並完成總查詢、產能、主資料、圖片及品質修正的本機瀏覽器 trial run。

### 2026-08-27 工作台教學與多值篩選

- 工作台頂部工具列新增獨立的 `工作台 UI 教學` 入口；signed-in／guest 各有精簡與完整流程，涵蓋左側收退料／查詢、中間結果與批次面板、右側資訊及角色可用的管理導航。
- 新增共用 `UiMultiSelect.vue`，並套用於 Modern、Form、工作台的可組合篩選／匯出條件，包括收退料類型與來源、治具／水位／配置狀態、品質問題及圖片狀態；互斥選擇與資料編輯欄位維持單選。
- 前端 API 以重複 query key 傳送多值；後端 transaction 與 configuration report 查詢在同類別內採 OR、不同類別間採 AND，並保留單一值及既有 `fixture_status=all` 相容性。
- 補上工作台 picker、多選元件、重複 transaction query 與配置狀態多值的回歸測試。
- 驗證基準：backend `129 passed, 2 subtests passed`；frontend `68` 個測試檔／`195 passed`；production build 通過；1024／1366／1920 三個 Workbench Playwright 視覺基準皆通過，實際本機端到端操作亦無整頁水平溢位或 console error。

### 2026-08-27 工作台收退料與 Admin 作業區整合

- 工作台的單筆收料／退料合併為同一個 `收料／退料` 工作區，以表單內方向切換控制作業，route 採 `workbench_mode=transaction&transaction_type=receipt|return`，並相容舊的 receipt／return 連結。
- 新增 `WorkbenchBatchOperations.vue`，在中間面板用工作台標題、三步驟提示、受控高度與水平捲動承載共享批次解析／預覽／送出流程；每列仍可混合收料與退料。
- Admin 的收退料帳目管理與治具資料品質改由 `WorkbenchAdminOperations.vue` 呈現工作台專用的篩選、結果、案件／明細分欄、品質摘要與表格；資料取得、分頁、匯出、重算、撤回及修復沿用既有 composable 與 API，不再在工作台內渲染 Form Admin workspace。
- 工作台新手教學、單元測試及 1024／1366／1920 視覺測試同步改為合併收退料流程。
- 驗證基準：frontend `69` 個測試檔／`198 passed`；production build 通過；1024／1366／1920 三個 Workbench Playwright 視覺基準更新後皆通過，瀏覽器 trial run 的合併流程、批次面板、帳目與品質頁均無 console error。

### 2026-08-27 工作台管理分頁與關聯搜尋

- 快速作業新增 `管理後臺` 第四分頁；Admin 可進入收退料總檢視、產能設定、資料維護、收退料帳目管理、治具資料品質與匯出中心，user／guest 依既有 backend 權限只顯示可用入口。
- 治具查詢切到機種時，使用 fixture search context 的正式關聯機種產生提示；機種切回治具時使用 model query 的正式治具集合。建議可關閉，也可直接選擇目標並執行查詢，不依代碼或名稱相似度猜測。
- 工作台新手教學同步改為四分頁與角色感知管理入口，並補上雙向關聯與 guest 範圍的元件測試。
- 驗證基準：frontend `69` 個測試檔／`201 passed`；production build 通過；1024／1366／1920 的工作台 visual regression、管理分頁水平溢位檢查與本機雙向關聯 trial run 均通過，瀏覽器無 console warning／error。

### 2026-08-25 大型前端頁面第二輪拆分

- configuration report 的 route、draft／applied filters、paging query 與正式匯出狀態集中到 `useConfigurationReportState.ts`；`InventoryRelationsPage.vue` 樣式移至 surface CSS 後約 975 行。
- Master CRUD／啟停與永久刪除分別集中到 `useMasterCrudActions.ts`、`useMasterEntityDeletion.ts`；品質快速修正和永久刪除另成獨立 modal 元件，`MasterPage.vue` 約 1,472 行。
- `BatchImportPanel.vue` 將解析與退料預檢、預覽合併衍生狀態、送出與 409 確認分成三個 composable，元件約 892 行。
- onboarding flow picker、guided tour、release notice、production batch import 及 Master modal 均共用 `UiModalShell` 的焦點、Esc、背景 inert 與焦點復原行為。
- `InventoryRelationsPage.vue`、`MasterPage.vue`、`ProductionPage.vue` 的大型樣式區移至 `styles/surfaces`，保留原 global／scoped 行為。
- 本輪完整前端測試 62 個檔案／166 tests 通過，production build 通過。

### 2026-08-24 進度同步

#### 1. Modern／Form UI 擴展為全系統介面

- `App.vue` 現在是 system-surface controller；Modern／Form 切換會套用到查詢、收退料、產能、主資料、帳目、品質與圖片維護，不再只切換 `/search` 的首頁內容。
- 原有 `/search`、`/inventory*`、`/production*` 與 `/master/*` routes 仍是兩套介面的共同書籤與導覽契約，`FormSystemSurface.vue` 只改變呈現方式。
- Form heading 改成依工作區顯示動態標題與說明，模組索引使用完整文字並分組；Form route 切換後會回到模組／篩選頂端，Modern UI 維持原捲動邏輯。
- admin／user 可保存依帳號隔離的登入預設 surface；guest 固定預設 Form UI，目前 surface 另以 session 狀態保存。

#### 2. Form UI 大量資料與權限流程收斂

- 治具、機種、站點、客戶、使用者、圖片狀態、機種站點 mapping 與治具需求均改接 50／100 筆 server-side paging，不再將完整客戶資料載入瀏覽器後篩選。
- 產能新增／編輯使用 `FormRemoteAutocomplete.vue` 按需取得最多 20 筆候選；不再於進頁時預抓完整治具、機種與站點清單。
- 分頁使用者回應會批次帶回 `allowed_customer_ids` 與精簡 `allowed_customers`；Form 使用者編輯器可搜尋、複選、移除及清除授權客戶，且 Form 儲存前至少要求選擇一個客戶。
- 圖片狀態篩選只掃描 customer-scoped 與安全 legacy 圖片檔名，再交給 SQL 分頁查治具；Form 圖片頁不再 materialize 全部 fixture ORM rows。

#### 3. 產能貼上匯入加入安全預覽

- Form 產能支援 `model_code + station_code` 兩欄 mapping，以及 `model_code + station_code + fixture_code + required_qty` 四欄 requirement 貼上。
- 新增 customer-scoped preview endpoints，逐列分類 `new / unchanged / conflict / error`；需求量衝突會並列既有值與匯入值。
- 正式匯入預設不覆蓋衝突；只有使用者在共用確認視窗明確確認後才送出 `overwrite_existing=true`，且不會刪除匯入內容未提及的既有綁定。

#### 4. 查詢首頁空白狀態改為可操作總覽

- Modern 查詢尚未輸入文字時，改由 `GET /search/fixtures/overview` 顯示目前客戶範圍內的治具總清單。
- 簡略列包含治具代碼／名稱、目前庫存、庫存狀態、儲位與啟用狀態；選取後載入既有 lazy fixture context，清單以 `load more` 逐頁追加。

#### 5. Form 領域元件與共用規則拆分

- `FormReportOperations.vue` 現在只負責依 route 分派領域元件與轉送 view 事件。
- 收退料、產能、主資料分別由 `FormTransactionOperations.vue`、`FormProductionOperations.vue`、`FormMasterDataOperations.vue` 持有狀態與 API 流程，共用樣式集中於 `styles/form-report-operations.css`。
- Form 與 Modern 產能編輯器共用 `utils/formOperations.ts` 的 selection validation；Form 分頁全量匯出與錯誤文字也集中於同一工具模組。
- `InventoryBatchEntryGrid.vue` 的焦點導覽已限定在元件自己的 grid root，避免多個 grid 實例使用相同 row id 時聚焦到錯誤表格。
- 目前檔案規模快照：`InventoryRelationsPage.vue` 3,040 行、`MasterPage.vue` 2,925 行；原 696 行的 `FormReportOperations.vue` 已縮為 44 行 dispatcher，領域元件分別為 147／375／351 行。

#### 6. 文件與驗證基準

- `ARCHITECTURE.md`、landing、frontend/backend map 與索引已依目前程式更新；`task.md`、`to-update.md` 與本月更新紀錄追加 2026-08-24 現況，舊日期快照保留。
- 最新完整驗證結果列於本節後方；2026-08-04 的測試數量保留為歷史快照，不再代表目前基準。

### 最新驗證結果（2026-08-24）

- `.venv\\Scripts\\python.exe -m pytest -q`：`119 passed`。
- `npm test`：`53` 個測試檔、`152 passed`。
- `npm run build`：通過（Vue type-check 與 Vite production build）。
- 第一次 frontend test run 的 145 個案例本身皆通過，但 Vitest 結束時遇到 Windows 暫存檔寫入錯誤並回傳 exit code 1；在其他測試程序結束後單獨重跑，最終以上述 `53 / 152` 與 exit code 0 為正式基準。

### 本月重點

#### 1. 庫存配置報表改為後端聚合

- 新增 `GET /inventory/configuration-report`、`/configuration-report/options` 與 `/configuration-report/export`。
- 關鍵字、治具狀態、機種、站點、水位、儲位、配置狀態、收退料方向、來源與日期都由後端套用；前端只保留目前 server page。
- 報表回傳總庫存、客供／自購庫存、配置缺口、穩定的 `populated_columns`、可選交易明細，以及完整 `model + station` 需求集合計算出的可開站數。
- 新增 Alembic `0015_configuration_report_indexes`，補上報表交易查詢的複合索引；目前 source head 為 `0015`，runtime 最低相容 gate 仍是 `0011_search_indexes`。

#### 2. 前端路由與共用互動整理

- feature routes 改為動態 import，未登入時導向輕量 `/login` route，登入或訪客入口完成後導向 `/search`。
- 首頁查詢／報表模式會保存並交接查詢文字、選取結果與 URL 狀態。
- 新增全域 Promise-based `SystemConfirmDialog`，取代功能頁的原生 `window.confirm`。
- 主資料頁新增唯讀摘要與 `summary / edit / create` 狀態；手機報表列抽成 `InventoryReportMobileCards.vue`。
- 報表欄位偏好、有效欄位、篩選差異、交易明細及首頁模式交接已抽成獨立 utility 並補測試。

#### 3. 文件校正

- admin 與 user 的 customer scope 都以 `user_customers` 指派為準；`manage` 不會繞過 customer scope。
- 現行儲位欄位為 `line_storage_location` 與 `department_storage_location`，舊 `fixtures.storage_location` 已由 `0013` 移除。
- Docker Compose 的資料庫密碼必須由 `.env` 提供，文件不再列出不存在的預設密碼。
- `to-update.md` 已從原始需求便條轉為狀態表，並移除失效的 Typora 本機圖片連結。

#### 4. 治具圖片 customer scope

- 圖片儲存從全域 `<fixture_code>.<ext>` 改為 `<customer_id>/<fixture_code>.<ext>`，跨客戶同碼不再互相覆寫。
- 圖片讀取 API 必填 `customer_id` 並套用 customer scope；前端圖片預覽一律傳入目前客戶。
- 舊平面圖片只在 code 全系統唯一時維持唯讀相容；治具更名可 rollback，永久刪除會清理 scoped 圖片。

#### 5. 手機主資料操作收斂

- KPI 改為單列可水平滑動的 compact chips，七個主資料分頁改成按「資料維護／系統管理」分組的下拉選單。
- 圖片、CSV／JSON、返回搜尋與教學等低頻入口集中至「更多操作」，讓主資料清單在 390px 首屏直接出現。
- 進入手機明細模式後隱藏 KPI 與批次工具，只保留返回清單、目前項目及適用的編輯入口。

#### 6. 報表主檢視切換（已於後續需求撤回）

- 曾加入「全部治具／全部機種／全部站點」主檢視與一個主要實體一列的投影，後續依需求完整撤回。
- 現況為治具、機種、站點三個一般聯動篩選器；空值表示各自的全部，不另提供「無」或主檢視切換。
- URL 不再保存 `basis`，API／匯出不再接受 `report_dimension`；所有結果固定使用關聯明細列，同一治具可因多個配置重複出現。
- `populated_columns` 自動收合無資料欄位、欄位選擇偏好與匯出可見欄位功能仍保留。

#### 7. 手機報表分頁與 sticky 結果列

- 手機報表預設每頁 20 筆並提供 20／50 選項；桌面維持 50／100，`page_size` 繼續同步至 URL。
- 結果摘要與已套用條件在手機改為 topbar 下方的 sticky toolbar，摘要與條件皆可單列橫向滑動。
- 初次進入及套用後自動收合篩選的流程維持不變。

#### 8. 收退料快速新增一列

- 正式收／退料面板新增常駐快速列：治具 autocomplete、datecode／編號、數量與「加入待送清單」。
- 快速列會驗證目前客戶的有效治具並沿用 identifier 正規化；加入後轉入原批次草稿、預覽、退料預檢及重複資料合併。
- 送出仍使用既有 receipts／returns batch API，不建立第二套單筆交易流程。
- 同步修正 MySQL `ONLY_FULL_GROUP_BY` 下的跨客戶治具代碼唯一性查詢，避免 customer-scope 圖片相容邏輯讓治具清單 API 回傳 500、連帶停用 autocomplete。

#### 9. 1280px 頂欄快捷操作

- `1024px–1366px` 的 compact desktop 頂欄固定保留漢堡選單、目前客戶及「收／退料」，不再讓常用庫存操作多經過一次抽屜點擊。
- 匯出、教學、今日統計、客戶切換與登出仍維持收進抽屜；低於 `1024px` 沿用手機精簡頂欄。
- 訪客與其他不可操作收退料的唯讀 session 不顯示快捷鍵。

#### 10. 全域 Modal 鍵盤與焦點行為

- 新增共用 `UiModalShell.vue`，補齊 dialog／alertdialog 語意、`aria-modal`、初始焦點、Tab／Shift+Tab 循環、Esc、背景 inert 與關閉後焦點還原。
- 全域收退料、匯出中心及 `SystemConfirmDialog` 共用同一套 shell；巢狀確認視窗只由最上層接收鍵盤事件。
- 收退料關閉仍沿用既有未送出草稿確認，不會因 Esc 或背景點擊繞過離開保護。

#### 11. Token 過期返回登入流程

- API transport 統一處理 authenticated `401`：立即清除 session／目前客戶、只顯示一次「登入已逾時」，並通知 shell 返回 `/login`。
- 原 route 的 path、query 與 hash 會暫存在 `sessionStorage`；重新登入或訪客入口成功後返回原頁並清除暫存。
- 並行 JSON、文字與檔案請求只觸發一次 expiry flow；登入 API 本身的帳密錯誤仍照原錯誤呈現。

#### 12. P2 前端頁面拆分與 Pydantic 相容

- `InventoryRelationsPage.vue` 將篩選、結果呈現與圖片對話框拆成獨立元件，頁面縮至 3,127 行並保留 route、API、draft／applied 與匯出協調。
- `MasterPage.vue` 將 toolbar、ledger 與 quality workflow 拆至 `MasterToolbar.vue`、`useMasterLedger.ts`、`useMasterQuality.ts`，頁面縮至 2,925 行。
- 圖片對話框集中 customer scope、請求競態與 object URL 清理；toolbar、ledger、quality 各自補上元件／composable 回歸測試。
- 共用 schema 改用 Pydantic 2 `field_serializer`，FastAPI 回應仍維持 `YYYY-MM-DD`，完整 suite 不再產生 `json_encoders` deprecation warnings。

### 2026-08-04 歷史驗證快照

- `.venv\\Scripts\\python.exe -m pytest -q`：`113 passed`，無 Pydantic `json_encoders` deprecation warnings。
- `npm test`：`35` 個測試檔、`102 passed`。
- `npm run build`：通過。
- 以 390 × 844 與 1280 × 800 實際檢查報表：手機 20 張卡片／篩選收合、桌面表格切換及整頁無水平溢位皆正常。

### 2026-08-04 更早驗證快照

- `.venv\\Scripts\\python.exe -m pytest -q`：`109 passed`、`3 subtests passed`（另有 399 個 Pydantic `json_encoders` deprecation warnings）。
- `npm test`：`31` 個測試檔、`97 passed`。
- `npm run build`：通過。
- `.venv\Scripts\python.exe -m pytest backend\tests\test_services.py -q`：`43 passed`；修正後的分組查詢另於目前 MySQL 8.4 容器實測通過。

## 2026-07 Update

本節記錄當時截至 2026-07-04 的快照；後續狀態請以上方 2026-08 Update 為準。

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

同步內容包含：onboarding / guided tour、tutorial mode、topbar shell 現況、`ExportCenterPanel.vue`、inventory report export / preview、搜尋頁相近編號提示收斂、測試現況與當時剩餘失敗點。

### 當時驗證結果

#### Frontend

- `npm run build`：通過

#### Backend / Tests

- `.venv\\Scripts\\python.exe -m pytest tests -q`：目前為 `4 passed, 1 failed`
- 已確認 `requirements.txt` 原本就有 `openpyxl`，但本機 `.venv` 當時未安裝。
- 已補安裝 `openpyxl` 到目前虛擬環境，排除因缺套件導致 backend import 失敗的問題。

### 當時剩餘問題（已由後續更新取代）

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
- 7 月初記錄的 inventory `identifier` 驗證與 validation error serialization 問題已在後續版本修正；目前驗證基準請見 2026-08 Update。
