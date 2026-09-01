<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "@/api";
import { authSession, customers, onboardingActive, onboardingPickerOpen, onboardingStepIndex, selectedCustomerId, setCustomerSwitchGuard } from "@/appState";
import MasterDetailPanel from "@/components/master/MasterDetailPanel.vue";
import FixtureQualityQuickEditModal from "@/components/master/FixtureQualityQuickEditModal.vue";
import MasterListPanel from "@/components/master/MasterListPanel.vue";
import MasterPermanentDeleteModal from "@/components/master/MasterPermanentDeleteModal.vue";
import FixtureQualityPanel from "@/components/master/FixtureQualityPanel.vue";
import MasterToolbar from "@/components/master/MasterToolbar.vue";
import TransactionAccountDetailPanel from "@/components/master/TransactionAccountDetailPanel.vue";
import TransactionAccountListPanel from "@/components/master/TransactionAccountListPanel.vue";
import UiSummaryCards from "@/components/UiSummaryCards.vue";
import { useMasterCrudActions } from "@/composables/useMasterCrudActions";
import { useMasterEntityDeletion } from "@/composables/useMasterEntityDeletion";
import { useMasterLedger } from "@/composables/useMasterLedger";
import { useMasterQuality } from "@/composables/useMasterQuality";
import { requestConfirmation } from "@/confirmState";
import { pageAfterItemRemoval } from "@/utils/pagination";
import { pushToast } from "@/toastState";
import type { AppUser, Customer, Fixture, MachineModel, Station } from "@/types";
import { fallbackText } from "@/utils/display";
import { canManageAccounts, canManageAdminReports } from "@/utils/roles";

type MasterTab = "fixture" | "model" | "station" | "customer" | "user" | "ledger" | "quality";

const router = useRouter();
const route = useRoute();

const fixtures = ref<Fixture[]>([]);
const models = ref<MachineModel[]>([]);
const stations = ref<Station[]>([]);
const users = ref<AppUser[]>([]);
const customerRows = ref<Customer[]>([]);
const customerAssignedUsers = ref<AppUser[]>([]);
const masterToolbarRef = ref<InstanceType<typeof MasterToolbar> | null>(null);
const fixtureImageBatchFiles = ref<File[]>([]);
const fixtureImageBatchUploading = ref(false);
const isMobileMasterFlow = ref(false);
const mobileMasterDetailOpen = ref(false);
const editorMode = ref<"summary" | "edit" | "create">("summary");

const activeTab = ref<MasterTab>("fixture");
const keyword = ref("");
const statusFilter = ref<Array<"active" | "inactive">>([]);
const loading = ref(false);
const saving = ref(false);
const listPage = ref(1);
const listPageSize = 10;

const selectedFixtureId = ref<number | null>(null);
const selectedModelId = ref<number | null>(null);
const selectedStationId = ref<number | null>(null);
const selectedUserId = ref<number | null>(null);
const selectedCustomerRowId = ref<number | null>(null);

const {
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
} = useMasterLedger({
  selectedCustomerId,
  canManage: () => canManageAdminReports(authSession.value?.role),
  reloadData: (options) => loadData(false, options)
});

const {
  fixtureQualityReport,
  qualityQuickEditOpen,
  qualityQuickEditIssueCode,
  qualityQuickEditFixture,
  qualityQuickEditForm,
  qualityQuickEditSaving,
  qualityInlineSavingFixtureId,
  qualityRelationSaving,
  qualityRelationModelId,
  qualityRelationStationId,
  qualityRelationRequiredQty,
  qualityRelationStationOptions,
  qualityImageInput,
  qualityImageFile,
  qualityImageUploading,
  qualityImageUrl,
  qualityImageLoading,
  qualityQuickEditTitle,
  openIssueEditorFromQuality,
  openLedgerFromQuality,
  closeQualityQuickEdit,
  updateQualityImageFile,
  saveQualityQuickEdit,
  saveInlineQualityIssue,
  saveQualityRelation,
  uploadQualityImage
} = useMasterQuality({
  fixtures,
  models,
  stations,
  selectedCustomerId,
  reloadData: () =>
    loadData(false, { preserveListPage: true, preserveLedgerPage: true }),
  openRequirements: async () => {
    await router.push({ name: "production-requirements" });
  },
  openLedger: async (fixtureCode) => {
    focusFixtureInLedger(fixtureCode);
    await router.push("/master/ledger");
  }
});

const qualityQuickEditBusy = computed(
  () => qualityQuickEditSaving.value || qualityRelationSaving.value || qualityImageUploading.value
);

function closeQualityQuickEditDialog(): void {
  if (!qualityQuickEditBusy.value) closeQualityQuickEdit();
}

const fixtureForm = ref(makeEmptyFixtureForm());
const modelForm = ref(makeEmptyModelForm());
const stationForm = ref(makeEmptyStationForm());
const customerForm = ref(makeEmptyCustomerForm());
const userForm = ref(makeEmptyUserForm());
const canManageUsers = computed(() => canManageAccounts(authSession.value?.role));
const canManageCustomers = computed(() => canManageAccounts(authSession.value?.role));
const canManageLedger = computed(() => canManageAdminReports(authSession.value?.role));
const canManageQuality = computed(() => canManageAdminReports(authSession.value?.role));
const canManageMasterEntities = computed(() => canManageAdminReports(authSession.value?.role));
const selectedCustomerScopeCount = computed(() => customerFormAssignedUserIds.value.length);
const customerFormAssignedUserIds = ref<number[]>([]);
const selectedGlobalCustomer = computed(() => customers.value.find((row) => row.id === selectedCustomerId.value) ?? null);
const { saveCurrent, toggleCurrentActive } = useMasterCrudActions({
  activeTab,
  selectedCustomerId,
  selectedFixtureId,
  selectedModelId,
  selectedStationId,
  selectedCustomerRowId,
  selectedUserId,
  fixtureForm,
  modelForm,
  stationForm,
  customerForm,
  userForm,
  customerAssignedUserIds: customerFormAssignedUserIds,
  saving,
  reloadSelection: () => loadData(false, { focusSelectedListRow: true, preserveLedgerPage: true }),
  finishEditing: () => {
    editorMode.value = "summary";
  }
});
const canCreateInCurrentTab = computed(() => {
  if (activeTab.value === "ledger" || activeTab.value === "quality") {
    return false;
  }
  return activeTab.value !== "customer" || canManageCustomers.value;
});

function normalizeText(value: string | null | undefined): string {
  return (value ?? "").trim();
}

function syncMasterViewport(): void {
  isMobileMasterFlow.value = window.innerWidth <= 1100;
  if (!isMobileMasterFlow.value) {
    mobileMasterDetailOpen.value = false;
  }
}

