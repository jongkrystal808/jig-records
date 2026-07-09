export type ReleaseNotice = {
  versionId: string;
  versionLabel: string;
  title: string;
  summary: string;
  highlights: string[];
};

// Bump versionId whenever a new release note should be shown again.
export const currentReleaseNotice: ReleaseNotice = {
  versionId: "2026-07-08.1",
  versionLabel: "2026-07-08",
  title: "本次更新",
  summary: "本次更新聚焦在治具查詢與收退料資訊的可讀性與操作效率。",
  highlights: [
    "治具查詢的收退料記錄可額外載入更完整的歷史資料，不再只限近期記錄。",
    "搜尋欄新增清空按鈕，清除後會自動回到輸入框。",
    "datecode/編號庫存會將連號壓縮為區間顯示，並補上總數摘要。"
  ]
};
