import { orderReportColumns, type ReportColumnKey } from "@/utils/reportColumnPresets";

export function effectiveReportColumns(
  selectedColumns: ReportColumnKey[],
  populatedColumns: Iterable<ReportColumnKey>,
  totalRows: number
): ReportColumnKey[] {
  const selected = orderReportColumns(selectedColumns);
  const populated = new Set(populatedColumns);
  if (totalRows <= 0 || populated.size === 0) return selected;

  const effective = selected.filter((column) => populated.has(column));
  return effective.length > 0 ? effective : selected.slice(0, 1);
}

export function autoHiddenReportColumns(
  selectedColumns: ReportColumnKey[],
  effectiveColumns: ReportColumnKey[]
): ReportColumnKey[] {
  const effective = new Set(effectiveColumns);
  return orderReportColumns(selectedColumns).filter((column) => !effective.has(column));
}
