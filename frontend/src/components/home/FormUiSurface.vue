<script setup lang="ts">
import { computed, ref, watch } from "vue";

import {
  authSession,
  customers,
  formWorkspaceRequestId,
  formWorkspaceRequestKey,
  onboardingSandboxMode,
  selectedCustomerId,
  type FormWorkspaceKey
} from "@/appState";
import FormReportOperations, {
  type FormMasterView,
  type FormOperationMode,
  type FormProductionView
} from "@/components/home/FormReportOperations.vue";
import FormAdminReports, { type FormAdminReportMode } from "@/components/home/FormAdminReports.vue";
import FormImageMaintenance from "@/components/home/FormImageMaintenance.vue";
import FormWorkspaceSwitcher from "@/components/home/FormWorkspaceSwitcher.vue";
import BatchImportPanel from "@/components/inventory/BatchImportPanel.vue";
import InventoryRelationsPage from "@/pages/InventoryRelationsPage.vue";
import { canManageAdminReports, canOperate, roleLabel } from "@/utils/roles";

export type FormWorkspace = "report" | FormWorkspaceKey | FormAdminReportMode | "image";
type BatchDraftState = { hasPendingDraft: boolean; pendingRowCount: number; promptMessage: string };

const props = defineProps<{
  workspace?: FormWorkspace;
  productionView?: FormProductionView;
  masterView?: FormMasterView;
  surfaceLabel?: string;
}>();
const emit = defineEmits<{
  workspaceChange: [workspace: FormWorkspace];
  productionViewChange: [view: FormProductionView];
  masterViewChange: [view: FormMasterView];
  "update:selectedCustomerId": [value: number | null];
}>();

const activeWorkspace = ref<FormWorkspace>("report");
const importMounted = ref(false);
const operationsMounted = ref(false);
const adminReportsMounted = ref(false);
const imageMaintenanceMounted = ref(false);
const batchDraftState = ref<BatchDraftState>({ hasPendingDraft: false, pendingRowCount: 0, promptMessage: "" });

const canOperateWorkspace = computed(() => canOperate(authSession.value?.role));
const canAdminReports = computed(() => canManageAdminReports(authSession.value?.role));
const workspaceItems = computed<Array<{ key: FormWorkspace; label: string; shortLabel: string }>>(() => [
  { key: "report", label: "篩選報表", shortLabel: "報" },
  ...(canOperateWorkspace.value ? [{ key: "import" as const, label: "收退料匯入", shortLabel: "匯" }] : []),
  { key: "inventory-overview", label: "收退料總檢視", shortLabel: "檢" },
  ...(canOperateWorkspace.value
    ? [
        { key: "production" as const, label: "產能", shortLabel: "產" },
        { key: "master" as const, label: "資料維護", shortLabel: "維" },
        { key: "image" as const, label: "圖片維護", shortLabel: "圖" },
        ...(canAdminReports.value
          ? [
              { key: "ledger" as const, label: "收退料帳目管理", shortLabel: "帳" },
              { key: "quality" as const, label: "治具資料品質", shortLabel: "品" }
            ]
          : [])
      ]
    : [])
]);
const operationMode = computed<FormOperationMode>(() =>
  activeWorkspace.value === "production"
    ? "production"
    : activeWorkspace.value === "master"
      ? "master"
      : "transactions"
);
const workspaceHint = computed(() => {
  if (batchDraftState.value.hasPendingDraft) return `收退料匯入尚有 ${batchDraftState.value.pendingRowCount} 筆未送出`;
  return "頁面表頭與表格位置固定，只切換條件欄與資料欄位";
});

