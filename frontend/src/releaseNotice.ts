export type ReleaseNotice = {
  versionId: string;
  versionLabel: string;
  title: string;
  summary: string;
  highlights: string[];
};

// Bump versionId whenever a new release note should be shown again.
export const currentReleaseNotice: ReleaseNotice = {
  versionId: "2026-07-16.1",
  versionLabel: "2026-07-16",
  title: "本次更新",
  summary: "本次更新聚焦在收退料預覽可讀性與系統操作追蹤。",
  highlights: [
    "收退料批次預覽表已新增「目前庫存」與「交易後庫存」，送出前可先確認每筆 identifier 的變化。",
    "同一批內重複出現的治具 + datecode/編號，預覽會按列順序累計交易後庫存，避免和實際送出結果不一致。",
    "系統已新增 audit log，所有 API 操作都會額外寫入 logs/audit.log，方便後續追查。"
  ]
};
