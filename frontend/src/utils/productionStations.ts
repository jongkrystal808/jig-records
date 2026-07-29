import type { ModelStation, Station } from "@/types";

export function getAvailableRequirementStations(
  stations: Station[],
  mappings: ModelStation[],
  modelId: number | null
): Station[] {
  if (modelId === null) {
    return [];
  }

  const mappedStationIds = new Set(
    mappings.filter((row) => row.model_id === modelId).map((row) => row.station_id)
  );

  return stations
    .filter((row) => mappedStationIds.has(row.id))
    .slice()
    .sort((a, b) => a.code.localeCompare(b.code));
}
