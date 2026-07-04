<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";

import { api } from "@/api";
import { authSession, customers, onboardingActive, onboardingStepIndex, selectedCustomerId } from "@/appState";
import { onboardingSteps } from "@/onboarding";
import { pushToast } from "@/toastState";
import type { AppUser, Customer, Fixture, MachineModel, Station } from "@/types";
import { fallbackText } from "@/utils/display";
import { formatLocalDate } from "@/utils/date";
import UiStatusPill from "@/components/UiStatusPill.vue";
import UiFormActions from "@/components/UiFormActions.vue";

type MasterTab = "fixture" | "model" | "station" | "customer" | "user";

const router = useRouter();

const fixtures = ref<Fixture[]>([]);
const models = ref<MachineModel[]>([]);
const stations = ref<Station[]>([]);
const users = ref<AppUser[]>([]);
const customerRows = ref<Customer[]>([]);
const customerAssignedUsers = ref<AppUser[]>([]);

const activeTab = ref<MasterTab>("fixture");
const keyword = ref("");
const statusFilter = ref<"all" | "active" | "inactive">("all");
const loading = ref(false);
const saving = ref(false);
const listPage = ref(1);
const listPageSize = 10;

const selectedFixtureId = ref<number | null>(null);
const selectedModelId = ref<number | null>(null);
const selectedStationId = ref<number | null>(null);
const selectedUserId = ref<number | null>(null);
const selectedCustomerRowId = ref<number | null>(null);

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
const selectedCustomerScopeCount = computed(() => customerFormAssignedUserIds.value.length);
const customerFormAssignedUserIds = ref<number[]>([]);
const selectedGlobalCustomer = computed(() => customers.value.find((row) => row.id === selectedCustomerId.value) ?? null);

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
  customer: "客戶"
};

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

