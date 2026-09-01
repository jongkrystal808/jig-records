<script setup lang="ts">
import { nextTick, ref, useId, watch } from "vue";

import type { Fixture } from "@/types";
import { parseInventoryClipboard } from "@/utils/inventoryBatchClipboard";

type GridColumn = "fixtureCode" | "identifier" | "quantity" | "note";

type GridRow = {
  id: number;
  mode: "receipt" | "return";
  transactionNo: string;
  fixtureCode: string;
  identifier: string;
  quantity: string;
  ownershipType: "customer_supplied" | "self_purchased";
  note: string;
};

const props = withDefaults(defineProps<{
  modelValue: string;
  fixtures: Fixture[];
  mode: "receipt" | "return";
  transactionNo: string;
  presetFixtureCode?: string;
  defaultOwnershipType?: "customer_supplied" | "self_purchased";
  defaultNote?: string;
  showModeSwitch?: boolean;
  disabled?: boolean;
}>(), {
  presetFixtureCode: "",
  defaultOwnershipType: "customer_supplied",
  defaultNote: "",
  showModeSwitch: true,
  disabled: false
});

const emit = defineEmits<{
  "update:modelValue": [value: string];
  "update:mode": [value: "receipt" | "return"];
  "update:transactionNo": [value: string];
}>();

const MIN_VISIBLE_ROWS = 5;
const columns: GridColumn[] = ["fixtureCode", "identifier", "quantity", "note"];
const rows = ref<GridRow[]>([]);
const applyModeToAll = ref(true);
const applyTransactionNoToAll = ref(true);
const applyOwnershipToAll = ref(false);
const gridRef = ref<HTMLElement | null>(null);
const fixtureListId = `batch-grid-fixtures-${useId()}`;
let nextRowId = 1;
let lastEmittedValue = "";

function normalizedPreset(): string {
  return props.presetFixtureCode.trim().toUpperCase();
}

function createBlankRow(): GridRow {
  return {
    id: nextRowId++,
    mode: props.mode,
    transactionNo: props.transactionNo,
    fixtureCode: normalizedPreset(),
    identifier: "",
    quantity: "1",
    ownershipType: props.defaultOwnershipType,
    note: props.defaultNote
  };
}

function splitLegacyFixtureAndIdentifier(value: string): [string, string] {
  const trimmed = value.trim();
  const lastDash = trimmed.lastIndexOf("-");
  if (lastDash <= 0 || lastDash === trimmed.length - 1) return [trimmed, ""];
  return [trimmed.slice(0, lastDash), trimmed.slice(lastDash + 1)];
}

function parseDraft(value: string): GridRow[] {
  const lines = value.replace(/\r/g, "").split("\n").filter((line) => line.trim().length > 0);
  const parsed: GridRow[] = [];
  for (let index = 0; index < lines.length; ) {
    const cells = lines[index].split("\t");
    if (cells.length >= 6 && (cells[0]?.trim() === "receipt" || cells[0]?.trim() === "return")) {
      parsed.push({
        id: nextRowId++,
        mode: cells[0].trim() as "receipt" | "return",
        transactionNo: cells[1]?.trim() ?? "",
        fixtureCode: cells[2]?.trim() ?? "",
        identifier: cells[3]?.trim() ?? "",
        quantity: cells[4]?.trim() || "1",
        ownershipType: cells[5]?.trim() === "self_purchased" ? "self_purchased" : "customer_supplied",
        note: cells.slice(6).join("\t").trim() || props.defaultNote
      });
      index += 1;
      continue;
    }
    if (cells.length >= 3) {
      parsed.push({
        id: nextRowId++,
        mode: props.mode,
        transactionNo: props.transactionNo,
        fixtureCode: cells[0]?.trim() ?? "",
        identifier: cells[1]?.trim() ?? "",
        quantity: cells[2]?.trim() || "1",
        ownershipType: cells[3]?.trim() === "self_purchased" ? "self_purchased" : "customer_supplied",
        note: cells.slice(4).join("\t").trim() || props.defaultNote
      });
      index += 1;
      continue;
    }

    const [fixtureCode, identifier] = splitLegacyFixtureAndIdentifier(lines[index]);
    parsed.push({
      id: nextRowId++,
      mode: props.mode,
      transactionNo: props.transactionNo,
      fixtureCode,
      identifier,
      quantity: lines[index + 1]?.trim() || "1",
      ownershipType: props.defaultOwnershipType,
      note: props.defaultNote
    });
    index += 2;
  }
  return parsed;
}

