<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

import { masterApi } from "@/api/masterClient";
import { storageApi } from "@/api/storageClient";
import { authSession, selectedCustomerId, setCustomerSwitchGuard } from "@/appState";
import { requestConfirmation } from "@/confirmState";
import { pushToast } from "@/toastState";
import type {
  Fixture,
  FixturePlacementDetail,
  FixturePlacementInput,
  StorageOverview
} from "@/types";

type PlacementDraft = FixturePlacementInput & { key: string; label: string };

const overview = ref<StorageOverview | null>(null);
const fixtures = ref<Fixture[]>([]);
const selectedFixtureId = ref<number | null>(null);
const fixtureDetail = ref<FixturePlacementDetail | null>(null);
const placementDrafts = ref<PlacementDraft[]>([]);
const selectedTarget = ref("");
const selectedCodeIds = ref<number[]>([]);
const targetContainerId = ref<number | null>(null);
const keyword = ref("");
const newCodesText = ref("");
const newContainerName = ref("");
const newContainerDescription = ref("");
const loading = ref(false);
const saving = ref(false);
const savedPlacementSignature = ref("[]");

const canWrite = computed(() => authSession.value?.role !== "guest");
const selectedFixture = computed(() => fixtures.value.find((item) => item.id === selectedFixtureId.value) ?? null);
const placementTotal = computed(() => placementDrafts.value.reduce((sum, row) => sum + (row.quantity ?? 0), 0));
const placementSignature = computed(() => JSON.stringify(
  placementDrafts.value.map(({ key: _key, label: _label, ...row }) => row)
));
const placementDirty = computed(() => placementSignature.value !== savedPlacementSignature.value);

const targetOptions = computed(() => {
  const codeOptions = (overview.value?.codes ?? []).map((code) => ({
    value: `code:${code.id}`,
    label: `${code.container_name ? `${code.container_name} / ` : ""}${code.code}`
  }));
  const stationOptions = (fixtureDetail.value?.station_options ?? []).map((station) => ({
    value: `station:${station.model_id}:${station.station_id}`,
    label: `${station.model_name} / ${station.station_code}`
  }));
  return [...stationOptions, ...codeOptions];
});

function draftKey(row: FixturePlacementInput): string {
  return row.target_type === "storage_code"
    ? `code:${row.storage_code_id}`
    : `station:${row.model_id}:${row.station_id}`;
}

function rebuildDrafts(detail: FixturePlacementDetail): void {
  placementDrafts.value = detail.placements.map((row) => ({
    key: draftKey(row),
    label: row.display_label,
    target_type: row.target_type,
    storage_code_id: row.storage_code_id,
    model_id: row.model_id,
    station_id: row.station_id,
    quantity: row.quantity
  }));
  savedPlacementSignature.value = placementSignature.value;
}

async function loadOverview(): Promise<void> {
  if (!selectedCustomerId.value) {
    overview.value = null;
    fixtures.value = [];
    return;
  }
  loading.value = true;
  try {
    const [nextOverview, nextFixtures] = await Promise.all([
      storageApi.getOverview(selectedCustomerId.value, keyword.value),
      masterApi.listFixtures(selectedCustomerId.value)
    ]);
    overview.value = nextOverview;
    fixtures.value = nextFixtures;
    selectedCodeIds.value = selectedCodeIds.value.filter((id) => nextOverview.codes.some((code) => code.id === id));
    if (selectedFixtureId.value && !nextFixtures.some((fixture) => fixture.id === selectedFixtureId.value)) {
      selectedFixtureId.value = null;
      fixtureDetail.value = null;
      placementDrafts.value = [];
    }
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "載入治具收納資料失敗", "error");
  } finally {
    loading.value = false;
  }
}

async function loadFixtureDetail(): Promise<void> {
  if (!selectedFixtureId.value) {
    fixtureDetail.value = null;
    placementDrafts.value = [];
    return;
  }
  try {
    const detail = await storageApi.getFixturePlacements(selectedFixtureId.value);
    fixtureDetail.value = detail;
    rebuildDrafts(detail);
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "載入治具位置失敗", "error");
  }
}

