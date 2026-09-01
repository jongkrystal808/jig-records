<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { authSession, customers, selectedCustomerId } from "@/appState";
import WorkbenchAdminOperations, { type WorkbenchAdminMode } from "@/components/home/WorkbenchAdminOperations.vue";
import FormImageMaintenance from "@/components/home/FormImageMaintenance.vue";
import FormReportOperations, {
  type FormMasterView,
  type FormProductionView
} from "@/components/home/FormReportOperations.vue";
import { uiSurfaceRouteQuery } from "@/utils/uiSurface";
import { canManageAccounts, canManageAdminReports, roleLabel } from "@/utils/roles";

type ManagementModule = "transactions" | "production" | "master" | WorkbenchAdminMode;
type WorkbenchMasterView = FormMasterView | "image";

const props = withDefaults(defineProps<{
  surface?: "workbench" | "workspace";
  showHeader?: boolean;
  transactionsOnly?: boolean;
}>(), {
  surface: "workbench",
  showHeader: true,
  transactionsOnly: false
});

const emit = defineEmits<{
  "update:selectedCustomerId": [value: number | null];
}>();

const route = useRoute();
const router = useRouter();
const filtersCollapsed = ref(false);
const isFloorOverview = computed(() => props.surface === "workspace" && props.transactionsOnly);

const module = computed<ManagementModule>(() => {
  if (route.path === "/master/ledger") return "ledger";
  if (route.path === "/master/quality") return "quality";
  if (route.path.startsWith("/production")) return "production";
  if (route.path.startsWith("/master")) return "master";
  return "transactions";
});
const productionView = computed<FormProductionView>(() =>
  route.path === "/production/mapping" ? "mappings" : "requirements"
);
const masterView = computed<WorkbenchMasterView>(() => {
  if (route.path === "/master/images") return "image";
  if (route.path === "/master/models") return "model";
  if (route.path === "/master/stations") return "station";
  if (route.path === "/master/customers") return "customer";
  if (route.path === "/master/users") return "user";
  return "fixture";
});
const reportMasterView = computed<FormMasterView>(() =>
  masterView.value === "image" ? "fixture" : masterView.value
);
const canUseProtectedManagement = computed(() => authSession.value?.role !== "guest");
const canManageReports = computed(() => canManageAdminReports(authSession.value?.role));
const canManageAccountRows = computed(() => canManageAccounts(authSession.value?.role));
const currentCustomer = computed(() => customers.value.find((row) => row.id === selectedCustomerId.value) ?? null);
const currentUserName = computed(
  () => authSession.value?.user?.display_name || authSession.value?.display_name || "訪客"
);
const currentRoleLabel = computed(() => {
  return roleLabel(authSession.value?.role);
});
const moduleLabel = computed(() => ({
  transactions: "收退料總檢視",
  production: "產能設定",
  master: "資料維護",
  ledger: "收退料帳目管理",
  quality: "治具資料品質"
})[module.value]);
const moduleEyebrow = computed(() => ({
  transactions: "庫存作業",
  production: "生產配置",
  master: "系統資料",
  ledger: "帳目稽核",
  quality: "資料治理"
})[module.value]);
const toolPanelLabel = computed(() => ({
  transactions: "篩選條件",
  production: "篩選與編輯",
  master: masterView.value === "image" ? "圖片維護" : "篩選與編輯",
  ledger: "帳目篩選",
  quality: "篩選與修正"
})[module.value]);

const primaryModules = computed(() => {
  const transactionModule = { key: "transactions" as const, index: "01", label: "收退料總檢視", path: "/inventory/overview" };
  if (props.transactionsOnly) return [transactionModule];
  return [
  transactionModule,
  ...(canUseProtectedManagement.value
    ? [
        { key: "production" as const, index: "02", label: "產能設定", path: "/production/requirements" },
        { key: "master" as const, index: "03", label: "資料維護", path: "/master/fixtures" }
      ]
    : []),
  ...(canManageReports.value
    ? [
        { key: "ledger" as const, index: "04", label: "收退料帳目管理", path: "/master/ledger" },
        { key: "quality" as const, index: "05", label: "治具資料品質", path: "/master/quality" }
      ]
    : [])
  ];
});
const floorModes = [
  { key: "transaction" as const, label: "收料／退料", path: "/inventory" },
  { key: "fixture" as const, label: "查詢治具", path: "/search" },
  { key: "model" as const, label: "查詢機種", path: "/search" },
  { key: "overview" as const, label: "收／退料總檢視", path: "/inventory/overview" }
];
const productionItems = [
  { key: "requirements" as const, label: "治具需求", path: "/production/requirements" },
  { key: "mappings" as const, label: "機種站點", path: "/production/mapping" }
];
const masterItems = computed(() => [
  { key: "fixture" as const, label: "治具", path: "/master/fixtures" },
  { key: "model" as const, label: "機種", path: "/master/models" },
  { key: "station" as const, label: "站點", path: "/master/stations" },
  { key: "image" as const, label: "圖片", path: "/master/images" },
  ...(canManageAccountRows.value
    ? [
        { key: "customer" as const, label: "客戶", path: "/master/customers" },
        { key: "user" as const, label: "使用者", path: "/master/users" }
      ]
    : [])
]);

