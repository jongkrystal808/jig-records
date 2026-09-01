<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

export type MasterToolbarTab =
  | "fixture"
  | "model"
  | "station"
  | "customer"
  | "user"
  | "ledger"
  | "quality";

const props = defineProps<{
  activeTab: MasterToolbarTab;
  canManageCustomers: boolean;
  canManageUsers: boolean;
  canManageLedger: boolean;
  canManageQuality: boolean;
  loading: boolean;
  hasSelectedCustomer: boolean;
  imageBatchUploading: boolean;
  imageBatchFileCount: number;
}>();

const emit = defineEmits<{
  switchTab: [tab: MasterToolbarTab];
  startTour: [];
  uploadImages: [];
  returnSearch: [];
  exportCsv: [];
  downloadTemplate: [];
  downloadJson: [];
  importCsv: [event: Event];
  imageFilesChange: [event: Event];
}>();

const importInput = ref<HTMLInputElement | null>(null);
const imageInput = ref<HTMLInputElement | null>(null);
const moreMenuOpen = ref(false);
const moreMenuRef = ref<HTMLElement | null>(null);
const supportsCsv = computed(() => ["fixture", "model", "station"].includes(props.activeTab));

function runAndClose(callback: () => void): void {
  moreMenuOpen.value = false;
  callback();
}

function openImportPicker(): void {
  moreMenuOpen.value = false;
  importInput.value?.click();
}

function openImagePicker(): void {
  moreMenuOpen.value = false;
  imageInput.value?.click();
}

function resetImageInput(): void {
  if (imageInput.value) imageInput.value.value = "";
}

function handleDocumentClick(event: MouseEvent): void {
  const target = event.target;
  if (target instanceof Node && !moreMenuRef.value?.contains(target)) {
    moreMenuOpen.value = false;
  }
}

onMounted(() => document.addEventListener("click", handleDocumentClick));
onBeforeUnmount(() => document.removeEventListener("click", handleDocumentClick));
defineExpose({ resetImageInput });
</script>

