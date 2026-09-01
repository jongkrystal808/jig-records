import { createRouter, createWebHistory } from "vue-router";
import { authSession } from "@/appState";
import { pushToast } from "@/toastState";
import { readSessionUiSurface, resolveHomeUiSurface } from "@/utils/uiSurface";
import { confirmUnsavedChanges, consumeRouteNavigationBypass } from "@/unsavedChangesGuard";
import { canManageAccounts, canManageAdminReports } from "@/utils/roles";

const FORM_WORKSPACE_ROUTE_NAMES = new Set([
  "search",
  "inventory",
  "inventory-overview",
  "storage",
  "master-fixtures",
  "master-models",
  "master-stations",
  "master-customers",
  "master-users",
  "master-ledger",
  "master-quality",
  "master-images",
  "production",
  "production-mapping",
  "production-requirements"
]);

export const FORM_WORKSPACE_SCROLL_POSITION = { left: 0, top: 0 } as const;

const SearchHomePage = () => import("@/pages/SearchHomePage.vue");
const LoginRoutePage = () => import("@/pages/LoginRoutePage.vue");
const SearchWorkspacePage = () => import("@/pages/SearchWorkspacePage.vue");
const InventoryPage = () => import("@/pages/InventoryPage.vue");
const MasterPage = () => import("@/pages/MasterPage.vue");
const ProductionPage = () => import("@/pages/ProductionPage.vue");
const StoragePage = () => import("@/pages/StoragePage.vue");

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior(to, from, savedPosition) {
    const requestedSurface = resolveHomeUiSurface(to.query.ui_surface, to.query.home_mode);
    const isFormWorkspaceNavigation =
      to.path !== from.path &&
      FORM_WORKSPACE_ROUTE_NAMES.has(String(to.name ?? "")) &&
      FORM_WORKSPACE_ROUTE_NAMES.has(String(from.name ?? "")) &&
      (requestedSurface ?? readSessionUiSurface()) === "form";

    if (isFormWorkspaceNavigation) {
      return FORM_WORKSPACE_SCROLL_POSITION;
    }
    return savedPosition ?? false;
  },
  routes: [
    { path: "/", redirect: () => (authSession.value ? "/search" : "/login") },
    { path: "/login", name: "login", component: LoginRoutePage },
    { path: "/search", name: "search", component: SearchHomePage },
    { path: "/search/detail", name: "search-detail", component: SearchWorkspacePage },
    { path: "/inventory", name: "inventory", component: InventoryPage },
    { path: "/inventory/overview", name: "inventory-overview", component: InventoryPage },
    { path: "/inventory/filter-view", redirect: "/search" },
    { path: "/inventory/relations", redirect: "/search" },
    { path: "/storage", name: "storage", component: StoragePage },
    { path: "/master", redirect: "/master/fixtures" },
    { path: "/master/fixtures", name: "master-fixtures", component: MasterPage },
    { path: "/master/models", name: "master-models", component: MasterPage },
    { path: "/master/stations", name: "master-stations", component: MasterPage },
    { path: "/master/customers", name: "master-customers", component: MasterPage },
    { path: "/master/users", name: "master-users", component: MasterPage },
    { path: "/master/ledger", name: "master-ledger", component: MasterPage },
    { path: "/master/quality", name: "master-quality", component: MasterPage },
    { path: "/master/images", name: "master-images", component: MasterPage },
    { path: "/production", name: "production", component: ProductionPage },
    { path: "/production/mapping", name: "production-mapping", component: ProductionPage },
    { path: "/production/requirements", name: "production-requirements", component: ProductionPage }
  ]
});

router.beforeEach(async (to, from) => {
  if (to.path !== from.path && !consumeRouteNavigationBypass()) {
    if (!(await confirmUnsavedChanges("route"))) return false;
  }
  if (!authSession.value && to.name !== "login") {
    return { name: "login" };
  }
  if (authSession.value && to.name === "login") {
    return { name: "search" };
  }
  if (["/master/ledger", "/master/quality"].includes(to.path) && !canManageAdminReports(authSession.value?.role)) {
    pushToast("此管理功能僅限 Admin 使用。", "info", 4800);
    if (to.query.ui_surface === "workbench" || to.query.ui_surface === "workspace") {
      const targetSurface = to.query.ui_surface;
      return {
        path: "/inventory/overview",
        query: {
          ui_surface: targetSurface,
          home_mode: "query",
          ...(to.query.customer ? { customer: to.query.customer } : {})
        }
      };
    }
    return { path: "/search" };
  }
  if (["/master/customers", "/master/users"].includes(to.path) && !canManageAccounts(authSession.value?.role)) {
    pushToast("此管理功能僅限 Super Admin 使用。", "info", 4800);
    return { path: "/master/fixtures", query: to.query };
  }
  if (to.path.startsWith("/master") && authSession.value?.role === "guest") {
    if (to.query.ui_surface === "workbench" || to.query.ui_surface === "workspace") {
      const targetSurface = to.query.ui_surface;
      pushToast("訪客無法使用資料維護，已返回收退料總檢視。", "info", 4800);
      return {
        path: "/inventory/overview",
        query: {
          ui_surface: targetSurface,
          home_mode: "query",
          ...(to.query.customer ? { customer: to.query.customer } : {})
        }
      };
    }
    return { path: "/search" };
  }
  if (to.path === "/inventory" && authSession.value?.role === "guest") {
    return { path: "/inventory/overview" };
  }
  if (to.path.startsWith("/production") && authSession.value?.role === "guest") {
    if (to.query.ui_surface === "workbench" || to.query.ui_surface === "workspace") {
      const targetSurface = to.query.ui_surface;
      pushToast("訪客無法使用產能設定，已返回收退料總檢視。", "info", 4800);
      return {
        path: "/inventory/overview",
        query: {
          ui_surface: targetSurface,
          home_mode: "query",
          ...(to.query.customer ? { customer: to.query.customer } : {})
        }
      };
    }
    pushToast("訪客無法使用產能設定，已返回報表。", "info", 4800);
    return { path: "/search", query: { ui_surface: "form", home_mode: "report" } };
  }
  return true;
});

export default router;
