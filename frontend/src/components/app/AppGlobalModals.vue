<script setup lang="ts">
import { useRouter } from "vue-router";

import BatchImportPanel from "@/components/inventory/BatchImportPanel.vue";
import InventoryExportPanel from "@/components/inventory/InventoryExportPanel.vue";

const props = defineProps<{
  batchModalOpen: boolean;
  exportModalOpen: boolean;
  customerId: number | undefined;
}>();

const emit = defineEmits<{
  closeBatch: [];
  closeExport: [];
  refreshStats: [];
}>();

const router = useRouter();

async function openInventoryOverview(): Promise<void> {
  emit("closeBatch");
  await router.push("/inventory/overview");
}

// Centralize global modal mounting so App.vue only toggles open state and refresh side effects.
</script>

<template>
  <teleport to="body">
    <div v-if="batchModalOpen" class="ui-modal-backdrop">
      <div class="ui-modal-card" data-tour="inventory-batch-panel">
        <div class="modal-head">
          <div>
            <span class="modal-eyebrow">Global Action</span>
            <h2>收 / 退料</h2>
          </div>
          <div class="modal-head-actions">
            <button class="overview-btn" type="button" @click="openInventoryOverview">收退料總檢視</button>
            <button class="outline-btn" type="button" @click="emit('closeBatch')">關閉</button>
          </div>
        </div>
        <BatchImportPanel
          :customer-id="customerId"
          title="全域收退料匯入"
          description="Modal 只保留批次匯入，方便在任何頁面直接處理收退料。"
          :hide-frame="true"
          @success="emit('refreshStats')"
        />
      </div>
    </div>
    <div v-if="exportModalOpen" class="ui-modal-backdrop">
      <div class="ui-modal-card ui-modal-card--narrow" data-tour="inventory-export-panel">
        <InventoryExportPanel :customer-id="customerId" @close="emit('closeExport')" />
      </div>
    </div>
  </teleport>
</template>

<style scoped>
.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
}

.modal-eyebrow {
  margin: 0;
  color: #2f6ee5;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.modal-head h2 {
  margin: 0;
  color: #1f2b45;
}

.modal-head-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.overview-btn {
  border: 1px solid #d3b07a;
  border-radius: 10px;
  padding: 7px 12px;
  background: linear-gradient(180deg, #fff7e8 0%, #ffebc4 100%);
  color: #8a5610;
  font: inherit;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
}

.overview-btn:hover {
  filter: brightness(0.98);
}

@media (max-width: 640px) {
  .modal-head-actions {
    width: 100%;
  }
}
</style>
