# Full Backend Landing Tasks



## Scope

### 0) 客戶切換與登入入口
- [x] `fixtures` 綁定 `customer_id`
- [x] 所有與治具相關列表/查詢 API 支援 `customer_id` 篩選
- [x] 前端新增全域客戶切換下拉
- [x] 前端在各模組請求帶入 `customer_id`
- [x] 新增 `users` 表（帳號、密碼雜湊、名稱、角色、啟用狀態）
- [x] 新增 `user_customers` 表，維護已登入 `admin` / `user` 的可見客戶清單
- [x] 新增 `POST /auth/login`、`POST /auth/guest`、`GET /auth/users`
- [x] 前端新增登入頁，支援「帳密登入」與「訪客入口」
- [x] `admin` 可管理已指派客戶內的全部資料
- [x] `guest` 可看全部客戶但不可編輯，且不可進入 `資料維護`
- [x] `user` 只能看授權客戶，客戶指派改由客戶分頁維護
- [x] `user` 可編輯授權客戶下的業務資料，但不可管理客戶與使用者

### 1) 資料維護停用能力一致化
- [x] `machine_models` 加入 `is_active`
- [x] `stations` 加入 `is_active`
- [x] 後端 `PUT` API 支援 `is_active`
- [x] 前端 `資料維護` 頁面可對治具/機種/站點執行停用

### 2) 儲位策略收斂
- [x] 治具儲位只保留 `fixtures.storage_location`
- [x] 移除 `warehouse_profiles`、`storage_locations`、`fixture_location_assignments`、`fixture_images`
- [x] 查詢與主檔統一使用文字儲位顯示

### 4) 產能頁目前開站數改為後端計算
- [x] `get_station_capacity` 以 `model_id + station_id` 為查詢範圍，回傳真實最大開站量
- [x] 前端 `產能` 頁改用 API 回傳值，移除 hardcoded `0`
- [x] `current_open_station_count` 已正式退場，不再出現在 production schema / API / frontend type
- [x] 產能頁改為只呈現「指定機種 + 指定站點」的單站獨立最大開站量語意

### 5) 查詢頁展示欄位去除示意值
- [x] 移除 `---` 類示意值
- [x] 交易/時間欄位改為實際資料或 `-`
- [x] 明確 fallback 規則（空值顯示 `-`）

### 6) Schema 演進機制（無 migration 下的保底）
- [x] 新增 startup schema patch（針對現有 DB 自動補欄位）
- [x] 補 `is_active` 新欄位 patch（model/station 等既有主檔）
- [x] 不破壞既有資料

## Validation Checklist

- [x] 可切換客戶後刷新各模組資料
- [x] 登入後可進入系統；訪客可直接進入
- [x] `python -m compileall backend/app` pass
- [x] `npm run build` pass
- [x] `master` 可新增/編輯/停用四類主檔
- [x] `production` 的目前開站數非固定值
- [x] `search` 不再出現示意字串 `---`

## Current Snapshot

- 目前 `App.vue` 已改為頂部 shell，不再使用左側常駐導覽；頂欄包含登入狀態、客戶切換、今日統計、全域 `收/退料` 與 `匯出中心` 入口，以及 `更多功能` 選單。
- 目前 shell 仍沒有桌面版 mini sidebar；手機版則維持漢堡選單 / overlay 導覽。
- 新手教學入口已搬到全域 shell：桌面版在 `AppTopbar`，手機版在 `AppMobileDrawer`；教學啟動方式改為開啟 flow picker，而不是綁在 `SearchWorkspacePage` 浮動按鈕。
- 新手教學 flow 目前是五張卡：`查詢工作台`、`批次收 / 退料 & 收退料總檢視`、`治具 / 機種 / 站點主資料`、`產能設定與治具需求`、`收退料帳目管理 / 治具資料品質`。
- `SearchWorkspacePage` 已移除 `相近編號` 提示框，查詢首頁目前只保留最近收 / 退料治具快捷入口與結果區導向流程。
- `MasterPage` 已有前端分頁；`SearchWorkspacePage` 也已改為 bounded search contract + `load more`。
- `SearchWorkspacePage` 目前仍沒有可收合的篩選區。
- `SearchWorkspacePage` 的 fixture / model context 已改為選取後延遲載入，不再首屏全量預載全部 search domain 資料。
- `SearchHeroSection.vue` 已補明確 `搜尋` CTA；搜尋後會自動收合 `最近收 / 退料治具` 區塊，讓結果更早進入第一屏。
- `SearchWorkspacePage.vue` 的 idle hero 已取消固定視窗高垂直置中，避免 1024px 左右筆電出現過大頂部留白。
- `npm run build` 目前可通過。
- `.venv\\Scripts\\python.exe -m pytest -q` 目前為 `86 passed`。
- 目前 `identifier` 已收斂為單一規則：
  - 純數字且長度 `1-4`：寫入前左補零為 4 碼，查詢時同時匹配 `1 / 01 / 001 / 0001` 類零補齊舊資料。
  - 其餘值：視為 legacy `identifier / datecode`，寫入與查詢都以原值處理。
- 這套規則已集中到 `backend/app/utils/identifier_rules.py`，並有獨立單元測試覆蓋。
- `BatchImportPanel.vue` 現在會在退料解析階段直接比對目前 `identifier` 庫存，預覽表就能指出哪一筆 `datecode/編號` 無庫存或同批累計退料超量。
- `BatchImportPanel.vue` 的 `來源` 已改成整批單一選擇：預設 `客供`、可切 `自購`，本批所有 items 送出時共用同一個 `ownership_type`。
- 收/退料送出失敗時現在會直接顯示 UI toast；後端錯誤訊息也補上「第幾筆 / 第幾列」上下文，不需要再到 F12 console 才能定位。
- `MasterPage.vue` 已新增 admin-only 的 `收退料帳目管理` 分頁，支援案件清單篩選、明細檢視、撤回單筆交易，以及依客戶全量重算庫存摘要。
- `收退料帳目管理` 已改成 server-side transaction paging：不再只抓最近 200 筆，改由後端回傳 `page / page_size / total`，並在後端處理單號 / 操作人 / 治具 / 類型篩選。
- `inventory` 後端已補 `reverse_transaction` 與 `recalculate_inventory_state` 管理 API；撤回會刪除整筆交易後重算庫存，並寫入 audit log。
- `ProductionPage.vue` 的 batch domain logic 已從 page 抽出：解析、相似比對、逐列狀態同步與批次提交現在集中到 `frontend/src/composables/useProductionBatchImport.ts` 與 `frontend/src/utils/productionBatchImport.ts`。
- `ProductionPage.vue` 的 editor / autocomplete state 也已抽到 `frontend/src/composables/useProductionEditorState.ts`；四個重複的 autocomplete input 則已收斂成 `frontend/src/components/UiAutocompleteInput.vue`。
- `ProductionPage.vue` 現在基本只保留 route/data orchestration，原本內嵌的 batch/editor 細節已移出頁面主檔。
- `ProductionPage.vue` 現在是 `總覽` / `產能設定` 雙模式：`/production` 顯示站點總覽與瓶頸 drill-down，`/production/mapping` 與 `/production/requirements` 共用同一個設定工作區。
- `ProductionPage.vue` 目前會把 `model_id` 與 `return_to` 保留在 route query；若有 `return_to` 就顯示 `返回來源`，否則 fallback 回 `/search`。
- `ProductionPage.vue` 的未儲存 mapping / requirement 變更已接到 customer switch guard 與 route leave / browser unload confirm，避免切客戶或離頁時直接丟資料。
- `ProductionDetailSection.vue` 已改為 `選機種 -> 選站點 -> 配置治具` 的響應式 master-detail 工作區；新增站點不再重輸機種，新增治具不再重輸站點。
- 產能設定的新建表單預設保持空白，不再自動塞入第一個站點 / 第一支治具；切換機種或站點時也會保護未儲存草稿。
- 產能頁 dirty-state 只比較可實際儲存的輸入欄位；總覽切換機種 / 站點、進入產能設定或重新整理，不再因自動繼承的 context 誤報未儲存修改。
- mapped station 即使尚未設定治具需求，也會保留在總覽及設定清單；治具需求表直接顯示庫存、可開站數與限制狀態。
- 治具需求送出前會以目前庫存預估儲存後最大開站數；guest 產能頁則只保留唯讀檢視，不顯示任何寫入操作。
- 產能設定第三階段已完成：可將目前站點的整套治具需求複製到同機種其他站點，或跨機種複製到指定站點。
- 複製預設採安全模式，目標已有相同治具時只顯示衝突並跳過；只有明確勾選覆蓋才會更新不同數量，完全相同的資料仍跳過。
- 跨機種目標尚未綁定站點時，後端會在同一交易中自動建立 `model_station`；完成後 UI 直接切到目標機種 / 站點並顯示新增、更新、跳過數量。
- `SearchWorkspacePage.vue` 的治具 / 機種內嵌編輯草稿已接到 customer switch guard，切換頂欄客戶時也會提示未儲存修改。
- `frontend/src/utils/productionStations.ts` 已把產能頁可選站點收斂成「目前機種已綁定站點」，避免總覽或治具需求預設落到未對應站點而觸發 NG capacity request。
- `RequestValidationError` payload 已修正為 JSON-safe 序列化，欄位驗證失敗會穩定回傳 `422`。
- `auth token` 目前以受信任內網為前提，`sessionStorage + Bearer token` 方案暫不列為本輪必要整改。
- `main.py` 與 Docker image 預設啟動路徑已改為明確 bootstrap launcher；`docker-compose` 的 `api` service 會顯式關閉重複 bootstrap，維持由獨立 `bootstrap` service 先初始化。
- 後端已新增全域 request-level audit logging，所有 API 操作都會額外寫入 `logs/audit.log`。
- `logs/audit.log` 目前同時收斂兩類事件：
  - `request_audit`：記錄 request method/path/query、client IP、status code、duration 與操作者資訊。
  - `domain_audit`：記錄既有業務審計事件，如主資料異動、交易撤回、密碼重設等 summary。
