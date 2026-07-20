<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "@/api";
import { authSession, customers, onboardingActive, onboardingPickerOpen, onboardingStepIndex, selectedCustomerId } from "@/appState";
import MasterDetailPanel from "@/components/master/MasterDetailPanel.vue";
import MasterListPanel from "@/components/master/MasterListPanel.vue";
import FixtureQualityPanel from "@/components/master/FixtureQualityPanel.vue";
import TransactionAccountDetailPanel from "@/components/master/TransactionAccountDetailPanel.vue";
import TransactionAccountListPanel from "@/components/master/TransactionAccountListPanel.vue";
import UiSummaryCards from "@/components/UiSummaryCards.vue";
import { pushToast } from "@/toastState";
import type { AppUser, Customer, Fixture, FixtureQualityReport, MachineModel, MaterialTransaction, Station } from "@/types";
import { fallbackText } from "@/utils/display";

type MasterTab = "fixture" | "model" | "station" | "customer" | "user" | "ledger" | "quality";

const router = useRouter();
const route = useRoute();

const fixtures = ref<Fixture[]>([]);
const models = ref<MachineModel[]>([]);
const stations = ref<Station[]>([]);
const users = ref<AppUser[]>([]);
const customerRows = ref<Customer[]>([]);
const customerAssignedUsers = ref<AppUser[]>([]);
const ledgerTransactions = ref<MaterialTransaction[]>([]);
const fixtureQualityReport = ref<FixtureQualityReport | null>(null);

const activeTab = ref<MasterTab>("fixture");
const keyword = ref("");
const statusFilter = ref<"all" | "active" | "inactive">("all");
const loading = ref(false);
const saving = ref(false);
const listPage = ref(1);
const listPageSize = 10;
const ledgerKeyword = ref("");
const ledgerTypeFilter = ref<"all" | "receipt" | "return">("all");
const ledgerPage = ref(1);
const ledgerPageSize = 12;
const ledgerProcessing = ref(false);

const selectedFixtureId = ref<number | null>(null);
const selectedModelId = ref<number | null>(null);
const selectedStationId = ref<number | null>(null);
const selectedUserId = ref<number | null>(null);
const selectedCustomerRowId = ref<number | null>(null);
const selectedLedgerTransactionId = ref<number | null>(null);

const fixtureForm = ref(makeEmptyFixtureForm());
const modelForm = ref(makeEmptyModelForm());
const stationForm = ref(makeEmptyStationForm());
const customerForm = ref(makeEmptyCustomerForm());
const userForm = ref(makeEmptyUserForm());
const importInput = ref<HTMLInputElement | null>(null);
const moreMenuOpen = ref(false);
const moreMenuRef = ref<HTMLElement | null>(null);
const canManageUsers = computed(() => authSession.value?.role === "admin");
const canManageCustomers = computed(() => authSession.value?.role === "admin");
const canManageLedger = computed(() => authSession.value?.role === "admin");
const canManageQuality = computed(() => authSession.value?.role === "admin");
const selectedCustomerScopeCount = computed(() => customerFormAssignedUserIds.value.length);
const customerFormAssignedUserIds = ref<number[]>([]);
const selectedGlobalCustomer = computed(() => customers.value.find((row) => row.id === selectedCustomerId.value) ?? null);
const canCreateInCurrentTab = computed(() => {
  if (activeTab.value === "ledger" || activeTab.value === "quality") {
    return false;
  }
  return activeTab.value !== "customer" || canManageCustomers.value;
});

function normalizeText(value: string | null | undefined): string {
  return (value ?? "").trim();
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
    reset_password: ""
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
      statusFilter.value === "all" ||
      (statusFilter.value === "active" && row.is_active) ||
      (statusFilter.value === "inactive" && !row.is_active);
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
      statusFilter.value === "all" ||
      (statusFilter.value === "active" && row.is_active) ||
      (statusFilter.value === "inactive" && !row.is_active);
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
      statusFilter.value === "all" ||
      (statusFilter.value === "active" && row.is_active) ||
      (statusFilter.value === "inactive" && !row.is_active);
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
      statusFilter.value === "all" ||
      (statusFilter.value === "active" && row.is_active) ||
      (statusFilter.value === "inactive" && !row.is_active);
    return byKeyword && byStatus;
  })
);

const filteredLedgerTransactions = computed(() =>
  ledgerTransactions.value.filter((row) => {
    const normalizedKeyword = ledgerKeyword.value.trim().toLowerCase();
    const byKeyword =
      !normalizedKeyword ||
      row.transaction_no.toLowerCase().includes(normalizedKeyword) ||
      row.created_by.toLowerCase().includes(normalizedKeyword) ||
      row.items.some((item) => item.fixture_code.toLowerCase().includes(normalizedKeyword));
    const byType = ledgerTypeFilter.value === "all" || row.transaction_type === ledgerTypeFilter.value;
    return byKeyword && byType;
  })
);

const currentRows = computed(() => {
  if (activeTab.value === "fixture") return filteredFixtures.value;
  if (activeTab.value === "model") return filteredModels.value;
  if (activeTab.value === "station") return filteredStations.value;
  if (activeTab.value === "customer") return filteredCustomers.value;
  if (activeTab.value === "ledger") return filteredLedgerTransactions.value;
  return filteredUsers.value;
});