function navigate(path: string): void {
  if (path === route.path) return;
  void router.push({
    path,
    query: {
      ...uiSurfaceRouteQuery(props.surface),
      ...(selectedCustomerId.value ? { customer: String(selectedCustomerId.value) } : {})
    }
  });
}

function navigateFloorMode(item: (typeof floorModes)[number]): void {
  if (item.key === "overview") return;
  void router.push({
    path: item.path,
    query: {
      ...uiSurfaceRouteQuery("workspace"),
      ...(selectedCustomerId.value ? { customer: String(selectedCustomerId.value) } : {}),
      workbench_mode: item.key
    }
  });
}

function openProductionView(view: FormProductionView): void {
  navigate(view === "mappings" ? "/production/mapping" : "/production/requirements");
}

function openMasterView(view: FormMasterView): void {
  const paths: Record<FormMasterView, string> = {
    fixture: "/master/fixtures",
    model: "/master/models",
    station: "/master/stations",
    customer: "/master/customers",
    user: "/master/users"
  };
  navigate(paths[view]);
}

function handleAdminNavigate(workspace: "ledger" | "production" | "master" | "image"): void {
  if (workspace === "ledger") navigate("/master/ledger");
  else if (workspace === "production") navigate("/production/requirements");
  else if (workspace === "image") navigate("/master/images");
  else navigate("/master/fixtures");
}

function handleCustomerChange(event: Event): void {
  const value = Number.parseInt((event.target as HTMLSelectElement).value, 10);
  emit("update:selectedCustomerId", Number.isFinite(value) ? value : null);
}

function returnToWorkbench(): void {
  void router.push({
    path: "/search",
    query: {
      ...uiSurfaceRouteQuery(props.surface),
      ...(selectedCustomerId.value ? { customer: String(selectedCustomerId.value) } : {}),
      workbench_mode: "fixture"
    }
  });
}

watch(selectedCustomerId, (customerId) => {
  const requestedCustomer = customerId ? String(customerId) : undefined;
  if (route.query.customer === requestedCustomer) return;
  void router.replace({
    path: route.path,
    query: {
      ...route.query,
      ...uiSurfaceRouteQuery(props.surface),
      ...(requestedCustomer ? { customer: requestedCustomer } : { customer: undefined })
    }
  });
});

watch([module, masterView], () => {
  filtersCollapsed.value = false;
});

</script>