- audit file 採每行一筆 JSON 的 append-only 形式，並使用 rotating file handler。
- 收退料批次預覽表已新增 `目前庫存` 與 `交易後庫存` 欄位，送出前可先確認每筆 `identifier` 的庫存變化。
- 同一批內若重複出現相同 `治具 + datecode/編號`，預覽表會按列順序累計 `交易後庫存`。
- 登入後的版本更新提示已改成同一版本只顯示一次，不再因再次登入或切換帳號重複跳出。
- 查詢頁已移除 `相近編號` 提示框，只保留最近收 / 退料治具快捷入口。
- 查詢頁送出搜尋後，會在版面穩定後自動捲動到結果區，不再被 `最近收 / 退料治具` 區塊擠偏。
- `AppTopbar.vue` 已把 `今日收料 / 今日退料 / 低水位` 從 hover-only 改成 click/tap popover，並支援鍵盤與 `Esc` 關閉。
- 頂欄今日統計已改走 `GET /api/v2/inventory/dashboard-summary`：不再由前端抓最近 200 筆交易自行推算，改由後端一次回傳今日收料數、今日退料數、低水位數、最近收料 10 筆、最近退料 10 筆與低水位預覽。
- `AppTopbar.vue` 現在於 `1366px` 以下直接切 compact header，不再保留中寬桌面下的雙列頂欄。
- `AppMobileDrawer.vue` 已補可捲動 drawer、sticky header，並把主要功能入口排在統計資訊前方。
- shell / search / drawer 已補一批無障礙語意：customer picker 名稱、搜尋 input 名稱、mode switch `aria-pressed`、drawer overlay `關閉選單`。
- 收退料送出已新增 2 分鐘重複交易防呆；遇到相同使用者、相同交易簽章時會先跳確認提示。
- 若使用者確認重送但沿用同一 `transaction_no`，後端仍會明確提示需修改單號，不會建立第二筆同單號交易。
- `MasterPage` 已新增 admin-only `治具資料品質` 分頁，可檢查名稱、儲位、圖片、最低水位、機種關聯與 `Identifier`/總庫存一致性。
- `治具資料品質` 分頁已支援依問題類型篩選、匯出品質 CSV，並依問題類型導向不同頁面。
- `治具資料品質` 中的 `沒有儲位 / 沒有最低水位` 已改成表格內直接填寫與更新，不需先開彈窗。
- 儲位欄位規則統一為分欄填寫：`產線儲位`、`部門儲位` 各自獨立，固定提示為「產線儲位、部門儲位分開填寫，只填一個也可」。
- `治具資料品質` 中的 `沒有任何機種關聯` 會直接導向 `產能管理 / 治具需求`。
- 全域 `匯出中心` 已整合收退料、主資料、站點設定、治具需求與治具資料品質匯出，不必再記各頁匯出入口。
- 匯出中心資料集現在會依角色過濾：admin 才看得到 `治具資料品質`，guest / user 不會再看到點了只回 `403` 的選項。
- 已修正 `GET /api/v2/inventory/admin/transactions` 在 MySQL 的 `500`：admin 收退料帳目管理的 transaction 分頁子查詢不再用 `DISTINCT id` 搭配 `occurred_at` 排序，改為 `transaction id desc`，避免帳目管理整頁無法載入。
- 收退料 `transaction_no` 規則已正式收斂為前後端都必填：backend 不再自動產生單號，避免和重複交易防呆形成「前端強制人工、後端默默補號」的雙軌狀態。
- 但歷史讀取已容許舊資料無單號：`/inventory/transactions`、`/inventory/admin/transactions`、`/inventory/transactions/overview` 都會接受 legacy `NULL / 空字串 transaction_no`，前端統一顯示為 `（無單號）`。
- `MasterPage` 各分頁已具備獨立 URL：`/master/fixtures`、`/master/models`、`/master/stations`、`/master/customers`、`/master/users`、`/master/ledger`、`/master/quality`。
- 查詢頁已支援從 route query 帶入 `mode` 與 `q`，供跨頁跳轉直接落到指定治具查詢結果。
- 現行權限與資料行為以 backend router/service/repository 為準；架構文件若有落差需回頭依程式校正。
- `admin` 已可在治具維護頁永久刪除治具，API 為 `DELETE /api/v2/master/fixtures/{fixture_id}`。
- 刪除時可選擇保留或刪除該治具的收/退料明細；保留時以治具代碼/名稱快照維持歷史查詢與匯出，刪除時只移除該治具明細，混合交易的其他治具明細不受影響。
- `admin` 也已可在資料維護頁永久刪除機種與站點，API 為 `DELETE /api/v2/master/models/{model_id}` 與 `DELETE /api/v2/master/stations/{station_id}`。
- 機種/站點永久刪除前會明確提示將一併刪除的關聯資料；刪除時會同步清掉 `model_stations`、`fixture_requirements` 與受影響 `machine_capacity_summary`。
- 目標 MySQL 已升級至 Alembic `0014_fixture_deletion`，transaction item 的 `fixture_id` 可為空並使用 `ON DELETE SET NULL`。
- 現行 backend customer scope 對 `admin` 與 `user` 都依 `user_customers` 指派；`manage` 權限不會略過客戶範圍。
- `資料維護` 主清單與 `收退料帳目管理` 清單已把頁數提示、總筆數提示與翻頁動作移到清單最上方，不再放在表格底部。
- `治具資料品質` 的 `Identifier 庫存與總庫存不一致` 現在跳到 `收退料帳目管理` 時，會自動帶入該治具的篩選條件。
- `InventoryOverviewPanel.vue` 的總檢視篩選區已改成主篩選 + `進階篩選`，並使用 `4 / 3 / 2 / 1` 欄 responsive 版面，避免筆電第一屏被表單吃滿。
- `InventoryPage.vue` 的總檢視查詢已改接分頁 detail-row API，查詢條件、頁碼、每頁筆數與 `return_to` 會同步進 route query。
- `App.vue` / `appState.ts` 現在會從 `sessionStorage` 還原登入 session 與目前客戶，並在切換客戶時整合各頁未儲存防呆訊息。
- `AppTopbar.vue` 的低水位 popover 已可直接對單一治具點 `收 / 退料`，會用預填治具代碼打開全域批次 modal；訪客不顯示這個 CTA。
- `BatchImportPanel.vue` 已支援預填治具快捷區；同一批內相同 `治具 + identifier` 的 ready 列會在送出前合併成單筆 payload。
- `BatchImportPanel.vue` 現在會依入口決定預設操作方式：有預填治具時先進快速模式，只顯示 `datecode/編號 + 數量 + 加入批次`；大型批次貼上框需使用者手動展開。
- 全域 `收退料` Modal 現在不會再因 `關閉`、`Esc` 或 `收退料總檢視` 直接丟掉草稿；未送出時會先統一跳確認。
- 全域 `收退料` Modal 也已新增 `sessionStorage` 草稿暫存；同客戶重新打開 modal 時可恢復上次未送出的批次內容。
- 但批次 `來源` 不會跟著草稿或上次操作保留；`清空`、成功送出與重新開啟後都會回到 `客供` 預設，避免誤送 `自購`。
- `SearchWorkspacePage.vue` 現在會保留 `mode / q / page / selected_id / detail` 查詢狀態，並在 fixture / model 編輯時加上未儲存離頁確認。
- 查詢頁治具 detail 已把「完整歷史」動作改為跳轉 `/inventory/overview`，並只帶 `fixture_code + return_to`，避免用最近 8 筆預覽資料反推日期範圍而漏掉更早交易。
- 查詢頁治具 detail 的 `以此治具收 / 退料` 與頂欄低水位 popover 的 `收 / 退料` 現在都會在訪客模式下直接隱藏，和頂欄主 `治具收/退料` 按鈕保持一致。
- `ProductionPage.vue` 現在以 `站點設定` 作為 operator-facing 文案；建立或更新治具需求時若底層 `model_station` 不存在，後端會自動補建。
- `MasterService.build_fixture_quality_report()` 已修正 `missing_storage_location` 判定：只要 `產線儲位` 或 `部門儲位` 任一存在，就不算缺儲位。
- `MasterPage.vue` 主資料頁雙欄會維持到約 `1100px`；手機寬度改成 `清單 -> 明細` 流程，不再長頁上下來回捲動。
- `MasterListPanel.vue` 的主資料表格列已支援 `tab` 聚焦與 `Enter / Space` 開啟明細。