const listTotalPages = computed(() => Math.max(1, Math.ceil(currentRows.value.length / listPageSize)));
const pagedFixtureRows = computed(() => filteredFixtures.value.slice((listPage.value - 1) * listPageSize, listPage.value * listPageSize));
const pagedModelRows = computed(() => filteredModels.value.slice((listPage.value - 1) * listPageSize, listPage.value * listPageSize));
const pagedStationRows = computed(() => filteredStations.value.slice((listPage.value - 1) * listPageSize, listPage.value * listPageSize));
const pagedCustomerRows = computed(() => filteredCustomers.value.slice((listPage.value - 1) * listPageSize, listPage.value * listPageSize));
const pagedUserRows = computed(() => filteredUsers.value.slice((listPage.value - 1) * listPageSize, listPage.value * listPageSize));
const ledgerTotalPages = computed(() => Math.max(1, Math.ceil(filteredLedgerTransactions.value.length / ledgerPageSize)));
const pagedLedgerRows = computed(() =>
  filteredLedgerTransactions.value.slice((ledgerPage.value - 1) * ledgerPageSize, ledgerPage.value * ledgerPageSize)
);

const emptyStateMessage = computed(() => {
  if (loading.value) return "資料載入中...";
  if (keyword.value) return `找不到符合「${keyword.value}」的資料`;
  if (statusFilter.value !== "all") return "目前篩選條件下沒有資料";
  return `目前沒有${tabTitleMap[activeTab.value]}資料`;
});

const selectedFixture = computed(() => fixtures.value.find((row) => row.id === selectedFixtureId.value) ?? null);
const selectedModel = computed(() => models.value.find((row) => row.id === selectedModelId.value) ?? null);
const selectedStation = computed(() => stations.value.find((row) => row.id === selectedStationId.value) ?? null);
const selectedUser = computed(() => users.value.find((row) => row.id === selectedUserId.value) ?? null);
const selectedCustomerRow = computed(() => customerRows.value.find((row) => row.id === selectedCustomerRowId.value) ?? null);
const selectedLedgerTransaction = computed(
  () => ledgerTransactions.value.find((row) => row.id === selectedLedgerTransactionId.value) ?? null
);
const selectedDetailLabel = computed(() =>
  fallbackText(
      selectedFixture.value?.code ||
      selectedModel.value?.code ||
      selectedStation.value?.code ||
      selectedCustomerRow.value?.code ||
      selectedUser.value?.username
  )
);
const isCreateMode = computed(
  () =>
    selectedFixtureId.value === null &&
    selectedModelId.value === null &&
    selectedStationId.value === null &&
    selectedCustomerRowId.value === null &&
    selectedUserId.value === null
);
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
        reset_password: ""
      }
    : {
        username: "",
        email: "",
        display_name: "",
        role: "user",
        is_active: true,
        password: "",
        reset_password: ""
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
    reset_password: normalizeText(userForm.value.reset_password)
  };
});
const hasUnsavedChanges = computed(() => JSON.stringify(editorCurrentState.value) !== JSON.stringify(editorBaseline.value));
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

function focusSelectedLedgerRow(fallbackPage = ledgerPage.value): void {
  if (selectedLedgerTransactionId.value === null) {
    ledgerPage.value = clampPage(fallbackPage, ledgerTotalPages.value);
    return;
  }
  const selectedIndex = filteredLedgerTransactions.value.findIndex((row) => row.id === selectedLedgerTransactionId.value);
  if (selectedIndex === -1) {
    ledgerPage.value = clampPage(fallbackPage, ledgerTotalPages.value);
    return;
  }
  ledgerPage.value = Math.floor(selectedIndex / ledgerPageSize) + 1;
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
  if (!confirmDiscardChanges("開始導覽會從首頁重新開始，並使用目前客戶的資料做教學流程。要繼續嗎？")) {
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
    const ledger = canManageLedger.value && customerId ? await api.listTransactions(200, customerId) : [];
    fixtures.value = f;
    models.value = m;
    stations.value = s;
    users.value = u;
    customerRows.value = c;
    customerAssignedUsers.value = customerUsers;
    ledgerTransactions.value = ledger;
    fixtureQualityReport.value = qualityReport;

    selectedFixtureId.value = f.find((row) => row.id === selectedFixtureId.value)?.id ?? f[0]?.id ?? null;
    selectedModelId.value = m.find((row) => row.id === selectedModelId.value)?.id ?? m[0]?.id ?? null;
    selectedStationId.value = s.find((row) => row.id === selectedStationId.value)?.id ?? s[0]?.id ?? null;
    selectedUserId.value = u.find((row) => row.id === selectedUserId.value)?.id ?? u[0]?.id ?? null;
    selectedCustomerRowId.value = c.find((row) => row.id === selectedCustomerRowId.value)?.id ?? c[0]?.id ?? null;
    selectedLedgerTransactionId.value = ledger.find((row) => row.id === selectedLedgerTransactionId.value)?.id ?? ledger[0]?.id ?? null;
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
    if (options.focusSelectedLedgerRow) {
      focusSelectedLedgerRow(previousLedgerPage);
    } else if (options.preserveLedgerPage) {
      ledgerPage.value = clampPage(previousLedgerPage, ledgerTotalPages.value);
    } else {
      ledgerPage.value = 1;
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
      reset_password: ""
    };
    return;
  }
  if (activeTab.value === "ledger" || activeTab.value === "quality") {
    return;
  }
}

