import { computed, onBeforeUnmount, ref, watch, type Ref } from "vue";

import { api, fetchFixtureImageObjectUrl } from "@/api";
import { pushToast } from "@/toastState";
import type {
  Fixture,
  FixtureQualityReport,
  MachineModel,
  ModelStation,
  Station
} from "@/types";

const ISSUE_LABELS: Record<string, string> = {
  missing_name: "沒有名稱",
  missing_storage_location: "沒有儲位",
  missing_image: "沒有圖片",
  missing_min_stock_qty: "沒有最低水位",
  missing_model_relation: "沒有任何機種關聯",
  stock_mismatch: "Identifier 庫存與總庫存不一致",
  missing_storage_and_min_stock: "沒有儲位 / 沒有最低水位"
};

function emptyFixtureForm() {
  return {
    code: "",
    name: "",
    responsible_user_id: null as number | null,
    line_storage_location: "",
    department_storage_location: "",
    min_stock_qty: 0,
    description: "",
    is_active: true
  };
}

function fixtureFormFromRow(row: Fixture) {
  return {
    code: row.code,
    name: row.name,
    responsible_user_id: row.responsible_user_id,
    line_storage_location: row.line_storage_location ?? "",
    department_storage_location: row.department_storage_location ?? "",
    min_stock_qty: row.min_stock_qty,
    description: row.description ?? "",
    is_active: row.is_active
  };
}

