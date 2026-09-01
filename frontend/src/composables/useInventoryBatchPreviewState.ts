import { computed, ref, type Ref } from "vue";

import type { Fixture, IdentifierStockSummary, StockSummary } from "@/types";
import { buildInventoryPreviewStats } from "@/utils/inventoryBatchPreview";
import type {
  InventoryBatchImportRow,
  InventoryBatchOwnershipType,
  InventoryImportMode
} from "@/composables/useInventoryBatchParser";

export type ReadyInventorySubmissionItem = {
  mode: InventoryImportMode;
  transactionNo: string;
  fixtureId: number;
  identifier: string;
  quantity: number;
  ownershipType: InventoryBatchOwnershipType;
  note: string;
  sourceRowCount: number;
};

export function useInventoryBatchPreviewState(options: {
  rows: Ref<InventoryBatchImportRow[]>;
  mode: Ref<InventoryImportMode>;
  fixtures: Ref<Fixture[]>;
  stockRows: Ref<StockSummary[]>;
  identifierStockRows: Ref<IdentifierStockSummary[]>;
}) {
  const showReadyDetails = ref(false);
  const showAllExceptions = ref(false);
  const readyRows = computed(() => options.rows.value.filter((row) => row.status === "ready"));
  const pendingRows = computed(() => options.rows.value.filter((row) => row.status === "needs-confirm" || row.status === "needs-add"));
  const errorRows = computed(() => options.rows.value.filter((row) => row.status === "error"));
  const skippedRows = computed(() => options.rows.value.filter((row) => row.status === "skipped"));
  const exceptionRows = computed(() => options.rows.value.filter((row) => row.status === "needs-confirm" || row.status === "needs-add" || row.status === "error"));
  const visibleExceptionRows = computed(() => showAllExceptions.value ? exceptionRows.value : exceptionRows.value.slice(0, 3));
  const hiddenExceptionCount = computed(() => Math.max(0, exceptionRows.value.length - visibleExceptionRows.value.length));
  const mergedReadyItems = computed<ReadyInventorySubmissionItem[]>(() => {
    const merged = new Map<string, ReadyInventorySubmissionItem>();
    for (const row of readyRows.value) {
      if (!row.resolvedFixtureId || !row.inputToken) continue;
      const key = `${row.mode}::${row.transactionNo}::${row.resolvedFixtureId}::${row.inputToken}::${row.ownershipType}::${row.note}`;
      const existing = merged.get(key);
      if (existing) {
        existing.quantity += row.quantity;
        existing.sourceRowCount += 1;
      } else {
        merged.set(key, {
          mode: row.mode,
          transactionNo: row.transactionNo,
          fixtureId: row.resolvedFixtureId,
          identifier: row.inputToken,
          quantity: row.quantity,
          ownershipType: row.ownershipType,
          note: row.note,
          sourceRowCount: 1
        });
      }
    }
    return [...merged.values()];
  });
  const mergedReadyItemCount = computed(() => mergedReadyItems.value.length);
  const mergedDuplicateReductionCount = computed(() => readyRows.value.length - mergedReadyItemCount.value);
  const mergedDuplicateGroupCount = computed(() => mergedReadyItems.value.filter((item) => item.sourceRowCount > 1).length);
  const readyModes = computed(() => new Set(readyRows.value.map((row) => row.mode)));
  const batchModeLabel = computed(() =>
    readyModes.value.size > 1
      ? "收／退料混合"
      : (readyRows.value[0]?.mode ?? options.mode.value) === "receipt"
        ? "收料"
        : "退料"
  );
  const previewHeadline = computed(() => `預覽 ${options.rows.value.length} 筆｜${batchModeLabel.value}`);
  const canSubmit = computed(() =>
    mergedReadyItems.value.length > 0 &&
    pendingRows.value.length === 0 &&
    errorRows.value.length === 0 &&
    readyRows.value.every((row) => row.transactionNo.trim().length > 0)
  );
  const previewStats = computed(() =>
    buildInventoryPreviewStats(
      options.rows.value.map((row) => ({
        resolvedFixtureId: row.resolvedFixtureId,
        inputToken: row.inputToken,
        quantity: row.mode === "receipt" ? row.quantity : -row.quantity
      })),
      options.identifierStockRows.value,
      options.fixtures.value,
      options.stockRows.value
    )
  );

  return {
    showReadyDetails,
    showAllExceptions,
    readyRows,
    pendingRows,
    errorRows,
    skippedRows,
    exceptionRows,
    visibleExceptionRows,
    hiddenExceptionCount,
    mergedReadyItems,
    mergedReadyItemCount,
    mergedDuplicateReductionCount,
    mergedDuplicateGroupCount,
    readyModes,
    previewHeadline,
    canSubmit,
    previewStats
  };
}
