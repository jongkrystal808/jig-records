import { computed, ref, watch, type ComputedRef, type Ref } from "vue";

import { api } from "@/api";
import { pushToast } from "@/toastState";
import type { Fixture, MachineModel, Station } from "@/types";
import {
  acceptSimilarEntity as acceptSimilarEntityHelper,
  parseMappingBatchText,
  parseRequirementBatchText,
  rejectSimilarEntity as rejectSimilarEntityHelper,
  setEntityReady,
  skipMappingBatchRow as skipMappingBatchRowHelper,
  skipRequirementBatchRow as skipRequirementBatchRowHelper,
  syncMappingBatchRow,
  syncRequirementBatchRow,
  toCsv,
  type ProductionBatchCollections,
  type ProductionBatchEntityResolution,
  type ProductionMappingBatchRow,
  type ProductionRequirementBatchRow
} from "@/utils/productionBatchImport";

type UseProductionBatchImportOptions = {
  models: Ref<MachineModel[]>;
  stations: Ref<Station[]>;
  fixtures: Ref<Fixture[]>;
  selectedCustomerId: Ref<number | null>;
  selectedModelCode: ComputedRef<string>;
  onImported: () => Promise<void>;
};

export function useProductionBatchImport(options: UseProductionBatchImportOptions) {
  const showMappingBatchModal = ref(false);
  const showRequirementBatchModal = ref(false);
  const mappingBatchText = ref("");
  const requirementBatchText = ref("");
  const mappingBatchRows = ref<ProductionMappingBatchRow[]>([]);
  const requirementBatchRows = ref<ProductionRequirementBatchRow[]>([]);
  const savingMapping = ref(false);
  const savingRequirement = ref(false);

  const collections = computed<ProductionBatchCollections>(() => ({
    models: options.models.value,
    stations: options.stations.value,
    fixtures: options.fixtures.value
  }));
  const mappingReadyRows = computed(() => mappingBatchRows.value.filter((row) => row.status === "ready"));
  const mappingPendingRows = computed(() => mappingBatchRows.value.filter((row) => row.status === "needs-confirm" || row.status === "needs-add"));
  const mappingErrorRows = computed(() => mappingBatchRows.value.filter((row) => row.status === "error"));
  const requirementReadyRows = computed(() => requirementBatchRows.value.filter((row) => row.status === "ready"));
  const requirementPendingRows = computed(() => requirementBatchRows.value.filter((row) => row.status === "needs-confirm" || row.status === "needs-add"));
  const requirementErrorRows = computed(() => requirementBatchRows.value.filter((row) => row.status === "error"));

  function refreshMappingBatchPreview(): void {
    mappingBatchRows.value = parseMappingBatchText(mappingBatchText.value, collections.value);
  }

  function refreshRequirementBatchPreview(): void {
    requirementBatchRows.value = parseRequirementBatchText(requirementBatchText.value, collections.value);
  }

  function clearMappingBatchImport(): void {
    mappingBatchText.value = "";
    mappingBatchRows.value = [];
  }

  function clearRequirementBatchImport(): void {
    requirementBatchText.value = "";
    requirementBatchRows.value = [];
  }

  function skipMappingBatchRow(row: ProductionMappingBatchRow): void {
    skipMappingBatchRowHelper(row);
  }

  function skipRequirementBatchRow(row: ProductionRequirementBatchRow): void {
    skipRequirementBatchRowHelper(row);
  }

  function acceptSimilarEntity(entity: ProductionBatchEntityResolution): void {
    acceptSimilarEntityHelper(collections.value, entity);
  }

  function rejectSimilarEntity(entity: ProductionBatchEntityResolution): void {
    rejectSimilarEntityHelper(entity);
  }

  async function createEntityForBatch(entity: ProductionBatchEntityResolution): Promise<void> {
    if (!options.selectedCustomerId.value || !entity.inputCode) {
      pushToast("請先選擇客戶。", "warning");
      return;
    }

    try {
      if (entity.kind === "model") {
        const created = await api.createModel({ customer_id: options.selectedCustomerId.value, code: entity.inputCode, name: entity.inputCode });
        options.models.value = [...options.models.value.filter((row) => row.id !== created.id), created];
        setEntityReady(entity, created.id, created.code, "已新增機種並加入匯入清單");
        pushToast(`已新增機種：${created.code}`, "success");
        return;
      }
      if (entity.kind === "station") {
        const created = await api.createStation({ customer_id: options.selectedCustomerId.value, code: entity.inputCode, name: entity.inputCode });
        options.stations.value = [...options.stations.value.filter((row) => row.id !== created.id), created];
        setEntityReady(entity, created.id, created.code, "已新增站點並加入匯入清單");
        pushToast(`已新增站點：${created.code}`, "success");
        return;
      }
      const created = await api.createFixture({
        customer_id: options.selectedCustomerId.value,
        code: entity.inputCode,
        name: entity.inputCode,
        min_stock_qty: 0,
        description: "由 production 批次匯入建立"
      });
      options.fixtures.value = [...options.fixtures.value.filter((row) => row.id !== created.id), created];
      setEntityReady(entity, created.id, created.code, "已新增治具並加入匯入清單");
      pushToast(`已新增治具：${created.code}`, "success");
    } catch (err) {
      pushToast(err instanceof Error ? err.message : `新增${entity.label}失敗`, "error");
    }
  }

  function syncMappingRowAfterEntityChange(row: ProductionMappingBatchRow): void {
    syncMappingBatchRow(row);
  }

  function syncRequirementRowAfterEntityChange(row: ProductionRequirementBatchRow): void {
    syncRequirementBatchRow(row);
  }

  async function submitMappingBatchImport(): Promise<void> {
    if (!options.selectedCustomerId.value) {
      pushToast("請先選擇客戶。", "warning");
      return;
    }
    if (mappingBatchRows.value.length === 0) {
      pushToast("請先貼上機種 / 站點資料。", "warning");
      return;
    }
    if (mappingPendingRows.value.length > 0) {
      pushToast("還有待確認的機種 / 站點列，請先完成同一 / 新增 / 略過。", "warning");
      return;
    }
    if (mappingErrorRows.value.length > 0) {
      pushToast("表格中有錯誤列，請先修正後再匯入。", "warning");
      return;
    }

    savingMapping.value = true;
    try {
      const rows = mappingReadyRows.value.map((row) => [row.model.resolvedCode, row.station.resolvedCode]);
      const csv = toCsv(["model_code", "station_code"], rows);
      const result = await api.importModelStationsCsv(options.selectedCustomerId.value, csv, "batch-model-stations.csv");
      showMappingBatchModal.value = false;
      clearMappingBatchImport();
      await options.onImported();
      pushToast(`批次貼上匯入 Mapping 完成，共 ${result.imported_count} 筆。`, "success");
    } catch (err) {
      pushToast(err instanceof Error ? err.message : "批次匯入 mapping 失敗", "error");
    } finally {
      savingMapping.value = false;
    }
  }

  async function submitRequirementBatchImport(): Promise<void> {
    if (!options.selectedCustomerId.value) {
      pushToast("請先選擇客戶。", "warning");
      return;
    }
    if (!options.selectedModelCode.value) {
      pushToast("請先選擇機種。", "warning");
      return;
    }
    if (requirementBatchRows.value.length === 0) {
      pushToast("請先貼上站點 / 治具 / 數量資料。", "warning");
      return;
    }
    if (requirementPendingRows.value.length > 0) {
      pushToast("還有待確認的站點 / 治具列，請先完成同一 / 新增 / 略過。", "warning");
      return;
    }
    if (requirementErrorRows.value.length > 0) {
      pushToast("表格中有錯誤列，請先修正後再匯入。", "warning");
      return;
    }

    savingRequirement.value = true;
    try {
      const rows = requirementReadyRows.value.map((row) => [
        options.selectedModelCode.value,
        row.station.resolvedCode,
        row.fixture.resolvedCode,
        String(row.quantity)
      ]);
      const csv = toCsv(["model_code", "station_code", "fixture_code", "required_qty"], rows);
      const result = await api.importFixtureRequirementsCsv(options.selectedCustomerId.value, csv, "batch-fixture-requirements.csv");
      showRequirementBatchModal.value = false;
      clearRequirementBatchImport();
      await options.onImported();
      pushToast(`批次貼上匯入 Requirement 完成，共 ${result.imported_count} 筆。`, "success");
    } catch (err) {
      pushToast(err instanceof Error ? err.message : "批次匯入 requirement 失敗", "error");
    } finally {
      savingRequirement.value = false;
    }
  }

  watch(mappingBatchText, refreshMappingBatchPreview);
  watch(requirementBatchText, refreshRequirementBatchPreview);

  return {
    showMappingBatchModal,
    showRequirementBatchModal,
    mappingBatchText,
    requirementBatchText,
    mappingBatchRows,
    requirementBatchRows,
    mappingReadyRows,
    mappingPendingRows,
    mappingErrorRows,
    requirementReadyRows,
    requirementPendingRows,
    requirementErrorRows,
    savingMapping,
    savingRequirement,
    clearMappingBatchImport,
    clearRequirementBatchImport,
    skipMappingBatchRow,
    skipRequirementBatchRow,
    acceptSimilarEntity,
    rejectSimilarEntity,
    createEntityForBatch,
    syncMappingRowAfterEntityChange,
    syncRequirementRowAfterEntityChange,
    submitMappingBatchImport,
    submitRequirementBatchImport
  };
}
