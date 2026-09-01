import type { Ref } from "vue";

import type { Fixture, IdentifierStockSummary } from "@/types";
import { normalizeIdentifierForWrite } from "@/utils/identifier";

export type InventoryImportMode = "receipt" | "return";
export type InventoryBatchRowStatus = "ready" | "needs-confirm" | "needs-add" | "skipped" | "error";
export type InventoryBatchOwnershipType = "customer_supplied" | "self_purchased";

export type InventoryBatchImportRow = {
  lineNo: number;
  raw: string;
  mode: InventoryImportMode;
  transactionNo: string;
  inputFixtureCode: string;
  inputToken: string;
  quantity: number;
  ownershipType: InventoryBatchOwnershipType;
  note: string;
  resolvedFixtureId: number | null;
  resolvedFixtureCode: string;
  suggestedFixtureId: number | null;
  suggestedFixtureCode: string;
  status: InventoryBatchRowStatus;
  message: string | null;
  errorSource: "parse" | "inventory" | null;
};

type ParseDefaults = {
  mode: InventoryImportMode;
  transactionNo: string;
  ownershipType: InventoryBatchOwnershipType;
  note: string;
};

function normalizeText(value: string): string {
  return value.replace(/\u00a0/g, " ").trim();
}

function normalizeCode(value: string): string {
  return normalizeText(value).toUpperCase();
}

function splitCells(line: string): string[] {
  const trimmed = normalizeText(line);
  if (!trimmed) return [];
  if (trimmed.includes("\t")) return trimmed.split("\t").map(normalizeText).filter(Boolean);
  if (trimmed.includes("|")) return trimmed.split("|").map(normalizeText).filter(Boolean);
  if (/[;,，；]/.test(trimmed)) return trimmed.split(/[;,，；]/).map(normalizeText).filter(Boolean);
  return trimmed.split(/\s{2,}/).map(normalizeText).filter(Boolean);
}

function splitCombinedFixtureText(value: string): { fixtureCode: string; token: string } {
  const trimmed = normalizeText(value);
  const lastDash = trimmed.lastIndexOf("-");
  if (lastDash <= 0 || lastDash >= trimmed.length - 1) return { fixtureCode: trimmed, token: "" };
  return {
    fixtureCode: trimmed.slice(0, lastDash).trim(),
    token: trimmed.slice(lastDash + 1).trim()
  };
}

function commonPrefixLength(left: string, right: string): number {
  const maxLength = Math.min(left.length, right.length);
  let index = 0;
  while (index < maxLength && left[index] === right[index]) index += 1;
  return index;
}

function levenshteinDistance(left: string, right: string): number {
  const a = left.toUpperCase();
  const b = right.toUpperCase();
  const previous = Array.from({ length: b.length + 1 }, (_, index) => index);
  for (let i = 1; i <= a.length; i += 1) {
    const current = [i];
    for (let j = 1; j <= b.length; j += 1) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      current[j] = Math.min(current[j - 1] + 1, previous[j] + 1, previous[j - 1] + cost);
    }
    previous.splice(0, previous.length, ...current);
  }
  return previous[b.length] ?? 0;
}

