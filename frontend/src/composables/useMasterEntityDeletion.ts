import { computed, ref, type ComputedRef, type Ref } from "vue";

import { api } from "@/api";
import type { MasterDeleteTargetType } from "@/components/master/MasterPermanentDeleteModal.vue";
import { pushToast } from "@/toastState";

type DeletableMasterTab = MasterDeleteTargetType | "customer" | "user" | "ledger" | "quality";

export function useMasterEntityDeletion(options: {
  activeTab: Ref<DeletableMasterTab>;
  canManage: ComputedRef<boolean>;
  selectedCustomerId: Ref<number | null>;
  selectedFixtureId: Ref<number | null>;
  selectedModelId: Ref<number | null>;
  selectedStationId: Ref<number | null>;
  selectedFixtureCode: ComputedRef<string>;
  selectedModelCode: ComputedRef<string>;
  selectedStationCode: ComputedRef<string>;
  saving: Ref<boolean>;
  selectedTabLabel: () => string;
  movePageBackAfterRemoval: () => void;
  reloadAfterRemoval: () => Promise<void>;
  finishEditing: () => void;
}) {
  const dialogOpen = ref(false);
  const deleteFixtureTransactions = ref(false);
  const deleting = ref(false);
  const targetType = ref<MasterDeleteTargetType | null>(null);

  const targetCode = computed(() => {
    if (targetType.value === "fixture") return options.selectedFixtureCode.value;
    if (targetType.value === "model") return options.selectedModelCode.value;
    if (targetType.value === "station") return options.selectedStationCode.value;
    return "";
  });

  const dialogTitle = computed(() => {
    if (targetType.value === "fixture") return `永久刪除治具 ${targetCode.value}`;
    if (targetType.value === "model") return `永久刪除機種 ${targetCode.value}`;
    if (targetType.value === "station") return `永久刪除站點 ${targetCode.value}`;
    return "永久刪除主資料";
  });

  const dialogIntro = computed(() => {
    if (targetType.value === "fixture") {
      return "治具主檔、庫存摘要與產能需求會永久刪除。請選擇歷史收退料記錄的處理方式。";
    }
    if (targetType.value === "model") {
      return "將一併刪除關聯的機種站點對應、站點治具需求與受影響產能摘要。是否確定刪除？";
    }
    if (targetType.value === "station") {
      return "將一併刪除關聯的機種站點對應、站點治具需求與該站點產能摘要。是否確定刪除？";
    }
    return "";
  });

  function openDialog(): void {
    if (!options.canManage.value) {
      pushToast("只有管理員可以永久刪除主資料。", "warning");
      return;
    }
    if (options.activeTab.value === "fixture" && options.selectedFixtureId.value) {
      targetType.value = "fixture";
    } else if (options.activeTab.value === "model" && options.selectedModelId.value) {
      targetType.value = "model";
    } else if (options.activeTab.value === "station" && options.selectedStationId.value) {
      targetType.value = "station";
    } else {
      pushToast(`請先選擇要刪除的${options.selectedTabLabel()}。`, "warning");
      return;
    }
    deleteFixtureTransactions.value = false;
    dialogOpen.value = true;
  }

  function closeDialog(): void {
    if (deleting.value) return;
    dialogOpen.value = false;
    targetType.value = null;
  }

  async function confirmDeletion(): Promise<void> {
    const customerId = options.selectedCustomerId.value;
    if (!customerId || !targetType.value) {
      pushToast("請先選擇要刪除的主資料與客戶。", "warning");
      return;
    }

    deleting.value = true;
    options.saving.value = true;
    try {
      if (targetType.value === "fixture") {
        const fixtureId = options.selectedFixtureId.value;
        if (!fixtureId) {
          pushToast("請先選擇要刪除的治具。", "warning");
          return;
        }
        const result = await api.deleteFixture(fixtureId, customerId, deleteFixtureTransactions.value);
        options.selectedFixtureId.value = null;
        options.movePageBackAfterRemoval();
        await options.reloadAfterRemoval();
        const recordMessage = result.transaction_records_deleted
          ? `已刪除 ${result.transaction_item_count} 筆相關收退料明細。`
          : `已保留 ${result.transaction_item_count} 筆相關收退料歷史。`;
        pushToast(`治具 ${result.fixture_code} 已永久刪除。${recordMessage}`, "success");
      } else if (targetType.value === "model") {
        const modelId = options.selectedModelId.value;
        if (!modelId) {
          pushToast("請先選擇要刪除的機種。", "warning");
          return;
        }
        const result = await api.deleteModel(modelId, customerId);
        options.selectedModelId.value = null;
        options.movePageBackAfterRemoval();
        await options.reloadAfterRemoval();
        pushToast(
          `機種 ${result.model_code} 已永久刪除。同步刪除 ${result.deleted_model_station_count} 筆機種站點對應、${result.deleted_requirement_count} 筆治具需求、${result.deleted_capacity_summary_count} 筆產能摘要。`,
          "success"
        );
      } else {
        const stationId = options.selectedStationId.value;
        if (!stationId) {
          pushToast("請先選擇要刪除的站點。", "warning");
          return;
        }
        const result = await api.deleteStation(stationId, customerId);
        options.selectedStationId.value = null;
        options.movePageBackAfterRemoval();
        await options.reloadAfterRemoval();
        pushToast(
          `站點 ${result.station_code} 已永久刪除。同步刪除 ${result.deleted_model_station_count} 筆機種站點對應、${result.deleted_requirement_count} 筆治具需求、${result.deleted_capacity_summary_count} 筆產能摘要。`,
          "success"
        );
      }
      options.finishEditing();
      dialogOpen.value = false;
      targetType.value = null;
    } catch (error) {
      pushToast(error instanceof Error ? error.message : "主資料刪除失敗", "error");
    } finally {
      deleting.value = false;
      options.saving.value = false;
    }
  }

  return {
    dialogOpen,
    deleteFixtureTransactions,
    deleting,
    targetType,
    dialogTitle,
    dialogIntro,
    openDialog,
    closeDialog,
    confirmDeletion
  };
}
