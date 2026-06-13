<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { api } from "@/api";
import { authSession, customers, selectedCustomerId } from "@/appState";
import { pushToast } from "@/toastState";
import type { AppUser, Fixture, MachineModel, Owner, Station } from "@/types";
import { fallbackText } from "@/utils/display";
import UiStatusPill from "@/components/UiStatusPill.vue";
import UiFormActions from "@/components/UiFormActions.vue";

type MasterTab = "fixture" | "model" | "station" | "owner" | "user";

const fixtures = ref<Fixture[]>([]);
const models = ref<MachineModel[]>([]);
const stations = ref<Station[]>([]);
const owners = ref<Owner[]>([]);
const users = ref<AppUser[]>([]);

const activeTab = ref<MasterTab>("fixture");
const keyword = ref("");
const statusFilter = ref<"all" | "active" | "inactive">("all");
const loading = ref(false);
const listPage = ref(1);
const listPageSize = 10;

const selectedFixtureId = ref<number | null>(null);
const selectedModelId = ref<number | null>(null);
const selectedStationId = ref<number | null>(null);
const selectedOwnerId = ref<number | null>(null);
const selectedUserId = ref<number | null>(null);

const fixtureForm = ref({
  code: "",
  name: "",
  owner_id: null as number | null,
  storage_location: "",
  min_stock_qty: 0,
  description: "",
  is_active: true
});
const modelForm = ref({ code: "", name: "", is_active: true });
const stationForm = ref({ code: "", name: "", is_active: true });
const ownerForm = ref({ name: "", is_active: true });
const customerForm = ref({ code: "", name: "" });
const userForm = ref({
  username: "",
  display_name: "",
  role: "user",
  is_active: true,
  password: "",
  reset_password: ""
});
const importInput = ref<HTMLInputElement | null>(null);
const canManageUsers = computed(() => authSession.value?.role === "admin");
const canManageCustomers = computed(() => authSession.value?.role === "admin");
const creatingCustomer = ref(false);

const tabTitleMap: Record<MasterTab, string> = {
  fixture: "治具",
  model: "機種",
  station: "站點",
  owner: "負責人",
  user: "使用者"
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
  models.value.filter(
    (row) =>
      !keyword.value ||
      row.code.toLowerCase().includes(keyword.value.toLowerCase()) ||
      row.name.toLowerCase().includes(keyword.value.toLowerCase())
  )
);

const filteredStations = computed(() =>
  stations.value.filter(
    (row) =>
      !keyword.value ||
      row.code.toLowerCase().includes(keyword.value.toLowerCase()) ||
      row.name.toLowerCase().includes(keyword.value.toLowerCase())
  )
);

const filteredOwners = computed(() =>
  owners.value.filter((row) => !keyword.value || row.name.toLowerCase().includes(keyword.value.toLowerCase()))
);