async function handleFixtureSelection(event: Event): Promise<void> {
  const select = event.target as HTMLSelectElement;
  const nextId = select.value ? Number(select.value) : null;
  if (placementDirty.value) {
    const confirmed = await requestConfirmation("目前治具的位置分配尚未儲存，切換治具會遺失修改。要繼續嗎？", {
      title: "切換治具",
      confirmLabel: "捨棄並切換",
      tone: "danger"
    });
    if (!confirmed) {
      select.value = selectedFixtureId.value === null ? "" : String(selectedFixtureId.value);
      return;
    }
  }
  selectedFixtureId.value = nextId;
}

async function registerCodes(): Promise<void> {
  if (!selectedCustomerId.value || !newCodesText.value.trim()) return;
  saving.value = true;
  try {
    overview.value = await storageApi.registerCodes(selectedCustomerId.value, newCodesText.value);
    newCodesText.value = "";
    pushToast("位置編號已登記；半形與全形逗號皆可使用。", "success");
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "登記位置編號失敗", "error");
  } finally {
    saving.value = false;
  }
}

async function createContainer(): Promise<void> {
  if (!selectedCustomerId.value || !newContainerName.value.trim()) return;
  saving.value = true;
  try {
    await storageApi.createContainer({
      customer_id: selectedCustomerId.value,
      name: newContainerName.value,
      description: newContainerDescription.value || null
    });
    newContainerName.value = "";
    newContainerDescription.value = "";
    await loadOverview();
    pushToast("收納處已建立。", "success");
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "建立收納處失敗", "error");
  } finally {
    saving.value = false;
  }
}

async function deleteContainer(containerId: number, name: string): Promise<void> {
  if (!selectedCustomerId.value) return;
  const confirmed = await requestConfirmation(`確定刪除收納處「${name}」嗎？其中的位置編號會移回未整理。`, {
    title: "刪除收納處",
    confirmLabel: "刪除",
    tone: "danger"
  });
  if (!confirmed) return;
  try {
    await storageApi.deleteContainer(containerId, selectedCustomerId.value);
    await loadOverview();
    pushToast("收納處已刪除，位置編號已移回未整理。", "success");
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "刪除收納處失敗", "error");
  }
}

async function organizeCodes(): Promise<void> {
  if (!selectedCustomerId.value || selectedCodeIds.value.length === 0) return;
  saving.value = true;
  try {
    overview.value = await storageApi.organizeCodes(
      selectedCustomerId.value,
      selectedCodeIds.value,
      targetContainerId.value
    );
    selectedCodeIds.value = [];
    pushToast("位置編號已完成整理。", "success");
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "整理位置編號失敗", "error");
  } finally {
    saving.value = false;
  }
}

function addPlacement(): void {
  if (!selectedTarget.value || placementDrafts.value.some((row) => row.key === selectedTarget.value)) return;
  const option = targetOptions.value.find((item) => item.value === selectedTarget.value);
  if (!option) return;
  const parts = selectedTarget.value.split(":");
  if (parts[0] === "code") {
    const storageCodeId = Number(parts[1]);
    placementDrafts.value.push({
      key: selectedTarget.value,
      label: option.label,
      target_type: "storage_code",
      storage_code_id: storageCodeId,
      model_id: null,
      station_id: null,
      quantity: null
    });
  } else {
    placementDrafts.value.push({
      key: selectedTarget.value,
      label: option.label,
      target_type: "model_station",
      storage_code_id: null,
      model_id: Number(parts[1]),
      station_id: Number(parts[2]),
      quantity: null
    });
  }
  selectedTarget.value = "";
}

async function syncFixtureFields(): Promise<void> {
  if (!selectedFixtureId.value) return;
  try {
    const detail = await storageApi.syncFixturePlacements(selectedFixtureId.value);
    fixtureDetail.value = detail;
    rebuildDrafts(detail);
    await loadOverview();
    pushToast("已依治具儲位欄位重新解析位置。", "success");
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "重新解析位置失敗", "error");
  }
}