## Phase 0-4 Approved Update

### Shell / Navigation

- [x] 側邊欄改為頂部欄
- [x] 頂部欄常駐顯示：登入者 / 登入登出、目前客戶 / 切換客戶、今日收退料總數、低水位提醒
- [x] 頂部欄新增 `收/退料` 按鈕，開啟全域 Modal
- [x] 頂部欄新增 `更多功能` 下拉，包含 `收退料總檢視 / 資料維護 / 產能管理`
- [x] Logo 可點擊回 `/search`
- [x] `MasterPage` 新增 `返回搜尋` 按鈕
- [x] `ProductionPage` 新增 `返回搜尋` 按鈕
- [x] 手機版 shell 改為常駐漢堡按鈕 + 目前客戶名稱，其餘收進選單

### Search Page

- [x] 拆出 `FixtureInfoPanel.vue` / `ModelInfoPanel.vue`，純展示、只吃 props
- [x] 拆出 `FixtureEditForm.vue` / `ModelEditForm.vue`，供搜尋頁內嵌編輯使用
- [x] 搜尋頁新增區塊勾選顯示 chip 列，並以 localStorage 分開記住治具 / 機種偏好
- [x] 全部取消勾選時擋住，至少保留一個區塊
- [x] 新增 `資料維護` 勾選項，勾上後出現 `編輯` 分頁
- [x] `資料維護` 勾選狀態也要記住在 localStorage
- [x] 查無結果時顯示 `找不到，新增一筆？`，並可直接打開建立流程
- [x] 機種搜尋結果提供輕量入口跳轉既有 `ProductionPage`，並帶入該機種預選
- [x] 編輯分頁首次 lazy load 時顯示共用小型 inline spinner

### Inventory / Global Modal

- [x] 抽出 `BatchImportPanel.vue` 共用元件
- [x] `/inventory` 與全域 Modal 共用同一份批次匯入 UI / 資料流
- [x] 全域 Modal 只含批次貼上匯入，不含庫存總覽 / 低水位 / 最近紀錄
- [x] Modal 成功送出後不自動關閉，僅清空輸入框

### Master / Production Scope

- [x] `ProductionPage` 內部結構維持不動，只新增搜尋頁導入入口

### Loading

- [x] 新增一個共用小型 inline spinner
- [x] spinner 先套用於：搜尋頁編輯分頁 lazy load、收退料 Modal 資料載入

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
- [x] 負責人來源改為「該客戶已指派使用者」
- [x] 治具命名規則改為：不可符號開頭，其餘不限制

### 10) 收退料資料模型調整
- [x] 治具主檔不再提供使用者維護 `manage_type`
- [x] 治具主檔不再區分 `客供 / 自購`
- [x] `客供 / 自購` 改為收退料交易明細欄位 `ownership_type`
- [x] `datecode` / `serial` 概念已統一為單一 `identifier`
- [x] 收退料查詢、匯出、展示、批次匯入都只使用單一 `identifier`
- [x] 收退料流程需檢核並展示 `ownership_type`

### 10.1) 退料解析預檢與錯誤提示
- [x] 批次貼上解析階段即比對 `identifier-stock-summary`
- [x] 退料時若 `datecode/編號` 無庫存，直接在預覽表標記錯誤列
- [x] 退料時若同一批解析累計數量超出可退庫存，直接在預覽表標記錯誤列
- [x] 收/退料送出失敗時顯示 UI toast，不再只留在瀏覽器 console
- [x] 後端退料與 CSV 匯入錯誤訊息補上「第幾筆 / 第幾列」上下文

### 10.2) Production 批次匯入結構收斂
- [x] `ProductionPage.vue` 移除 batch parsing / similarity / submit domain 邏輯
- [x] 新增 `useProductionBatchImport.ts` composable 統一管理 modal state、batch rows 與提交流程
- [x] 新增 `productionBatchImport.ts` helper 收斂純解析與相似比對規則
- [x] 補前端單元測試覆蓋 production batch parsing / similarity 行為

### 10.3) Production 編輯器與 autocomplete 結構收斂
- [x] `ProductionPage.vue` 移除 editor / autocomplete state 與 selection sync 細節
- [x] 新增 `useProductionEditorState.ts` composable 集中管理編輯狀態、未儲存變更判斷與 autocomplete handlers
- [x] 新增 `UiAutocompleteInput.vue` 共用元件，收斂 `ProductionDetailSection.vue` 內四個重複欄位模板

### 10.3.1) Production route / station workflow 校正
- [x] `ProductionPage.vue` 以 `總覽` / `產能設定` 雙模式收斂 route workflow
- [x] `model_id` 與 `return_to` 由 production route query 持續同步，刷新與跨頁返回都保留上下文
- [x] 未儲存的 mapping / requirement 變更接入 customer switch guard、route leave 與 browser unload confirm
- [x] 站點可選範圍統一收斂為目前機種已綁定站點，不再預設落到同客戶但未對應的站點
- [x] 新增 `frontend/src/utils/productionStations.ts` 與前端測試，固定 model-scoped station derivation 行為

### 10.4) 收退料帳目管理與庫存修復
- [x] `MasterPage.vue` 新增 admin-only `ledger` 分頁
- [x] 新增 `TransactionAccountListPanel.vue` / `TransactionAccountDetailPanel.vue` 拆出帳目管理清單與案件細節
- [x] 後端新增 `DELETE /inventory/admin/transactions/{transaction_id}`，支援撤回單筆案件
- [x] 後端新增 `POST /inventory/admin/recalculate`，支援依交易明細全量重算庫存摘要
- [x] 撤回案件後自動重算庫存，並寫入 audit log
- [x] 帳目管理頁支援依單號 / 操作人 / 治具編號與交易類型篩選

#### 10.5) 模型定案

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

#### 10.6) 前端流程定案

- 收退料頁不再提供單筆表單，統一由批次貼上匯入處理
- 每筆貼上資料都必須包含 `治具編號 + 識別碼 + 數量`
- `identifier` 採單一共用規則：只有純數字且長度 `1-4` 會左補零為 4 碼；其餘值都以 legacy 原值保留
- `identifier` 的查詢 / 匯出篩選與寫入共用同一份判斷：短純數字做零補齊相容匹配，其餘值做原值查詢
- 所有收退料明細都必填 `ownership_type`

### 11) 儲位與圖片整合
- [x] 治具主檔可直接填寫 / 維護文字儲位
- [x] 查詢頁可依治具代碼讀取檔案式圖片預覽

### 12) Review / Hardening Backlog
- [x] 密碼雜湊改為帶 salt 的 PBKDF2，並相容舊的 sha256 密碼資料
- [x] 治具 code lookup 補 customer scope，避免未來跨客戶查詢污染
- [x] 治具列表與匯出不再因讀取而自動建立 stock level
- [x] CSV 匯入改為批次原子操作，避免部分成功、部分失敗
- [x] 今日統計改用本地日期邏輯，並避免只看最近 50 筆
- [x] 忽略前端生成檔與 build 產物，降低 repo 雜訊
- [x] 正式導入 Alembic migration，逐步移除 runtime schema patch
- [x] 為登入 / 角色權限補上真正的後端授權機制
- [x] 補上 backend 與 frontend 的測試覆蓋，至少涵蓋 auth / inventory / capacity / CSV

### 13) 優先級優化待辦

