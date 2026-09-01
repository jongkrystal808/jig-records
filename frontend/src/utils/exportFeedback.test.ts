import { beforeEach, describe, expect, it, vi } from "vitest";

import { pushToast } from "@/toastState";
import { downloadCsvBlob, downloadCsvRows } from "@/utils/csvDownload";
import { completeBlobExport, completeCsvRowsExport } from "@/utils/exportFeedback";

vi.mock("@/toastState", () => ({ pushToast: vi.fn() }));
vi.mock("@/utils/csvDownload", () => ({ downloadCsvBlob: vi.fn(), downloadCsvRows: vi.fn() }));

beforeEach(() => vi.clearAllMocks());

describe("export feedback", () => {
  it("uses server metadata and reports the completed download", () => {
    const blob = new Blob(["data"]);

    expect(completeBlobExport({ blob, filename: "server.csv", rowCount: 12 }, "fallback.csv", 5)).toBe(true);

    expect(downloadCsvBlob).toHaveBeenCalledWith("server.csv", blob);
    expect(pushToast).toHaveBeenCalledWith("已匯出 12 筆：server.csv", "success");
  });

  it("does not download an empty export", () => {
    const blob = new Blob([]);

    expect(completeBlobExport({ blob, filename: null, rowCount: 0 }, "empty.csv", 0)).toBe(false);

    expect(downloadCsvBlob).not.toHaveBeenCalled();
    expect(pushToast).toHaveBeenCalledWith("目前沒有可匯出的資料。", "warning");
  });

  it("reports generated CSV row count and filename", () => {
    const rows = [["A"], ["B"]];

    expect(completeCsvRowsExport("quality.csv", ["Name"], rows)).toBe(true);

    expect(downloadCsvRows).toHaveBeenCalledWith("quality.csv", ["Name"], rows);
    expect(pushToast).toHaveBeenCalledWith("已匯出 2 筆：quality.csv", "success");
  });
});