async function savePlacements(): Promise<void> {
  if (!selectedFixtureId.value) return;
  saving.value = true;
  try {
    const detail = await storageApi.replaceFixturePlacements(
      selectedFixtureId.value,
      placementDrafts.value.map(({ key: _key, label: _label, ...row }) => row)
    );
    fixtureDetail.value = detail;
    rebuildDrafts(detail);
    await loadOverview();
    pushToast("治具位置與數量已儲存。", "success");
  } catch (error) {
    pushToast(error instanceof Error ? error.message : "儲存治具位置失敗", "error");
  } finally {
    saving.value = false;
  }
}

watch(selectedCustomerId, () => {
  selectedFixtureId.value = null;
  fixtureDetail.value = null;
  placementDrafts.value = [];
  void loadOverview();
});
watch(selectedFixtureId, () => void loadFixtureDetail());
watch(placementSignature, () => {
  setCustomerSwitchGuard("storage-placements", placementDirty.value, "治具位置分配尚未儲存，確定要離開嗎？");
});
onMounted(() => void loadOverview());
onBeforeUnmount(() => setCustomerSwitchGuard("storage-placements", false, ""));
</script>

<template>
  <section class="storage-page">
    <header class="storage-hero">
      <div>
        <p class="eyebrow">治具收納與位置索引</p>
        <h1>位置字典、收納處與站點數量</h1>
        <p>儲位輸入會以逗號拆分；唯一可判定的站點代碼會保留「機種＋站點」上下文。</p>
      </div>
      <label class="search-field">
        <span>搜尋位置或收納處</span>
        <div class="inline-controls">
          <input v-model="keyword" placeholder="例如 AXG001、機櫃1" @keyup.enter="loadOverview" />
          <button class="outline-btn" type="button" :disabled="loading" @click="loadOverview">搜尋</button>
        </div>
      </label>
    </header>

    <div v-if="!selectedCustomerId" class="empty-state">請先在上方選擇客戶。</div>
    <template v-else>
      <div class="summary-grid">
        <article><span>收納處</span><strong>{{ overview?.containers.length ?? 0 }}</strong></article>
        <article><span>位置編號</span><strong>{{ overview?.codes.length ?? 0 }}</strong></article>
        <article><span>尚未整理</span><strong>{{ overview?.ungrouped_code_count ?? 0 }}</strong></article>
        <article><span>待分配數量</span><strong>{{ overview?.pending_quantity_count ?? 0 }}</strong></article>
      </div>

      <div class="storage-layout">
        <section class="panel">
          <div class="panel-head">
            <div><h2>收納處整理</h2><p>先登記零散編號，再集合到機櫃或其他收納處。</p></div>
          </div>

          <form v-if="canWrite" class="form-row" @submit.prevent="registerCodes">
            <label class="grow"><span>位置編號</span><input v-model="newCodesText" placeholder="AXG001, MOXA001, BNG001" /></label>
            <button class="primary-btn" type="submit" :disabled="saving || !newCodesText.trim()">登記編號</button>
          </form>
          <form v-if="canWrite" class="form-row" @submit.prevent="createContainer">
            <label><span>收納處名稱</span><input v-model="newContainerName" placeholder="機櫃1" /></label>
            <label class="grow"><span>備註</span><input v-model="newContainerDescription" placeholder="選填" /></label>
            <button class="primary-btn" type="submit" :disabled="saving || !newContainerName.trim()">建立</button>
          </form>

          <div v-if="canWrite" class="organize-bar">
            <span>已選 {{ selectedCodeIds.length }} 個位置</span>
            <select v-model="targetContainerId">
              <option :value="null">移至未整理</option>
              <option v-for="container in overview?.containers ?? []" :key="container.id" :value="container.id">{{ container.name }}</option>
            </select>
            <button class="outline-btn" type="button" :disabled="saving || selectedCodeIds.length === 0" @click="organizeCodes">套用收納處</button>
          </div>

          <div class="container-list">
            <article v-for="container in overview?.containers ?? []" :key="container.id" class="container-card">
              <div><strong>{{ container.name }}</strong><small>{{ container.description || "未填備註" }}</small></div>
              <div class="container-metrics"><span>{{ container.code_count }} 個編號</span><span>{{ container.total_quantity }} 個治具</span></div>
              <button v-if="canWrite" class="text-danger" type="button" @click="deleteContainer(container.id, container.name)">刪除</button>
            </article>
          </div>

          <div class="table-wrap">
            <table>
              <thead><tr><th v-if="canWrite">選擇</th><th>位置編號</th><th>收納處</th><th>治具種類</th><th>已分配數量</th><th>待分配</th></tr></thead>
              <tbody>
                <tr v-for="code in overview?.codes ?? []" :key="code.id">
                  <td v-if="canWrite"><input v-model="selectedCodeIds" type="checkbox" :value="code.id" :aria-label="`選擇 ${code.code}`" /></td>
                  <td><strong>{{ code.code }}</strong></td>
                  <td>{{ code.container_name || "未整理" }}</td>
                  <td>{{ code.fixture_type_count }}</td>
                  <td>{{ code.total_quantity }}</td>
                  <td>{{ code.pending_quantity_count }}</td>
                </tr>
                <tr v-if="(overview?.codes.length ?? 0) === 0"><td :colspan="canWrite ? 6 : 5" class="empty-cell">尚無位置編號</td></tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="panel">
          <div class="panel-head"><div><h2>治具位置分配</h2><p>站點位置使用機種＋站點辨認；空白數量代表待分配。</p></div></div>
          <label><span>選擇治具</span>
            <select :value="selectedFixtureId ?? ''" @change="handleFixtureSelection">
              <option value="">請選擇</option>
              <option v-for="fixture in fixtures" :key="fixture.id" :value="fixture.id">{{ fixture.code }} - {{ fixture.name }}</option>
            </select>
          </label>

          <template v-if="fixtureDetail && selectedFixture">
            <div class="fixture-summary">
              <div><span>目前庫存</span><strong>{{ fixtureDetail.stock_qty }}</strong></div>
              <div><span>草稿已分配</span><strong>{{ placementTotal }}</strong></div>
              <div><span>尚未分配</span><strong>{{ Math.max(fixtureDetail.stock_qty - placementTotal, 0) }}</strong></div>
            </div>
            <p class="raw-location">原儲位：{{ [selectedFixture.line_storage_location, selectedFixture.department_storage_location].filter(Boolean).join(", ") || "未填" }}</p>
            <button v-if="canWrite" class="outline-btn" type="button" @click="syncFixtureFields">依原儲位重新解析</button>

            <div v-if="canWrite" class="form-row placement-add">
              <label class="grow"><span>新增位置</span>
                <select v-model="selectedTarget"><option value="">請選擇位置編號或綁定站點</option><option v-for="option in targetOptions" :key="option.value" :value="option.value">{{ option.label }}</option></select>
              </label>
              <button class="outline-btn" type="button" :disabled="!selectedTarget" @click="addPlacement">加入</button>
            </div>

            <div class="placement-list">
              <article v-for="(row, index) in placementDrafts" :key="row.key" class="placement-row">
                <div><strong>{{ row.label }}</strong><small>{{ row.target_type === "model_station" ? "機種站點" : "位置編號" }}</small></div>
                <label><span>數量</span><input v-model.number="row.quantity" type="number" min="0" placeholder="待分配" :readonly="!canWrite" /></label>
                <button v-if="canWrite" class="text-danger" type="button" @click="placementDrafts.splice(index, 1)">移除</button>
              </article>
              <div v-if="placementDrafts.length === 0" class="empty-state">此治具尚未設定位置。</div>
            </div>
            <div v-if="canWrite" class="actions"><button class="primary-btn" type="button" :disabled="saving || placementTotal > fixtureDetail.stock_qty" @click="savePlacements">儲存位置與數量</button></div>
          </template>
        </section>
      </div>
    </template>
  </section>
