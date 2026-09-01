<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";

import { api } from "@/api";
import { authSession, selectedCustomerId } from "@/appState";
import UiMultiSelect from "@/components/common/UiMultiSelect.vue";
import { pushToast } from "@/toastState";
import FormUserCustomerScopePicker from "@/components/home/FormUserCustomerScopePicker.vue";
import type {
  AppUser,
  Customer,
  Fixture,
  MachineModel,
  Station,
} from "@/types";
import { completeBlobExport } from "@/utils/exportFeedback";
import { formOperationError } from "@/utils/formOperations";
import { scrollReportResultsIntoView } from "@/utils/scrollReportResults";
import { uiSurfaceRouteQuery } from "@/utils/uiSurface";
import { canManageAccounts } from "@/utils/roles";
import { setUnsavedChangesGuard } from "@/unsavedChangesGuard";
import type { FormMasterView } from "@/components/home/FormReportOperations.vue";

const props = defineProps<{
  requestedView?: FormMasterView;
  workbenchLayout?: boolean;
}>();
const emit = defineEmits<{ viewChange: [view: FormMasterView] }>();
const router = useRouter();

const loading = ref(false);
const saving = ref(false);
const exporting = ref(false);
const keyword = ref("");
const resultsSection = ref<HTMLElement | null>(null);
const fixtures = ref<Fixture[]>([]);
const models = ref<MachineModel[]>([]);
const stations = ref<Station[]>([]);
const customerRows = ref<Customer[]>([]);
const userCustomerOptions = ref<Customer[]>([]);
const users = ref<AppUser[]>([]);
const view = ref<FormMasterView>(props.requestedView ?? "fixture");
const status = ref<Array<"active" | "inactive">>([]);
const statusApiValue = computed<"all" | "active" | "inactive">(() =>
  status.value.length === 1 ? status.value[0] : "all",
);
const adding = ref(false);
const editingId = ref<number | null>(null);
const fixtureDraft = reactive({
  code: "",
  name: "",
  line_storage_location: "",
  department_storage_location: "",
  min_stock_qty: 0,
  is_active: true,
});
const simpleDraft = reactive({ code: "", name: "", is_active: true });
const userDraft = reactive({
  username: "",
  email: "",
  display_name: "",
  role: "user",
  password: "",
  is_active: true,
  allowed_customer_ids: [] as number[],
});
const pageNumber = ref(1);
const pageSize = ref<50 | 100>(50);
const total = ref(0);
const userCustomerOptionsLoading = ref(false);
let userCustomerOptionTimer: number | undefined;
let userCustomerOptionRequestId = 0;

const canManageAdminRows = computed(() => canManageAccounts(authSession.value?.role));
const customerMap = computed(
  () => new Map(userCustomerOptions.value.map((row) => [row.id, row])),
);
const normalizedKeyword = computed(() => keyword.value.trim().toLowerCase());
const rows = computed<
  Array<Fixture | MachineModel | Station | Customer | AppUser>
>(() => {
  const source =
    view.value === "fixture"
      ? fixtures.value
      : view.value === "model"
        ? models.value
        : view.value === "station"
          ? stations.value
          : view.value === "customer"
            ? customerRows.value
            : users.value;
  if (["fixture", "model", "station"].includes(view.value)) return source;
  return source.filter((row) => {
    const active = "is_active" in row ? row.is_active : true;
    if (
      status.value.length &&
      !status.value.includes(active ? "active" : "inactive")
    )
      return false;
    if (!normalizedKeyword.value) return true;
    const searchable =
      "username" in row
        ? `${row.username} ${row.display_name} ${row.email ?? ""}`
        : `${row.code} ${row.name}`;
    return searchable.toLowerCase().includes(normalizedKeyword.value);
  });
});
const hasUnsavedRow = computed(() => adding.value || editingId.value !== null);
const totalPages = computed(() =>
  Math.max(1, Math.ceil(total.value / pageSize.value)),
);

