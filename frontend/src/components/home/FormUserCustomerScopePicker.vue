<script setup lang="ts">
import { computed, ref } from "vue";

import type { Customer } from "@/types";

const props = defineProps<{
  customers: Customer[];
  modelValue: number[];
  loading?: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [customerIds: number[]];
  search: [value: string];
}>();

const search = ref("");
const selectedIdSet = computed(() => new Set(props.modelValue));
const selectedCustomers = computed(() => props.customers.filter((customer) => selectedIdSet.value.has(customer.id)));
const filteredCustomers = computed(() => {
  const query = search.value.trim().toLowerCase();
  if (!query) return props.customers;
  return props.customers.filter((customer) =>
    `${customer.code} ${customer.name}`.toLowerCase().includes(query)
  );
});
const allVisibleSelected = computed(() =>
  filteredCustomers.value.length > 0
  && filteredCustomers.value.every((customer) => selectedIdSet.value.has(customer.id))
);

function updateSelection(customerId: number, selected: boolean): void {
  const next = new Set(props.modelValue);
  if (selected) next.add(customerId);
  else next.delete(customerId);
  emit("update:modelValue", [...next]);
}

function selectVisible(): void {
  const next = new Set(props.modelValue);
  filteredCustomers.value.forEach((customer) => next.add(customer.id));
  emit("update:modelValue", [...next]);
}

function clearSelection(): void {
  emit("update:modelValue", []);
}
</script>

<template>
  <section
    class="customer-scope-picker"
    data-tour="form-user-customer-scope"
    aria-label="使用者可存取客戶多選"
  >
    <header class="scope-header">
      <div>
        <strong>可存取客戶</strong>
        <p>可勾選多個，儲存前至少選擇 1 個。</p>
      </div>
      <span class="selected-count" aria-live="polite">已選 {{ modelValue.length }} 個</span>
    </header>

    <div class="scope-tools">
      <label>
        <span class="sr-only">搜尋客戶代碼或名稱</span>
        <input v-model="search" type="search" placeholder="搜尋客戶代碼或名稱" @input="emit('search', search)" />
      </label>
      <button class="scope-action" type="button" :disabled="allVisibleSelected || filteredCustomers.length === 0" @click="selectVisible">
        全選搜尋結果
      </button>
      <button class="scope-action danger" type="button" :disabled="modelValue.length === 0" @click="clearSelection">
        清除全部
      </button>
    </div>

    <div v-if="selectedCustomers.length" class="selected-customers" aria-label="已選客戶">
      <button
        v-for="customer in selectedCustomers"
        :key="`selected-${customer.id}`"
        class="selected-chip"
        type="button"
        :aria-label="`移除 ${customer.code} ${customer.name}`"
        @click="updateSelection(customer.id, false)"
      >
        {{ customer.code }}<span aria-hidden="true">×</span>
      </button>
    </div>
    <p v-else class="scope-warning">尚未選擇客戶，無法儲存使用者。</p>

    <div class="customer-options" role="group" aria-label="客戶選項">
      <label
        v-for="customer in filteredCustomers"
        :key="customer.id"
        :class="{ selected: selectedIdSet.has(customer.id) }"
      >
        <input
          type="checkbox"
          :checked="selectedIdSet.has(customer.id)"
          @change="updateSelection(customer.id, ($event.target as HTMLInputElement).checked)"
        />
        <span>
          <strong>{{ customer.code }}</strong>
          <small>{{ customer.name }}</small>
        </span>
      </label>
      <p v-if="!loading && filteredCustomers.length === 0" class="scope-empty">找不到符合的客戶。</p>
      <p v-if="loading" class="scope-empty" role="status">搜尋中...</p>
    </div>
  </section>
</template>

<style scoped>
.customer-scope-picker { display: grid; gap: 8px; min-width: 360px; padding: 10px; border: 1px solid var(--line-strong); border-radius: 8px; color: var(--text); background: #fff; }
.scope-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.scope-header strong { font-size: 0.78rem; }
.scope-header p { margin: 2px 0 0; color: var(--muted); font-size: 0.68rem; line-height: 1.4; }
.selected-count { flex: none; padding: 3px 7px; border-radius: 999px; color: #1f5eaa; background: #e7f1ff; font-size: 0.68rem; font-weight: 800; }
.scope-tools { display: grid; grid-template-columns: minmax(150px, 1fr) auto auto; gap: 5px; }
.scope-tools input { min-height: 30px; }
.scope-action { min-height: 30px; padding: 0 8px; border: 1px solid var(--line-strong); border-radius: 5px; color: #2d5f9d; background: #f7faff; font: inherit; font-size: 0.68rem; font-weight: 700; cursor: pointer; }
.scope-action.danger { color: #9f3636; }
.scope-action:disabled { opacity: 0.45; cursor: default; }
.selected-customers { display: flex; flex-wrap: wrap; gap: 4px; }
.selected-chip { display: inline-flex; align-items: center; gap: 5px; min-height: 25px; padding: 2px 7px; border: 1px solid #b9d2f2; border-radius: 999px; color: #245d9e; background: #edf5ff; font: inherit; font-size: 0.68rem; font-weight: 750; cursor: pointer; }
.selected-chip span { font-size: 0.9rem; line-height: 1; }
.scope-warning { margin: 0; color: #a05b00; font-size: 0.68rem; font-weight: 750; }
.customer-options { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 5px; max-height: 180px; padding: 2px; overflow-y: auto; }
.customer-options label { display: flex; align-items: center; gap: 7px; min-width: 0; padding: 6px 7px; border: 1px solid var(--line); border-radius: 6px; background: #fbfcfe; cursor: pointer; }
.customer-options label.selected { border-color: #92b9e8; background: #edf5ff; }
.customer-options input { width: 15px; min-width: 15px; min-height: 15px; margin: 0; padding: 0; }
.customer-options label > span { display: grid; min-width: 0; line-height: 1.25; }
.customer-options strong, .customer-options small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.customer-options strong { font-size: 0.72rem; }
.customer-options small { color: var(--muted); font-size: 0.66rem; }
.scope-empty { grid-column: 1 / -1; margin: 8px; color: var(--muted); text-align: center; font-size: 0.7rem; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
@media (max-width: 700px) { .customer-scope-picker { min-width: 300px; } .scope-tools { grid-template-columns: 1fr 1fr; } .scope-tools label { grid-column: 1 / -1; } .customer-options { grid-template-columns: 1fr; } }
</style>
