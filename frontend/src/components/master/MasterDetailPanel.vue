<script setup lang="ts">
import UiFormActions from "@/components/UiFormActions.vue";
import UiSectionHeader from "@/components/UiSectionHeader.vue";
import UiStatusPill from "@/components/UiStatusPill.vue";
import type { AppUser, Customer } from "@/types";
import { formatLocalDate } from "@/utils/date";

type MasterTab = "fixture" | "model" | "station" | "customer" | "user";

const props = defineProps<{
  activeTab: MasterTab;
  tabTitle: string;
  isCreateMode: boolean;
  selectedDetailLabel: string;
  selectedStatusBadge: { label: string; tone: "active" | "inactive" } | null;
  saving: boolean;
  toggleActionLabel: string;
  canManageCustomers: boolean;
  canManageUsers: boolean;
  canDeleteFixture: boolean;
  selectedFixtureId: number | null;
  selectedUserId: number | null;
  selectedCustomerScopeCount: number;
  selectedCustomerRow: Customer | null;
  selectedUser: AppUser | null;
  customerAssignedUsers: AppUser[];
  users: AppUser[];
  fixtureForm: {
    code: string;
    name: string;
    responsible_user_id: number | null;
    line_storage_location: string;
    department_storage_location: string;
    min_stock_qty: number;
    description: string;
    is_active: boolean;
  };
  modelForm: {
    code: string;
    name: string;
    is_active: boolean;
  };
  stationForm: {
    code: string;
    name: string;
    is_active: boolean;
  };
  customerForm: {
    code: string;
    name: string;
  };
  userForm: {
    username: string;
    email: string;
    display_name: string;
    role: string;
    is_active: boolean;
    password: string;
    reset_password: string;
  };
  onStartCreate: () => void;
  onReloadSelection: () => void;
  onSaveCurrent: () => void | Promise<void>;
  onToggleCurrentActive: () => void | Promise<void>;
  onRequestDeleteFixture: () => void;
  onResetUserPassword: () => void | Promise<void>;
  onToggleAssignedUser: (userId: number, checked: boolean) => void;
  onHasAssignedUser: (userId: number) => boolean;
}>();
</script>

