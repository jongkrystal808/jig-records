<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { api } from "@/api";
import type { MachineModel } from "@/types";

const props = defineProps<{
  customerId: number | undefined;
  model: MachineModel | null;
  initialCode?: string;
}>();

const emit = defineEmits<{
  saved: [modelId: number];
  cancel: [];
}>();

const saving = ref(false);
const form = ref(makeForm());

function makeForm() {
  return {
    code: props.model?.code ?? props.initialCode ?? "",
    name: props.model?.name ?? "",
    is_active: props.model?.is_active ?? true
  };
}

const isCreateMode = computed(() => props.model === null);

watch(
  () => [props.model, props.initialCode],
  () => {
    form.value = makeForm();
  },
  { deep: true }
);

async function save(): Promise<void> {
  if (!props.customerId) {
    return;
  }
  saving.value = true;
  try {
    if (props.model) {
      const updated = await api.updateModel(props.model.id, {
        customer_id: props.customerId,
        code: form.value.code.trim(),
        name: form.value.name.trim(),
        is_active: form.value.is_active
      });
      emit("saved", updated.id);
      return;
    }

    const created = await api.createModel({
      customer_id: props.customerId,
      code: form.value.code.trim(),
      name: form.value.name.trim()
    });
    emit("saved", created.id);
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <form class="edit-form" @submit.prevent="save">
    <div class="edit-head">
      <div>
        <span class="eyebrow">資料維護</span>
        <h3>{{ isCreateMode ? "新增機種" : `編輯 ${model?.code}` }}</h3>
      </div>
      <button class="outline-btn small" type="button" :disabled="saving" @click="emit('cancel')">取消</button>
    </div>

    <label>
      <span>機種編號 *</span>
      <input v-model="form.code" required autocomplete="off" spellcheck="false" />
    </label>
    <label>
      <span>機種名稱 *</span>
      <input v-model="form.name" required />
    </label>
    <label class="full">
      <span>狀態</span>
      <select v-model="form.is_active">
        <option :value="true">啟用中</option>
        <option :value="false">停用</option>
      </select>
    </label>

    <div class="form-actions">
      <button class="primary-btn" type="submit" :disabled="saving || !customerId">
        {{ saving ? "儲存中..." : isCreateMode ? "建立機種" : "儲存修改" }}
      </button>
    </div>
  </form>
</template>

<style scoped>
.edit-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.edit-head,
.full,
.form-actions {
  grid-column: 1 / -1;
}

.edit-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}

.eyebrow {
  color: #2f6ee5;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h3 {
  margin: 2px 0 0;
  color: #22314a;
  font-size: 18px;
}

label {
  display: grid;
  gap: 6px;
}

span {
  color: #56657f;
  font-size: 12px;
  font-weight: 700;
}

input,
select {
  width: 100%;
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  padding: 8px 10px;
  background: #fff;
  font: inherit;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
}

.primary-btn,
.outline-btn {
  border-radius: 10px;
  font-weight: 700;
  min-height: 36px;
}

.primary-btn {
  border: 1px solid var(--green);
  background: linear-gradient(180deg, #4cc36b 0%, #2ea54e 100%);
  color: #fff;
  padding: 8px 14px;
}

.outline-btn {
  border: 1px solid var(--line-strong);
  background: linear-gradient(180deg, #ffffff 0%, #f7f9fd 100%);
  color: #5b677d;
  padding: 8px 14px;
}

.outline-btn.small {
  min-height: 32px;
  padding: 6px 12px;
}

@media (max-width: 720px) {
  .edit-form {
    grid-template-columns: 1fr;
  }
}
</style>