const activeWorkspaceLabel = computed(
  () => workspaceItems.value.find((item) => item.key === activeWorkspace.value)?.label ?? "篩選報表"
);
const activeWorkspaceDescription = computed(() => {
  const descriptions: Record<FormWorkspace, string> = {
    report: "查詢治具庫存、配置關係與可開站產能",
    import: "以表格批次建立收料與退料帳目",
    "inventory-overview": "集中檢視目前客戶的收退料明細",
    production: "維護機種、站點與治具需求關係",
    master: "維護治具、機種、站點與權限主資料",
    ledger: "查詢、重算或撤回已建立的收退料案件",
    quality: "檢查並直接修正治具資料缺漏",
    image: "依治具編號預覽、替換與批次上傳圖片"
  };
  return descriptions[activeWorkspace.value];
});
const selectedCustomerIndex = computed(() =>
  customers.value.findIndex((customer) => customer.id === selectedCustomerId.value)
);
const customerPositionLabel = computed(() => {
  if (customers.value.length === 0 || selectedCustomerIndex.value < 0) return "尚未選擇客戶";
  return `目前客戶 ${selectedCustomerIndex.value + 1} / ${customers.value.length}`;
});
const currentUserName = computed(
  () => authSession.value?.user?.display_name || authSession.value?.display_name || "訪客"
);
const currentUserAccount = computed(() => authSession.value?.user?.username || "Guest");
const currentUserRole = computed(() => {
  const role = authSession.value?.role;
  return roleLabel(role);
});
const currentUserInitial = computed(() => currentUserName.value.trim().slice(0, 1).toLocaleUpperCase() || "U");

function canOpenWorkspace(key: FormWorkspace): boolean {
  if (["ledger", "quality"].includes(key)) return canAdminReports.value;
  return ["report", "inventory-overview"].includes(key) || canOperateWorkspace.value;
}

function selectWorkspace(key: FormWorkspace): void {
  if (!canOpenWorkspace(key)) return;
  if (key === "import") importMounted.value = true;
  if (["inventory-overview", "production", "master"].includes(key)) operationsMounted.value = true;
  if (["ledger", "quality"].includes(key)) adminReportsMounted.value = true;
  if (key === "image") imageMaintenanceMounted.value = true;
  activeWorkspace.value = key;
  emit("workspaceChange", key);
}

function selectWorkspaceFromSwitcher(key: string): void {
  if (workspaceItems.value.some((item) => item.key === key)) {
    selectWorkspace(key as FormWorkspace);
  }
}

function rememberBatchDraft(state: BatchDraftState): void {
  batchDraftState.value = state;
}

function handleCustomerChange(event: Event): void {
  const value = Number.parseInt((event.target as HTMLSelectElement).value, 10);
  emit("update:selectedCustomerId", Number.isFinite(value) ? value : null);
}

function stepCustomer(offset: -1 | 1): void {
  if (customers.value.length === 0) return;
  const currentIndex = selectedCustomerIndex.value;
  const nextIndex = Math.min(
    customers.value.length - 1,
    Math.max(0, (currentIndex < 0 ? 0 : currentIndex) + offset)
  );
  const nextCustomerId = customers.value[nextIndex]?.id;
  if (nextCustomerId != null && nextCustomerId !== selectedCustomerId.value) {
    emit("update:selectedCustomerId", nextCustomerId);
  }
}

watch(formWorkspaceRequestId, () => {
  if (formWorkspaceRequestKey.value) selectWorkspace(formWorkspaceRequestKey.value);
});

watch(() => props.workspace, (workspace) => {
  if (workspace && workspace !== activeWorkspace.value) selectWorkspace(workspace);
}, { immediate: true });

watch(canOperateWorkspace, (allowed) => {
  if (!allowed && !["report", "inventory-overview"].includes(activeWorkspace.value)) activeWorkspace.value = "report";
});

watch(canAdminReports, (allowed) => {
  if (!allowed && ["ledger", "quality"].includes(activeWorkspace.value)) activeWorkspace.value = "report";
});
</script>

