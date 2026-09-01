import { computed, ref, watch, type Ref } from "vue";

import { api } from "@/api";
import { requestConfirmation } from "@/confirmState";
import { pushToast } from "@/toastState";
import type { MaterialTransaction, TransactionQueryFilters } from "@/types";
import { pageAfterItemRemoval } from "@/utils/pagination";

type ReloadOptions = {
  preserveListPage?: boolean;
  preserveLedgerPage?: boolean;
  focusSelectedLedgerRow?: boolean;
};

function normalized(value: string): string {
  return value.trim();
}

function transactionNo(value: string | null | undefined): string {
  return value?.trim() || "（無單號）";
}

export function useMasterLedger(options: {
  selectedCustomerId: Ref<number | null>;
  canManage: () => boolean;
  reloadData: (options: ReloadOptions) => Promise<void>;
}) {
  const ledgerTransactions = ref<MaterialTransaction[]>([]);
  const ledgerTransactionNoFilter = ref("");
  const ledgerCreatedByFilter = ref("");
  const ledgerFixtureCodeFilter = ref("");
  const ledgerTypeFilter = ref<Array<"receipt" | "return">>([]);
  const ledgerPage = ref(1);
  const ledgerPageSize = ref(12);
  const ledgerTotal = ref(0);
  const ledgerLoading = ref(false);
  const ledgerProcessing = ref(false);
  const selectedLedgerTransactionId = ref<number | null>(null);

  const ledgerTotalPages = computed(() =>
    Math.max(1, Math.ceil(ledgerTotal.value / ledgerPageSize.value))
  );
  const selectedLedgerTransaction = computed(
    () =>
      ledgerTransactions.value.find(
        (row) => row.id === selectedLedgerTransactionId.value
      ) ?? null
  );

  function buildFilters(): TransactionQueryFilters {
    return {
      transaction_type: ledgerTypeFilter.value.length ? [...ledgerTypeFilter.value] : undefined,
      transaction_no: normalized(ledgerTransactionNoFilter.value) || undefined,
      created_by: normalized(ledgerCreatedByFilter.value) || undefined,
      fixture_code: normalized(ledgerFixtureCodeFilter.value) || undefined
    };
  }

  async function loadLedgerPage(
    loadOptions: { preserveSelection?: boolean } = {}
  ): Promise<void> {
    const customerId = options.selectedCustomerId.value ?? undefined;
    if (!options.canManage() || !customerId) {
      ledgerTransactions.value = [];
      ledgerTotal.value = 0;
      selectedLedgerTransactionId.value = null;
      return;
    }
    ledgerLoading.value = true;
    try {
      const response = await api.listTransactionLedgerPage(
        ledgerPage.value,
        ledgerPageSize.value,
        customerId,
        buildFilters()
      );
      const totalPages = Math.max(1, Math.ceil(response.total / response.page_size));
      if (ledgerPage.value > totalPages) {
        ledgerPage.value = totalPages;
        return;
      }
      ledgerTransactions.value = response.items;
      ledgerTotal.value = response.total;
      if (
        loadOptions.preserveSelection &&
        response.items.some((row) => row.id === selectedLedgerTransactionId.value)
      ) {
        return;
      }
      selectedLedgerTransactionId.value =
        response.items.find((row) => row.id === selectedLedgerTransactionId.value)?.id ??
        response.items[0]?.id ??
        null;
    } catch (error) {
      ledgerTransactions.value = [];
      ledgerTotal.value = 0;
      selectedLedgerTransactionId.value = null;
      pushToast(error instanceof Error ? error.message : "載入收退料帳目失敗", "error");
    } finally {
      ledgerLoading.value = false;
    }
  }

  function focusSelectedLedgerRow(fallbackPage = ledgerPage.value): void {
    ledgerPage.value = Math.min(Math.max(1, fallbackPage), ledgerTotalPages.value);
    if (ledgerTransactions.value.length === 0) {
      selectedLedgerTransactionId.value = null;
      return;
    }
    if (!ledgerTransactions.value.some((row) => row.id === selectedLedgerTransactionId.value)) {
      selectedLedgerTransactionId.value = ledgerTransactions.value[0]?.id ?? null;
    }
  }

  function resetLedgerFilters(): void {
    ledgerTransactionNoFilter.value = "";
    ledgerCreatedByFilter.value = "";
    ledgerFixtureCodeFilter.value = "";
    ledgerTypeFilter.value = [];
    ledgerPage.value = 1;
  }

  function focusFixtureInLedger(fixtureCode: string): void {
    ledgerTransactionNoFilter.value = "";
    ledgerCreatedByFilter.value = "";
    ledgerFixtureCodeFilter.value = fixtureCode;
    ledgerTypeFilter.value = [];
    ledgerPage.value = 1;
  }

  function selectLedgerTransaction(id: number): void {
    selectedLedgerTransactionId.value = id;
  }

  function updateLedgerTransactionNo(value: string): void {
    ledgerTransactionNoFilter.value = value;
  }
  function updateLedgerCreatedBy(value: string): void {
    ledgerCreatedByFilter.value = value;
  }
  function updateLedgerFixtureCode(value: string): void {
    ledgerFixtureCodeFilter.value = value;
  }
  function updateLedgerTypeFilter(value: Array<"receipt" | "return">): void {
    ledgerTypeFilter.value = value;
  }
  function updateLedgerPageSize(value: number): void {
    ledgerPageSize.value = value;
  }
  function previousLedgerPage(): void {
    ledgerPage.value = Math.max(1, ledgerPage.value - 1);
  }
  function nextLedgerPage(): void {
    ledgerPage.value = Math.min(ledgerTotalPages.value, ledgerPage.value + 1);
  }

  async function reloadLedgerSelection(): Promise<void> {
    await loadLedgerPage({ preserveSelection: true });
  }

  async function recalculateLedgerState(
    recalculateOptions?: { skipConfirm?: boolean }
  ): Promise<void> {
    const customerId = options.selectedCustomerId.value;
    if (!customerId) {
      pushToast("請先選擇客戶。", "warning");
      return;
    }
    if (
      !recalculateOptions?.skipConfirm &&
      !(await requestConfirmation("將依目前交易明細全量重算庫存摘要。要繼續嗎？", {
        title: "全量重算庫存？",
        confirmLabel: "開始重算"
      }))
    ) {
      return;
    }
    ledgerProcessing.value = true;
    try {
      const result = await api.recalculateInventoryState(customerId);
      await options.reloadData({ preserveListPage: true, focusSelectedLedgerRow: true });
      pushToast(
        `重算完成：${result.fixture_count} 個治具、${result.item_count} 筆明細。`,
        "success"
      );
    } catch (error) {
      pushToast(error instanceof Error ? error.message : "重算失敗", "error");
    } finally {
      ledgerProcessing.value = false;
    }
  }

  async function reverseSelectedLedgerTransaction(): Promise<void> {
    const customerId = options.selectedCustomerId.value;
    if (!customerId) {
      pushToast("請先選擇客戶。", "warning");
      return;
    }
    const selected = selectedLedgerTransaction.value;
    if (!selected) {
      pushToast("請先選擇要撤回的案件。", "warning");
      return;
    }
    if (
      !(await requestConfirmation(
        `確定要撤回單號 ${transactionNo(selected.transaction_no)}？這會刪除整筆${selected.transaction_type === "receipt" ? "收料" : "退料"}案件並重算庫存。`,
        { title: "撤回收退料案件？", confirmLabel: "撤回案件", tone: "danger" }
      ))
    ) {
      return;
    }
    ledgerProcessing.value = true;
    try {
      const result = await api.reverseTransaction(selected.id, customerId);
      ledgerPage.value = pageAfterItemRemoval(ledgerPage.value, ledgerTransactions.value.length);
      await options.reloadData({ preserveListPage: true, focusSelectedLedgerRow: true });
      pushToast(
        `已撤回 ${transactionNo(result.transaction_no)}，共 ${result.item_count} 筆明細。`,
        "success"
      );
      if (
        await requestConfirmation("案件已撤回。要接著再執行一次全量重算嗎？", {
          title: "執行全量重算？",
          confirmLabel: "接著重算"
        })
      ) {
        await recalculateLedgerState({ skipConfirm: true });
      }
    } catch (error) {
      pushToast(error instanceof Error ? error.message : "撤回案件失敗", "error");
    } finally {
      ledgerProcessing.value = false;
    }
  }

  watch(
    [
      ledgerTransactionNoFilter,
      ledgerCreatedByFilter,
      ledgerFixtureCodeFilter,
      ledgerTypeFilter,
      ledgerPageSize
    ],
    async () => {
      if (ledgerPage.value !== 1) {
        ledgerPage.value = 1;
        return;
      }
      await loadLedgerPage();
    }
  );
  watch(ledgerPage, async () => loadLedgerPage());

  return {
    ledgerTransactions,
    ledgerTransactionNoFilter,
    ledgerCreatedByFilter,
    ledgerFixtureCodeFilter,
    ledgerTypeFilter,
    ledgerPage,
    ledgerPageSize,
    ledgerTotal,
    ledgerLoading,
    ledgerProcessing,
    ledgerTotalPages,
    selectedLedgerTransactionId,
    selectedLedgerTransaction,
    loadLedgerPage,
    focusSelectedLedgerRow,
    resetLedgerFilters,
    focusFixtureInLedger,
    selectLedgerTransaction,
    updateLedgerTransactionNo,
    updateLedgerCreatedBy,
    updateLedgerFixtureCode,
    updateLedgerTypeFilter,
    updateLedgerPageSize,
    previousLedgerPage,
    nextLedgerPage,
    reloadLedgerSelection,
    recalculateLedgerState,
    reverseSelectedLedgerTransaction
  };
}
