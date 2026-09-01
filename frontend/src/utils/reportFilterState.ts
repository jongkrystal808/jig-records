export type ReportFilterState = {
  keyword: string;
  fixtureStatus: string[];
  fixtureId: string;
  stationId: string;
  modelId: string;
  waterStatus: string[];
  storage: string;
  configurationStatus: string[];
};

export type ReportTransactionFilterState = {
  mode: string;
  dateFrom: string;
  dateTo: string;
  ownershipType: string[];
};

const REPORT_FILTER_KEYS: Array<keyof ReportFilterState> = [
  "keyword",
  "fixtureStatus",
  "fixtureId",
  "modelId",
  "stationId",
  "waterStatus",
  "storage",
  "configurationStatus"
];

function normalized(value: string | string[]): string {
  return Array.isArray(value) ? [...value].sort().join(",") : value.trim();
}

function activeOwnership(filters: ReportTransactionFilterState): string {
  return filters.mode ? normalized(filters.ownershipType) : "";
}

function activeDateRange(filters: ReportTransactionFilterState): string {
  if (!filters.mode.startsWith("range")) return "";
  const dateFrom = normalized(filters.dateFrom);
  const dateTo = normalized(filters.dateTo);
  return dateFrom || dateTo ? `${dateFrom}|${dateTo}` : "";
}

export function pendingReportConditionCount(
  draft: ReportFilterState,
  applied: ReportFilterState,
  draftTransaction: ReportTransactionFilterState,
  appliedTransaction: ReportTransactionFilterState
): number {
  let count = REPORT_FILTER_KEYS.filter(
    (key) => normalized(draft[key]) !== normalized(applied[key])
  ).length;

  if (normalized(draftTransaction.mode) !== normalized(appliedTransaction.mode)) count += 1;
  if (activeOwnership(draftTransaction) !== activeOwnership(appliedTransaction)) count += 1;
  if (activeDateRange(draftTransaction) !== activeDateRange(appliedTransaction)) count += 1;
  return count;
}