async function load(): Promise<void> {
  const customerId = selectedCustomerId.value;
  loading.value = true;
  try {
    if (!canManageAdminRows.value && ["customer", "user"].includes(view.value))
      view.value = "fixture";
    fixtures.value = [];
    models.value = [];
    stations.value = [];
    customerRows.value = [];
    userCustomerOptions.value = [];
    users.value = [];
    if (view.value === "fixture" && customerId) {
      const result = await api.listFixturesPage(
        customerId,
        pageNumber.value,
        pageSize.value,
        keyword.value.trim(),
        statusApiValue.value,
      );
      fixtures.value = result.items;
      total.value = result.total;
    } else if (view.value === "model" && customerId) {
      const result = await api.listModelsPage(
        customerId,
        pageNumber.value,
        pageSize.value,
        keyword.value.trim(),
        statusApiValue.value,
      );
      models.value = result.items;
      total.value = result.total;
    } else if (view.value === "station" && customerId) {
      const result = await api.listStationsPage(
        customerId,
        pageNumber.value,
        pageSize.value,
        keyword.value.trim(),
        statusApiValue.value,
      );
      stations.value = result.items;
      total.value = result.total;
    } else if (view.value === "customer" && canManageAdminRows.value) {
      const result = await api.listCustomersPage(
        pageNumber.value,
        pageSize.value,
        keyword.value.trim(),
      );
      customerRows.value = result.items;
      total.value = result.total;
    } else if (view.value === "user" && canManageAdminRows.value) {
      const result = await api.listUsersPage(
        pageNumber.value,
        pageSize.value,
        keyword.value.trim(),
        statusApiValue.value,
      );
      users.value = result.items;
      total.value = result.total;
    } else {
      total.value = 0;
    }
  } catch (error) {
    pushToast(formOperationError(error, "載入資料維護清單失敗"), "error");
  } finally {
    loading.value = false;
  }
}

function resetDraft(): void {
  window.clearTimeout(userCustomerOptionTimer);
  userCustomerOptionRequestId += 1;
  userCustomerOptionsLoading.value = false;
  adding.value = false;
  editingId.value = null;
  Object.assign(fixtureDraft, {
    code: "",
    name: "",
    line_storage_location: "",
    department_storage_location: "",
    min_stock_qty: 0,
    is_active: true,
  });
  Object.assign(simpleDraft, { code: "", name: "", is_active: true });
  Object.assign(userDraft, {
    username: "",
    email: "",
    display_name: "",
    role: "user",
    password: "",
    is_active: true,
    allowed_customer_ids: selectedCustomerId.value
      ? [selectedCustomerId.value]
      : [],
  });
}

function startAdd(): void {
  resetDraft();
  adding.value = true;
  if (view.value === "user") void loadUserCustomerOptions("");
}

function editRow(
  row: Fixture | MachineModel | Station | Customer | AppUser,
): void {
  if ("username" in row) {
    openFullMaintenance(row);
    return;
  }
  resetDraft();
  editingId.value = row.id;
  if ("min_stock_qty" in row) {
    Object.assign(fixtureDraft, {
      code: row.code,
      name: row.name,
      line_storage_location: row.line_storage_location ?? "",
      department_storage_location: row.department_storage_location ?? "",
      min_stock_qty: row.min_stock_qty,
      is_active: row.is_active,
    });
  } else {
    Object.assign(simpleDraft, {
      code: row.code,
      name: row.name,
      is_active: "is_active" in row ? row.is_active : true,
    });
  }
}

function openFullMaintenance(
  row?: Fixture | MachineModel | Station | Customer | AppUser,
): void {
  const paths: Record<FormMasterView, string> = {
    fixture: "/master/fixtures",
    model: "/master/models",
    station: "/master/stations",
    customer: "/master/customers",
    user: "/master/users",
  };
  const entityKeys: Record<FormMasterView, string> = {
    fixture: "fixture_id",
    model: "model_id",
    station: "station_id",
    customer: "customer_id",
    user: "user_id",
  };
  void router.push({
    path: paths[view.value],
    query: {
      ...uiSurfaceRouteQuery("modern"),
      ...(row
        ? {
            [entityKeys[view.value]]: String(row.id),
            keyword: "username" in row ? row.username : row.code,
            edit: "1"
          }
        : {}),
    },
  });
}

function userCustomerLabel(row: AppUser): string {
  if (row.allowed_customer_ids.length === 0) return "未授權";
  const summaryMap = new Map(
    (row.allowed_customers ?? []).map((customer) => [customer.id, customer]),
  );
  return row.allowed_customer_ids
    .map((customerId) => {
      const customer =
        summaryMap.get(customerId) ?? customerMap.value.get(customerId);
      return customer
        ? `${customer.code}－${customer.name}`
        : `客戶 #${customerId}`;
    })
    .join("、");
}

