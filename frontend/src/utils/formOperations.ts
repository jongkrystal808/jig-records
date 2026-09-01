export function formOperationError(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

export function productionMappingValidationMessage(
  modelId: number | null,
  stationId: number | null
): string | null {
  if (!modelId) return "請輸入有效的機種代碼。";
  if (!stationId) return "請輸入有效的站點代碼。";
  return null;
}

export function productionRequirementValidationMessage(
  stationId: number | null,
  fixtureId: number | null,
  requiredQty: number
): string | null {
  if (!stationId) return "請輸入有效的站點代碼。";
  if (!fixtureId) return "請輸入有效的治具代碼。";
  if (!Number.isFinite(requiredQty) || requiredQty <= 0) return "需求數量必須大於 0。";
  return null;
}