const currentRows = computed(() => {
  if (activeTab.value === "fixture") return filteredFixtures.value;
  if (activeTab.value === "model") return filteredModels.value;
  if (activeTab.value === "station") return filteredStations.value;
  if (activeTab.value === "customer") return filteredCustomers.value;
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
  if (statusFilter.value !== "all") return "目前篩選條件下沒有資料";
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

const summaryCards = computed(() => [
  { label: "治具總數", value: fixtures.value.length, meta: `啟用 ${fixtures.value.filter((row) => row.is_active).length}` },
  { label: "機種總數", value: models.value.length, meta: `啟用 ${models.value.filter((row) => row.is_active).length}` },
  { label: "站點總數", value: stations.value.length, meta: `啟用 ${stations.value.filter((row) => row.is_active).length}` },
  { label: "客戶", value: customerRows.value.length, meta: `可見 ${customerRows.value.length}` },
  { label: "使用者", value: users.value.length, meta: `啟用 ${users.value.filter((row) => row.is_active).length}` }
]);

async function startDemoTour(): Promise<void> {
  if (!selectedGlobalCustomer.value) {
    pushToast("請先選擇客戶，才可以開始新手導覽。", "warning");
    return;
  }
  if (!confirmDiscardChanges("開始導覽會從首頁重新開始，並使用目前客戶的資料做教學流程。要繼續嗎？")) {
    return;
  }
  onboardingStepIndex.value = 0;
  onboardingActive.value = true;
  await router.push({ path: onboardingSteps[0].route, query: { tour: "1" } });
}

async function loadData(showLoading = true): Promise<void> {
  if (showLoading) {
    loading.value = true;
  }
  try {
    const customerId = selectedCustomerId.value ?? undefined;
    const [f, m, s, u, c, customerUsers] = await Promise.all([
      api.listFixtures(customerId),
      customerId ? api.listModels(customerId) : Promise.resolve([]),
      customerId ? api.listStations(customerId) : Promise.resolve([]),
      canManageUsers.value ? api.listUsers() : Promise.resolve([]),
      api.listCustomers(),
      customerId ? api.listCustomerUsers(customerId) : Promise.resolve([])
    ]);
    fixtures.value = f;
    models.value = m;
    stations.value = s;
    users.value = u;
    customerRows.value = c;
    customerAssignedUsers.value = customerUsers;

    selectedFixtureId.value = f.find((row) => row.id === selectedFixtureId.value)?.id ?? f[0]?.id ?? null;
    selectedModelId.value = m.find((row) => row.id === selectedModelId.value)?.id ?? m[0]?.id ?? null;
    selectedStationId.value = s.find((row) => row.id === selectedStationId.value)?.id ?? s[0]?.id ?? null;
    selectedUserId.value = u.find((row) => row.id === selectedUserId.value)?.id ?? u[0]?.id ?? null;
    selectedCustomerRowId.value = c.find((row) => row.id === selectedCustomerRowId.value)?.id ?? c[0]?.id ?? null;
    if (!canManageUsers.value && activeTab.value === "user") {
      activeTab.value = "fixture";
    }
    listPage.value = 1;
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
}

function confirmDiscardChanges(message: string): boolean {
  if (!hasUnsavedChanges.value) {
    return true;
  }
  return window.confirm(message);
}

function switchTab(tab: MasterTab): void {
  if (tab === activeTab.value) {
    return;
  }
  if (!confirmDiscardChanges("目前表單有未儲存的修改，切換分頁後將會捨棄。要繼續嗎？")) {
    return;
  }
  activeTab.value = tab;
  keyword.value = "";
  statusFilter.value = "all";
  listPage.value = 1;
  syncEditorFromSelection();
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
  syncEditorFromSelection();
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
    let savedUserId: number | null = null;
    if (activeTab.value === "fixture") {
      if (!selectedCustomerId.value) {
        pushToast("請先在側邊欄選擇客戶。", "warning");
        return;
      }
      if (selectedFixtureId.value) {
        await api.updateFixture(selectedFixtureId.value, {
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
      } else {
        await api.createFixture({
          customer_id: selectedCustomerId.value,
          responsible_user_id: fixtureForm.value.responsible_user_id,
          code: fixtureForm.value.code.trim(),
          name: fixtureForm.value.name.trim(),
          line_storage_location: fixtureForm.value.line_storage_location.trim() || undefined,
          department_storage_location: fixtureForm.value.department_storage_location.trim() || undefined,
          min_stock_qty: fixtureForm.value.min_stock_qty,
          description: fixtureForm.value.description.trim() || undefined
        });
      }
    } else if (activeTab.value === "model") {
      if (!selectedCustomerId.value) {
        pushToast("請先選擇客戶。", "warning");
        return;
      }
      if (selectedModelId.value) {
        await api.updateModel(selectedModelId.value, {
          customer_id: selectedCustomerId.value,
          code: modelForm.value.code.trim(),
          name: modelForm.value.name.trim(),
          is_active: modelForm.value.is_active
        });
      } else {
        await api.createModel({
          customer_id: selectedCustomerId.value,
          code: modelForm.value.code.trim(),
          name: modelForm.value.name.trim()
        });
      }
    } else if (activeTab.value === "station") {
      if (!selectedCustomerId.value) {
        pushToast("請先選擇客戶。", "warning");
        return;
      }
      if (selectedStationId.value) {
        await api.updateStation(selectedStationId.value, {
          customer_id: selectedCustomerId.value,
          code: stationForm.value.code.trim(),
          name: stationForm.value.name.trim(),
          is_active: stationForm.value.is_active
        });
      } else {
        await api.createStation({
          customer_id: selectedCustomerId.value,
          code: stationForm.value.code.trim(),
          name: stationForm.value.name.trim()
        });
      }
    } else if (activeTab.value === "customer") {
      const assignedUserIds = [...customerFormAssignedUserIds.value].sort((a, b) => a - b);
      if (selectedCustomerRowId.value) {
        await api.updateCustomer(selectedCustomerRowId.value, {
          code: customerForm.value.code.trim(),
          name: customerForm.value.name.trim(),
          assigned_user_ids: assignedUserIds
        });
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
        savedUserId = user.id;
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
        savedUserId = user.id;
      }
    }
    await loadData(false);
    if (savedUserId !== null) {
      selectedUserId.value = savedUserId;
      syncEditorFromSelection();
    }
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
    await loadData(false);
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

watch([activeTab, keyword, statusFilter], () => {
  listPage.value = 1;
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
    await loadData(false);
    syncEditorFromSelection();
    pushToast(`匯入完成，共 ${result?.imported_count ?? 0} 筆。`, "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "匯入失敗", "error");
  } finally {
    input.value = "";
  }
}

watch(activeTab, syncEditorFromSelection);
watch(selectedCustomerId, async () => {
  await loadData();
  syncEditorFromSelection();
});

onMounted(async () => {
  document.addEventListener("click", handleDocumentClick);
  await loadData();
  syncEditorFromSelection();
});

onBeforeUnmount(() => {
  document.removeEventListener("click", handleDocumentClick);
});
</script>

<template>
  <div class="master-shell">
    <section class="summary-row">
      <article v-for="card in summaryCards" :key="card.label" class="summary-card">
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
        <p>{{ card.meta }}</p>
      </article>
    </section>

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
        </div>
      </div>

        <div class="toolbar-side">
          <div class="toolbar-actions">
            <button
              class="outline-btn toolbar-primary-action demo-tour-btn"
              type="button"
              :disabled="loading"
              @click="startDemoTour"
            >
              {{ selectedGlobalCustomer ? "開始新手導覽" : "先選客戶再導覽" }}
            </button>
            <button class="outline-btn toolbar-primary-action" type="button" @click="router.push({ name: 'search' })">返回搜尋</button>
            <button class="outline-btn toolbar-primary-action" type="button" :disabled="loading" @click="exportActiveCsv">匯出 CSV</button>
          <div ref="moreMenuRef" class="more-menu">
            <button class="outline-btn more-menu-trigger" type="button" :disabled="loading" :aria-expanded="moreMenuOpen" @click.stop="toggleMoreMenu">更多</button>
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

    <section class="content-grid">
      <article class="panel list-panel">
        <div class="panel-head">
          <div>
            <h2>{{ tabTitleMap[activeTab] }}清單</h2>
            <p>{{ currentRows.length }} 筆資料</p>
          </div>
        </div>

        <div class="list-toolbar" data-tour="master-list-toolbar">
          <input v-model="keyword" :placeholder="searchPlaceholder" :disabled="loading" />
          <select v-if="activeTab !== 'customer'" v-model="statusFilter">
            <option value="all">狀態：全部</option>
            <option value="active">狀態：啟用中</option>
            <option value="inactive">狀態：停用</option>
          </select>
          <button class="primary-btn" type="button" :disabled="loading || (activeTab === 'customer' && !canManageCustomers)" @click="startCreate">+ 新增{{ tabTitleMap[activeTab] }}</button>
        </div>

        <div v-if="loading" class="loading-banner">資料載入中，請稍候...</div>

        <div class="table-scroll" data-tour="master-list-table">
          <table class="data-table">
            <thead>
              <tr v-if="activeTab === 'fixture'"><th>治具編號</th><th>治具名稱</th><th>水位</th><th>產線儲位</th><th>部門儲位</th><th>狀態</th></tr>
              <tr v-else-if="activeTab === 'model'"><th>機種編號</th><th>機種名稱</th><th>狀態</th></tr>
              <tr v-else-if="activeTab === 'station'"><th>站點編號</th><th>站點名稱</th><th>狀態</th></tr>
              <tr v-else-if="activeTab === 'customer'"><th>客戶代碼</th><th>客戶名稱</th></tr>
              <tr v-else><th>帳號</th><th>Email</th><th>顯示名稱</th><th>角色</th><th>狀態</th></tr>
            </thead>

            <tbody v-if="activeTab === 'fixture'">
              <tr v-for="row in pagedFixtureRows" :key="row.id" :class="{ selected: selectedFixtureId === row.id }" @click="selectRow(row.id)">
                <td>{{ row.code }}</td><td>{{ row.name }}</td><td>{{ row.min_stock_qty }}</td><td>{{ row.line_storage_location || "-" }}</td><td>{{ row.department_storage_location || "-" }}</td><td><span class="status-pill" :class="row.is_active ? 'active' : 'inactive'">{{ row.is_active ? "啟用中" : "停用" }}</span></td>
              </tr>
              <tr v-if="!loading && currentRows.length === 0">
                <td colspan="6" class="empty-cell">{{ emptyStateMessage }}</td>
              </tr>
            </tbody>
            <tbody v-else-if="activeTab === 'model'">
              <tr v-for="row in pagedModelRows" :key="row.id" :class="{ selected: selectedModelId === row.id }" @click="selectRow(row.id)">
                <td>{{ row.code }}</td><td>{{ row.name }}</td><td><span class="status-pill" :class="row.is_active ? 'active' : 'inactive'">{{ row.is_active ? "啟用中" : "停用" }}</span></td>
              </tr>
              <tr v-if="!loading && currentRows.length === 0">
                <td colspan="3" class="empty-cell">{{ emptyStateMessage }}</td>
              </tr>
            </tbody>
            <tbody v-else-if="activeTab === 'station'">
              <tr v-for="row in pagedStationRows" :key="row.id" :class="{ selected: selectedStationId === row.id }" @click="selectRow(row.id)">
                <td>{{ row.code }}</td><td>{{ row.name }}</td><td><span class="status-pill" :class="row.is_active ? 'active' : 'inactive'">{{ row.is_active ? "啟用中" : "停用" }}</span></td>
              </tr>
              <tr v-if="!loading && currentRows.length === 0">
                <td colspan="3" class="empty-cell">{{ emptyStateMessage }}</td>
              </tr>
            </tbody>
            <tbody v-else-if="activeTab === 'customer'">
              <tr v-for="row in pagedCustomerRows" :key="row.id" :class="{ selected: selectedCustomerRowId === row.id }" @click="selectRow(row.id)">
                <td>{{ row.code }}</td><td>{{ row.name }}</td>
              </tr>
              <tr v-if="!loading && currentRows.length === 0">
                <td colspan="2" class="empty-cell">{{ emptyStateMessage }}</td>
              </tr>
            </tbody>
            <tbody v-else>
                <tr v-for="row in pagedUserRows" :key="row.id" :class="{ selected: selectedUserId === row.id }" @click="selectRow(row.id)">
                 <td>{{ row.username }}</td><td>{{ fallbackText(row.email) }}</td><td>{{ row.display_name }}</td><td>{{ row.role }}</td><td><span class="status-pill" :class="row.is_active ? 'active' : 'inactive'">{{ row.is_active ? "啟用中" : "停用" }}</span></td>
               </tr>
              <tr v-if="!loading && currentRows.length === 0">
                <td colspan="5" class="empty-cell">{{ emptyStateMessage }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="currentRows.length > 0" class="list-footer">
          <span>第 {{ listPage }} / {{ listTotalPages }} 頁，共 {{ currentRows.length }} 筆</span>
          <div class="pager-actions">
            <button class="outline-btn small" type="button" :disabled="loading || listPage <= 1" @click="previousListPage">上一頁</button>
            <button class="outline-btn small" type="button" :disabled="loading || listPage >= listTotalPages" @click="nextListPage">下一頁</button>
          </div>
        </div>
      </article>

      <article class="panel detail-panel" :class="{ 'detail-panel-create': isCreateMode }">
        <div class="panel-head" :class="{ 'panel-head-create': isCreateMode }">
          <div>
            <h2>{{ tabTitleMap[activeTab] }}詳細資料</h2>
            <p>{{ isCreateMode ? "新增資料" : selectedDetailLabel }}</p>
          </div>
          <span v-if="isCreateMode" class="mode-chip mode-chip-create">新增模式</span>
          <UiStatusPill
            v-if="selectedStatusBadge"
            class="status-legend"
            :label="selectedStatusBadge.label"
            :tone="selectedStatusBadge.tone"
          />
          <div class="action-group detail-head-actions">
            <button class="outline-btn small" type="button" :disabled="saving" @click="startCreate">新增</button>
            <button class="ghost-btn small action-divider-btn" type="button" :disabled="saving || isCreateMode" @click="reloadSelection">重載</button>
          </div>
        </div>

        <form class="detail-form" data-tour="master-detail-form" @submit.prevent="saveCurrent">
          <template v-if="activeTab === 'fixture'">
            <label>
              <span>治具編號 *</span>
              <input v-model="fixtureForm.code" required />
            </label>
            <label><span>治具名稱 *</span><input v-model="fixtureForm.name" required /></label>
            <label><span>產線儲位</span><input v-model="fixtureForm.line_storage_location" placeholder="A-01-03" /></label>
            <label><span>部門儲位</span><input v-model="fixtureForm.department_storage_location" placeholder="RD-SHELF-3" /></label>
            <label><span>最低水位</span><input v-model.number="fixtureForm.min_stock_qty" type="number" min="0" /></label>
            <label>
              <span>負責人</span>
              <select v-model="fixtureForm.responsible_user_id">
                <option :value="null">未指定</option>
                <option v-for="user in customerAssignedUsers.filter((row) => row.is_active)" :key="user.id" :value="user.id">{{ user.display_name }}</option>
              </select>
            </label>
            <label>
              <span>狀態</span>
              <select v-model="fixtureForm.is_active">
                <option :value="true">啟用中</option>
                <option :value="false">停用</option>
              </select>
            </label>
            <label class="full"><span>備註</span><textarea v-model="fixtureForm.description" rows="4" placeholder="輸入備註內容..." /></label>
          </template>

          <template v-else-if="activeTab === 'model'">
            <label><span>機種編號 *</span><input v-model="modelForm.code" required /></label>
            <label><span>機種名稱 *</span><input v-model="modelForm.name" required /></label>
            <label class="full">
              <span>狀態</span>
              <select v-model="modelForm.is_active">
                <option :value="true">啟用中</option>
                <option :value="false">停用</option>
              </select>
            </label>
          </template>

          <template v-else-if="activeTab === 'station'">
            <label><span>站點編號 *</span><input v-model="stationForm.code" required /></label>
            <label><span>站點名稱 *</span><input v-model="stationForm.name" required /></label>
            <label class="full">
              <span>狀態</span>
              <select v-model="stationForm.is_active">
                <option :value="true">啟用中</option>
                <option :value="false">停用</option>
              </select>
            </label>
          </template>

          <template v-else-if="activeTab === 'customer' && canManageCustomers">
            <label><span>客戶代碼 *</span><input v-model="customerForm.code" required /></label>
            <label><span>客戶名稱 *</span><input v-model="customerForm.name" required /></label>
            <div class="full role-scope-panel">
              <span>指派使用者</span>
              <div class="customer-scope-panel">
                <div class="customer-scope-summary">已選 {{ selectedCustomerScopeCount }} 位使用者</div>
                <div class="customer-scope-list">
                  <label v-for="user in users" :key="user.id" class="customer-scope-item">
                    <input
                      class="customer-scope-checkbox"
                      :checked="hasAssignedUser(user.id)"
                      type="checkbox"
                      @change="toggleAssignedUser(user.id, ($event.target as HTMLInputElement).checked)"
                    />
                    <span class="customer-scope-indicator" :class="{ selected: hasAssignedUser(user.id) }" aria-hidden="true"></span>
                    <span class="customer-scope-text">
                      <strong>{{ user.display_name }}</strong>
                      <small>{{ user.username }}</small>
                    </span>
                  </label>
                </div>
              </div>
            </div>
            <label class="full"><span>建立時間</span><input :value="formatLocalDate(selectedCustomerRow?.created_at)" disabled /></label>
            <label class="full"><span>更新時間</span><input :value="formatLocalDate(selectedCustomerRow?.updated_at)" disabled /></label>
          </template>

          <template v-else-if="canManageUsers">
            <label><span>帳號 *</span><input v-model="userForm.username" :disabled="selectedUserId !== null" required /></label>
            <label><span>Email</span><input v-model="userForm.email" type="email" placeholder="name@example.com" /></label>
            <label><span>顯示名稱 *</span><input v-model="userForm.display_name" required /></label>
            <label><span>角色</span><select v-model="userForm.role"><option value="admin">Admin</option><option value="user">User</option></select></label>
            <label><span>狀態</span><select v-model="userForm.is_active"><option :value="true">啟用中</option><option :value="false">停用</option></select></label>
            <label v-if="selectedUserId === null" class="full"><span>登入密碼 *</span><input v-model="userForm.password" type="password" minlength="6" required /></label>
            <label class="full"><span>建立時間</span><input :value="formatLocalDate(selectedUser?.created_at)" disabled /></label>
            <label class="full"><span>更新時間</span><input :value="formatLocalDate(selectedUser?.updated_at)" disabled /></label>
            <label v-if="selectedUserId !== null" class="full">
              <span>重設密碼</span>
              <div class="inline-action">
                <input v-model="userForm.reset_password" type="password" minlength="6" placeholder="輸入新密碼" />
                <button class="outline-btn" type="button" @click="resetUserPassword">重設密碼</button>
              </div>
            </label>
          </template>

          <UiFormActions
            class="form-actions-full"
            data-tour="master-form-actions"
            :editing="!isCreateMode"
            :saving="saving"
            submit-label="儲存"
            saving-label="儲存中..."
            cancel-label="取消"
            :delete-label="toggleActionLabel"
            :show-delete="activeTab !== 'customer'"
            :state-text="isCreateMode ? '新增模式' : '編輯模式'"
            @cancel="startCreate"
            @delete="toggleCurrentActive"
          />
        </form>
      </article>
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

.summary-row {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
}

.summary-card,
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

.summary-card {
  padding: 9px 10px;
  display: grid;
  gap: 4px;
}

.summary-card span {
  color: var(--muted);
  font-size: 12px;
}

.summary-card strong {
  color: #22314a;
  font-size: 20px;
  line-height: 1.1;
}

.summary-card p {
  margin: 0;
  color: #5d6d89;
  font-size: 12px;
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

.primary-btn,
.outline-btn,
.danger-btn {
  border-radius: 10px;
  font-weight: 700;
  cursor: pointer;
  min-height: 30px;
  font-size: 12px;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease, filter 0.15s ease;
}

.primary-btn {
  border: 1px solid var(--green);
  background: linear-gradient(180deg, #4cc36b 0%, #2ea54e 100%);
  color: #fff;
  padding: 6px 10px;
  box-shadow: 0 6px 14px rgba(46, 165, 78, 0.16);
}

.outline-btn {
  border: 1px solid var(--line-strong);
  background: linear-gradient(180deg, #ffffff 0%, #f7f9fd 100%);
  color: #5b677d;
  padding: 6px 10px;
}

.outline-btn.small {
  padding: 5px 8px;
  min-height: 28px;
}

.danger-btn {
  border: 1px solid #df5a5a;
  background: linear-gradient(180deg, #ff7a72 0%, #e95d57 100%);
  color: #fff;
  padding: 6px 10px;
  box-shadow: 0 6px 14px rgba(233, 93, 87, 0.14);
}

.primary-btn:hover,
.outline-btn:hover,
.danger-btn:hover,
.tab-btn:hover {
  transform: translateY(-1px);
}

.primary-btn:hover {
  box-shadow: 0 10px 22px rgba(46, 165, 78, 0.24);
  filter: brightness(1.02);
}

.outline-btn:hover, 
.tab-btn:hover {
  border-color: #c0cad9;
  box-shadow: 0 4px 12px rgba(28, 47, 84, 0.08);
}

.primary-btn:disabled,
.outline-btn:disabled,
.danger-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.danger-btn:hover {
  box-shadow: 0 10px 22px rgba(233, 93, 87, 0.2);
}

.primary-btn:active,
.outline-btn:active,
.danger-btn:active,
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

.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 64px;
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 700;
}

.status-pill.active {
  color: var(--green);
  background: var(--green-soft);
}

.status-pill.inactive {
  color: var(--red);
  background: var(--red-soft);
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
  .summary-row,
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

  .summary-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
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
  .summary-row {
    grid-template-columns: 1fr;
  }

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