#### P0 - 高優先
- [x] 正式導入 Alembic migration，建立可追蹤的資料庫版本管理流程，逐步移除 runtime schema patch
- [x] 為登入 / 角色權限補上真正的後端授權機制，明確區分可讀、可寫、可管理操作
- [x] 補上 backend 與 frontend 的測試覆蓋，至少涵蓋 auth / inventory / capacity / CSV / production 主流程
- [x] 清理 `frontend/src` 與專案內的生成檔、`*.js`、`*.map`、`dist` 類產物，避免 source tree 混入 build artifacts
- [x] 統一 API 錯誤處理與回傳格式，避免前後端對錯誤訊息的解讀不一致
- [x] 修正 `RequestValidationError` payload 序列化，確保欄位驗證失敗穩定回傳 `422`，不再因 `ctx.error = ValueError(...)` 變成 `500`
- [x] 將 `identifier` 規格全面對齊後端現行規則：同步更新 backend tests、frontend tests、CSV 範本、頁面文案與文件，移除 `202606` 類舊示例

#### P1 - 中優先
- [x] 統一各頁面的表單編輯體驗，讓新增 / 編輯 / 取消編輯的操作邏輯一致
- [x] 強化錯誤提示內容，讓使用者知道是欄位驗證失敗、權限不足、還是後端查詢失敗
- [x] 補齊 loading / empty / no-result 狀態，特別是查詢頁與維護頁
- [x] 統一表格操作列的按鈕順序與樣式，例如編輯、刪除、停用的排列方式
- [x] 抽出共用 UI 元件，像是區塊卡片、操作列、確認對話框、表單標題
- [x] 調整收退料頁的常用操作優先順序，讓單筆新增、批次匯入、最近操作分區更清楚
- [x] 用更直觀的視覺方式呈現產能狀態，例如顏色、進度條、警示標籤
- [x] 讓資料維護頁的啟用 / 停用、可用 / 不可用狀態更一致、更容易辨識
- [x] 再整理一次手機版與小螢幕版布局，特別是 top nav、表格操作列、表單寬度
- [x] 修正 `get_model_query` 的 `max_open_station_count` 摘要算法，改為反映整個機種查詢結果的真實瓶頸值，並補多站點測試
- [x] 將 DB migration / 預設 admin bootstrap 從 app startup 拆成明確的 deploy/bootstrap 流程，降低多 instance 啟動副作用

#### P2 - 次優先
- [x] 抽出日期格式化、欄位 fallback、狀態映射等共用工具，降低各頁重複邏輯
- [x] 持續拆分大型頁面，`InventoryPage` / `ProductionPage` / `MasterPage` / `SearchWorkspacePage` / `App.vue` 已拆出主要區塊；剩餘前端結構整理重點改為 `MasterPage` ledger admin flow 與查詢頁可收合篩選區
- [x] 將 `api.ts` 進一步拆成 domain client，讓前端資料存取不再集中在單一大型檔案
- [x] 補更完整的審計資訊，例如誰在什麼時間修改了哪些主資料
- [x] 若資料量持續增加，針對查詢與列表頁開始規劃分頁、索引與查詢效能優化
- [x] 重新整理首頁資訊層級，讓客戶資訊、登入狀態、今日統計、導航區更清楚

### 14) 前端布局優化與 UX 深度改良 (針對 100% 縮放全可視化)

#### P0 - 核心空間優化 (解決 50% 縮放問題)
- [x] **重構主布局柵格**：將 `.inventory-board` 從固定的 `minmax` 寬度改為動態 `1fr` 彈性布局，確保內容依視窗寬度自適應。
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
- [x] 查詢頁治具關聯機種改為直接使用 `fixture_requirements.model_id`，不再從站點反推機種
- [x] 查詢頁治具站點詳細改為顯示 `機種 + 站點 + 所需數量`

### 16) Production 多機種共站模型定案
- [x] `fixture_requirements` 正式改為 `model_id + station_id + fixture_id`
- [x] 同一站點可被多機種共用，但每個機種在該站點的治具需求各自獨立
- [x] `get_station_capacity` 強制要求 `model_id`
- [x] `get_model_query` 支援 `station_id`
- [x] `Fixture Requirement` create/update/import/export 全面帶入 `model_id`
- [x] 產能頁站點下拉只顯示當前機種已綁定站點
- [x] 切換機種後，站點選擇會自動收斂到該機種可用站點
- [x] 查詢頁與產能頁已移除 `station -> model` 執行期反推邏輯

### 17) 新手導覽 / 教學模式

- [x] 新增全域 `GuidedTour` 浮層元件，支援 spotlight、高亮目標與逐步導覽
- [x] 首次登入後自動啟動新手導覽，並以 sessionStorage 記住本次 session 已看過
- [x] 搜尋首頁新增固定「開始新手教學」入口，可隨時重播
- [x] 導覽步驟已涵蓋：搜尋首頁、收退料入口、匯出入口、總檢視、資料維護、產能管理
- [x] 收退料批次匯入元件新增 `tutorialMode`，教學模式下可自動帶入試跑資料
- [x] 教學模式送出收 / 退料時不寫入正式資料，只清空畫面並提示試跑完成
- [x] `MasterPage` 新增「開始新手導覽」按鈕，可從資料維護頁回到導覽起點

### 18) Migration / 啟動穩定性修補
- [x] 新增 Alembic migration `0004_model_station_scope`
- [x] 新增 Alembic migration `0005_remove_warehouse_tables`
- [x] 新增 Alembic migration `0006_identifier_cleanup`
- [x] 新增 Alembic migration `0007_user_customer_scope`
- [x] 新增 Alembic migration `0008_fixture_responsible_user`
- [x] 新增 Alembic migration `0009_remove_owners_and_scope_fixture_code`
- [x] 修正舊 revision id 過長導致 `alembic_version.version_num` 寫入失敗問題
- [x] 啟動前自動放寬 MySQL/MariaDB `alembic_version.version_num` 欄位
- [x] 啟動前自動將舊 revision id `0004_model_station_fixture_requirements` 正規化為 `0004_model_station_scope`
- [x] `fixtures.code` 改為 `(customer_id, code)` 唯一鍵，允許不同客戶使用相同治具代碼
- [x] 舊 `owners` 資料表正式移除，責任人收斂為 `fixtures.responsible_user_id`
- [x] Docker 環境已驗證 migration 可正常完成且 API 可正常啟動

### 19) 測試補強
- [x] 新增 migration preflight 測試
- [x] 新增 production service 測試，覆蓋同站點多機種共用情境
- [x] 新增 production API 測試，驗證同站點多機種共用時 capacity / query 不互相污染
- [x] 新增 auth / customer scope 測試，驗證 `admin` / `guest` / `user` 三種角色行為

### 20) 角色與客戶權限定案
- [x] `admin` 具備完整管理權限，但 customer-scoped 操作仍限 `user_customers` 已指派客戶
- [x] `guest` 不限制客戶可視範圍，但只能讀取
- [x] `guest` 不顯示 `資料維護` 導航，且不可直接進入 `/master`
- [x] `user` 可先建立帳號，再由客戶分頁指派可見客戶
- [x] `user` 可編輯 `fixtures / models / stations`
- [x] `user` 不可管理 `customers / users`
- [x] 所有 customer-scoped API 對已登入的 `admin` / `user` 強制檢查 `customer_id` 與客戶指派
- [x] 使用者分頁不再維護客戶勾選；改由客戶分頁維護 `assigned_user_ids`
- [x] 客戶已指派使用者同時作為該客戶治具的負責人候選名單
- [x] 負責人分頁已移除

## Update Log

### 2026-07-22

- 新增 admin-only 治具永久刪除 API 與資料維護頁操作入口。
- 刪除對話框可選擇：
  - 保留收/退料紀錄：將 transaction item 的 `fixture_id` 設為 `NULL`，並保留 `deleted_fixture_code` / `deleted_fixture_name` 快照。
  - 一起刪除收/退料紀錄：只刪除該治具的 item；父交易沒有其他 item 時才一併刪除。
- 治具刪除會在同一 transaction 內清除 requirement、stock level/summary，並使相關 capacity summary 失效。
- 新增 Alembic `0014_fixture_deletion`，並已在目標 MySQL 完成升級與 schema/backfill 驗證。
- 修正 Alembic URL 中 percent-encoded 密碼會觸發 ConfigParser interpolation 的問題。
- 新增 service/API/migration 測試，覆蓋保留歷史、刪除明細、混合交易與 admin 授權。
- 文件 customer scope 已依現行 backend 校正：admin 仍需被指派到客戶，`manage` 不會繞過 scope。
- 已重新驗證完整後端測試：`86 passed`；frontend production build 亦通過。


### 2026-07-09

- 已將 migration/schema patch 技術債的退場策略正式收斂成三段式：
  - `Phase 1`：保留 compat 邏輯與觀測
  - `Phase 2`：runtime 改為 fail-loud gate，不再靜默修補
  - `Phase 3`：確認所有環境都ผ่าน gate 後，移除 `schema_patch.py` 與 legacy revision normalization
