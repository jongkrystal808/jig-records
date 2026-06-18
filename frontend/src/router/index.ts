import { createRouter, createWebHistory } from "vue-router";
import { authSession } from "@/appState";
import InventoryPage from "@/pages/InventoryPage.vue";
import MasterPage from "@/pages/MasterPage.vue";
import ProductionPage from "@/pages/ProductionPage.vue";
import SearchWorkspacePage from "@/pages/SearchWorkspacePage.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/search" },
    { path: "/search", name: "search", component: SearchWorkspacePage },
    { path: "/inventory", name: "inventory", component: InventoryPage },
    { path: "/inventory/overview", name: "inventory-overview", component: InventoryPage },
    { path: "/master", name: "master", component: MasterPage },
    { path: "/production", name: "production", component: ProductionPage }
  ]
});

router.beforeEach((to) => {
  if (to.path.startsWith("/master") && authSession.value?.role === "guest") {
    return { path: "/search" };
  }
  return true;
});

export default router;