export function useInventoryBatchParser(options: {
  fixtures: Ref<Fixture[]>;
  identifierStockRows: Ref<IdentifierStockSummary[]>;
}) {
  function findFixtureByCode(code: string): Fixture | undefined {
    const target = normalizeCode(code);
    return options.fixtures.value.find((row) => normalizeCode(row.code) === target);
  }

  function findSimilarFixture(code: string): Fixture | undefined {
    const target = normalizeCode(code);
    let best: { fixture: Fixture; distance: number; prefix: number } | null = null;
    for (const fixture of options.fixtures.value) {
      const candidate = normalizeCode(fixture.code);
      const prefix = commonPrefixLength(target, candidate);
      const distance = levenshteinDistance(target, candidate);
      if (prefix < 4 && distance > 2) continue;
      if (best === null || distance < best.distance || (distance === best.distance && prefix > best.prefix)) {
        best = { fixture, distance, prefix };
      }
    }
    return best && best.distance <= 2 ? best.fixture : undefined;
  }

  function makeErrorRow(
    lineNo: number,
    raw: string,
    message: string,
    defaults: ParseDefaults
  ): InventoryBatchImportRow {
    return {
      lineNo,
      raw,
      mode: defaults.mode,
      transactionNo: defaults.transactionNo,
      inputFixtureCode: "",
      inputToken: "",
      quantity: 0,
      ownershipType: defaults.ownershipType,
      note: defaults.note,
      resolvedFixtureId: null,
      resolvedFixtureCode: "",
      suggestedFixtureId: null,
      suggestedFixtureCode: "",
      status: "error",
      message,
      errorSource: "parse"
    };
  }

  function buildRow(
    lineNo: number,
    codeLine: string,
    qtyLine: string,
    defaults: ParseDefaults
  ): InventoryBatchImportRow {
    const raw = `${codeLine}\n${qtyLine}`;
    const codeCells = splitCells(codeLine);
    const qtyText = splitCells(qtyLine)[0] ?? "";
    if (!qtyText || !/^\d+$/.test(qtyText) || Number.parseInt(qtyText, 10) <= 0) {
      return makeErrorRow(lineNo, raw, "數量必須是大於 0 的整數", defaults);
    }

    let fixtureCodeText = normalizeText(codeLine);
    let tokenText = "";
    if (codeCells.length >= 3) {
      fixtureCodeText = `${codeCells[0]}-${codeCells[1]}`;
      tokenText = codeCells[2];
    } else if (codeCells.length === 2) {
      fixtureCodeText = codeCells[0];
      tokenText = codeCells[1];
    } else {
      const split = splitCombinedFixtureText(codeLine);
      fixtureCodeText = split.fixtureCode;
      tokenText = split.token;
    }

    const identifier = normalizeIdentifierForWrite(tokenText);
    if (!identifier) return makeErrorRow(lineNo, raw, "缺少 datecode/編號", defaults);

    const base = {
      lineNo,
      raw,
      mode: defaults.mode,
      transactionNo: defaults.transactionNo,
      inputFixtureCode: fixtureCodeText,
      inputToken: identifier,
      quantity: Number.parseInt(qtyText, 10),
      ownershipType: defaults.ownershipType,
      note: defaults.note
    };
    const exactFixture = findFixtureByCode(fixtureCodeText);
    if (exactFixture) {
      return {
        ...base,
        resolvedFixtureId: exactFixture.id,
        resolvedFixtureCode: exactFixture.code,
        suggestedFixtureId: null,
        suggestedFixtureCode: "",
        status: "ready",
        message: null,
        errorSource: null
      };
    }
    const similarFixture = findSimilarFixture(fixtureCodeText);
    if (similarFixture) {
      return {
        ...base,
        resolvedFixtureId: null,
        resolvedFixtureCode: "",
        suggestedFixtureId: similarFixture.id,
        suggestedFixtureCode: similarFixture.code,
        status: "needs-confirm",
        message: `可能是 ${similarFixture.code}，請確認`,
        errorSource: null
      };
    }
    return {
      ...base,
      resolvedFixtureId: null,
      resolvedFixtureCode: "",
      suggestedFixtureId: null,
      suggestedFixtureCode: "",
      status: "needs-add",
      message: `找不到治具 ${fixtureCodeText}`,
      errorSource: null
    };
  }

  function parseRows(text: string, defaults: ParseDefaults): InventoryBatchImportRow[] {
    const lines = text.replace(/\r/g, "").split("\n").map(normalizeText).filter(Boolean);
    const parsed: InventoryBatchImportRow[] = [];
    for (let index = 0; index < lines.length; ) {
      const current = lines[index];
      const serializedCells = current.split("\t");
      if (serializedCells.length >= 6 && (serializedCells[0]?.trim() === "receipt" || serializedCells[0]?.trim() === "return")) {
        const [modeValue, transactionNo, fixtureCode, identifier, quantity, ownershipValue, ...noteCells] = serializedCells;
        parsed.push(buildRow(parsed.length + 1, `${fixtureCode.trim()}\t${identifier.trim()}`, quantity.trim(), {
          mode: modeValue.trim() as InventoryImportMode,
          transactionNo: transactionNo.trim(),
          ownershipType: ownershipValue.trim() === "self_purchased" ? "self_purchased" : "customer_supplied",
          note: noteCells.join("\t").trim()
        }));
        index += 1;
        continue;
      }
      if (serializedCells.length >= 4) {
        const [fixtureCode, identifier, quantity, ownershipValue, ...noteCells] = serializedCells;
        parsed.push(buildRow(parsed.length + 1, `${fixtureCode.trim()}\t${identifier.trim()}`, quantity.trim(), {
          ...defaults,
          ownershipType: ownershipValue.trim() === "self_purchased" ? "self_purchased" : "customer_supplied",
          note: noteCells.join("\t").trim()
        }));
        index += 1;
        continue;
      }
      const cells = splitCells(current);
      if (cells.length >= 3 && /^\d+$/.test(cells[cells.length - 1])) {
        parsed.push(buildRow(parsed.length + 1, cells.slice(0, -1).join("\t"), cells[cells.length - 1], defaults));
        index += 1;
        continue;
      }
      const qtyLine = lines[index + 1];
      if (!qtyLine) {
        parsed.push(makeErrorRow(parsed.length + 1, current, "缺少數量列", defaults));
        break;
      }
      parsed.push(buildRow(parsed.length + 1, current, qtyLine, defaults));
      index += 2;
    }
    return parsed;
  }

  function validateRowsForInventory(sourceRows: InventoryBatchImportRow[]): InventoryBatchImportRow[] {
    const resetRows = sourceRows.map((row): InventoryBatchImportRow =>
      row.mode === "receipt" && row.errorSource === "inventory"
        ? { ...row, status: "ready", message: null, errorSource: null }
        : { ...row }
    );
    if (!resetRows.some((row) => row.mode === "return")) return resetRows;

    const availableQtyByKey = new Map(
      options.identifierStockRows.value.map((row) => [`${row.fixture_id}::${row.identifier}`, row.stock_qty])
    );
    const requestedQtyByKey = new Map<string, number>();
    return resetRows.map((row) => {
      if (row.mode !== "return" || row.status === "skipped" || row.status === "needs-add" || row.status === "needs-confirm" || row.errorSource === "parse" || !row.resolvedFixtureId || !row.inputToken) return row;
      const key = `${row.resolvedFixtureId}::${row.inputToken}`;
      const availableQty = availableQtyByKey.get(key) ?? 0;
      const requestedQty = (requestedQtyByKey.get(key) ?? 0) + row.quantity;
      requestedQtyByKey.set(key, requestedQty);
      if (availableQty <= 0) return { ...row, status: "error", message: `退料無庫存：${row.resolvedFixtureCode} / ${row.inputToken}`, errorSource: "inventory" };
      if (requestedQty > availableQty) return { ...row, status: "error", message: `退料超出庫存：${row.resolvedFixtureCode} / ${row.inputToken} 可退 ${availableQty} pcs，本次解析合計 ${requestedQty} pcs`, errorSource: "inventory" };
      return { ...row, status: "ready", message: null, errorSource: null };
    });
  }

  return { parseRows, validateRowsForInventory };
}