- runtime migration gate 現在要求資料庫 revision 至少達到 `0011_search_indexes`；低於 gate 的環境不再由 startup 自動修正，而是直接拒絕啟動。
- 已新增離線檢查入口：`python -m backend.app.tools.migration_check`
  - 可列出目前 revision、`alembic_version` 狀態、legacy alias / 短欄位 / 無 version table 等問題
  - 可在人工確認後加上 `--apply-compat-fixes`，顯式套用舊版 `alembic_version` 相容修補
- runtime gate 現在會固定輸出 structured log event：`migration_runtime_gate`
  - `outcome=passed`
  - `outcome=blocked`
  - `outcome=compat_fixes_applied`
- 已補上 backend logging bootstrap：`backend/app/core/logging.py`
  - standalone CLI 現在會把 `backend.app` 的 `INFO` log 接到 stdout
  - app runtime 若已有既有 handler，則不覆蓋，只把 `backend.app` logger 拉到 `INFO`
- 已新增環境盤點文件：
  - `MIGRATION_GATE_RUNBOOK.md`
  - `MIGRATION_ENVIRONMENT_INVENTORY.md`
- 已確認目前已知環境分流：
  - 測試機：`docker`
  - 正式機：`systemd`
  - 兩者需作為獨立 environment entries 追蹤，不共用 revision 與 gate log 狀態
- `schema_patch.py` 現在文件定位已收斂為 `0002_schema_backfill` 的歷史 backfill 依賴，不再視為 runtime startup 的保底機制。
- 已補上 migration gate 單元測試，覆蓋：
  - fresh DB 無 `alembic_version` 仍可通過 runtime gate
  - legacy alias revision 會被 fail-loud 擋下
  - 有 app tables 但沒有 `alembic_version` 的 legacy schema 會被 fail-loud 擋下
- 目前仍未完成的前置條件：
  - 尚未在 repo 內填入所有已知部署環境的 inventory 實際資料
  - 尚未累積 `N` 次連續 `passed` 的 deploy 證據
  - 因此還不能宣告 `schema_patch.py` 已達可刪除條件
- 已重新驗證：
  - `backend/tests/test_migrations.py`

- 已在真實 Docker 測試部署驗證 logging 修復與 gate 事件落地：
  - `docker compose exec -T api python -m backend.app.tools.migration_check` -> `status: runtime migration gate passed`
  - `docker logs fixture_m_lite_api 2>&1 | grep migration_runtime_gate` 可直接撈到 JSON event
  - 事件內容為：
    - `source=app_startup`
    - `outcome=passed`
- 已將這次實測結果寫回 `MIGRATION_ENVIRONMENT_INVENTORY.md`
  - `test-docker-01`
  - `Manual Baseline Count = 0`
  - `Deploy Triggered Passed Count = 1`

- 已將搜尋頁主查詢改成 page-based contract：`GET /api/v2/search/global` 現在支援 `entity_type`、`page`、`page_size`，回傳 `items / total / page / page_size / has_more`。
- 已將搜尋頁前端改成 `load more` 模式，不再在首頁一次預載完整 fixture / model / station / transaction context。
- 已新增 `GET /api/v2/search/fixtures/{fixture_id}/context` 與 `GET /api/v2/search/models/{model_id}/context`，治具 / 機種 detail 現在改成選取後延遲載入。
- 已把搜尋結果排序 contract 收斂到 `backend/app/repositories/search_repository.py`，目前採 active first + exact/prefix/contains ranking。
- 已補上搜尋流量相關索引 migration：`backend/alembic/versions/0011_search_indexes.py`，覆蓋 `fixtures.storage_location`、`machine_models.name`、`stations.name`、`material_transactions.occurred_at`。
- 已補上搜尋分頁與 lazy context 的 API 測試，並驗證：
  - `tests/test_inventory_and_production.py`
  - `backend/tests/test_services.py`
  - `frontend/npm run build`

- 已新增前端共用 `identifier` helper：`frontend/src/utils/identifier.ts`。
- helper 目前提供：
  - `isStrictIdentifier`
  - `normalizeIdentifierForWrite`
  - `resolveIdentifierQuery`
- `frontend/src/components/inventory/BatchImportPanel.vue` 已改走這份 helper，不再在元件內自行維護短純數字補零規則。
- 已新增 `frontend/src/utils/identifier.test.ts`，獨立覆蓋：
  - 短純數字補零
  - legacy 值原樣保留
  - 空字串回傳空值
  - query helper 的短碼展開與 legacy 原值匹配
- 已重新驗證：
  - `frontend/npm run test -- src/utils/identifier.test.ts`
  - `frontend/npm run build`

- 已將 `identifier` 寫入 / 查詢規則正式抽出為獨立 utility：`backend/app/utils/identifier_rules.py`。
- utility 目前提供：
  - `is_strict_identifier`
  - `normalize_identifier_for_write`
  - `resolve_identifier_query`
- `backend/app/schemas/inventory.py` 與 `backend/app/services/inventory_service.py` 現在都改走這份共用規則，不再各自維護一段 `identifier` 判斷。
- 已新增 `backend/tests/test_identifier_rules.py`，獨立覆蓋：
  - 短純數字補零
  - 長純數字 legacy 保留
  - 含非數字 legacy 保留
  - 空值驗證
  - 查詢時短純數字的零補齊展開
  - 查詢時 legacy 值的原值精確匹配
- 已重新驗證：
  - `backend/tests/test_identifier_rules.py`
  - `backend/tests/test_services.py`
  - `tests/test_inventory_and_production.py`
  - `frontend/npm run build`

- 已將前端新手導覽從單一路徑改為可分類選擇的 flow，使用者現在可依頁面 / tab 自行選擇要看的教學，不必重播整套長導覽。
- 已新增 `frontend/src/components/common/OnboardingFlowPicker.vue`，並由 `App.vue` 協調分類選單與實際 `GuidedTour` 的切換。
- 已補強收退料與產能頁教學文案，明確說明：
  - 收退料批次貼上支援的格式
  - 收料遇到未建治具時的 `needs-confirm / needs-add` 處理方式
- 產能頁 UI 已改成以 `站點設定` 與 `治具需求` 呈現；新增治具需求時不再要求先手動建立 `Model-Station Mapping`
- 已為 `ProductionDetailSection.vue` 補上 onboarding 用的 `data-tour` anchor，讓 mapping / requirement 表單與列表可被精準對位。
- 已修正導覽偏移問題：
  - `GuidedTour.vue` 改為依實際卡片高度定位，不再使用固定高度估算
  - 收退料教學 target 改為限定抓 modal 內的 `data-tour` 節點，避免和 `/inventory` 頁內的同名 target 撞到
  - `OnboardingFlowPicker.vue` 改為真正置中顯示
- 已將 `frontend/src` 內所有使用者可見的 `識別碼` 文案安全替換為 `datecode/編號`，但未更動任何 `identifier` 程式契約、API 參數、型別或資料庫欄位。
- 已重新驗證 `frontend\\npm run build` 通過。

### 2026-07-08

- 已修正 `frontend/src/components/inventory/BatchImportPanel.vue` 的批次內容輸入行為：在收退料批次貼上欄位按 `Tab` 時，現在會插入真正的 tab 字元，不再直接跳出欄位，便於手動輸入 `fixture-code[TAB]identifier[TAB]quantity` 格式。
- 已修正 `frontend/src/releaseNotice.ts` 物件結構錯誤，補回 `summary` 並清掉壞掉的 `title/highlights` 語法，版本公告設定重新回到合法的 `ReleaseNotice` 型別。
- 已重新驗證 `frontend\\npm run build` 通過。
- 已同步更新 `ARCHITECTURE.md`、`ARCHITECTURE_LANDING.md`、`frontend-map.md`、`backend-map.md`、`map.md`，補上版本公告定位與收退料批次貼上 `Tab` 行為說明。

### 2026-07-27

- 已新增收退料總檢視分頁 API：
  - backend 新增 `GET /api/v2/inventory/transactions/overview`。
  - response contract 為 `items / page / page_size / total`，每列直接對應單一 transaction item，而不是先回 parent transaction 再由前端展開。
- `InventoryPage.vue` 已把 `/inventory/overview` 改接上述分頁 API：
  - route query 會保留 `transaction_type / date_from / date_to / fixture_code / transaction_no / tracking_code / created_by / page / page_size`。
  - 若從其他頁面帶 `return_to` 進來，總檢視頁會顯示 `返回來源`。
- `InventoryOverviewPanel.vue` 已補齊：
  - `共幾筆 / 第幾頁` 提示
  - `50 / 100` 每頁切換
  - 指定頁碼跳轉
  - sticky table header
