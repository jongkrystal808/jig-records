import { ref, type Ref } from "vue";

import { api } from "@/api";
import { ApiRequestError } from "@/api/core";
import { requestConfirmation } from "@/confirmState";
import { pushToast } from "@/toastState";
import type { InventoryBatchImportRow } from "@/composables/useInventoryBatchParser";
import type { ReadyInventorySubmissionItem } from "@/composables/useInventoryBatchPreviewState";

export function useInventoryBatchSubmit(options: {
  customerId: () => number | undefined;
  tutorialMode: () => boolean;
  createdBy: () => string;
  readyRows: Ref<InventoryBatchImportRow[]>;
  mergedReadyItems: Ref<ReadyInventorySubmissionItem[]>;
  canSubmit: Ref<boolean>;
  clearPanel: () => void;
  emitSuccess: () => void;
  reloadFixtures: () => Promise<void>;
}) {
  const saving = ref(false);

  async function submit(): Promise<void> {
    const customerId = options.customerId();
    if (!customerId) return;
    if (options.readyRows.value.some((row) => !row.transactionNo.trim())) {
      pushToast("每一筆資料都必須填寫單號。", "warning");
      return;
    }
    if (!options.canSubmit.value) return;

    saving.value = true;
    try {
      if (options.tutorialMode()) {
        options.clearPanel();
        options.emitSuccess();
        pushToast("教學試跑完成，未寫入正式收退料資料。", "success");
        return;
      }
      const groups = new Map<string, ReadyInventorySubmissionItem[]>();
      for (const item of options.mergedReadyItems.value) {
        const key = `${item.mode}::${item.transactionNo}`;
        groups.set(key, [...(groups.get(key) ?? []), item]);
      }

      for (const groupItems of groups.values()) {
        const firstItem = groupItems[0];
        if (!firstItem) continue;
        const payload = {
          customer_id: customerId,
          created_by: options.createdBy(),
          transaction_no: firstItem.transactionNo.trim(),
          items: groupItems.map((item) => ({
            fixture_id: item.fixtureId,
            ownership_type: item.ownershipType,
            identifier: item.identifier,
            quantity: item.quantity,
            note: item.note || undefined
          }))
        };
        const sendTransaction = async (confirmDuplicate = false) => {
          if (firstItem.mode === "receipt") {
            await api.createReceiptWithOptions(payload, { confirmDuplicate });
          } else {
            await api.createReturnWithOptions(payload, { confirmDuplicate });
          }
        };

        try {
          await sendTransaction();
        } catch (error) {
          if (error instanceof ApiRequestError && error.status === 409) {
            const confirmed = await requestConfirmation(error.message, {
              title: `單號 ${firstItem.transactionNo} 已存在`,
              confirmLabel: "仍要送出",
              tone: "danger"
            });
            if (!confirmed) return;
            await sendTransaction(true);
          } else {
            throw error;
          }
        }
      }
      options.clearPanel();
      options.emitSuccess();
      await options.reloadFixtures();
    } catch (error) {
      await options.reloadFixtures();
      pushToast(error instanceof Error ? error.message : "收退料送出失敗", "error");
    } finally {
      saving.value = false;
    }
  }

  return { saving, submit };
}