</template>

<style scoped>
.storage-page { display: grid; gap: 18px; padding: clamp(16px, 2.4vw, 32px); color: #162033; }
.storage-hero { display: flex; justify-content: space-between; gap: 24px; align-items: end; padding: 24px; border: 1px solid #d9e2ef; border-radius: 18px; background: linear-gradient(135deg, #f7fbff, #eef5ff); }
.storage-hero h1, .panel h2 { margin: 4px 0 6px; }
.storage-hero p, .panel p { margin: 0; color: #596579; }
.eyebrow { color: #2368b5 !important; font-weight: 700; letter-spacing: .04em; }
.search-field { min-width: min(390px, 100%); }
label { display: grid; gap: 6px; font-size: 13px; color: #4b5668; }
input, select { min-height: 40px; border: 1px solid #cbd6e4; border-radius: 9px; padding: 8px 10px; background: #fff; color: #162033; }
.inline-controls, .form-row, .organize-bar { display: flex; gap: 10px; align-items: end; }
.grow { flex: 1; }
.summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.summary-grid article { display: grid; gap: 4px; padding: 16px; border: 1px solid #d9e2ef; border-radius: 14px; background: #fff; }
.summary-grid span { color: #687386; font-size: 13px; }
.summary-grid strong { font-size: 26px; }
.storage-layout { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(340px, .75fr); gap: 16px; align-items: start; }
.panel { display: grid; gap: 16px; padding: 20px; border: 1px solid #d9e2ef; border-radius: 16px; background: #fff; box-shadow: 0 8px 30px rgba(42, 67, 102, .06); }
.panel-head { display: flex; justify-content: space-between; gap: 12px; }
.organize-bar { padding: 12px; border-radius: 10px; background: #f3f7fc; }
.organize-bar select { min-width: 160px; }
.container-list, .placement-list { display: grid; gap: 8px; }
.container-card, .placement-row { display: flex; align-items: center; gap: 12px; padding: 12px; border: 1px solid #e1e7f0; border-radius: 11px; }
.container-card > div:first-child, .placement-row > div:first-child { display: grid; flex: 1; }
.container-card small, .placement-row small { color: #778194; }
.container-metrics { display: flex; gap: 10px; color: #596579; font-size: 13px; }
.table-wrap { overflow: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { padding: 10px; border-bottom: 1px solid #e6ebf2; text-align: left; white-space: nowrap; }
th { color: #596579; background: #f8fafc; }
.fixture-summary { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.fixture-summary div { display: grid; padding: 10px; border-radius: 10px; background: #f3f7fc; }
.fixture-summary span { font-size: 12px; color: #687386; }
.fixture-summary strong { font-size: 20px; }
.raw-location { padding: 10px; border-left: 3px solid #6a9bd4; background: #f7faff; }
.placement-row label { width: 100px; }
.placement-row input { width: 100%; }
.actions { display: flex; justify-content: flex-end; }
.primary-btn, .outline-btn { min-height: 40px; border-radius: 9px; padding: 8px 14px; font-weight: 650; cursor: pointer; }
.primary-btn { border: 1px solid #2368b5; background: #2368b5; color: #fff; }
.outline-btn { border: 1px solid #aebdd0; background: #fff; color: #25415f; }
button:disabled { cursor: not-allowed; opacity: .55; }
.text-danger { border: 0; background: transparent; color: #b43a45; cursor: pointer; }
.empty-state, .empty-cell { padding: 18px; text-align: center; color: #778194; }
@media (max-width: 980px) { .storage-hero { align-items: stretch; flex-direction: column; } .summary-grid { grid-template-columns: repeat(2, 1fr); } .storage-layout { grid-template-columns: 1fr; } }
@media (max-width: 620px) { .summary-grid { grid-template-columns: 1fr 1fr; } .form-row, .organize-bar, .container-card, .placement-row { align-items: stretch; flex-direction: column; } .fixture-summary { grid-template-columns: 1fr; } .placement-row label { width: auto; } }
</style>
