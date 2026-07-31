import { createRouter, createWebHistory } from "vue-router";
import { authSession } from "@/appState";
import InventoryPage from "@/pages/InventoryPage.vue";
import MasterPage from "@/pages/MasterPage.vue";
import ProductionPage from "@/pages/ProductionPage.vue";
import SearchHomePage from "@/pages/SearchHomePage.vue";
import SearchWorkspacePage from "@/pages/SearchWorkspacePage.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/search" },
    { path: "/search", name: "search", component: SearchHomePage },
    { path: "/search/detail", name: "search-detail", component: SearchWorkspacePage },
    { path: "/inventory", name: "inventory", component: InventoryPage },
    { path: "/inventory/overview", name: "inventory-overview", component: InventoryPage },
    { path: "/inventory/filter-view", redirect: "/search" },
    { path: "/inventory/relations", redirect: "/search" },
    { path: "/master", redirect: "/master/fixtures" },
    { path: "/master/fixtures", name: "master-fixtures", component: MasterPage },
    { path: "/master/models", name: "master-models", component: MasterPage },
    { path: "/master/stations", name: "master-stations", component: MasterPage },
    { path: "/master/customers", name: "master-customers", component: MasterPage },
    { path: "/master/users", name: "master-users", component: MasterPage },
    { path: "/master/ledger", name: "master-ledger", component: MasterPage },
    { path: "/master/quality", name: "master-quality", component: MasterPage },
    { path: "/production", name: "production", component: ProductionPage },
    { path: "/production/mapping", name: "production-mapping", component: ProductionPage },
    { path: "/production/requirements", name: "production-requirements", component: ProductionPage }
  ]
});

router.beforeEach((to) => {
  if (to.path.startsWith("/master") && authSession.value?.role === "guest") {
    return { path: "/search" };
  }
  if (to.path === "/inventory" && authSession.value?.role === "guest") {
    return { path: "/inventory/overview" };
  }
  if (to.path.startsWith("/production") && authSession.value?.role === "guest") {
    return { path: "/search", query: { home_mode: "report" } };
  }
  return true;
});

export default router;
