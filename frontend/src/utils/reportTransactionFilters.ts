import type { TransactionQueryFilters } from "@/types";

export type ReportTransactionMode =
  | ""
  | "today_receipt"
  | "today_return"
  | "range_receipt"
  | "range_return";

export function reportTransactionDateError(
  mode: ReportTransactionMode,
  dateFrom: string,
  dateTo: string
): string {
  if (!mode.startsWith("range")) return "";
  if (!dateFrom || !dateTo) return "請同時選擇起始與結束日期。";
  if (dateFrom > dateTo) return "起始日期不可晚於結束日期。";
  return "";
}

export function buildReportTransactionQuery(
  mode: ReportTransactionMode,
  dateFrom: string,
  dateTo: string,
  today: string
): TransactionQueryFilters | null {
  if (!mode) return null;
  const transactionType = mode.endsWith("receipt") ? "receipt" : "return";
  if (mode.startsWith("today")) {
    return {
      transaction_type: transactionType,
      date_from: today,
      date_to: today
    };
  }
  return {
    transaction_type: transactionType,
    date_from: dateFrom,
    date_to: dateTo
  };
}