async function loadUserCustomerOptions(value: string): Promise<void> {
  const requestId = ++userCustomerOptionRequestId;
  userCustomerOptionsLoading.value = true;
  try {
    const result = await api.listCustomersPage(1, 50, value.trim());
    if (requestId !== userCustomerOptionRequestId) return;
    const selectedIds = new Set(userDraft.allowed_customer_ids);
    const selectedRows = userCustomerOptions.value.filter((customer) =>
      selectedIds.has(customer.id),
    );
    userCustomerOptions.value = [
      ...new Map(
        [...selectedRows, ...result.items].map((customer) => [
          customer.id,
          customer,
        ]),
      ).values(),
    ];
  } catch (error) {
    if (requestId === userCustomerOptionRequestId)
      pushToast(formOperationError(error, "搜尋客戶選項失敗"), "error");
  } finally {
    if (requestId === userCustomerOptionRequestId)
      userCustomerOptionsLoading.value = false;
  }
}

function searchUserCustomerOptions(value: string): void {
  window.clearTimeout(userCustomerOptionTimer);
  userCustomerOptionTimer = window.setTimeout(
    () => void loadUserCustomerOptions(value),
    250,
  );
}

async function saveRow(): Promise<void> {
  const customerId = selectedCustomerId.value;
  if (!customerId && !["customer", "user"].includes(view.value)) {
    pushToast("請先選擇客戶。", "warning");
    return;
  }
  if (view.value === "user" && userDraft.allowed_customer_ids.length === 0) {
    pushToast("請至少選擇一個可存取客戶。", "warning");
    return;
  }
  saving.value = true;
  try {
    if (view.value === "fixture") {
      const payload = {
        customer_id: customerId as number,
        code: fixtureDraft.code.trim(),
        name: fixtureDraft.name.trim(),
        line_storage_location:
          fixtureDraft.line_storage_location.trim() || null,
        department_storage_location:
          fixtureDraft.department_storage_location.trim() || null,
        min_stock_qty: Math.max(0, fixtureDraft.min_stock_qty),
      };
      if (editingId.value)
        await api.updateFixture(editingId.value, {
          ...payload,
          description: "",
          is_active: fixtureDraft.is_active,
        });
      else await api.createFixture(payload);
    } else if (view.value === "model") {
      const payload = {
        customer_id: customerId as number,
        code: simpleDraft.code.trim(),
        name: simpleDraft.name.trim(),
      };
      if (editingId.value)
        await api.updateModel(editingId.value, {
          ...payload,
          is_active: simpleDraft.is_active,
        });
      else await api.createModel(payload);
    } else if (view.value === "station") {
      const payload = {
        customer_id: customerId as number,
        code: simpleDraft.code.trim(),
        name: simpleDraft.name.trim(),
      };
      if (editingId.value)
        await api.updateStation(editingId.value, {
          ...payload,
          is_active: simpleDraft.is_active,
        });
      else await api.createStation(payload);
    } else if (view.value === "customer") {
      const existing = customerRows.value.find(
        (row) => row.id === editingId.value,
      );
      const payload = {
        code: simpleDraft.code.trim(),
        name: simpleDraft.name.trim(),
        assigned_user_ids: existing?.assigned_user_ids ?? [],
      };
      if (editingId.value) await api.updateCustomer(editingId.value, payload);
      else await api.createCustomer(payload);
    } else if (editingId.value) {
      await api.updateUser(editingId.value, {
        email: userDraft.email.trim() || null,
        display_name: userDraft.display_name.trim(),
        role: userDraft.role,
        is_active: userDraft.is_active,
        allowed_customer_ids: userDraft.allowed_customer_ids,
      });
    } else {
      await api.createUser({
        username: userDraft.username.trim(),
        email: userDraft.email.trim() || null,
        password: userDraft.password,
        display_name: userDraft.display_name.trim(),
        role: userDraft.role,
        is_active: userDraft.is_active,
        allowed_customer_ids: userDraft.allowed_customer_ids,
      });
    }
    pushToast(editingId.value ? "資料已更新。" : "資料已新增。", "success");
    resetDraft();
    await load();
  } catch (error) {
    pushToast(formOperationError(error, "儲存資料失敗"), "error");
  } finally {
    saving.value = false;
  }
}