function confirmDiscardChanges(message: string): boolean {
  if (!hasUnsavedChanges.value) {
    return true;
  }
  return window.confirm(message);
}

function switchTab(tab: MasterTab): void {
  if (tab === activeTab.value && route.path === TAB_PATH_MAP[tab]) {
    return;
  }
  if (!confirmDiscardChanges("目前表單有未儲存的修改，切換分頁後將會捨棄。要繼續嗎？")) {
    return;
  }
  keyword.value = "";
  statusFilter.value = "all";
  listPage.value = 1;
  ledgerKeyword.value = "";
  ledgerTypeFilter.value = "all";
  ledgerPage.value = 1;
  void router.push(TAB_PATH_MAP[tab]);
}

function startCreate(): void {
  if (!confirmDiscardChanges("目前表單有未儲存的修改，切換到新增模式後將會捨棄。要繼續嗎？")) {
    return;
  }
  startCreateWithoutPrompt();
}

function startCreateWithoutPrompt(): void {
  if (activeTab.value === "fixture") {
    selectedFixtureId.value = null;
    fixtureForm.value = makeEmptyFixtureForm();
    return;
  }
  if (activeTab.value === "model") {
    selectedModelId.value = null;
    modelForm.value = makeEmptyModelForm();
    return;
  }
  if (activeTab.value === "station") {
    selectedStationId.value = null;
    stationForm.value = makeEmptyStationForm();
    return;
  }
  if (activeTab.value === "user") {
    selectedUserId.value = null;
    userForm.value = makeEmptyUserForm();
    return;
  }
  if (activeTab.value === "customer") {
    selectedCustomerRowId.value = null;
    customerForm.value = makeEmptyCustomerForm();
    customerFormAssignedUserIds.value = [];
    return;
  }
  if (activeTab.value === "ledger" || activeTab.value === "quality") {
    return;
  }
}

function selectRow(id: number): void {
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
    return;
  }
  if (!confirmDiscardChanges("目前表單有未儲存的修改，切換資料後將會捨棄。要繼續嗎？")) {
    return;
  }
  if (activeTab.value === "fixture") selectedFixtureId.value = id;
  if (activeTab.value === "model") selectedModelId.value = id;
  if (activeTab.value === "station") selectedStationId.value = id;
  if (activeTab.value === "customer") selectedCustomerRowId.value = id;
  if (activeTab.value === "user") selectedUserId.value = id;
  if (activeTab.value === "ledger") selectedLedgerTransactionId.value = id;
  syncEditorFromSelection();
}

function openFixtureFromQuality(fixtureId: number): void {
  if (!confirmDiscardChanges("目前表單有未儲存的修改，切換到治具詳細資料後將會捨棄。要繼續嗎？")) {
    return;
  }
  activeTab.value = "fixture";
  keyword.value = "";
  statusFilter.value = "all";
  listPage.value = 1;
  selectedFixtureId.value = fixtureId;
  syncEditorFromSelection();
}

async function openSearchFixtureFromQuality(fixtureCode: string): Promise<void> {
  if (!confirmDiscardChanges("目前表單有未儲存的修改，切換到查詢頁後將會捨棄。要繼續嗎？")) {
    return;
  }
  await router.push({
    name: "search",
    query: {
      mode: "fixture",
      q: fixtureCode,
    },
  });
}