export function useMasterQuality(options: {
  fixtures: Ref<Fixture[]>;
  models: Ref<MachineModel[]>;
  stations: Ref<Station[]>;
  selectedCustomerId: Ref<number | null>;
  reloadData: () => Promise<void>;
  openRequirements: () => Promise<void>;
  openLedger: (fixtureCode: string) => Promise<void>;
}) {
  const fixtureQualityReport = ref<FixtureQualityReport | null>(null);
  const qualityQuickEditOpen = ref(false);
  const qualityQuickEditIssueCode = ref<string | null>(null);
  const qualityQuickEditFixtureId = ref<number | null>(null);
  const qualityQuickEditForm = ref(emptyFixtureForm());
  const qualityQuickEditSaving = ref(false);
  const qualityInlineSavingFixtureId = ref<number | null>(null);
  const qualityRelationSaving = ref(false);
  const qualityModelStations = ref<ModelStation[]>([]);
  const qualityRelationModelId = ref<number | null>(null);
  const qualityRelationStationId = ref<number | null>(null);
  const qualityRelationRequiredQty = ref(1);
  const qualityImageInput = ref<HTMLInputElement | null>(null);
  const qualityImageFile = ref<File | null>(null);
  const qualityImageUploading = ref(false);
  const qualityImageVersion = ref(Date.now());
  const qualityImageUrl = ref("");
  const qualityImageLoading = ref(false);
  let imageRequestId = 0;

  const qualityQuickEditFixture = computed(
    () => options.fixtures.value.find((row) => row.id === qualityQuickEditFixtureId.value) ?? null
  );
  const qualityQuickEditIssueLabel = computed(() => {
    if (!qualityQuickEditIssueCode.value) return "";
    return ISSUE_LABELS[qualityQuickEditIssueCode.value] ?? qualityQuickEditIssueCode.value;
  });
  const qualityQuickEditTitle = computed(() => {
    const fixtureCode = qualityQuickEditFixture.value?.code ?? "";
    return fixtureCode
      ? `${fixtureCode} - ${qualityQuickEditIssueLabel.value}`
      : qualityQuickEditIssueLabel.value;
  });
  const qualityRelationStationOptions = computed(() => options.stations.value);

  function revokeQualityImageUrl(): void {
    if (!qualityImageUrl.value) return;
    URL.revokeObjectURL(qualityImageUrl.value);
    qualityImageUrl.value = "";
  }

  watch(
    [
      () => qualityQuickEditFixture.value?.code,
      () => qualityQuickEditFixture.value?.has_image,
      qualityImageVersion,
      options.selectedCustomerId
    ],
    async ([fixtureCode, hasImage, , customerId]) => {
      const requestId = ++imageRequestId;
      revokeQualityImageUrl();
      if (!fixtureCode || !hasImage || customerId == null) {
        qualityImageLoading.value = false;
        return;
      }
      qualityImageLoading.value = true;
      try {
        const objectUrl = await fetchFixtureImageObjectUrl(fixtureCode as string, customerId as number);
        if (requestId !== imageRequestId) {
          URL.revokeObjectURL(objectUrl);
          return;
        }
        qualityImageUrl.value = objectUrl;
      } catch {
        if (requestId === imageRequestId) qualityImageUrl.value = "";
      } finally {
        if (requestId === imageRequestId) qualityImageLoading.value = false;
      }
    },
    { immediate: true }
  );

  watch(qualityRelationStationOptions, (rows) => {
    if (!rows.some((row) => row.id === qualityRelationStationId.value)) {
      qualityRelationStationId.value = rows[0]?.id ?? null;
    }
  });

  async function openIssueEditorFromQuality(fixtureId: number, issueCode: string): Promise<void> {
    const editorIssueCode =
      issueCode === "missing_storage_location" || issueCode === "missing_min_stock_qty"
        ? "missing_storage_and_min_stock"
        : issueCode;
    if (editorIssueCode === "missing_model_relation") {
      await options.openRequirements();
      return;
    }
    const fixture = options.fixtures.value.find((row) => row.id === fixtureId);
    if (!fixture) {
      pushToast("找不到要修正的治具資料。", "warning");
      return;
    }
    qualityQuickEditFixtureId.value = fixtureId;
    qualityQuickEditIssueCode.value = editorIssueCode;
    qualityQuickEditForm.value = fixtureFormFromRow(fixture);
    qualityRelationRequiredQty.value = 1;
    qualityQuickEditOpen.value = true;
  }

  async function openLedgerFromQuality(): Promise<void> {
    await options.openLedger(qualityQuickEditFixture.value?.code ?? "");
  }

  function closeQualityQuickEdit(): void {
    qualityQuickEditOpen.value = false;
    qualityQuickEditIssueCode.value = null;
    qualityQuickEditFixtureId.value = null;
    qualityQuickEditForm.value = emptyFixtureForm();
    qualityRelationModelId.value = null;
    qualityRelationStationId.value = null;
    qualityRelationRequiredQty.value = 1;
    qualityImageFile.value = null;
    if (qualityImageInput.value) qualityImageInput.value.value = "";
    imageRequestId += 1;
    revokeQualityImageUrl();
  }

  function updateQualityImageFile(event: Event): void {
    qualityImageFile.value = (event.target as HTMLInputElement).files?.[0] ?? null;
  }

  async function saveQualityQuickEdit(): Promise<void> {
    const customerId = options.selectedCustomerId.value;
    const fixtureId = qualityQuickEditFixtureId.value;
    if (!customerId || !fixtureId) {
      pushToast("請先選擇客戶與治具。", "warning");
      return;
    }
    qualityQuickEditSaving.value = true;
    try {
      await api.updateFixture(fixtureId, {
        customer_id: customerId,
        responsible_user_id: qualityQuickEditForm.value.responsible_user_id,
        code: qualityQuickEditForm.value.code.trim(),
        name: qualityQuickEditForm.value.name.trim(),
        line_storage_location: qualityQuickEditForm.value.line_storage_location.trim() || undefined,
        department_storage_location:
          qualityQuickEditForm.value.department_storage_location.trim() || undefined,
        min_stock_qty: qualityQuickEditForm.value.min_stock_qty,
        description: qualityQuickEditForm.value.description.trim() || undefined,
        is_active: qualityQuickEditForm.value.is_active
      });
      await options.reloadData();
      pushToast(`治具 ${qualityQuickEditForm.value.code} 已更新。`, "success");
      closeQualityQuickEdit();
    } catch (error) {
      pushToast(error instanceof Error ? error.message : "更新治具失敗", "error");
    } finally {
      qualityQuickEditSaving.value = false;
    }
  }

  async function saveInlineQualityIssue(
    fixtureId: number,
    lineStorageLocation: string,
    departmentStorageLocation: string,
    minStockQty: number
  ): Promise<void> {
    const customerId = options.selectedCustomerId.value;
    if (!customerId) {
      pushToast("請先選擇客戶。", "warning");
      return;
    }
    const fixture = options.fixtures.value.find((row) => row.id === fixtureId);
    if (!fixture) {
      pushToast("找不到要更新的治具資料。", "warning");
      return;
    }
    qualityInlineSavingFixtureId.value = fixtureId;
    try {
      await api.updateFixture(fixtureId, {
        customer_id: customerId,
        responsible_user_id: fixture.responsible_user_id,
        code: fixture.code.trim(),
        name: fixture.name.trim(),
        line_storage_location: lineStorageLocation.trim() || undefined,
        department_storage_location: departmentStorageLocation.trim() || undefined,
        min_stock_qty: minStockQty,
        description: fixture.description?.trim() || undefined,
        is_active: fixture.is_active
      });
      await options.reloadData();
      pushToast(`治具 ${fixture.code} 已更新。`, "success");
    } catch (error) {
      pushToast(error instanceof Error ? error.message : "更新治具失敗", "error");
    } finally {
      qualityInlineSavingFixtureId.value = null;
    }
  }

  async function saveQualityRelation(): Promise<void> {
    const customerId = options.selectedCustomerId.value;
    const fixtureId = qualityQuickEditFixtureId.value;
    if (!customerId || !fixtureId) {
      pushToast("請先選擇客戶與治具。", "warning");
      return;
    }
    if (!qualityRelationModelId.value || !qualityRelationStationId.value) {
      pushToast("請先選擇機種與站點。", "warning");
      return;
    }
    qualityRelationSaving.value = true;
    try {
      const existingMapping = qualityModelStations.value.find(
        (row) =>
          row.model_id === qualityRelationModelId.value &&
          row.station_id === qualityRelationStationId.value
      );
      if (!existingMapping) {
        const createdMapping = await api.createModelStation({
          customer_id: customerId,
          model_id: qualityRelationModelId.value,
          station_id: qualityRelationStationId.value
        });
        qualityModelStations.value = [...qualityModelStations.value, createdMapping];
      }
      await api.createFixtureRequirement({
        customer_id: customerId,
        model_id: qualityRelationModelId.value,
        station_id: qualityRelationStationId.value,
        fixture_id: fixtureId,
        required_qty: qualityRelationRequiredQty.value
      });
      await options.reloadData();
      pushToast("已補上第一筆機種站點治具需求。", "success");
      closeQualityQuickEdit();
    } catch (error) {
      pushToast(error instanceof Error ? error.message : "建立治具關聯失敗", "error");
    } finally {
      qualityRelationSaving.value = false;
    }
  }

  async function uploadQualityImage(): Promise<void> {
    const customerId = options.selectedCustomerId.value;
    const fixtureId = qualityQuickEditFixtureId.value;
    if (!customerId || !fixtureId) {
      pushToast("請先選擇客戶與治具。", "warning");
      return;
    }
    if (!qualityImageFile.value) {
      pushToast("請先選擇要上傳的圖片。", "warning");
      return;
    }
    qualityImageUploading.value = true;
    try {
      const result = await api.uploadFixtureImage(fixtureId, customerId, qualityImageFile.value);
      qualityImageVersion.value = Date.now();
      qualityQuickEditForm.value = fixtureFormFromRow(result.fixture);
      await options.reloadData();
      pushToast(`治具 ${result.fixture_code} 圖片已更新。`, "success");
      closeQualityQuickEdit();
    } catch (error) {
      pushToast(error instanceof Error ? error.message : "上傳治具圖片失敗", "error");
    } finally {
      qualityImageUploading.value = false;
    }
  }

  onBeforeUnmount(() => {
    imageRequestId += 1;
    revokeQualityImageUrl();
  });

  return {
    fixtureQualityReport,
    qualityQuickEditOpen,
    qualityQuickEditIssueCode,
    qualityQuickEditFixtureId,
    qualityQuickEditFixture,
    qualityQuickEditForm,
    qualityQuickEditSaving,
    qualityInlineSavingFixtureId,
    qualityRelationSaving,
    qualityRelationModelId,
    qualityRelationStationId,
    qualityRelationRequiredQty,
    qualityRelationStationOptions,
    qualityImageInput,
    qualityImageFile,
    qualityImageUploading,
    qualityImageUrl,
    qualityImageLoading,
    qualityQuickEditTitle,
    openIssueEditorFromQuality,
    openLedgerFromQuality,
    closeQualityQuickEdit,
    updateQualityImageFile,
    saveQualityQuickEdit,
    saveInlineQualityIssue,
    saveQualityRelation,
    uploadQualityImage
  };
}