<template>
  <section class="toolbar panel">
    <label class="mobile-tab-picker">
      <span>目前功能</span>
      <select
        :value="activeTab"
        aria-label="主資料功能"
        @change="emit('switchTab', ($event.target as HTMLSelectElement).value as MasterToolbarTab)"
      >
        <optgroup label="資料維護">
          <option value="fixture">治具資訊</option><option value="model">機種資訊</option><option value="station">站點資訊</option>
        </optgroup>
        <optgroup v-if="canManageCustomers || canManageUsers || canManageLedger || canManageQuality" label="系統管理">
          <option v-if="canManageCustomers" value="customer">客戶</option>
          <option v-if="canManageUsers" value="user">使用者</option>
          <option v-if="canManageLedger" value="ledger">收退料帳目管理</option>
          <option v-if="canManageQuality" value="quality">治具資料品質</option>
        </optgroup>
      </select>
    </label>

    <div class="tab-bar desktop-tab-bar" data-tour="master-tabs">
      <div class="tab-group">
        <span class="tab-group-label">資料維護</span>
        <button class="tab-btn" :class="{ active: activeTab === 'fixture' }" data-tour="master-tab-fixture" @click="emit('switchTab', 'fixture')">治具資訊</button>
        <button class="tab-btn" :class="{ active: activeTab === 'model' }" data-tour="master-tab-model" @click="emit('switchTab', 'model')">機種資訊</button>
        <button class="tab-btn" :class="{ active: activeTab === 'station' }" data-tour="master-tab-station" @click="emit('switchTab', 'station')">站點資訊</button>
      </div>
      <div v-if="canManageCustomers || canManageUsers || canManageLedger || canManageQuality" class="tab-group tab-group-admin">
        <span class="tab-group-label">系統管理</span>
        <button v-if="canManageCustomers" class="tab-btn tab-btn-admin" :class="{ active: activeTab === 'customer' }" data-tour="master-tab-customer" @click="emit('switchTab', 'customer')">客戶</button>
        <button v-if="canManageUsers" class="tab-btn tab-btn-admin" :class="{ active: activeTab === 'user' }" data-tour="master-tab-user" @click="emit('switchTab', 'user')">使用者</button>
        <button v-if="canManageLedger" class="tab-btn tab-btn-admin" :class="{ active: activeTab === 'ledger' }" data-tour="master-tab-ledger" @click="emit('switchTab', 'ledger')">收退料帳目管理</button>
        <button v-if="canManageQuality" class="tab-btn tab-btn-admin" :class="{ active: activeTab === 'quality' }" data-tour="master-tab-quality" @click="emit('switchTab', 'quality')">治具資料品質</button>
      </div>
    </div>

    <div class="toolbar-side">
      <div class="toolbar-actions">
        <button class="outline-btn btn-compact toolbar-primary-action demo-tour-btn desktop-toolbar-action" type="button" :disabled="loading" @click="emit('startTour')">
          {{ hasSelectedCustomer ? "開始新手導覽" : "先選客戶再導覽" }}
        </button>
        <button v-if="activeTab === 'fixture'" class="toolbar-image-btn desktop-toolbar-action" type="button" :disabled="loading || imageBatchUploading || !hasSelectedCustomer" @click="openImagePicker">
          <span class="toolbar-image-btn-title">{{ imageBatchFileCount > 0 ? `已選 ${imageBatchFileCount} 張圖片` : "治具圖片上傳" }}</span>
          <span class="toolbar-image-btn-meta">檔名對應治具編號，最多 50 張 / 每張小於 5 MB</span>
        </button>
        <button v-if="activeTab === 'fixture' && imageBatchFileCount > 0" class="toolbar-image-upload-btn desktop-toolbar-action" type="button" :disabled="loading || imageBatchUploading || !hasSelectedCustomer" @click="emit('uploadImages')">
          {{ imageBatchUploading ? "圖片上傳中..." : `開始上傳 ${imageBatchFileCount} 張` }}
        </button>
        <button class="outline-btn btn-compact toolbar-primary-action desktop-toolbar-action" type="button" @click="emit('returnSearch')">返回搜尋</button>
        <button class="outline-btn btn-compact toolbar-primary-action desktop-toolbar-action" type="button" :disabled="loading || !supportsCsv" @click="emit('exportCsv')">匯出 CSV</button>
        <div ref="moreMenuRef" class="more-menu">
          <button class="outline-btn btn-compact more-menu-trigger" type="button" :disabled="loading" :aria-expanded="moreMenuOpen" @click.stop="moreMenuOpen = !moreMenuOpen">更多操作</button>
          <div v-if="moreMenuOpen" class="more-menu-panel">
            <button class="more-menu-item mobile-more-item" type="button" :disabled="loading" @click="runAndClose(() => emit('startTour'))">開始新手導覽</button>
            <button v-if="activeTab === 'fixture'" class="more-menu-item mobile-more-item" type="button" :disabled="loading || imageBatchUploading || !hasSelectedCustomer" @click="openImagePicker">
              {{ imageBatchFileCount > 0 ? `重新選擇圖片（已選 ${imageBatchFileCount} 張）` : "上傳治具圖片" }}
            </button>
            <button v-if="activeTab === 'fixture' && imageBatchFileCount > 0" class="more-menu-item mobile-more-item mobile-more-item-primary" type="button" :disabled="loading || imageBatchUploading || !hasSelectedCustomer" @click="runAndClose(() => emit('uploadImages'))">
              {{ imageBatchUploading ? "圖片上傳中..." : `開始上傳 ${imageBatchFileCount} 張` }}
            </button>
            <button class="more-menu-item mobile-more-item" type="button" @click="runAndClose(() => emit('returnSearch'))">返回搜尋</button>
            <button class="more-menu-item mobile-more-item" type="button" :disabled="loading || !supportsCsv" @click="runAndClose(() => emit('exportCsv'))">匯出 CSV</button>
            <span class="more-menu-divider mobile-more-item" aria-hidden="true"></span>
            <button class="more-menu-item" type="button" :disabled="loading || !supportsCsv" @click="runAndClose(() => emit('downloadTemplate'))">下載範本</button>
            <button class="more-menu-item" type="button" :disabled="loading || !supportsCsv" @click="openImportPicker">匯入 CSV</button>
            <button class="more-menu-item" type="button" :disabled="loading || activeTab === 'ledger'" @click="runAndClose(() => emit('downloadJson'))">匯出 JSON</button>
          </div>
        </div>
        <input ref="importInput" type="file" accept=".csv,text/csv" class="hidden-input" @change="emit('importCsv', $event)" />
        <input ref="imageInput" type="file" accept="image/png,image/jpeg,image/webp,image/gif" multiple class="hidden-input" @change="emit('imageFilesChange', $event)" />
      </div>
    </div>
  </section>
</template>
