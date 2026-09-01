import type { TransactionOverviewRow } from "@/types";

export function normalizeReportFixtureCode(value: string): string {
  return value.trim().toLocaleUpperCase();
}

export function groupReportTransactionDetails(
  rows: Iterable<TransactionOverviewRow>
): Map<string, TransactionOverviewRow[]> {
  const groups = new Map<string, TransactionOverviewRow[]>();
  for (const row of rows) {
    const fixtureCode = normalizeReportFixtureCode(row.fixture_code);
    if (!fixtureCode) continue;
    const details = groups.get(fixtureCode) ?? [];
    details.push(row);
    groups.set(fixtureCode, details);
  }
  return groups;
}

export type ReportTransactionExportRow<TRow> = {
  reportRow: TRow;
  reportIndex: number;
  detail: TransactionOverviewRow | null;
};

export function expandReportRowsWithTransactionDetails<TRow extends { fixtureCode: string }>(
  reportRows: readonly TRow[],
  detailsByFixtureCode: ReadonlyMap<string, readonly TransactionOverviewRow[]>
): ReportTransactionExportRow<TRow>[] {
  const expandedRows: ReportTransactionExportRow<TRow>[] = [];
  const expandedFixtureCodes = new Set<string>();

  reportRows.forEach((reportRow, reportIndex) => {
    const fixtureCode = normalizeReportFixtureCode(reportRow.fixtureCode);
    const details =
      fixtureCode && !expandedFixtureCodes.has(fixtureCode)
        ? detailsByFixtureCode.get(fixtureCode) ?? []
        : [];
    if (fixtureCode) expandedFixtureCodes.add(fixtureCode);

    if (details.length === 0) {
      expandedRows.push({ reportRow, reportIndex, detail: null });
      return;
    }
    details.forEach((detail) => {
      expandedRows.push({ reportRow, reportIndex, detail });
    });
  });

  return expandedRows;
}