<template>
  <section
    class="form-ui-surface"
    data-ui-surface="form"
    :data-active-form-workspace="activeWorkspace"
    :aria-label="props.surfaceLabel || 'Form UI'"
  >
    <div class="guest-report-page form-fixed-report-page">
      <header class="report-heading form-system-heading" data-tour="form-system-heading">
        <div class="form-heading-title">
          <p class="eyebrow">Fixture-M Lite · {{ props.surfaceLabel || "Form UI" }}</p>
          <div class="form-heading-copy">
            <h1>{{ activeWorkspaceLabel }}</h1>
            <p>{{ activeWorkspaceDescription }}</p>
          </div>
        </div>
        <div class="form-heading-switcher">
          <slot name="ui-switcher" />
        </div>
        <div class="form-heading-side">
          <slot name="heading-actions" />
          <div class="form-session-tools">
            <div class="form-scope-badge" data-tour="form-customer-scope">
              <button
                class="form-customer-step"
                type="button"
                aria-label="切換到上一個客戶"
                :disabled="selectedCustomerIndex <= 0"
                @click="stepCustomer(-1)"
              >
                ‹
              </button>
              <label>
                <span>{{ customerPositionLabel }}</span>
                <select :value="selectedCustomerId ?? undefined" aria-label="選擇客戶" @change="handleCustomerChange">
                  <option v-for="customer in customers" :key="customer.id" :value="customer.id">
                    {{ customer.code }}－{{ customer.name }}
                  </option>
                </select>
              </label>
              <button
                class="form-customer-step"
                type="button"
                aria-label="切換到下一個客戶"
                :disabled="selectedCustomerIndex < 0 || selectedCustomerIndex >= customers.length - 1"
                @click="stepCustomer(1)"
              >
                ›
              </button>
            </div>
            <div class="form-current-user" aria-label="目前用戶">
              <span class="form-user-avatar" aria-hidden="true">{{ currentUserInitial }}</span>
              <span class="form-user-copy">
                <small>{{ currentUserRole }} · {{ currentUserAccount }}</small>
                <strong>{{ currentUserName }}</strong>
              </span>
            </div>
            <slot name="account-action" />
          </div>
        </div>
      </header>

      <InventoryRelationsPage
        v-show="activeWorkspace === 'report'"
        class="form-workspace-pane"
        hide-heading
        embedded-shell
      >
        <template #between-filter-and-results>
          <FormWorkspaceSwitcher
            :active-workspace="activeWorkspace"
            :items="workspaceItems"
            :hint="workspaceHint"
            @select="selectWorkspaceFromSwitcher"
          />
        </template>
      </InventoryRelationsPage>

      <div
        v-if="importMounted"
        v-show="activeWorkspace === 'import'"
        class="report-workspace form-batch-workspace form-workspace-pane"
        data-tour="form-import-workspace"
      >
        <div class="report-main-column">
          <BatchImportPanel
            :customer-id="selectedCustomerId ?? undefined"
            :tutorial-mode="onboardingSandboxMode"
            title="收退料匯入條件"
            description="下方表格可直接輸入，或貼上 Excel／其他表格資料。"
            :hide-frame="true"
            @draft-state-change="rememberBatchDraft"
          >
            <template #between-meta-and-grid>
              <FormWorkspaceSwitcher
                :active-workspace="activeWorkspace"
                :items="workspaceItems"
                :hint="workspaceHint"
                @select="selectWorkspaceFromSwitcher"
              />
            </template>
          </BatchImportPanel>
        </div>
      </div>

      <FormReportOperations
        v-if="operationsMounted"
        v-show="['inventory-overview', 'production', 'master'].includes(activeWorkspace)"
        class="form-workspace-pane"
        :mode="operationMode"
        :requested-production-view="productionView"
        :requested-master-view="masterView"
        @production-view-change="emit('productionViewChange', $event)"
        @master-view-change="emit('masterViewChange', $event)"
      >
        <template #between-filter-and-results>
          <FormWorkspaceSwitcher
            :active-workspace="activeWorkspace"
            :items="workspaceItems"
            :hint="workspaceHint"
            @select="selectWorkspaceFromSwitcher"
          />
        </template>
      </FormReportOperations>

      <FormAdminReports
        v-if="adminReportsMounted"
        v-show="['ledger', 'quality'].includes(activeWorkspace)"
        class="form-workspace-pane"
        :mode="activeWorkspace === 'quality' ? 'quality' : 'ledger'"
        @navigate="selectWorkspace"
      >
        <template #between-filter-and-results>
          <FormWorkspaceSwitcher
            :active-workspace="activeWorkspace"
            :items="workspaceItems"
            :hint="workspaceHint"
            @select="selectWorkspaceFromSwitcher"
          />
        </template>
      </FormAdminReports>

      <FormImageMaintenance
        v-if="imageMaintenanceMounted"
        v-show="activeWorkspace === 'image'"
        class="form-workspace-pane"
      >
        <template #between-filter-and-results>
          <FormWorkspaceSwitcher
            :active-workspace="activeWorkspace"
            :items="workspaceItems"
            :hint="workspaceHint"
            @select="selectWorkspaceFromSwitcher"
          />
        </template>
      </FormImageMaintenance>
    </div>
  </section>
</template>

<style src="../../styles/surfaces/form.css"></style>