function makeEmptyFixtureForm() {
  return {
    code: "",
    name: "",
    responsible_user_id: null as number | null,
    line_storage_location: "",
    department_storage_location: "",
    min_stock_qty: 0,
    description: "",
    is_active: true
  };
}

function makeEmptyModelForm() {
  return { code: "", name: "", is_active: true };
}

function clearFixtureImageBatchSelection(): void {
  fixtureImageBatchFiles.value = [];
  masterToolbarRef.value?.resetImageInput();
}

function makeEmptyStationForm() {
  return { code: "", name: "", is_active: true };
}

function makeEmptyCustomerForm() {
  return { code: "", name: "" };
}

function makeEmptyUserForm() {
  return {
    username: "",
    email: "",
    display_name: "",
    role: "user",
    is_active: true,
    password: "",
    reset_password: "",
    allowed_customer_ids: selectedCustomerId.value ? [selectedCustomerId.value] : []
  };
}

function makeFixtureFormFromRow(row: Fixture) {
  return {
    code: row.code,
    name: row.name,
    responsible_user_id: row.responsible_user_id,
    line_storage_location: row.line_storage_location ?? "",
    department_storage_location: row.department_storage_location ?? "",
    min_stock_qty: row.min_stock_qty,
    description: row.description ?? "",
    is_active: row.is_active
  };
}

const tabTitleMap: Record<MasterTab, string> = {
  fixture: "治具",
  model: "機種",
  station: "站點",
  user: "使用者",
  customer: "客戶",
  ledger: "收退料帳目",
  quality: "治具資料品質"
};

const mobileDetailHeading = computed(() => {
  if (editorMode.value === "create") return `新增${tabTitleMap[activeTab.value]}`;
  return selectedDetailLabel.value || `${tabTitleMap[activeTab.value]}明細`;
});

const TAB_PATH_MAP: Record<MasterTab, string> = {
  fixture: "/master/fixtures",
  model: "/master/models",
  station: "/master/stations",
  customer: "/master/customers",
  user: "/master/users",
  ledger: "/master/ledger",
  quality: "/master/quality"
};

function resolveMasterTabFromPath(pathname: string): MasterTab {
  if (pathname === "/master/models") return "model";
  if (pathname === "/master/stations") return "station";
  if (pathname === "/master/customers") return "customer";
  if (pathname === "/master/users") return "user";
  if (pathname === "/master/ledger") return "ledger";
  if (pathname === "/master/quality") return "quality";
  return "fixture";
}

const searchPlaceholder = computed(() => `搜尋${tabTitleMap[activeTab.value]}編號 / 名稱`);

const filteredFixtures = computed(() =>
  fixtures.value.filter((row) => {
    const byKeyword =
      !keyword.value ||
      row.code.toLowerCase().includes(keyword.value.toLowerCase()) ||
      row.name.toLowerCase().includes(keyword.value.toLowerCase());
    const byStatus =
      statusFilter.value.length === 0 ||
      (statusFilter.value.includes("active") && row.is_active) ||
      (statusFilter.value.includes("inactive") && !row.is_active);
    return byKeyword && byStatus;
  })
);

const filteredModels = computed(() =>
  models.value.filter((row) => {
    const byKeyword =
      !keyword.value ||
      row.code.toLowerCase().includes(keyword.value.toLowerCase()) ||
      row.name.toLowerCase().includes(keyword.value.toLowerCase());
    const byStatus =
      statusFilter.value.length === 0 ||
      (statusFilter.value.includes("active") && row.is_active) ||
      (statusFilter.value.includes("inactive") && !row.is_active);
    return byKeyword && byStatus;
  })
);

const filteredStations = computed(() =>
  stations.value.filter((row) => {
    const byKeyword =
      !keyword.value ||
      row.code.toLowerCase().includes(keyword.value.toLowerCase()) ||
      row.name.toLowerCase().includes(keyword.value.toLowerCase());
    const byStatus =
      statusFilter.value.length === 0 ||
      (statusFilter.value.includes("active") && row.is_active) ||
      (statusFilter.value.includes("inactive") && !row.is_active);
    return byKeyword && byStatus;
  })
);

const filteredCustomers = computed(() =>
  customerRows.value.filter(
    (row) =>
      !keyword.value ||
      row.code.toLowerCase().includes(keyword.value.toLowerCase()) ||
      row.name.toLowerCase().includes(keyword.value.toLowerCase())
  )
);

const filteredUsers = computed(() =>
  users.value.filter((row) => {
    const byKeyword =
      !keyword.value ||
      row.username.toLowerCase().includes(keyword.value.toLowerCase()) ||
      (row.email ?? "").toLowerCase().includes(keyword.value.toLowerCase()) ||
      row.display_name.toLowerCase().includes(keyword.value.toLowerCase());
    const byStatus =
      statusFilter.value.length === 0 ||
      (statusFilter.value.includes("active") && row.is_active) ||
      (statusFilter.value.includes("inactive") && !row.is_active);
    return byKeyword && byStatus;
  })
);

const currentRows = computed(() => {
  if (activeTab.value === "fixture") return filteredFixtures.value;
  if (activeTab.value === "model") return filteredModels.value;
  if (activeTab.value === "station") return filteredStations.value;
  if (activeTab.value === "customer") return filteredCustomers.value;
  if (activeTab.value === "ledger") return ledgerTransactions.value;
  return filteredUsers.value;
});

const listTotalPages = computed(() => Math.max(1, Math.ceil(currentRows.value.length / listPageSize)));
const pagedFixtureRows = computed(() => filteredFixtures.value.slice((listPage.value - 1) * listPageSize, listPage.value * listPageSize));
const pagedModelRows = computed(() => filteredModels.value.slice((listPage.value - 1) * listPageSize, listPage.value * listPageSize));
const pagedStationRows = computed(() => filteredStations.value.slice((listPage.value - 1) * listPageSize, listPage.value * listPageSize));
const pagedCustomerRows = computed(() => filteredCustomers.value.slice((listPage.value - 1) * listPageSize, listPage.value * listPageSize));
const pagedUserRows = computed(() => filteredUsers.value.slice((listPage.value - 1) * listPageSize, listPage.value * listPageSize));

const emptyStateMessage = computed(() => {
  if (loading.value) return "資料載入中...";
  if (keyword.value) return `找不到符合「${keyword.value}」的資料`;
  if (statusFilter.value.length) return "目前篩選條件下沒有資料";
  return `目前沒有${tabTitleMap[activeTab.value]}資料`;
});