const filteredUsers = computed(() =>
  users.value.filter((row) => {
    const byKeyword =
      !keyword.value ||
      row.username.toLowerCase().includes(keyword.value.toLowerCase()) ||
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
  if (activeTab.value === "owner") return filteredOwners.value;
  return filteredUsers.value;
});

const listTotalPages = computed(() => Math.max(1, Math.ceil(currentRows.value.length / listPageSize)));
const pagedFixtureRows = computed(() => filteredFixtures.value.slice((listPage.value - 1) * listPageSize, listPage.value * listPageSize));
const pagedModelRows = computed(() => filteredModels.value.slice((listPage.value - 1) * listPageSize, listPage.value * listPageSize));
const pagedStationRows = computed(() => filteredStations.value.slice((listPage.value - 1) * listPageSize, listPage.value * listPageSize));
const pagedOwnerRows = computed(() => filteredOwners.value.slice((listPage.value - 1) * listPageSize, listPage.value * listPageSize));
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
const selectedOwner = computed(() => owners.value.find((row) => row.id === selectedOwnerId.value) ?? null);
const selectedUser = computed(() => users.value.find((row) => row.id === selectedUserId.value) ?? null);
const selectedDetailLabel = computed(() =>
  fallbackText(
    selectedFixture.value?.code ||
      selectedModel.value?.code ||
      selectedStation.value?.code ||
      selectedOwner.value?.name ||
      selectedUser.value?.username
  )
);
const selectedStatusBadge = computed(() => {
  const row =
    activeTab.value === "fixture"
      ? selectedFixture.value
      : activeTab.value === "model"
        ? selectedModel.value
        : activeTab.value === "station"
          ? selectedStation.value
          : activeTab.value === "owner"
            ? selectedOwner.value
            : selectedUser.value;
  if (!row) return null;
  return {
    label: row.is_active ? "啟用中" : "停用",
    tone: (row.is_active ? "active" : "inactive") as "active" | "inactive"
  };
});

const summaryCards = computed(() => [
  { label: "治具總數", value: fixtures.value.length, meta: `啟用 ${fixtures.value.filter((row) => row.is_active).length}` },
  { label: "機種總數", value: models.value.length, meta: `啟用 ${models.value.filter((row) => row.is_active).length}` },
  { label: "站點總數", value: stations.value.length, meta: `啟用 ${stations.value.filter((row) => row.is_active).length}` },
  { label: "負責人", value: owners.value.length, meta: `啟用 ${owners.value.filter((row) => row.is_active).length}` },
  { label: "使用者", value: users.value.length, meta: `啟用 ${users.value.filter((row) => row.is_active).length}` }
]);

async function createCustomer(): Promise<void> {
  if (!customerForm.value.code.trim() || !customerForm.value.name.trim()) {
    pushToast("請輸入客戶代碼與名稱。", "warning");
    return;
  }
  creatingCustomer.value = true;
  try {
    const customer = await api.createCustomer({
      code: customerForm.value.code.trim(),
      name: customerForm.value.name.trim()
    });
    customers.value = await api.listCustomers();
    selectedCustomerId.value = customer.id;
    customerForm.value.code = "";
    customerForm.value.name = "";
    pushToast(`已新增客戶：${customer.code}`, "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "新增客戶失敗", "error");
  } finally {
    creatingCustomer.value = false;
  }
}

async function loadData(): Promise<void> {
  loading.value = true;
  try {
    const customerId = selectedCustomerId.value ?? undefined;
    const [f, m, s, o, u] = await Promise.all([
      api.listFixtures(customerId),
      customerId ? api.listModels(customerId) : Promise.resolve([]),
      customerId ? api.listStations(customerId) : Promise.resolve([]),
      api.listOwners(),
      canManageUsers.value ? api.listUsers() : Promise.resolve([])
    ]);
    fixtures.value = f;
    models.value = m;
    stations.value = s;
    owners.value = o;
    users.value = u;

    selectedFixtureId.value = f.find((row) => row.id === selectedFixtureId.value)?.id ?? f[0]?.id ?? null;
    selectedModelId.value = m.find((row) => row.id === selectedModelId.value)?.id ?? m[0]?.id ?? null;
    selectedStationId.value = s.find((row) => row.id === selectedStationId.value)?.id ?? s[0]?.id ?? null;
    selectedOwnerId.value = o.find((row) => row.id === selectedOwnerId.value)?.id ?? o[0]?.id ?? null;
    selectedUserId.value = u.find((row) => row.id === selectedUserId.value)?.id ?? u[0]?.id ?? null;
    if (!canManageUsers.value && activeTab.value === "user") {
      activeTab.value = "fixture";
    }
    listPage.value = 1;
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "載入資料維護資料失敗", "error");
  } finally {
    loading.value = false;
  }
}

function syncEditorFromSelection(): void {
  if (activeTab.value === "fixture") {
    const row = selectedFixture.value;
    if (!row) return;
    fixtureForm.value = {
      code: row.code,
      name: row.name,
      owner_id: row.owner_id,
      storage_location: row.storage_location ?? "",
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
  if (activeTab.value === "user") {
    const row = selectedUser.value;
    if (!row) return;
    userForm.value = {
      username: row.username,
      display_name: row.display_name,
      role: row.role,
      is_active: row.is_active,
      password: "",
      reset_password: ""
    };
    return;
  }
  const row = selectedOwner.value;
  if (!row) return;
  ownerForm.value = { name: row.name, is_active: row.is_active };
}

function switchTab(tab: MasterTab): void {
  activeTab.value = tab;
  keyword.value = "";
  statusFilter.value = "all";
  listPage.value = 1;
  syncEditorFromSelection();
}

function startCreate(): void {
  if (activeTab.value === "fixture") {
    selectedFixtureId.value = null;
    fixtureForm.value = {
      code: "",
      name: "",
      owner_id: null,
      storage_location: "",
      min_stock_qty: 0,
      description: "",
      is_active: true
    };
    return;
  }
  if (activeTab.value === "model") {
    selectedModelId.value = null;
    modelForm.value = { code: "", name: "", is_active: true };
    return;
  }
  if (activeTab.value === "station") {
    selectedStationId.value = null;
    stationForm.value = { code: "", name: "", is_active: true };
    return;
  }
  if (activeTab.value === "user") {
    selectedUserId.value = null;
    userForm.value = {
      username: "",
      display_name: "",
      role: "user",
      is_active: true,
      password: "",
      reset_password: ""
    };
    return;
  }
  selectedOwnerId.value = null;
  ownerForm.value = { name: "", is_active: true };
}

function selectRow(id: number): void {
  if (activeTab.value === "fixture") selectedFixtureId.value = id;
  if (activeTab.value === "model") selectedModelId.value = id;
  if (activeTab.value === "station") selectedStationId.value = id;
  if (activeTab.value === "owner") selectedOwnerId.value = id;
  if (activeTab.value === "user") selectedUserId.value = id;
  syncEditorFromSelection();
}

async function saveCurrent(): Promise<void> {
  const isUpdate =
    (activeTab.value === "fixture" && selectedFixtureId.value !== null) ||
    (activeTab.value === "model" && selectedModelId.value !== null) ||
    (activeTab.value === "station" && selectedStationId.value !== null) ||
    (activeTab.value === "owner" && selectedOwnerId.value !== null) ||
    (activeTab.value === "user" && selectedUserId.value !== null);
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
          owner_id: fixtureForm.value.owner_id,
          code: fixtureForm.value.code.trim(),
          name: fixtureForm.value.name.trim(),
          storage_location: fixtureForm.value.storage_location.trim() || undefined,
          min_stock_qty: fixtureForm.value.min_stock_qty,
          description: fixtureForm.value.description.trim() || undefined,
          is_active: fixtureForm.value.is_active
        });
      } else {
        await api.createFixture({
          customer_id: selectedCustomerId.value,
          owner_id: fixtureForm.value.owner_id,
          code: fixtureForm.value.code.trim(),
          name: fixtureForm.value.name.trim(),
          storage_location: fixtureForm.value.storage_location.trim() || undefined,
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
    } else if (activeTab.value === "user") {
      if (selectedUserId.value) {
        const user = await api.updateUser(selectedUserId.value, {
          display_name: userForm.value.display_name.trim(),
          role: userForm.value.role,
          is_active: userForm.value.is_active
        });
        savedUserId = user.id;
      } else {
        if (!userForm.value.password.trim()) {
          pushToast("新增使用者時必須輸入密碼。", "warning");
          return;
        }
        const user = await api.createUser({
          username: userForm.value.username.trim(),
          password: userForm.value.password.trim(),
          display_name: userForm.value.display_name.trim(),
          role: userForm.value.role,
          is_active: userForm.value.is_active
        });
        savedUserId = user.id;
      }
    } else {
      if (selectedOwnerId.value) {
        await api.updateOwner(selectedOwnerId.value, { name: ownerForm.value.name.trim(), is_active: ownerForm.value.is_active });
      } else {
        await api.createOwner({ name: ownerForm.value.name.trim() });
      }
    }
    await loadData();
    if (savedUserId !== null) {
      selectedUserId.value = savedUserId;
      syncEditorFromSelection();
    }
    pushToast(isUpdate ? "更新完成。" : "新增完成。", "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "儲存失敗", "error");
  }
}

async function deactivateCurrent(): Promise<void> {
  try {
    if (activeTab.value === "fixture" && selectedFixtureId.value) {
      if (!selectedCustomerId.value) {
        pushToast("請先在側邊欄選擇客戶。", "warning");
        return;
      }
      await api.updateFixture(selectedFixtureId.value, {
        customer_id: selectedCustomerId.value,
        owner_id: fixtureForm.value.owner_id,
        code: fixtureForm.value.code.trim(),
        name: fixtureForm.value.name.trim(),
        storage_location: fixtureForm.value.storage_location.trim() || undefined,
        min_stock_qty: fixtureForm.value.min_stock_qty,
        description: fixtureForm.value.description.trim() || undefined,
        is_active: false
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
        is_active: false
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
        is_active: false
      });
    } else if (activeTab.value === "owner" && selectedOwnerId.value) {
      await api.updateOwner(selectedOwnerId.value, { name: ownerForm.value.name.trim(), is_active: false });
    } else if (activeTab.value === "user" && selectedUserId.value) {
      await api.updateUser(selectedUserId.value, {
        display_name: userForm.value.display_name.trim(),
        role: userForm.value.role,
        is_active: false
      });
    } else {
      pushToast("請先選擇要停用的資料。", "warning");
      return;
    }
    await loadData();
    syncEditorFromSelection();
    pushToast("停用完成。", "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "停用失敗", "error");
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
  try {
    await api.resetUserPassword(selectedUserId.value, userForm.value.reset_password.trim());
    userForm.value.reset_password = "";
    pushToast("密碼已重設。", "success");
  } catch (err) {
    pushToast(err instanceof Error ? err.message : "重設密碼失敗", "error");
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

function triggerImport(): void {
  if (activeTab.value !== "fixture" && activeTab.value !== "model" && activeTab.value !== "station") {
    pushToast("此分頁目前未提供匯入 CSV。", "info");
    return;
  }
  importInput.value?.click();
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
    await loadData();
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
  await loadData();
  syncEditorFromSelection();
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
      <div class="tab-bar">
        <button class="tab-btn" :class="{ active: activeTab === 'fixture' }" @click="switchTab('fixture')">治具資訊</button>
        <button class="tab-btn" :class="{ active: activeTab === 'model' }" @click="switchTab('model')">機種資訊</button>
        <button class="tab-btn" :class="{ active: activeTab === 'station' }" @click="switchTab('station')">站點資訊</button>
        <button class="tab-btn" :class="{ active: activeTab === 'owner' }" @click="switchTab('owner')">負責人</button>
        <button v-if="canManageUsers" class="tab-btn" :class="{ active: activeTab === 'user' }" @click="switchTab('user')">使用者</button>
      </div>

      <div class="toolbar-actions">
        <button class="outline-btn" type="button" :disabled="loading" @click="downloadTemplate">下載範本</button>
        <button class="outline-btn" type="button" :disabled="loading" @click="triggerImport">匯入 CSV</button>
        <button class="outline-btn" type="button" :disabled="loading" @click="exportActiveCsv">匯出 CSV</button>
        <button class="outline-btn" type="button" :disabled="loading" @click="downloadCurrent">匯出 JSON</button>
        <input ref="importInput" type="file" accept=".csv,text/csv" class="hidden-input" @change="importCsv" />
      </div>

      <form v-if="canManageCustomers" class="customer-create customer-admin" @submit.prevent="createCustomer">
        <label>
          <span>客戶代碼</span>
          <input v-model="customerForm.code" name="customer_code" autocomplete="off" spellcheck="false" placeholder="例如：666…" />
        </label>
        <label>
          <span>客戶名稱</span>
          <input v-model="customerForm.name" name="customer_name" autocomplete="off" placeholder="例如：666-hmg…" />
        </label>
        <button class="primary-btn" type="submit" :disabled="creatingCustomer">
          {{ creatingCustomer ? "新增中…" : "新增客戶" }}
        </button>
      </form>
    </section>

    <section class="content-grid">
      <article class="panel detail-panel">
        <div class="panel-head">
          <div>
            <h2>{{ tabTitleMap[activeTab] }}詳細資料</h2>
            <p>{{ selectedDetailLabel === "-" ? "新增資料" : selectedDetailLabel }}</p>
          </div>
          <UiStatusPill
            v-if="selectedStatusBadge"
            class="status-legend"
            :label="selectedStatusBadge.label"
            :tone="selectedStatusBadge.tone"
          />
          <div class="action-group">
            <button class="outline-btn small" type="button" :disabled="loading" @click="startCreate">新增</button>
            <button class="outline-btn small" type="button" :disabled="loading" @click="syncEditorFromSelection">重載</button>
          </div>
        </div>

        <form class="detail-form" @submit.prevent="saveCurrent">
          <template v-if="activeTab === 'fixture'">
            <label>
              <span>治具編號 *</span>
              <input v-model="fixtureForm.code" required />
              <small class="field-hint">可輸入中文、英文、數字與符號，前後空白會自動移除。</small>
            </label>
            <label><span>治具名稱 *</span><input v-model="fixtureForm.name" required /></label>
            <label><span>儲位</span><input v-model="fixtureForm.storage_location" placeholder="A-01-03" /></label>
            <label><span>最低庫存</span><input v-model.number="fixtureForm.min_stock_qty" type="number" min="0" /></label>
            <label class="full">
              <span>負責人</span>
              <select v-model="fixtureForm.owner_id">
                <option :value="null">未指定</option>
                <option v-for="owner in owners.filter((row) => row.is_active)" :key="owner.id" :value="owner.id">{{ owner.name }}</option>
              </select>
            </label>
            <label class="full">
              <span>狀態</span>
              <select v-model="fixtureForm.is_active" :disabled="selectedFixtureId !== null">
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

          <template v-else-if="activeTab === 'owner'">
            <label class="full"><span>負責人名稱 *</span><input v-model="ownerForm.name" required /></label>
            <label class="full">
              <span>狀態</span>
              <select v-model="ownerForm.is_active">
                <option :value="true">啟用中</option>
                <option :value="false">停用</option>
              </select>
            </label>
          </template>

          <template v-else-if="canManageUsers">
            <label><span>帳號 *</span><input v-model="userForm.username" :disabled="selectedUserId !== null" required /></label>
            <label><span>顯示名稱 *</span><input v-model="userForm.display_name" required /></label>
            <label><span>角色</span><select v-model="userForm.role"><option value="admin">Admin</option><option value="user">User</option></select></label>
            <label><span>狀態</span><select v-model="userForm.is_active"><option :value="true">啟用中</option><option :value="false">停用</option></select></label>
            <label v-if="selectedUserId === null" class="full"><span>登入密碼 *</span><input v-model="userForm.password" type="password" minlength="6" required /></label>
            <label class="full"><span>建立時間</span><input :value="selectedUser?.created_at ? new Date(selectedUser.created_at).toLocaleString('zh-TW') : '-'" disabled /></label>
            <label class="full"><span>更新時間</span><input :value="selectedUser?.updated_at ? new Date(selectedUser.updated_at).toLocaleString('zh-TW') : '-'" disabled /></label>
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
            :editing="selectedFixtureId !== null || selectedModelId !== null || selectedStationId !== null || selectedOwnerId !== null || selectedUserId !== null"
            :saving="loading"
            submit-label="儲存"
            saving-label="儲存中..."
            cancel-label="取消"
            delete-label="停用"
            :show-delete="true"
            :state-text="selectedDetailLabel === '-' ? '新增模式' : '編輯模式'"
            @cancel="startCreate"
            @delete="deactivateCurrent"
          />
        </form>
      </article>

      <article class="panel list-panel">
        <div class="panel-head">
          <div>
            <h2>{{ tabTitleMap[activeTab] }}清單</h2>
            <p>{{ currentRows.length }} 筆資料</p>
          </div>
        </div>

        <div class="list-toolbar">
          <input v-model="keyword" :placeholder="searchPlaceholder" :disabled="loading" />
          <select v-if="activeTab === 'fixture' || activeTab === 'user'" v-model="statusFilter">
            <option value="all">狀態：全部</option>
            <option value="active">狀態：啟用中</option>
            <option value="inactive">狀態：停用</option>
          </select>
          <button class="primary-btn" type="button" :disabled="loading" @click="startCreate">+ 新增{{ tabTitleMap[activeTab] }}</button>
        </div>

        <div v-if="loading" class="loading-banner">資料載入中，請稍候...</div>

        <div class="table-scroll">
          <table class="data-table">
            <thead>
              <tr v-if="activeTab === 'fixture'"><th>治具編號</th><th>治具名稱</th><th>儲位</th><th>狀態</th></tr>
              <tr v-else-if="activeTab === 'model'"><th>機種編號</th><th>機種名稱</th><th>狀態</th></tr>
              <tr v-else-if="activeTab === 'station'"><th>站點編號</th><th>站點名稱</th><th>狀態</th></tr>
              <tr v-else-if="activeTab === 'owner'"><th>負責人</th><th>狀態</th></tr>
              <tr v-else><th>帳號</th><th>顯示名稱</th><th>角色</th><th>狀態</th></tr>
            </thead>

            <tbody v-if="activeTab === 'fixture'">
              <tr v-for="row in pagedFixtureRows" :key="row.id" :class="{ selected: selectedFixtureId === row.id }" @click="selectRow(row.id)">
                <td>{{ row.code }}</td><td>{{ row.name }}</td><td>{{ row.storage_location || "-" }}</td><td><span class="status-pill" :class="row.is_active ? 'active' : 'inactive'">{{ row.is_active ? "啟用中" : "停用" }}</span></td>
              </tr>
              <tr v-if="!loading && currentRows.length === 0">
                <td colspan="4" class="empty-cell">{{ emptyStateMessage }}</td>
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
            <tbody v-else-if="activeTab === 'owner'">
              <tr v-for="row in pagedOwnerRows" :key="row.id" :class="{ selected: selectedOwnerId === row.id }" @click="selectRow(row.id)">
                <td>{{ row.name }}</td><td><span class="status-pill" :class="row.is_active ? 'active' : 'inactive'">{{ row.is_active ? "啟用中" : "停用" }}</span></td>
              </tr>
              <tr v-if="!loading && currentRows.length === 0">
                <td colspan="2" class="empty-cell">{{ emptyStateMessage }}</td>
              </tr>
            </tbody>
            <tbody v-else>
              <tr v-for="row in pagedUserRows" :key="row.id" :class="{ selected: selectedUserId === row.id }" @click="selectRow(row.id)">
                <td>{{ row.username }}</td><td>{{ row.display_name }}</td><td>{{ row.role }}</td><td><span class="status-pill" :class="row.is_active ? 'active' : 'inactive'">{{ row.is_active ? "啟用中" : "停用" }}</span></td>
              </tr>
              <tr v-if="!loading && currentRows.length === 0">
                <td colspan="4" class="empty-cell">{{ emptyStateMessage }}</td>
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.tab-bar {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
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

.toolbar-actions,
.action-group {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.customer-admin {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--line);
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr)) auto;
  gap: 8px;
  align-items: end;
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
  grid-template-columns: 0.92fr 1.08fr;
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
    flex-direction: column;
    align-items: stretch;
  }

  .list-toolbar,
  .detail-form {
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

