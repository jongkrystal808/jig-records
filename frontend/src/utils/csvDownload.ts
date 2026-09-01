export function escapeSpreadsheetFormula(value: unknown): unknown {
  return typeof value === "string" && /^[=+\-@]/.test(value) ? `'${value}` : value;
}

function csvCell(value: unknown): string {
  const safeValue = escapeSpreadsheetFormula(value);
  return `"${String(safeValue ?? "").replace(/"/g, '""')}"`;
}

export function downloadCsvRows(filename: string, headers: string[], rows: unknown[][]): void {
  const content = [headers, ...rows].map((row) => row.map(csvCell).join(",")).join("\n");
  downloadCsvText(filename, content);
}

export function downloadCsvText(filename: string, content: string): void {
  const blob = new Blob(["\ufeff", content], { type: "text/csv;charset=utf-8" });
  downloadCsvBlob(filename, blob);
}

export function downloadCsvBlob(filename: string, blob: Blob): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.style.display = "none";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}