const selectedFixture = computed(() => fixtures.value.find((row) => row.id === selectedFixtureId.value) ?? null);
const selectedModel = computed(() => models.value.find((row) => row.id === selectedModelId.value) ?? null);
const selectedStation = computed(() => stations.value.find((row) => row.id === selectedStationId.value) ?? null);
const selectedUser = computed(() => users.value.find((row) => row.id === selectedUserId.value) ?? null);
const selectedCustomerRow = computed(() => customerRows.value.find((row) => row.id === selectedCustomerRowId.value) ?? null);
const selectedDetailLabel = computed(() =>
  fallbackText(
      selectedFixture.value?.code ||
      selectedModel.value?.code ||
      selectedStation.value?.code ||
      selectedCustomerRow.value?.code ||
      selectedUser.value?.username
  )
);
const isCreateMode = computed(() => editorMode.value === "create");
const hasSelectedMasterRow = computed(() => {
  if (activeTab.value === "fixture") return selectedFixture.value !== null;
  if (activeTab.value === "model") return selectedModel.value !== null;
  if (activeTab.value === "station") return selectedStation.value !== null;
  if (activeTab.value === "customer") return selectedCustomerRow.value !== null;
  if (activeTab.value === "user") return selectedUser.value !== null;
  return false;
});
const masterSummaryFields = computed(() => {
  const yesNoStatus = (active: boolean) => (active ? "啟用中" : "停用");
  if (activeTab.value === "fixture" && selectedFixture.value) {
    const row = selectedFixture.value;
    const responsibleUser = users.value.find((user) => user.id === row.responsible_user_id);
    return [
      { label: "治具編號", value: fallbackText(row.code) },
      { label: "治具名稱", value: fallbackText(row.name) },
      { label: "產線儲位", value: fallbackText(row.line_storage_location, "未設定") },
      { label: "部門儲位", value: fallbackText(row.department_storage_location, "未設定") },
      { label: "最低水位", value: String(row.min_stock_qty) },
      { label: "負責人", value: responsibleUser?.display_name ?? "未指定" },
      { label: "狀態", value: yesNoStatus(row.is_active) },
      { label: "備註", value: fallbackText(row.description, "無") }
    ];
  }
  if (activeTab.value === "model" && selectedModel.value) {
    return [
      { label: "機種編號", value: fallbackText(selectedModel.value.code) },
      { label: "機種名稱", value: fallbackText(selectedModel.value.name) },
      { label: "狀態", value: yesNoStatus(selectedModel.value.is_active) }
    ];
  }
  if (activeTab.value === "station" && selectedStation.value) {
    return [
      { label: "站點編號", value: fallbackText(selectedStation.value.code) },
      { label: "站點名稱", value: fallbackText(selectedStation.value.name) },
      { label: "狀態", value: yesNoStatus(selectedStation.value.is_active) }
    ];
  }
  if (activeTab.value === "customer" && selectedCustomerRow.value) {
    return [
      { label: "客戶代碼", value: fallbackText(selectedCustomerRow.value.code) },
      { label: "客戶名稱", value: fallbackText(selectedCustomerRow.value.name) },
      { label: "指派使用者", value: `${selectedCustomerRow.value.assigned_user_ids.length} 位` }
    ];
  }
  if (activeTab.value === "user" && selectedUser.value) {
    const allowedCustomerLabel = selectedUser.value.allowed_customers?.length
      ? selectedUser.value.allowed_customers.map((customer) => `${customer.code} ${customer.name}`).join("、")
      : selectedUser.value.allowed_customer_ids.length > 0
        ? `${selectedUser.value.allowed_customer_ids.length} 個客戶`
        : "尚未分派";
    return [
      { label: "帳號", value: fallbackText(selectedUser.value.username) },
      { label: "顯示名稱", value: fallbackText(selectedUser.value.display_name) },
      { label: "Email", value: fallbackText(selectedUser.value.email, "未設定") },
      { label: "角色", value: selectedUser.value.role === "super_admin" ? "Super Admin" : selectedUser.value.role === "admin" ? "Admin" : "User" },
      { label: "可存取客戶", value: allowedCustomerLabel },
      { label: "狀態", value: yesNoStatus(selectedUser.value.is_active) }
    ];
  }
  return [];
});
const showMasterListPanel = computed(() => !isMobileMasterFlow.value || !mobileMasterDetailOpen.value);
const showMasterDetailPanel = computed(() => !isMobileMasterFlow.value || mobileMasterDetailOpen.value);
const editorBaseline = computed(() => {
  if (activeTab.value === "fixture") {
    const row = selectedFixture.value;
    return row
      ? {
          code: normalizeText(row.code),
          name: normalizeText(row.name),
          responsible_user_id: row.responsible_user_id,
          line_storage_location: normalizeText(row.line_storage_location),
          department_storage_location: normalizeText(row.department_storage_location),
          min_stock_qty: row.min_stock_qty,
          description: normalizeText(row.description),
          is_active: row.is_active
        }
      : {
          code: "",
          name: "",
          responsible_user_id: null,
          line_storage_location: "",
          department_storage_location: "",
          min_stock_qty: 0,
          description: "",
          is_active: true
        };
  }
  if (activeTab.value === "model") {
    const row = selectedModel.value;
    return row
      ? { code: normalizeText(row.code), name: normalizeText(row.name), is_active: row.is_active }
      : { code: "", name: "", is_active: true };
  }
  if (activeTab.value === "station") {
    const row = selectedStation.value;
    return row
      ? { code: normalizeText(row.code), name: normalizeText(row.name), is_active: row.is_active }
      : { code: "", name: "", is_active: true };
  }
  if (activeTab.value === "customer") {
    const row = selectedCustomerRow.value;
    return row
      ? { code: normalizeText(row.code), name: normalizeText(row.name), assigned_user_ids: [...row.assigned_user_ids].sort((a, b) => a - b) }
      : { code: "", name: "", assigned_user_ids: [] as number[] };
  }
  if (activeTab.value === "ledger" || activeTab.value === "quality") {
    return { mode: "ledger" };
  }
  const row = selectedUser.value;
  return row
    ? {
        username: normalizeText(row.username),
        email: normalizeText(row.email),
        display_name: normalizeText(row.display_name),
        role: row.role,
        is_active: row.is_active,
        password: "",
        reset_password: "",
        allowed_customer_ids: [...row.allowed_customer_ids].sort((a, b) => a - b)
      }
    : {
        username: "",
        email: "",
        display_name: "",
        role: "user",
        is_active: true,
        password: "",
        reset_password: "",
        allowed_customer_ids: selectedCustomerId.value ? [selectedCustomerId.value] : []
      };
});
const editorCurrentState = computed(() => {
  if (activeTab.value === "fixture") {
    return {
      code: normalizeText(fixtureForm.value.code),
      name: normalizeText(fixtureForm.value.name),
      responsible_user_id: fixtureForm.value.responsible_user_id,
      line_storage_location: normalizeText(fixtureForm.value.line_storage_location),
      department_storage_location: normalizeText(fixtureForm.value.department_storage_location),
      min_stock_qty: fixtureForm.value.min_stock_qty,
      description: normalizeText(fixtureForm.value.description),
      is_active: fixtureForm.value.is_active
    };
  }
  if (activeTab.value === "model") {
    return {
      code: normalizeText(modelForm.value.code),
      name: normalizeText(modelForm.value.name),
      is_active: modelForm.value.is_active
    };
  }
  if (activeTab.value === "station") {
    return {
      code: normalizeText(stationForm.value.code),
      name: normalizeText(stationForm.value.name),
      is_active: stationForm.value.is_active
    };
  }
  if (activeTab.value === "customer") {
    return {
      code: normalizeText(customerForm.value.code),
      name: normalizeText(customerForm.value.name),
      assigned_user_ids: [...customerFormAssignedUserIds.value].sort((a, b) => a - b)
    };
  }
  if (activeTab.value === "ledger" || activeTab.value === "quality") {
    return { mode: "ledger" };
  }
  return {
    username: normalizeText(userForm.value.username),
    email: normalizeText(userForm.value.email),
    display_name: normalizeText(userForm.value.display_name),
    role: userForm.value.role,
    is_active: userForm.value.is_active,
    password: normalizeText(userForm.value.password),
    reset_password: normalizeText(userForm.value.reset_password),
    allowed_customer_ids: [...userForm.value.allowed_customer_ids].sort((a, b) => a - b)
  };
});
const hasUnsavedChanges = computed(
  () =>
    editorMode.value !== "summary" &&
    JSON.stringify(editorCurrentState.value) !== JSON.stringify(editorBaseline.value)
);
const selectedStatusBadge = computed(() => {
  const row =
    activeTab.value === "fixture"
      ? selectedFixture.value
      : activeTab.value === "model"
        ? selectedModel.value
        : activeTab.value === "station"
          ? selectedStation.value
          : activeTab.value === "customer"
            ? null
          : selectedUser.value;
  if (!row) return null;
  return {
    label: row.is_active ? "啟用中" : "停用",
    tone: (row.is_active ? "active" : "inactive") as "active" | "inactive"
  };
});

