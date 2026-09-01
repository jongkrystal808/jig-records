<script setup lang="ts">
import { computed, ref } from "vue";

import type { InventoryReportMobileRow } from "@/components/inventory/InventoryReportMobileCards.vue";

const props = defineProps<{
  row: InventoryReportMobileRow;
}>();

const emit = defineEmits<{
  quickTransaction: [mode: "receipt" | "return"];
  editFixture: [];
  viewProduction: [];
}>();

const detailsRef = ref<HTMLDetailsElement | null>(null);
const hasProductionContext = computed(() => Boolean(props.row.modelId && props.row.stationId));

function select(action: () => void): void {
  detailsRef.value?.removeAttribute("open");
  action();
}
</script>

<template>
  <details ref="detailsRef" class="fixture-row-actions">
    <summary>更多操作</summary>
    <div class="fixture-row-action-menu">
      <button type="button" @click="select(() => emit('quickTransaction', 'receipt'))">快速收料</button>
      <button type="button" @click="select(() => emit('quickTransaction', 'return'))">快速退料</button>
      <button type="button" @click="select(() => emit('editFixture'))">編輯治具</button>
      <button
        type="button"
        :disabled="!hasProductionContext"
        :title="hasProductionContext ? '查看此列的相關機種與站點' : '此治具尚未配置機種與站點'"
        @click="select(() => emit('viewProduction'))"
      >
        查看產能
      </button>
    </div>
  </details>
</template>

<style scoped>
.fixture-row-actions {
  position: relative;
  display: inline-block;
}

.fixture-row-actions summary {
  min-height: 30px;
  padding: 5px 9px;
  border: 1px solid #b9c9df;
  border-radius: 6px;
  color: #245da9;
  background: #fff;
  font-size: 0.72rem;
  font-weight: 800;
  cursor: pointer;
  list-style: none;
  white-space: nowrap;
}

.fixture-row-actions summary::-webkit-details-marker { display: none; }
.fixture-row-actions summary::after { content: " ▾"; }
.fixture-row-actions[open] summary::after { content: " ▴"; }

.fixture-row-action-menu {
  position: absolute;
  right: 0;
  z-index: 8;
  display: grid;
  width: 140px;
  margin-top: 4px;
  padding: 5px;
  border: 1px solid #c8d5e7;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 10px 26px rgba(26, 48, 82, 0.18);
}

.fixture-row-action-menu button {
  padding: 7px 9px;
  border: 0;
  border-radius: 5px;
  color: #253b5d;
  background: transparent;
  text-align: left;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
}

.fixture-row-action-menu button:hover:not(:disabled),
.fixture-row-action-menu button:focus-visible:not(:disabled) {
  color: #174f9d;
  background: #edf4ff;
}

.fixture-row-action-menu button:disabled {
  color: #98a3b3;
  cursor: not-allowed;
}

@media (max-width: 680px) {
  .fixture-row-actions { width: 100%; }
  .fixture-row-actions summary { width: 100%; text-align: center; }
  .fixture-row-action-menu { position: static; width: 100%; box-shadow: none; }
}
</style>