async function exportResults(): Promise<void> {
  const customerId = selectedCustomerId.value;
  if (!["customer", "user"].includes(view.value) && !customerId) {
    pushToast("請先選擇客戶。", "warning");
    return;
  }
  if (exporting.value) return;
  if (total.value === 0) {
    pushToast("目前沒有可匯出的資料。", "warning");
    return;
  }
  exporting.value = true;
  try {
    const response =
      view.value === "user"
        ? await api.exportFormUsersCsv(
            keyword.value.trim(),
            statusApiValue.value,
          )
        : await api.exportFormMasterCsv({
            entity: view.value,
            customerId:
              view.value === "customer" ? undefined : (customerId ?? undefined),
            keyword: keyword.value.trim(),
            statusFilter: statusApiValue.value,
          });
    const filename =
      view.value === "fixture"
        ? "form-fixtures-filtered.csv"
        : view.value === "user"
          ? "form-users-filtered.csv"
          : `form-${view.value}-filtered.csv`;
    completeBlobExport(response, filename, total.value);
  } catch (error) {
    pushToast(formOperationError(error, "匯出篩選結果失敗"), "error");
  } finally {
    exporting.value = false;
  }
}

async function applyFilters(): Promise<void> {
  pageNumber.value = 1;
  await load();
  await nextTick();
  scrollReportResultsIntoView(resultsSection.value);
}

function changeView(): void {
  emit("viewChange", view.value);
}

watch(
  selectedCustomerId,
  () => {
    pageNumber.value = 1;
    resetDraft();
    void load();
  },
  { immediate: true },
);
watch(
  () => props.requestedView,
  (requestedView) => {
    if (requestedView) view.value = requestedView;
  },
);
watch(view, () => {
  pageNumber.value = 1;
  resetDraft();
  void load();
});
watch(
  hasUnsavedRow,
  (value) => {
    setUnsavedChangesGuard(
      "form-master-grid",
      value,
      "資料維護表格內有尚未儲存的輸入列",
    );
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  window.clearTimeout(userCustomerOptionTimer);
  userCustomerOptionRequestId += 1;
  setUnsavedChangesGuard(
    "form-master-grid",
    false,
    "資料維護表格內有尚未儲存的輸入列",
  );
});
</script>

