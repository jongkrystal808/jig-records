import { describe, expect, it } from "vitest";

import { parseInventoryClipboard } from "@/utils/inventoryBatchClipboard";

describe("parseInventoryClipboard", () => {
  it("splits the combined fixture and identifier column in format A Markdown tables", () => {
    const result = parseInventoryClipboard(`| 治具編號 + Datecode/流水號 | 治具數量 |
| -------------------------- | -------- |
| M-00534-0001               | 1        |
| O-00116-0263               | 1        |
| O-00230-0008               | 1        |`);

    expect(result).toEqual({
      format: "header-table",
      rows: [
        ["M-00534", "0001", "1"],
        ["O-00116", "0263", "1"],
        ["O-00230", "0008", "1"]
      ]
    });
  });

  it("also recognizes format A when copied from Excel as two tab-separated columns", () => {
    expect(parseInventoryClipboard("治具編號 + Datecode/流水號\t治具數量\nM-00534-0001\t1")).toEqual({
      format: "header-table",
      rows: [["M-00534", "0001", "1"]]
    });
  });

  it("converts vertical fixture-identifier and quantity pairs after ignoring format A headers", () => {
    const result = parseInventoryClipboard(`治具編號 +
Datecode/流水號
治具數量
C-00090-2605
3
C-00135-2606
25
C-00136-2605
3`);

    expect(result).toEqual({
      format: "vertical-pairs",
      rows: [
        ["C-00090", "2605", "3"],
        ["C-00135", "2606", "25"],
        ["C-00136", "2605", "3"]
      ]
    });
  });

  it("extracts fixture, identifier, defect quantity and defect symptom from format B", () => {
    const result = parseInventoryClipboard(`"日期
(YYYY/MM/DD)
"	治具編號	治具date code / 流水碼	治具名稱	不良數量	不良現象
2026/07/30	L-00005	2305	I/O TB-3.81-12 TB-3.81-12 15	1	接頭線材鬆脫(肉眼可視別)
2026/07/30	L-00091	2212	I/O TB-3.81-8 TB-3.81-8 15	1	接頭線材鬆脫(肉眼可視別)
2026/07/30	L-00091	2407	I/O TB-3.81-8 TB-3.81-8 15	1	接頭線材鬆脫(肉眼可視別)
2026/07/30	L-00143	2505	I/O TB-3.81-12 TB-3.81-8 20(ioLogik E1212 T2)	1	接頭線材鬆脫(肉眼可視別)`);

    expect(result).toEqual({
      format: "header-table",
      rows: [
        ["L-00005", "2305", "1", "接頭線材鬆脫(肉眼可視別)"],
        ["L-00091", "2212", "1", "接頭線材鬆脫(肉眼可視別)"],
        ["L-00091", "2407", "1", "接頭線材鬆脫(肉眼可視別)"],
        ["L-00143", "2505", "1", "接頭線材鬆脫(肉眼可視別)"]
      ]
    });
  });

  it("keeps symbols and non-breaking spaces in the defect symptom note", () => {
    const result = parseInventoryClipboard(
      "治具編號\t治具date code / 流水碼\t不良數量\t不良現象\nO-19-7\t0446\t1\t無法連線 & 無法讀取"
    );

    expect(result).toEqual({
      format: "header-table",
      rows: [["O-19-7", "0446", "1", "無法連線 & 無法讀取"]]
    });
  });

  it("keeps normal three-column spreadsheet ranges unchanged", () => {
    expect(parseInventoryClipboard("FX-001\t2405\t2\nFX-002\t2406\t3")).toEqual({
      format: "grid",
      rows: [
        ["FX-001", "2405", "2"],
        ["FX-002", "2406", "3"]
      ]
    });
  });
});