<template>
  <section
    class="workbench-ui workbench-management-ui"
    :class="{
      'is-guest-management': !canUseProtectedManagement,
      'without-header': !showHeader,
      'is-floor-overview': isFloorOverview
    }"
    :data-workbench-area="isFloorOverview ? 'floor' : 'management'"
    :aria-label="isFloorOverview ? '現場工作台收退料總檢視' : '工作台管理後臺'"
  >
    <header v-if="showHeader" class="workbench-header">
      <div class="workbench-brand">
        <span class="workbench-mark">FM</span>
        <div>
          <p>Fixture-M Lite</p>
          <h1>工作台管理後臺</h1>
        </div>
      </div>

      <div class="workbench-header-center">
        <slot name="ui-switcher" />
      </div>

      <div class="workbench-session">
        <slot name="heading-actions" />
        <label>
          <span>目前客戶</span>
          <select :value="selectedCustomerId ?? undefined" aria-label="工作台管理客戶" @change="handleCustomerChange">
            <option v-for="customer in customers" :key="customer.id" :value="customer.id">
              {{ customer.code }}－{{ customer.name }}
            </option>
          </select>
        </label>
        <div class="workbench-account">
          <strong>{{ currentUserName }}</strong>
          <span>{{ currentRoleLabel }}</span>
        </div>
        <slot name="account-action" />
      </div>
    </header>

    <div class="workbench-columns workbench-management-columns">
      <aside
        class="workbench-panel workbench-controls workbench-management-nav"
        :aria-label="isFloorOverview ? '現場工作台總檢視導覽' : '工作台管理模組'"
      >
        <div class="workbench-panel-heading">
          <div><span>{{ isFloorOverview ? "現場工作台" : "管理後臺" }}</span><h2>{{ moduleLabel }}</h2></div>
        </div>

        <nav
          v-if="isFloorOverview"
          class="workbench-mode-tabs"
          data-tour="workbench-mode-tabs"
          role="tablist"
          aria-label="工作台作業模式"
        >
          <button
            v-for="item in floorModes"
            :key="item.key"
            type="button"
            role="tab"
            :aria-selected="item.key === 'overview'"
            :class="{ active: item.key === 'overview' }"
            @click="navigateFloorMode(item)"
          >
            {{ item.label }}
          </button>
        </nav>

        <nav v-if="!transactionsOnly" class="workbench-management-module-list" data-tour="workbench-management-nav" aria-label="管理功能">
          <button
            v-for="item in primaryModules"
            :key="item.key"
            type="button"
            :class="{ active: module === item.key }"
            @click="navigate(item.path)"
          >
            <span class="workbench-module-index">{{ item.index }}</span>
            <strong>{{ item.label }}</strong>
            <span aria-hidden="true">›</span>
          </button>
        </nav>

        <p v-if="!transactionsOnly && !canUseProtectedManagement" class="workbench-management-access-note">
          訪客可使用收退料總檢視；產能設定與資料維護需要登入後才能使用。
        </p>

        <section v-if="module === 'production'" class="workbench-management-subnav" aria-label="產能設定子功能">
          <div class="workbench-subheading"><h3>產能設定內容</h3></div>
          <button
            v-for="item in productionItems"
            :key="item.key"
            type="button"
            :class="{ active: productionView === item.key }"
            @click="navigate(item.path)"
          >
            {{ item.label }}
          </button>
        </section>

        <section v-if="module === 'master'" class="workbench-management-subnav" aria-label="資料維護子功能">
          <div class="workbench-subheading"><h3>資料類型</h3></div>
          <button
            v-for="item in masterItems"
            :key="item.key"
            type="button"
            :class="{ active: masterView === item.key }"
            @click="navigate(item.path)"
          >
            {{ item.label }}
          </button>
        </section>

        <button v-if="!isFloorOverview" class="workbench-return-floor" type="button" @click="returnToWorkbench">
          <span aria-hidden="true">←</span>
          返回現場工作台
        </button>
      </aside>

      <main class="workbench-panel workbench-results workbench-management-results" aria-live="polite">
        <div class="workbench-panel-heading workbench-results-heading">
          <div><span>{{ moduleEyebrow }}</span><h2>{{ moduleLabel }}</h2></div>
          <div class="workbench-management-heading-actions">
            <span v-if="currentCustomer" class="workbench-customer-chip">{{ currentCustomer.code }}</span>
          </div>
        </div>

        <div
          class="workbench-management-operation-shell"
          :class="{ 'filters-collapsed': filtersCollapsed }"
        >
          <WorkbenchAdminOperations
            v-if="module === 'ledger' || module === 'quality'"
            :mode="module"
            @navigate="handleAdminNavigate"
          />
          <FormImageMaintenance
            v-else-if="module === 'master' && masterView === 'image'"
            workbench-layout
          />
          <FormReportOperations
            v-else
            :mode="module"
            :requested-production-view="productionView"
            :requested-master-view="reportMasterView"
            workbench-layout
            @production-view-change="openProductionView"
            @master-view-change="openMasterView"
          />
        </div>
      </main>

      <aside
        class="workbench-panel workbench-detail workbench-management-detail"
        :class="{ 'filters-collapsed': filtersCollapsed }"
        aria-label="工作台篩選與編輯工具"
      >
        <div class="workbench-panel-heading">
          <div><span>操作面板</span><h2>{{ toolPanelLabel }}</h2></div>
          <button
            class="workbench-filter-toggle"
            type="button"
            :aria-expanded="!filtersCollapsed"
            aria-controls="workbench-management-tools"
            @click="filtersCollapsed = !filtersCollapsed"
          >
            {{ filtersCollapsed ? "展開篩選" : "收合篩選" }}
          </button>
        </div>
        <div id="workbench-management-tools" class="workbench-management-tools" />
      </aside>
    </div>
  </section>
</template>

<style scoped src="@/styles/surfaces/workbench.css"></style>
