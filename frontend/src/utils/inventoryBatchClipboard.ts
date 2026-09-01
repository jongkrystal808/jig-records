export type InventoryClipboardFormat = "grid" | "vertical-pairs" | "header-table";

export type InventoryClipboardParseResult = {
  format: InventoryClipboardFormat;
  rows: string[][];
};

function parseTsv(text: string): string[][] {
  const normalized = text.replace(/\r\n?/g, "\n");
  const rows: string[][] = [];
  let row: string[] = [];
  let cell = "";
  let quoted = false;

  for (let index = 0; index < normalized.length; index += 1) {
    const character = normalized[index];
    if (character === '"') {
      if (quoted && normalized[index + 1] === '"') {
        cell += '"';
        index += 1;
      } else {
        quoted = !quoted;
      }
      continue;
    }
    if (!quoted && character === "\t") {
      row.push(cell.trim());
      cell = "";
      continue;
    }
    if (!quoted && character === "\n") {
      row.push(cell.trim());
      rows.push(row);
      row = [];
      cell = "";
      continue;
    }
    cell += character;
  }

  row.push(cell.trim());
  rows.push(row);
  return rows.filter((cells) => cells.some((value) => value.length > 0));
}

function parseMarkdownTable(text: string): string[][] | null {
  const lines = text
    .replace(/\r\n?/g, "\n")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  if (lines.length < 2 || !lines.every((line) => line.startsWith("|") && line.endsWith("|"))) {
    return null;
  }

  return lines
    .map((line) => line.slice(1, -1).split("|").map((cell) => cell.trim()))
    .filter((row) => !row.every((cell) => /^:?-{3,}:?$/.test(cell)));
}

function normalizeHeader(value: string): string {
  return value.toLowerCase().replace(/[\s/／+＋()（）_-]/g, "");
}

function fixtureHeaderIndex(row: string[]): number {
  return row.findIndex((value) => normalizeHeader(value).includes("治具編號"));
}

function identifierHeaderIndex(row: string[]): number {
  return row.findIndex((value) => {
    const header = normalizeHeader(value);
    return header.includes("datecode") || header.includes("流水碼") || header.includes("流水號");
  });
}

function quantityHeaderIndex(row: string[]): number {
  return row.findIndex((value) => normalizeHeader(value).includes("數量"));
}

function noteHeaderIndex(row: string[]): number {
  return row.findIndex((value) => {
    const header = normalizeHeader(value);
    return header.includes("不良現象") || header.includes("備註");
  });
}

function parseHeaderTable(rows: string[][]): string[][] | null {
  const headerRowIndex = rows.findIndex((row) =>
    fixtureHeaderIndex(row) >= 0 && identifierHeaderIndex(row) >= 0 && quantityHeaderIndex(row) >= 0
  );
  if (headerRowIndex < 0) return null;

  const header = rows[headerRowIndex];
  const fixtureIndex = fixtureHeaderIndex(header);
  const identifierIndex = identifierHeaderIndex(header);
  const quantityIndex = quantityHeaderIndex(header);
  const noteIndex = noteHeaderIndex(header);
  return rows
    .slice(headerRowIndex + 1)
    .map((row) => {
      const quantity = row[quantityIndex]?.trim() ?? "";
      const note = noteIndex >= 0 ? row[noteIndex]?.trim() ?? "" : null;
      if (fixtureIndex === identifierIndex) {
        const [fixtureCode, identifier] = splitFixtureAndIdentifier(row[fixtureIndex] ?? "");
        return note === null ? [fixtureCode, identifier, quantity] : [fixtureCode, identifier, quantity, note];
      }
      const parsedRow = [row[fixtureIndex]?.trim() ?? "", row[identifierIndex]?.trim() ?? "", quantity];
      if (note !== null) parsedRow.push(note);
      return parsedRow;
    })
    .filter((row) => row.some(Boolean));
}

function splitFixtureAndIdentifier(value: string): [string, string] {
  const trimmed = value.trim();
  const lastDash = trimmed.lastIndexOf("-");
  if (lastDash <= 0 || lastDash >= trimmed.length - 1) return [trimmed, ""];
  return [trimmed.slice(0, lastDash).trim(), trimmed.slice(lastDash + 1).trim()];
}

function isVerticalHeader(value: string): boolean {
  const header = normalizeHeader(value);
  return (
    header === "治具編號" ||
    header === "datecode流水號" ||
    header === "datecode流水碼" ||
    header === "治具數量" ||
    header === "數量"
  );
}

function parseVerticalPairs(rows: string[][]): string[][] | null {
  if (rows.some((row) => row.length > 1)) return null;
  const values = rows.map((row) => row[0]?.trim() ?? "").filter(Boolean);
  while (values.length > 0 && isVerticalHeader(values[0])) values.shift();
  if (values.length < 2 || values.length % 2 !== 0) return null;

  const parsed: string[][] = [];
  for (let index = 0; index < values.length; index += 2) {
    const [fixtureCode, identifier] = splitFixtureAndIdentifier(values[index]);
    const quantity = values[index + 1];
    if (!fixtureCode || !identifier || !/^\d+$/.test(quantity)) return null;
    parsed.push([fixtureCode, identifier, quantity]);
  }
  return parsed;
}

export function parseInventoryClipboard(text: string): InventoryClipboardParseResult {
  const parsedRows = parseMarkdownTable(text) ?? parseTsv(text);
  const headerTableRows = parseHeaderTable(parsedRows);
  if (headerTableRows) return { format: "header-table", rows: headerTableRows };

  const verticalRows = parseVerticalPairs(parsedRows);
  if (verticalRows) return { format: "vertical-pairs", rows: verticalRows };

  return { format: "grid", rows: parsedRows };
}