- `BatchImportPanel.vue` 已補兩個新行為：
  - 可接收預填治具代碼，讓 topbar / 查詢頁可直接把單一治具帶進批次 modal。
  - 送出前會把同批內相同 `fixture_id + identifier` 的 ready 列合併，避免重複 item 只在前端預覽累計、實際 payload 卻仍拆多列。
- `App.vue` / `AppGlobalModals.vue` / `BatchImportPanel.vue` 已把 modal 草稿保護收斂成單一路徑：
  - `關閉`
  - `Esc`
  - `收退料總檢視`
  都會先檢查未送出草稿，再決定是否真的離開。
- `BatchImportPanel.vue` 現在會把全域 modal 草稿暫存到 `sessionStorage`；同客戶下重新打開 modal 時會自動恢復。
- `App.vue` / `appState.ts` 已把 shell-level 狀態再往前收斂：
  - session 與 selected customer 直接由 `sessionStorage` 還原
  - 新增 `customerSwitchGuards`
  - 新增 `requestInventoryBatchOpen()` 供其他頁面直接要求打開全域收退料 modal
- `AppTopbar.vue` 的低水位列表已支援直接對單一治具開 `收 / 退料`；`AppGlobalModals.vue` 會把該治具代碼傳給共用 `BatchImportPanel.vue`。
- `SearchWorkspacePage.vue` 已補 route restore 與 dirty guard：
  - 支援 `mode / q / page / selected_id / detail`
  - fixture / model 編輯中離頁、切查詢模式、換結果或重整頁面前都會先確認
  - fixture detail 的歷史動作改為導向 `/inventory/overview`，並只保留 `fixture_code + return_to`
- `FixtureInfoPanel.vue` 已改成兩個明確動作：
  - `以此治具收 / 退料`
  - `到總檢視看完整歷史`
- `ProductionPage.vue` / `ProductionDetailSection.vue` 已把 configure flow 再收斂成單一工作區：
  - operator-facing 文案改成 `站點設定`
  - 上方站點清單可直接帶動下方 requirement station 選擇
  - requirement 建立 / 更新時若缺底層 `model_station`，後端 `ProductionService` 會自動補建
- `FixtureQualityPanel.vue` 與 backend quality report 已對齊新的儲位語意：
  - `沒有儲位 / 沒有最低水位` 仍可列內修正
  - 但 `missing_storage_location` 現在只會在 `產線儲位` 與 `部門儲位` 都缺時才成立
- onboarding 文案已同步改成目前實作：
  - `收退料明細匯出` 改為全域 `匯出中心`
  - `產能設定與治具需求` 改成同頁連續操作，而不是先切 Mapping 再切 Requirement

### 2026-07-16

- 已把 `MasterPage` 分頁正式拆成獨立 URL：
  - `/master/fixtures`
  - `/master/models`
  - `/master/stations`
  - `/master/customers`
  - `/master/users`
  - `/master/ledger`
  - `/master/quality`
  - `/master` 會自動導向 `/master/fixtures`。
- `MasterPage.vue` 現在會依路由反向同步 tab state，因此直接貼網址也能打開正確分頁。
- `治具資料品質` 的問題跳轉規則已改成依 issue code 分流：
  - `沒有儲位`、`沒有最低水位`：直接在品質表列內修正並送出。
  - `沒有圖片`：不跳轉。
  - `沒有任何機種關聯`：跳到 `產能管理 / 治具需求`。
- `SearchWorkspacePage.vue` 已支援從 query string 接收 `mode` 與 `q`，供品質頁等跨頁流程直接帶入搜尋條件。
- 已重新驗證：
  - `frontend\npm run build` -> pass

- 已新增 admin-only 的 `治具資料品質` 分頁與品質報表 API：
  - backend 新增 `GET /api/v2/master/fixtures/quality?customer_id=...`。
  - 檢查項目目前包含：沒有名稱、沒有儲位、沒有圖片、沒有最低水位、沒有任何機種關聯、`Identifier` 庫存與總庫存不一致。
- `FixtureQualityPanel.vue` 已支援三個操作：
  - 針對 `沒有儲位 / 沒有最低水位` 的列，直接在表格內編輯並更新。
  - 依單一問題類型篩選異常列。
  - 匯出目前篩選結果為 `fixture-quality-report.csv`。
- 已新增 backend 測試，驗證品質報表能抓出上述六類問題。
- 已重新驗證：
  - `.venv\Scripts\python -m pytest backend\tests\test_services.py -q` -> `27 passed`
  - `frontend\npm run build` -> pass

- 已在收退料送出流程補上「2 分鐘重複交易防呆」：
  - 比對條件為同一使用者、相同交易類型、相同單號，以及完全相同的 `治具 + identifier + 數量 + ownership_type` 明細集合。
  - 後端若判定為重複送出，會回 `409` 與確認訊息；前端會顯示確認視窗，讓使用者決定是否重送。
  - 即使使用者確認重送，`transaction_no` 仍維持唯一；若沿用相同單號，後端會回明確錯誤訊息要求修改單號。
- 已同步更新前端 API 與批次匯入流程：
  - `frontend/src/api/core.ts` 新增可讀取 `status` 的 `ApiRequestError`。
  - `frontend/src/api/inventoryClient.ts` 新增 `createReceiptWithOptions()` / `createReturnWithOptions()`，支援 `confirm_duplicate=true`。
  - `BatchImportPanel.vue` 現在會處理 `409` 重複交易回應，先顯示確認提示，再決定是否重送。
- 已修正查詢頁搜尋後的自動定位：
  - `SearchWorkspacePage.vue` 改為在結果區真正渲染完成後再計算 scroll target。
  - 新增 `最近收 / 退料治具` 區塊後，搜尋結果不再停在半路，會更穩定地落到結果框位置。
- 已重新驗證：
  - `.venv\Scripts\python -m pytest backend\tests\test_services.py -q` -> `26 passed`
  - `frontend\npm run build` -> pass

- 已新增 `logs/audit.log` 檔案型審計紀錄，目標是補齊「所有人做過的所有動作」的落地追蹤能力。
- 已在 FastAPI app 掛上全域 middleware，所有進入後端的 HTTP request 都會寫入 `request_audit`：
  - `timestamp`
  - `actor.mode / user_id / username / display_name / role`
  - `request.method / path / query / client_ip`
  - `response.status_code / duration_ms`
  - `error`
- 已保留原本資料庫 `audit_logs` 表的業務審計能力，並讓 `AuditService.record()` 同步追加寫入 `logs/audit.log`，事件型別為 `domain_audit`。
- 已新增可配置項：
  - `LOG_DIR`，預設為 `logs`
  - `AUDIT_LOG_FILENAME`，預設為 `audit.log`
- 已新增後端測試覆蓋：
  - audit file 會自動建立
  - middleware 會把已登入/訪客 session 與 request metadata 寫入 audit file
- 已重新驗證：
  - `.venv\\Scripts\\python.exe -m pytest backend\\tests\\test_migrations.py -q` -> `14 passed`
  - `.venv\\Scripts\\python.exe -m pytest backend\\tests\\test_services.py -q` -> `24 passed`
- 已新增收退料批次預覽的 `目前庫存` 與 `交易後庫存` 欄位。
- `交易後庫存` 目前以 `identifier` 維度計算，並在同一批次內按列順序累計，避免預覽結果與實際送出不一致。
- 已新增前端 helper 與測試：
  - `frontend/src/utils/inventoryBatchPreview.ts`
  - `frontend/src/utils/inventoryBatchPreview.test.ts`
- 已將登入後版本更新提示收斂為「同一版本在同一台瀏覽器只顯示一次」。
- 已更新本次版本公告內容，說明：
  - 收退料預覽新增 `目前庫存`
  - 收退料預覽新增 `交易後庫存`
  - audit log 已落地到 `logs/audit.log`
- 已將查詢首頁 `相近編號` 提示卡改為可收合 UI，查到結果後可先收起，不影響搜尋結果與 detail 區。
- 已重新驗證：
  - `frontend\\npm run build` -> pass
  - `frontend\\npm test -- src/utils/inventoryBatchPreview.test.ts` -> `3 passed`

### 2026-07-07

- 已把 `identifier` 規則正式拆成「寫入規則」與「查詢相容規則」：
  - 新增 / 匯入寫入仍只接受 1-4 位數字，並在寫入前左補零為 4 碼。
  - 收退料查詢、匯出與總檢視篩選則需相容舊資料庫：輸入 1-4 位數字時，同時匹配 `1 / 01 / 001 / 0001` 類零補齊變體；輸入超過 4 碼或含非數字時，則以 legacy `identifier / datecode` 原值查詢。
