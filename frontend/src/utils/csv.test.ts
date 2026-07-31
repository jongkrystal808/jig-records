import { describe, expect, it } from "vitest";

import { buildCsv } from "@/utils/csv";

describe("buildCsv", () => {
  it("quotes every cell and escapes quotes for Excel-compatible CSV", () => {
    expect(
      buildCsv(
        ["治具代碼", "治具名稱"],
        [
          ["FX-001", '測試,治具"A"'],
          ["FX-002", null]
        ]
      )
    ).toBe(
      '"治具代碼","治具名稱"\r\n"FX-001","測試,治具""A"""\r\n"FX-002",""'
    );
  });

  it("keeps numeric and boolean values readable", () => {
    expect(buildCsv(["數量", "啟用"], [[12, true]])).toBe('"數量","啟用"\r\n"12","true"');
  });
});