const selectedActivatableRow = computed(() => {
  if (activeTab.value === "fixture") return selectedFixture.value;
  if (activeTab.value === "model") return selectedModel.value;
  if (activeTab.value === "station") return selectedStation.value;
  if (activeTab.value === "user") return selectedUser.value;
  return null;
});

const toggleActionLabel = computed(() => (selectedActivatableRow.value?.is_active ?? true ? "停用" : "恢復使用"));
const canDeleteMasterEntity = computed(
  () => canManageMasterEntities.value && (activeTab.value === "fixture" || activeTab.value === "model" || activeTab.value === "station")
);
// Keep the page responsible only for counts; layout now lives in UiSummaryCards.
const summaryCards = computed(() => [
  { label: "治具總數", value: fixtures.value.length, meta: `啟用 ${fixtures.value.filter((row) => row.is_active).length}` },
  { label: "機種總數", value: models.value.length, meta: `啟用 ${models.value.filter((row) => row.is_active).length}` },
  { label: "站點總數", value: stations.value.length, meta: `啟用 ${stations.value.filter((row) => row.is_active).length}` },
  { label: "客戶", value: customerRows.value.length, meta: `可見 ${customerRows.value.length}` },
  { label: "使用者", value: users.value.length, meta: `啟用 ${users.value.filter((row) => row.is_active).length}` }
]);

function clampPage(page: number, totalPages: number): number {
  return Math.min(Math.max(1, page), totalPages);
}

function moveListPageBackAfterLastRowRemoval(): void {
  const pageStart = (listPage.value - 1) * listPageSize;
  const currentPageItemCount = currentRows.value.slice(pageStart, pageStart + listPageSize).length;
  listPage.value = pageAfterItemRemoval(listPage.value, currentPageItemCount);
}

const {
  dialogOpen: hardDeleteDialogOpen,
  deleteFixtureTransactions,
  deleting: hardDeleting,
  targetType: hardDeleteTargetType,
  dialogTitle: hardDeleteDialogTitle,
  dialogIntro: hardDeleteDialogIntro,
  openDialog: openHardDeleteDialog,
  closeDialog: closeHardDeleteDialog,
  confirmDeletion: confirmHardDeletion
} = useMasterEntityDeletion({
  activeTab,
  canManage: canManageMasterEntities,
  selectedCustomerId,
  selectedFixtureId,
  selectedModelId,
  selectedStationId,
  selectedFixtureCode: computed(() => selectedFixture.value?.code ?? ""),
  selectedModelCode: computed(() => selectedModel.value?.code ?? ""),
  selectedStationCode: computed(() => selectedStation.value?.code ?? ""),
  saving,
  selectedTabLabel: () => tabTitleMap[activeTab.value],
  movePageBackAfterRemoval: moveListPageBackAfterLastRowRemoval,
  reloadAfterRemoval: () => loadData(false, { focusSelectedListRow: true, preserveLedgerPage: true }),
  finishEditing: () => {
    editorMode.value = "summary";
  }
});

function getSelectedListRowId(): number | null {
  if (activeTab.value === "fixture") return selectedFixtureId.value;
  if (activeTab.value === "model") return selectedModelId.value;
  if (activeTab.value === "station") return selectedStationId.value;
  if (activeTab.value === "customer") return selectedCustomerRowId.value;
  if (activeTab.value === "user") return selectedUserId.value;
  return null;
}

function focusSelectedListRow(fallbackPage = listPage.value): void {
  const selectedId = getSelectedListRowId();
  if (selectedId === null) {
    listPage.value = clampPage(fallbackPage, listTotalPages.value);
    return;
  }
  const selectedIndex = currentRows.value.findIndex((row) => row.id === selectedId);
  if (selectedIndex === -1) {
    listPage.value = clampPage(fallbackPage, listTotalPages.value);
    return;
  }
  listPage.value = Math.floor(selectedIndex / listPageSize) + 1;
}

type LoadDataOptions = {
  preserveListPage?: boolean;
  preserveLedgerPage?: boolean;
  focusSelectedListRow?: boolean;
  focusSelectedLedgerRow?: boolean;
};

async function startDemoTour(): Promise<void> {
  if (!selectedGlobalCustomer.value) {
    pushToast("請先選擇客戶，才可以開始新手導覽。", "warning");
    return;
  }
  if (!(await confirmDiscardChanges("開始導覽會從首頁重新開始，並使用目前客戶的資料做教學流程。要繼續嗎？"))) {
    return;
  }
  onboardingActive.value = false;
  onboardingStepIndex.value = 0;
  onboardingPickerOpen.value = true;
}

