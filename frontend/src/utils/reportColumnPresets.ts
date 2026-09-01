export type ReportColumnKey =
  | "index"
  | "customer"
  | "fixtureCode"
  | "fixtureName"
  | "stockQty"
  | "customerSuppliedQty"
  | "selfPurchasedQty"
  | "minStockQty"
  | "waterStatus"
  | "lineStorage"
  | "departmentStorage"
  | "modelCode"
  | "station"
  | "requiredQty"
  | "maxOpenStationCount"
  | "configurationStatus";

export type ReportColumnPresetKey = "floorStock" | "configurationCheck" | "full";

export const REPORT_COLUMN_DEFINITIONS: Array<{
  key: ReportColumnKey;
  label: string;
}> = [
  { key: "index", label: "序號" },
  { key: "customer", label: "客戶" },
  { key: "fixtureCode", label: "治具代碼" },
  { key: "fixtureName", label: "治具名稱" },
  { key: "stockQty", label: "總庫存" },
  { key: "customerSuppliedQty", label: "客供庫存" },
  { key: "selfPurchasedQty", label: "自購庫存" },
  { key: "minStockQty", label: "最低水位" },
  { key: "waterStatus", label: "水位狀態" },
  { key: "lineStorage", label: "產線儲位" },
  { key: "departmentStorage", label: "部門儲位" },
  { key: "modelCode", label: "機種" },
  { key: "station", label: "站點" },
  { key: "requiredQty", label: "需求數量" },
  { key: "maxOpenStationCount", label: "此治具可支援站數" },
  { key: "configurationStatus", label: "配置狀態" }
];

export const REPORT_COLUMN_PRESETS: Array<{
  key: ReportColumnPresetKey;
  label: string;
  description: string;
  columns: ReportColumnKey[];
}> = [
  {
    key: "floorStock",
    label: "現場庫存",
    description: "總庫存、客供、自購、水位",
    columns: [
      "index",
      "fixtureCode",
      "fixtureName",
      "stockQty",
      "customerSuppliedQty",
      "selfPurchasedQty",
      "minStockQty",
      "waterStatus"
    ]
  },
  {
    key: "configurationCheck",
    label: "配置檢查",
    description: "機種、站點、需求、此治具可支援站數",
    columns: [
      "index",
      "fixtureCode",
      "fixtureName",
      "modelCode",
      "station",
      "requiredQty",
      "maxOpenStationCount",
      "configurationStatus"
    ]
  },
  {
    key: "full",
    label: "完整報表",
    description: "全部欄位",
    columns: REPORT_COLUMN_DEFINITIONS.map((column) => column.key)
  }
];

export function orderReportColumns(columns: Iterable<ReportColumnKey>): ReportColumnKey[] {
  const selected = new Set(columns);
  return REPORT_COLUMN_DEFINITIONS
    .map((column) => column.key)
    .filter((column) => selected.has(column));
}

export function reportColumnPresetKey(
  columns: ReportColumnKey[]
): ReportColumnPresetKey | null {
  const ordered = orderReportColumns(columns);
  return (
    REPORT_COLUMN_PRESETS.find(
      (preset) =>
        preset.columns.length === ordered.length &&
        preset.columns.every((column, index) => column === ordered[index])
    )?.key ?? null
  );
}

export function reportColumnPreset(
  key: ReportColumnPresetKey
): ReportColumnKey[] {
  const preset = REPORT_COLUMN_PRESETS.find((candidate) => candidate.key === key);
  return preset ? [...preset.columns] : [];
}
