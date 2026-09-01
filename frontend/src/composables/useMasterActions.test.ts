import { computed, ref } from "vue";
import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "@/api";
import { useMasterCrudActions } from "./useMasterCrudActions";
import { useMasterEntityDeletion } from "./useMasterEntityDeletion";

vi.mock("@/api", () => ({ api: {} }));
vi.mock("@/toastState", () => ({ pushToast: vi.fn() }));

afterEach(() => vi.clearAllMocks());

function createCrudOptions() {
  return {
    activeTab: ref<"fixture" | "model" | "station" | "customer" | "user" | "ledger" | "quality">("fixture"),
    selectedCustomerId: ref<number | null>(3),
    selectedFixtureId: ref<number | null>(11),
    selectedModelId: ref<number | null>(null),
    selectedStationId: ref<number | null>(null),
    selectedCustomerRowId: ref<number | null>(null),
    selectedUserId: ref<number | null>(null),
    fixtureForm: ref({
      code: " FX-011 ",
      name: "治具十一",
      responsible_user_id: null,
      line_storage_location: " A-1 ",
      department_storage_location: "",
      min_stock_qty: 2,
      description: "",
      is_active: true
    }),
    modelForm: ref({ code: "", name: "", is_active: true }),
    stationForm: ref({ code: "", name: "", is_active: true }),
    customerForm: ref({ code: "", name: "" }),
    userForm: ref({ username: "", email: "", display_name: "", role: "user", is_active: true, password: "", reset_password: "", allowed_customer_ids: [] as number[] }),
    customerAssignedUserIds: ref<number[]>([]),
    saving: ref(false),
    reloadSelection: vi.fn().mockResolvedValue(undefined),
    finishEditing: vi.fn()
  };
}

describe("Master action composables", () => {
  it("updates the selected fixture and returns the editor to summary", async () => {
    const updateFixture = vi.fn().mockResolvedValue({ id: 11 });
    Object.assign(api, { updateFixture });
    const options = createCrudOptions();
    const actions = useMasterCrudActions(options);

    await actions.saveCurrent();

    expect(updateFixture).toHaveBeenCalledWith(11, expect.objectContaining({
      customer_id: 3,
      code: "FX-011",
      line_storage_location: "A-1",
      is_active: true
    }));
    expect(options.reloadSelection).toHaveBeenCalledOnce();
    expect(options.finishEditing).toHaveBeenCalledOnce();
    expect(options.saving.value).toBe(false);
  });

  it("preserves customer access while editing a user", async () => {
    const updateUser = vi.fn().mockResolvedValue({ id: 21 });
    Object.assign(api, { updateUser });
    const options = createCrudOptions();
    options.activeTab.value = "user";
    options.selectedUserId.value = 21;
    options.userForm.value = {
      username: "operator",
      email: "operator@example.com",
      display_name: "Updated Operator",
      role: "user",
      is_active: true,
      password: "",
      reset_password: "",
      allowed_customer_ids: [8, 3]
    };
    const actions = useMasterCrudActions(options);

    await actions.saveCurrent();

    expect(updateUser).toHaveBeenCalledWith(21, expect.objectContaining({
      display_name: "Updated Operator",
      allowed_customer_ids: [3, 8]
    }));
  });

  it("preserves customer access while toggling a user", async () => {
    const updateUser = vi.fn().mockResolvedValue({ id: 21 });
    Object.assign(api, { updateUser });
    const options = createCrudOptions();
    options.activeTab.value = "user";
    options.selectedUserId.value = 21;
    options.userForm.value = {
      username: "operator",
      email: "operator@example.com",
      display_name: "Operator",
      role: "admin",
      is_active: true,
      password: "",
      reset_password: "",
      allowed_customer_ids: [8, 3]
    };
    const actions = useMasterCrudActions(options);

    await actions.toggleCurrentActive();

    expect(updateUser).toHaveBeenCalledWith(21, expect.objectContaining({
      is_active: false,
      allowed_customer_ids: [3, 8]
    }));
  });

  it("does not save a user without customer access", async () => {
    const updateUser = vi.fn().mockResolvedValue({ id: 21 });
    Object.assign(api, { updateUser });
    const options = createCrudOptions();
    options.activeTab.value = "user";
    options.selectedUserId.value = 21;
    options.userForm.value = {
      username: "operator",
      email: "",
      display_name: "Operator",
      role: "user",
      is_active: true,
      password: "",
      reset_password: "",
      allowed_customer_ids: []
    };
    const actions = useMasterCrudActions(options);

    await actions.saveCurrent();

    expect(updateUser).not.toHaveBeenCalled();
    expect(options.reloadSelection).not.toHaveBeenCalled();
  });

  it("deletes a fixture, moves an empty last page back, and reloads selection", async () => {
    const deleteFixture = vi.fn().mockResolvedValue({
      fixture_code: "FX-011",
      transaction_records_deleted: false,
      transaction_item_count: 4
    });
    Object.assign(api, { deleteFixture });
    const selectedFixtureId = ref<number | null>(11);
    const movePageBackAfterRemoval = vi.fn();
    const reloadAfterRemoval = vi.fn().mockResolvedValue(undefined);
    const finishEditing = vi.fn();
    const actions = useMasterEntityDeletion({
      activeTab: ref("fixture" as const),
      canManage: computed(() => true),
      selectedCustomerId: ref(3),
      selectedFixtureId,
      selectedModelId: ref<number | null>(null),
      selectedStationId: ref<number | null>(null),
      selectedFixtureCode: computed(() => "FX-011"),
      selectedModelCode: computed(() => ""),
      selectedStationCode: computed(() => ""),
      saving: ref(false),
      selectedTabLabel: () => "治具",
      movePageBackAfterRemoval,
      reloadAfterRemoval,
      finishEditing
    });

    actions.openDialog();
    await actions.confirmDeletion();

    expect(deleteFixture).toHaveBeenCalledWith(11, 3, false);
    expect(selectedFixtureId.value).toBeNull();
    expect(movePageBackAfterRemoval).toHaveBeenCalledOnce();
    expect(reloadAfterRemoval).toHaveBeenCalledOnce();
    expect(finishEditing).toHaveBeenCalledOnce();
    expect(actions.dialogOpen.value).toBe(false);
  });
});