function reloadSelection(): void {
  if (!confirmDiscardChanges("重載會放棄目前尚未儲存的修改，重新載入已選資料。要繼續嗎？")) {
    return;
  }
  syncEditorFromSelection();
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

async function saveCurrent(): Promise<void> {
  const isUpdate =
    (activeTab.value === "fixture" && selectedFixtureId.value !== null) ||
    (activeTab.value === "model" && selectedModelId.value !== null) ||
    (activeTab.value === "station" && selectedStationId.value !== null) ||
    (activeTab.value === "customer" && selectedCustomerRowId.value !== null) ||
    (activeTab.value === "user" && selectedUserId.value !== null);
  saving.value = true;
  try {
    if (activeTab.value === "fixture") {
      if (!selectedCustomerId.value) {
        pushToast("請先在側邊欄選擇客戶。", "warning");
        return;
      }
      if (selectedFixtureId.value) {
        const fixture = await api.updateFixture(selectedFixtureId.value, {
          customer_id: selectedCustomerId.value,
          responsible_user_id: fixtureForm.value.responsible_user_id,
          code: fixtureForm.value.code.trim(),
          name: fixtureForm.value.name.trim(),
          line_storage_location: fixtureForm.value.line_storage_location.trim() || undefined,
          department_storage_location: fixtureForm.value.department_storage_location.trim() || undefined,
          min_stock_qty: fixtureForm.value.min_stock_qty,
          description: fixtureForm.value.description.trim() || undefined,
          is_active: fixtureForm.value.is_active
        });
        selectedFixtureId.value = fixture.id;
      } else {
        const fixture = await api.createFixture({
          customer_id: selectedCustomerId.value,
          responsible_user_id: fixtureForm.value.responsible_user_id,
          code: fixtureForm.value.code.trim(),
          name: fixtureForm.value.name.trim(),
          line_storage_location: fixtureForm.value.line_storage_location.trim() || undefined,
          department_storage_location: fixtureForm.value.department_storage_location.trim() || undefined,
          min_stock_qty: fixtureForm.value.min_stock_qty,
          description: fixtureForm.value.description.trim() || undefined
        });
        selectedFixtureId.value = fixture.id;
      }
    } else if (activeTab.value === "model") {
      if (!selectedCustomerId.value) {
        pushToast("請先選擇客戶。", "warning");
        return;
      }
      if (selectedModelId.value) {
        const model = await api.updateModel(selectedModelId.value, {
          customer_id: selectedCustomerId.value,
          code: modelForm.value.code.trim(),
          name: modelForm.value.name.trim(),
          is_active: modelForm.value.is_active
        });
        selectedModelId.value = model.id;
      } else {
        const model = await api.createModel({
          customer_id: selectedCustomerId.value,
          code: modelForm.value.code.trim(),
          name: modelForm.value.name.trim()
        });
        selectedModelId.value = model.id;
      }
    } else if (activeTab.value === "station") {
      if (!selectedCustomerId.value) {
        pushToast("請先選擇客戶。", "warning");
        return;
      }
      if (selectedStationId.value) {
        const station = await api.updateStation(selectedStationId.value, {
          customer_id: selectedCustomerId.value,
          code: stationForm.value.code.trim(),
          name: stationForm.value.name.trim(),
          is_active: stationForm.value.is_active
        });
        selectedStationId.value = station.id;
      } else {
        const station = await api.createStation({
          customer_id: selectedCustomerId.value,
          code: stationForm.value.code.trim(),
          name: stationForm.value.name.trim()
        });
        selectedStationId.value = station.id;
      }
    } else if (activeTab.value === "customer") {
      const assignedUserIds = [...customerFormAssignedUserIds.value].sort((a, b) => a - b);
      if (selectedCustomerRowId.value) {
        const customer = await api.updateCustomer(selectedCustomerRowId.value, {
          code: customerForm.value.code.trim(),
          name: customerForm.value.name.trim(),
          assigned_user_ids: assignedUserIds
        });
        selectedCustomerRowId.value = customer.id;
      } else {
        const customer = await api.createCustomer({
          code: customerForm.value.code.trim(),
          name: customerForm.value.name.trim(),
          assigned_user_ids: assignedUserIds
        });
        selectedCustomerId.value = customer.id;
        selectedCustomerRowId.value = customer.id;
      }
    } else if (activeTab.value === "user") {
      if (selectedUserId.value) {
        const user = await api.updateUser(selectedUserId.value, {
          email: userForm.value.email.trim() || null,
          display_name: userForm.value.display_name.trim(),
          role: userForm.value.role,
          is_active: userForm.value.is_active,
          allowed_customer_ids: []
        });
        selectedUserId.value = user.id;
      } else {
        if (!userForm.value.password.trim()) {
          pushToast("新增使用者時必須輸入密碼。", "warning");
          return;
        }
        const user = await api.createUser({
          username: userForm.value.username.trim(),
          email: userForm.value.email.trim() || null,
          password: userForm.value.password.trim(),
          display_name: userForm.value.display_name.trim(),
          role: userForm.value.role,
          is_active: userForm.value.is_active,
          allowed_customer_ids: []
        });
        selectedUserId.value = user.id;
      }
    }
    await loadData(false, { focusSelectedListRow: true, preserveLedgerPage: true });
    syncEditorFromSelection();
    pushToast(isUpdate ? "更新完成。" : "新增完成。", "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "儲存失敗", "error");
  } finally {
    saving.value = false;
  }
}

async function toggleCurrentActive(): Promise<void> {
  const nextActive = !(selectedActivatableRow.value?.is_active ?? true);
  saving.value = true;
  try {
    if (activeTab.value === "fixture" && selectedFixtureId.value) {
      if (!selectedCustomerId.value) {
        pushToast("請先在側邊欄選擇客戶。", "warning");
        return;
      }
      await api.updateFixture(selectedFixtureId.value, {
        customer_id: selectedCustomerId.value,
        responsible_user_id: fixtureForm.value.responsible_user_id,
        code: fixtureForm.value.code.trim(),
        name: fixtureForm.value.name.trim(),
        line_storage_location: fixtureForm.value.line_storage_location.trim() || undefined,
        department_storage_location: fixtureForm.value.department_storage_location.trim() || undefined,
        min_stock_qty: fixtureForm.value.min_stock_qty,
        description: fixtureForm.value.description.trim() || undefined,
        is_active: nextActive
      });
    } else if (activeTab.value === "model" && selectedModelId.value) {
      if (!selectedCustomerId.value) {
        pushToast("請先選擇客戶。", "warning");
        return;
      }
      await api.updateModel(selectedModelId.value, {
        customer_id: selectedCustomerId.value,
        code: modelForm.value.code.trim(),
        name: modelForm.value.name.trim(),
        is_active: nextActive
      });
    } else if (activeTab.value === "station" && selectedStationId.value) {
      if (!selectedCustomerId.value) {
        pushToast("請先選擇客戶。", "warning");
        return;
      }
      await api.updateStation(selectedStationId.value, {
        customer_id: selectedCustomerId.value,
        code: stationForm.value.code.trim(),
        name: stationForm.value.name.trim(),
        is_active: nextActive
      });
    } else if (activeTab.value === "user" && selectedUserId.value) {
      await api.updateUser(selectedUserId.value, {
        email: userForm.value.email.trim() || null,
        display_name: userForm.value.display_name.trim(),
        role: userForm.value.role,
        is_active: nextActive,
        allowed_customer_ids: []
      });
    } else {
      pushToast(activeTab.value === "customer" ? "客戶分頁不提供停用。" : "請先選擇要調整狀態的資料。", "warning");
      return;
    }
    await loadData(false, { focusSelectedListRow: true, preserveLedgerPage: true });
    syncEditorFromSelection();
    pushToast(nextActive ? "已恢復使用。" : "停用完成。", "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "狀態更新失敗", "error");
  } finally {
    saving.value = false;
  }
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
  closeMoreMenu();
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

function updateStatusFilter(value: "all" | "active" | "inactive"): void {
  statusFilter.value = value;
}

watch([activeTab, keyword, statusFilter], () => {
  listPage.value = 1;
});

function updateLedgerKeyword(value: string): void {
  ledgerKeyword.value = value;
}

function updateLedgerTypeFilter(value: "all" | "receipt" | "return"): void {
  ledgerTypeFilter.value = value;
}

function previousLedgerPage(): void {
  ledgerPage.value = Math.max(1, ledgerPage.value - 1);
}

function nextLedgerPage(): void {
  ledgerPage.value = Math.min(ledgerTotalPages.value, ledgerPage.value + 1);
}

watch([ledgerKeyword, ledgerTypeFilter], () => {
  ledgerPage.value = 1;
});

watch(filteredLedgerTransactions, () => {
  if (ledgerPage.value > ledgerTotalPages.value) {
    ledgerPage.value = ledgerTotalPages.value;
  }
  const selectedExists = filteredLedgerTransactions.value.some((row) => row.id === selectedLedgerTransactionId.value);
  if (!selectedExists) {
    selectedLedgerTransactionId.value = filteredLedgerTransactions.value[0]?.id ?? null;
  }
});

watch(currentRows, () => {
  if (listPage.value > listTotalPages.value) {
    listPage.value = listTotalPages.value;
  }
});

function downloadCsv(filename: string, content: string): void {
  const blob = new Blob([content], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

async function exportActiveCsv(): Promise<void> {
  try {
    closeMoreMenu();
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
    closeMoreMenu();
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

function triggerImport(): void {
  moreMenuOpen.value = false;
  if (activeTab.value !== "fixture" && activeTab.value !== "model" && activeTab.value !== "station") {
    pushToast("此分頁目前未提供匯入 CSV。", "info");
    return;
  }
  importInput.value?.click();
}

function toggleMoreMenu(): void {
  moreMenuOpen.value = !moreMenuOpen.value;
}

function closeMoreMenu(): void {
  moreMenuOpen.value = false;
}

function handleDocumentClick(event: MouseEvent): void {
  if (!moreMenuRef.value) return;
  const target = event.target;
  if (target instanceof Node && !moreMenuRef.value.contains(target)) {
    moreMenuOpen.value = false;
  }
}

async function reloadLedgerSelection(): Promise<void> {
  await loadData();
}

async function recalculateLedgerState(): Promise<void> {
  if (!selectedCustomerId.value) {
    pushToast("請先選擇客戶。", "warning");
    return;
  }
  if (!window.confirm("將依目前交易明細全量重算庫存摘要。要繼續嗎？")) {
    return;
  }
  ledgerProcessing.value = true;
  try {
    const result = await api.recalculateInventoryState(selectedCustomerId.value);
    await loadData(false, { preserveListPage: true, focusSelectedLedgerRow: true });
    pushToast(`重算完成：${result.fixture_count} 個治具、${result.item_count} 筆明細。`, "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "重算失敗", "error");
  } finally {
    ledgerProcessing.value = false;
  }
}

async function reverseSelectedLedgerTransaction(): Promise<void> {
  if (!selectedCustomerId.value) {
    pushToast("請先選擇客戶。", "warning");
    return;
  }
  if (!selectedLedgerTransaction.value) {
    pushToast("請先選擇要撤回的案件。", "warning");
    return;
  }
  const tx = selectedLedgerTransaction.value;
  if (!window.confirm(`確定要撤回單號 ${tx.transaction_no}？這會刪除整筆${tx.transaction_type === "receipt" ? "收料" : "退料"}案件並重算庫存。`)) {
    return;
  }
  ledgerProcessing.value = true;
  try {
    const result = await api.reverseTransaction(tx.id, selectedCustomerId.value);
    await loadData(false, { preserveListPage: true, focusSelectedLedgerRow: true });
    pushToast(`已撤回 ${result.transaction_no}，共 ${result.item_count} 筆明細。`, "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "撤回案件失敗", "error");
  } finally {
    ledgerProcessing.value = false;
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
    syncEditorFromSelection();
    pushToast(`匯入完成，共 ${result?.imported_count ?? 0} 筆。`, "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "匯入失敗", "error");
  } finally {
    input.value = "";
  }
}

watch(activeTab, syncEditorFromSelection);
watch(
  () => route.path,
  (pathname) => {
    activeTab.value = resolveMasterTabFromPath(pathname);
  },
  { immediate: true }
);
watch(selectedCustomerId, async () => {
  await loadData();
  syncEditorFromSelection();
});

onMounted(async () => {
  document.addEventListener("click", handleDocumentClick);
  activeTab.value = resolveMasterTabFromPath(route.path);
  await loadData();
  syncEditorFromSelection();
});

onBeforeUnmount(() => {
  document.removeEventListener("click", handleDocumentClick);
});
</script>

<template>
  <div class="master-shell">
    <UiSummaryCards class="summary-row" :cards="summaryCards" :desktop-columns="5" :tablet-columns="2" :mobile-columns="1" />

    <section class="toolbar panel">
      <div class="tab-bar" data-tour="master-tabs">
        <div class="tab-group">
          <span class="tab-group-label">資料維護</span>
          <button class="tab-btn" :class="{ active: activeTab === 'fixture' }" @click="switchTab('fixture')">治具資訊</button>
          <button class="tab-btn" :class="{ active: activeTab === 'model' }" @click="switchTab('model')">機種資訊</button>
          <button class="tab-btn" :class="{ active: activeTab === 'station' }" @click="switchTab('station')">站點資訊</button>
        </div>
        <div v-if="canManageCustomers || canManageUsers" class="tab-group tab-group-admin">
          <span class="tab-group-label">系統管理</span>
          <button v-if="canManageCustomers" class="tab-btn tab-btn-admin" :class="{ active: activeTab === 'customer' }" @click="switchTab('customer')">客戶</button>
          <button v-if="canManageUsers" class="tab-btn tab-btn-admin" :class="{ active: activeTab === 'user' }" @click="switchTab('user')">使用者</button>
          <button v-if="canManageLedger" class="tab-btn tab-btn-admin" :class="{ active: activeTab === 'ledger' }" @click="switchTab('ledger')">收退料帳目管理</button>
          <button v-if="canManageQuality" class="tab-btn tab-btn-admin" :class="{ active: activeTab === 'quality' }" @click="switchTab('quality')">治具資料品質</button>
        </div>
      </div>

        <div class="toolbar-side">
          <div class="toolbar-actions">
            <button
              class="outline-btn btn-compact toolbar-primary-action demo-tour-btn"
              type="button"
              :disabled="loading"
              @click="startDemoTour"
            >
              {{ selectedGlobalCustomer ? "開始新手導覽" : "先選客戶再導覽" }}
            </button>
            <button class="outline-btn btn-compact toolbar-primary-action" type="button" @click="router.push({ name: 'search' })">返回搜尋</button>
            <button class="outline-btn btn-compact toolbar-primary-action" type="button" :disabled="loading || activeTab === 'ledger'" @click="exportActiveCsv">匯出 CSV</button>
          <div ref="moreMenuRef" class="more-menu">
            <button class="outline-btn btn-compact more-menu-trigger" type="button" :disabled="loading || activeTab === 'ledger'" :aria-expanded="moreMenuOpen" @click.stop="toggleMoreMenu">更多</button>
            <div v-if="moreMenuOpen" class="more-menu-panel">
              <button class="more-menu-item" type="button" :disabled="loading" @click="downloadTemplate">下載範本</button>
              <button class="more-menu-item" type="button" :disabled="loading" @click="triggerImport">匯入 CSV</button>
              <button class="more-menu-item" type="button" :disabled="loading" @click="downloadCurrent">匯出 JSON</button>
            </div>
          </div>
          <input ref="importInput" type="file" accept=".csv,text/csv" class="hidden-input" @change="importCsv" />
        </div>
      </div>
    </section>

    <section class="content-grid" :class="{ 'content-grid-single': activeTab === 'quality' }">
      <template v-if="activeTab === 'quality'">
        <FixtureQualityPanel
          :report="fixtureQualityReport"
          :loading="loading"
          @open-fixture="openFixtureFromQuality"
          @open-search-fixture="openSearchFixtureFromQuality"
        />
      </template>

      <template v-else-if="activeTab !== 'ledger'">
        <MasterListPanel
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

        <MasterDetailPanel
        :active-tab="activeTab"
        :tab-title="tabTitleMap[activeTab]"
        :is-create-mode="isCreateMode"
        :selected-detail-label="selectedDetailLabel"
        :selected-status-badge="selectedStatusBadge"
        :saving="saving"
        :toggle-action-label="toggleActionLabel"
        :can-manage-customers="canManageCustomers"
        :can-manage-users="canManageUsers"
        :selected-fixture-id="selectedFixtureId"
        :selected-user-id="selectedUserId"
        :selected-customer-scope-count="selectedCustomerScopeCount"
        :selected-customer-row="selectedCustomerRow"
        :selected-user="selectedUser"
        :customer-assigned-users="customerAssignedUsers"
        :users="users"
        :fixture-form="fixtureForm"
        :model-form="modelForm"
        :station-form="stationForm"
        :customer-form="customerForm"
        :user-form="userForm"
        :on-start-create="startCreate"
        :on-reload-selection="reloadSelection"
        :on-save-current="saveCurrent"
        :on-toggle-current-active="toggleCurrentActive"
        :on-reset-user-password="resetUserPassword"
        :on-toggle-assigned-user="toggleAssignedUser"
        :on-has-assigned-user="hasAssignedUser"
        />
      </template>

      <template v-else>
        <TransactionAccountListPanel
          :rows="pagedLedgerRows"
          :selected-transaction-id="selectedLedgerTransactionId"
          :loading="loading"
          :keyword="ledgerKeyword"
          :transaction-type="ledgerTypeFilter"
          :page="ledgerPage"
          :total-pages="ledgerTotalPages"
          :on-keyword-change="updateLedgerKeyword"
          :on-transaction-type-change="updateLedgerTypeFilter"
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
  </div>
</template>

<style scoped>
.master-shell {
  height: 100%;
  overflow: hidden;
  padding: 8px;
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
  gap: 8px;
  background: #fff;
}

.panel {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
}

.loading-banner,
.empty-cell {
  text-align: center;
  padding: 14px 12px;
  color: #56657f;
  background: #f8fbff;
  border-top: 1px solid var(--line);
}

.panel {
  padding: 10px;
  min-width: 0;
  min-height: 0;
}

.toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(420px, 0.8fr);
  gap: 10px 14px;
  align-items: start;
}

.tab-bar {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tab-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.tab-group-admin {
  position: relative;
  margin-left: 10px;
  padding-left: 14px;
}

.tab-group-admin::before {
  content: "";
  position: absolute;
  left: 0;
  top: 4px;
  bottom: 4px;
  width: 1px;
  background: linear-gradient(180deg, rgba(182, 192, 208, 0) 0%, rgba(182, 192, 208, 0.95) 20%, rgba(182, 192, 208, 0.95) 80%, rgba(182, 192, 208, 0) 100%);
}

.tab-group-label {
  color: #7a869b;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.toolbar-side {
  display: grid;
  gap: 10px;
  min-width: 0;
}

.tab-btn {
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  background: linear-gradient(180deg, #ffffff 0%, #f7f9fd 100%);
  padding: 6px 10px;
  color: #5b677d;
  font-weight: 700;
  cursor: pointer;
  min-height: 32px;
  font-size: 12px;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease, filter 0.15s ease;
}

.tab-btn.active {
  border-color: #a9c3f9;
  background: linear-gradient(180deg, #eff5ff 0%, #e3eeff 100%);
  color: var(--blue);
  box-shadow: 0 6px 16px rgba(47, 110, 229, 0.12);
}

.tab-btn-admin {
  border-color: #d5dbe6;
  background: linear-gradient(180deg, #fffef9 0%, #f7f3e8 100%);
  color: #68563a;
}

.tab-btn-admin.active {
  border-color: #d7bf92;
  background: linear-gradient(180deg, #fff7e5 0%, #f8ecd2 100%);
  color: #8a5a08;
  box-shadow: 0 6px 16px rgba(180, 126, 28, 0.14);
}

.toolbar-actions,
.action-group {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.toolbar-actions {
  justify-content: flex-end;
}

.toolbar-primary-action {
  flex: 0 0 auto;
}

.more-menu {
  position: relative;
}

.more-menu-trigger {
  min-width: 72px;
}

.more-menu-panel {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: 20;
  min-width: 148px;
  display: grid;
  gap: 4px;
  padding: 6px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 14px 28px rgba(28, 47, 84, 0.14);
}

.more-menu-item {
  border: 1px solid transparent;
  border-radius: 8px;
  background: #fff;
  padding: 8px 10px;
  color: #324462;
  font: inherit;
  font-weight: 700;
  text-align: left;
  cursor: pointer;
}

.more-menu-item:hover {
  background: #f6f9ff;
  border-color: #d8e3f5;
}

.customer-admin {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr)) auto;
  gap: 8px;
  align-items: end;
  padding-top: 10px;
  border-top: 1px solid var(--line);
}

.customer-admin label {
  display: grid;
  gap: 6px;
}

.customer-admin span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}

.customer-admin input {
  width: 100%;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(360px, 420px);
  gap: 8px;
  min-height: 0;
  overflow: hidden;
}

.content-grid-single {
  grid-template-columns: minmax(0, 1fr);
}

.detail-panel,
.list-panel {
  display: grid;
  min-height: 0;
  gap: 8px;
  overflow: auto;
}

.detail-panel {
  grid-template-rows: auto minmax(0, 1fr);
}

.detail-panel-create {
  border-color: rgba(224, 138, 30, 0.28);
  background: linear-gradient(180deg, rgba(255, 252, 246, 0.98) 0%, rgba(255, 248, 237, 0.96) 100%);
  box-shadow: inset 0 0 0 1px rgba(255, 244, 220, 0.7);
}

.list-panel {
  grid-template-rows: auto auto minmax(0, 1fr);
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.panel-head h2 {
  margin: 0;
  color: #22314a;
  font-size: 15px;
}

.panel-head p {
  margin: 3px 0 0;
  color: var(--muted);
  font-size: 12px;
}

.detail-head-actions {
  align-items: center;
}

.action-divider-btn {
  margin-left: 8px;
}

.panel-head-create {
  padding: 10px 12px;
  margin: -2px -2px 0;
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(255, 243, 220, 0.95) 0%, rgba(255, 249, 237, 0.92) 100%);
  border: 1px solid rgba(224, 138, 30, 0.18);
}

.mode-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.mode-chip-create {
  color: #8f4b00;
  background: rgba(255, 239, 207, 0.95);
  border: 1px solid rgba(224, 138, 30, 0.24);
}

.list-toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 150px 128px;
  gap: 8px;
  align-items: start;
}

input,
select,
textarea {
  width: 100%;
  border: 1px solid var(--line-strong);
  border-radius: 8px;
  padding: 5px 8px;
  background: #fff;
  font: inherit;
  font-size: 12px;
}

textarea {
  resize: vertical;
}

.detail-form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 8px;
  align-content: start;
}

.detail-form label {
  display: grid;
  gap: 6px;
}

.field-hint {
  color: var(--muted);
  font-size: 11px;
  line-height: 1.3;
}

.detail-form label.full {
  grid-column: 1 / -1;
}

.form-actions-full {
  grid-column: 1 / -1;
}

.detail-form span {
  color: #56657f;
  font-size: 12px;
  font-weight: 700;
}

.inline-action {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 6px;
}

.customer-scope-note {
  border: 1px dashed var(--line-strong);
  border-radius: 8px;
  padding: 8px 10px;
  color: #5d6d89;
  background: #f7f9fd;
}

.role-scope-panel {
  display: grid;
  gap: 6px;
}

.customer-scope-panel {
  display: grid;
  gap: 8px;
}

.customer-scope-summary {
  color: #5d6d89;
  font-size: 12px;
  font-weight: 700;
}

.customer-scope-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 10px;
  background: #fbfcff;
  max-height: 220px;
  overflow: auto;
}

.customer-scope-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  min-width: 0;
  padding: 8px 10px;
  border: 1px solid #d9e3f2;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
}

.customer-scope-item:hover {
  border-color: #b8c9e6;
  background: #f8fbff;
}

.customer-scope-checkbox {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.customer-scope-indicator {
  width: 16px;
  height: 16px;
  margin-top: 2px;
  flex: 0 0 16px;
  border-radius: 999px;
  border: 2px solid #d24b4b;
  background: #fff;
  box-shadow: inset 0 0 0 3px #fff;
}

.customer-scope-indicator.selected {
  background: #d24b4b;
}

.customer-scope-text {
  color: #22314a;
  display: grid;
  gap: 2px;
  min-width: 0;
  line-height: 1.4;
}

.customer-scope-text strong,
.customer-scope-text small {
  display: block;
  min-width: 0;
  overflow-wrap: anywhere;
}

.customer-scope-text strong {
  font-size: 13px;
  font-weight: 700;
}

.customer-scope-text small {
  color: #5d6d89;
  font-size: 11px;
}

.actions {
  grid-column: 1 / -1;
  display: flex;
  justify-content: flex-end;
  gap: 4px;
  margin-top: 2px;
}

.tab-btn:hover {
  transform: translateY(-1px);
}

.outline-btn:hover, 
.tab-btn:hover {
  border-color: #c0cad9;
  box-shadow: 0 4px 12px rgba(28, 47, 84, 0.08);
}

.tab-btn:active {
  transform: translateY(0);
}

.data-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border: 1px solid var(--line);
  border-radius: 10px;
  overflow: hidden;
}

.table-scroll {
  min-width: 0;
  overflow-x: auto;
  min-height: 0;
}

.data-table th,
.data-table td {
  padding: 3px 8px;
  text-align: left;
  border-bottom: 1px solid var(--line);
  font-size: 12px;
}

.data-table thead th {
  background: #f7f9fd;
  color: #52607b;
  font-weight: 700;
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.data-table tbody tr:hover {
  background: #f6f9ff;
  cursor: pointer;
}

.data-table tbody tr.selected {
  background: #edf3ff;
}

.status-legend {
  margin-left: auto;
}

.hidden-input {
  display: none;
}

.list-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  color: #5d6d89;
  font-size: 12px;
}

.pager-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

@media (max-width: 1500px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .toolbar {
    grid-template-columns: 1fr;
  }

  .list-toolbar,
  .detail-form {
    grid-template-columns: 1fr;
  }

  .customer-scope-list {
    grid-template-columns: 1fr;
  }

  .actions {
    justify-content: stretch;
  }
}

@media (max-width: 900px) {
  .master-shell {
    padding: 6px;
    gap: 8px;
  }

  .toolbar-actions,
  .action-group {
    width: 100%;
  }

  .customer-admin {
    grid-template-columns: 1fr;
  }

  .toolbar-actions button,
  .action-group button {
    flex: 1 1 120px;
  }

  .toolbar-actions {
    justify-content: flex-start;
  }

  .tab-group-admin {
    margin-left: 0;
    padding-left: 0;
  }

  .tab-group-admin::before {
    display: none;
  }

  .more-menu {
    flex: 1 1 120px;
  }

  .more-menu-trigger {
    width: 100%;
  }

  .more-menu-panel {
    left: 0;
    right: auto;
    min-width: min(220px, 100%);
  }

  .detail-form,
  .list-toolbar {
    grid-template-columns: 1fr;
  }

  .panel-head,
  .toolbar,
  .list-toolbar {
    align-items: stretch;
  }

  .actions {
    flex-direction: column;
  }
}

@media (max-width: 640px) {
  .panel {
    padding: 10px;
  }

  .tab-bar {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .tab-btn {
    width: 100%;
  }

  .data-table th,
  .data-table td {
    white-space: nowrap;
  }

  .inline-action {
    grid-template-columns: 1fr;
  }
}
</style>

