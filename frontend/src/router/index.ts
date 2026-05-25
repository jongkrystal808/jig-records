import { createRouter, createWebHistory } from "vue-router";
import SearchWorkspacePage from "@/pages/SearchWorkspacePage.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/search" },
    { path: "/search", name: "search", component: SearchWorkspacePage }
  ]
});

export default router;
