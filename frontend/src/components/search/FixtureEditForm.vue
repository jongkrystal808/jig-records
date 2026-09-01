<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { api } from "@/api";
import type { AppUser, Fixture } from "@/types";

const props = defineProps<{
  customerId: number | undefined;
  fixture: Fixture | null;
  assignedUsers: AppUser[];
  initialCode?: string;
}>();

const emit = defineEmits<{
  saved: [fixtureId: number];
  cancel: [];
  dirtyChange: [dirty: boolean];
}>();

const saving = ref(false);
const form = ref(makeForm());
const initialSnapshot = ref("");

function makeForm() {
  return {
    code: props.fixture?.code ?? props.initialCode ?? "",
    name: props.fixture?.name ?? "",
    line_storage_location: props.fixture?.line_storage_location ?? "",
    department_storage_location: props.fixture?.department_storage_location ?? "",
    min_stock_qty: props.fixture?.min_stock_qty ?? 0,
    responsible_user_id: props.fixture?.responsible_user_id ?? null,
    description: props.fixture?.description ?? "",
    is_active: props.fixture?.is_active ?? true
  };
}

function serializeForm(value: ReturnType<typeof makeForm>): string {
  return JSON.stringify(value);
}

const isCreateMode = computed(() => props.fixture === null);

watch(
  () => [props.fixture, props.initialCode],
  () => {
    form.value = makeForm();
    initialSnapshot.value = serializeForm(form.value);
    emit("dirtyChange", false);
  },
  { deep: true, immediate: true }
);

watch(
  form,
  (value) => {
    emit("dirtyChange", serializeForm(value) !== initialSnapshot.value);
  },
  { deep: true }
);

async function save(): Promise<void> {
  if (!props.customerId) {
    return;
  }
  saving.value = true;
  try {
    if (props.fixture) {
      const updated = await api.updateFixture(props.fixture.id, {
        customer_id: props.customerId,
        code: form.value.code.trim(),
        name: form.value.name.trim(),
        line_storage_location: form.value.line_storage_location.trim() || null,
        department_storage_location: form.value.department_storage_location.trim() || null,
        min_stock_qty: Math.max(0, Number(form.value.min_stock_qty) || 0),
        responsible_user_id: form.value.responsible_user_id,
        description: form.value.description.trim() || "",
        is_active: form.value.is_active
      });
      emit("saved", updated.id);
      return;
    }

    const created = await api.createFixture({
      customer_id: props.customerId,
      code: form.value.code.trim(),
      name: form.value.name.trim(),
      line_storage_location: form.value.line_storage_location.trim() || null,
      department_storage_location: form.value.department_storage_location.trim() || null,
      min_stock_qty: Math.max(0, Number(form.value.min_stock_qty) || 0),
      responsible_user_id: form.value.responsible_user_id,
      description: form.value.description.trim() || ""
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
        <h3>{{ isCreateMode ? "新增治具" : `編輯 ${fixture?.code}` }}</h3>
      </div>
      <button class="outline-btn btn-sm" type="button" :disabled="saving" @click="emit('cancel')">取消</button>
    </div>

    <label>
      <span>治具編號 *</span>
      <input v-model="form.code" required autocomplete="off" spellcheck="false" />
    </label>
    <label>
      <span>治具名稱 *</span>
      <input v-model="form.name" required />
    </label>
    <label>
      <span>產線儲位</span>
      <input v-model="form.line_storage_location" placeholder="T2, AXG001, MOXA001" />
    </label>
    <label>
      <span>部門儲位</span>
      <input v-model="form.department_storage_location" placeholder="RD-SHELF-3, BNG001" />
    </label>
    <label>
      <span>最低水位</span>
      <input v-model.number="form.min_stock_qty" type="number" min="0" />
    </label>
    <label>
      <span>負責人</span>
      <select v-model="form.responsible_user_id">
        <option :value="null">未指定</option>
        <option v-for="user in assignedUsers.filter((row) => row.is_active)" :key="user.id" :value="user.id">
          {{ user.display_name }}
        </option>
      </select>
    </label>
    <label>
      <span>狀態</span>
      <select v-model="form.is_active">
        <option :value="true">啟用中</option>
        <option :value="false">停用</option>
      </select>
    </label>
    <label class="full">
      <span>備註</span>
      <textarea v-model="form.description" rows="4"></textarea>
    </label>

    <div class="form-actions">
      <button class="primary-btn" type="submit" :disabled="saving || !customerId">
        {{ saving ? "儲存中..." : isCreateMode ? "建立治具" : "儲存修改" }}
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
.form-actions,
.full {
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
select,
textarea {
  width: 100%;
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  padding: 8px 10px;
  background: #fff;
  font: inherit;
}

textarea {
  resize: vertical;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 720px) {
  .edit-form {
    grid-template-columns: 1fr;
  }
}
</style>
