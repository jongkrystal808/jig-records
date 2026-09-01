import type { Ref } from "vue";

import { api } from "@/api";
import { pushToast } from "@/toastState";

type MasterCrudTab = "fixture" | "model" | "station" | "customer" | "user" | "ledger" | "quality";
type FixtureForm = {
  code: string;
  name: string;
  responsible_user_id: number | null;
  line_storage_location: string;
  department_storage_location: string;
  min_stock_qty: number;
  description: string;
  is_active: boolean;
};
type SimpleMasterForm = { code: string; name: string; is_active: boolean };
type CustomerForm = { code: string; name: string };
type UserForm = {
  username: string;
  email: string;
  display_name: string;
  role: string;
  is_active: boolean;
  password: string;
  reset_password: string;
  allowed_customer_ids: number[];
};

export function useMasterCrudActions(options: {
  activeTab: Ref<MasterCrudTab>;
  selectedCustomerId: Ref<number | null>;
  selectedFixtureId: Ref<number | null>;
  selectedModelId: Ref<number | null>;
  selectedStationId: Ref<number | null>;
  selectedCustomerRowId: Ref<number | null>;
  selectedUserId: Ref<number | null>;
  fixtureForm: Ref<FixtureForm>;
  modelForm: Ref<SimpleMasterForm>;
  stationForm: Ref<SimpleMasterForm>;
  customerForm: Ref<CustomerForm>;
  userForm: Ref<UserForm>;
  customerAssignedUserIds: Ref<number[]>;
  saving: Ref<boolean>;
  reloadSelection: () => Promise<void>;
  finishEditing: () => void;
}) {
  function requireCustomer(message = "請先選擇客戶。"): number | null {
    if (options.selectedCustomerId.value) return options.selectedCustomerId.value;
    pushToast(message, "warning");
    return null;
  }

  function fixturePayload(customerId: number, isActive = options.fixtureForm.value.is_active) {
    const form = options.fixtureForm.value;
    return {
      customer_id: customerId,
      responsible_user_id: form.responsible_user_id,
      code: form.code.trim(),
      name: form.name.trim(),
      line_storage_location: form.line_storage_location.trim() || undefined,
      department_storage_location: form.department_storage_location.trim() || undefined,
      min_stock_qty: form.min_stock_qty,
      description: form.description.trim() || undefined,
      is_active: isActive
    };
  }

  async function saveCurrent(): Promise<void> {
    const isUpdate =
      (options.activeTab.value === "fixture" && options.selectedFixtureId.value !== null) ||
      (options.activeTab.value === "model" && options.selectedModelId.value !== null) ||
      (options.activeTab.value === "station" && options.selectedStationId.value !== null) ||
      (options.activeTab.value === "customer" && options.selectedCustomerRowId.value !== null) ||
      (options.activeTab.value === "user" && options.selectedUserId.value !== null);
    options.saving.value = true;
    try {
      if (options.activeTab.value === "fixture") {
        const customerId = requireCustomer("請先在側邊欄選擇客戶。");
        if (!customerId) return;
        const fixture = options.selectedFixtureId.value
          ? await api.updateFixture(options.selectedFixtureId.value, fixturePayload(customerId))
          : await api.createFixture(fixturePayload(customerId));
        options.selectedFixtureId.value = fixture.id;
      } else if (options.activeTab.value === "model") {
        const customerId = requireCustomer();
        if (!customerId) return;
        const form = options.modelForm.value;
        const model = options.selectedModelId.value
          ? await api.updateModel(options.selectedModelId.value, {
              customer_id: customerId,
              code: form.code.trim(),
              name: form.name.trim(),
              is_active: form.is_active
            })
          : await api.createModel({ customer_id: customerId, code: form.code.trim(), name: form.name.trim() });
        options.selectedModelId.value = model.id;
      } else if (options.activeTab.value === "station") {
        const customerId = requireCustomer();
        if (!customerId) return;
        const form = options.stationForm.value;
        const station = options.selectedStationId.value
          ? await api.updateStation(options.selectedStationId.value, {
              customer_id: customerId,
              code: form.code.trim(),
              name: form.name.trim(),
              is_active: form.is_active
            })
          : await api.createStation({ customer_id: customerId, code: form.code.trim(), name: form.name.trim() });
        options.selectedStationId.value = station.id;
      } else if (options.activeTab.value === "customer") {
        const form = options.customerForm.value;
        const assignedUserIds = [...options.customerAssignedUserIds.value].sort((a, b) => a - b);
        const customer = options.selectedCustomerRowId.value
          ? await api.updateCustomer(options.selectedCustomerRowId.value, {
              code: form.code.trim(),
              name: form.name.trim(),
              assigned_user_ids: assignedUserIds
            })
          : await api.createCustomer({
              code: form.code.trim(),
              name: form.name.trim(),
              assigned_user_ids: assignedUserIds
            });
        if (!options.selectedCustomerRowId.value) options.selectedCustomerId.value = customer.id;
        options.selectedCustomerRowId.value = customer.id;
      } else if (options.activeTab.value === "user") {
        const form = options.userForm.value;
        const allowedCustomerIds = [...new Set(form.allowed_customer_ids)].sort((a, b) => a - b);
        if (allowedCustomerIds.length === 0) {
          pushToast("請至少選擇一個可存取客戶。", "warning");
          return;
        }
        if (options.selectedUserId.value) {
          const user = await api.updateUser(options.selectedUserId.value, {
            email: form.email.trim() || null,
            display_name: form.display_name.trim(),
            role: form.role,
            is_active: form.is_active,
            allowed_customer_ids: allowedCustomerIds
          });
          options.selectedUserId.value = user.id;
        } else {
          if (!form.password.trim()) {
            pushToast("新增使用者時必須輸入密碼。", "warning");
            return;
          }
          const user = await api.createUser({
            username: form.username.trim(),
            email: form.email.trim() || null,
            password: form.password.trim(),
            display_name: form.display_name.trim(),
            role: form.role,
            is_active: form.is_active,
            allowed_customer_ids: allowedCustomerIds
          });
          options.selectedUserId.value = user.id;
        }
      }
      await options.reloadSelection();
      options.finishEditing();
      pushToast(isUpdate ? "更新完成。" : "新增完成。", "success");
    } catch (error) {
      pushToast(error instanceof Error ? error.message : "儲存失敗", "error");
    } finally {
      options.saving.value = false;
    }
  }

  async function toggleCurrentActive(): Promise<void> {
    const active =
      options.activeTab.value === "fixture"
        ? options.fixtureForm.value.is_active
        : options.activeTab.value === "model"
          ? options.modelForm.value.is_active
          : options.activeTab.value === "station"
            ? options.stationForm.value.is_active
            : options.userForm.value.is_active;
    const nextActive = !active;
    options.saving.value = true;
    try {
      if (options.activeTab.value === "fixture" && options.selectedFixtureId.value) {
        const customerId = requireCustomer("請先在側邊欄選擇客戶。");
        if (!customerId) return;
        await api.updateFixture(options.selectedFixtureId.value, fixturePayload(customerId, nextActive));
      } else if (options.activeTab.value === "model" && options.selectedModelId.value) {
        const customerId = requireCustomer();
        if (!customerId) return;
        const form = options.modelForm.value;
        await api.updateModel(options.selectedModelId.value, {
          customer_id: customerId,
          code: form.code.trim(),
          name: form.name.trim(),
          is_active: nextActive
        });
      } else if (options.activeTab.value === "station" && options.selectedStationId.value) {
        const customerId = requireCustomer();
        if (!customerId) return;
        const form = options.stationForm.value;
        await api.updateStation(options.selectedStationId.value, {
          customer_id: customerId,
          code: form.code.trim(),
          name: form.name.trim(),
          is_active: nextActive
        });
      } else if (options.activeTab.value === "user" && options.selectedUserId.value) {
        const form = options.userForm.value;
        await api.updateUser(options.selectedUserId.value, {
          email: form.email.trim() || null,
          display_name: form.display_name.trim(),
          role: form.role,
          is_active: nextActive,
          allowed_customer_ids: [...new Set(form.allowed_customer_ids)].sort((a, b) => a - b)
        });
      } else {
        pushToast(options.activeTab.value === "customer" ? "客戶分頁不提供停用。" : "請先選擇要調整狀態的資料。", "warning");
        return;
      }
      await options.reloadSelection();
      options.finishEditing();
      pushToast(nextActive ? "已恢復使用。" : "停用完成。", "success");
    } catch (error) {
      pushToast(error instanceof Error ? error.message : "狀態更新失敗", "error");
    } finally {
      options.saving.value = false;
    }
  }

  return { saveCurrent, toggleCurrentActive };
}