async function loadData(showLoading = true, options: LoadDataOptions = {}): Promise<void> {
  const previousListPage = listPage.value;
  const previousLedgerPage = ledgerPage.value;
  if (showLoading) {
    loading.value = true;
  }
  try {
    const customerId = selectedCustomerId.value ?? undefined;
    const [f, m, s, u, c, customerUsers, qualityReport] = await Promise.all([
      api.listFixtures(customerId),
      customerId ? api.listModels(customerId) : Promise.resolve([]),
      customerId ? api.listStations(customerId) : Promise.resolve([]),
      canManageUsers.value ? api.listUsers() : Promise.resolve([]),
      api.listCustomers(),
      customerId ? api.listCustomerUsers(customerId) : Promise.resolve([]),
      canManageQuality.value && customerId ? api.getFixtureQualityReport(customerId) : Promise.resolve(null)
    ]);
    fixtures.value = f;
    models.value = m;
    stations.value = s;
    users.value = u;
    customerRows.value = c;
    customerAssignedUsers.value = customerUsers;
    fixtureQualityReport.value = qualityReport;

    selectedFixtureId.value = f.find((row) => row.id === selectedFixtureId.value)?.id ?? null;
    selectedModelId.value = m.find((row) => row.id === selectedModelId.value)?.id ?? null;
    selectedStationId.value = s.find((row) => row.id === selectedStationId.value)?.id ?? null;
    selectedUserId.value = u.find((row) => row.id === selectedUserId.value)?.id ?? null;
    selectedCustomerRowId.value = c.find((row) => row.id === selectedCustomerRowId.value)?.id ?? null;
    if (!canManageUsers.value && activeTab.value === "user") {
      activeTab.value = "fixture";
    }
    if (!canManageLedger.value && activeTab.value === "ledger") {
      activeTab.value = "fixture";
    }
    if (!canManageQuality.value && activeTab.value === "quality") {
      activeTab.value = "fixture";
    }
    if (options.focusSelectedListRow) {
      focusSelectedListRow(previousListPage);
    } else if (options.preserveListPage) {
      listPage.value = clampPage(previousListPage, listTotalPages.value);
    } else {
      listPage.value = 1;
    }
    if (!options.preserveLedgerPage && !options.focusSelectedLedgerRow) {
      ledgerPage.value = 1;
    } else {
      ledgerPage.value = clampPage(previousLedgerPage, ledgerTotalPages.value);
    }
    await loadLedgerPage({ preserveSelection: Boolean(options.focusSelectedLedgerRow) });
    if (options.focusSelectedLedgerRow) {
      focusSelectedLedgerRow(previousLedgerPage);
    }
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "載入資料維護資料失敗", "error");
  } finally {
    if (showLoading) {
      loading.value = false;
    }
  }
}

function syncEditorFromSelection(): void {
  if (activeTab.value === "fixture") {
    const row = selectedFixture.value;
    if (!row) return;
    fixtureForm.value = {
      code: row.code,
      name: row.name,
      responsible_user_id: row.responsible_user_id,
      line_storage_location: row.line_storage_location ?? "",
      department_storage_location: row.department_storage_location ?? "",
      min_stock_qty: row.min_stock_qty,
      description: row.description ?? "",
      is_active: row.is_active
    };
    return;
  }
  if (activeTab.value === "model") {
    const row = selectedModel.value;
    if (!row) return;
    modelForm.value = { code: row.code, name: row.name, is_active: row.is_active };
    return;
  }
  if (activeTab.value === "station") {
    const row = selectedStation.value;
    if (!row) return;
    stationForm.value = { code: row.code, name: row.name, is_active: row.is_active };
    return;
  }
  if (activeTab.value === "customer") {
    const row = selectedCustomerRow.value;
    if (!row) return;
    customerForm.value = { code: row.code, name: row.name };
    customerFormAssignedUserIds.value = [...row.assigned_user_ids];
    return;
  }
  if (activeTab.value === "user") {
    const row = selectedUser.value;
    if (!row) return;
    userForm.value = {
      username: row.username,
      email: row.email ?? "",
      display_name: row.display_name,
      role: row.role,
      is_active: row.is_active,
      password: "",
      reset_password: "",
      allowed_customer_ids: [...row.allowed_customer_ids].sort((a, b) => a - b)
    };
    return;
  }
  if (activeTab.value === "ledger" || activeTab.value === "quality") {
    return;
  }
}

async function confirmDiscardChanges(message: string): Promise<boolean> {
  if (!hasUnsavedChanges.value) {
    return true;
  }
  return requestConfirmation(message, {
    title: "捨棄未儲存的修改？",
    confirmLabel: "捨棄並繼續",
    tone: "danger"
  });
}

function switchTab(tab: MasterTab): void {
  if (tab === activeTab.value && route.path === TAB_PATH_MAP[tab]) {
    return;
  }
  keyword.value = "";
  statusFilter.value = [];
  listPage.value = 1;
  resetLedgerFilters();
  void router.push(TAB_PATH_MAP[tab]);
}

async function startCreate(): Promise<void> {
  if (!(await confirmDiscardChanges("目前表單有未儲存的修改，切換到新增模式後將會捨棄。要繼續嗎？"))) {
    return;
  }
  startCreateWithoutPrompt();
}

function startCreateWithoutPrompt(): void {
  editorMode.value = "create";
  if (activeTab.value === "fixture") {
    selectedFixtureId.value = null;
    fixtureForm.value = makeEmptyFixtureForm();
    clearFixtureImageBatchSelection();
    mobileMasterDetailOpen.value = isMobileMasterFlow.value;
    return;
  }
  if (activeTab.value === "model") {
    selectedModelId.value = null;
    modelForm.value = makeEmptyModelForm();
    mobileMasterDetailOpen.value = isMobileMasterFlow.value;
    return;
  }
  if (activeTab.value === "station") {
    selectedStationId.value = null;
    stationForm.value = makeEmptyStationForm();
    mobileMasterDetailOpen.value = isMobileMasterFlow.value;
    return;
  }
  if (activeTab.value === "user") {
    selectedUserId.value = null;
    userForm.value = makeEmptyUserForm();
    mobileMasterDetailOpen.value = isMobileMasterFlow.value;
    return;
  }
  if (activeTab.value === "customer") {
    selectedCustomerRowId.value = null;
    customerForm.value = makeEmptyCustomerForm();
    customerFormAssignedUserIds.value = [];
    mobileMasterDetailOpen.value = isMobileMasterFlow.value;
    return;
  }
  if (activeTab.value === "ledger" || activeTab.value === "quality") {
    return;
  }
}