<template>
  <div
    class="report-workspace form-operation-workspace"
    data-form-operation-domain="master"
  >
    <div class="report-main-column">
      <Teleport defer to="#workbench-management-tools" :disabled="!workbenchLayout">
      <section
        class="filter-panel workbench-side-section"
        data-tour="form-operation-filters"
        aria-label="資料維護條件"
      >
        <div class="filter-panel-title">
          <div>
            <strong>篩選條件</strong
            ><span>資料維護｜依目前功能顯示適用欄位</span>
          </div>
          <div class="filter-panel-title-actions">
            <button
              class="text-button"
              type="button"
              :disabled="loading"
              @click="load"
            >
              重新整理</button
            ><button
              class="primary-btn btn-sm"
              type="button"
              :disabled="loading"
              @click="applyFilters"
            >
              套用條件
            </button>
          </div>
        </div>
        <div class="filter-grid form-operation-filters compact">
          <label data-tour="form-master-view-selector"
            ><span>資料表</span
            ><select v-model="view" @change="changeView">
              <option value="fixture">治具</option>
              <option value="model">機種</option>
              <option value="station">站點</option>
              <option v-if="canManageAdminRows" value="customer">客戶</option>
              <option v-if="canManageAdminRows" value="user">使用者</option>
            </select></label
          >
          <UiMultiSelect
            v-model="status"
            label="狀態"
            placeholder="全部狀態"
            :options="[
              { value: 'active', label: '啟用' },
              { value: 'inactive', label: '停用' },
            ]"
          />
          <label class="wide"
            ><span>關鍵字</span
            ><input
              v-model="keyword"
              :placeholder="
                view === 'user' ? '帳號、姓名或 Email' : '編號或名稱'
              "
          /></label>
        </div>
      </section>
      </Teleport>

      <Teleport v-if="workbenchLayout && hasUnsavedRow" defer to="#workbench-management-tools">
        <section class="workbench-side-section workbench-side-editor" aria-label="資料維護編輯欄位">
          <header class="workbench-side-section-heading">
            <div><span>EDIT</span><strong>{{ editingId ? "編輯" : "新增" }}{{ view === "fixture" ? "治具" : view === "model" ? "機種" : view === "station" ? "站點" : "客戶" }}</strong></div>
            <button class="text-button" type="button" @click="resetDraft">取消</button>
          </header>
          <div v-if="view === 'fixture'" class="workbench-side-form">
            <label><span>治具編號</span><input v-model="fixtureDraft.code" /></label>
            <label><span>治具名稱</span><input v-model="fixtureDraft.name" /></label>
            <label><span>產線儲位</span><input v-model="fixtureDraft.line_storage_location" /></label>
            <label><span>部門儲位</span><input v-model="fixtureDraft.department_storage_location" /></label>
            <label><span>最低水位</span><input v-model.number="fixtureDraft.min_stock_qty" type="number" min="0" /></label>
            <label><span>狀態</span><select v-model="fixtureDraft.is_active"><option :value="true">啟用</option><option :value="false">停用</option></select></label>
          </div>
          <div v-else class="workbench-side-form">
            <label><span>編號</span><input v-model="simpleDraft.code" /></label>
            <label><span>名稱</span><input v-model="simpleDraft.name" /></label>
            <label v-if="view !== 'customer'"><span>狀態</span><select v-model="simpleDraft.is_active"><option :value="true">啟用</option><option :value="false">停用</option></select></label>
          </div>
          <div class="workbench-side-actions"><button class="primary-btn" type="button" :disabled="saving" @click="saveRow">{{ saving ? "儲存中…" : "儲存變更" }}</button></div>
        </section>
      </Teleport>

      <slot name="between-filter-and-results" />

      <section
        ref="resultsSection"
        class="report-section"
        data-tour="form-operation-results"
        aria-label="資料維護結果表格"
      >
        <div class="report-toolbar">
          <div class="report-summary">
            <strong>{{ total }}</strong
            ><span>筆資料</span
            ><span v-if="hasUnsavedRow" class="form-draft-note"
              >表格內有未儲存列</span
            >
          </div>
          <div
            class="form-operation-toolbar-actions"
            data-tour="form-master-toolbar"
          >
            <button
              class="outline-btn"
              type="button"
              :disabled="exporting"
              @click="exportResults"
            >
              {{ exporting ? "匯出中..." : "匯出篩選結果" }}</button
            ><button
              class="outline-btn"
              data-tour="form-master-open-full"
              type="button"
              @click="openFullMaintenance()"
            >
              前往完整維護</button
            ><button
              v-if="view !== 'user'"
              class="primary-btn"
              data-tour="form-master-add-row"
              type="button"
              :disabled="saving || adding"
              @click="startAdd"
            >
              ＋ 新增一列</button
            ><label class="page-size-inline"
              >每頁<select
                v-model="pageSize"
                @change="
                  pageNumber = 1;
                  load();
                "
              >
                <option :value="50">50</option>
                <option :value="100">100</option>
              </select></label
            >
          </div>
        </div>
        <div class="form-report-grid-wrap">
          <table
            class="form-report-grid editable-grid"
            :data-tour="`form-master-${view}-table`"
          >
            <thead>
              <tr v-if="view === 'fixture'">
                <th>治具編號</th>
                <th>治具名稱</th>
                <th>產線儲位</th>
                <th>部門儲位</th>
                <th>最低水位</th>
                <th>狀態</th>
                <th>操作</th>
              </tr>
              <tr v-else-if="view === 'user'">
                <th>帳號</th>
                <th>顯示名稱</th>
                <th>Email</th>
                <th>角色</th>
                <th>可存取客戶</th>
                <th>狀態</th>
                <th>操作</th>
              </tr>
              <tr v-else>
                <th>編號</th>
                <th>名稱</th>
                <th>狀態</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="adding && !workbenchLayout" class="editing-row">
                <template v-if="view === 'fixture'"
                  ><td><input v-model="fixtureDraft.code" /></td>
                  <td><input v-model="fixtureDraft.name" /></td>
                  <td>
                    <input v-model="fixtureDraft.line_storage_location" />
                  </td>
                  <td>
                    <input v-model="fixtureDraft.department_storage_location" />
                  </td>
                  <td>
                    <input
                      v-model.number="fixtureDraft.min_stock_qty"
                      type="number"
                      min="0"
                    />
                  </td>
                  <td>
                    <select v-model="fixtureDraft.is_active">
                      <option :value="true">啟用</option>
                      <option :value="false">停用</option>
                    </select>
                  </td>
                  <td>
                    <button
                      class="primary-btn btn-sm"
                      type="button"
                      @click="saveRow"
                    >
                      儲存</button
                    ><button
                      class="outline-btn btn-sm"
                      type="button"
                      @click="resetDraft"
                    >
                      取消
                    </button>
                  </td></template
                >
                <template v-else-if="view === 'user'"
                  ><td><input v-model="userDraft.username" /></td>
                  <td><input v-model="userDraft.display_name" /></td>
                  <td><input v-model="userDraft.email" /></td>
                  <td>
                    <select v-model="userDraft.role">
                      <option value="user">user</option>
                      <option value="super_admin">super_admin</option>
                      <option value="admin">admin</option>
                      <option value="guest">guest</option></select
                    ><input
                      v-model="userDraft.password"
                      type="password"
                      placeholder="初始密碼"
                    />
                  </td>
                  <td class="customer-scope-cell">
                    <FormUserCustomerScopePicker
                      v-model="userDraft.allowed_customer_ids"
                      :customers="userCustomerOptions"
                      :loading="userCustomerOptionsLoading"
                      @search="searchUserCustomerOptions"
                    />
                  </td>
                  <td>
                    <select v-model="userDraft.is_active">
                      <option :value="true">啟用</option>
                      <option :value="false">停用</option>
                    </select>
                  </td>
                  <td>
                    <button
                      class="primary-btn btn-sm"
                      type="button"
                      @click="saveRow"
                    >
                      儲存</button
                    ><button
                      class="outline-btn btn-sm"
                      type="button"
                      @click="resetDraft"
                    >
                      取消
                    </button>
                  </td></template
                >
                <template v-else
                  ><td><input v-model="simpleDraft.code" /></td>
                  <td><input v-model="simpleDraft.name" /></td>
                  <td>
                    <select
                      v-if="view !== 'customer'"
                      v-model="simpleDraft.is_active"
                    >
                      <option :value="true">啟用</option>
                      <option :value="false">停用</option></select
                    ><span v-else>新增</span>
                  </td>
                  <td>
                    <button
                      class="primary-btn btn-sm"
                      type="button"
                      @click="saveRow"
                    >
                      儲存</button
                    ><button
                      class="outline-btn btn-sm"
                      type="button"
                      @click="resetDraft"
                    >
                      取消
                    </button>
                  </td></template
                >
              </tr>
              <tr
                v-for="row in rows"
                :key="row.id"
                :class="{ 'editing-row': editingId === row.id }"
              >
                <template v-if="editingId === row.id && view === 'fixture' && !workbenchLayout"
                  ><td><input v-model="fixtureDraft.code" /></td>
                  <td><input v-model="fixtureDraft.name" /></td>
                  <td>
                    <input v-model="fixtureDraft.line_storage_location" />
                  </td>
                  <td>
                    <input v-model="fixtureDraft.department_storage_location" />
                  </td>
                  <td>
                    <input
                      v-model.number="fixtureDraft.min_stock_qty"
                      type="number"
                      min="0"
                    />
                  </td>
                  <td>
                    <select v-model="fixtureDraft.is_active">
                      <option :value="true">啟用</option>
                      <option :value="false">停用</option>
                    </select>
                  </td>
                  <td>
                    <button
                      class="primary-btn btn-sm"
                      type="button"
                      @click="saveRow"
                    >
                      儲存</button
                    ><button
                      class="outline-btn btn-sm"
                      type="button"
                      @click="resetDraft"
                    >
                      取消
                    </button>
                  </td></template
                >
                <template v-else-if="editingId === row.id && view === 'user' && !workbenchLayout"
                  ><td>{{ userDraft.username }}</td>
                  <td><input v-model="userDraft.display_name" /></td>
                  <td><input v-model="userDraft.email" /></td>
                  <td>
                    <select v-model="userDraft.role">
                      <option value="user">user</option>
                      <option value="super_admin">super_admin</option>
                      <option value="admin">admin</option>
                      <option value="guest">guest</option>
                    </select>
                  </td>
                  <td class="customer-scope-cell">
                    <FormUserCustomerScopePicker
                      v-model="userDraft.allowed_customer_ids"
                      :customers="userCustomerOptions"
                      :loading="userCustomerOptionsLoading"
                      @search="searchUserCustomerOptions"
                    />
                  </td>
                  <td>
                    <select v-model="userDraft.is_active">
                      <option :value="true">啟用</option>
                      <option :value="false">停用</option>
                    </select>
                  </td>
                  <td>
                    <button
                      class="primary-btn btn-sm"
                      type="button"
                      @click="saveRow"
                    >
                      儲存</button
                    ><button
                      class="outline-btn btn-sm"
                      type="button"
                      @click="resetDraft"
                    >
                      取消
                    </button>
                  </td></template
                >
                <template v-else-if="editingId === row.id && !workbenchLayout"
                  ><td><input v-model="simpleDraft.code" /></td>
                  <td><input v-model="simpleDraft.name" /></td>
                  <td>
                    <select
                      v-if="view !== 'customer'"
                      v-model="simpleDraft.is_active"
                    >
                      <option :value="true">啟用</option>
                      <option :value="false">停用</option></select
                    ><span v-else>編輯中</span>
                  </td>
                  <td>
                    <button
                      class="primary-btn btn-sm"
                      type="button"
                      @click="saveRow"
                    >
                      儲存</button
                    ><button
                      class="outline-btn btn-sm"
                      type="button"
                      @click="resetDraft"
                    >
                      取消
                    </button>
                  </td></template
                >
                <template v-else-if="view === 'fixture'"
                  ><td>{{ (row as Fixture).code }}</td>
                  <td>{{ (row as Fixture).name }}</td>
                  <td>{{ (row as Fixture).line_storage_location || "-" }}</td>
                  <td>
                    {{ (row as Fixture).department_storage_location || "-" }}
                  </td>
                  <td>{{ (row as Fixture).min_stock_qty }}</td>
                  <td>
                    <span
                      class="status-pill"
                      :class="(row as Fixture).is_active ? 'normal' : 'muted'"
                      >{{ (row as Fixture).is_active ? "啟用" : "停用" }}</span
                    >
                  </td>
                  <td>
                    <button
                      class="text-button"
                      type="button"
                      @click="editRow(row)"
                    >
                      編輯</button
                    ><button
                      class="text-button"
                      type="button"
                      @click="openFullMaintenance(row)"
                    >
                      完整維護
                    </button>
                  </td></template
                >
                <template v-else-if="view === 'user'"
                  ><td>{{ (row as AppUser).username }}</td>
                  <td>{{ (row as AppUser).display_name }}</td>
                  <td>{{ (row as AppUser).email || "-" }}</td>
                  <td>{{ (row as AppUser).role }}</td>
                  <td class="authorized-customers">
                    {{ userCustomerLabel(row as AppUser) }}
                  </td>
                  <td>
                    <span
                      class="status-pill"
                      :class="(row as AppUser).is_active ? 'normal' : 'muted'"
                      >{{ (row as AppUser).is_active ? "啟用" : "停用" }}</span
                    >
                  </td>
                  <td>
                    <button
                      class="text-button"
                      type="button"
                      @click="openFullMaintenance(row)"
                    >
                      完整維護
                    </button>
                  </td></template
                >
                <template v-else
                  ><td>
                    {{ (row as MachineModel | Station | Customer).code }}
                  </td>
                  <td>{{ (row as MachineModel | Station | Customer).name }}</td>
                  <td>
                    <span
                      v-if="'is_active' in row"
                      class="status-pill"
                      :class="row.is_active ? 'normal' : 'muted'"
                      >{{ row.is_active ? "啟用" : "停用" }}</span
                    ><span v-else>—</span>
                  </td>
                  <td>
                    <button
                      class="text-button"
                      type="button"
                      @click="editRow(row)"
                    >
                      編輯</button
                    ><button
                      class="text-button"
                      type="button"
                      @click="openFullMaintenance(row)"
                    >
                      完整維護
                    </button>
                  </td></template
                >
              </tr>
              <tr v-if="!loading && rows.length === 0">
                <td
                  :colspan="view === 'fixture' || view === 'user' ? 7 : 4"
                  class="empty-cell"
                >
                  查無資料
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="form-grid-pager">
          <button
            class="outline-btn btn-sm"
            type="button"
            :disabled="pageNumber <= 1 || loading"
            @click="
              pageNumber -= 1;
              load();
            "
          >
            上一頁</button
          ><span>第 {{ pageNumber }} / {{ totalPages }} 頁</span
          ><button
            class="outline-btn btn-sm"
            type="button"
            :disabled="pageNumber >= totalPages || loading"
            @click="
              pageNumber += 1;
              load();
            "
          >
            下一頁
          </button>
        </div>
      </section>
    </div>
  </div>
</template>
