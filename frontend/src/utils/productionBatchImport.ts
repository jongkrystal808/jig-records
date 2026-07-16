import type { Fixture, MachineModel, Station } from "@/types";

export type ProductionBatchRowStatus = "ready" | "needs-confirm" | "needs-add" | "skipped" | "error";
export type ProductionBatchEntityKind = "model" | "station" | "fixture";

type ProductionBatchEntitySource = Pick<MachineModel, "id" | "code"> | Pick<Station, "id" | "code"> | Pick<Fixture, "id" | "code">;

export type ProductionBatchEntityResolution = {
  kind: ProductionBatchEntityKind;
  label: string;
  inputCode: string;
  resolvedId: number | null;
  resolvedCode: string;
  suggestedId: number | null;
  suggestedCode: string;
  status: Exclude<ProductionBatchRowStatus, "error">;
  message: string | null;
  note: string | null;
};

export type ProductionMappingBatchRow = {
  lineNo: number;
  raw: string;
  model: ProductionBatchEntityResolution;
  station: ProductionBatchEntityResolution;
  status: ProductionBatchRowStatus;
  message: string | null;
  note: string | null;
};

export type ProductionRequirementBatchRow = {
  lineNo: number;
  raw: string;
  station: ProductionBatchEntityResolution;
  fixture: ProductionBatchEntityResolution;
  quantity: number;
  status: ProductionBatchRowStatus;
  message: string | null;
  note: string | null;
};

export type ProductionBatchCollections = {
  models: MachineModel[];
  stations: Station[];
  fixtures: Fixture[];
};

function splitBatchCells(line: string): string[] {
  const trimmed = line.trim();
  if (!trimmed) return [];
  if (trimmed.includes("\t")) return trimmed.split("\t").map((cell) => cell.trim()).filter(Boolean);
  if (trimmed.includes("|")) return trimmed.split("|").map((cell) => cell.trim()).filter(Boolean);
  if (/[;,，；]/.test(trimmed)) return trimmed.split(/[;,，；]/).map((cell) => cell.trim()).filter(Boolean);
  return trimmed.split(/\s+/).map((cell) => cell.trim()).filter(Boolean);
}

function groupBatchCells(cells: string[], expectedSize: number): string[][] {
  if (cells.length <= expectedSize) return [cells];
  if (cells.length % expectedSize !== 0) return [cells];

  const groups: string[][] = [];
  for (let index = 0; index < cells.length; index += expectedSize) {
    groups.push(cells.slice(index, index + expectedSize));
  }
  return groups;
}

function normalizeBatchText(value: string): string {
  return value.replace(/\u00a0/g, " ").trim();
}

function normalizeCode(value: string): string {
  return normalizeBatchText(value).toUpperCase();
}

function isHeaderLikeLine(line: string, keywords: string[]): boolean {
  const normalized = normalizeBatchText(line).toLowerCase();
  if (!normalized) return true;
  return keywords.some((keyword) => normalized.includes(keyword.toLowerCase()));
}