- 已修正 `RequestValidationError` payload 的 JSON-safe 序列化，避免 `ctx.error = ValueError(...)` 再把欄位驗證錯誤升級成 `500`。
- 已補上 backend 測試，涵蓋：
  - `max_open_station_count` 以機種整體瓶頸值摘要
  - 舊資料庫 numeric identifier 不同零補齊寬度的相容查詢
  - legacy `2024W12` 類 identifier/datecode 的查詢與匯出相容
- 已把 `ExportCenterPanel`、`InventoryPage` 篩選 placeholder 與 onboarding 文案更新為相容規則，不再把使用者導向必定失敗的 `Datecode` 輸入格式。
- 已將 `InventoryPage` 拆成較薄的頁面容器，並抽出：
  - `frontend/src/components/inventory/InventoryOperationBoard.vue`
  - `frontend/src/components/inventory/InventoryOverviewPanel.vue`
- 已將 `ProductionPage` 的頁首 / detail 編輯區進一步拆出，頁面本體改為較薄的資料容器，並抽出：
  - `frontend/src/components/production/ProductionHeaderSection.vue`
  - `frontend/src/components/production/ProductionDetailSection.vue`
- 已將 `ProductionPage` 的批次貼上匯入 modal shell 進一步抽出為：
  - `frontend/src/components/production/ProductionBatchImportModal.vue`
- `ProductionPage` 的批次解析、相似比對與提交邏輯目前仍保留在頁面層，先把 modal shell 抽離，下一步再視需要把 batch domain logic 拆到 composable 或 service helper。
- 已將 `MasterPage` 的 list / detail 編輯區抽成獨立元件，頁面本體改為以資料載入與 CRUD 為主，並抽出：
  - `frontend/src/components/master/MasterListPanel.vue`
  - `frontend/src/components/master/MasterDetailPanel.vue`
- 已再往上抽出跨頁共用 UI 結構，先集中收斂高重複率區塊：
  - `frontend/src/components/UiSummaryCards.vue`：統一 `Inventory` / `Master` 的摘要卡片列 rendering 與響應式欄位配置
  - `frontend/src/components/UiSectionHeader.vue`：統一 `Master` / `Production` 多個 panel header 的標題 + 說明 + actions 結構
- 已將 `SearchWorkspacePage` 的外層頁面結構拆出：
  - `frontend/src/components/search/SearchHeroSection.vue`
  - `frontend/src/components/search/SearchResultPanel.vue`
- `SearchWorkspacePage` 目前保留查詢狀態、選取邏輯與資料彙整；hero / result shell 已抽離，但內層 `FixtureInfoPanel` / `ModelInfoPanel` 的獨特視覺語言仍維持獨立，避免過度抽象後讓查詢頁失去辨識度。
- 已將 `App.vue` 的 shell UI 進一步拆出，讓頁面本體只保留 session、route、onboarding 與全域資料刷新協調：
  - `frontend/src/components/app/AppAuthScreen.vue`
  - `frontend/src/components/app/AppTopbar.vue`
  - `frontend/src/components/app/AppMobileDrawer.vue`
  - `frontend/src/components/app/AppGlobalModals.vue`
  - `frontend/src/components/app/AppToastStack.vue`
- 已同步清掉 `App.vue` 搬遷後殘留的 topbar / mobile drawer / toast scoped style 死碼，避免只是搬檔但沒有真正降低頁面密度。
- 已將一批跨頁重複 CSS 抽回全域 `frontend/src/styles.css`，集中收斂：
  - 共用按鈕尺寸 utility，如 `btn-sm`
  - 共用 modal shell，如 `ui-modal-backdrop` / `ui-modal-card`
  - 共用 detail layout / panel card / section head / chip / info table 樣式
- 已新增 `frontend/src/components/UiSplitDetailLayout.vue`，把查詢頁 `FixtureInfoPanel` / `ModelInfoPanel` 的 summary rail + detail scroll 外殼抽成共用元件。
- 已讓 `FixtureInfoPanel` / `ModelInfoPanel`、`AppGlobalModals`、`ProductionBatchImportModal`、`AppAuthScreen`、`AppTopbar`、`AppMobileDrawer`、`FixtureEditForm`、`ModelEditForm` 改接全域 utility，移除重複的 local button / modal / layout CSS。
- 已再往下補齊兩種高重複率變體 utility，避免 `MasterPage` / `BatchImportPanel` 各自維護一份按鈕與狀態樣式：
  - `btn-compact`：緊湊型工具列按鈕
  - `status-pill.batch-state` 與 `ready / needs-confirm / needs-add / error / skipped`：批次匯入狀態膠囊
- 已將 `MasterPage` 的 toolbar 改接 `btn-compact`，並清掉頁面層殘留的 dead button / status CSS。
- 已將 `BatchImportPanel` 的 batch row action、accent submit/ghost button、status pill 改接共用 utility，只保留 panel accent 變體本身。
- 已將 `ExportCenterPanel` 收斂到專案主流藍白配色，header pill、filter card、preview chip 與操作按鈕已與全站主色一致。
- 已將 `frontend/src/api.ts` 從單一大型實作檔收斂為穩定 barrel 入口，對外仍維持 `import { api } from "@/api"` 不變；內部則拆成：
  - `frontend/src/api/core.ts`
  - `frontend/src/api/authClient.ts`
  - `frontend/src/api/masterClient.ts`
  - `frontend/src/api/inventoryClient.ts`
  - `frontend/src/api/productionClient.ts`
  - `frontend/src/api/searchClient.ts`
  - `frontend/src/api/auditClient.ts`
  - `frontend/src/api/mediaClient.ts`
- 這次 `api.ts` 拆分只做到 domain client 層，不再往更細碎的 function-per-file 方向切，避免過度抽象後降低可發現性；transport/error handling 仍集中在 `core.ts`。
- 已在查詢首頁補上「最近收 / 退料治具」快捷入口，預設顯示 5 個唯一治具代碼，並提供「顯示更多 / 收合」按鈕；點擊任一快捷入口後會自動切到治具模式並帶入對應查詢，降低現場重複查同一批剛收/退料治具的操作成本。
- 已同步讓治具查詢結果內的「最近收退料」表格保留較大的近期資料池，預設顯示 8 筆，並提供「顯示更多 / 收合」按鈕，避免明細區只看得到極少數交易。
- 已將治具查詢結果內的 `查看更多` 接到真正的歷史查詢流程：點擊後會依 `fixture_code` 額外載入該治具更完整的收退料歷史，而不只是把首頁預載的近期交易池展開。
- 已同步讓 `BatchImportPanel` 支援外部受控 `mode`，避免頁面外層分段切換與批次匯入元件內部模式脫鉤。
- 已將 app startup 內的 migration / default admin side effect 保持移除，並補上明確 launcher：
  - `main.py` 直接啟動時會先執行 bootstrap 再啟動 uvicorn
  - Docker image 預設改走 `python main.py`
  - `docker-compose` 的 `api` service 顯式關閉 `BOOTSTRAP_BEFORE_RUN`，仍由獨立 `bootstrap` service 先初始化，避免重複 bootstrap
- 已驗證：
  - `.venv\\Scripts\\python.exe -m pytest -q` -> `33 passed`
  - `frontend\\npm run build` -> pass
  - `tests\\test_inventory_and_production.py -q` -> `3 passed`

### 2026-07-04

- 已確認 review open questions 的決策：
  - `identifier` 以後端現行規則為準，只接受 1-4 位數字，並於寫入前左補零為 4 碼。
  - `auth token` 風險接受前提為「系統只跑在受信任內網」，因此 `sessionStorage + Bearer token` 暫不列為本輪必要整改。
- 已依上述決策把當前必要修正重排優先級：
  - `P0`：修正 validation error payload 序列化；全面對齊 `identifier` 規格與測試/範本/文件。
  - `P1`：修正 `get_model_query` 摘要產能算法；拆除 startup 內的 migration / bootstrap 副作用。
  - `P2`：持續拆分大型前端頁面與 `api.ts` / shell 模組。
- 已重新同步 `task.md`、`ARCHITECTURE.md`、`frontend-map.md`、`backend-map.md`、`map.md`、`ARCHITECTURE_LANDING.md`，讓文件描述對齊目前 topbar shell、全域收退料/匯出 modal、onboarding 導覽與教學模式。
- 已在文件中補上 `GuidedTour`、`frontend/src/onboarding.ts`、`ExportCenterPanel.vue`、搜尋頁「相近編號」提示收斂等最新前端結構。
- 已確認 `requirements.txt` 原本就包含 `openpyxl`；本次已補安裝到目前 `.venv`，排除測試因缺套件而在 import 階段直接失敗的問題。
- 已重新驗證 `npm run build` 通過。
- 已重新驗證 `.venv\\Scripts\\python.exe -m pytest tests -q`，目前結果為 `4 passed, 1 failed`。
- 目前剩餘失敗案例集中在 `tests/test_inventory_and_production.py::test_inventory_capacity_and_search_flow`：`identifier = "202606"` 仍被限制為 4 碼內，且 validation error payload 的 `ctx.error` 仍含未序列化的 `ValueError`。

