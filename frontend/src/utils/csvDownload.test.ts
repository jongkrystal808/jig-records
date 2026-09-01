// @vitest-environment jsdom

import { afterEach, describe, expect, it, vi } from "vitest";

import { downloadCsvRows, escapeSpreadsheetFormula } from "@/utils/csvDownload";

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  document.body.innerHTML = "";
});

describe("downloadCsvRows", () => {
  it("escapes spreadsheet formula prefixes only for string cells", () => {
    expect(["=1+1", "+SUM(A1:A2)", "-2+3", "@cmd"].map(escapeSpreadsheetFormula)).toEqual([
      "'=1+1",
      "'+SUM(A1:A2)",
      "'-2+3",
      "'@cmd"
    ]);
    expect(escapeSpreadsheetFormula(-12)).toBe(-12);
    expect(escapeSpreadsheetFormula("ordinary")).toBe("ordinary");
  });

  it("keeps the blob URL alive until the browser has received the download click", () => {
    vi.useFakeTimers();
    const createObjectUrl = vi.fn().mockReturnValue("blob:csv-export");
    const revokeObjectUrl = vi.fn();
    vi.stubGlobal("URL", { createObjectURL: createObjectUrl, revokeObjectURL: revokeObjectUrl });
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);

    downloadCsvRows("filtered.csv", ["欄位"], [["內容"]]);

    expect(createObjectUrl).toHaveBeenCalledOnce();
    expect(click).toHaveBeenCalledOnce();
    expect(document.querySelector("a[download='filtered.csv']")).toBeNull();
    expect(revokeObjectUrl).not.toHaveBeenCalled();

    vi.runAllTimers();
    expect(revokeObjectUrl).toHaveBeenCalledWith("blob:csv-export");
  });
});
