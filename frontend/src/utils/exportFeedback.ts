import { pushToast } from "@/toastState";
import { downloadCsvBlob, downloadCsvRows } from "@/utils/csvDownload";

export type BlobExportResult = {
  blob: Blob;
  filename: string | null;
  rowCount: number | null;
};

function resolveExportCount(responseCount: number | null, fallbackCount: number): number {
  return responseCount ?? fallbackCount;
}

export function completeBlobExport(
  response: BlobExportResult,
  fallbackFilename: string,
  fallbackRowCount: number
): boolean {
  const rowCount = resolveExportCount(response.rowCount, fallbackRowCount);
  if (rowCount <= 0) {
    pushToast("目前沒有可匯出的資料。", "warning");
    return false;
  }
  const filename = response.filename || fallbackFilename;
  downloadCsvBlob(filename, response.blob);
  pushToast(`已匯出 ${rowCount} 筆：${filename}`, "success");
  return true;
}

export function completeCsvRowsExport(
  filename: string,
  headers: string[],
  rows: unknown[][]
): boolean {
  if (rows.length === 0) {
    pushToast("目前沒有可匯出的資料。", "warning");
    return false;
  }
  downloadCsvRows(filename, headers, rows);
  pushToast(`已匯出 ${rows.length} 筆：${filename}`, "success");
  return true;
}