### 2026-06-27

- 已重新對照目前程式碼校正文檔，確認 `ARCHITECTURE.md` 與 `task.md` 不再把「最近異動側欄卡片」與「桌面 mini sidebar」視為已落地現況。
- 已補記目前測試現況：`.venv\\Scripts\\python.exe -m pytest tests -q` 尚有 1 個失敗案例，集中在 `identifier` 驗證與 validation error 序列化。

### 2026-06-20

- 已修正首頁左側側邊欄右側的白邊問題，收斂 scrollbar 預留空間與滾動區背景，避免主內容區左側出現視覺縫隙。
- 已將前端共用日期格式化工具統一為只顯示 `年月日`，不再顯示時分秒。
- 已將首頁側邊欄顯示文案由 `時間` 調整為 `日期`，並只呈現當日日期。
- 已將 `收退料總檢視`、`資料維護`、`查詢頁`、`產能頁` 中所有建立/更新/交易日期顯示統一改為 `年月日`。
- 已將後端 API 的 `datetime` 回應序列化統一收斂為 `YYYY-MM-DD`，避免前端再收到帶時分秒的日期字串。
- 已將收退料 CSV 匯出的 `occurred_at` 與範本日期格式統一改為 `YYYY-MM-DD`。
- 已將收退料建立交易與 CSV 匯入流程收斂為「只記錄日期」：即使輸入帶時分秒，也會在寫入前正規化為當日零點。
- 已補齊 `資料維護` 頁的停用資料恢復流程，`治具 / 機種 / 站點 / 使用者` 現在都可從停用狀態恢復使用。
- 已讓 `資料維護` 頁的狀態篩選一致套用到 `治具 / 機種 / 站點 / 使用者` 清單，便於找到停用資料後重新啟用。
- 已將 `資料維護` 頁底部動作按鈕改為依當前狀態動態顯示 `停用 / 恢復使用`，不再只有單向停用途徑。

### 2026-06-15

- 已將 production requirement 的正式資料模型定案為 `model_id + station_id + fixture_id`。
- 已將 production 展開與計算邏輯定案為：
  - `機種 -> 機種已綁定站點 -> 該機種該站點的治具需求`
- 已修正 production 頁站點選擇邏輯，切換機種後不再保留無效 `station_id`。
- 已修正 production 頁 requirement 清單過濾，改為 `model_id + station_id`，不再只看 `station_id`。
- 已修正查詢頁治具關聯機種與站點詳細，不再從站點反推機種。
- 已將 production capacity UI 改為單站獨立語意，不再展示誤導性的「目前開站 / 剩餘開站」資訊。
- 已將 `current_open_station_count` 從 backend schema / service、frontend types / page props / UI 中正式移除。
- 已修正 Alembic `0004` revision id 過長造成的 MySQL `alembic_version.version_num` 寫入失敗問題。
- 已將 migration revision 正式收斂為 `0004_model_station_scope`，並補上 legacy revision alias normalization。
- 已驗證 docker compose 下的 API 與 Web 可正常重建與啟動。
- 已修正批次收退料自定義單號不生效問題，後端現在會保留使用者輸入的 `transaction_no`。
- 已新增 migration 測試與 production API / service 測試，特別覆蓋「同站點多機種共用」情境。
- 已移除 warehouse 相關資料表，正式收斂為 `fixtures.storage_location` 單一文字儲位策略。
- 已新增 Alembic `0006_identifier_cleanup`，將 `material_transaction_items` 正式改為 `identifier` 欄位，並移除 legacy `manage_type / datecode / serial_number` 與 `fixture_serials`。
- 已將客戶可見範圍維護入口從使用者分頁移到客戶分頁，改由 `assigned_user_ids` 管理 `user_customers`。
- 已將治具負責人收斂為客戶已指派使用者，並移除前端負責人分頁與對應 API 使用。
- 已新增 Alembic `0007_user_customer_scope`，將一般使用者的客戶可見範圍正式落到 `user_customers`。
- 已新增 Alembic `0008_fixture_responsible_user`，在 `fixtures` 補上 `responsible_user_id`。
- 已新增 Alembic `0009_remove_owners_and_scope_fixture_code`，移除 `owners` 並將治具代碼唯一鍵收斂為 `(customer_id, code)`。

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
- 已於後續 migration 正式移除 `manage_type / datecode / serial_number` 與 `fixture_serials`，資料庫也改成單一 `identifier`。
- 已重構查詢頁為 `治具 / 機種` 兩種模式，並加入固定統計方格。
- 已讓查詢頁改為面板內滾動，避免內容超出頁面高度。
- 已依圖片移除查詢頁右側重複的治具名稱卡片。
- 已驗證 `npm run build` 與 `python -m compileall backend/app` 通過。

### 2026-06-11

- 已將 `MasterPage` 與 `ProductionPage` 補上載入中提示與空狀態列，避免資料尚未載入或清單為空時畫面顯得像壞掉。
- 已將 `MasterPage` 的主要操作按鈕在載入中鎖定，降低切換客戶或重整時的誤操作。
- 已將 `ProductionPage` 的查詢/匯入/更新操作在載入與儲存中鎖定，避免表單與資料刷新互相打架。
- 當時曾規劃將 `SearchWorkspace` 的篩選區改成可收合；目前程式碼中尚未保留這個互動。
- 已把 `ProductionPage` 的 Station Capacity 改成進度條 + 狀態標籤呈現，讓產能是否接近上限更容易一眼看懂。
- 已將 `ProductionPage` 兩個表格的操作列包成一致的動作區塊，統一編輯 / 刪除的排列方式。
- 已將前端錯誤訊息解析強化為可讀的欄位驗證/後端錯誤訊息，避免只看到模糊的 request failed。
- 已在 `MasterPage` 的編輯區加上目前狀態徽章，讓資料維護頁的啟用 / 停用狀態更一致也更醒目。
- 已將收退料頁的批次匯入區收合為次要作業，並補上明確的優先級提示，讓單筆收退料與最近操作更突出。
- 已補上前端共用顯示工具，集中處理欄位 fallback 與狀態文字，減少頁面內重複字串與映射邏輯。
- 已抽出共用 `StatusPill` 元件，並在 `MasterPage`、`ProductionPage`、`InventoryPage` 內共用使用。
- 已抽出共用 `UiFormActions` 元件，讓主檔與產能頁的新增 / 編輯 / 取消 / 儲存動作列統一。
- 已新增 `audit_logs` 與 `/audit/logs`，將主資料異動、使用者更新與匯入事件納入審計記錄。
- 已完成 `audit_logs` 與 `/audit/logs` 後端能力；目前首頁側欄沒有渲染最近異動卡片。
- 已將全站主要按鈕配色統一為綠色儲存、灰色取消、紅色停用/刪除。
- 已將 `MasterPage` 清單補上分頁；`SearchWorkspace` 查詢結果目前尚未分頁。
- 已把 `ProductionPage` 的 Station Capacity / Model Query 區塊拆成獨立元件，降低單一頁面的程式碼密度。
- 目前首頁側欄支援 mobile overlay 開關；桌面版 mini mode 尚未保留。
- 已將收退料頁主布局改為頂部摘要列 + 左中右三欄配置，並把批次貼上匯入改為 modal。
- 已把收退料操作區改成 segmented control，並補上庫存水位條與批次行動作精簡。
- 已驗證 `frontend` 的 `npm run build` 通過。
- 已將前端表格與 body 字級微調至 12px，並略縮 cell padding，提升工業管理場景下的資訊密度。
- 舊的單筆表單自動聚焦調整不再適用，因目前流程已收斂為批次貼上匯入。

### 2026-06-10

- 已補上前端 Vitest 測試骨架，並新增共用 helper 的 unit tests。
- 已將前端日期格式化與 API 錯誤訊息解析抽成共用 util，減少重複邏輯。
- 已補上查詢頁與收退料頁的空狀態 / 載入狀態回饋，讓資料不足時的 UI 更清楚。
- 已將收退料頁的庫存列表補上空狀態提示。
- 已將收退料頁的左側操作區加寬，並把「最近收料 / 退料」區塊提前到批次匯入前面，降低使用時的垂直捲動壓力。
- 已補上 backend unittest，覆蓋 auth / role、API error payload、inventory、production 核心流程。
- 已將 frontend 測試擴充到共用 util 層，驗證日期格式化、API 錯誤解析與治具圖片 URL 組裝。

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