function isVisibleBlank(row: GridRow): boolean {
  const fixtureCode = row.fixtureCode.trim().toUpperCase();
  return (
    !row.identifier.trim() &&
    !row.note.trim() &&
    (!fixtureCode || fixtureCode === normalizedPreset()) &&
    (!row.quantity.trim() || row.quantity.trim() === "1")
  );
}

function ensureBlankRows(): void {
  const blankCount = rows.value.filter(isVisibleBlank).length;
  for (let index = blankCount; index < MIN_VISIBLE_ROWS; index += 1) {
    rows.value.push(createBlankRow());
  }
}

function serializeRows(): string {
  return rows.value
    .filter((row) => !isVisibleBlank(row))
    .map((row) =>
      [
        row.mode,
        row.transactionNo.trim(),
        row.fixtureCode.trim(),
        row.identifier.trim(),
        row.quantity.trim() || "1",
        row.ownershipType,
        row.note.trim()
      ].join("\t")
    )
    .join("\n");
}

function emitGridValue(): void {
  ensureBlankRows();
  lastEmittedValue = serializeRows();
  emit("update:modelValue", lastEmittedValue);
}

function addRow(focus = true): void {
  const row = createBlankRow();
  rows.value.push(row);
  if (!focus) return;
  void nextTick(() => {
    gridRef.value
      ?.querySelector<HTMLInputElement>(`[data-grid-row="${row.id}"][data-grid-column="fixtureCode"]`)
      ?.focus();
  });
}

function removeRow(rowId: number): void {
  rows.value = rows.value.filter((row) => row.id !== rowId);
  ensureBlankRows();
  emitGridValue();
}

function pasteMatrix(event: ClipboardEvent, startRowIndex: number, startColumn: GridColumn): void {
  const text = event.clipboardData?.getData("text/plain") ?? "";
  if (!text) return;
  event.preventDefault();

  const matrix = parseInventoryClipboard(text).rows;
  const startColumnIndex = columns.indexOf(startColumn);

  matrix.forEach((sourceRow, rowOffset) => {
    const targetIndex = startRowIndex + rowOffset;
    while (rows.value.length <= targetIndex) rows.value.push(createBlankRow());
    sourceRow.slice(0, columns.length - startColumnIndex).forEach((cell, columnOffset) => {
      const column = columns[startColumnIndex + columnOffset];
      if (column) rows.value[targetIndex][column] = cell.trim();
    });
  });
  emitGridValue();
}

function moveOnEnter(event: KeyboardEvent, rowIndex: number, column: GridColumn): void {
  if (event.key !== "Enter") return;
  event.preventDefault();
  if (rowIndex >= rows.value.length - 1) addRow(false);
  void nextTick(() => {
    const nextRow = rows.value[rowIndex + 1];
    if (!nextRow) return;
    gridRef.value
      ?.querySelector<HTMLInputElement>(`[data-grid-row="${nextRow.id}"][data-grid-column="${column}"]`)
      ?.focus();
  });
}

function updateMode(row: GridRow): void {
  if (applyModeToAll.value) {
    rows.value.forEach((target) => {
      target.mode = row.mode;
    });
    emit("update:mode", row.mode);
  }
  emitGridValue();
}