<template>
  <article class="panel detail-panel" :class="{ 'detail-panel-create': isCreateMode }">
    <UiSectionHeader class="panel-head" :class="{ 'panel-head-create': isCreateMode }" :title="`${tabTitle}詳細資料`" :description="isCreateMode ? '新增資料' : selectedDetailLabel">
      <template #actions>
        <span v-if="isCreateMode" class="mode-chip mode-chip-create">新增模式</span>
        <UiStatusPill v-if="selectedStatusBadge" class="status-legend" :label="selectedStatusBadge.label" :tone="selectedStatusBadge.tone" />
        <div class="action-group detail-head-actions">
          <button class="outline-btn small" type="button" :disabled="saving" @click="onStartCreate">新增</button>
          <button class="ghost-btn small action-divider-btn" type="button" :disabled="saving || isCreateMode" @click="onReloadSelection">重載</button>
        </div>
      </template>
    </UiSectionHeader>

    <form class="detail-form" data-tour="master-detail-form" @submit.prevent="onSaveCurrent">
      <template v-if="activeTab === 'fixture'">
        <label>
          <span>治具編號 *</span>
          <input v-model="fixtureForm.code" required />
        </label>
        <label><span>治具名稱 *</span><input v-model="fixtureForm.name" required /></label>
        <label><span>產線儲位</span><input v-model="fixtureForm.line_storage_location" placeholder="A-01-03" /></label>
        <label><span>部門儲位</span><input v-model="fixtureForm.department_storage_location" placeholder="RD-SHELF-3" /></label>
        <label><span>最低水位</span><input v-model.number="fixtureForm.min_stock_qty" type="number" min="0" /></label>
        <label>
          <span>負責人</span>
          <select v-model="fixtureForm.responsible_user_id">
            <option :value="null">未指定</option>
            <option v-for="user in customerAssignedUsers.filter((row) => row.is_active)" :key="user.id" :value="user.id">{{ user.display_name }}</option>
          </select>
        </label>
        <label>
          <span>狀態</span>
          <select v-model="fixtureForm.is_active">
            <option :value="true">啟用中</option>
            <option :value="false">停用</option>
          </select>
        </label>
        <label class="full"><span>備註</span><textarea v-model="fixtureForm.description" rows="4" placeholder="輸入備註內容..." /></label>
      </template>

      <template v-else-if="activeTab === 'model'">
        <label><span>機種編號 *</span><input v-model="modelForm.code" required /></label>
        <label><span>機種名稱 *</span><input v-model="modelForm.name" required /></label>
        <label class="full">
          <span>狀態</span>
          <select v-model="modelForm.is_active">
            <option :value="true">啟用中</option>
            <option :value="false">停用</option>
          </select>
        </label>
      </template>

      <template v-else-if="activeTab === 'station'">
        <label><span>站點編號 *</span><input v-model="stationForm.code" required /></label>
        <label><span>站點名稱 *</span><input v-model="stationForm.name" required /></label>
        <label class="full">
          <span>狀態</span>
          <select v-model="stationForm.is_active">
            <option :value="true">啟用中</option>
            <option :value="false">停用</option>
          </select>
        </label>
      </template>

      <template v-else-if="activeTab === 'customer' && canManageCustomers">
        <label><span>客戶代碼 *</span><input v-model="customerForm.code" required /></label>
        <label><span>客戶名稱 *</span><input v-model="customerForm.name" required /></label>
        <div class="full role-scope-panel">
          <span>指派使用者</span>
          <div class="customer-scope-panel">
            <div class="customer-scope-summary">已選 {{ selectedCustomerScopeCount }} 位使用者</div>
            <div class="customer-scope-list">
              <label v-for="user in users" :key="user.id" class="customer-scope-item">
                <input class="customer-scope-checkbox" :checked="onHasAssignedUser(user.id)" type="checkbox" @change="onToggleAssignedUser(user.id, ($event.target as HTMLInputElement).checked)" />
                <span class="customer-scope-indicator" :class="{ selected: onHasAssignedUser(user.id) }" aria-hidden="true"></span>
                <span class="customer-scope-text">
                  <strong>{{ user.display_name }}</strong>
                  <small>{{ user.username }}</small>
                </span>
              </label>
            </div>
          </div>
        </div>
        <label class="full"><span>建立時間</span><input :value="formatLocalDate(selectedCustomerRow?.created_at)" disabled /></label>
        <label class="full"><span>更新時間</span><input :value="formatLocalDate(selectedCustomerRow?.updated_at)" disabled /></label>
      </template>

      <template v-else-if="canManageUsers">
        <label><span>帳號 *</span><input v-model="userForm.username" :disabled="selectedUserId !== null" required /></label>
        <label><span>Email</span><input v-model="userForm.email" type="email" placeholder="name@example.com" /></label>
        <label><span>顯示名稱 *</span><input v-model="userForm.display_name" required /></label>
        <label><span>角色</span><select v-model="userForm.role"><option value="admin">Admin</option><option value="user">User</option></select></label>
        <label><span>狀態</span><select v-model="userForm.is_active"><option :value="true">啟用中</option><option :value="false">停用</option></select></label>
        <label v-if="selectedUserId === null" class="full"><span>登入密碼 *</span><input v-model="userForm.password" type="password" minlength="6" required /></label>
        <label class="full"><span>建立時間</span><input :value="formatLocalDate(selectedUser?.created_at)" disabled /></label>
        <label class="full"><span>更新時間</span><input :value="formatLocalDate(selectedUser?.updated_at)" disabled /></label>
        <label v-if="selectedUserId !== null" class="full">
          <span>重設密碼</span>
          <div class="inline-action">
            <input v-model="userForm.reset_password" type="password" minlength="6" placeholder="輸入新密碼" />
            <button class="outline-btn" type="button" @click="onResetUserPassword">重設密碼</button>
          </div>
        </label>
      </template>

      <UiFormActions
        class="form-actions-full"
        data-tour="master-form-actions"
        :editing="!isCreateMode"
        :saving="saving"
        submit-label="儲存"
        saving-label="儲存中..."
        cancel-label="取消"
        :delete-label="toggleActionLabel"
        :show-delete="activeTab !== 'customer'"
        :state-text="isCreateMode ? '新增模式' : '編輯模式'"
        @cancel="onStartCreate"
        @delete="onToggleCurrentActive"
      />
      <div v-if="activeTab === 'fixture' && canDeleteFixture && !isCreateMode" class="fixture-delete-zone">
        <div>
          <strong>永久刪除治具</strong>
          <small>此操作不可復原，執行前可選擇是否一併刪除相關收退料記錄。</small>
        </div>
        <button class="fixture-delete-btn" type="button" :disabled="saving" @click="onRequestDeleteFixture">永久刪除</button>
      </div>

    </form>
  </article>
</template>

<style scoped>
.panel {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
  padding: 10px;
  min-width: 0;
  min-height: 0;
}

.detail-panel {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 8px;
  overflow: auto;
}

.detail-panel-create {
  border-color: rgba(224, 138, 30, 0.28);
  background: linear-gradient(180deg, rgba(255, 252, 246, 0.98) 0%, rgba(255, 248, 237, 0.96) 100%);
  box-shadow: inset 0 0 0 1px rgba(255, 244, 220, 0.7);
}

