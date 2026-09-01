# Requirement Follow-up Status

最後同步：2026-08-25

這份文件原本是 2026 年 5 月的需求便條。下表已依目前程式碼與 `task.md` 轉成狀態，避免已完成需求繼續被誤認為待辦。

| 原始需求 | 狀態 | 現況 |
|---|---|---|
| 收退料操作與庫存總覽布局 | 已完成 | `/inventory` 提供正式收／退料流程，`/inventory/overview` 提供分頁總檢視；全域 modal 可由 top bar 與治具快捷入口開啟。 |
| 表格匯入與範本下載 | 已完成 | 收退料、治具、機種、站點、站點設定與治具需求已有批次貼上或 CSV 匯入／匯出／範本流程。 |
| 治具儲位 | 已完成 | 現行欄位為 `line_storage_location` 與 `department_storage_location`，可只填其中一欄。 |
| 治具圖片 | 已完成 | 已有單張／批次上傳、替換與預覽；檔案依 `customer_id/fixture_code.ext` 隔離，讀取會驗證 customer scope，永久刪除治具時同步清理圖片。 |
| 收退料總檢視 | 已完成 | 已有 server-side 篩選、分頁、route query 保存與交易明細匯出。 |
| Datecode／serial 分類 | 已完成（設計調整） | API 與資料模型統一使用 `identifier`；純 1–4 位數字會正規化，其餘 legacy datecode／編號保留原值。 |
| 客供／自購 | 已完成 | `ownership_type` 位於 transaction item，收退料、庫存統計、報表篩選與匯出均支援。 |
| 治具最低水位與負責人 | 已完成 | 使用 `min_stock_qty` 與 customer-scoped `responsible_user_id`。 |

## Remaining Item

- 目前這份原始需求清單沒有未完成項目；後續若要新增「只刪圖片、不刪治具」的獨立操作，需另行定義權限與確認流程。

其他進度、歷史決策與未來範圍請分別查看 `task.md`、`ARCHITECTURE.md` 與 `ARCHITECTURE_LANDING.md`。