function updateTransactionNo(row: GridRow): void {
  if (applyTransactionNoToAll.value) {
    rows.value.forEach((target) => {
      target.transactionNo = row.transactionNo;
    });
    emit("update:transactionNo", row.transactionNo);
  }
  emitGridValue();
}

function updateOwnershipType(row: GridRow): void {
  if (applyOwnershipToAll.value) {
    rows.value.forEach((target) => {
      target.ownershipType = row.ownershipType;
    });
  }
  emitGridValue();
}

function applyColumnToAll(column: "mode" | "transactionNo" | "ownershipType"): void {
  const enabled =
    column === "mode"
      ? applyModeToAll.value
      : column === "transactionNo"
        ? applyTransactionNoToAll.value
        : applyOwnershipToAll.value;
  if (!enabled || rows.value.length === 0) return;

  const source =
    column === "transactionNo"
      ? rows.value.find((row) => row.transactionNo.trim()) ?? rows.value[0]
      : rows.value.find((row) => !isVisibleBlank(row)) ?? rows.value[0];
  if (!source) return;
  rows.value.forEach((row) => {
    if (column === "mode") row.mode = source.mode;
    if (column === "transactionNo") row.transactionNo = source.transactionNo;
    if (column === "ownershipType") row.ownershipType = source.ownershipType;
  });
  if (column === "mode") emit("update:mode", source.mode);
  if (column === "transactionNo") emit("update:transactionNo", source.transactionNo);
  emitGridValue();
}

watch(
  () => props.modelValue,
  (value) => {
    if (rows.value.length > 0 && value === lastEmittedValue && serializeRows() === value) return;
    rows.value = parseDraft(value);
    ensureBlankRows();
  },
  { immediate: true }
);

watch(
  () => props.presetFixtureCode,
  () => {
    if (props.modelValue.trim()) return;
    rows.value = [];
    ensureBlankRows();
  }
);

watch(
  () => props.mode,
  (value) => {
    if (!applyModeToAll.value) return;
    rows.value.forEach((row) => {
      row.mode = value;
    });
  }
);

watch(
  () => props.transactionNo,
  (value) => {
    if (!applyTransactionNoToAll.value) return;
    rows.value.forEach((row) => {
      row.transactionNo = value;
    });
  }
);
</script>