async function selectRow(id: number): Promise<void> {
  const currentId =
    activeTab.value === "fixture"
      ? selectedFixtureId.value
      : activeTab.value === "model"
        ? selectedModelId.value
        : activeTab.value === "station"
          ? selectedStationId.value
          : activeTab.value === "customer"
            ? selectedCustomerRowId.value
            : selectedUserId.value;
  if (currentId === id) {
    if (
      editorMode.value === "summary" &&
      activeTab.value !== "ledger" &&
      activeTab.value !== "quality"
    ) {
      mobileMasterDetailOpen.value = isMobileMasterFlow.value;
    }
    return;
  }
  if (!(await confirmDiscardChanges("目前表單有未儲存的修改，切換資料後將會捨棄。要繼續嗎？"))) {
    return;
  }
  if (activeTab.value === "fixture") selectedFixtureId.value = id;
  if (activeTab.value === "model") selectedModelId.value = id;
  if (activeTab.value === "station") selectedStationId.value = id;
  if (activeTab.value === "customer") selectedCustomerRowId.value = id;
  if (activeTab.value === "user") selectedUserId.value = id;
  if (activeTab.value === "ledger") selectLedgerTransaction(id);
  if (activeTab.value !== "ledger" && activeTab.value !== "quality") {
    editorMode.value = "summary";
    mobileMasterDetailOpen.value = isMobileMasterFlow.value;
  }
}

async function returnToMobileList(): Promise<void> {
  if (!(await confirmDiscardChanges("返回清單會離開目前明細畫面。尚未儲存的修改將會捨棄。要繼續嗎？"))) {
    return;
  }
  editorMode.value = "summary";
  mobileMasterDetailOpen.value = false;
}

function startEdit(): void {
  if (!hasSelectedMasterRow.value) {
    pushToast(`請先選擇要編輯的${tabTitleMap[activeTab.value]}。`, "warning");
    return;
  }
  syncEditorFromSelection();
  editorMode.value = "edit";
  mobileMasterDetailOpen.value = isMobileMasterFlow.value;
}

async function cancelEditor(): Promise<void> {
  if (!(await confirmDiscardChanges("取消後將捨棄目前尚未儲存的修改。要繼續嗎？"))) {
    return;
  }
  editorMode.value = "summary";
  if (isMobileMasterFlow.value && !hasSelectedMasterRow.value) {
    mobileMasterDetailOpen.value = false;
  }
}

async function reloadSelection(): Promise<void> {
  if (
    !(await confirmDiscardChanges(
      "重載會放棄目前尚未儲存的修改，重新載入已選資料。要繼續嗎？"
    ))
  ) {
    return;
  }
  syncEditorFromSelection();
}

function updateFixtureImageBatchFiles(event: Event): void {
  const input = event.target as HTMLInputElement;
  const files = Array.from(input.files ?? []);
  if (files.length > 50) {
    clearFixtureImageBatchSelection();
    pushToast("單次最多可選擇 50 張圖片。", "warning");
    return;
  }
  const oversizeFile = files.find((file) => file.size > 5 * 1024 * 1024);
  if (oversizeFile) {
    clearFixtureImageBatchSelection();
    pushToast(`圖片 ${oversizeFile.name} 超過 5 MB。`, "warning");
    return;
  }
  fixtureImageBatchFiles.value = files;
}

async function uploadFixtureImageBatch(): Promise<void> {
  if (!selectedCustomerId.value) {
    pushToast("請先選擇客戶。", "warning");
    return;
  }
  if (fixtureImageBatchFiles.value.length === 0) {
    pushToast("請先選擇要上傳的圖片。", "warning");
    return;
  }
  if (fixtureImageBatchFiles.value.length > 50) {
    pushToast("單次最多可上傳 50 張圖片。", "warning");
    return;
  }
  fixtureImageBatchUploading.value = true;
  try {
    const result = await api.uploadFixtureImagesBatch(selectedCustomerId.value, fixtureImageBatchFiles.value);
    await loadData(false, { preserveListPage: true, preserveLedgerPage: true, focusSelectedListRow: true });
    clearFixtureImageBatchSelection();
    if (result.failed_count === 0) {
      pushToast(`圖片批次上傳完成，成功 ${result.uploaded_count} 張。`, "success");
      return;
    }
    const firstFailure = result.results.find((row) => !row.success);
    pushToast(
      `批次上傳完成，成功 ${result.uploaded_count} 張，失敗 ${result.failed_count} 張。${firstFailure ? ` 首筆失敗：${firstFailure.file_name} - ${firstFailure.message}` : ""}`,
      "warning"
    );
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "批次上傳治具圖片失敗", "error");
  } finally {
    fixtureImageBatchUploading.value = false;
  }
}

function toggleAssignedUser(userId: number, checked: boolean): void {
  const current = new Set(customerFormAssignedUserIds.value);
  if (checked) {
    current.add(userId);
  } else {
    current.delete(userId);
  }
  customerFormAssignedUserIds.value = [...current].sort((a, b) => a - b);
}

function hasAssignedUser(userId: number): boolean {
  return customerFormAssignedUserIds.value.includes(userId);
}