function commonPrefixLength(left: string, right: string): number {
  const maxLength = Math.min(left.length, right.length);
  let index = 0;
  while (index < maxLength && left[index] === right[index]) {
    index += 1;
  }
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

function makeEntityResolution(kind: ProductionBatchEntityKind, label: string, inputCode: string): ProductionBatchEntityResolution {
  return {
    kind,
    label,
    inputCode,
    resolvedId: null,
    resolvedCode: "",
    suggestedId: null,
    suggestedCode: "",
    status: "needs-add",
    message: null,
    note: null
  };
}

export function setEntityReady(entity: ProductionBatchEntityResolution, id: number, code: string, note: string): void {
  entity.resolvedId = id;
  entity.resolvedCode = code;
  entity.suggestedId = null;
  entity.suggestedCode = "";
  entity.status = "ready";
  entity.message = null;
  entity.note = note;
}

function getCollectionByKind(collections: ProductionBatchCollections, kind: ProductionBatchEntityKind): ProductionBatchEntitySource[] {
  if (kind === "model") return collections.models;
  if (kind === "station") return collections.stations;
  return collections.fixtures;
}

function findExactEntity(collections: ProductionBatchCollections, kind: ProductionBatchEntityKind, code: string): ProductionBatchEntitySource | undefined {
  const target = normalizeCode(code);
  return getCollectionByKind(collections, kind).find((row) => normalizeCode(row.code) === target);
}

function findEntityById(
  collections: ProductionBatchCollections,
  kind: ProductionBatchEntityKind,
  entityId: number
): ProductionBatchEntitySource | undefined {
  return getCollectionByKind(collections, kind).find((row) => row.id === entityId);
}

function findSimilarEntity(collections: ProductionBatchCollections, kind: ProductionBatchEntityKind, code: string): ProductionBatchEntitySource | undefined {
  const target = normalizeCode(code);
  let best: { row: ProductionBatchEntitySource; distance: number; prefix: number } | null = null;

  for (const row of getCollectionByKind(collections, kind)) {
    const candidate = normalizeCode(row.code);
    const prefix = commonPrefixLength(target, candidate);
    const distance = levenshteinDistance(target, candidate);
    if (prefix < 3 && distance > 2) continue;
    if (
      best === null ||
      distance < best.distance ||
      (distance === best.distance && prefix > best.prefix) ||
      (distance === best.distance && prefix === best.prefix && candidate.length < normalizeCode(best.row.code).length)
    ) {
      best = { row, distance, prefix };
    }
  }

  return best && best.distance <= 2 ? best.row : undefined;
}

function resolveEntity(
  collections: ProductionBatchCollections,
  kind: ProductionBatchEntityKind,
  label: string,
  code: string
): ProductionBatchEntityResolution {
  const entity = makeEntityResolution(kind, label, code);
  const normalized = normalizeBatchText(code);
  if (!normalized) {
    entity.status = "needs-add";
    entity.message = `缺少${label}編號`;
    return entity;
  }

  const exact = findExactEntity(collections, kind, normalized);
  if (exact) {
    setEntityReady(entity, exact.id, exact.code, `已對應現有${label}`);
    return entity;
  }

  const similar = findSimilarEntity(collections, kind, normalized);
  if (similar) {
    entity.suggestedId = similar.id;
    entity.suggestedCode = similar.code;
    entity.status = "needs-confirm";
    entity.message = `可能是 ${similar.code}，請先確認是否為同一個${label}`;
    return entity;
  }

  entity.status = "needs-add";
  entity.message = `找不到${label} ${normalized}，可新增或跳過`;
  return entity;
}

export function syncMappingBatchRow(row: ProductionMappingBatchRow): void {
  const entities = [row.model, row.station];
  if (entities.some((entity) => entity.status === "skipped")) {
    row.status = "skipped";
    row.message = "已跳過";
    row.note = null;
    return;
  }
  const pendingConfirm = entities.find((entity) => entity.status === "needs-confirm");
  if (pendingConfirm) {
    row.status = "needs-confirm";
    row.message = pendingConfirm.message;
    row.note = pendingConfirm.note;
    return;
  }
  const pendingAdd = entities.find((entity) => entity.status === "needs-add");
  if (pendingAdd) {
    row.status = "needs-add";
    row.message = pendingAdd.message;
    row.note = pendingAdd.note;
    return;
  }
  row.status = "ready";
  row.message = null;
  row.note = "已完成機種 / 站點確認";
}

export function syncRequirementBatchRow(row: ProductionRequirementBatchRow): void {
  if (!Number.isFinite(row.quantity) || row.quantity <= 0) {
    row.status = "error";
    row.message = "數量必須是大於 0 的整數";
    row.note = null;
    return;
  }
  const entities = [row.station, row.fixture];
  if (entities.some((entity) => entity.status === "skipped")) {
    row.status = "skipped";
    row.message = "已跳過";
    row.note = null;
    return;
  }
  const pendingConfirm = entities.find((entity) => entity.status === "needs-confirm");
  if (pendingConfirm) {
    row.status = "needs-confirm";
    row.message = pendingConfirm.message;
    row.note = pendingConfirm.note;
    return;
  }
  const pendingAdd = entities.find((entity) => entity.status === "needs-add");
  if (pendingAdd) {
    row.status = "needs-add";
    row.message = pendingAdd.message;
    row.note = pendingAdd.note;
    return;
  }
  row.status = "ready";
  row.message = null;
  row.note = "已完成站點 / 治具確認";
}

function toCsvCell(value: string): string {
  const normalized = value.replace(/"/g, "\"\"");
  return /[",\n]/.test(normalized) ? `"${normalized}"` : normalized;
}

export function toCsv(headers: string[], rows: string[][]): string {
  return [headers.join(","), ...rows.map((row) => row.map(toCsvCell).join(","))].join("\n");
}

export function parseMappingBatchText(text: string, collections: ProductionBatchCollections): ProductionMappingBatchRow[] {
  const lines = text
    .replace(/\r/g, "")
    .split("\n")
    .map((line) => normalizeBatchText(line))
    .filter(Boolean)
    .filter((line) => !isHeaderLikeLine(line, ["model_code", "station_code", "機種", "站點"]));

  const rows: ProductionMappingBatchRow[] = [];
  for (const line of lines) {
    const groups = groupBatchCells(splitBatchCells(line), 2);
    for (const cells of groups) {
      const modelCode = cells[0] ?? "";
      const stationCode = cells[1] ?? "";
      const row: ProductionMappingBatchRow = {
        lineNo: rows.length + 1,
        raw: cells.join(","),
        model: resolveEntity(collections, "model", "機種", modelCode),
        station: resolveEntity(collections, "station", "站點", stationCode),
        status: "error",
        message: null,
        note: null
      };
      if (!modelCode || !stationCode) {
        row.status = "error";
        row.message = "每筆必須包含機種與站點";
        rows.push(row);
        continue;
      }
      syncMappingBatchRow(row);
      rows.push(row);
    }
  }

  return rows;
}

export function parseRequirementBatchText(text: string, collections: ProductionBatchCollections): ProductionRequirementBatchRow[] {
  const lines = text
    .replace(/\r/g, "")
    .split("\n")
    .map((line) => normalizeBatchText(line))
    .filter(Boolean)
    .filter((line) => !isHeaderLikeLine(line, ["station_code", "fixture_code", "required_qty", "站點", "治具", "數量"]));

  const rows: ProductionRequirementBatchRow[] = [];
  for (const line of lines) {
    const groups = groupBatchCells(splitBatchCells(line), 3);
    for (const cells of groups) {
      const stationCode = cells[0] ?? "";
      const fixtureCode = cells[1] ?? "";
      const quantityText = cells[2] ?? "";
      const quantity = /^\d+$/.test(quantityText) ? Number.parseInt(quantityText, 10) : 0;
      const row: ProductionRequirementBatchRow = {
        lineNo: rows.length + 1,
        raw: cells.join(","),
        station: resolveEntity(collections, "station", "站點", stationCode),
        fixture: resolveEntity(collections, "fixture", "治具", fixtureCode),
        quantity,
        status: "error",
        message: null,
        note: null
      };
      if (!stationCode || !fixtureCode || !quantityText) {
        row.status = "error";
        row.message = "每筆必須包含站點、治具與數量";
        rows.push(row);
        continue;
      }
      syncRequirementBatchRow(row);
      rows.push(row);
    }
  }

  return rows;
}

export function skipMappingBatchRow(row: ProductionMappingBatchRow): void {
  row.model.status = "skipped";
  row.station.status = "skipped";
  syncMappingBatchRow(row);
}

export function skipRequirementBatchRow(row: ProductionRequirementBatchRow): void {
  row.station.status = "skipped";
  row.fixture.status = "skipped";
  syncRequirementBatchRow(row);
}

export function acceptSimilarEntity(collections: ProductionBatchCollections, entity: ProductionBatchEntityResolution): void {
  const target = entity.suggestedId ? findEntityById(collections, entity.kind, entity.suggestedId) : undefined;
  if (!target) {
    entity.status = "needs-add";
    entity.message = `找不到建議${entity.label}，請改用新增或略過`;
    entity.suggestedId = null;
    entity.suggestedCode = "";
    return;
  }
  setEntityReady(entity, target.id, target.code, `已替換為 ${target.code}`);
}

export function rejectSimilarEntity(entity: ProductionBatchEntityResolution): void {
  entity.status = "needs-add";
  entity.message = `若不是 ${entity.suggestedCode}，可直接新增或略過`;
}