<template>
  <section ref="gridRef" class="batch-grid-card" aria-labelledby="batch-grid-title" data-tour="inventory-paste-field">
    <div class="batch-grid-scroll">
      <table class="batch-entry-grid">
        <colgroup>
          <col class="row-number-column" />
          <col class="mode-column" />
          <col class="transaction-column" />
          <col />
          <col class="ownership-column" />
          <col />
          <col class="quantity-column" />
          <col class="note-column" />
          <col class="action-column" />
        </colgroup>
        <caption id="batch-grid-title" class="sr-only">收退料報表編輯區</caption>
        <thead>
          <tr v-if="$slots['between-meta-and-grid']" class="batch-grid-control-row batch-grid-switcher-row">
            <th class="batch-grid-control-cell batch-grid-switcher-cell" colspan="9">
              <slot name="between-meta-and-grid" />
            </th>
          </tr>
          <tr class="batch-grid-column-row">
            <th class="row-number-cell">#</th>
            <th data-tour="inventory-mode-column">
              <span>收／退料</span>
              <label class="apply-all-control">
                <input v-model="applyModeToAll" type="checkbox" @change="applyColumnToAll('mode')" />
                全部套用
              </label>
            </th>
            <th data-tour="inventory-transaction-column">
              <span>單號 *</span>
              <label class="apply-all-control">
                <input v-model="applyTransactionNoToAll" type="checkbox" @change="applyColumnToAll('transactionNo')" />
                全部套用
              </label>
            </th>
            <th data-tour="inventory-fixture-column">治具</th>
            <th data-tour="inventory-ownership-column">
              <span>來源</span>
              <label class="apply-all-control">
                <input v-model="applyOwnershipToAll" type="checkbox" @change="applyColumnToAll('ownershipType')" />
                全部套用
              </label>
            </th>
            <th data-tour="inventory-identifier-column">datecode/編號</th>
            <th class="quantity-cell" data-tour="inventory-quantity-column">數量</th>
            <th data-tour="inventory-note-column">備註</th>
            <th class="action-cell">
              <button class="grid-add-button" type="button" :disabled="disabled" aria-label="新增一列" title="新增一列" @click="addRow()">＋</button>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, rowIndex) in rows" :key="row.id">
            <th class="row-number-cell" scope="row">{{ rowIndex + 1 }}</th>
            <td>
              <select
                v-model="row.mode"
                :disabled="disabled || !showModeSwitch"
                aria-label="收／退料"
                data-grid-column="mode"
                @change="updateMode(row)"
              >
                <option value="receipt">收料</option>
                <option value="return">退料</option>
              </select>
            </td>
            <td>
              <input
                v-model="row.transactionNo"
                :disabled="disabled"
                aria-label="單號"
                data-grid-column="transactionNo"
                autocomplete="off"
                spellcheck="false"
                @input="updateTransactionNo(row)"
              />
            </td>
            <td>
              <input
                v-model="row.fixtureCode"
                :data-grid-row="row.id"
                data-grid-column="fixtureCode"
                :list="fixtureListId"
                :disabled="disabled"
                aria-label="治具"
                autocomplete="off"
                spellcheck="false"
                @input="emitGridValue"
                @paste="pasteMatrix($event, rowIndex, 'fixtureCode')"
                @keydown="moveOnEnter($event, rowIndex, 'fixtureCode')"
              />
            </td>
            <td>
              <select v-model="row.ownershipType" :disabled="disabled" aria-label="來源" data-grid-column="ownershipType" @change="updateOwnershipType(row)">
                <option value="customer_supplied">客供</option>
                <option value="self_purchased">自購</option>
              </select>
            </td>
            <td>
              <input
                v-model="row.identifier"
                :data-grid-row="row.id"
                data-grid-column="identifier"
                :disabled="disabled"
                aria-label="datecode/編號"
                autocomplete="off"
                spellcheck="false"
                @input="emitGridValue"
                @paste="pasteMatrix($event, rowIndex, 'identifier')"
                @keydown="moveOnEnter($event, rowIndex, 'identifier')"
              />
            </td>
            <td class="quantity-cell">
              <input
                v-model="row.quantity"
                :data-grid-row="row.id"
                data-grid-column="quantity"
                :disabled="disabled"
                aria-label="數量"
                inputmode="numeric"
                pattern="[0-9]*"
                @input="emitGridValue"
                @paste="pasteMatrix($event, rowIndex, 'quantity')"
                @keydown="moveOnEnter($event, rowIndex, 'quantity')"
              />
            </td>
            <td>
              <input
                v-model="row.note"
                :data-grid-row="row.id"
                data-grid-column="note"
                :disabled="disabled"
                aria-label="備註"
                autocomplete="off"
                @input="emitGridValue"
              />
            </td>
            <td class="action-cell">
              <button
                class="grid-remove-button"
                type="button"
                :disabled="disabled || isVisibleBlank(row)"
                :aria-label="`刪除第 ${rowIndex + 1} 列`"
                @click="removeRow(row.id)"
              >
                ×
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <datalist :id="fixtureListId">
      <option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.code">
        {{ fixture.name }}
      </option>
    </datalist>
  </section>
</template>

<style scoped>
.batch-grid-card {
  width: 100%;
  min-width: 0;
  border: 1px solid var(--panel-input-border);
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
}

.batch-grid-scroll {
  width: 100%;
  min-width: 0;
  max-height: min(68dvh, 640px);
  overflow: auto;
}