async function resetUserPassword(): Promise<void> {
  if (activeTab.value !== "user" || !selectedUserId.value) {
    pushToast("請先選擇使用者。", "warning");
    return;
  }
  if (!userForm.value.reset_password.trim()) {
    pushToast("請輸入新密碼。", "warning");
    return;
  }
  saving.value = true;
  try {
    await api.resetUserPassword(selectedUserId.value, userForm.value.reset_password.trim());
    userForm.value.reset_password = "";
    pushToast("密碼已重設。", "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "重設密碼失敗", "error");
  } finally {
    saving.value = false;
  }
}

function downloadCurrent(): void {
  const payload = JSON.stringify(currentRows.value, null, 2);
  const blob = new Blob([payload], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `master-${activeTab.value}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

function previousListPage(): void {
  listPage.value = Math.max(1, listPage.value - 1);
}

function nextListPage(): void {
  listPage.value = Math.min(listTotalPages.value, listPage.value + 1);
}

function updateKeyword(value: string): void {
  keyword.value = value;
}

function updateStatusFilter(value: Array<"active" | "inactive">): void {
  statusFilter.value = value;
}

watch([activeTab, keyword, statusFilter], () => {
  listPage.value = 1;
});

watch(currentRows, () => {
  if (listPage.value > listTotalPages.value) {
    listPage.value = listTotalPages.value;
  }
});

function downloadCsv(filename: string, content: string): void {
  const blob = new Blob(["\ufeff", content], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

async function exportActiveCsv(): Promise<void> {
  try {
    if (activeTab.value !== "fixture" && activeTab.value !== "model" && activeTab.value !== "station") {
      pushToast("此分頁目前未提供匯出 CSV。", "info");
      return;
    }
    if (activeTab.value === "fixture") {
      if (!selectedCustomerId.value) {
        pushToast("請先選擇客戶。", "warning");
        return;
      }
      downloadCsv("fixtures.csv", await api.exportFixturesCsv(selectedCustomerId.value));
      return;
    }
    if (activeTab.value === "model") {
      if (!selectedCustomerId.value) {
        pushToast("請先選擇客戶。", "warning");
        return;
      }
      downloadCsv("models.csv", await api.exportModelsCsv(selectedCustomerId.value));
      return;
    }
    if (activeTab.value === "station") {
      if (!selectedCustomerId.value) {
        pushToast("請先選擇客戶。", "warning");
        return;
      }
      downloadCsv("stations.csv", await api.exportStationsCsv(selectedCustomerId.value));
      return;
    }
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "匯出失敗", "error");
  }
}

async function downloadTemplate(): Promise<void> {
  try {
    if (activeTab.value !== "fixture" && activeTab.value !== "model" && activeTab.value !== "station") {
      pushToast("此分頁目前未提供範本下載。", "info");
      return;
    }
    if (activeTab.value === "fixture") {
      downloadCsv("fixtures-template.csv", await api.downloadFixtureTemplateCsv());
      return;
    }
    if (activeTab.value === "model") {
      if (!selectedCustomerId.value) {
        pushToast("請先選擇客戶。", "warning");
        return;
      }
      downloadCsv("models-template.csv", await api.downloadModelTemplateCsv());
      return;
    }
    if (activeTab.value === "station") {
      if (!selectedCustomerId.value) {
        pushToast("請先選擇客戶。", "warning");
        return;
      }
      downloadCsv("stations-template.csv", await api.downloadStationTemplateCsv());
      return;
    }
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "下載範本失敗", "error");
  }
}

async function importCsv(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  try {
    const content = await file.text();
    let result: { imported_count: number } | null = null;
    if (activeTab.value === "fixture") {
      if (!selectedCustomerId.value) {
        pushToast("請先選擇客戶。", "warning");
        return;
      }
      result = await api.importFixturesCsv(selectedCustomerId.value, content, file.name);
    } else if (activeTab.value === "model") {
      if (!selectedCustomerId.value) {
        pushToast("請先選擇客戶。", "warning");
        return;
      }
      result = await api.importModelsCsv(selectedCustomerId.value, content, file.name);
    } else if (activeTab.value === "station") {
      if (!selectedCustomerId.value) {
        pushToast("請先選擇客戶。", "warning");
        return;
      }
      result = await api.importStationsCsv(selectedCustomerId.value, content, file.name);
    }
    await loadData(false, { focusSelectedListRow: true, preserveLedgerPage: true });
    editorMode.value = "summary";
    pushToast(`匯入完成，共 ${result?.imported_count ?? 0} 筆。`, "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "匯入失敗", "error");
  } finally {
    input.value = "";
  }
}

watch(activeTab, () => {
  editorMode.value = "summary";
  mobileMasterDetailOpen.value = false;
});
watch(
  () => route.path,
  (pathname) => {
    activeTab.value = resolveMasterTabFromPath(pathname);
  },
  { immediate: true }
);
watch(
  [activeTab, selectedCustomerId, selectedFixtureId],
  () => {
    clearFixtureImageBatchSelection();
  }
);
watch(selectedCustomerId, async () => {
  editorMode.value = "summary";
  await loadData();
  applyMasterDeepLinkSelection();
});

function applyMasterDeepLinkSelection(): void {
  const fixtureId = Number.parseInt(typeof route.query.fixture_id === "string" ? route.query.fixture_id : "", 10);
  const modelId = Number.parseInt(typeof route.query.model_id === "string" ? route.query.model_id : "", 10);
  const stationId = Number.parseInt(typeof route.query.station_id === "string" ? route.query.station_id : "", 10);
  const customerId = Number.parseInt(typeof route.query.customer_id === "string" ? route.query.customer_id : "", 10);
  const userId = Number.parseInt(typeof route.query.user_id === "string" ? route.query.user_id : "", 10);
  if (activeTab.value === "fixture" && fixtures.value.some((row) => row.id === fixtureId)) {
    selectedFixtureId.value = fixtureId;
  } else if (activeTab.value === "model" && models.value.some((row) => row.id === modelId)) {
    selectedModelId.value = modelId;
  } else if (activeTab.value === "station" && stations.value.some((row) => row.id === stationId)) {
    selectedStationId.value = stationId;
  } else if (activeTab.value === "customer" && customerRows.value.some((row) => row.id === customerId)) {
    selectedCustomerRowId.value = customerId;
  } else if (activeTab.value === "user" && users.value.some((row) => row.id === userId)) {
    selectedUserId.value = userId;
  }
  if (route.query.edit === "1" && hasSelectedMasterRow.value) {
    startEdit();
  } else {
    editorMode.value = "summary";
  }
}

watch(
  () => route.query,
  () => {
    applyMasterDeepLinkSelection();
  }
);

watch(
  hasUnsavedChanges,
  (value) => {
    setCustomerSwitchGuard("master-page", value, "主資料頁有未儲存的修改");
  },
  { immediate: true }
);

onMounted(async () => {
  syncMasterViewport();
  window.addEventListener("resize", syncMasterViewport);
  activeTab.value = resolveMasterTabFromPath(route.path);
  await loadData();
  applyMasterDeepLinkSelection();
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", syncMasterViewport);
  clearFixtureImageBatchSelection();
  setCustomerSwitchGuard("master-page", false, "主資料頁有未儲存的修改");
});
</script>

<template>
  <div class="master-shell" :class="{ 'mobile-detail-active': isMobileMasterFlow && mobileMasterDetailOpen }">
    <UiSummaryCards
      v-if="!isMobileMasterFlow || !mobileMasterDetailOpen"
      class="summary-row"
      :cards="summaryCards"
      :variant="isMobileMasterFlow ? 'compact' : 'default'"
      :desktop-columns="5"
      :tablet-columns="2"
      :mobile-columns="1"
    />

    <MasterToolbar
      v-if="!isMobileMasterFlow || !mobileMasterDetailOpen"
      ref="masterToolbarRef"
      :active-tab="activeTab"
      :can-manage-customers="canManageCustomers"
      :can-manage-users="canManageUsers"
      :can-manage-ledger="canManageLedger"
      :can-manage-quality="canManageQuality"
      :loading="loading"
      :has-selected-customer="Boolean(selectedGlobalCustomer)"
      :image-batch-uploading="fixtureImageBatchUploading"
      :image-batch-file-count="fixtureImageBatchFiles.length"
      @switch-tab="switchTab"
      @start-tour="startDemoTour"
      @upload-images="uploadFixtureImageBatch"
      @return-search="router.push({ name: 'search' })"
      @export-csv="exportActiveCsv"
      @download-template="downloadTemplate"
      @download-json="downloadCurrent"
      @import-csv="importCsv"
      @image-files-change="updateFixtureImageBatchFiles"
    />

    <section class="content-grid" :class="{ 'content-grid-single': activeTab === 'quality' }">
      <template v-if="activeTab === 'quality'">
        <FixtureQualityPanel
          :report="fixtureQualityReport"
          :fixtures="fixtures"
          :loading="loading"
          :inline-saving-fixture-id="qualityInlineSavingFixtureId"
          @open-issue-editor="openIssueEditorFromQuality"
          @save-inline-issue="saveInlineQualityIssue"
        />
      </template>

      <template v-else-if="activeTab !== 'ledger'">
        <MasterListPanel
        v-if="showMasterListPanel"
        :active-tab="activeTab"
        :tab-title="tabTitleMap[activeTab]"
        :current-rows-length="currentRows.length"
        :keyword="keyword"
        :search-placeholder="searchPlaceholder"
        :loading="loading"
        :status-filter="statusFilter"
        :can-create="canCreateInCurrentTab"
        :empty-state-message="emptyStateMessage"
        :list-page="listPage"
        :list-total-pages="listTotalPages"
        :paged-fixture-rows="pagedFixtureRows"
        :paged-model-rows="pagedModelRows"
        :paged-station-rows="pagedStationRows"
        :paged-customer-rows="pagedCustomerRows"
        :paged-user-rows="pagedUserRows"
        :selected-fixture-id="selectedFixtureId"
        :selected-model-id="selectedModelId"
        :selected-station-id="selectedStationId"
        :selected-customer-row-id="selectedCustomerRowId"
        :selected-user-id="selectedUserId"
        :on-keyword-change="updateKeyword"
        :on-status-filter-change="updateStatusFilter"
        :on-start-create="startCreate"
        :on-select-row="selectRow"
        :on-previous-page="previousListPage"
        :on-next-page="nextListPage"
        />

        <div v-if="showMasterDetailPanel" class="detail-panel-stack">
          <header v-if="isMobileMasterFlow" class="mobile-detail-header">
            <button class="outline-btn mobile-back-btn" type="button" @click="returnToMobileList">← 返回清單</button>
            <div class="mobile-detail-context">
              <span>{{ tabTitleMap[activeTab] }}</span>
              <strong>{{ mobileDetailHeading }}</strong>
            </div>
            <button
              v-if="editorMode === 'summary' && masterSummaryFields.length > 0"
              class="primary-btn mobile-detail-edit-btn"
              type="button"
              :disabled="saving"
              @click="startEdit"
            >
              編輯
            </button>
          </header>
          <MasterDetailPanel
          :active-tab="activeTab"
          :tab-title="tabTitleMap[activeTab]"
          :editor-mode="editorMode"
          :is-create-mode="isCreateMode"
          :summary-fields="masterSummaryFields"
          :selected-detail-label="selectedDetailLabel"
          :selected-status-badge="selectedStatusBadge"
          :saving="saving"
          :toggle-action-label="toggleActionLabel"
          :can-manage-customers="canManageCustomers"
          :can-manage-users="canManageUsers"
          :can-delete-master-entity="canDeleteMasterEntity"
          :selected-fixture-id="selectedFixtureId"
          :selected-user-id="selectedUserId"
          :selected-customer-scope-count="selectedCustomerScopeCount"
          :selected-customer-row="selectedCustomerRow"
          :selected-user="selectedUser"
          :customer-assigned-users="customerAssignedUsers"
          :customers="customerRows"
          :users="users"
          :fixture-form="fixtureForm"
          :model-form="modelForm"
          :station-form="stationForm"
          :customer-form="customerForm"
          :user-form="userForm"
          :on-start-create="startCreate"
          :on-start-edit="startEdit"
          :on-cancel-edit="cancelEditor"
          :on-reload-selection="reloadSelection"
          :on-save-current="saveCurrent"
          :on-toggle-current-active="toggleCurrentActive"
          :on-request-delete-entity="openHardDeleteDialog"
          :on-reset-user-password="resetUserPassword"
          :on-toggle-assigned-user="toggleAssignedUser"
          :on-has-assigned-user="hasAssignedUser"
          />
        </div>
      </template>

      <template v-else>
        <TransactionAccountListPanel
          :rows="ledgerTransactions"
          :selected-transaction-id="selectedLedgerTransactionId"
          :loading="loading || ledgerLoading"
          :transaction-no="ledgerTransactionNoFilter"
          :created-by="ledgerCreatedByFilter"
          :fixture-code="ledgerFixtureCodeFilter"
          :transaction-type="ledgerTypeFilter"
          :page="ledgerPage"
          :page-size="ledgerPageSize"
          :total-pages="ledgerTotalPages"
          :total="ledgerTotal"
          :on-transaction-no-change="updateLedgerTransactionNo"
          :on-created-by-change="updateLedgerCreatedBy"
          :on-fixture-code-change="updateLedgerFixtureCode"
          :on-transaction-type-change="updateLedgerTypeFilter"
          :on-page-size-change="updateLedgerPageSize"
          :on-select-row="selectRow"
          :on-previous-page="previousLedgerPage"
          :on-next-page="nextLedgerPage"
        />

        <TransactionAccountDetailPanel
          :transaction="selectedLedgerTransaction"
          :processing="ledgerProcessing"
          :on-reload="reloadLedgerSelection"
          :on-recalculate="recalculateLedgerState"
          :on-reverse="reverseSelectedLedgerTransaction"
        />
      </template>
    </section>

    <FixtureQualityQuickEditModal
      v-model:form="qualityQuickEditForm"
      v-model:relation-model-id="qualityRelationModelId"
      v-model:relation-station-id="qualityRelationStationId"
      v-model:relation-required-qty="qualityRelationRequiredQty"
      :open="qualityQuickEditOpen"
      :busy="qualityQuickEditBusy"
      :issue-code="qualityQuickEditIssueCode"
      :fixture="qualityQuickEditFixture"
      :models="models"
      :station-options="qualityRelationStationOptions"
      :image-url="qualityImageUrl"
      :image-file="qualityImageFile"
      :quick-edit-saving="qualityQuickEditSaving"
      :relation-saving="qualityRelationSaving"
      :image-uploading="qualityImageUploading"
      :title="qualityQuickEditTitle"
      @close="closeQualityQuickEditDialog"
      @image-change="updateQualityImageFile"
      @image-input="qualityImageInput = $event"
      @open-ledger="openLedgerFromQuality"
      @save-fixture="saveQualityQuickEdit"
      @save-relation="saveQualityRelation"
      @upload-image="uploadQualityImage"
    />

    <MasterPermanentDeleteModal
      v-model:delete-fixture-transactions="deleteFixtureTransactions"
      :open="hardDeleteDialogOpen"
      :deleting="hardDeleting"
      :target-type="hardDeleteTargetType"
      :title="hardDeleteDialogTitle"
      :intro="hardDeleteDialogIntro"
      @close="closeHardDeleteDialog"
      @confirm="confirmHardDeletion"
    />
  </div>
</template>


<style src="@/styles/surfaces/master.css"></style>