.panel-head-create {
  padding: 10px 12px;
  margin: -2px -2px 0;
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(255, 243, 220, 0.95) 0%, rgba(255, 249, 237, 0.92) 100%);
  border: 1px solid rgba(224, 138, 30, 0.18);
}

.status-legend {
  align-self: center;
}

.mode-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.mode-chip-create {
  color: #8f4b00;
  background: rgba(255, 239, 207, 0.95);
  border: 1px solid rgba(224, 138, 30, 0.24);
}

.fixture-delete-zone {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px;
  border: 1px solid #efc0c0;
  border-radius: 10px;
  background: #fff8f8;
}

.fixture-delete-zone div {
  display: grid;
  gap: 3px;
}

.fixture-delete-zone strong {
  color: #9f2f2f;
  font-size: 12px;
}

.fixture-delete-zone small {
  color: #7f5555;
  font-size: 11px;
}

.fixture-delete-btn {
  border: 1px solid #bd3e3e;
  border-radius: 8px;
  padding: 6px 10px;
  color: #fff;
  background: #bd3e3e;
  font: inherit;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.fixture-delete-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}


.action-group {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.detail-head-actions {
  align-items: center;
}

.action-divider-btn {
  margin-left: 8px;
}

.detail-form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 8px;
  align-content: start;
}

.detail-form label {
  display: grid;
  gap: 6px;
}

.detail-form label.full {
  grid-column: 1 / -1;
}

.detail-form span {
  color: #56657f;
  font-size: 12px;
  font-weight: 700;
}

.form-actions-full {
  grid-column: 1 / -1;
}

input,
select,
textarea {
  width: 100%;
  border: 1px solid var(--line-strong);
  border-radius: 8px;
  padding: 5px 8px;
  background: #fff;
  font: inherit;
  font-size: 12px;
}

textarea {
  resize: vertical;
}

.inline-action {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 6px;
}

.role-scope-panel {
  display: grid;
  gap: 6px;
}

.customer-scope-panel {
  display: grid;
  gap: 8px;
}

.customer-scope-summary {
  color: #5d6d89;
  font-size: 12px;
  font-weight: 700;
}

.customer-scope-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 10px;
  background: #fbfcff;
  max-height: 220px;
  overflow: auto;
}

.customer-scope-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  min-width: 0;
  padding: 8px 10px;
  border: 1px solid #d9e3f2;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
}

.customer-scope-item:hover {
  border-color: #b8c9e6;
  background: #f8fbff;
}

.customer-scope-checkbox {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.customer-scope-indicator {
  width: 16px;
  height: 16px;
  margin-top: 2px;
  flex: 0 0 16px;
  border-radius: 999px;
  border: 2px solid #d24b4b;
  background: #fff;
  box-shadow: inset 0 0 0 3px #fff;
}

.customer-scope-indicator.selected {
  background: #d24b4b;
}

.customer-scope-text {
  color: #22314a;
  display: grid;
  gap: 2px;
  min-width: 0;
  line-height: 1.4;
}

.customer-scope-text strong,
.customer-scope-text small {
  display: block;
  min-width: 0;
  overflow-wrap: anywhere;
}

.customer-scope-text strong {
  font-size: 13px;
  font-weight: 700;
}

.customer-scope-text small {
  color: #5d6d89;
  font-size: 11px;
}

.outline-btn,
.ghost-btn {
  border-radius: 10px;
  font-weight: 700;
  cursor: pointer;
  min-height: 30px;
  font-size: 12px;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease, filter 0.15s ease;
}

.outline-btn {
  border: 1px solid var(--line-strong);
  background: linear-gradient(180deg, #ffffff 0%, #f7f9fd 100%);
  color: #5b677d;
  padding: 6px 10px;
}

.outline-btn.small,
.ghost-btn.small {
  padding: 5px 8px;
  min-height: 28px;
}

.ghost-btn {
  border: 1px solid transparent;
  background: transparent;
  color: #5b677d;
  padding: 6px 10px;
}

.outline-btn:hover,
.ghost-btn:hover {
  transform: translateY(-1px);
}

.outline-btn:hover {
  border-color: #c0cad9;
  box-shadow: 0 4px 12px rgba(28, 47, 84, 0.08);
}

.ghost-btn:hover {
  color: #324462;
}

.outline-btn:disabled,
.ghost-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.outline-btn:active,
.ghost-btn:active {
  transform: translateY(0);
}

@media (max-width: 900px) {
  .detail-form,
  .customer-scope-list {
    grid-template-columns: 1fr;
  }
}
</style>
