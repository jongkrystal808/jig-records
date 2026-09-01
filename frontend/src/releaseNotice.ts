export type ReleaseNotice = {
  versionId: string;
  versionLabel: string;
  title: string;
  summary: string;
  highlights: string[];
};

// Bump versionId whenever a new release note should be shown again.
export const currentReleaseNotice: ReleaseNotice = {
  versionId: "2026-08-25.1",
  versionLabel: "2026-08-25",
  title: "本次更新",
  summary: "本次更新新增三欄式工作台 UI，並保留 Modern 與 Form 介面自由切換。",
  highlights: [
    "新增工作台 UI：左側快速作業、中間即時結果、右側固定顯示圖片、儲位及機種站點資訊。",
    "Modern UI、Form UI 與工作台 UI 可整套切換，登入使用者也能把任一介面設為個人預設。",
    "大型清單改用後端 50／100 筆分頁與搜尋，匯出則由正式 endpoint 產生完整篩選結果，不再由瀏覽器逐頁收集。",
    "產能機種站點與治具需求支援試算表貼上；送出前會預覽新增、相同、衝突與錯誤，差異需求量必須明確確認才會取代。"
  ]
};