.batch-entry-grid {
  width: 100%;
  min-width: 1120px;
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
}

.batch-entry-grid th,
.batch-entry-grid td {
  height: 42px;
  padding: 0;
  border-right: 1px solid #d7e1ed;
  border-bottom: 1px solid #d7e1ed;
  text-align: left;
}

.batch-entry-grid .batch-grid-column-row th {
  position: sticky;
  top: 0;
  z-index: 2;
  padding: 0 10px;
  color: #43536d;
  background: #dce9f8;
  font-size: 12px;
  font-weight: 800;
}

.batch-entry-grid .batch-grid-column-row th > span {
  display: block;
}

.apply-all-control {
  display: flex;
  align-items: center;
  gap: 4px;
  width: fit-content;
  margin-top: 2px;
  color: #60708a;
  font-size: 10px;
  font-weight: 700;
  white-space: nowrap;
  cursor: pointer;
}

.batch-entry-grid .apply-all-control input {
  appearance: auto;
  flex: 0 0 auto;
  width: 13px;
  height: 13px;
  padding: 0;
  accent-color: var(--panel-accent);
}

.batch-entry-grid .batch-grid-control-cell {
  position: static;
  height: auto;
  padding: 0;
  border-right: 0;
  color: inherit;
  background: #fff;
  font-size: inherit;
  font-weight: inherit;
}

.batch-entry-grid .batch-grid-switcher-cell {
  overflow: visible;
  background: #f8fafd;
}

.batch-entry-grid tbody tr:nth-child(even) {
  background: #f2f6fb;
}

.batch-entry-grid tbody tr:nth-child(odd) {
  background: #fff;
}

.batch-entry-grid input,
.batch-entry-grid select {
  width: 100%;
  height: 41px;
  border: 0;
  border-radius: 0;
  padding: 0 10px;
  color: #34445d;
  background: transparent;
  font: inherit;
  font-size: 13px;
}

.batch-entry-grid select {
  appearance: none;
  padding-right: 24px;
  background-image: linear-gradient(45deg, transparent 50%, #62718a 50%), linear-gradient(135deg, #62718a 50%, transparent 50%);
  background-position: calc(100% - 14px) 17px, calc(100% - 9px) 17px;
  background-size: 5px 5px, 5px 5px;
  background-repeat: no-repeat;
}

.batch-entry-grid input:focus,
.batch-entry-grid select:focus {
  position: relative;
  z-index: 1;
  outline: 2px solid var(--panel-accent);
  outline-offset: -2px;
  box-shadow: none;
  background: #fff;
}

.row-number-cell {
  color: #7a8799;
  text-align: center !important;
  font-size: 11px;
  font-weight: 700;
}

.row-number-column {
  width: 44px;
}

.mode-column {
  width: 92px;
}

.transaction-column {
  width: 180px;
}

.ownership-column {
  width: 104px;
}

.quantity-column {
  width: 88px;
}

.note-column {
  width: 200px;
}

.quantity-cell input {
  text-align: right;
}

.action-column {
  width: 48px;
}

.action-cell {
  border-right: 0 !important;
  text-align: center !important;
}

.grid-remove-button {
  width: 30px;
  height: 30px;
  border: 0;
  border-radius: 7px;
  color: #6f7d91;
  background: transparent;
  font-size: 18px;
  cursor: pointer;
}

.grid-add-button {
  width: 28px;
  height: 28px;
  border: 1px solid rgba(47, 125, 224, 0.38);
  border-radius: 8px;
  color: var(--panel-accent);
  background: #fff;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
}

.grid-add-button:hover:not(:disabled) {
  background: color-mix(in srgb, var(--panel-accent-soft) 70%, white);
}

.grid-remove-button:hover:not(:disabled) {
  color: #a33c3c;
  background: #fdecec;
}

.grid-remove-button:disabled {
  opacity: 0.25;
  cursor: default;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

</style>
