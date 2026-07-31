<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { authSession, customerSwitchGuards } from "@/appState";
import InventoryRelationsPage from "@/pages/InventoryRelationsPage.vue";
import SearchWorkspacePage from "@/pages/SearchWorkspacePage.vue";
import { pushToast } from "@/toastState";
import type { AuthSession } from "@/types";

type HomeMode = "query" | "report";

const PREFERENCE_PREFIX = "search-home-default-mode";
const route = useRoute();
const router = useRouter();

function modeFromQuery(value: unknown): HomeMode | null {
  if (value === "query" || value === "report") return value;
  if (Array.isArray(value) && (value[0] === "query" || value[0] === "report")) return value[0];
  return null;
}

function preferenceKey(session: AuthSession): string {
  const identity = session.user?.id ?? session.user?.username ?? session.display_name;
  return `${PREFERENCE_PREFIX}:${identity}`;
}

function roleDefaultMode(session: AuthSession | null): HomeMode {
  return session?.role === "guest" ? "report" : "query";
}

function readPreferredMode(session: AuthSession | null): HomeMode {
  const fallback = roleDefaultMode(session);
  if (!session || session.role === "guest") return fallback;
  try {
    const saved = window.localStorage.getItem(preferenceKey(session));
    return saved === "query" || saved === "report" ? saved : fallback;
  } catch {
    return fallback;
  }
}

const preferredMode = ref<HomeMode>(readPreferredMode(authSession.value));
const activeMode = ref<HomeMode>(
  modeFromQuery(route.query.home_mode) ?? preferredMode.value
);
const isGuest = computed(() => authSession.value?.role === "guest");
const activeModeLabel = computed(() => (activeMode.value === "query" ? "查詢" : "報表"));
const preferredModeLabel = computed(() =>
  preferredMode.value === "query" ? "查詢" : "報表"
);
const currentModeIsPreferred = computed(() => activeMode.value === preferredMode.value);

function canLeaveQueryMode(): boolean {
  if (activeMode.value !== "query" || !customerSwitchGuards.value["search-page"]) return true;
  return window.confirm("查詢頁有尚未儲存的修改，切換到報表後會遺失。要繼續嗎？");
}

function selectMode(nextMode: HomeMode): void {
  if (nextMode === activeMode.value || !canLeaveQueryMode()) return;
  activeMode.value = nextMode;
  void router.replace({
    path: route.path,
    query: {
      ...route.query,
      home_mode: nextMode
    }
  });
}

function saveCurrentAsDefault(): void {
  const session = authSession.value;
  if (!session || session.role === "guest") return;
  try {
    window.localStorage.setItem(preferenceKey(session), activeMode.value);
    preferredMode.value = activeMode.value;
    pushToast(`已將「${activeModeLabel.value}」設為登入後預設首頁。`, "success");
  } catch {
    pushToast("無法儲存首頁偏好，請確認瀏覽器允許本機儲存。", "error");
  }
}

watch(
  () => route.query.home_mode,
  (value) => {
    const routeMode = modeFromQuery(value);
    if (routeMode) activeMode.value = routeMode;
  }
);

watch(
  () => `${authSession.value?.role ?? ""}:${authSession.value?.user?.id ?? authSession.value?.display_name ?? ""}`,
  () => {
    preferredMode.value = readPreferredMode(authSession.value);
    const routeMode = modeFromQuery(route.query.home_mode);
    activeMode.value = routeMode ?? preferredMode.value;
  }
);
</script>

<template>
  <div class="search-home">
    <section class="home-mode-bar" aria-label="首頁模式">
      <div
        class="home-mode-tabs"
        data-tour="home-mode-switch"
        role="tablist"
        aria-label="切換查詢或報表"
      >
        <button
          type="button"
          role="tab"
          :aria-selected="activeMode === 'query'"
          :class="{ active: activeMode === 'query' }"
          @click="selectMode('query')"
        >
          <strong>查詢</strong>
          <span>治具／機種查詢</span>
        </button>
        <button
          type="button"
          role="tab"
          :aria-selected="activeMode === 'report'"
          :class="{ active: activeMode === 'report' }"
          @click="selectMode('report')"
        >
          <strong>報表</strong>
          <span>庫存與配置報表</span>
        </button>
      </div>

      <div v-if="isGuest" class="home-mode-preference guest">
        <span>訪客預設</span>
        <strong>報表</strong>
      </div>
      <div v-else class="home-mode-preference">
        <span>登入後預設：<strong>{{ preferredModeLabel }}</strong></span>
        <span v-if="currentModeIsPreferred" class="default-confirmation">目前為預設</span>
        <button v-else type="button" @click="saveCurrentAsDefault">
          將{{ activeModeLabel }}設為登入後預設
        </button>
      </div>
    </section>

    <SearchWorkspacePage v-if="activeMode === 'query'" />
    <InventoryRelationsPage v-else />
  </div>
</template>

<style scoped>
.search-home {
  min-height: 100%;
}

.home-mode-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 12px clamp(12px, 2vw, 28px) 0;
}

.home-mode-tabs {
  display: inline-grid;
  grid-template-columns: repeat(2, minmax(150px, 1fr));
  gap: 4px;
  padding: 4px;
  border: 1px solid #c8d7ea;
  border-radius: 11px;
  background: #edf3fb;
}

.home-mode-tabs button {
  display: grid;
  gap: 1px;
  min-height: 46px;
  padding: 6px 16px;
  border: 1px solid transparent;
  border-radius: 8px;
  color: #61718a;
  background: transparent;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.home-mode-tabs button:hover {
  color: #245c9f;
  background: rgba(255, 255, 255, 0.7);
}

.home-mode-tabs button.active {
  border-color: #8db5ee;
  color: #235991;
  background: #fff;
  box-shadow: 0 2px 7px rgba(40, 89, 148, 0.12);
}

.home-mode-tabs strong {
  font-size: 0.84rem;
}

.home-mode-tabs span {
  font-size: 0.67rem;
  font-weight: 650;
}

.home-mode-preference {
  display: flex;
  align-items: center;
  gap: 9px;
  min-height: 34px;
  padding: 5px 7px 5px 11px;
  border: 1px solid #d2deed;
  border-radius: 9px;
  color: #61718a;
  background: #f8fafd;
  font-size: 0.7rem;
  font-weight: 700;
}

.home-mode-preference strong {
  color: #2b4f7d;
}

.home-mode-preference button {
  min-height: 27px;
  padding: 4px 8px;
  border: 1px solid #8db5ee;
  border-radius: 6px;
  color: #245c9f;
  background: #fff;
  font: inherit;
  font-size: 0.68rem;
  font-weight: 800;
  cursor: pointer;
}

.home-mode-preference button:hover {
  background: #edf5ff;
}

.home-mode-preference.guest {
  padding-right: 11px;
}

.default-confirmation {
  padding: 3px 7px;
  border-radius: 999px;
  color: #1c7350;
  background: #e8f7f0;
}

@media (max-width: 680px) {
  .home-mode-bar {
    align-items: stretch;
    flex-direction: column;
    gap: 7px;
    padding: 9px 8px 0;
  }

  .home-mode-tabs {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    width: 100%;
  }

  .home-mode-tabs button {
    min-width: 0;
    padding-inline: 10px;
  }

  .home-mode-preference {
    justify-content: space-between;
  }
}
</style>
